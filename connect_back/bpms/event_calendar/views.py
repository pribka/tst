from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Value, Q
from django.utils import timezone
from django.shortcuts import redirect

from django_q.tasks import async_task

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import exceptions as drf_exceptions
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from bkz3.settings import TIME_ZONE

from common.views import BaseCatalogViewSet, BaseModelViewSet
from common.paginators import CustomPagination
from users.models import ProfileModel
from users.serializers import AppUserShortSerializer

from common.catalogs.models import ContractorModel
from common.catalogs.serializers import ContractorModelShortSerializer

from app_info.models import AppInfo
from . import models, serializers, utils, permissions, notifications
from bpms.favorites.models import FavoriteModel
from bpms.tasks import permissions as tasks_permissions
from bpms.tasks.models import TaskModel, TaskExecutionTimeModel


class CalendarModelViewSet(BaseCatalogViewSet):
    model = models.CalendarModel
    permission_classes = (IsAuthenticated, permissions.CalendarModelPermission)

    @action(methods=('get',), detail=False, url_path='related/(?P<pk>[^/.]+)')
    def get_related_calendar(self, request, *args, **kwargs):
        related_object_id = kwargs.get('pk')
        instance = utils.get_or_create_related_calendar(request, related_object_id)
        data = serializers.CalendarModelListSerializer(instance).data
        return Response(data)

    def list(self, request, *args, **kwargs):
        user = request.user.profile
        if not models.CalendarModel.objects.filter(author=user, related_object__isnull=True).exists():
            utils.create_first_personal_calendar(request)
        queryset = self.filter_queryset(self.get_queryset()).filter(author=user, related_object__isnull=True)
        custom_set = utils.get_custom_set(request)
        personal_calendars = custom_set.personal_calendars
        if personal_calendars == 'all':
            queryset = queryset.annotate(checked=Value(True))
        elif not personal_calendars:
            queryset = queryset.annotate(checked=Value(False))
        else:
            selected_calendars = queryset.filter(pk__in=personal_calendars).annotate(checked=Value(True))
            queryset = selected_calendars.union(
                queryset.exclude(pk__in=personal_calendars).annotate(checked=Value(False))
            )
        queryset = queryset.order_by('-checked', *self.model.get_order_param())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='resources')
    def get_resources(self, request, *args, **kwargs):
        queryset = self.model.objects.filter(
            is_active=True,
            related_object__isnull=True,
            calendar_group_id='resources'
        ).order_by('sort')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('get', 'post',), detail=False, url_path='check_personal')
    def check_personal(self, request, *args, **kwargs):
        if request.method == 'POST':
            data = request.data
            custom_set = utils.get_custom_set(request)
            custom_set.personal_calendars = data
            custom_set.save()
        else:
            custom_set = utils.get_custom_set(request)
        return Response(custom_set.personal_calendars)

    @action(methods=('get', 'post',), detail=False, url_path='check_group')
    def check_group(self, request, *args, **kwargs):
        if request.method == 'POST':
            data = request.data
            custom_set = utils.get_custom_set(request)
            custom_set.group_calendars = data
            custom_set.save()
        else:
            custom_set = utils.get_custom_set(request)
        return Response(custom_set.group_calendars)

    @action(methods=('get',), detail=False, url_path='group_calendars')
    def get_group_calendars(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(code='calendars_group_calendars', is_active=True).metadata
        except AppInfo.DoesNotExist:
            data = serializers.CalendarGroupModelSerializer(
                models.CalendarGroupModel.objects.filter(is_active=True).order_by('sort', 'name'),
                many=True
            ).data
        custom_set = utils.get_custom_set(request)
        group_calendars = custom_set.group_calendars
        if group_calendars == 'all':
            for each in data:
                each['checked'] = True
        elif not group_calendars:
            for each in data:
                each['checked'] = False
        else:
            for each in data:
                if each.get('id') in group_calendars:
                    each['checked'] = True
                else:
                    each['checked'] = False
            data = sorted(data, key=lambda x: x['checked'], reverse=True)
        return Response(data)

    @action(methods=('get',), detail=False, url_path='info')
    def get_info(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(is_active=True, code='calendars_info').metadata
        except AppInfo.DoesNotExist:
            data = {
                'timeFormat': TIME_ZONE,
                'minTime': 0,
                'maxTime': 24,
            }
        return Response(data)


class EventCalendarModelViewSet(BaseCatalogViewSet):
    model = models.EventCalendarModel
    permission_classes = (IsAuthenticated, permissions.EventCalendarPermission)

    def get_queryset(self):
        qs = models.EventCalendarModel.objects.filter(is_active=True, calendar__is_active=True)
        return qs

    @action(methods=('get',), detail=False, url_path='user_events')
    def get_user_events(self, request, *args, **kwargs, ):
        """События в разрезе пользователей."""
        qs = ProfileModel.objects.filter(is_active=True)
        event_date_gte = request.query_params.get('start')
        event_date_lte = request.query_params.get('end')
        from rest_framework.serializers import DateTimeField
        try:
            event_date_gte_date = DateTimeField().to_internal_value(event_date_gte)
            event_date_lte_date = DateTimeField().to_internal_value(event_date_lte)
        except (TypeError,):
            qs = qs.none()
        else:
            delta = event_date_lte_date - event_date_gte_date
            if 6 < delta.days < 0:
                qs = qs.none()
            else:
                org_id = request.query_params.get('organization')
                if org_id:
                    try:
                        qs = qs.filter(contractors=org_id)
                    except ValidationError:
                        raise drf_exceptions.ValidationError('Invalid organization id')
                access_users_id = utils.get_access_users(request)
                qs = qs.filter(pk__in=access_users_id).distinct()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.UserEventCalendarListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        )
        data = serializer.data
        return paginator.get_paginated_response(data)

    @action(methods=('get',), detail=False, url_path='events_by_user')
    def get_event_by_user(self, request, *args, **kwargs):
        user_id = request.query_params.get('user')
        if not user_id:
            return Response()
        try:
            profile = ProfileModel.objects.get(pk=user_id)
        except (ProfileModel.DoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('User not found')
        if profile.pk not in utils.get_access_users(request):
            raise drf_exceptions.ValidationError('Permission denied')
        qs = models.EventCalendarModel.objects.filter(
            is_active=True,
            calendar__is_active=True,
            members=profile
        ).order_by('-start_at', '-created_at',)
        qs = utils.filter_event_queryset(qs, request)
        serializer = serializers.EventCalendarModelListSerializer(
            qs,
            many=True,
            context={'request': request, 'view': self}
        )
        data = serializer.data
        return Response(data)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                "delete": {"availability": True},
                "edit": {"availability": True},
                "share": {"availability": True},
                "create_accounting": {"availability": True}
            }

        elif instance.get_detail_permission(request):
            actions = {
                "share": {"availability": True},
                "create_accounting": {"availability": True}
            }
        return Response({"actions": actions})

    @action(methods=('post',), detail=True, url_path='escape')
    def escape_event(self, request, *args, **kwargs):
        user = request.user.profile
        instance = self.get_object()
        try:
            event_member = models.EventCalendarMemberModel.objects.get(user=user, event=instance)
        except models.EventCalendarMemberModel.DoesNotExist:
            return Response('ok')
        event_member.delete()
        async_task(notifications.notify_about_escape_from_event, instance, user)
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='create_meeting')
    def create_meeting(self, request, *args, **kwargs):
        """Создать связанное собрание для события (если у события ещё нет собрания)."""
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        try:
            utils.create_meeting_for_calendar_event(instance, request=request)
        except drf_exceptions.ValidationError as err:
            return Response({'detail': err.detail}, status=status.HTTP_400_BAD_REQUEST)
        instance.refresh_from_db()
        serializer = serializers.EventCalendarModelDetailSerializer(
            instance, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=('post',), detail=True, url_path='attendance')
    def update_attendance(self, request, *args, **kwargs):
        user = request.user.profile
        instance = self.get_object()
        try:
            event_member = models.EventCalendarMemberModel.objects.get(user=user, event=instance)
        except models.EventCalendarMemberModel.DoesNotExist:
            raise drf_exceptions.NotFound('Вы не являетесь участником этого события')
        
        serializer = serializers.EventCalendarMemberUpdateSerializer(
            event_member,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='top')
    def get_top_events(self, request, *args, **kwargs):
        user = request.user.profile
        queryset = models.EventCalendarModel.objects.filter(
            Q(author=user) | Q(members=user),
            is_active=True,
            calendar__is_active=True,
            ).order_by('start_at', 'created_at',).distinct()
        queryset = utils.filter_event_queryset(queryset, request)
        related_object_id = request.query_params.get('related_object')
        if related_object_id:
            queryset = queryset.filter(calendar__related_object_id=related_object_id)
        paginate = request.query_params.get('paginate', '')
        if paginate == '1':
            paginator = CustomPagination()
            page = paginator.paginate_queryset(queryset.order_by('-start_at', '-created_at',), request, self)
            s_data = serializers.EventCalendarModelListSerializer(
                page, many=True, context={"request": request}
            ).data
            return paginator.get_paginated_response(s_data)
        else:
            s_data = serializers.EventCalendarModelListSerializer(
                queryset, many=True, context={"request": request}
            ).data
            return Response(s_data)

    def list(self, request, *args, **kwargs):
        related_object_id = request.query_params.get('related_object')
        if related_object_id:
            calendar = utils.get_or_create_related_calendar(request, related_object_id)
            queryset = calendar.events.filter(is_active=True)
            queryset = utils.filter_event_queryset(queryset, request)
            queryset = FavoriteModel.annotate_favorites(queryset)
            queryset = self.filter_queryset(queryset)
        else:
            custom_set = utils.get_custom_set(request)

            personal_calendars = custom_set.personal_calendars
            personal_calendars_qs = utils.get_personal_calendar_qs(request, personal_calendars)
            personal_calendars_qs = FavoriteModel.annotate_favorites(personal_calendars_qs)
            personal_calendars_qs = self.filter_queryset(personal_calendars_qs)
            group_calendars = custom_set.group_calendars
            group_calendars_qs = utils.get_group_calendar_qs(request, group_calendars)
            group_calendars_qs = FavoriteModel.annotate_favorites(group_calendars_qs)
            group_calendars_qs = self.filter_queryset(group_calendars_qs)
            queryset = personal_calendars_qs.union(group_calendars_qs)

        if request.query_params.get('ranges', '') == 'true':
            dates = list(queryset.order_by('start_at',).values('start_at', 'end_at',))
            try:
                current_range = dates[0]
            except IndexError:
                return Response([])
            ranges = []
            i = 0
            while i < len(dates) - 1:
                i += 1
                next_range = dates[i]
                if next_range['end_at'] > current_range['end_at'] > next_range['start_at']:
                    current_range['end_at'] = next_range['end_at']
                elif current_range['end_at'] < next_range['start_at']:
                    ranges.append(current_range)
                    current_range = next_range
            else:
                ranges.append(current_range)
            return Response(ranges)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='my_day')
    def my_day(self, request, *args, **kwargs):
        user_param = request.query_params.get('user')
        profile_id = request.user.profile.pk

        if user_param:
            user_ids = user_param.split(',')
        else:
            user_ids = [str(profile_id)]
        
        # # Проверяем права доступа без запроса к базе - ПОКА НЕ НАДО.
        # access_users = utils.get_access_users(request)
        # access_user_ids = {str(uid) for uid in access_users}
        # for user_id in user_ids:
        #     if user_id not in access_user_ids:
        #         raise drf_exceptions.ValidationError('Permission denied')
        
        qs = utils.get_my_day_event_queryset(request)

        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)

        serializer = serializers.EventCalendarModelMyDaySerializer(
            page,
            many=True,
            context={'request': request, 'view': self, 'user_ids': user_ids}
        )
        data = serializer.data
        return paginator.get_paginated_response(data)


class GoogleCalendarViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'], )
    def synchronize(self, request, pk=None):
        calendars = request.data

        external_calendar, created = models.ExternalCalendarModel.objects.get_or_create(
            code=models.ExternalCalendarModel.GOOGLE,
            defaults={'name': "Google",
                      "code": models.ExternalCalendarModel.GOOGLE})

        utils.set_sync_for_absent_google_calendar_choices(calendars, external_calendar)
        utils.create_or_update_google_calendars(calendars, external_calendar)
        utils.sync_events_from_google_calendars(calendars=calendars, profile=request.user.profile)


        return Response(data=[])


class EventCalendarAccessViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        owner = request.user.profile
        request_data = request.data
        users_id = request_data.get('users')
        orgs_id = request_data.get('organizations')

        with transaction.atomic():
            owner.event_calendar_access_profiles.all().delete()
            user_access_list = []
            for each in users_id:
                user_access = models.EventCalendarAccessProfileModel()
                user_access.owner = owner
                user_access.user_id = each
                user_access_list.append(user_access)
            try:
                models.EventCalendarAccessProfileModel.objects.bulk_create(user_access_list)
            except ValidationError:
                raise drf_exceptions.ValidationError('Invalid users')
            org_access_list = []
            owner.event_calendar_access_org.all().delete()
            for each in orgs_id:
                org_access = models.EventCalendarAccessOrganizationModel()
                org_access.owner = owner
                org_access.organization_id = each
                org_access_list.append(org_access)
            try:
                models.EventCalendarAccessOrganizationModel.objects.bulk_create(org_access_list)
            except ValidationError:
                raise drf_exceptions.ValidationError('Invalid organizations')
            metadata_obj, created = models.EventCalendarAccessProfileMetadataModel.objects.get_or_create(
                user=request.user.profile,
            )
            serializer = serializers.EventCalendarAccessProfileMetadataModelSerializer(
                metadata_obj, data=request_data, context={'request': request, 'view': self}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        data = {
            'users': [],
            'organizations': [],
        }
        user = request.user.profile
        users_id = user.event_calendar_access_profiles.all().values_list('user', flat=True)
        users = ProfileModel.objects.filter(pk__in=users_id)
        context = {'request': request, 'view': self}
        if users:
            serializer = AppUserShortSerializer(users, many=True, context=context)
            data['users'] = serializer.data
        orgs_id = user.event_calendar_access_org.all().values_list('organization', flat=True)
        orgs = ContractorModel.objects.filter(pk__in=orgs_id)
        if orgs:
            serializer = ContractorModelShortSerializer(orgs, many=True, context=context)
            data['organizations'] = serializer.data

        metadata_obj, created = models.EventCalendarAccessProfileMetadataModel.objects.get_or_create(
            user=user,
        )
        metadata = serializers.EventCalendarAccessProfileMetadataModelSerializer(
            metadata_obj, context={'request': request, 'view': self}
        ).data
        data['metadata'] = metadata['metadata']
        return Response(data)

