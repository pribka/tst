from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from bpms.workgroups import models as wg_models
from common import models as c_models
from common.catalogs import models as cat_models
from common.views import BaseCatalogViewSet
from users import models as u_models

from . import models as wl_models
from . import permissions as wl_permissions
from . import serializers as wl_serialisers
from . import utils


class WorkScheduleModelViewSet(BaseCatalogViewSet):
    model = wl_models.WorkScheduleModel
    http_method_names = ('get', 'put', 'options')

    @action(
        methods=('get', 'put'), detail=False,
        url_path=r'(?P<profile>\S+)/schedule',
        permission_classes=(wl_permissions.WorkSchedulePermission,)
    )
    def set_schedule(self, request, profile=None):
        schedule, _ = self.model.objects.get_or_create(profile_id=profile)
        serializer = self.get_serializer(schedule)

        if request.method == 'PUT':  # [do] валидация часов
            data = request.data
            if not data:
                return Response(serializer.data, status.HTTP_204_NO_CONTENT)

            days = data.get('work_days')
            if days is not None:
                for key, value in days.items():
                    if key in schedule.work_days:
                        schedule.work_days[key] = value
                    else:
                        raise drf_exceptions.NotFound(f'"{key}" not found.')

            start_hour = data.get('start_hour')
            end_hour = data.get('end_hour')
            utils.set_time(schedule, 'start_hour', start_hour)
            utils.set_time(schedule, 'end_hour', end_hour)

            break_exist = data.get('break_exist')
            if break_exist is not None:
                schedule.break_exist = break_exist
            break_start = data.get('break_start')
            break_end = data.get('break_end')
            utils.set_time(schedule, 'break_start', break_start)
            utils.set_time(schedule, 'break_end', break_end)

            schedule.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('get',), detail=False,
        url_path=r'(?P<profile>\S+)/schedule/action_info'
    )
    def get_action_info(self, request, profile=None):
        owner = u_models.ProfileModel.objects.get(id=profile)
        object_id = request.query_params.get('related_object')
        related_object = c_models.BaseModel.objects.super_get(pk=object_id)
        actions = {'watch': {'availability': True}}

        if isinstance(related_object, cat_models.ContractorModel):
            user = cat_models.ContractorProfileModel.objects.get(
                user=request.user.profile, contractor=related_object,
            )
            if wg_models.WorkgroupMembersModel.objects.filter(
                member=user.user,
                membership_role__code__in=('MODERATOR', 'FOUNDER')
            ).exists():
                actions.update({
                    'create': {'availability': True},
                    'update': {'availability': True},
                    'delete': {'availability': True},
                })

        if isinstance(related_object, wg_models.WorkgroupModel):
            moder_founder = wg_models.WorkgroupMembersModel.objects.get(
                member=request.user.profile, work_group=related_object,
            )

            if (
                owner == request.user.profile
                or moder_founder.membership_role.code
                in ('MODERATOR', 'FOUNDER')
            ):
                actions.update({
                    'create': {'availability': True},
                    'update': {'availability': True},
                    'delete': {'availability': True},
                })

        return Response({'actions': actions})


class ExceptionModelViewSet(BaseCatalogViewSet):
    model = wl_models.ExceptionModel
    serializer_class = wl_serialisers.ExceptionCUDSerializer
    http_method_names = ('get', 'post', 'put', 'delete', 'options')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = wl_serialisers.ExceptionListSerializer(
            queryset, many=True
        )
        return Response(serializer.data, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = wl_serialisers.ExceptionCUDSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except self.model.DoesNotExist:
            raise drf_exceptions.NotFound('Instance not found.')
        serializer = wl_serialisers.ExceptionCUDSerializer(
            instance, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except self.model.DoesNotExist:
            raise drf_exceptions.NotFound('Instance not found.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()

    @action(
        methods=('get',), detail=False, url_path=r'(?P<profile>\S+)/exceptions'
    )
    def get_exceptions(self, request, profile=None):
        queryset = self.filter_queryset(
            self.get_queryset().filter(profile=profile)
        )

        dates = []
        for obj in queryset:
            dates.extend(obj.dates.all())

        exception_dates = (
            wl_models.ExceptionDatesModel.objects
            .filter(id__in=[i.id for i in dates])
            .select_related('exception')
        )

        year = request.query_params.get('year')
        if year:
            try:
                year = int(year)
            except ValueError:
                raise drf_exceptions.ValidationError({"detail": "Use YYYY."})
            exception_dates = exception_dates.filter(start_date__year=year)

        serializer = wl_serialisers.ExceptionDatesListSerializer(
            exception_dates, many=True
        )
        return Response(serializer.data, status.HTTP_200_OK)

    @action(
        methods=('get',), detail=False,
        url_path=r'(?P<profile>\S+)/exceptions/action_info',
    )
    def get_action_info(self, request, profile=None):
        owner = u_models.ProfileModel.objects.get(id=profile)
        object_id = request.query_params.get('related_object')
        related_object = c_models.BaseModel.objects.super_get(pk=object_id)
        actions = {'watch': {'availability': True}}

        if isinstance(related_object, cat_models.ContractorModel):
            user = cat_models.ContractorProfileModel.objects.get(
                user=request.user.profile, contractor=related_object,
            )
            if wg_models.WorkgroupMembersModel.objects.filter(
                member=user.user,
                membership_role__code__in=('MODERATOR', 'FOUNDER')
            ).exists():
                actions.update({
                    'create': {'availability': True},
                    'update': {'availability': True},
                    'delete': {'availability': True},
                })

        if isinstance(related_object, wg_models.WorkgroupModel):
            moder_founder = wg_models.WorkgroupMembersModel.objects.get(
                member=request.user.profile,
                work_group=related_object,
            )

            if (
                owner == request.user.profile
                or moder_founder.membership_role.code
                in ('MODERATOR', 'FOUNDER')
            ):
                actions.update({
                    'create': {'availability': True},
                    'update': {'availability': True},
                    'delete': {'availability': True},
                })

        return Response({'actions': actions})


class WorkLoadViewSet(BaseCatalogViewSet):
    model = wl_models.WorkLoadModel
    serializer_class = wl_serialisers.WorkLoadSerializer

    @action(
        methods=('get', 'post'), detail=False,
        url_path=r'(?P<related_object>\S+)/members'
    )
    def get_members(self, request, related_object=None):
        related_object = c_models.BaseModel.objects.super_get(
            pk=related_object
        )

        if isinstance(related_object, wg_models.WorkgroupModel):
            profiles = u_models.ProfileModel.objects.filter(
                workgroupmembersmodel__work_group_id=related_object
            )
            for profile in profiles:
                if not wl_models.WorkScheduleModel.objects.filter(
                    profile=profile
                ).exists():
                    wl_models.WorkScheduleModel.objects.create(profile=profile)

        if isinstance(related_object, cat_models.ContractorModel):
            profiles = related_object.profiles.all()
            for profile in profiles:
                if not wl_models.WorkScheduleModel.objects.filter(
                    profile=profile
                ).exists():
                    wl_models.WorkScheduleModel.objects.create(profile=profile)

        members_list, _ = wl_models.MembersListModel.objects.get_or_create(
            related_object=related_object
        )

        if not members_list.members:
            profiles = profiles.annotate(checked=models.Value(False))
        elif members_list.members == 'all':
            profiles = profiles.annotate(checked=models.Value(True))
        else:
            selected_members = (
                profiles.filter(pk__in=members_list.members)
                .annotate(checked=models.Value(True))
            )
            profiles = selected_members.union(
                profiles.exclude(pk__in=members_list.members)
                .annotate(checked=models.Value(False))
            )
            profiles = profiles.order_by('-checked')

        serializer = wl_serialisers.MembersSerializer(
            profiles, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('get', 'post'), detail=False,
        url_path=r'(?P<related_object>\S+)/check_members'
    )
    def check_members(self, request, related_object):

        if request.method == 'POST':
            data = request.data
            members_list, _ = wl_models.MembersListModel.objects.get_or_create(
                related_object=related_object
            )
            members_list.members = data
            members_list.save()
        else:
            members_list, _ = wl_models.MembersListModel.objects.get_or_create(
                related_object=related_object
            )

        return Response(members_list.members, status=status.HTTP_200_OK)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        start_date = self.request.query_params.get('start', None)
        end_date = self.request.query_params.get('end', None)

        if start_date:
            queryset = queryset.filter(date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(date__lte=parse_date(end_date))
        if (start_date and end_date) is not None:
            queryset = queryset.filter(
                date__gte=parse_date(start_date),
                date__lte=parse_date(end_date)
            )

        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        object_id = request.query_params.get('related_object', None)
        related_object = c_models.BaseModel.objects.super_get(pk=object_id)
        try:
            members_list = wl_models.MembersListModel.objects.get(
                related_object=related_object
            )
        except:  # noqa: E722
            members_list = wl_models.MembersListModel.objects.create(
                related_object=related_object, members='all'
            )
        members = members_list.members

        if members_list.members == 'all':
            if isinstance(related_object, wg_models.WorkgroupModel):
                members = u_models.ProfileModel.objects.filter(
                    workgroupmembersmodel__work_group_id=related_object
                ).values_list('pk', flat=True)

            if isinstance(related_object, cat_models.ContractorModel):
                members = u_models.ProfileModel.objects.filter(
                    contractorprofilemodel__contractor_id=related_object
                ).values_list('pk', flat=True)

            if isinstance(related_object, u_models.ProfileModel):
                queryset = queryset.filter(profile_id=related_object.id)
            else:
                queryset = queryset.filter(profile_id__in=members)

        else:
            if isinstance(related_object, u_models.ProfileModel):
                queryset = queryset.filter(profile_id=related_object.id)
            else:
                queryset = queryset.filter(profile_id__in=members)

        tasks = (
            Q(tasks__project__id=related_object.id)
            | Q(tasks__workgroup__id=related_object.id)
            | Q(tasks__organization__id=related_object.id)
        )

        serializer = self.serializer_class(
            queryset.filter(tasks, tasks_num__gte=1).order_by('date'),
            many=True
        )

        return Response(serializer.data, status.HTTP_200_OK)

    @action(('post',), False, 'task_duration')
    def set_task_duration(self, request, *args, **kwargs):
        data = request.data
        is_distributed = data.get('is_distributed', None)
        if is_distributed:
            start = data.get('start', None)
            if start is not None:
                start = datetime.strptime(start, '%Y-%m-%d').date()
            end = data.get('end', None)
            if end is not None:
                end = datetime.strptime(end, '%Y-%m-%d').date()
            try:
                dates_range = utils.get_dates_range(start, end)
            except:  # noqa: E722
                dates_range = []
            durations = []
            for date in dates_range:
                durations.append({'date': str(date), 'hours': 0})
            task_dur, _ = wl_models.TaskDurationModel.objects.get_or_create(
                task__isnull=True,
                is_distributed=is_distributed,
                durations=durations
            )
            serializer = wl_serialisers.TaskDurationSerializer(task_dur)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response({'is_distributed': is_distributed}, status.HTTP_200_OK)

    @action(('post',), False, 'check_overload')
    def check_overload(self, request, *args, **kwargs):
        data = request.data
        date = data.get('date')
        operator = data.get('operator')
        hours = data.get('hours')
        hours = datetime.strptime(f'{hours}:00:00', '%H:%M:%S').time()
        workload = wl_models.WorkLoadModel.objects.get(
            date=date, profile=operator
        )
        duration = utils.add_time(hours, workload.total_duration)
        if duration > workload.profile.schedule.work_hours:
            return Response({'overload': True}, status.HTTP_200_OK)
        return Response({'overload': False}, status.HTTP_200_OK)
