import requests
import urllib.parse
import xmltodict
import jwt
import hashlib
from datetime import timedelta, datetime
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.generics import GenericAPIView as HaystackGenericApiView
from haystack.query import RelatedSearchQuerySet, SearchQuerySet

from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q, Count, Prefetch, F, Exists, OuterRef
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.db import transaction

from rest_framework import status, generics, exceptions as drf_exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from common.views import BaseModelViewSet, BaseCatalogViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action

from django_q.tasks import async_task

from bkz3.settings import BACKEND_URL, FRONTEND_URL, GLOBAL_FRONT_SETTINGS

from common.paginators import CustomPagination
from common.models import BaseModel
from common.utils import order_queryset_from_get_param
from users.models import ProfileModel
from bpms.tasks.models import TaskModel, TaskExecutionTimeModel
from bpms.chat.models import ChatModel
from bpms.workgroups.models import WorkgroupModel

from . import models
from . import serializers
from . import permissions
from bpms.tasks import permissions as tasks_permissions
from . import notifications
from .utils import get_connect_meeting_url, get_invite_link, get_meeting_queryset, get_hash_url, process_meeting_record, \
    sync_meeting_members, sync_meeting_recordings, get_related_meeting, get_meeting_project_for_related_object, filter_meeting_section_queryset, \
    extract_summary_from_meeting, extract_efficiency_from_meeting, merge_deskshare_with_audio, delete_file_physically_and_from_db, \
    create_meeting_execution_times, create_call_execution_times, get_my_day_meeting_sections_queryset, get_my_day_user_ids, \
    reassign_section_execution_times
from .cron import update_meeting_section_members
from . import utils_call
from help_desk import serializers as help_desk_serializers
from help_desk import models as help_desk_models
from help_desk import utils as help_desk_utils
from contractor_permissions.utils import contractors_where_user_has_app_section_role_permission


class MeetingConnectMixin:
    pm_template = 'pm_entrance.html'
    pm_not_found = 'Конференция не найдена'
    pm_forbidden = 'У Вас нет прав на вход в конференцию.'
    too_early = 'Конференция еще не началась.'
    too_late = 'Конференция уже закончилась.'
    waiting_for_moderator = 'Конференция еще не началась. Ожидаем модератора.'

    @staticmethod
    def allow_same_origin_iframe(response):
        existing_csp = response.get('Content-Security-Policy', '')
        directives = [directive.strip() for directive in existing_csp.split(';') if directive.strip()]
        directives = [
            directive for directive in directives
            if not directive.lower().startswith('frame-ancestors')
        ]
        directives.append("frame-ancestors 'self'")
        response['Content-Security-Policy'] = '; '.join(directives) + ';'
        return response

    def is_running(self, meeting_uid, server):
        url = get_hash_url('isMeetingRunning', 'meetingID=' + meeting_uid, server)
        r = requests
        req = r.get(url)
        doc = xmltodict.parse(req.text)
        if doc['response']['running'] == 'true':
            return True
        else:
            return False

    def run_meeting(self, meeting, section_id=None):
        get_params_create = 'allowStartStopRecording=true' \
                            + '&attendeePW=' + str(meeting.attendeePW) \
                            + '&autoStartRecording=false&meetingID=' + str(meeting.id) \
                            + '&moderatorPW=' + str(meeting.moderatorPW) \
                            + '&name=' + urllib.parse.quote(meeting.name) \
                            + '&record=true' \
                            + '&logoutURL=' + urllib.parse.quote(FRONTEND_URL) \
                            + '&duration=' + str(meeting.duration) \
                            + '&meta_endCallbackUrl=' + urllib.parse.quote(
            BACKEND_URL + '/api/v1/meetings/set_complete/?uid=' + str(meeting.id)) \
                            + '&meta_bbb-recording-ready-url=' + urllib.parse.quote(
            BACKEND_URL + '/api/v1/meetings/set_record_ready/')
        if section_id is not None:
            get_params_create += '&meta_section_id=' + urllib.parse.quote(str(section_id))
        create_url = self.get_hash_url('create', get_params_create, meeting.server)
        resp = requests.get(create_url)
        return resp

    def get_join_url(self, first_name, last_name, meeting, password, user_id=None, role=None):
        u_l_name = urllib.parse.quote(last_name)
        u_f_name = urllib.parse.quote(first_name)
        u_name = u_l_name + '+' + u_f_name if u_l_name or u_f_name else urllib.parse.quote('Moderator')
        get_params_join = (
            f'fullName={u_name}'
            f'&meetingID={meeting.id}'
            f'&password={password}'
            f'&redirect=true'
        )
        if user_id is not None:
            u_id = urllib.parse.quote(str(user_id))
            get_params_join += f'&userID={u_id}'
        if role is not None:
            get_params_join += f'&role={urllib.parse.quote(str(role))}'
        return get_hash_url('join', get_params_join, meeting.server)

    @staticmethod
    def get_planned_meeting(lookup):
        try:
            meeting = models.PlannedMeetingModel.objects.get(lookup, is_active=True)
        except (ObjectDoesNotExist, ValidationError):
            return None
        return meeting

    @staticmethod
    def is_moderator(meeting, user):
        is_moderator = False
        if user == meeting.author or meeting.meetingmembermodel_set.filter(
                is_moderator=True,
                is_active=True,
                user=user.pk
        ).exists():
            is_moderator = True
        return is_moderator

    @staticmethod
    def is_visor(meeting, user):
        is_visor = False
        members = models.MeetingMemberModel.objects.filter(
            meeting=meeting,
            is_active=True
        ).values_list('user', flat=True).distinct()
        if user.id in members:
            is_visor = True
        return is_visor

    @staticmethod
    def check_early(date_start):
        now = timezone.now()
        if (date_start - timedelta(minutes=30)) > now:
            return True
        else:
            return False

    @staticmethod
    def get_hash_url(first_param, get_params, server):
        prep = first_param + get_params + server.secret
        checksum = hashlib.sha1(prep.encode()).hexdigest()
        divider = ''
        if not get_params == '':
            divider = '&'
        return server.url + first_param + '?' + get_params + divider + 'checksum=' + checksum

    def start_meeting(self, meeting, user, notify_user_ids=None, emit_start_push=True):
        """
        Запускает собрание и создает MeetingSectionModel.
        Возвращает True если собрание успешно запущено, False в противном случае.
        notify_user_ids: опционально список UUID профилей — только им уйдёт уведомление о старте; None = всем участникам.
        """
        # Перед запуском синхронизируем имя и состав участников, если встреча привязана к объекту
        # TODO Перенести это в StartRelatedMeetingView, когда для запуска собрания из чата тоже будет использоваться start-related
        if meeting.related_object:
            original_object = meeting.related_object.original_object
            object_name = str(original_object)
            if meeting.name != object_name:
                meeting.name = object_name
                meeting.save(update_fields=('name',))
            required_member_ids = original_object.get_member_ids
            sync_meeting_members(meeting, required_member_ids)

        # Обеспечиваем наличие активной секции до запуска BBB, чтобы прокинуть meta_section_id.
        # Делаем это под row-lock встречи, чтобы при параллельных стартах не плодить секции/уведомления.
        with transaction.atomic():
            locked_meeting = models.PlannedMeetingModel.objects.select_for_update().get(pk=meeting.pk)
            if locked_meeting.status == 'online':
                meeting.status = 'online' # для консистентности meeting в памяти
                return True

            section = models.MeetingSectionModel.objects.filter(
                meeting=locked_meeting,
                status='online'
            ).order_by('-date_start').first()
            if not section:
                section = models.MeetingSectionModel.objects.create(
                    meeting=locked_meeting,
                    name=locked_meeting.name,
                    status='online',
                    date_start=timezone.now()
                )

        resp = self.run_meeting(meeting, section_id=section.id)

        if resp.status_code == 200:
            with transaction.atomic():
                updated_rows = models.PlannedMeetingModel.objects.filter(
                    pk=meeting.pk
                ).exclude(
                    status='online'
                ).update(
                    status='online'
                )
                meeting.status = 'online'
                if updated_rows and emit_start_push:
                    transaction.on_commit(
                        lambda: async_task(notifications.notify_about_start_meeting, meeting, user, notify_user_ids)
                    )
            return True
        return False

    @staticmethod
    def complete_meeting(meeting):
        """
        Присваивает собранию статус 'Завершен'.
        Находит все активные секции (теоретически одну) и устанавливает время окончания, продолжительность и статус.
        Если у собрания есть related_object, очищает лишних участников (которых нет в get_member_ids объекта).
        """
        with transaction.atomic():
            locked_meeting = models.PlannedMeetingModel.objects.select_for_update().get(pk=meeting.pk)
            locked_meeting.status = 'ended'
            locked_meeting.save(update_fields=('status',))
            meeting.status = 'ended'

            sections = models.MeetingSectionModel.objects.select_for_update().filter(
                meeting=locked_meeting,
                status='online'
            ).order_by('-created_at')

            active_section = None
            if sections.exists():
                now = timezone.now()
                for section in sections:
                    section.date_end = now
                    section.duration = now - section.date_start
                    section.status = 'ended'
                    section.save(update_fields=('date_end', 'duration', 'status'))
                active_section = sections.first()

            # Если у собрания есть related_object, очищаем лишних участников
            if locked_meeting.related_object:
                original_object = locked_meeting.related_object.original_object
                required_member_ids = original_object.get_member_ids
                # Синхронизируем имя встречи с именем связанного объекта
                object_name = str(original_object)
                if locked_meeting.name != object_name:
                    locked_meeting.name = object_name
                    locked_meeting.save(update_fields=('name',))
                    meeting.name = object_name
                sync_meeting_members(locked_meeting, required_member_ids)
            if active_section is not None:
                if active_section.meeting.calls.exists():
                    create_call_execution_times(active_section)
                else:
                    create_meeting_execution_times(active_section)

        # Завершить все прошедшие связанные события календаря.
        now = timezone.now()
        meeting.calendar_events.filter(
            is_active=True,
            is_finished=False,
            start_at__lte=now,
        ).update(is_finished=True)

        return True


class PlannedMeetingFilteredList(generics.ListAPIView):
    serializer_class = serializers.PlannedMeetingListSerializer
    queryset = models.PlannedMeetingModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = get_meeting_queryset(self.request).annotate(
            members_count=Count('members', distinct=True)
        )
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class PlannedMeetingUpdate(generics.UpdateAPIView):
    serializer_class = serializers.PlannedMeetingUpdateSerializer
    queryset = models.PlannedMeetingModel.objects.filter(is_active=True)
    permission_classes = (
        IsAuthenticated, permissions.MeetingAuthorPermission
    )


class PlannedMeetingModeratorUpdate(generics.UpdateAPIView):
    serializer_class = serializers.MeetingModeratorUpdateSerializer
    permission_classes = (IsAuthenticated, permissions.MeetingModeratorUpdatePermission)
    queryset = models.MeetingMemberModel.objects.all()

    def get_object(self):
        try:
            obj = models.MeetingMemberModel.objects.get(is_active=True, meeting_id=self.request.data.get('meeting'),
                                                        user_id=self.request.data.get('user'))
        except ObjectDoesNotExist:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_moderator = request.data.get('is_moderator')
        if isinstance(is_moderator, bool) and instance.meeting.author != instance.user:
            instance.is_moderator = is_moderator
            instance.save(update_fields=('is_moderator',))
            return Response('ok', status=status.HTTP_200_OK)
        else:
            return Response('not_valid', status=status.HTTP_400_BAD_REQUEST)


class PlannedMeetingAddMember(generics.CreateAPIView):
    serializer_class = serializers.PlannedMeetingAddMemberSerializer
    queryset = models.PlannedMeetingModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated, permissions.MeetingAuthorPermission)

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user')
        if user_id:
            try:
                ProfileModel.objects.get(id=user_id)
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        data = super().create(request, *args, **kwargs)
        return data


class PlannedMeetingDeleteMember(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        meeting_id = kwargs['pk']
        user_id = request.data['user']
        try:
            meeting_member = models.MeetingMemberModel.objects.get(meeting_id=meeting_id, user_id=user_id)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = request.user.profile
        if not user == meeting_member.meeting.author and not user.pk == user_id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if meeting_member.user_id == meeting_member.meeting.author_id:
            return Response('Нельзя удалять автора конференции.', status.HTTP_403_FORBIDDEN)
        meeting_member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlannedMeetingRecordings(APIView, MeetingConnectMixin):

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        meeting = models.PlannedMeetingModel.objects.get(pk=pk)
        is_visor = self.is_visor(meeting, request.user.profile)
        if not is_visor:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if meeting.is_external:
            saved_record = meeting.records.filter(is_active=True).order_by('-created_at')
            record_serializer = serializers.MeetingRecordSerializer
            return Response(record_serializer(saved_record, many=True).data, status.HTTP_200_OK)

        server = meeting.server
        url = get_hash_url('getRecordings', 'meetingID=' + str(meeting.id), server)
        resp = requests.get(url)
        doc = xmltodict.parse(resp.text)
        try:
            recording = doc['response']['recordings']['recording']
        except TypeError:
            meeting.has_record = False
            meeting.save()
            return Response([], status=status.HTTP_200_OK)
        if meeting.has_record is False:
            meeting.has_record = True
            meeting.save()
        if isinstance(recording, list):
            records = []
            for each in recording:
                records.append(each['playback']['format'])
        else:
            records = [recording['playback']['format']]
        for record in records:
            models.MeetingRecordsModel.objects.get_or_create(meeting=meeting,
                                                             url=record['url'],
                                                             defaults={'initial_data': record}
                                                             )
        saved_record = meeting.records.filter(is_active=True).order_by('-created_at')
        record_serializer = serializers.MeetingRecordSerializer
        return Response(record_serializer(saved_record, many=True).data, status.HTTP_200_OK)


@method_decorator(xframe_options_exempt, name='dispatch')
class ConnectPlannedMeetingView(APIView, MeetingConnectMixin):  # TODO Добавить уведомление
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        if request.user.is_anonymous:
            return self.allow_same_origin_iframe(
                HttpResponseRedirect(FRONTEND_URL + '/ru/user/login/?from=' + get_connect_meeting_url(pk))
            )
        user = request.user.profile
        lookup = Q(pk=pk)
        meeting = self.get_planned_meeting(lookup)
        context = {
            'logo': GLOBAL_FRONT_SETTINGS['header_setting']['logo'],
            'meeting': meeting,
        }
        if not meeting:
            format_value = meeting.name if meeting else ''
            context['reason'] = self.pm_not_found
            context['alert_type'] = 'danger'
            return self.allow_same_origin_iframe(render(request, self.pm_template, context=context))
        is_moderator = self.is_moderator(meeting, user)
        is_visor = self.is_visor(meeting, user)
        if is_moderator is False and is_visor is False:
            context['reason'] = self.pm_forbidden
            context['alert_type'] = 'danger'
            return self.allow_same_origin_iframe(render(request, self.pm_template, context=context))
        server = meeting.server
        password = str(meeting.attendeePW)
        if is_moderator is True:
            password = str(meeting.moderatorPW)
        date_start = meeting.date_begin
        if meeting.status != 'online':
            if meeting.status == 'ended' and is_moderator is False:
                context['reason'] = self.too_late
                return self.allow_same_origin_iframe(render(request, self.pm_template, context=context))
            elif self.check_early(date_start) and is_moderator is False:
                context['reason'] = self.too_early
                return self.allow_same_origin_iframe(render(request, self.pm_template, context=context))
            elif is_moderator is True:
                self.start_meeting(meeting, user)
            else:
                context['reason'] = self.waiting_for_moderator
                return self.allow_same_origin_iframe(render(request, self.pm_template, context=context))
        join_role = 'MODERATOR' if is_moderator else 'VIEWER'
        return self.allow_same_origin_iframe(HttpResponseRedirect(self.get_join_url(
            request.user.first_name,
            request.user.last_name,
            meeting,
            password,
            request.user.profile.pk,
            join_role,
        )))


class RestartPlannedMeetingView(APIView, MeetingConnectMixin):
    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        if request.user.is_anonymous:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        user = request.user.profile
        lookup = Q(pk=pk)
        meeting = self.get_planned_meeting(lookup)
        is_moderator = self.is_moderator(meeting, user)
        is_visor = self.is_visor(meeting, user)
        if is_moderator or is_visor:
            meeting.status = 'new'
            meeting.save()
            return HttpResponse(status=status.HTTP_200_OK)
        else:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)


@method_decorator(xframe_options_exempt, name='dispatch')
class ExternalLoginPlannedMeetingView(APIView, MeetingConnectMixin):
    permission_classes = ()

    def get_planned_meeting_by_uniq(self, uniq):
        lookup = Q(invite_link=uniq)
        meeting = self.get_planned_meeting(lookup)
        if not meeting:
            return None
        return meeting

    def get(self, request, *args, **kwargs):
        uniq = kwargs['uniq']
        meeting = self.get_planned_meeting_by_uniq(uniq)
        context = {
            'url': get_invite_link(uniq),
            'reason': None,
            'meeting': meeting,
            'logo': GLOBAL_FRONT_SETTINGS['header_setting']['logo'],
        }
        if not meeting:
            return self.allow_same_origin_iframe(
                render(request, 'pm_entrance.html', context={'reason': self.pm_not_found})
            )
        is_running = self.is_running(str(meeting.id), meeting.server)
        user = request.user
        if not user.is_anonymous:
            member, created = models.MeetingMemberModel.objects.get_or_create(user=user.profile, meeting=meeting)
            if not created and member.is_moderator is True and is_running is False:
                context['url'] = get_connect_meeting_url(meeting.pk)
                return self.allow_same_origin_iframe(render(request, 'pm_start.html', context))
            return self.allow_same_origin_iframe(HttpResponseRedirect(get_connect_meeting_url(meeting.pk)))
        if is_running is False:
            if meeting.status == 'ended':
                context['reason'] = self.too_late
            elif self.check_early(meeting.date_begin):
                context['reason'] = self.too_early
            else:
                context['reason'] = self.waiting_for_moderator
        return self.allow_same_origin_iframe(render(request, 'pm_entrance.html', context))

    def post(self, request, *args, **kwargs):
        uniq = kwargs['uniq']
        meeting = self.get_planned_meeting_by_uniq(uniq)
        if not meeting:
            return self.allow_same_origin_iframe(
                render(request, 'pm_entrance.html', context={'reason': self.pm_not_found})
            )
        password = str(meeting.attendeePW)
        server = meeting.server
        is_running = self.is_running(str(meeting.id), server)
        if not is_running:
            return self.allow_same_origin_iframe(
                render(request, 'pm_entrance.html', context={'reason': self.too_late})
            )
        data = request.data
        return self.allow_same_origin_iframe(HttpResponseRedirect(self.get_join_url(
            data.get('first_name', ''), data.get('last_name', ''),
            meeting, password)
        ))


class PlannedMeetingCreateView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.PlannedMeetingCreateSerializer
    queryset = models.PlannedMeetingModel.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        user = request.user.profile
        from billing.models import TariffModel
        from contractor_permissions.utils import get_tariffs_id_by_contractors
        demo_tariff = TariffModel.objects.get(code='demo')
        organizations = user.my_organizations
        organizations_tariffs = get_tariffs_id_by_contractors(organizations)
        if {str(demo_tariff.pk), } == organizations_tariffs:
            raise drf_exceptions.ValidationError('Создание встречи недоступно в демо-тарифе.')
        return super().create(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class PlannedMeetingMemberListView(generics.ListAPIView):
    serializer_class = serializers.MeetingMemberListSerializer
    permission_classes = (IsAuthenticated,)
    queryset = models.MeetingMemberModel.objects.all()
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user.profile
        queryset = self.queryset
        meeting_id = self.request.query_params.get('meeting')
        if meeting_id and models.MeetingMemberModel.objects.filter(meeting_id=meeting_id, user_id=user.pk).exists():
            queryset = queryset.filter(meeting_id=meeting_id).order_by('user__user__last_name',
                                                                       'user__user__first_name',
                                                                       'user__user__middle_name')
        else:
            queryset = queryset.none()
        return queryset


def sync_help_desk_call_with_meeting_end(meeting):
    from help_desk import utils as help_desk_utils

    with transaction.atomic():
        call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
            'ticket',
            'chat',
        ).filter(
            meeting_id=meeting.pk,
            is_active=True,
            status_id__in=models.CallModel.ACTIVE_STATUSES,
        ).order_by('-created_at').first()
        if not call_obj:
            return False

        action_dt = timezone.now()
        old_status = call_obj.status_id
        call_obj.status_id = 'ended'
        call_obj.ended_at = action_dt
        call_obj.save(update_fields=('status', 'ended_at'))
        ticket = call_obj.ticket

    transaction.on_commit(lambda: utils_call.send_socketio_about_call_updated(call_obj, old_status=old_status))
    transaction.on_commit(
        lambda: async_task(
            notifications.notify_about_call_updated_notification,
            call_obj,
            call_obj.initiator,
            recipients=list(utils_call.get_call_notification_recipients(call_obj)),
        )
    )
    transaction.on_commit(
        lambda: async_task(
            notifications.notify_about_call_updated_push,
            call_obj,
            call_obj.initiator,
                old_status=old_status,
            recipients=list(utils_call.get_call_notification_recipients(call_obj)),
        )
    )
    if ticket is not None:
        transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))
    return True


@csrf_exempt
def set_meeting_complete(request):
    uid = request.GET.get('uid')
    if uid:
        try:
            meeting = models.PlannedMeetingModel.objects.get(pk=uid)
        except ObjectDoesNotExist:
            return HttpResponse(status=200)

        if meeting.status == 'online':
            sync_help_desk_call_with_meeting_end(meeting)
            MeetingConnectMixin.complete_meeting(meeting)
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=200)


@csrf_exempt
def set_record_ready(request):
    signed_parameters = jwt.decode(request.POST.get('signed_parameters', ''),
                                   key=models.MeetingServerModel.objects.get(code='default').secret,
                                   algorithms=['HS256'])
    with transaction.atomic():
        try:
            meeting = models.PlannedMeetingModel.objects.get(pk=signed_parameters.get('meeting_id'))
        except ObjectDoesNotExist:
            return HttpResponse(status=200)
        # определяем fallback_section_id как id самой последней секции встречи
        section = models.MeetingSectionModel.objects.filter(
            meeting=meeting,
            is_active=True
        ).order_by('-created_at').first()
        section_id = section.id if section else None
        if meeting.has_record is False:
            meeting.has_record = True
            meeting.save()
        transaction.on_commit(
            lambda: (
                async_task(sync_meeting_recordings, meeting.id, section_id),
                async_task(notifications.notify_about_set_record_ready, meeting)
            )
        )
    return HttpResponse(status=200)


class MeetingEndView(APIView, MeetingConnectMixin):
    def post(self, request, *args, **kwargs):
        meeting_id = request.data.get('id')
        if meeting_id:
            try:
                meeting = models.PlannedMeetingModel.objects.get(pk=meeting_id)
            except ObjectDoesNotExist:
                return Response('ok', status=status.HTTP_200_OK)
            user = request.user.profile
            if meeting.author == user:
                params = 'meetingID=' + str(meeting.id) \
                         + '&password=' + str(meeting.moderatorPW)
                hash_url = get_hash_url('end', params, meeting.server)
                requests.get(hash_url)

                sync_help_desk_call_with_meeting_end(meeting)
                self.complete_meeting(meeting)
                return Response('ok', status=status.HTTP_200_OK)
            else:
                return Response('bad_request', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('bad_request', status=status.HTTP_400_BAD_REQUEST)


class MeetingDetailView(generics.RetrieveAPIView):
    queryset = (
        models.PlannedMeetingModel.objects.filter(is_active=True)
        .prefetch_related('members')
    )
    serializer_class = serializers.PlannedMeetingDetailSerializer
    permission_classes = (IsAuthenticated, permissions.MeetingDetailPermission)


class MeetingSectionModelViewSet(BaseCatalogViewSet):
    """Вьюсет секций собрания."""
    model = models.MeetingSectionModel
    permission_classes = (IsAuthenticated,)
    queryset = models.MeetingSectionModel.objects.filter(is_active=True)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = models.MeetingSectionModel.get_queryset(
            self.request
        ).select_related('meeting__author', 'execution_time_project')
        has_records_param = self.request.query_params.get('has_records')
        if has_records_param == 'true':
            has_records_subq = models.MeetingRecordsModel.objects.filter(
                section=OuterRef('pk'), is_active=True
            )
            queryset = queryset.filter(Exists(has_records_subq))
        elif has_records_param == 'false':
            has_records_subq = models.MeetingRecordsModel.objects.filter(
                section=OuterRef('pk'), is_active=True
            )
            queryset = queryset.filter(~Exists(has_records_subq))
        return queryset

    def list(self, request, *args, **kwargs):
        meeting_id = request.query_params.get('meeting')
        if not meeting_id:
            queryset = self.get_queryset().none()
        else:
            queryset = self.get_queryset().filter(
                meeting_id=meeting_id
            ).order_by('-created_at').prefetch_related('meeting_section_members')

        if request.query_params.get('paginate') == 'false':
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, self)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        can_update = instance.get_update_permission(request)
        records_qs = models.MeetingRecordsModel.objects.filter(
            section=instance,
            is_active=True,
        )
        can_regenerate_summary = False
        if can_update and records_qs.exists() and not records_qs.filter(is_summary_ready=False).exists():
            can_regenerate_summary = True

        actions = {
            "create_accounting": {
                "availability": instance.get_detail_permission(request)
            },
            "update": {"availability": can_update},
            "update_visors": {"availability": can_update},
            "update_intents": {
                "availability": instance.get_detail_permission(request)
            },
            "regenerate_summary": {"availability": can_regenerate_summary},
        }
        return Response({"actions": actions})

    @action(methods=('get',), detail=False, url_path='my_day')
    def my_day(self, request, *args, **kwargs):
        queryset = get_my_day_meeting_sections_queryset(request)
        user_ids = get_my_day_user_ids(request)
        queryset = queryset.select_related(
            'meeting__related_object', 'meeting__author', 'execution_time_project',
        )
        queryset = queryset.prefetch_related(
            'meeting_section_members',
            'members',
            'visors'
        )

        paginator = CustomPagination()
        page = paginator.paginate_queryset(queryset, request, self)

        serializer = serializers.MeetingSectionMyDaySerializer(
            page,
            many=True,
            context={'request': request, 'user_ids': user_ids}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('get',), detail=False, url_path='my_day_intents_statistics')
    def my_day_intents_statistics(self, request, *args, **kwargs):
        """
        Возвращает агрегированную статистику по намерениям (intents) для секций,
        которые попадают в выборку "my_day" с учётом всех query-параметров.
        """
        queryset = get_my_day_meeting_sections_queryset(request)
        sections_count = queryset.count()

        from bpms.chat_ai.models import IntentModel
        record_ids_subquery = models.MeetingRecordsModel.objects.filter(
            is_active=True,
            section_id__in=queryset.values('id')
        ).values('id')
        intents_stats = IntentModel.objects.filter(
            source_object_id__in=record_ids_subquery
        ).aggregate(
            total=Count('id'),
            accepted=Count('id', filter=Q(related_object__isnull=False)),
            deleted=Count('id', filter=Q(is_active=False)),
        )
        intents_total = intents_stats.get('total', 0) or 0
        intents_accepted = intents_stats.get('accepted', 0) or 0
        intents_deleted = intents_stats.get('deleted', 0) or 0

        return Response({
            'sections_count': sections_count,
            'intents': {
                'total': intents_total,
                'accepted': intents_accepted,
                'deleted': intents_deleted,
                'unprocessed': intents_total - intents_accepted - intents_deleted,
            }
        })

    @action(methods=('get',), detail=False, url_path='my_day_intents')
    def my_day_intents(self, request, *args, **kwargs):
        queryset = get_my_day_meeting_sections_queryset(request)
        queryset = queryset.select_related('meeting', 'meeting__related_object')

        # исключаем секции без связанных intents (через join: section -> records -> intents)
        # queryset = queryset.filter(records__intents__isnull=False).distinct()
        
        # Важно: если задаём кастомный Prefetch('records', queryset=...), то вложенный prefetch
        # нужно делать внутри него, иначе Django может "потерять" records__intents.
        from bpms.chat_ai.models import IntentModel
        records_qs = models.MeetingRecordsModel.objects.prefetch_related(
            Prefetch(
                'intents',
                queryset=IntentModel.objects.select_related(
                    'intent_type',
                    'status',
                    'related_object',
                    'source_object',
                ).order_by('created_at', 'id')
            )
        )
        queryset = queryset.prefetch_related(Prefetch('records', queryset=records_qs))

        serializer = serializers.MeetingSectionIntentsSerializer(
            queryset,
            many=True,
            context={
                'request': request,
            }
        )
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='regenerate_summary')
    def regenerate_summary(self, request, *args, **kwargs):
        """Ставит в очередь повторную генерацию краткого содержания по всем записям секции."""
        instance = self.get_object()

        if not instance.get_update_permission(request):
            raise PermissionDenied('Только автор собрания может перезапускать генерацию краткого содержания')

        updated = models.MeetingRecordsModel.objects.filter(
            section=instance,
            is_active=True,
        ).update(is_summary_ready=False)

        return Response(
            {"updated_records": updated},
            status=status.HTTP_200_OK,
        )

    @action(methods=('put',), detail=True, url_path='update_visors')
    def update_visors(self, request, *args, **kwargs):
        """Обновляет наблюдателей секции собрания."""
        instance = self.get_object()
        
        if not instance.get_update_permission(request):
            raise PermissionDenied('Только автор собрания может назначать наблюдателей секции')
        
        serializer = serializers.MeetingSectionVisorsUpdateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=('put',), detail=True, url_path='update_name')
    def update_name(self, request, *args, **kwargs):
        """Обновляет название секции собрания."""
        instance = self.get_object()

        if not instance.get_update_permission(request):
            raise PermissionDenied('Только автор собрания может изменять название секции')

        serializer = serializers.MeetingSectionNameUpdateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='reassign_execution_times')
    def reassign_execution_times(self, request, *args, **kwargs):
        """Переназначает трудозатраты секции на автозадачу выбранного проекта."""
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise PermissionDenied('Только автор собрания может переназначать трудозатраты секции')

        project_uid = request.data.get('project')

        project = WorkgroupModel.objects.filter(
            pk=project_uid,
            is_active=True,
            is_project=True,
        ).first()

        reassign_section_execution_times(
            section=instance,
            project=project,
        )
        return Response('ok', status=status.HTTP_200_OK)


class MeetingRecordsModelViewSet(BaseCatalogViewSet):
    """Вьюсет записей собраний."""
    model = models.MeetingRecordsModel
    permission_classes = (IsAuthenticated,)
    queryset = models.MeetingRecordsModel.objects.filter(is_active=True)

    @action(methods=('get',), detail=False, url_path='untranscribed', permission_classes=[IsAdminUser])
    def untranscribed(self, request, *args, **kwargs):
        queryset = models.MeetingRecordsModel.objects.filter(status='new', url__isnull=False, is_active=True)

        start = request.query_params.get('start')
        if start:
            queryset = queryset.filter(created_at__gte=start)
        else:
            # Если start не передан, фильтруем начиная от 15.11.2025 - когда появилась привязка видеозаписи к секциям
            default_start = timezone.datetime(2025, 11, 15, tzinfo=timezone.utc)
            queryset = queryset.filter(created_at__gte=default_start)

        end = request.query_params.get('end')
        if end:
            queryset = queryset.filter(created_at__lte=end)

        queryset = queryset.select_related(
            'section', 'section__meeting__author'
        )
        queryset = queryset.prefetch_related('section__meeting_section_members')
        queryset = order_queryset_from_get_param(request, self.model, queryset)

        paginator = self.paginator
        if paginator is not None:
            if request.query_params.get('page_size') is None:
                paginator.page_size = 1
            page = paginator.paginate_queryset(queryset, request, self)
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('post',), detail=False, url_path='set_transcribe', permission_classes=[IsAdminUser])
    def set_transcribe(self, request, *args, **kwargs):
        record_id = request.data.get('id')
        text = request.data.get('text')
        transcribe_json = request.data.get('text_json')
        summary = request.data.get('summary')
        try:
            record = models.MeetingRecordsModel.objects.filter(is_active=True).get(pk=record_id)
        except models.MeetingRecordsModel.DoesNotExist:
            return Response({'detail': 'record not found'}, status=status.HTTP_404_NOT_FOUND)

        updates = ['status']
        if text is not None:
            record.transcribe = text
            updates.append('transcribe')
        if transcribe_json is not None:
            record.transcribe_json = transcribe_json
            updates.append('transcribe_json')
        if summary is not None:
            record.summary = summary
            updates.append('summary')
        record.status = 'done'
        record.save(update_fields=updates)
        return Response('ok', status=status.HTTP_200_OK)

    @action(methods=('post',), detail=False, url_path='status', permission_classes=[IsAdminUser])
    def set_status(self, request, *args, **kwargs):
        record_id = request.data.get('id')
        new_status = request.data.get('status')
        try:
            record = models.MeetingRecordsModel.objects.filter(is_active=True).get(pk=record_id)
        except models.MeetingRecordsModel.DoesNotExist:
            return Response({'detail': 'record not found'}, status=status.HTTP_404_NOT_FOUND)
        record.status = new_status
        record.save(update_fields=['status'])
        return Response('ok', status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='extract_intents', permission_classes=[IsAdminUser])
    def extract_intents(self, request, pk=None, *args, **kwargs):
        from .utils import extract_intents_from_meeting
        from bpms.chat_ai.models import IntentModel

        record = self.get_object()
        extract_intents_from_meeting(record)
        count = IntentModel.objects.filter(source_object_id=record.pk).count()
        return Response({'result': count}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='extract_summary', permission_classes=[IsAdminUser])
    def extract_summary(self, request, pk=None, *args, **kwargs):
        record = self.get_object()
        count = extract_summary_from_meeting(record)
        return Response({'result': count}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='extract_efficiency', permission_classes=[IsAdminUser])
    def extract_efficiency(self, request, pk=None, *args, **kwargs):
        record = self.get_object()
        result = extract_efficiency_from_meeting(record)
        return Response({'result': result}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='reset_intents_ready', permission_classes=[IsAdminUser])
    def reset_intents_ready(self, request, *args, **kwargs):
        queryset = models.MeetingRecordsModel.objects.filter(is_intents_ready=True)
        
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=end)
        
        updated = queryset.update(is_intents_ready=False)
        return Response({'updated': updated}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='reset_summary_ready', permission_classes=[IsAdminUser])
    def reset_summary_ready(self, request, *args, **kwargs):
        queryset = models.MeetingRecordsModel.objects.filter(is_summary_ready=True)
        
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=end)
        
        updated = queryset.update(
            summary_old=F('summary'),
            is_summary_ready=False
        )
        return Response({'updated': updated}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='reset_efficiency_ready', permission_classes=[IsAdminUser])
    def reset_efficiency_ready(self, request, *args, **kwargs):
        queryset = models.MeetingRecordsModel.objects.filter(is_efficiency_ready=True)
        
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=end)
        
        updated = queryset.update(is_efficiency_ready=False)
        return Response({'updated': updated}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='pending_intents', permission_classes=[IsAdminUser])
    def pending_intents(self, request, *args, **kwargs):
        records = models.MeetingRecordsModel.objects.filter(
            section__isnull=False,
            transcribe_json__isnull=False,
            is_intents_ready=False
        ).exclude(transcribe_json={}).exclude(transcribe_json="").order_by("-created_at")
        record_ids = list(records.values_list('id', flat=True))
        return Response(record_ids, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='pending_summary', permission_classes=[IsAdminUser])
    def pending_summary(self, request, *args, **kwargs):
        records = models.MeetingRecordsModel.objects.filter(
            section__isnull=False,
            transcribe_json__isnull=False,
            is_summary_ready=False
        ).exclude(transcribe_json={}).exclude(transcribe_json="").order_by("-created_at")
        record_ids = list(records.values_list('id', flat=True))
        return Response(record_ids, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='merge_video_audio')
    def merge_video_audio(self, request, pk=None, *args, **kwargs):
        """
        Склеивает видео экрана (deskshare.webm) и аудио из webcams.webm,
        сохраняет результат в meeting_record.record_file.
        """
        meeting_record = self.get_object()
        
        if not meeting_record.get_detail_permission(request):
            raise PermissionDenied('У вас нет прав на доступ к этой записи')
        
        # if meeting_record.record_file_id and meeting_record.record_file and meeting_record.record_file.is_active:
        #     serializer = serializers.MeetingRecordSerializer(meeting_record)
        #     return Response(serializer.data, status=status.HTTP_200_OK)
        
        if not meeting_record.url:
            raise drf_exceptions.ValidationError('URL записи встречи пустой')
        
        file_obj = merge_deskshare_with_audio(meeting_record.url)
        
        if not file_obj:
            raise drf_exceptions.APIException('Не удалось склеить видео и аудио')
        
        if meeting_record.record_file_id:
            delete_file_physically_and_from_db(meeting_record.record_file)
        
        meeting_record.record_file = file_obj
        meeting_record.save(update_fields=('record_file',))
        
        serializer = serializers.MeetingRecordSerializer(meeting_record)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MeetingSearchView(HaystackGenericApiView):
    index_models = [models.PlannedMeetingModel]
    serializer_class = serializers.MeetingSearchSerializer
    pagination_class = CustomPagination
    queryset = models.PlannedMeetingModel.objects.filter(is_active=True)
    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request, *args, **kwargs):
        text = request.query_params.get('text')
        if not text:
            search_queryset = SearchQuerySet().none()
        else:
            search_queryset = RelatedSearchQuerySet().filter(
                text=text,
            ).models(models.PlannedMeetingModel).load_all()
        ordering = request.query_params.get('ordering')
        if ordering:
            ordering_list = ordering.split(',')
            if ordering_list:
                search_queryset = search_queryset.order_by(*ordering)
        page = self.paginate_queryset(list(search_queryset))
        s_data = self.serializer_class(page, many=True, context={'request': request}).data
        return self.get_paginated_response(s_data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_update_meeting_members(request):
    """
    Запускает обновление участников собраний (duration, присутствие).
    Для тестирования.
    """
    try:
        update_meeting_section_members()
        return Response({'detail': 'Meeting members updated successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CallViewSet(BaseModelViewSet, MeetingConnectMixin):
    permission_classes = (IsAuthenticated,)
    model = models.CallModel

    @action(methods=('get',), detail=False, url_path='active_calls')
    def active_calls(self, request, *args, **kwargs):
        profile = request.user.profile
        queryset = self.filter_queryset(
            models.CallModel.objects.filter(
                is_active=True,
            ).filter(
                Q(initiator_id=profile.pk) |
                Q(accepted_by_id=profile.pk) |
                Q(current_target=profile.pk),
            ).filter(
                status_id__in=('ringing', 'in_call'),
            ).distinct().order_by('-created_at'),
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        ticket_id = request.query_params.get('ticket')
        if not ticket_id:
            return super().list(request, *args, **kwargs)

        ticket = help_desk_models.HelpDeskTicketModel.objects.filter(
            is_active=True,
            pk=ticket_id,
        ).first()
        if not ticket:
            raise drf_exceptions.NotFound('Обращение не найдено')
        if not ticket.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()

        queryset = self.filter_queryset(
            models.CallModel.objects.filter(is_active=True, ticket=ticket),
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('post',), detail=False, url_path='start')
    def start(self, request, *args, **kwargs):
        profile = request.user.profile
        chat_uid = request.data.get('chat_uid')
        ticket_id = request.data.get('ticket_id')
        org_admin_id = request.data.get('org_admin')

        if chat_uid:
            start_source = 'chat'
        elif ticket_id:
            start_source = 'ticket'
        else:
            start_source = 'org_support'
        ticket = None
        call_obj = None
        is_created = False

        if start_source == 'chat':
            ticket, call_obj, is_created = utils_call.start_call_from_personal_chat(
                profile_id=profile.pk,
                chat_uid=chat_uid,
            )
        elif start_source == 'ticket':
            ticket = help_desk_models.HelpDeskTicketModel.objects.select_related(
                'contact_person',
                'specialist',
                'customer_card',
            ).filter(is_active=True, pk=ticket_id).first()
            if not ticket:
                raise drf_exceptions.ValidationError('Обращение не найдено')
            if not ticket.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()

            ticket, call_obj, is_created = utils_call.start_call_from_ticket(
                profile_id=profile.pk,
                ticket_id=ticket_id,
            )
        else:
            ticket, call_obj, is_created = utils_call.start_call_to_org_support(
                profile_id=profile.pk,
                org_admin_id=org_admin_id,
            )

        if is_created:
            current_target_ids = utils_call.get_current_target_ids(call_obj)
            if not current_target_ids:
                raise drf_exceptions.ValidationError(
                    'Некорректное состояние звонка: отсутствует current_target'
                )

            self.start_meeting(
                call_obj.meeting,
                profile,
                notify_user_ids=[],
                emit_start_push=False,  # старт звонка создаёт Meeting, но push должен быть call-specific
            )
            transaction.on_commit(
                lambda: utils_call.send_socketio_about_call_created(call_obj, current_target_ids)
            )
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_about_start_call_notification,
                    call_obj,
                    profile,
                    recipients=current_target_ids,
                )
            )
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_about_start_call_push,
                    call_obj,
                    recipients=current_target_ids,
                )
            )
            transaction.on_commit(lambda: utils_call.schedule_ring_timeout_for_call(call_obj))
            if ticket is not None:
                transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))

            return Response(
                serializers.CallListSerializer(call_obj, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializers.CallListSerializer(call_obj, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(methods=('post',), detail=False, url_path='request_callback')
    def request_callback(self, request, *args, **kwargs):
        profile = request.user.profile
        org_admin_id = request.data.get('org_admin')
        description = request.data.get('description')

        if not org_admin_id:
            raise drf_exceptions.ValidationError('org_admin обязателен')
        if not description:
            raise drf_exceptions.ValidationError('description обязателен')

        ticket, call_obj = utils_call.create_callback_call_to_org_support(
            profile_id=profile.pk,
            org_admin_id=org_admin_id,
            description=description,
        )
        return Response(
            serializers.CallListSerializer(call_obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=('post',), detail=True, url_path='send_call_reminder')
    def send_call_reminder(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        try:
            call_obj = models.CallModel.objects.select_related(
                'ticket',
            ).get(pk=pk, is_active=True)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.NotFound('call not found')
        if not call_obj.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        if call_obj.initiator_id != user.pk:
            raise drf_exceptions.PermissionDenied('Напоминание о звонке доступно только инициатору')
        if call_obj.status_id not in ('connecting', 'ringing'):
            raise drf_exceptions.ValidationError(
                'Напоминание доступно только для звонков в статусах connecting/ringing'
            )

        current_target_ids = utils_call.get_current_target_ids(call_obj)
        if not current_target_ids:
            raise drf_exceptions.ValidationError(
                'Напоминание не отправлено: у звонка отсутствуют текущие получатели (current_target)'
            )

        utils_call.send_socketio_about_call_created(call_obj, current_target_ids)
        async_task(
            notifications.notify_about_start_call_push,
            call_obj,
            recipients=current_target_ids,
        )
        return Response({'detail': 'Уведомления отправлены'}, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='report_call_receiver_online')
    def report_call_receiver_online(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        try:
            call_obj = models.CallModel.objects.select_related(
                'ticket',
                'initiator',
            ).get(pk=pk, is_active=True)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.NotFound('call not found')
        if not call_obj.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        if call_obj.status_id not in ('connecting', 'ringing'):
            raise drf_exceptions.ValidationError(
                'Подтверждение присутствия доступно только для звонков в статусах connecting/ringing'
            )

        current_target_ids = utils_call.get_current_target_ids(call_obj)
        if user.pk not in current_target_ids:
            raise drf_exceptions.PermissionDenied(
                'Подтверждение присутствия доступно только текущему получателю звонка'
            )

        initiator_recipients = [call_obj.initiator_id]
        utils_call.send_socketio_about_call_receiver_presence(
            call_obj,
            recipients=initiator_recipients,
            receiver_id=user.pk,
        )
        async_task(
            notifications.notify_about_call_receiver_presence_push,
            call_obj,
            user,
            recipients=initiator_recipients,
        )
        return Response({'detail': 'Инициатор уведомлен'}, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='report_call_receiver_joined_bbb')
    def report_call_receiver_joined_bbb(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        try:
            call_obj = models.CallModel.objects.select_related(
                'ticket',
                'initiator',
            ).get(pk=pk, is_active=True)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.NotFound('call not found')
        if not call_obj.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        if call_obj.status_id not in ('in_call', 'ringing'):
            raise drf_exceptions.ValidationError(
                'Подтверждение подключения к BBB доступно только для звонков в статусах in_call/ringing'
            )

        current_target_ids = utils_call.get_current_target_ids(call_obj)
        if user.pk not in current_target_ids:
            raise drf_exceptions.PermissionDenied(
                'Подтверждение подключения к BBB доступно только текущему получателю звонка'
            )

        initiator_recipients = [call_obj.initiator_id]
        utils_call.send_socketio_about_call_receiver_joined_bbb(
            call_obj,
            recipients=initiator_recipients,
            receiver_id=user.pk,
        )
        async_task(
            notifications.notify_about_call_receiver_joined_bbb_push,
            call_obj,
            user,
            recipients=initiator_recipients,
        )
        return Response({'detail': 'Инициатор уведомлен о подключении к BBB'}, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='cancel')
    def cancel(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        with transaction.atomic():
            try:
                call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
                    'ticket',
                ).get(pk=pk, is_active=True)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound('call not found')
            if not call_obj.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()
            if call_obj.status_id not in models.CallModel.ACTIVE_STATUSES:
                return Response(serializers.CallListSerializer(call_obj, context={'request': request}).data)
            if call_obj.initiator_id != user.pk:
                raise drf_exceptions.PermissionDenied('Отменить звонок может только инициатор')
            old_status = call_obj.status_id
            call_obj.status_id = 'cancelled_by_caller'
            call_obj.ended_at = timezone.now()
            call_obj.save(update_fields=('status', 'ended_at'))
            ticket = call_obj.ticket
            recipients = utils_call.get_call_notification_recipients(call_obj)

        transaction.on_commit(lambda: utils_call.send_socketio_about_call_updated(call_obj, old_status=old_status, recipients=recipients))
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_notification,
                call_obj,
                user,
                recipients=list(recipients),
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_push,
                call_obj,
                user,
                old_status=old_status,
                recipients=list(recipients),
            )
        )
        if ticket is not None:
            transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))
        return Response(serializers.CallListSerializer(call_obj, context={'request': request}).data)

    @action(methods=('post',), detail=True, url_path='accept')
    def accept(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        with transaction.atomic():
            try:
                call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
                    'ticket',
                ).get(pk=pk, is_active=True)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound('call not found')
            if not call_obj.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()
            if call_obj.status_id not in ('connecting', 'ringing'):
                raise drf_exceptions.ValidationError('Нельзя принять звонок в текущем статусе')
            current_target_ids = utils_call.get_current_target_ids(call_obj)
            if current_target_ids and user.pk not in current_target_ids:
                raise drf_exceptions.PermissionDenied('Сейчас звонок направлен другому участнику')

            old_status = call_obj.status_id
            call_obj.status_id = 'in_call'
            call_obj.accepted_by = user
            call_obj.answered_at = timezone.now()
            call_obj.save(update_fields=('status', 'accepted_by', 'answered_at'))
            utils_call.set_current_targets(call_obj, [user.pk])
            ticket = call_obj.ticket
            if call_obj.meeting_id:
                models.MeetingMemberModel.objects.get_or_create(
                    meeting=call_obj.meeting,
                    user=user,
                    defaults={'is_moderator': True},
                )
            if (
                ticket is not None
                and not ticket.specialist_id
                and utils_call._is_current_customer_specialist(ticket, user.pk)
            ):
                ticket.specialist = user
                ticket.save(update_fields=('specialist',))

        recipients = utils_call.get_call_notification_recipients(call_obj)
        transaction.on_commit(
            lambda: utils_call.send_socketio_about_call_updated(
                call_obj,
                old_status=old_status,
                recipients=recipients,
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_notification,
                call_obj,
                user,
                recipients=list(recipients),
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_push,
                call_obj,
                user,
                old_status=old_status,
                recipients=list(recipients),
            )
        )
        if ticket is not None:
            transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))
        return Response(serializers.CallListSerializer(call_obj, context={'request': request}).data)

    @action(methods=('post',), detail=True, url_path='reject')
    def reject(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        with transaction.atomic():
            try:
                call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
                    'ticket',
                ).get(pk=pk, is_active=True)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound('call not found')
            if not call_obj.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()
            if call_obj.status_id not in ('connecting', 'ringing'):
                raise drf_exceptions.ValidationError('Нельзя отклонить звонок в текущем статусе')
            current_target_ids = utils_call.get_current_target_ids(call_obj)
            if current_target_ids and user.pk not in current_target_ids:
                raise drf_exceptions.PermissionDenied('Сейчас звонок направлен другому участнику')
            old_status = call_obj.status_id
            if len(current_target_ids) > 1:
                remaining_target_ids = [target_id for target_id in current_target_ids if target_id != user.pk]
                utils_call.set_current_targets(call_obj, remaining_target_ids)
                recipients = utils_call.get_call_notification_recipients(call_obj)
                recipients.add(user.pk)
                has_next_target = True
            else:
                has_next_target, recipients = utils_call.advance_call_queue(
                    call_obj=call_obj,
                    old_status=old_status,
                    final_status_if_empty='cancelled_by_receiver',
                    from_profile_id=user.pk,
                )
            ticket = call_obj.ticket

        if has_next_target:
            transaction.on_commit(lambda: utils_call.schedule_ring_timeout_for_call(call_obj))
        transaction.on_commit(
            lambda: utils_call.send_socketio_about_call_updated(
                call_obj,
                old_status=old_status,
                recipients=recipients,
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_notification,
                call_obj,
                user,
                recipients=list(recipients),
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_push,
                call_obj,
                user,
                old_status=old_status,
                recipients=list(recipients),
            )
        )
        if ticket is not None:
            transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))
        return Response(serializers.CallListSerializer(call_obj, context={'request': request}).data)

    @action(methods=('post',), detail=True, url_path='end')
    def end(self, request, pk=None, *args, **kwargs):
        user = request.user.profile
        meeting_to_complete = None
        with transaction.atomic():
            try:
                call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
                    'ticket',
                    'meeting__server',
                ).get(pk=pk, is_active=True)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound('call not found')
            if not call_obj.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()
            if call_obj.status_id != 'in_call':
                raise drf_exceptions.ValidationError('Нельзя завершить звонок в текущем статусе')
            old_status = call_obj.status_id
            call_obj.status_id = 'ended'
            call_obj.ended_at = timezone.now()
            call_obj.save(update_fields=('status', 'ended_at'))
            ticket = call_obj.ticket
            recipients = utils_call.get_call_notification_recipients(call_obj)
            if call_obj.meeting_id:
                meeting_to_complete = call_obj.meeting

        if meeting_to_complete is not None:
            params = 'meetingID=' + str(meeting_to_complete.id) + '&password=' + str(meeting_to_complete.moderatorPW)
            hash_url = get_hash_url('end', params, meeting_to_complete.server)
            try:
                requests.get(hash_url)
            except Exception:
                pass
            MeetingConnectMixin.complete_meeting(meeting_to_complete)
        transaction.on_commit(lambda: utils_call.send_socketio_about_call_updated(call_obj, old_status=old_status, recipients=recipients))
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_notification,
                call_obj,
                user,
                recipients=list(recipients),
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_push,
                call_obj,
                user,
                old_status=old_status,
                recipients=list(recipients),
            )
        )
        if ticket is not None:
            transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))
        return Response(serializers.CallListSerializer(call_obj, context={'request': request}).data)

    @action(methods=('post',), detail=True, url_path='transfer')
    def transfer(self, request, pk=None, *args, **kwargs):
        to_profile_id = request.data.get('to_profile_id')
        from_profile = request.user.profile

        if not to_profile_id:
            raise drf_exceptions.ValidationError({'to_profile_id': 'Поле обязательно'})

        with transaction.atomic():
            try:
                call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
                    'ticket__customer_card',
                    'ticket__contact_person',
                ).get(pk=pk, is_active=True)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound('call not found')
            if not call_obj.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()
            if not call_obj.ticket_id:
                raise drf_exceptions.ValidationError('Передача доступна только для звонков, связанных с обращением')
            if call_obj.status_id not in ('in_call', 'connecting', 'ringing'):
                raise drf_exceptions.ValidationError('Передача доступна только для активных звонков')

            current_target_ids = utils_call.get_current_target_ids(call_obj)
            if call_obj.status_id == 'in_call':
                if call_obj.accepted_by_id != from_profile.pk:
                    raise drf_exceptions.PermissionDenied('Передавать звонок может только текущий принявший специалист')
            else:
                if not current_target_ids:
                    raise drf_exceptions.ValidationError('Передача недоступна: у звонка отсутствует current_target')
                if from_profile.pk not in current_target_ids:
                    raise drf_exceptions.PermissionDenied('Передавать звонок может только текущий получатель звонка')

            from_profile_support_orgs = contractors_where_user_has_app_section_role_permission(
                from_profile.pk,
                'help_desk',
            )
            if not from_profile_support_orgs:
                raise drf_exceptions.PermissionDenied('Передавать звонок может только специалист техподдержки')

            ticket = call_obj.ticket
            is_target_in_customer_card_support = ticket.customer_card.customer_support_specialists.filter(
                user_id=to_profile_id,
                is_active=True,
            ).exists()
            if not is_target_in_customer_card_support:
                raise drf_exceptions.ValidationError(
                    'Нельзя передать: получатель не является специалистом карточки клиента обращения'
                )

            to_profile = ProfileModel.objects.filter(
                is_active=True,
                pk=to_profile_id,
            ).first()
            if not to_profile:
                raise drf_exceptions.ValidationError({'to_profile_id': 'Пользователь не найден'})

            old_status = call_obj.status_id
            action_dt = timezone.now()
            call_obj.status_id = 'ringing'
            call_obj.accepted_by = None
            call_obj.answered_at = None
            call_obj.ring_attempt = (call_obj.ring_attempt or 0) + 1
            call_obj.ring_started_at = action_dt
            call_obj.save(
                update_fields=('status', 'accepted_by', 'answered_at', 'ring_attempt', 'ring_started_at')
            )
            utils_call.set_current_targets(call_obj, [to_profile.pk])
            if ticket.specialist_id != to_profile.pk:
                ticket.specialist = to_profile
                ticket.save(update_fields=('specialist',))

            recipients = utils_call.get_call_notification_recipients(call_obj)
            recipients.add(from_profile.pk)

        transaction.on_commit(
            lambda: utils_call.send_socketio_about_call_updated(
                call_obj,
                old_status=old_status,
                recipients=recipients,
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_notification,
                call_obj,
                from_profile,
                recipients=list(recipients),
            )
        )
        transaction.on_commit(
            lambda: async_task(
                notifications.notify_about_call_updated_push,
                call_obj,
                from_profile,
                old_status=old_status,
                recipients=list(recipients),
            )
        )
        transaction.on_commit(lambda: utils_call.schedule_ring_timeout_for_call(call_obj, allow_queue_advance=False))
        transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))
        return Response(serializers.CallListSerializer(call_obj, context={'request': request}).data)


class MeetingRecordDetailView(generics.RetrieveAPIView):
    """Эндпойнт для получения детальной информации о записи встречи."""
    queryset = models.MeetingRecordsModel.objects.filter(is_active=True)
    serializer_class = serializers.MeetingRecordDetailSerializer
    permission_classes = (IsAuthenticated,)


class MeetingRecordTranscribeView(APIView):
    """Эндпойнт для запуска процесса транскрибации записи встречи."""
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        meeting_record = models.MeetingRecordsModel.objects.get(pk=pk)
        if meeting_record.status in ['done', 'processing']:
            return Response({'detail': 'Процесс транскрибации уже был запущен.'}, status=status.HTTP_400_BAD_REQUEST)
        async_task(process_meeting_record, meeting_record.pk)
        return Response({'detail': 'Процесс транскрибации запущен в фоновом режиме.'}, status=status.HTTP_200_OK)


class MeetingModelViewSet(BaseModelViewSet):
    """Этот вьюсет нужен, чтобы были стандартные эндпойнты DRF для CRUD-операций.
    Действует как прокси для других (рабочих) вьюсетов. Для ИИ-ассистента."""
    model = models.PlannedMeetingModel
    permission_classes = (IsAuthenticated,)
    queryset = models.PlannedMeetingModel.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        """Прокси для PlannedMeetingCreateView"""
        view = PlannedMeetingCreateView()
        view.request = request
        view.format_kwarg = self.format_kwarg
        return view.post(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """Прокси для PlannedMeetingFilteredList"""
        view = PlannedMeetingFilteredList()
        view.request = request
        view.format_kwarg = self.format_kwarg
        return view.get(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Прокси для MeetingDetailView"""
        view = MeetingDetailView()
        view.request = request
        view.format_kwarg = self.format_kwarg
        view.kwargs = kwargs
        return view.get(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Прокси для PlannedMeetingUpdate"""
        view = PlannedMeetingUpdate()
        view.request = request
        view.format_kwarg = self.format_kwarg
        return view.patch(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Прокси для PlannedMeetingUpdate"""
        view = PlannedMeetingUpdate()
        view.request = request
        view.format_kwarg = self.format_kwarg
        return view.patch(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Вызывает метод set_is_active экземпляра объекта, передавая в него (False, request)"""
        instance = self.get_object()
        instance.set_is_active(False, request)
        instance.save(update_fields=('is_active', 'deleted_at'))
        return Response(status=status.HTTP_204_NO_CONTENT)


class StartRelatedMeetingView(APIView, MeetingConnectMixin):
    """Универсальный эндпойнт для запуска собрания, привязанного к объекту (related_object)."""
    permission_classes = (IsAuthenticated,)

    def _run_start_related(self, request, related_object_id, notify_user_ids):
        try:
            original_object = BaseModel.objects.super_get(pk=related_object_id)
        except (ObjectDoesNotExist, ValidationError):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not original_object.get_detail_permission(request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        object_name = str(original_object)
        project_id = get_meeting_project_for_related_object(original_object)

        with transaction.atomic():
            meeting = get_related_meeting(original_object)

            if not meeting:
                meeting = models.PlannedMeetingModel.objects.create(
                    related_object_id=related_object_id,
                    name=object_name,
                    date_begin=timezone.now(),
                    duration=60,
                    project_id=project_id,
                )
            else:
                has_linked_event = meeting.calendar_events.filter(is_active=True).exists()

                if not has_linked_event:
                    meeting.name = object_name
                    meeting.date_begin = timezone.now()
                    meeting.duration = 60
                    meeting.project_id = project_id
                    meeting.save(update_fields=('name', 'date_begin', 'duration', 'project_id'))

            if meeting.status != 'online':
                self.start_meeting(meeting, request.user.profile, notify_user_ids=notify_user_ids)

        response_data = meeting.get_connect_info()
        return Response(response_data, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        related_object_id = request.query_params.get('related_object')
        if not related_object_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return self._run_start_related(request, related_object_id, None)

    def post(self, request, *args, **kwargs):
        related_object_id = request.data.get('related_object') or request.query_params.get('related_object')
        if not related_object_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        notify_user_ids = request.data.get('notify_user_ids')
        if not isinstance(notify_user_ids, list):
            notify_user_ids = None
        return self._run_start_related(request, related_object_id, notify_user_ids)

