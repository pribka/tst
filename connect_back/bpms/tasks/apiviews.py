import datetime
import json
from tempfile import NamedTemporaryFile
from decimal import InvalidOperation, Decimal
from uuid import UUID

import pandas as pd

from django.db.models import Q, Min, Count, Sum, Avg, Prefetch, Case, When, F, DecimalField, OuterRef, Subquery, Value, \
    BooleanField, IntegerField, DurationField, ExpressionWrapper, Exists
from django.db.models.functions import Coalesce

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404, FileResponse
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.translation import gettext as _
from django.utils import timezone
from django.core.cache import cache
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action, permission_classes

from haystack.query import SearchQuerySet, RelatedSearchQuerySet
from drf_haystack.viewsets import HaystackGenericAPIView
from django_q.tasks import async_task

from common import utils as common_utils
from common.paginators import CustomPagination
from common.views import BaseModelViewSet
from common.models import Organization, BaseModel, FiltersStore
from common.catalogs.models import ContractorModel, PotentialContractorModel
from common.utils import (
    check_request_from_urv,
    get_search_bool,
    get_filter_queryset,
    get_datetime_param,
    get_tariff_section_codes,
)

from common.catalogs.models import MeasureUnitModel
from users.models import CustomUser, ProfileModel
from users.serializers import CachedAppUserPreviewSerializer
from users.utils import get_tree_departments_related_organizations

from app_info.models import AppInfo

from bpms.workgroups.models import WorkgroupModel, WorkgroupMembersModel, WorkgroupMembershipRole, \
    WorkgroupMembershipStatus
from bpms.bpms_common.models import ProfileModel
from bpms.event_calendar.models import EventCalendarModel
from bpms.personal_planes.utils import has_work_plan_access
from bpms.comments.models import CommentModel

from crm.models import GoodsOrderModel, TPGoodsOrderModel

from change_history.models import ChangeHistoryModel

from .utils import get_task_queryset, filter_by_permissions, get_task_sprint_queryset, \
    order_tasks_queryset_from_get_param, get_budget_aggregate_data, get_budget_aggregate_qs, \
    get_difficulty_aggregate_qs, get_difficulty_aggregate_data, create_workbook_task_analytics, \
    plus_one_day_logistic_tasks, delete_task_delivery_points, create_workbook_task_list, \
    get_goods_by_warehouses, create_workbook_interest_list, get_tasks_status_count, get_my_tasks_count, \
    get_gantt_chart_task_queryset, get_tasks_for_sprint_qs, get_sprint_report_file_act, \
    get_sprint_report_file_report, \
    get_all_sprint_tasks, prepare_list_task_queryset, prepare_list_kanban_task_queryset, prepare_my_day_task_queryset, \
    clear_my_day_grouped_cache, get_cached_statuses
from . import utils
from .utils_my_day import get_task_execution_time_dataframe, get_task_status_history_dataframes, \
    STATUS_INWORK_CODES, STATUS_REWORK_CODES, STATUS_COMPLETED_CODES, \
    get_my_day_task_ids_grouped, calculate_actual_duration, calculate_related_profile_ids, \
    build_my_day_analytics, get_my_day_task_queryset, build_action_info_map
from bpms.event_calendar.utils import get_my_day_event_queryset
from bpms.meetings.utils import get_my_day_meeting_sections_queryset
from help_desk.utils_my_day import get_my_day_tickets_queryset
from . import permissions
from . import serializers
from . import models
from . import notifications


# CRM: LLM-анализ интереса не просто читает данные, а создает/перезаписывает
# потребности. Поэтому фронту отдаем не только 403, но и понятное объяснение,
# почему кнопка анализа недоступна конкретному пользователю.
INTEREST_ANALYZE_ALLOWED_ROLE_LABELS = ('постановщик', 'модератор проекта')
TASK_ROLE_LABELS = {
    'owner': 'постановщик',
    'operator': 'ответственный',
    'cooperator': 'соисполнитель',
    'visor': 'наблюдатель',
    'project_moderator': 'модератор проекта',
}


def get_interest_analyze_permission_info(task, request):
    """Вернуть права и текст причины для кнопки LLM-анализа в карточке интереса."""
    can_analyze = task.get_update_permission(request)
    if can_analyze:
        return {
            'can_analyze_interest': True,
            'analyze_interest_permission_message': '',
        }

    roles = sorted(set(task.get_task_roles(request.user.profile.pk)))
    role_labels = [TASK_ROLE_LABELS.get(role, role) for role in roles]
    role_text = ', '.join(role_labels) if role_labels else 'нет роли в этом интересе'
    allowed_text = ' или '.join(INTEREST_ANALYZE_ALLOWED_ROLE_LABELS)
    return {
        'can_analyze_interest': False,
        'current_roles': roles,
        'allowed_roles': ('owner', 'project_moderator'),
        'analyze_interest_permission_message': (
            f'LLM-анализ изменяет интерес: создает или обновляет потребности клиента. '
            f'Запуск доступен только роли: {allowed_text}. '
            f'Ваша текущая роль: {role_text}.'
        ),
    }


class SprintActionInfoView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.TaskSprintModel.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.get_update_permission(request):
            data = {
                'edit': {'availability': True},
                'delete': {'availability': True},
                'set_status': {'availability': True},
            }
            if not instance.status == 'completed':
                data['set_task'] = {'availability': True}
        else:
            data = dict()
        return Response(data)


class CreateSprintView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TaskSprintCreateSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


class UpdateSprintView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateSprintPermission)
    serializer_class = serializers.TaskSprintUpdateSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


class UpdateTaskSprintStatusView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateTaskSprintStatusPermission)
    serializer_class = serializers.TaskSprintUpdateStatusSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


class DetailSprintView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailSprintPermission)
    serializer_class = serializers.TaskSprintDetailSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


class ListTasksBySprintListView(generics.ListAPIView):
    """Список задач, добавленных в спринт."""
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ListTasksBySprintListSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)
    pagination_class = CustomPagination
    model = models.TaskModel

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if pk:
            try:
                sprint = models.TaskSprintModel.objects.get(pk=pk)
            except ObjectDoesNotExist:
                raise exceptions.NotFound()
            query_params = request.query_params
            display = query_params.get('display')
            if display == 'opened':
                queryset = sprint.tasks.filter(is_active=True).exclude(status_id='completed')
            elif display == 'completed':
                queryset = sprint.tasks.filter(is_active=True, status_id='completed')
            elif display == 'after_start':
                tasks_id = utils.get_tasks_after_start_sprint_id(sprint)
                queryset = models.TaskModel.objects.filter(pk__in=tasks_id)
            elif display == 'moved_to_backlog':
                moved_tasks = sprint.task_sprint_history.filter(moved_to='backlog').values_list('task', flat=True)
                queryset = self.model.objects.filter(is_active=True, pk__in=moved_tasks)
            elif display == 'moved_to_sprint':
                moved_tasks = sprint.task_sprint_history.filter(moved_to='sprint').values_list('task', flat=True)
                queryset = self.model.objects.filter(is_active=True, pk__in=moved_tasks)
            else:
                queryset = sprint.tasks.filter(is_active=True)
            if queryset.exists():
                queryset = order_tasks_queryset_from_get_param(
                    request, get_task_queryset(self.request, queryset, list_type='sprint_list')
                )
                qs_pk = queryset.values_list('id', flat=True)
                qs_pk = self.paginate_queryset(qs_pk)
                qs = self.model.objects.all().filter(pk__in=qs_pk)
                qs = prepare_list_task_queryset(qs, request)
                qs = qs.order_by(*(queryset.query.order_by))
            else:
                qs = self.paginate_queryset(queryset)
            serialized_data = self.serializer_class(
                qs,
                many=True,
                context={'request': request, 'view': self, 'sprint': sprint}
            ).data
            return self.get_paginated_response(serialized_data)
        raise Http404()


class TaskCountSprintView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)  # TODO
    serializer_class = serializers.TaskCountSprintSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


class ReportSprintView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailSprintPermission,)
    serializer_class = serializers.ReportSprintSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


# Статистика по спринтам
class ReportTimeSprintView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailSprintPermission,)
    serializer_class = serializers.ReportTimeSprintSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)


class ReportTasksSprintView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailSprintPermission,)
    serializer_class = serializers.TaskSprintReportSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user_id = request.query_params.get('user')
        tasks_id = get_all_sprint_tasks(instance)
        qs = models.TaskModel.objects.filter(pk__in=tasks_id)
        display = request.query_params.get('display', '')
        if display == 'only_time_tracking':
            execution_times = models.TaskExecutionTimeModel.objects.filter(
                is_active=True,
                sprint=instance,
            ).values_list('pk', flat=True)
            qs = qs.filter(
                execution_time__in=execution_times,
            ).distinct()
        if user_id:
            execution_times = models.TaskExecutionTimeModel.objects.filter(
                is_active=True,
                user_id=user_id,
                sprint=instance,
            ).values_list('pk', flat=True)
            qs = qs.filter(
                execution_time__in=execution_times,
            ).distinct()
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serialized_data = self.serializer_class(page, many=True, context={
            'request': request,
            'view': self,
            'sprint': instance,
            'user_id': user_id,
        }).data
        response = paginator.get_paginated_response(serialized_data)
        return response


class ReportFileSprintView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailSprintPermission,)
    serializer_class = serializers.TaskSprintDetailSerializer
    queryset = models.TaskSprintModel.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        from tempfile import NamedTemporaryFile
        query_params = request.query_params
        file_code = query_params.get('file_code', 'act')
        file_type = query_params.get('file_type', 'xlsx')
        if file_code == 'act':
            wb = get_sprint_report_file_act(self.get_object())
        elif file_code == 'report':
            wb = get_sprint_report_file_report(self.get_object())
        else:
            raise exceptions.ValidationError('Код файла не существует')
        with NamedTemporaryFile() as tmp_file:
            wb.save(tmp_file.name)
            return FileResponse(
                open(tmp_file.name, 'rb', ),
                filename=f'{file_code}.xlsx',
                as_attachment=True,
            )


class ListSprintView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TaskSprintListSerializer
    queryset = models.TaskSprintModel.objects.select_related('author__organizations').filter(is_active=True)
    pagination_class = CustomPagination

    def get_queryset(self):
        filtered_qs = get_task_sprint_queryset(self.request)
        if not filtered_qs.ordered:
            filtered_qs = filtered_qs.order_by('-created_at')
        search = self.request.query_params.get('search')
        if search and len(search) >= 3:
            filtered_qs = filtered_qs.filter(name__icontains=search)
        filtered_qs = filtered_qs.prefetch_related('projects')
        return filtered_qs


class SearchSprintView(HaystackGenericAPIView):
    index_models = (models.TaskSprintModel,)
    serializer_class = serializers.TaskSprintSearchSerializer
    pagination_class = CustomPagination
    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request, *args, **kwargs):
        text = request.query_params.get('text')
        boolean_value = get_search_bool()
        if not text:
            search_queryset = SearchQuerySet().none()
        else:
            search_queryset = RelatedSearchQuerySet().filter(
                text=text, is_active=boolean_value,
            ).models(models.TaskSprintModel).load_all()
        ordering = request.query_params.get('ordering').split(',')
        if ordering:
            search_queryset = search_queryset.order_by(*ordering)
        page = self.paginate_queryset(list(search_queryset))
        s_data = self.serializer_class(page, many=True, context={'request': request}).data
        return self.get_paginated_response(s_data)


class ListSprintTaskView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ListTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)
    pagination_class = CustomPagination
    model = models.TaskModel

    def get_queryset(self):
        return get_tasks_for_sprint_qs(self.queryset, self.request)


class CreateTaskView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated | permissions.IsBySecretAuthenticated,)
    serializer_class = serializers.CreateTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)

    def perform_create(self, serializer):
        is_secret_auth = isinstance(self.request.auth, type(None)) and hasattr(self.request,
                                                                               'data') and 'secret' in self.request.data
        serializer.save(is_sign_task=is_secret_auth)


class BulkDeleteTaskView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        from bpms.tasks.utils import create_temp_bases
        create_temp_bases()
        task_quantity = self.request.query_params.get('task_quantity', None)

        tasks = models.TaskModel.objects.filter(is_active=True).order_by('-created_at')[:int(task_quantity)]
        points = models.TaskPointModel.objects.filter(is_active=True).order_by('-created_at')[:int(task_quantity)]

        for point in points:
            point.delete()

        for task in tasks:
            task.delete()

        return Response({f'Удалено {task_quantity} задач и точек'})


class BulkCreateTaskView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        import uuid
        import random
        task_quantity = self.request.query_params.get('task_quantity', None)

        lat_range = (51.308296457825, 50.980047046302)
        lon_range = (71.171493530273, 71.722869873047)

        statuses = models.TaskStatusModel.objects.filter(is_active=True).exclude(color='default')

        for _ in range(int(task_quantity)):
            task = models.TaskModel.objects.create(
                name=str(uuid.uuid4()),
                status=random.choice(statuses)
            )
            models.TaskPointModel.objects.create(
                lat=random.uniform(*lat_range),
                lon=random.uniform(*lon_range),
                name=str(uuid.uuid4()),
                address=str(uuid.uuid4()) * 5,
                task=task
            )
        return Response({f'Создано {task_quantity} задач с точками'})


class CreateTaskFromOrderView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CreateTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)

    def post(self, request, *args, **kwargs):
        data = request.data
        user = request.user.profile
        order_id = data.get('order')
        if not order_id:
            raise exceptions.ValidationError('Order is empty.')
        try:
            order = apps.get_model('crm', 'GoodsOrderModel').objects.get(pk=order_id, is_active=True)
        except ObjectDoesNotExist:
            raise exceptions.ValidationError('Order not found.')
        # Проверяем права пользователя:
        logistic_manager = order.logistic_manager
        is_logistic_manager = logistic_manager is not None and user == logistic_manager
        if not user.can_create_logistic_task and not is_logistic_manager:
            raise exceptions.PermissionDenied()
        start_point_id = data.get('start_point')
        if not start_point_id:
            warehouse = order.warehouse
            if warehouse:
                start_point_id = warehouse.delivery_point_id
            else:
                raise exceptions.ValidationError('warehouse is empty.')
        else:
            exceptions.ValidationError('start point is empty.')
        from common.catalogs.models import DeliveryPointModel
        try:
            start_point = DeliveryPointModel.objects.get(pk=start_point_id, is_active=True)
        except ObjectDoesNotExist:
            raise exceptions.ValidationError('Start point not found.')
        # Валидация данных о задаче
        task_data = data.get('task')
        if not isinstance(task_data, dict):
            raise exceptions.ValidationError('Incorrect task data.')
        task_data['task_type'] = 'logistic'
        task_serializer = self.serializer_class(data=data.get('task'))
        task_serializer.is_valid(raise_exception=True)
        # Валидация данных о точке доставки
        delivery_point_serializer = serializers.TaskDeliveryPointCreateFromOrderSerializer(
            data=data.get('delivery_point'))
        delivery_point_serializer.is_valid(raise_exception=True)
        # Создаем логистическую задачу
        with transaction.atomic():
            task = task_serializer.save()
            # Создаем стартовую точку
            start_delivery_point = models.TaskDeliveryPointModel()
            start_delivery_point.task = task
            start_delivery_point.is_start = True
            start_delivery_point.delivery_point = start_point
            start_delivery_point.save()
            # Создаем конечную точку
            delivery_point = delivery_point_serializer.save()
            delivery_point.task = task
            delivery_point.delivery_point = order.delivery_point
            delivery_point.save(update_fields=('task', 'delivery_point'))
            # Привязываем точки к заказу:
            order.start_task_delivery_point = start_delivery_point
            order.task_delivery_point = delivery_point
            order.operator = task.operator
            order.save(update_fields=('start_task_delivery_point', 'task_delivery_point', 'operator'))
        async_task(notifications.notify_driver_about_start_order, task, order, request.user.profile)
        async_task(notifications.notify_order_user_about_start_order, task, order, request.user.profile)
        return Response(task_serializer.data)


class SprintExpectedResultView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SprintExpectedResultListSerializer
    queryset = models.SprintExpectedResultModel.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        sprint_id = kwargs.get('pk')
        try:
            sprint = models.TaskSprintModel.objects.get(pk=sprint_id, is_active=True)
        except ObjectDoesNotExist:
            raise exceptions.NotFound('Спринт не найден')
        if not sprint.get_detail_permission(request):
            raise exceptions.PermissionDenied()
        qs = utils.get_expected_results_qs(sprint).order_by('task__counter')
        qs = qs.annotate(
            **{
                'result': F('task__result'),
                'operator': F('task__operator__user__last_name'),
                'dead_line': F('task__dead_line'),
                'status': F('task__status__name'),
                'task.counter': F('task__counter'),
            }
        )
        qs = utils.order_queryset_from_get_param(
            self.request,
            models.SprintExpectedResultModel,
            utils.get_filter_queryset(self.request, models.SprintExpectedResultModel, qs)
        )
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = self.serializer_class(
            page,
            many=True,
            context={'request': request, 'view': self},
        ).data
        return paginator.get_paginated_response(s_data)


class SprintAnalyticView(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.TaskSprintModel.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        sprint_id = kwargs.get('pk')
        try:
            sprint = models.TaskSprintModel.objects.get(pk=sprint_id, is_active=True)
        except ObjectDoesNotExist:
            raise exceptions.NotFound('Спринт не найден')
        if not sprint.get_detail_permission(request):
            raise exceptions.PermissionDenied()

        completed_tasks_count = sprint.tasks.filter(status_id='completed', ).count()
        excluded_tasks = sprint.task_sprint_history.filter(for_completed=True)
        uncompleted_tasks_count = sprint.tasks.exclude(status_id='completed').count() + excluded_tasks.count()
        all_tasks_count = completed_tasks_count + uncompleted_tasks_count
        try:
            completed_tasks_count_percent = round((completed_tasks_count * 100) / all_tasks_count, 2)
        except ZeroDivisionError:
            completed_tasks_count_percent = 0
            completed_tasks_count_percent_str = '-'
        else:
            completed_tasks_count_percent_str = completed_tasks_count_percent
        completed_tasks_count_value = f"{completed_tasks_count}/{completed_tasks_count_percent_str}%"
        excluded_tasks_in_sprint_count = excluded_tasks.filter(moved_to='sprint').count()
        try:
            excluded_tasks_in_sprint_count_percent = round((excluded_tasks_in_sprint_count * 100) / all_tasks_count, 2)
        except ZeroDivisionError:
            excluded_tasks_in_sprint_count_percent = '-'

        expected_results = utils.get_expected_results_qs(sprint)
        if not expected_results.exists():
            goal_achieved = True
        else:
            goal_achieved = not expected_results.filter(approved=False).exists()
        if not expected_results.exists():
            approved_results_count = 0
            approved_results_count_percent = 0
        else:
            approved_results_count = expected_results.filter(approved=True).count()
            approved_results_count_percent = round((approved_results_count * 100) / expected_results.count(), 2)

        blocked_tasks_count = sprint.tasks.filter(object_tags__isnull=False).exclude(status_id='completed', ).count() + \
                              excluded_tasks.filter(blockers__isnull=False).count()

        sprint_tasks = sprint.tasks.filter(is_active=True)
        on_check_sprint_tasks_count = sprint_tasks.filter(status_id__in=('on_check', 'on_testing')).count()
        on_check_excluded_sprint_task_count = excluded_tasks.filter(status_id__in=('on_check', 'on_testing')).count()
        on_check_count = on_check_sprint_tasks_count + on_check_excluded_sprint_task_count
        execution_time_fact = models.TaskExecutionTimeModel.objects.filter(
            sprint=sprint,
            is_active=True,
        ).aggregate(hours_sum=Sum('hours'))['hours_sum']
        if execution_time_fact is None:
            execution_time_fact = 0
        else:
            execution_time_fact = float(execution_time_fact)
        sprint_tasks_execution_time_plan = sprint_tasks.aggregate(hours_sum=Sum('execution_time_plan'))['hours_sum']
        if sprint_tasks_execution_time_plan is None:
            sprint_tasks_execution_time_plan = 0
        else:
            sprint_tasks_execution_time_plan = float(sprint_tasks_execution_time_plan)
        excluded_tasks_execution_time_plan = excluded_tasks.aggregate(hours_sum=Sum('task__execution_time_plan'))[
            'hours_sum']
        if excluded_tasks_execution_time_plan is None:
            excluded_tasks_execution_time_plan = 0
        else:
            excluded_tasks_execution_time_plan = float(excluded_tasks_execution_time_plan)
        execution_time_plan = sprint_tasks_execution_time_plan + excluded_tasks_execution_time_plan
        execution_time_diff = execution_time_plan - execution_time_fact
        try:
            execution_time_diff_percent = round((execution_time_diff * 100) / execution_time_plan, 2)
        except (InvalidOperation, ZeroDivisionError):
            execution_time_diff_percent = 0

        after_start_tasks_id = utils.get_tasks_after_start_sprint_id(sprint)

        task_operators = set(sprint_tasks.values_list('operator', flat=True))
        history_task_operators = set(excluded_tasks.values_list('task__operator', flat=True))
        operators = task_operators | history_task_operators
        have_looser = False
        for each in operators:
            if sprint_tasks.filter(
                    operator_id=each, status_id='completed'
            ).exists() or excluded_tasks.filter(
                task__operator_id=each, status_id='completed'
            ).exists():
                pass
            else:
                have_looser = True
                break
        retro_authors_count = sprint.related_retrospectives.filter(
            is_active=True).aggregate(author_count=Count('author', distinct=True))['author_count']
        if retro_authors_count is None:
            retro_authors_count = 0
        retro_ideas_count = sprint.related_retrospectives.filter(
            is_active=True,
            retrospective_type_id='ideas',
        ).count()

        included_tasks_members_id, excluded_tasks_members_id = utils.get_sprint_members_set(sprint)
        members_id_count = len(included_tasks_members_id | excluded_tasks_members_id)
        have_blockers = bool(blocked_tasks_count)
        diff_name = _('отклонение')
        table = [
            {
                'name': _('Результативность'),
                'value': [
                    {
                        'name': _('Достижение цели'),
                        'value': _('Да') if goal_achieved else _('Нет')
                    },
                    {
                        'name': _('Завершено задач в спринте'),
                        'value': completed_tasks_count_value
                    },
                    {
                        'name': _('Перешло в другой спринт'),
                        'value': f'{excluded_tasks_in_sprint_count}/{excluded_tasks_in_sprint_count_percent}%'
                    },
                    {
                        'name': _('Принято ценностей'),
                        'value': f'{approved_results_count}/{approved_results_count_percent}%'
                    }
                ]
            },
            {
                'name': _('Процесс'),
                'value': [
                    {
                        'name': _('Заблокировано задач'),
                        'value': blocked_tasks_count,
                    },
                    {
                        'name': _('Задачи со статусом "На проверке" и "На приемке"'),
                        'value': on_check_count,
                    },
                    {
                        'name': _('Количество незапланированных задач'),
                        'value': len(after_start_tasks_id),
                    },
                    {
                        'name': _('Трудозатраты (план/факт)'),
                        'value': f'{execution_time_plan}/{execution_time_fact} ({diff_name} {execution_time_diff_percent}%)',
                    }
                ]
            },
            {
                'name': _('Команда и нагрузка'),
                'value': [
                    {
                        'name': _('Отсутствие блокеров после завершения спринта'),
                        'value': _('Да') if not have_blockers else _('Нет'),
                    },
                    {
                        'name': _('Отсутствует участник с 0 завершенными задачами'),
                        'value': _('Да') if not have_looser else _('Нет'),
                    }
                ]
            },
            {
                'name': _('Улучшения и ретроспектива'),
                'value': [
                    {
                        'name': _('Оставили ретро-заметки в спринте'),
                        'value': f'{retro_authors_count}/{members_id_count}'
                    },
                ]
            }
        ]
        if all_tasks_count == 0:
            excluded_tasks_percent = 0
            blocked_tasks_percent = 0
            on_check_percent = 0
        else:
            excluded_tasks_percent = excluded_tasks.count() / all_tasks_count
            blocked_tasks_percent = blocked_tasks_count / all_tasks_count
            on_check_percent = on_check_count / all_tasks_count

        if members_id_count == 0:
            retro_authors_percent = 0
        else:
            retro_authors_percent = retro_authors_count / members_id_count

        if sprint.status == 'new':
            score = 0
            score_name = _('Спринт не запущен')
        else:
            score = round(
                int(goal_achieved) + (completed_tasks_count_percent / 100) * 0.6
                + (1 - excluded_tasks_percent) * 0.4
                + (approved_results_count_percent / 100) * 0.5
                + (1 - blocked_tasks_percent) * 0.3
                + (1 - on_check_percent) * 0.2
                + float(((100 - abs(execution_time_diff_percent)) / 100) * 0.4)
                + (int(not have_blockers)) * 0.3
                + (int(not have_looser)) * 0.3
                + (retro_authors_percent) * 0.4
                + min(retro_ideas_count / 5, 1) * 0.3,
                2
            )

            if score < 1:
                score_name = _('Спринт сорван, цели не достигнуты')
            elif 1 <= score < 2:
                score_name = _('Низкий результат, много проблем')
            elif 2 <= score < 3:
                score_name = _('Удовлетворительно, часть целей выполнена')
            elif 3 <= score < 4:
                score_name = _('Хороший результат, цели в целом достигнуты')
            else:
                score_name = _('Отличный результат, цели выполнены полностью')

        data = {
            'table': table,
            'score': {
                'name': score_name,
                'value': score,
            },
            'goal_achieved': goal_achieved
        }
        return Response(data)


class SprintExpectedResultUpdateView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.SprintExpectedResultUpdatePermission)
    serializer_class = serializers.SprintExpectedResultUpdateSerializer
    queryset = models.SprintExpectedResultModel.objects.filter(is_active=True)


class SprintMemberListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SprintMemberListSerializer
    queryset = ProfileModel

    def get(self, request, *args, **kwargs):
        sprint_id = kwargs.get('pk')
        try:
            sprint = models.TaskSprintModel.objects.get(pk=sprint_id, is_active=True)
        except ObjectDoesNotExist:
            raise exceptions.NotFound('Спринт не найден')
        if not sprint.get_detail_permission(request):
            raise exceptions.PermissionDenied()
        included_tasks = models.TaskModel.objects.filter(sprint=sprint, is_active=True)
        included_tasks_id = set(included_tasks.filter(
            sprint=sprint, is_active=True
        ).values_list('pk', flat=True))
        excluded_tasks = sprint.task_sprint_history.filter(
            for_completed=True,
        )
        excluded_tasks_id = set(excluded_tasks.values_list('task', flat=True))
        included_tasks_members_id, excluded_tasks_members_id = utils.get_sprint_members_set(sprint)
        members_id = included_tasks_members_id | excluded_tasks_members_id
        qs = ProfileModel.objects.filter(pk__in=members_id).order_by(
            'user__last_name', 'user__first_name', 'created_at')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        projects = sprint.projects.all()
        # Скрам-мастера:
        scrum_masters_id = set(WorkgroupMembersModel.objects.filter(
            models.Q(membership_role__code="MODERATOR") |
            models.Q(membership_role__code="FOUNDER"),
            work_group__in=projects,
        ).distinct().values_list('member', flat=True))
        scrum_masters_id.add(sprint.author_id)
        # Трудозатраты:
        execution_time = models.TaskExecutionTimeModel.objects.filter(
            is_active=True,
            sprint=sprint,
        ).values('user').annotate(hours_sum=Sum('hours')).values('user', 'hours_sum')
        s_data = self.serializer_class(
            page,
            many=True,
            context={
                'request': request,
                'view': self,
                'sprint': sprint,
                'scrum_masters_id': scrum_masters_id,
                'execution_time': execution_time,
                'included_tasks_id': included_tasks_id,
                'excluded_tasks_id': excluded_tasks_id,
            }
        ).data
        return paginator.get_paginated_response(s_data)


class SetSprintTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SetSprintTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        sprint_id = request.data.get('sprint')
        if instance.sprint and sprint_id:
            raise exceptions.ValidationError('Спринт уже установлен')
        project = instance.project
        if project and not project.get_update_permission(request):
            raise exceptions.ValidationError('Вы не можете добавить задачу в спринт: нет доступа.')
        return super().update(request, *args, **kwargs)


class BulkSetSprintTaskView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SetSprintTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)

    def post(self, request, *args, **kwargs):
        tasks_id = request.data.get('tasks')
        tasks = get_tasks_for_sprint_qs(
            models.TaskModel.objects.filter(is_active=True),
            request
        ).filter(pk__in=tasks_id)
        data = {'sprint': request.data.get('sprint')}
        with transaction.atomic():
            for each in tasks:
                serializer = self.serializer_class(
                    instance=each,
                    data=data,
                    context={'request': request, 'view': self}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response('ok')


class DeleteTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.DeleteTaskPermission)
    serializer_class = serializers.DeleteTaskSerializer

    def get_object(self):
        try:
            obj = models.TaskModel.objects.get(is_active=True, pk=self.request.data.get('id'))
        except ObjectDoesNotExist:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        task.is_active = False
        task.sprint = None
        task.add_sprint_date = None
        task_sprint_history = task.task_sprint_history.all()
        for each in task_sprint_history:
            each.delete()
        task.save()
        return Response('ok', status=status.HTTP_200_OK)


class UpdateStatusTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateTaskStatusPermission)
    serializer_class = serializers.UpdateStatusTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class TaskPinView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TaskPinSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pinned = serializer.validated_data.get('pinned')
        user_profile = request.user.profile

        if pinned:
            models.TaskPinnedModel.objects.get_or_create(
                is_active=True,
                user=user_profile,
                task=task,
            )
        else:
            pinned_obj = models.TaskPinnedModel.objects.filter(
                is_active=True,
                user=user_profile,
                task=task,
            ).first()
            if pinned_obj:
                pinned_obj.set_is_active(False, request)
                pinned_obj.save()

        clear_my_day_grouped_cache(user_profile.pk)

        return Response({'pinned': pinned}, status=status.HTTP_200_OK)


class UpdateCooperatorStatusTaskView(generics.UpdateAPIView):
    """Изменить статус задачи соисполнителя."""
    permission_classes = (IsAuthenticated, permissions.UpdateCooperatorTaskStatusPermission)
    serializer_class = serializers.UpdateCooperatorStatusTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)

    def update(self, request, *args, **kwargs):
        cooperator_id = request.data.get("id")
        try:
            cooperator = models.TaskCooperator.objects.get(pk=cooperator_id)
        except:
            raise exceptions.ValidationError('wrong id"')

        serializer = self.get_serializer(cooperator, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateBySecretStatusTaskView(generics.UpdateAPIView):
    permission_classes = (permissions.IsBySecretAuthenticated,)
    serializer_class = serializers.UpdateStatusTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateRejectionReasonTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UpdateRejectionReasonTasSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateKanbanStatusTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateTaskStatusPermission)
    serializer_class = serializers.UpdateKanbanStatusTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateTaskPermission)
    serializer_class = serializers.UpdateTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class TakeAuctionTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.TakeAuctionTaskPermission)
    serializer_class = serializers.TakeAuctionTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateOwnerTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateOwnerTaskPermission)
    serializer_class = serializers.UpdateOwnerTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateOperatorTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateOperatorPermission)
    serializer_class = serializers.UpdateOperatorTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateDeadlineTaskView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, permissions.UpdateTaskPermission)
    serializer_class = serializers.UpdateDeadlineTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class UpdateReasonTaskView(generics.UpdateAPIView):
    """Привязка задачи к обращению хэлпдеска."""
    permission_classes = (IsAuthenticated, permissions.UpdateTaskPermission)
    serializer_class = serializers.UpdateReasonTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)


class DetailTaskView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailTaskPermission)
    serializer_class = serializers.DetailTaskSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)
    action = 'retrieve'

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().retrieve(request, *args, **kwargs)
        data = response.data

        data['editable'] = obj.get_update_permission(request)
        return response


class ListTaskView(generics.ListAPIView):
    """Обычный список задач пользователя."""
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ListTaskSerializer
    model = models.TaskModel
    pagination_class = CustomPagination
    queryset = models.TaskModel.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = get_task_queryset(self.request, self.queryset)
        my_tasks_count = None
        if 'my_tasks_count' in request.query_params:
            count_queryset = queryset.values(
                'pk',
                'operator_id',
                'owner_id',
                'status_id',
                'dead_line',
            )
            my_tasks_count = get_my_tasks_count(request, count_queryset)
        queryset = order_tasks_queryset_from_get_param(self.request, queryset)
        order_by = queryset.query.order_by

        # qs_pk - айдишники задач, отсортированы, отфильтрованы. Нет огромного обвеса со связанными моделями
        # Если пагинировать краба, то занимает 2-3 секунды. Только ID - моментально
        qs_pk = queryset.values_list('id', flat=True)
        qs_pk = self.paginate_queryset(qs_pk)

        qs = self.model.objects.all().filter(pk__in=qs_pk)
        qs = prepare_list_task_queryset(qs, request)
        qs = qs.order_by(*order_by)

        task_type = request.query_params.get('task_type', '')
        task_types = [t.strip() for t in task_type.split(',') if t.strip()]

        if any(task_type in task_types for task_type in ['task', 'milestone', 'stage']):
            serializer = serializers.OptimizedListTaskSerializer(qs, many=True)
        else:
            serializer = serializers.ListTaskSerializer(qs, many=True)

        response = self.get_paginated_response(serializer.data)
        if my_tasks_count is not None:
            response.data['my_tasks_count'] = my_tasks_count
        return response


class TaskMembersListView(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        request = self.request
        task_id = request.query_params.get('task')
        if not task_id:
            return Response([])
        try:
            task = models.TaskModel.objects.get(is_active=True, pk=task_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response([])
        if not task.get_detail_permission(request):
            return Response([])
        members_id = task.get_member_ids
        qs = ProfileModel.objects.filter(is_active=True, pk__in=members_id).order_by(
            'user__last_name',
            'user__first_name',
        ).values_list('pk', flat=True)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = CachedAppUserPreviewSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ListTaskPointsView(generics.ListAPIView):
    """Список задач пользователя для отображения на карте. Пока не используется."""
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ListTaskSerializer
    model = models.TaskModel
    queryset = models.TaskModel.objects.filter(is_active=True)
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = get_task_queryset(self.request, self.queryset)
        return qs

    def list(self, request, *args, **kwargs):
        query_params = request.query_params
        lat_gte = query_params.get('lat__gte', 0)
        lat_lte = query_params.get('lat__lte', 0)
        lon_gte = query_params.get('lon__gte', 0)
        lon_lte = query_params.get('lon__lte', 0)
        queryset = self.get_queryset()
        queryset = queryset.filter(
            task_points__lat__gte=lat_gte,
            task_points__lat__lte=lat_lte,
            task_points__lon__gte=lon_gte,
            task_points__lon__lte=lon_lte,
        ).distinct()

        qs_pk = queryset.values_list('id', flat=True)
        qs_pk = self.paginate_queryset(qs_pk)
        qs = self.model.objects.all().filter(pk__in=qs_pk)
        qs = prepare_list_task_queryset(qs, request)
        serializer = self.get_serializer(qs, many=True)
        return self.get_paginated_response(serializer.data)


class MyTasksCountView(APIView):
    """Возвращает количество задач, где я исполнитель, я постановщик, я наблюдатель, а также количество просроченных."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        _, _, complete_statuses = get_cached_statuses()
        base_qs = models.TaskModel.objects.filter(is_active_custom=True, task_type_id='task')
        queryset = get_filter_queryset(request, models.TaskModel, base_qs)
        queryset = queryset.exclude(status__in=complete_statuses)
        data = get_my_tasks_count(request, queryset)
        return Response(data, status=status.HTTP_200_OK)


class ListCalendarTaskView(ListTaskView):
    serializer_class = serializers.ListCalendarTaskSerializer


class ListChartGanttTaskView(generics.ListAPIView):
    """Вывод задач в формате для диаграммы Ганта. Старый формат (до 2025г.)."""
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ListGanttTaskSerializer
    model = models.TaskModel

    queryset = models.TaskModel.objects.filter(is_active=True, parent__isnull=True).select_related(
        'author__user',
        'owner__user',
        'operator__user',
        'workgroup',
        'project',
    )
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = get_gantt_chart_task_queryset(self.request, self.queryset)
        return queryset


class ListChartGanttTaskView_v2(generics.ListAPIView):
    """Вывод задач в формате для диаграммы Ганта https://docs.dhtmlx.com/"""
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ListGanttTaskSerializer_v2
    model = models.TaskModel

    queryset = models.TaskModel.objects.filter(is_active=True)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = get_gantt_chart_task_queryset(self.request, self.queryset)
        return queryset


class ListKanbanTaskView(generics.ListAPIView):
    """Список задач для отображения на канбане."""
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.KanbanListTaskSerializer
    model = models.TaskModel
    pagination_class = CustomPagination
    queryset = models.TaskModel.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        qs_pk = queryset.values_list('id', flat=True)
        qs_pk = self.paginate_queryset(qs_pk)
        qs = self.model.objects.all().filter(pk__in=qs_pk)
        qs = prepare_list_kanban_task_queryset(qs, request)
        # qs = prepare_list_task_queryset(qs, request)

        # Восстанавливаем сортировку: заново аннотируем sort_field и сортируем
        user = self.request.user.profile
        user_task_sort = models.UserTaskSort.objects.filter(
            is_active=True,
            user=user,
            task=OuterRef('pk')
        )
        qs = qs.annotate(
            u_task_sort=Subquery(user_task_sort.values('sort')),
            sort_field=Case(
                When(u_task_sort__isnull=True, then=F('number_from_counter')),
                default=F('u_task_sort'),
                output_field=DecimalField(max_digits=10, decimal_places=10)
            )
        ).order_by('-sort_field')

        serializer = self.get_serializer(qs, many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        queryset = get_task_queryset(self.request, self.queryset)
        user = self.request.user.profile
        user_task_sort = models.UserTaskSort.objects.filter(
            is_active=True,
            user=user,
            task=OuterRef('pk')
        )
        queryset = queryset.annotate(
            u_task_sort=Subquery(user_task_sort.values('sort')),
            sort_field=Case(
                When(u_task_sort__isnull=True, then=F('number_from_counter')),
                default=F('u_task_sort'),
                output_field=DecimalField(max_digits=10, decimal_places=10)
            )
        ).order_by('-sort_field')
        return queryset


class WeekOperatorStatsView(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.TaskModel.objects.filter(is_active=True)

    def get_queryset(self):
        return get_task_queryset(self.request, self.queryset)

    def get(self, request, *args, **kwargs):
        td = datetime.timedelta
        week_days = td(days=7)
        now = timezone.now()
        week_ago = now - week_days
        qs = self.get_queryset().filter(operator=request.user.profile.id, created_at__gte=week_ago)
        data = qs.aggregate(
            first_day=Count('created_at', filter=Q(created_at__gte=week_ago, created_at__lte=week_ago + td(days=1), )),
            second_day=Count('created_at',
                             filter=Q(created_at__gte=week_ago + td(days=1), created_at__lte=week_ago + td(days=2), )),
            third_day=Count('created_at',
                            filter=Q(created_at__gte=week_ago + td(days=2), created_at__lte=week_ago + td(days=3), )),
            fourth_day=Count('created_at',
                             filter=Q(created_at__gte=week_ago + td(days=3), created_at__lte=week_ago + td(days=4), )),
            fifth_day=Count('created_at',
                            filter=Q(created_at__gte=week_ago + td(days=4), created_at__lte=week_ago + td(days=5), )),
            sixth_day=Count('created_at',
                            filter=Q(created_at__gte=week_ago + td(days=5), created_at__lte=week_ago + td(days=6), )),
            seventh_day=Count('created_at',
                              filter=Q(created_at__gte=week_ago + td(days=6), created_at__lte=week_ago + td(days=7), )),
        )
        return Response(data, status=status.HTTP_200_OK)


class CountKanbanStatusView(APIView):
    permission_classes = (IsAuthenticated,)
    model = models.TaskModel
    queryset = models.TaskModel.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        queryset = get_task_queryset(self.request, self.queryset)
        data = get_tasks_status_count(queryset)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        request.query_params._mutable = True
        import json
        for key, value in request.data.items():
            if isinstance(value, dict):
                request.query_params[key] = json.dumps(value)
            else:
                request.query_params[key] = value
        request.query_params._mutable = False
        queryset = self.get_queryset()
        data = get_tasks_status_count(queryset)
        return Response(data, status=status.HTTP_200_OK)


class TaskExecutionTimeStartView(APIView):
    def post(self, request, *args, **kwargs):
        task_id = kwargs.get('pk')
        try:
            task = models.TaskModel.objects.get(is_active=True, pk=task_id)
        except ObjectDoesNotExist:
            raise exceptions.ValidationError('Задача не найдена')
        user = request.user.profile
        duration, is_current = utils.start_work_log_timer(user, task)
        return Response({'duration': duration, 'is_current': is_current})


class TaskExecutionTimeStopView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user.profile
        task_id = kwargs.get('pk')
        try:
            task = models.TaskModel.objects.get(is_active=True, pk=task_id)
        except ObjectDoesNotExist:
            raise exceptions.ValidationError('Задача не найдена')

        # фронт шлёт {"duration_incomplete": <секунды>}
        provided = request.data.get('duration_incomplete')
        description = request.data.get('description')
        duration, is_current = utils.stop_work_log_timer(
            user,
            task,
            provided_duration=provided,
            description=description
        )
        return Response({'duration': duration, 'is_current': is_current})


class TaskExecutionTimeDurationView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user.profile
        task_id = kwargs.get('pk')
        try:
            task = models.TaskModel.objects.get(is_active=True, pk=task_id)
        except ObjectDoesNotExist:
            raise exceptions.ValidationError('Задача не найдена')
        if not task.get_detail_permission(request):
            raise exceptions.NotFound()
        duration, is_current, incomplete_duration = utils.get_work_log_duration(user, task)
        return Response({'duration': duration, 'duration_incomplete': incomplete_duration, 'is_current': is_current})


class TaskExecutionTimeModelViewSet(BaseModelViewSet):
    model = models.TaskExecutionTimeModel
    permission_classes = (IsAuthenticated, permissions.TaskExecutionTimeModelPermission)
    queryset = models.TaskExecutionTimeModel.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        # Обходим провепку check_custom_permission
        task_id = self.request.data.get('task')
        try:
            task = models.TaskModel.objects.get(pk=task_id)
        except ObjectDoesNotExist:
            raise exceptions.NotFound('Задача не найдена')
        user = request.user.profile
        if user not in (*list(task.visors.all()), *list(task.cooperators.all()), task.owner, task.operator):
            raise exceptions.PermissionDenied('Вы не являетесь оператором задачи')
        # created = super(BaseModelViewSet, self).create(request, *args, **kwargs)
        return super(BaseModelViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Обходим провепку check_custom_permission
        return super(BaseModelViewSet, self).update(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            task_id = self.request.query_params.get('task')
            event_calendar_id = self.request.query_params.get('event_calendar')
            meeting_section_id = self.request.query_params.get('meeting_section')

            if not any((task_id, event_calendar_id, meeting_section_id)):
                return queryset.none()

            user = self.request.user.profile

            if task_id:
                if not filter_by_permissions(models.TaskModel.objects.filter(pk=task_id), user=user).exists():
                    return queryset.none()
                queryset = queryset.filter(task_id=task_id)

            if event_calendar_id:
                queryset = queryset.filter(event_calendar_id=event_calendar_id)

            if meeting_section_id:
                queryset = queryset.filter(meeting_section_id=meeting_section_id)

            return queryset.select_related('measure_unit', 'work_type', 'event_calendar', 'meeting_section', 'task') \
                .order_by('-created_at')

        return queryset

    @action(methods=('get',), detail=False, url_path='fix_duration')
    def fix_duration(self, request, *args, **kwargs):
        """
        Исправляет поле duration для записей TaskExecutionTimeModel,
        у которых duration=0, а hours>0.
        Доступно только для superuser.
        """
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Только суперпользователь может выполнить эту операцию')

        # Находим все записи с duration=0 и hours>0
        records_to_fix = models.TaskExecutionTimeModel.objects.filter(
            duration=0,
            hours__gt=0
        )

        total_count = records_to_fix.count()
        if total_count == 0:
            return Response({
                'message': 'Нет записей для исправления',
                'fixed_count': 0
            })

        # Обновляем duration для каждой записи
        fixed_count = 0
        with transaction.atomic():
            for record in records_to_fix:
                duration_value = int(Decimal(str(record.hours)) * 3600)
                record.duration = duration_value
                fixed_count += 1

            # Используем bulk_update для эффективности
            models.TaskExecutionTimeModel.objects.bulk_update(
                records_to_fix,
                ['duration'],
                batch_size=1000
            )

        return Response({
            'message': f'Исправлено записей: {fixed_count} из {total_count}',
            'fixed_count': fixed_count,
            'total_count': total_count
        })

    @action(methods=('get',), detail=False, url_path='my_day_statistics')
    def my_day_statistics(self, request, *args, **kwargs):
        user_param = request.query_params.get('user')
        project_param = request.query_params.get('project')
        workgroup_param = request.query_params.get('workgroup')
        start = get_datetime_param(request, 'start')
        end = get_datetime_param(request, 'end')
        profile_id = request.user.profile.pk

        if user_param:
            user_ids = user_param.split(',')
        else:
            user_ids = [str(profile_id)]

        queryset = models.TaskExecutionTimeModel.objects.filter(is_active=True)

        if project_param:
            project_ids = project_param.split(',')
            queryset = queryset.filter(task__project_id__in=project_ids)

        if workgroup_param:
            workgroup_ids = workgroup_param.split(',')
            queryset = queryset.filter(task__workgroup_id__in=workgroup_ids)

        queryset = queryset.filter(user_id__in=user_ids)

        if not start or not end:
            current_date = timezone.localdate()
            start_date = current_date
            end_date = current_date
        else:
            start_date = parse_date(start.split('T')[0])
            end_date = parse_date(end.split('T')[0])
            if not start_date or not end_date:
                current_date = timezone.localdate()
                start_date = current_date
                end_date = current_date

        queryset = queryset.filter(date__gte=start_date, date__lte=end_date)

        # Calculate total statistics
        total_quantity = float(queryset.aggregate(
            total=Sum('hours')
        )['total'] or 0)

        total_duration = int(queryset.aggregate(
            total=Sum('duration')
        )['total'] or 0)

        # Group by work_type and calculate statistics
        work_type_stats = queryset.values(
            'work_type',
            'work_type__name'
        ).annotate(
            quantity_fact=Sum('hours'),
            duration=Sum('duration')
        ).order_by('work_type__sort')

        # Get work_type codes and load TaskWorkTypeModel objects
        work_type_codes = [stat['work_type'] for stat in work_type_stats if stat['work_type']]
        work_type_objects = {}
        if work_type_codes:
            task_work_types = models.TaskWorkTypeModel.objects.filter(
                code__in=work_type_codes,
                is_active=True
            ).values('code', 'name', 'icon', 'hex_color')
            work_type_objects = {wt['code']: wt for wt in task_work_types}

        # Calculate percentages and format response
        by_work_type = []
        for stat in work_type_stats:
            quantity = float(stat['quantity_fact'] or 0)
            duration = int(stat['duration'] or 0)

            quantity_percentage = (quantity / total_quantity * 100) if total_quantity > 0 else 0
            duration_percentage = (duration / total_duration * 100) if total_duration > 0 else 0

            work_type_code = stat['work_type']
            work_type_data = work_type_objects.get(work_type_code, {})

            by_work_type.append({
                'work_type_name': work_type_data.get('name', ''),
                'work_type_icon': work_type_data.get('icon', ''),
                'work_type_color': work_type_data.get('hex_color', ''),
                'quantity_fact': quantity,
                'quantity_percentage': round(quantity_percentage, 2),
                'duration': duration,
                'duration_percentage': round(duration_percentage, 2),
            })

        response_data = {
            'total_quantity_fact': total_quantity,
            'total_duration': total_duration,
            'by_work_type': by_work_type,
        }

        return Response(response_data)

    @action(methods=['get', ], detail=False, permission_classes=(), url_path='1c/list')
    def get_list_for_1c(self, request, *args, **kwargs):
        common_utils.check_request_from_urv(request)
        organization_id = request.query_params.get('organization', None)
        date_type = request.query_params.get('date_type', 'date')
        # if not organization_id:
        #     raise exceptions.ValidationError('Не указана организация.')
        if organization_id:
            if not isinstance(organization_id, str):
                raise exceptions.ValidationError('Неправильная организация')
            try:
                organization = Organization.objects.get(pk=organization_id)
            except Organization.DoesNotExist:
                raise exceptions.ValidationError(f'Организации с id {organization_id} не существует')
        date__gte = request.query_params.get('date__gte')
        date__lte = request.query_params.get('date__lte')

        if not date__lte or not date__gte:
            raise exceptions.ValidationError('Не указан диапазон дат.')
        if date_type == 'date':
            if not parse_date(date__gte):
                raise exceptions.ValidationError('Неправильный формат начальной даты.')

            if not parse_date(date__lte):
                raise exceptions.ValidationError('Неправильный формат конечной даты.')
        elif date_type == 'datetime':
            if not parse_datetime(date__gte):
                raise exceptions.ValidationError('Неправильный формат начальной даты.')
            if not parse_datetime(date__lte):
                raise exceptions.ValidationError('Неправильный формат конечной даты.')

        get_type = request.query_params.get('get_type', None)
        if get_type:
            if get_type == 'by_task_update':
                queryset = self.queryset.select_related('task').filter(task__updated_at__gte=date__gte,
                                                                       task__updated_at__lte=date__lte)
            else:
                queryset = self.queryset.select_related('task').filter(created_at__gte=date__gte,
                                                                       created_at__lte=date__lte)
        else:
            queryset = self.queryset.select_related('task').filter(created_at__gte=date__gte,
                                                                   created_at__lte=date__lte)

        if organization_id:
            queryset = queryset.filter(user__temp_organization=organization)
        queryset = queryset.filter(is_current=False)
        queryset = queryset.order_by('task__created_at', 'date')

        s_data = serializers.TaskExecutionTimeModel1CListSerializer(queryset, many=True).data
        return Response(s_data, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='table_info')
    def get_table_info(self, request, *args, **kwargs):
        task_type = request.query_params.get('task_type', 'task')
        if task_type not in ['task', 'interest', 'helpdesk']:
            raise exceptions.NotFound()
        data = dict()
        if task_type == 'task' or task_type == 'helpdesk':
            data = {
                'defaultValue': {"measure_unit": "hours"},
                "gridColumns": "130px 1fr 100px 1fr 1fr 80px 1fr 60px",
                "modalConfig": {
                    "label": "Добавить",
                    "okButton": {
                        "type": "primary",
                        "size": "default",
                        "text": "Добавить"
                    },
                    "cancelButton": {
                        "type": "default",
                        "size": "default",
                        "text": "Отмена"
                    }
                },
                "listActions": {
                    "deleteAction": True,
                    "editAction": True
                },
                "headerButtons": {
                    "size": "default",
                    "type": "dashed",
                    "text": "Добавить",
                    "icon": "plus"
                },
                "tableInfo": [
                    {
                        "field": "work_type",
                        "headerName": "Тип работы"
                    },
                    {
                        "field": "description",
                        "headerName": "Описание",
                        "class": "desc"
                    },
                    {
                        "field": "is_result",
                        "headerName": "Не брать в зачет"
                    },
                    {
                        "field": "author",
                        "headerName": "Автор"
                    },
                    {
                        "field": "hours",
                        "headerName": "Потрачено",
                        "class": "hours"
                    },
                    {
                        "field": "measure_unit",
                        "headerName": "Единица измерения",
                    },
                    {
                        "field": "date",
                        "headerName": "Дата",
                        "class": "hours"
                    },
                    {
                        "field": "actions",
                        "headerName": "",
                        "class": "action"
                    }
                ],
                "formInfo": [
                    "work_type",
                    "description",
                    "date",
                    "hours",
                    "measure_unit",
                ]
            }
        elif task_type == 'interest':
            data = {
                "gridColumns": "130px 1fr 1fr 1fr 60px",
                "modalConfig": {
                    "label": "Добавить",
                    "okButton": {
                        "type": "primary",
                        "size": "default",
                        "text": "Добавить"
                    },
                    "cancelButton": {
                        "type": "default",
                        "size": "default",
                        "text": "Отмена"
                    }
                },
                "listActions": {
                    "deleteAction": True,
                    "editAction": True
                },
                "headerButtons": {
                    "size": "default",
                    "type": "dashed",
                    "text": "Добавить",
                    "icon": "plus"
                },
                "tableInfo": [
                    {
                        "field": "work_type",
                        "headerName": "Тип работы"
                    },
                    {
                        "field": "description",
                        "headerName": "Описание",
                        "class": "desc"
                    },
                    {
                        "field": "author",
                        "headerName": "Автор"
                    },
                    {
                        "field": "date",
                        "headerName": "Дата",
                        "class": "hours"
                    },
                    {
                        "field": "actions",
                        "headerName": "",
                        "class": "action"
                    }
                ],
                "formInfo": [
                    "work_type",
                    "description",
                    "date"
                ]
            }
        return Response(data)


class TaskBudgetModelViewSet(BaseModelViewSet):
    model = models.TaskBudgetModel
    permission_classes = (IsAuthenticated, permissions.TaskBudgetModelPermission)
    queryset = models.TaskBudgetModel.objects.select_related(
        'author__user', 'task__author__user', 'measure_unit',
    ).filter(is_active=True)

    def create(self, request, *args, **kwargs):
        # Обходим проверку check_custom_permission
        task_id = self.request.data.get('task')
        try:
            task = models.TaskModel.objects.get(pk=task_id)
        except models.TaskModel.DoesNotExist:
            raise exceptions.NotFound('Задача не найдена')
        user = request.user.profile
        is_task_owner = user == task.owner
        is_task_operator = user == task.operator
        if not is_task_owner and not is_task_operator:
            raise exceptions.PermissionDenied('Вы не можете составлять затраты для этой задачи.')
        # created = super(BaseModelViewSet, self).create(request, *args, **kwargs)
        return super(BaseModelViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Обходим провепку check_custom_permission
        return super(BaseModelViewSet, self).update(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            task_id = self.request.query_params.get('task')
            if not task_id:
                return queryset.none()
            user = self.request.user.profile
            if not filter_by_permissions(models.TaskModel.objects.filter(pk=task_id), user=user).exists():
                return queryset.none()
            return queryset.filter(task_id=task_id, ).order_by('-created_at')
        else:
            return queryset

    @action(methods=('get',), detail=False, url_path='aggregate')
    def get_aggregate(self, request, *args, **kwargs):
        obj_id = request.query_params.get('obj')
        try:
            obj = BaseModel.objects.super_get(pk=obj_id)
        except ObjectDoesNotExist:
            return Response('')
        qs = get_budget_aggregate_qs(obj, request)
        qs = qs.values(
            'cost_item',
        ).annotate(amount_sum=Sum('amount'))
        data = get_budget_aggregate_data(qs)
        return Response(data)

    @action(methods=('get',), detail=False, url_path='table_info')
    def get_table_info(self, request, *args, **kwargs):
        model = models.TaskBudgetModel
        data = {
            "headerButtons": {
                "createButton": {
                    "icon": "plus",
                    "size": "default",
                    "title": "Добавить",
                    "type": "dashed"
                }
            },
            "modal": {
                "title": "Добавить затраты",
                "width": 520,
                "dialogClass": "",
                "zIndex": 2000,
                "forceRender": False,
                "modalButtons": {
                    "ok": {
                        "type": "primary",
                        "size": "default",
                        "title": "Сохранить"
                    },
                    "cancel": {
                        "type": "default",
                        "size": "default",
                        "title": "Закрыть"
                    }
                }
            },
            "formInfo": {
                "form": {
                    # тут объект с ключами и типами для формы типо:
                    "amount": 1,
                    "description": "",
                    "cost_item": None,
                    "quantity": 0,
                },
                "formField": [
                    {
                        "label": "Статья затрат",
                        "key": "cost_item",
                        "disabled": False,
                        "autoFocus": False,
                        "rules": [
                            {
                                "required": True,
                                "message": 'Обязательно для заполнения',
                                "trigger": 'blur'
                            }
                        ],
                        "widget": "Select",
                        "placeholder": "",
                        "size": "large",
                        "params": model.cost_item.field.field_info.get_dict()  # Объект параметров для селекта
                    },
                    {
                        "label": "Описание расхода",
                        "key": "description",
                        "rules": [],
                        "widget": "Textarea",
                        "allowClear": False,
                        "autoFocus": False,
                        "disabled": False,
                        "autoSize": {
                            "minRows": 2,
                            "maxRows": 6
                        },
                        "placeholder": "",
                        "size": "large"
                    },
                    {
                        "label": "Количество",
                        "key": "quantity",
                        "rules": [
                            {
                                "required": True,
                                "message": 'Обязательно для заполнения',
                                "trigger": 'blur'
                            }
                        ],
                        "widget": "Number",
                        "max": 1000,
                        "min": 1,
                        "autoFocus": False,
                        "step": 1,
                        "disabled": False,
                        "placeholder": "",
                        "size": "large"
                    },
                    {
                        "label": "Единица измерения",
                        "key": "measure_unit",
                        "disabled": False,
                        "autoFocus": False,
                        "rules": [
                            {
                                "required": True,
                                "message": 'Обязательно для заполнения',
                                "trigger": 'blur'
                            }
                        ],
                        "widget": "Select",
                        "placeholder": "",
                        "size": "large",
                        "params": model.measure_unit.field.field_info.get_dict()  # Объект параметров для селекта
                    },
                    {
                        "label": "Сумма",
                        "key": "ключ поля",
                        "rules": [
                            {
                                "required": True,
                                "message": 'Обязательно для заполнения',
                                "trigger": 'blur'
                            }
                        ],
                        "widget": "Decimal",
                        "autoFocus": False,
                        "disabled": False,
                        "placeholder": "",
                        "decimalConfig": model.amount.field.field_info.get_dict(),
                        # Вот у нас раньше на формах был виджет decimal и у него был конфиг, и я не помню какой он там
                        "size": "large"
                    }
                ]
            },
            "tableInfo": {
                "size": "default",
                "pagination": {
                    "defaultPageSize": 15,
                    "showLessItems": False,
                    "showQuickJumper": False,
                    "size": "default"
                },
                "columns": [
                    {
                        "title": "Статья затрат",
                        "key": "cost_item",
                        "string_view": "name",
                        "fixed": "left",
                        "sorter": False,
                        "width": "",
                        "scopedSlots": {
                            "customRender": 'RelatedRow'
                        }
                    },
                    {
                        "title": "Описание расхода",
                        "key": "description",
                        "fixed": False,
                        "sorter": False,
                        "width": "",
                        "scopedSlots": {
                            "customRender": 'StringRow'
                        }
                    },
                    {
                        "title": "Количество",
                        "key": "quantity",
                        "fixed": False,
                        "sorter": False,
                        "width": 120,
                        "scopedSlots": {
                            "customRender": 'IntegerRow'
                        }
                    },
                    {
                        "title": "Единица измерения",
                        "key": "measure_unit",
                        "string_view": "name__short",
                        "fixed": "left",
                        "sorter": False,
                        "width": "",
                        "scopedSlots": {
                            "customRender": 'RelatedRow'
                        }
                    },
                    {
                        "title": "Сумма",
                        "key": "amount",
                        "fixed": False,
                        "sorter": False,
                        "width": 130,
                        "scopedSlots": {
                            "customRender": 'DecimalRow'
                        }
                    }
                ]
            }
        }
        return Response(data)


class TaskInterestNeedViewSet(BaseModelViewSet):
    model = models.TaskInterestNeedModel
    permission_classes = (IsAuthenticated, permissions.TaskInterestNeedPermission)
    queryset = models.TaskInterestNeedModel.objects.select_related(
        'author__user',
        'task',
        'goods',
        'measure_unit',
    ).filter(is_active=True)

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            task_id = self.request.query_params.get('task')
            if not task_id:
                return queryset.none()
            user = self.request.user.profile
            if not filter_by_permissions(models.TaskModel.objects.filter(pk=task_id), user=user).exists():
                return queryset.none()
            return queryset.filter(task_id=task_id, task__task_type_id='interest').order_by('-created_at')
        return queryset

    @action(methods=('get',), detail=False, url_path='aggregate')
    def get_aggregate(self, request, *args, **kwargs):
        # CRM: вкладка потребностей в интересе показывает итог по строкам,
        # поэтому агрегат считаем отдельным легким endpoint-ом.
        task_id = request.query_params.get('obj')
        if not task_id:
            return Response({})

        user = request.user.profile
        task_qs = models.TaskModel.objects.filter(pk=task_id, task_type_id='interest')
        if not filter_by_permissions(task_qs, user=user).exists():
            return Response({})

        data = self.queryset.filter(task_id=task_id, task__task_type_id='interest').aggregate(
            count=Count('id'),
            amount_sum=Coalesce(Sum('amount'), Decimal('0')),
        )
        return Response(data)


class TaskDifficultyModelViewSet(BaseModelViewSet):
    model = models.TaskDifficulty
    permission_classes = (IsAuthenticated, permissions.TaskDifficultyPermission)
    queryset = models.TaskDifficulty.objects.select_related(
        'author__user', 'task__author__user'
    ).filter(is_active=True)

    def create(self, request, *args, **kwargs):
        # Обходим проверку check_custom_permission
        task_id = self.request.data.get('task')
        try:
            task = models.TaskModel.objects.get(pk=task_id)
        except models.TaskModel.DoesNotExist:
            raise exceptions.NotFound('Задача не найдена')
        user = request.user.profile
        is_task_owner = user == task.owner
        if not is_task_owner:
            raise exceptions.PermissionDenied('Вы не можете оценивать сложность этой задачи.')
        return super(BaseModelViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Обходим провепку check_custom_permission
        return super(BaseModelViewSet, self).update(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        if self.action == 'list':
            task_id = self.request.query_params.get('task')
            if not task_id:
                return queryset.none()
            user = self.request.user.profile
            if not filter_by_permissions(models.TaskModel.objects.filter(pk=task_id), user=user).exists():
                return queryset.none()
            return queryset.filter(task_id=task_id, ).order_by('-created_at')
        else:
            return queryset

    @action(methods=('get',), detail=False, url_path='aggregate')
    def get_aggregate(self, request, *args, **kwargs):
        obj_id = request.query_params.get('obj')
        try:
            obj = BaseModel.objects.super_get(pk=obj_id)
        except ObjectDoesNotExist:
            return Response('')
        qs = get_difficulty_aggregate_qs(obj, request)
        data = get_difficulty_aggregate_data(qs)
        return Response(data)

    @action(methods=('get',), detail=False, url_path='table_info')
    def get_table_info(self, request, *args, **kwargs):
        model = models.TaskDifficulty
        data = {
            "headerButtons": {
                "createButton": {
                    "icon": "plus",
                    "size": "default",
                    "title": "Добавить",
                    "type": "dashed"
                }
            },
            "modal": {
                "title": "Добавить оценку сложности",
                "width": 520,
                "dialogClass": "",
                "zIndex": 2000,
                "forceRender": False,
                "modalButtons": {
                    "ok": {
                        "type": "primary",
                        "size": "default",
                        "title": "Сохранить"
                    },
                    "cancel": {
                        "type": "default",
                        "size": "default",
                        "title": "Закрыть"
                    }
                }
            },
            "formInfo": {
                "form": {
                    # тут объект с ключами и типами для формы типо:
                    "score": 1,
                    "criterion": None,
                },
                "formField": [
                    {
                        "label": "Критерий",
                        "key": "criterion",
                        "disabled": False,
                        "autoFocus": False,
                        "rules": [
                            {
                                "required": True,
                                "message": 'Обязательно для заполнения',
                                "trigger": 'blur'
                            }
                        ],
                        "widget": "Select",
                        "placeholder": "",
                        "size": "large",
                        "params": model.criterion.field.field_info.get_dict()  # Объект параметров для селекта
                    },
                    {
                        "label": "Оценка",
                        "key": "score",
                        "rules": [
                            {
                                "required": True,
                                "message": 'Обязательно для заполнения',
                                "trigger": 'blur'
                            }
                        ],
                        "widget": "Number",
                        "max": 10,
                        "min": 1,
                        "autoFocus": False,
                        "step": 1,
                        "disabled": False,
                        "placeholder": "",
                        "size": "large"
                    },
                ]
            },
            "tableInfo": {
                "size": "default",
                "pagination": {
                    "defaultPageSize": 15,
                    "showLessItems": False,
                    "showQuickJumper": False,
                    "size": "default"
                },
                "columns": [
                    {
                        "title": "Критерий",
                        "key": "criterion",
                        "string_view": "name",
                        "fixed": "left",
                        "sorter": False,
                        "width": "",
                        "scopedSlots": {
                            "customRender": 'RelatedRow'
                        }
                    },
                    {
                        "title": "Оценка",
                        "key": "score",
                        "fixed": False,
                        "sorter": False,
                        "width": 120,
                        "scopedSlots": {
                            "customRender": 'IntegerRow'
                        }
                    },
                ]
            }
        }
        return Response(data)


class SelectListSprintView(generics.ListAPIView):
    serializer_class = serializers.TaskSprintShortSerializer
    pagination_class = CustomPagination
    queryset = models.TaskSprintModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.filter(author=self.request.user.profile,
                                        status='completed',
                                        is_active=True)
        search = self.request.query_params.get('search')
        if isinstance(search, str):
            queryset = queryset.filter(name__icontains=search)
        return queryset.order_by(
            '-created_at',
        )


from .models import TaskTypeModel, TaskStatusModel


class ImportTaskFromUrv(APIView):
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        check_request_from_urv(request)
        list_docs = request.data['data']

        for item in list_docs:

            task_id = item.get('task_id')
            task_name = item.get('task_name')
            task_is_auction = item.get('is_auction', False)
            task_scenario = item.get('scenario', None)
            profile_id = item.get('profile_id')
            operator_id = item.get('operator_id')
            project = item.get('project')
            project_id = None
            project_name = None
            project_owner = None
            if project:
                project_id = project.get('id')
                project_name = project.get('name')
                project_owner = project.get('owner')

            is_new_profile = not ProfileModel.objects.filter(id=profile_id).exists()

            if is_new_profile:
                """ Создаём пользователя """
                us = models.CustomUser()
                us.username = item.get('profile_email')
                us.email = item.get('profile_email')
                us.first_name = item.get('profile_i')
                us.last_name = item.get('profile_f')
                us.phone = item.get('profile_tel')
                us.is_loading = True
                us.save()
                profile = ProfileModel.objects.create(id=profile_id, user=us)
                profile.name = us.first_name + ' ' + us.last_name
                profile.save()

            with transaction.atomic():
                project_obj = (None, None)

                if project:
                    project_obj = WorkgroupModel.objects.get_or_create(id=project_id,
                                                                       defaults={"name": project_name,
                                                                                 "is_project": True,
                                                                                 "author_id": project_owner})
                if project and project_obj[1]:
                    WorkgroupMembersModel.objects.create(
                        member_id=project_owner,
                        work_group=project_obj[0],
                        membership_role=WorkgroupMembershipRole.objects.get(code="FOUNDER"),
                        membership_request_status=WorkgroupMembershipStatus.objects.get(code="APPROVED")
                    )

                try:
                    rewrite = item["rewrite"]
                    description = item.get('description', '')
                    project_id = item.get('project_id', None)
                    if rewrite:
                        task, created = models.TaskModel.objects.get_or_create(id=task_id, defaults={
                            "name": task_name, "operator_id": operator_id, "owner_id": profile_id,
                            "description": description,
                        })
                    else:
                        task = models.TaskModel()
                    task.description = description

                    task.id = task_id
                    task.name = task_name
                    task_type, created = TaskTypeModel.objects.get_or_create(code='interest',
                                                                             defaults={'name': "Интерес"})
                    task.task_type = task_type
                    task.owner_id = profile_id
                    task.operator_id = operator_id
                    if project_id:
                        wg = WorkgroupModel.objects.filter(id=project_id)
                        if wg.exists():
                            task.workgroup = wg.last()
                    task.is_auction = task_is_auction
                    task.is_active = True
                    if task_scenario is not None:
                        has_scenario_in_db = models.BaseModel.objects.filter(id=task_scenario).exists()
                    else:
                        has_scenario_in_db = None

                    if has_scenario_in_db is True:
                        task.task_scenario_id = task_scenario
                    elif has_scenario_in_db is False:
                        task.is_active = False

                    try:
                        task_status = TaskStatusModel.objects.get(pk=item['task_status'])
                        task.status = task_status
                    except:
                        task.is_active = False
                    task.from_urv = item.get('from_urv', False)
                    if task.from_urv:
                        task.task_type = TaskTypeModel.objects.get(code='task')

                    dealer_id = item.get('dealer_id', None)
                    if dealer_id is not None:
                        dealer = ContractorModel.objects.get(id=dealer_id)
                        task.contractor = dealer
                        if not task.operator:
                            main_manager = dealer.profiles.through.objects.filter(contractor=dealer,
                                                                                  director=True).last()
                            if main_manager:
                                task.operator = main_manager.user
                            else:
                                task.operator_id = profile_id
                    else:
                        task.contractor = None
                    if task_is_auction is True:
                        task.operator = None
                    client_id = item.get('client_id', None)
                    if client_id:
                        company_name = item.get('client_company_name', '')
                        client_business_region_name = item.get('client_business_region_name', '')
                        pot_contr, is_new_contr = PotentialContractorModel.objects.get_or_create(id=client_id,
                                                                                                 defaults={
                                                                                                     "name": item[
                                                                                                         'client_name'],
                                                                                                     "phone": item[
                                                                                                         'client_tel'],
                                                                                                     "email": item[
                                                                                                         'client_email'],
                                                                                                     'company_name': company_name,
                                                                                                     'business_region_name': client_business_region_name,

                                                                                                 })
                        if not is_new_contr:
                            pot_contr.phone = item['client_tel']
                            pot_contr.email = item['client_email']
                            pot_contr.company_name = company_name
                            pot_contr.business_region_name = client_business_region_name
                            pot_contr.save()
                        task.potential_contractor = pot_contr

                    if project and project_obj[0]:
                        task.project = project_obj[0]

                    task.save()

                except Exception as e:
                    return Response(
                        {"status": "bad_data", "exception": e.args},
                        status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"status": "ok",
                 "task_counter": task.counter.id},
                status=status.HTTP_200_OK,
            )


class GetLeadTask(APIView):
    authentication_classes = ()

    def get(self, request, *args, **kwargs):
        common_utils.check_request_from_urv(request)
        date__gte = request.query_params.get('date__gte')
        date__lte = request.query_params.get('date__lte')
        qs = models.TaskModel.objects.filter(potential_contractor__isnull=False).filter(
            updated_at__gte=date__gte, updated_at__lte=date__lte)
        serialized_data = serializers.ListLeadTaskSerializer(qs, many=True).data

        return Response(serialized_data)


class TaskStatusListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.TaskStatusTypeModel.objects.all()
    serializer_class = serializers.TaskStatusTypeModelSerializer

    def get_queryset(self):
        task_type = self.request.query_params.get('task_type', 'task')
        return self.queryset.select_related('task_status').filter(
            task_type=task_type
        ).order_by('sort')


from common.models import TableSettingsModel


class TableInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        user = request.user
        if user.is_authenticated:
            task_type = request.query_params.get('task_type', 'task')
            if 'drop' in request.query_params:
                if request.query_params.get('drop') == 'true':
                    TableSettingsModel.objects.filter(profile=user.profile,
                                                      field1='tasks',
                                                      field2=task_type).delete()
                    return Response(status=status.HTTP_200_OK)
            rec, is_new = TableSettingsModel.objects.get_or_create(profile=user.profile,
                                                                   field1='tasks',
                                                                   field2=task_type,
                                                                   defaults={'value': request.data})
            rec.value = request.data
            rec.save()
            return Response(status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):

        task_type = request.query_params.get('task_type', 'task')

        is_mobile = request.query_params.get('ver', '') == 'mobile'

        rec = TableSettingsModel.objects.filter(profile=request.user.profile,
                                                field1='tasks',
                                                field2=task_type).first()

        if task_type == 'interest':
            data = [
                {
                    "headerName": "#", 'slots': {'title': 'titleWithSettings'},
                    "cellRenderer": "DefaultRow",
                    "sortable": True,
                    "field": "counter",
                    "open": True,
                    "width": 80,
                    "hidable": False,
                    "visible": True,
                    "fixed": "left"
                },
                {
                    "headerName": "Название",
                    "cellRenderer": "NameRow",
                    "sortable": True,
                    "open": True,
                    "tree": True,
                    "field": "name",
                    "hidable": True,
                    "visible": True,
                    "width": 170,
                    "fixed": "left"
                },
                {
                    "headerName": "Карточка клиента",
                    "cellRenderer": "RelatedRow",
                    "interpretationField": "name",
                    "sortable": True,
                    "visible": False,
                    "hidable": True,
                    "open": False,
                    "field": "customer_card"
                },
                {
                    "headerName": "Организация учета",
                    "cellRenderer": "RelatedRow",
                    "interpretationField": "name",
                    "sortable": True,
                    "visible": False,
                    "hidable": True,
                    "open": False,
                    "field": "organization"
                },
                {
                    "headerName": "Клиент",
                    "cellRenderer": "DefaultRow",
                    "field": "customer_name",
                    "sortable": False,
                    "visible": True,
                    "hidable": True,
                    "open": False,
                },
                {
                    "headerName": "Бизнес регион",
                    "cellRenderer": "DefaultRow",
                    "field": "business_region_name",
                    "sortable": False,
                    "visible": True,
                    "hidable": True,
                    "open": False,
                },
                {
                    "headerName": "Лид",
                    "cellRenderer": "RelatedRow",
                    "interpretationField": "name",
                    "sortable": True,
                    "visible": False,
                    "hidable": True,
                    "open": False,
                    "field": "potential_contractor"
                },
                {
                    "headerName": "Ответственный",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "visible": True,
                    "edit": True,
                    "open": False,
                    "hidable": True,
                    "field": "operator"
                },
                {
                    "headerName": "Постановщик",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "visible": True,
                    "hidable": True,
                    "edit": True,
                    "open": False,
                    "field": "owner"
                },
                {
                    "headerName": "Крайний срок",
                    "cellRenderer": "DeadLineRow",
                    "sortable": True,
                    "visible": True,
                    "hidable": True,
                    "open": False,
                    "field": "dead_line"
                },
                {
                    "headerName": "Статус",
                    "cellRenderer": "StatusRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": True,
                    "edit": True,
                    "open": False,
                    "field": "status"
                },
                {
                    "headerName": "",
                    "cellRenderer": "ActionsRow",
                    "sortable": False,
                    "visible": True,
                    "hidable": False,
                    "field": "actions"
                }
            ]
        elif task_type == 'logistic':
            data = [
                {
                    "headerName": "#", 'slots': {'title': 'titleWithSettings'},
                    "cellRenderer": "DefaultRow",
                    "sortable": True,
                    "visible": True,
                    "field": "counter",
                    "open": True,
                    "hidable": False,
                    "width": 80,
                    "fixed": "left"
                },
                {
                    "headerName": "Название",
                    "cellRenderer": "NameRow",
                    "sortable": True,
                    "open": True,
                    "tree": True,
                    "field": "name",
                    "visible": True,
                    "hidable": True,
                    "width": 170,
                    "fixed": "left"
                },
                # {
                #     "headerName": "Старт план.",
                #     "cellRenderer": "DateTimeRow",
                #     "sortable": True,
                #     "hidable": True,
                #     "visible": True,
                #     "open": False,
                #     "field": "date_start_plan"
                # },
                {
                    "headerName": "Старт факт.",
                    "cellRenderer": "DateTimeRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "field": "date_start_fact"
                },
                {
                    "headerName": "Водитель",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "edit": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "field": "operator"
                },
                {
                    "headerName": "Логист",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "edit": True,
                    "open": False,
                    "visible": True,
                    "hidable": True,
                    "field": "owner"
                },
                {
                    "headerName": "Крайний срок",
                    "cellRenderer": "DeadLineRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "field": "dead_line"
                },
                {
                    "headerName": "Статус",
                    "cellRenderer": "StatusRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": True,
                    "edit": True,
                    "open": False,
                    "field": "status"
                },
                {
                    "headerName": "",
                    "cellRenderer": "ActionsRow",
                    "sortable": False,
                    "visible": True,
                    "hidable": False,
                    "field": "actions"
                }
            ]


        elif task_type == 'helpdesk':
            data = [
                {
                    "headerName": "#", 'slots': {'title': 'titleWithSettings'},
                    "cellRenderer": "DefaultRow",
                    "sortable": True,
                    "field": "counter",
                    "open": True,
                    "hidable": False,
                    "visible": True,
                    "width": 80,
                    "fixed": "left"
                },
                {
                    "headerName": "Вопрос",
                    "cellRenderer": "NameRow",
                    "sortable": True,
                    "open": True,
                    "tree": True,
                    "hidable": True,
                    "visible": True,
                    "field": "name",
                    "width": 170,
                    "fixed": "left"
                },
                {
                    "headerName": "Старт план.",
                    "cellRenderer": "DateTimeRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": False,
                    "open": False,
                    "field": "date_start_plan"
                },
                {
                    "headerName": "Старт факт.",
                    "cellRenderer": "DateTimeRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": False,
                    "open": False,
                    "field": "date_start_fact"
                },

                {
                    "headerName": "Автор",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "visible": True,
                    "edit": True,
                    "hidable": True,
                    "open": False,
                    "field": "owner"
                },
                {
                    "headerName": "Специалист",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "visible": True,
                    "edit": True,
                    "hidable": True,
                    "open": False,
                    "field": "operator"
                },
                {
                    "headerName": "Линия ТП",
                    "cellRenderer": "WorkgroupRow",
                    "sortable": True,
                    "edit": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "width": 200,
                    "field": "workgroup"
                },

                {
                    "headerName": "Крайний срок",
                    "cellRenderer": "DeadLineRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": False,
                    "open": False,
                    "field": "dead_line"
                },
                {
                    "headerName": "Статус",
                    "cellRenderer": "StatusRow",
                    "sortable": True,
                    "edit": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "field": "status"
                },
                {
                    "headerName": "",
                    "cellRenderer": "ActionsRow",
                    "visible": True,
                    "sortable": False,
                    "hidable": False,
                    "field": "actions"
                }
            ]

        else:
            data = [
                {
                    "headerName": "#",
                    "cellRenderer": "DefaultRow",
                    "sortable": True,
                    "field": "counter",
                    "visible": True,
                    "hidable": False,
                    "open": True,
                    "width": 80,
                    "fixed": "left"
                },
                {
                    "headerName": "Название",
                    "cellRenderer": "NameRow",
                    "sortable": True,
                    "open": True,
                    "visible": True,
                    "hidable": True,
                    "tree": True,
                    "field": "name",
                    "width": 240,
                    "fixed": "left"
                },
                {
                    "headerName": "Ответственный",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "edit": True,
                    "visible": True,
                    "open": False,
                    "hidable": True,
                    "width": 200,
                    "field": "operator"
                },
                {
                    "headerName": "Постановщик",
                    "cellRenderer": "UserRow",
                    "sortable": True,
                    "edit": True,
                    "visible": True,
                    "open": False,
                    "hidable": True,
                    "width": 200,
                    "field": "owner"
                },
                {
                    "headerName": "Дата начала",
                    "cellRenderer": "DateTimeRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "field": "date_start_plan"
                },
                {
                    "headerName": "Крайний срок",
                    "cellRenderer": "DeadLineRow",
                    "sortable": True,
                    "hidable": True,
                    "visible": True,
                    "open": False,
                    "field": "dead_line"
                },
                {
                    "headerName": "Статус",
                    "cellRenderer": "StatusRow",
                    "sortable": True,
                    "hidable": True,
                    "edit": True,
                    "visible": True,
                    "open": False,
                    "field": "status"
                },
                {
                    "headerName": "",
                    "cellRenderer": "ActionsRow",
                    "sortable": False,
                    "visible": True,
                    "hidable": False,
                    "width": 100,
                    "field": "actions",
                    'slots': {'title': 'titleWithSettings'},
                }
            ]

        part = request.query_params.get('part', '')
        if part == 'difficulty':
            model = models.TaskDifficulty
            data = {
                "accessRules": {
                    "owner": True,
                    "operator": False,
                    "visors": False,
                },
                "headerButtons": {
                    "createButton": {
                        "icon": "plus",
                        "size": "default",
                        "title": "Добавить",
                        "type": "dashed"
                    }
                },
                "modal": {
                    "title": "Добавить оценку сложности",
                    "width": 520,
                    "dialogClass": "",
                    "zIndex": 2000,
                    "forceRender": False,
                    "modalButtons": {
                        "ok": {
                            "type": "primary",
                            "size": "default",
                            "title": "Сохранить"
                        },
                        "cancel": {
                            "type": "default",
                            "size": "default",
                            "title": "Закрыть"
                        }
                    }
                },
                "formInfo": {
                    "form": {
                        # тут объект с ключами и типами для формы типо:
                        "score": 1,
                        "criterion": None,
                    },
                    "formField": [
                        {
                            "label": "Критерий",
                            "key": "criterion",
                            "disabled": False,
                            "autoFocus": False,
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Select",
                            "placeholder": "",
                            "size": "large",
                            "params": model.criterion.field.field_info.get_dict()  # Объект параметров для селекта
                        },
                        {
                            "label": "Оценка",
                            "key": "score",
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Number",
                            "max": 10,
                            "min": 1,
                            "autoFocus": False,
                            "step": 1,
                            "disabled": False,
                            "placeholder": "",
                            "size": "large"
                        },
                    ]
                },
                "tableInfo": {
                    "size": "default",
                    "pagination": {
                        "defaultPageSize": 15,
                        "showLessItems": False,
                        "showQuickJumper": False,
                        "size": "default"
                    },
                    "columns": [
                        {
                            "title": "Критерий",
                            "key": "criterion",
                            "string_view": "name",
                            "fixed": "left",
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'RelatedRow'
                            }
                        },
                        {
                            "key": "author",
                            "sorter": False,
                            "title": "Автор",
                            "width": "",
                            "scopedSlots": {
                                "customRender": "UserRow"
                            }
                        },
                        {
                            "title": "Оценка",
                            "key": "score",
                            "fixed": False,
                            "sorter": False,
                            "width": 120,
                            "scopedSlots": {
                                "customRender": 'IntegerRow'
                            }
                        },
                        {
                            "title": "",
                            "key": "actions",
                            "fixed": False,
                            "sorter": False,
                            "width": 60,
                            "scopedSlots": {
                                "customRender": 'ActionsRow'
                            },
                            "actionsButton": {
                                "type": "link",
                                "icon": "fi-rr-menu-burger",
                                "size": "default",
                                "edit": {
                                    "title": "Редактировать",
                                    "icon": "fi-rr-edit"
                                },
                                "delete": {
                                    "title": "Удалить",
                                    "icon": "fi-rr-trash"
                                }
                            }
                        },
                    ]
                }
            }
            return Response(data)
        elif part == 'interest_needs':
            model = models.TaskInterestNeedModel
            data = {
                "accessRules": {
                    "owner": True,
                    "operator": True,
                    "visors": False,
                },
                "headerButtons": {
                    "createButton": {
                        "icon": "plus",
                        "size": "default",
                        "title": "Добавить",
                        "type": "dashed"
                    }
                },
                "modal": {
                    "title": "Добавить потребность",
                    "width": 560,
                    "dialogClass": "",
                    "zIndex": 2000,
                    "forceRender": False,
                    "modalButtons": {
                        "ok": {
                            "type": "primary",
                            "size": "default",
                            "title": "Сохранить"
                        },
                        "cancel": {
                            "type": "default",
                            "size": "default",
                            "title": "Закрыть"
                        }
                    }
                },
                "formInfo": {
                    "form": {
                        "name": "",
                        "goods": None,
                        "quantity": 1,
                        "price": 0,
                        "comment": "",
                    },
                    "formField": [
                        {
                            "label": "Потребность",
                            "key": "name",
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Textarea",
                            "allowClear": True,
                            "autoFocus": True,
                            "disabled": False,
                            "autoSize": {
                                "minRows": 1,
                                "maxRows": 2
                            },
                            "placeholder": "",
                            "size": "large"
                        },
                        {
                            "label": "Товар или услуга",
                            "key": "goods",
                            "disabled": False,
                            "autoFocus": False,
                            "rules": [],
                            "widget": "Select",
                            "allowClear": True,
                            "placeholder": "",
                            "size": "large",
                            "params": {
                                "dataPath": "/app_info/select_list/?model=catalogs.NomenclatureModel"
                            }
                        },
                        {
                            "label": "Количество",
                            "key": "quantity",
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Decimal",
                            "autoFocus": False,
                            "disabled": False,
                            "placeholder": "",
                            "decimalConfig": model.quantity.field.field_info.get_dict(),
                            "size": "large"
                        },
                        {
                            "label": "Цена/оценка",
                            "key": "price",
                            "rules": [],
                            "widget": "Decimal",
                            "autoFocus": False,
                            "disabled": False,
                            "placeholder": "",
                            "decimalConfig": model.price.field.field_info.get_dict(),
                            "size": "large"
                        },
                        {
                            "label": "Комментарий",
                            "key": "comment",
                            "rules": [],
                            "widget": "Textarea",
                            "allowClear": True,
                            "autoFocus": False,
                            "disabled": False,
                            "autoSize": {
                                "minRows": 2,
                                "maxRows": 6
                            },
                            "placeholder": "",
                            "size": "large"
                        },
                    ]
                },
                "tableInfo": {
                    "size": "default",
                    "pagination": {
                        "defaultPageSize": 15,
                        "showLessItems": False,
                        "showQuickJumper": False,
                        "size": "default"
                    },
                    "columns": [
                        {
                            "title": "Потребность",
                            "key": "name",
                            "fixed": "left",
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'StringRow'
                            }
                        },
                        {
                            "title": "Товар или услуга",
                            "key": "goods",
                            "string_view": "name",
                            "fixed": False,
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'RelatedRow'
                            }
                        },
                        {
                            "title": "Артикул",
                            "key": "article_number",
                            "fixed": False,
                            "sorter": False,
                            "width": 130,
                            "scopedSlots": {
                                "customRender": 'StringRow'
                            }
                        },
                        {
                            "title": "Количество",
                            "key": "quantity",
                            "fixed": False,
                            "sorter": False,
                            "width": 120,
                            "scopedSlots": {
                                "customRender": 'DecimalRow'
                            }
                        },
                        {
                            "title": "Ед. изм.",
                            "key": "measure_unit",
                            "string_view": "name_short",
                            "fixed": False,
                            "sorter": False,
                            "width": 100,
                            "scopedSlots": {
                                "customRender": 'RelatedRow'
                            }
                        },
                        {
                            "title": "Цена/оценка",
                            "key": "price",
                            "fixed": False,
                            "sorter": False,
                            "width": 130,
                            "scopedSlots": {
                                "customRender": 'DecimalRow'
                            }
                        },
                        {
                            "title": "Сумма",
                            "key": "amount",
                            "fixed": False,
                            "sorter": False,
                            "width": 130,
                            "scopedSlots": {
                                "customRender": 'DecimalRow'
                            }
                        },
                        {
                            "title": "Комментарий",
                            "key": "comment",
                            "fixed": False,
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'StringRow'
                            }
                        },
                        {
                            "title": "",
                            "key": "actions",
                            "fixed": False,
                            "sorter": False,
                            "width": 60,
                            "scopedSlots": {
                                "customRender": 'ActionsRow'
                            },
                            "actionsButton": {
                                "type": "link",
                                "icon": "fi-rr-menu-burger",
                                "size": "default",
                                "edit": {
                                    "title": "Редактировать",
                                    "icon": "fi-rr-edit"
                                },
                                "delete": {
                                    "title": "Удалить",
                                    "icon": "fi-rr-trash"
                                }
                            }
                        },
                    ]
                }
            }
        elif part == 'budget':
            model = models.TaskBudgetModel
            data = {
                "accessRules": {
                    "owner": True,
                    "operator": True,
                    "visors": False,
                },
                "headerButtons": {
                    "createButton": {
                        "icon": "plus",
                        "size": "default",
                        "title": "Добавить",
                        "type": "dashed"
                    },
                    "headerWidgets": ['ListAmount'],
                },
                "modal": {
                    "title": "Добавить затраты",
                    "width": 520,
                    "dialogClass": "",
                    "zIndex": 2000,
                    "forceRender": False,
                    "modalButtons": {
                        "ok": {
                            "type": "primary",
                            "size": "default",
                            "title": "Сохранить"
                        },
                        "cancel": {
                            "type": "default",
                            "size": "default",
                            "title": "Закрыть"
                        }
                    }
                },
                "formInfo": {
                    "form": {
                        # тут объект с ключами и типами для формы типо:
                        "amount": 1,
                        "description": "",
                        "cost_item": None,
                        "quantity": 1,
                    },
                    "formField": [
                        {
                            "label": "Статья затрат",
                            "key": "cost_item",
                            "disabled": False,
                            "autoFocus": False,
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Select",
                            "placeholder": "",
                            "size": "large",
                            "params": model.cost_item.field.field_info.get_dict()  # Объект параметров для селекта
                        },
                        {
                            "label": "Описание расхода",
                            "key": "description",
                            "rules": [],
                            "widget": "Textarea",
                            "allowClear": False,
                            "autoFocus": False,
                            "disabled": False,
                            "autoSize": {
                                "minRows": 2,
                                "maxRows": 6
                            },
                            "placeholder": "",
                            "size": "large"
                        },
                        {
                            "label": "Количество",
                            "key": "quantity",
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Number",
                            "max": 1000,
                            "min": 1,
                            "autoFocus": False,
                            "step": 1,
                            "disabled": False,
                            "placeholder": "",
                            "size": "large"
                        },
                        {
                            "label": "Единица измерения",
                            "key": "measure_unit",
                            "disabled": False,
                            "autoFocus": False,
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Select",
                            "placeholder": "",
                            "size": "large",
                            "params": model.measure_unit.field.field_info.get_dict()  # Объект параметров для селекта
                        },
                        {
                            "label": "Сумма",
                            "key": "amount",
                            "rules": [
                                {
                                    "required": True,
                                    "message": 'Обязательно для заполнения',
                                    "trigger": 'blur'
                                }
                            ],
                            "widget": "Decimal",
                            "autoFocus": False,
                            "disabled": False,
                            "placeholder": "",
                            "decimalConfig": model.amount.field.field_info.get_dict(),
                            # Вот у нас раньше на формах был виджет decimal и у него был конфиг, и я не помню какой он там
                            "size": "large"
                        }
                    ]
                },
                "tableInfo": {
                    "size": "default",
                    "pagination": {
                        "defaultPageSize": 15,
                        "showLessItems": False,
                        "showQuickJumper": False,
                        "size": "default"
                    },
                    "columns": [
                        {
                            "title": "Статья затрат",
                            "key": "cost_item",
                            "string_view": "name",
                            "fixed": "left",
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'RelatedRow'
                            }
                        },
                        {
                            "key": "author",
                            "sorter": False,
                            "title": "Автор",
                            "width": "",
                            "scopedSlots": {
                                "customRender": "UserRow"
                            }
                        },
                        {
                            "title": "Описание расхода" if not is_mobile else "Описание",
                            "key": "description",
                            "fixed": False,
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'StringRow'
                            }
                        },
                        {
                            "title": "Количество",
                            "key": "quantity",
                            "fixed": False,
                            "sorter": False,
                            "width": 120,
                            "scopedSlots": {
                                "customRender": 'IntegerRow'
                            }
                        },
                        {
                            "title": "Единица измерения",
                            "key": "measure_unit",
                            "string_view": "name_short",
                            "fixed": "left",
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'RelatedRow'
                            }
                        },
                        {
                            "title": "Сумма",
                            "key": "amount",
                            "fixed": False,
                            "sorter": False,
                            "width": 130,
                            "scopedSlots": {
                                "customRender": 'DecimalRow'
                            }
                        },
                        {
                            "title": "",
                            "key": "actions",
                            "fixed": False,
                            "sorter": False,
                            "width": 60,
                            "scopedSlots": {
                                "customRender": 'ActionsRow'
                            },
                            "actionsButton": {
                                "type": "link",
                                "icon": "fi-rr-menu-burger",
                                "size": "default",
                                "edit": {
                                    "title": "Редактировать",
                                    "icon": "fi-rr-edit"
                                },
                                "delete": {
                                    "title": "Удалить",
                                    "icon": "fi-rr-trash"
                                }
                            }
                        },
                    ]
                }
            }
        elif part == 'time_tracking':
            task_type = request.query_params.get('task_type', 'task')
            if task_type not in ['task', 'interest']:
                raise exceptions.NotFound()
            data = dict()
            if task_type == 'task':
                data = {
                    "accessRules": {
                        "owner": False,
                        "operator": True,
                        "visors": False,
                    },
                    "gridColumns": "130px 1fr 1fr 1fr 1fr 60px",
                    "modalConfig": {
                        "label": "Добавить",
                        "okButton": {
                            "type": "primary",
                            "size": "default",
                            "text": "Добавить"
                        },
                        "cancelButton": {
                            "type": "default",
                            "size": "default",
                            "text": "Отмена"
                        }
                    },
                    "listActions": {
                        "deleteAction": True,
                        "editAction": True
                    },
                    "headerButtons": {
                        "size": "default",
                        "type": "dashed",
                        "text": "Добавить",
                        "icon": "plus"
                    },
                    "tableInfo": [
                        {
                            "field": "work_type",
                            "headerName": "Тип работы"
                        },
                        {
                            "field": "description",
                            "headerName": "Описание",
                            "class": "desc"
                        },
                        {
                            "field": "author",
                            "headerName": "Автор"
                        },
                        {
                            "field": "hours",
                            "headerName": "Потрачено",
                            "class": "hours"
                        },
                        {
                            "title": "Единица измерения",
                            "key": "measure_unit",
                            "string_view": "name_short",
                            "fixed": "left",
                            "sorter": False,
                            "width": "",
                            "scopedSlots": {
                                "customRender": 'RelatedRow'
                            }
                        },
                        {
                            "field": "date",
                            "headerName": "Дата",
                            "class": "hours"
                        },
                        {
                            "field": "actions",
                            "headerName": "",
                            "class": "action"
                        }
                    ],
                    "formInfo": [
                        "work_type",
                        "description",
                        "date",
                        "hours"
                    ]
                }
            elif task_type == 'interest':
                data = {
                    "accessRules": {
                        "owner": False,
                        "operator": False,
                        "visors": False,
                    },
                    "gridColumns": "130px 1fr 1fr 1fr 60px",
                    "modalConfig": {
                        "label": "Добавить",
                        "okButton": {
                            "type": "primary",
                            "size": "default",
                            "text": "Добавить"
                        },
                        "cancelButton": {
                            "type": "default",
                            "size": "default",
                            "text": "Отмена"
                        }
                    },
                    "listActions": {
                        "deleteAction": True,
                        "editAction": True
                    },
                    "headerButtons": {
                        "size": "default",
                        "type": "dashed",
                        "text": "Добавить",
                        "icon": "plus"
                    },
                    "tableInfo": [
                        {
                            "field": "work_type",
                            "headerName": "Тип работы"
                        },
                        {
                            "field": "description",
                            "headerName": "Описание",
                            "class": "desc"
                        },
                        {
                            "field": "author",
                            "headerName": "Автор"
                        },
                        {
                            "field": "date",
                            "headerName": "Дата",
                            "class": "hours"
                        },
                    ],
                    "formInfo": [
                        "work_type",
                        "description",
                        "date"
                    ]
                }
            return Response(data)

        data1 = {
            "page_size": 50,
            "columns": data
        }
        if rec:
            return Response(rec.value)

        return Response(data1)


class ActionsInfoView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailTaskPermission)
    queryset = models.TaskModel.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        task_type = task.task_type_id
        user = request.user.profile
        operator = task.operator
        owner = task.owner
        is_operator = user == operator
        is_owner = user == owner
        is_visor = task.visors.filter(pk=user.pk).exists()
        is_cooperator = task.cooperators.filter(pk=user.pk).exists()
        task_status = task.status
        status_code = task.status_id
        actions = dict()
        task_roles = set(task.get_task_roles(user.pk))
        if task_type == 'interest':
            if is_owner:
                actions['change_status'] = {"availability": True}
                actions['add_task'] = {"availability": True}
                actions['edit'] = {"availability": True}
            actions['share'] = {"availability": True}
        elif task_type == 'logistic':
            actions['share'] = {"availability": True}
            if status_code not in ('completed', 'in_transit'):
                if is_owner:
                    actions['edit'] = {"availability": True}
            if not status_code == 'completed' and is_operator and user.current_work_status_code == 'in_work':
                actions['change_status'] = {"availability": True}
        elif task_type in ['task', 'stage', 'milestone']:
            if task.get_update_permission(request):
                actions['edit'] = {"availability": True}
            if task.get_update_tag_permission(request):
                actions['update_tags'] = {"availability": True}
            # if is_cooperator:
            #     actions['change_cooperator_status'] = {"availability": True}
            available_coop_statuses = task.get_available_coop_statuses(user.pk)
            if available_coop_statuses:
                available_coop_statuses_data = models.TaskStatusModel.objects.filter(
                    code__in=available_coop_statuses
                ).values(
                    'code',
                    'name',
                    'color',
                )
                if 'cooperator' in task_roles and len(task_roles) == 1:
                    only_coop = True
                else:
                    only_coop = False
                actions['change_cooperator_status'] = {
                    'availability': True,
                    'available_statuses': available_coop_statuses_data,
                    'only_coop': only_coop,
                }
            actions['copy'] = {"availability": True}
            actions['share'] = {"availability": True}
            if is_operator or is_owner or is_visor or is_cooperator:
                actions['add_subtask'] = {"availability": True}
                actions['can_use_timer'] = {"availability": True}
            if is_owner:
                actions['delete'] = {"availability": True}
            if has_work_plan_access(request):
                actions['add_to_work_plan'] = {"availability": True}
        if is_owner or is_operator or is_visor or is_cooperator:
            actions['create_accounting'] = {"availability": True}
        im_project_moderator = task.project and task.project.get_update_permission(request)
        if im_project_moderator:
            actions['create_accounting'] = {'availability': True, 'edit_user': True}
            actions['edit_accounting'] = {'availability': True, 'edit_user': True}
            actions['delete_accounting'] = {'availability': True}
        if task_type == 'task':
            available_statuses = task.get_available_statuses(user.pk)
            task_status_type = task_status.task_status_type.filter(task_type=task_type).first()
            next_status = None
            if not status_code == 'completed':
                if (is_owner or im_project_moderator) and not (is_operator or is_cooperator):
                    next_status = 'completed'
                else:
                    if task_status_type:
                        next_task_status_type = task_status_type.next_status
                        if next_task_status_type:
                            next_status = next_task_status_type.task_status_id
                            if next_status not in available_statuses:
                                next_status = None
            if available_statuses:
                available_statuses_data = models.TaskStatusModel.objects.filter(
                    code__in=available_statuses
                ).values(
                    'code',
                    'name',
                    'color',
                )
                actions['change_status'] = {
                    'availability': True,
                    'available_statuses': available_statuses_data,
                    'next_status': next_status,
                }
            if not task_roles.isdisjoint({'owner', 'operator'}):
                actions['update_operator'] = {
                    'availability': True,
                }
            if is_owner:
                actions['update_owner'] = {
                    'availability': True,
                }
        if task_type == 'task' and task.project:
            if im_project_moderator and task.sprint:
                actions['unset_sprint'] = {'availability': True}
            if im_project_moderator and not task.sprint:
                actions['set_sprint'] = {'availability': True}
            # if im_project_moderator:
            #     statuses = set(models.TaskStatusTypeModel.objects.filter(
            #         is_active=True,
            #         task_type_id='task',
            #         is_open=False,
            #     ).values_list('task_status', flat=True))
            #     statuses.discard(status_code)
            #     if not (is_operator or is_cooperator):
            #         statuses.discard('in_work')
            #         statuses.discard('on_check')
            #     if status_code not in ('completed', 'on_check', 'on_pause',):
            #         statuses.discard('on_rework')
            #     next_status = None
            #     task_status_type = task_status.task_status_type.filter(task_type=task_type).first()
            #     if not status_code == 'completed':
            #         if (is_owner or im_project_moderator) and not (is_operator or is_cooperator):
            #             next_status = 'completed'
            #         else:
            #             if task_status_type:
            #                 next_task_status_type = task_status_type.next_status
            #                 if next_task_status_type:
            #                     next_status = next_task_status_type.task_status_id
            #                     if next_status not in statuses:
            #                         next_status = None
            #     else:
            #         next_status = None
            #     actions['change_status'] = {
            #         'availability': True,
            #         'available_statuses': list(statuses),
            #         'next_status': next_status,
            #     }
        if task.is_auto_created:
            excluded_actions = [
                'edit', 'update_tags', 'change_cooperator_status',
                'add_subtask', 'delete', 'add_to_work_plan',
                'update_operator', 'update_owner'
            ]
            for action_key in excluded_actions:
                actions.pop(action_key, None)
        data = {"actions": actions}
        return Response(data)


class TaskSearchView(HaystackGenericAPIView):
    index_models = (models.TaskModel,)
    serializer_class = serializers.TaskModelSearchSerializer
    pagination_class = CustomPagination
    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request, *args, **kwargs):
        text = request.query_params.get('text')
        search_bool = get_search_bool()
        if not text:
            search_queryset = SearchQuerySet().none()
        else:
            search_queryset = RelatedSearchQuerySet().filter(
                text=text, is_active=search_bool
            ).models(models.TaskModel).load_all()
        ordering = request.query_params.get('ordering').split(',')
        if ordering:
            search_queryset = search_queryset.order_by(*ordering)
        page = self.paginate_queryset(search_queryset)
        s_data = self.serializer_class(page, many=True, context={'request': request}).data
        return self.get_paginated_response(s_data)


class TaskAnalyticsView(ListTaskView):
    serializer_class = serializers.TaskAnalyticsSerializer


class TaskAnalyticsFileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        page_name = request.GET.get('page_name')
        queryset = models.TaskModel.objects.filter(is_active=True).select_related(
            'parent__author__user',
            'parent__author__avatar',
            'author__user',
            'author__avatar',
            'owner__user',
            'owner__avatar',
            'operator__user',
            'operator__avatar',
            'workgroup',
            'project',
            'contractor',
            'potential_contractor',
            'status',
        ).prefetch_related(
            'prerequisites__author__avatar',
            'visors',
            'attachments',
            'children'
        )
        queryset = order_tasks_queryset_from_get_param(
            self.request, get_task_queryset(self.request, queryset),
        ).annotate(
            execution_time_sum=Sum('execution_time__hours', filter=Q(execution_time__is_active=True)),
            budget_sum=Sum('task_budgets__amount', filter=Q(task_budgets__is_active=True)),
            difficulty_avg=Avg('difficulty__score', filter=Q(difficulty__is_active=True))
        )
        wb = create_workbook_task_analytics(queryset)
        with NamedTemporaryFile() as tmp:
            wb.save('test.xls')  # wb.save(tmp.name)
            return FileResponse(open('test.xls', 'rb'), filename='analytics.xlsx')
            # return FileResponse(open(tmp.name, 'rb'), filename='analytics.xlsx')


class TaskListFileView(APIView):
    permission_classes = (IsAuthenticated,)
    model = models.TaskModel
    queryset = models.TaskModel.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        queryset = get_task_queryset(self.request, self.queryset)
        queryset = order_tasks_queryset_from_get_param(self.request, queryset)

        queryset = queryset.select_related(
            #  'counter',
            'sprint',
            'project',
            'workgroup',
            'parent__author__user',
            'author__user',
            'owner__user',
            'operator__user',
            'contractor',
            'potential_contractor',
            'status',
            'task_type'
        ).prefetch_related(
            Prefetch(
                'execution_time',
                queryset=models.TaskExecutionTimeModel.objects.filter(is_active=True).select_related(
                    'work_type', 'measure_unit', 'author__user', 'user__user'
                ),
                to_attr='task_steps'
            ),
            Prefetch('visors', queryset=ProfileModel.objects.filter(is_active=True))
        )
        wb = create_workbook_task_list(queryset)
        with NamedTemporaryFile() as tmp:
            wb.save(tmp.name)
            return FileResponse(open(tmp.name, 'rb'), filename='analytics.xlsx')


class InterestListFileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        task_type = request.GET.get('task_type', 'interest')
        queryset = models.TaskModel.objects.filter(
            is_active=True,
            task_type=task_type
        )
        queryset = order_tasks_queryset_from_get_param(
            self.request, get_task_queryset(self.request, queryset))

        queryset = queryset.select_related(
            'counter',
            'potential_contractor',
            'operator__user',
            'lead_source',
            'status',
        ).prefetch_related(
            Prefetch('execution_time',
                     queryset=models.TaskExecutionTimeModel.objects.filter(is_active=True),
                     to_attr='task_steps'),
            Prefetch('execution_time__work_type',
                     queryset=models.TaskWorkTypeModel.objects.filter(is_active=True)),
            Prefetch('rejection_reason',
                     queryset=models.RejectionReasonModel.objects.filter(is_active=True)),
        )
        wb = create_workbook_interest_list(queryset)
        with NamedTemporaryFile() as tmp:
            wb.save(tmp.name)
            return FileResponse(open(tmp.name, 'rb'), filename='analytics.xlsx')


class UpdateDeliveryView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.DeliveryTableSerializer
    queryset = models.TaskDeliveryModel.objects.filter(is_active=True)
    action = 'retirieve'  # Это чтобы BaseSerializer не ругался


class TaskGoodsView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailTaskPermission)
    queryset = models.TaskModel.objects.filter(task_type_id='logistic', is_active=True)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        delivery_points = task.task_delivery_points.filter(is_active=True, is_start=False).values_list('pk', flat=True)

        orders = GoodsOrderModel.objects.filter(
            is_active=True,
            task_delivery_point_id__in=delivery_points
        ).values_list('pk', flat=True)
        goods = TPGoodsOrderModel.objects.filter(
            is_active=True,
            owner_id__in=orders
        ).order_by(
            'goods__name',
        ).values(
            'goods',
        ).annotate(
            id=F('goods_id'),
            name=F('goods__name'),
            code=F('goods__code'),
            count=Count('goods'),
            quantity=Sum('quantity'),
            quantity_success=Sum('quantity_success'),
            amount=Sum('amount'),
            measure_unit_name_short=F('goods__base_measure_unit__name_short')
        )
        for each in goods:
            warehouses_data = models.TaskLoadingGoodsModel.objects.filter(
                is_active=True,
                goods_id=each['id'],
                task=task,
            ).values('warehouse').annotate(
                id=F('warehouse_id'),
                name=F('warehouse__name'),
                quantity_loaded=Sum('quantity'),
                measure_unit_name_short=F('goods__base_measure_unit__name_short')
            )
            each['warehouses'] = warehouses_data
        return Response(goods)


class TaskPaymentToWarehousesView(generics.RetrieveAPIView):
    """Информация об оплате складам за закупку товара со склада."""
    permission_classes = (IsAuthenticated, permissions.DetailTaskPermission)
    queryset = models.TaskModel.objects.filter(task_type_id='logistic', is_active=True)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        delivery_points = task.task_delivery_points.filter(is_active=True, is_start=False).values_list('pk', flat=True)
        orders = GoodsOrderModel.objects.filter(
            is_active=True,
            task_delivery_point_id__in=delivery_points
        ).order_by('warehouse__name')
        warehouses = orders.values('warehouse').annotate(
            id=F('warehouse_id'),
            name=F('warehouse__name'),
            need_amount_pay=Sum(
                'start_task_delivery_point__need_amount_pay',
                filter=Q(
                    start_task_delivery_point__is_active=True,
                    start_task_delivery_point__task__is_active=True,
                ),
            )
        )
        for warehouse in warehouses:
            amount_paid = task.task_loading_goods.filter(
                is_active=True, warehouse_id=warehouse['id']).aggregate(Sum('amount_paid'))['amount_paid__sum']
            if amount_paid is None:
                amount_paid = 0
            warehouse['amount_paid'] = amount_paid
        return Response(warehouses)


class GoodsByWarehousesView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailTaskPermission)
    queryset = models.TaskModel.objects.filter(task_type_id='logistic', is_active=True)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        warehouse = request.query_params.get('warehouse', None)
        warehouses = get_goods_by_warehouses(task, (warehouse,))
        return Response(warehouses)


class TaskLoadingCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user.profile
        data = request.data
        serializer = serializers.TaskLoadingGoodsModelSerializer(
            data=data,
            many=True,
            context={'user': request.user.profile},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
        task = serializer.validated_data[0].get('task')
        warehouses = tuple(map(lambda x: x.get('warehouse'), serializer.validated_data))
        returned_data = get_goods_by_warehouses(task, warehouses=warehouses)
        for each in returned_data:
            async_task(notifications.notify_about_task_goods_loaded, task.pk, each["warehouse"], user.pk)
        return Response(returned_data)


class TaskDeliveryPointSortView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TaskDeliveryPointSortSerializer
    queryset = models.TaskModel.objects.filter(is_active=True)
    action = 'retrieve'


class TaskDeliveryPointListView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.DetailTaskPermission)
    queryset = models.TaskModel.objects.filter(task_type_id='logistic', is_active=True)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        filters = self.request.query_params.get('filters', '')
        try:
            filters_dict = json.loads(filters)
        except json.JSONDecodeError:
            filters_dict = dict()
        delivery_points = common_utils.filter_queryset_from_get_param(
            filters_dict,
            task.task_delivery_points.filter(is_active=True)
        ).order_by('sort', 'created_at')
        data = serializers.TaskDeliveryPointSerializer(delivery_points, many=True).data
        return Response(data)


class TaskDeliveryPointCreateView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, permissions.LogistPermission)
    queryset = models.TaskModel.objects.filter(is_active=True, task_type_id='logistic')
    serializer_class = serializers.TaskDeliveryPointCreateSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(
            data=data,
            many=True,
            context={'request': request, 'task': self.get_object()}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TaskDeliveryPointUpdateView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, permissions.LogistPermission)
    queryset = models.TaskModel.objects.filter(is_active=True, task_type_id='logistic')
    serializer_class = serializers.TaskDeliveryPointCreateSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        with transaction.atomic():
            transaction.on_commit(
                lambda: async_task(notifications.notify_about_update_delivery_points, instance, request.user.profile)
            )
            add = data.get('add', None)
            if isinstance(add, list):
                for each in add:
                    add_serializer = serializers.TaskDeliveryPointCreateSerializer(data=each,
                                                                                   context={'task': instance})
                    add_serializer.is_valid(raise_exception=True)
                    add_serializer.save()
            edit = data.get('edit', None)
            if isinstance(edit, list):
                for each in edit:
                    try:
                        edit_instance = instance.task_delivery_points.get(pk=each.get('id'))
                    except ObjectDoesNotExist:
                        raise exceptions.ValidationError('Delivery point does not exist.')
                    edit_serializer = serializers.TaskDeliveryPointUpdateSerializer(instance=edit_instance, data=each)
                    edit_serializer.is_valid(raise_exception=True)
                    edit_serializer.save()
            delete = data.get('delete', None)
            if isinstance(delete, list):
                delete_serializer = serializers.TaskDeliveryPointDeleteSerializer(
                    data=delete,
                    many=True,
                    context={"task": instance}
                )
                delete_serializer.is_valid(raise_exception=True)
                delete_instances = [each.get('id') for each in delete_serializer.validated_data]
                delete_task_delivery_points(delete_instances)
        task_delivery_points = instance.task_delivery_points.all().order_by('sort', 'created_at')
        task_data = serializers.ListTaskSerializer(instance).data
        task_data['has_order'] = instance.task_delivery_points.all().exists()
        data = {
            'task': task_data,
            'delivery_points': serializers.TaskDeliveryPointSerializer(task_delivery_points, many=True).data,
        }
        return Response(data)


class TaskDeliveryPointSetNeedPayAmount(generics.UpdateAPIView):
    queryset = models.TaskDeliveryPointModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated, permissions.LogistPermission)
    serializer_class = serializers.TaskDeliveryPointSetNeedPayAmountSerializer


class TaskDeliveryPointDeleteView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, permissions.LogistPermission)
    queryset = models.TaskModel.objects.filter(is_active=True, task_type_id='logistic')
    serializer_class = serializers.TaskDeliveryPointDeleteSerializer

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.serializer_class(data=request.data, many=True, context={'request': request, 'task': task})
        serializer.is_valid(raise_exception=True)
        task_delivery_points = [each.get('id') for each in serializer.validated_data]
        with transaction.atomic():
            delete_task_delivery_points(task_delivery_points)
        return Response('ok')


class TaskDeliveryPointDeleteOrdersView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, permissions.LogistPermission)
    queryset = models.TaskModel.objects.filter(is_active=True, task_type_id='logistic')
    serializer_class = serializers.TaskDeliveryPointDeleteOrdersSerializer

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.serializer_class(data=request.data, many=True, context={'request': request, 'task': task})
        serializer.is_valid(raise_exception=True)
        orders = [each.get('id') for each in serializer.validated_data]
        with transaction.atomic():
            for order in orders:
                task_delivery_point = order.task_delivery_point
                order.task_delivery_point = None
                start_task_delivery_point = order.start_task_delivery_point
                order.start_task_delivery_point = None
                order.save(update_fields=('task_delivery_point', 'start_task_delivery_point',))
                if not task_delivery_point.goods_orders.filter(is_active=True).exists():
                    task_delivery_point.delete()
                if not start_task_delivery_point.start_goods_orders.filter(is_active=True).exists():
                    start_task_delivery_point.delete()
        return Response('ok')


class LogisticTaskPlusOneDay(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        plus_one_day_logistic_tasks()
        return Response(data={'status': 'ok'}, status=200)


class TaskPointsInfoView(APIView):
    '''
    Возвращает настройки для дравера указания адресов задач
    '''
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            config = AppInfo.objects.get(
                is_active=True,
                code='tasks_pask_points_info').metadata
        except AppInfo.DoesNotExist:
            config = {
                "zoom": 11,
                "center": [51.14015560526592, 71.42967224121095],
                "listTitle": "Адреса объектов",
                "form_rules": {
                    "lat": [
                        {
                            "type": "number",
                            "message": "Необходимо ввести число",
                            "trigger": "blur"
                        },
                        {
                            "message": "Обязательно для заполнения",
                            "trigger": "blur",
                            "required": True
                        }
                    ],
                    "lon": [
                        {
                            "type": "number",
                            "message": "Необходимо ввести число",
                            "trigger": "blur"
                        },
                        {
                            "message": "Обязательно для заполнения",
                            "trigger": "blur",
                            "required": True
                        }
                    ],
                    "name": {
                        "type": "string",
                        "message": "Обязательно для заполнения",
                        "required": True,
                        "whitespace": True
                    },
                    "address": {
                        "type": "string",
                        "message": "Обязательно для заполнения",
                        "required": True,
                        "whitespace": True
                    }
                },
                "mapOptions": {
                    "closePopupOnClick": False,
                    "attributionControl": False
                },
            }
        return Response(config, status=status.HTTP_200_OK)


class LeadSourcesView(APIView):
    """
    Возвращает список источников обращений потенциальных клиентов
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        lead_sources = models.LeadSourceModel.objects.filter(is_active=True).distinct()
        data = serializers.LeadSourceModelSerializer(lead_sources, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class RejectionReasonsView(APIView):
    """
    Возвращает список причин отказа от сделки
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        rejection_reasons = models.RejectionReasonModel.objects.filter(is_active=True).distinct()
        data = serializers.RejectionReasonModelSerializer(rejection_reasons, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class TaskFormInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        task_type = request.query_params.get('task_type', 'task')
        try:
            data = AppInfo.objects.get(is_active=True, code=f"tasks_{task_type}_form_info").metadata
        except AppInfo.DoesNotExist:

            data = {
                "formActions": {
                    "create_and_open": True,
                    "create_and_create": True,
                    "create_and_copy": True
                },
                "drawerTitle": "Добавить задачу",
                "name": {
                    "title": "Название задачи",
                    "rules": [
                        {"required": True, "message": 'Обязательно для заполнения', "trigger": 'blur'},
                        {"max": 255, "message": 'Максимум 255 символов', "trigger": 'blur'}
                    ]
                },
                "description": {
                    "title": "Описание задачи"
                },
                "date_start_plan": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "title": "Дата начала",  # Для логистической задачи - Планируемая дата выезда
                },
                "dead_line": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "title": "Крайний срок",
                },
                "owner": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать автора",
                    "title": "Постановщик",  # Для логистической задачи - Логист
                },
                "operator": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать исполнителя",
                    "auction": True,
                    "title": "Ответственный",  # Для логистической задачи - Водитель
                },
                "visors": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать наблюдателей",
                    "title": "Наблюдатели",  # Для логистической задачи - Экипаж
                },
                "priority": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "points": {
                        "ultralow": True,
                        "low": True,
                        "middle": True,
                        "tall": True,
                        "veryhigh": True
                    },
                    "title": "Приоритет",
                },
                "project": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать проект",
                    "title": "Проект",
                },
                "workgroup": {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать команду",
                    "title": "Команда",
                },
                "parent": {  # Для логистической задачи - null
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "title": "Родительская задача"
                },
                "files": {
                    "title": "Файлы"
                },
                "set_points": {
                    "available": False,
                    "button_text": "Указать адрес",
                    "drawer_title": "Адреса"
                }
            }
            if task_type == 'logistic':
                data['start_point'] = {
                    "label-col": {
                        "span": 5
                    },
                    "wrapper-col": {
                        "span": 12
                    },
                    "title": "Стартовая точка доставки",
                }
                # data['date_start_plan'] = {
                #     "label-col": {"span": 5},
                #     "wrapper-col": {"span": 12},
                #     "title": "Планируемая дата выезда",
                # }
                data['owner'] = {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать логиста",
                    "title": "Логист",
                }
                data['operator'] = {
                    "rules": {
                        "message": "Обязательно для заполнения",
                        "trigger": "blur",
                        "required": True
                    },
                    "title": "Водитель",
                    "auction": True,
                    "filters": {
                        "c1_roles__is_driver": True
                    },
                    "label-col": {
                        "span": 5
                    },
                    "drawerTitle": "Выбрать водителя",
                    "oldSelected": False,
                    "wrapper-col": {
                        "span": 12
                    }
                }
                data['visors'] = {
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "drawerTitle": "Выбрать экипаж",
                    "title": "Экипаж",
                }
                data['parent'] = None
                data['pvh'] = {
                    "name": "tasks.TaskModel_parts",
                    "collapse_title": "Доп. поля",
                    "path": "/pvh/form_info/",
                    "query": {
                        "model": "tasks.TaskModel",
                        "task_type": "<task_type>"
                    }
                }
            if task_type == 'interest':
                data["drawerTitle"] = 'Добавить интерес',
                data["name"]["title"] = 'Название интереса'
                data["description"]["title"] = 'Описание потребности'
                data["potential_contractor_name"] = {
                    "title": "Лид",
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "rules": [
                        {"required": False, "message": 'Обязательно для заполнения', "trigger": 'blur'},
                        {"max": 255, "message": 'Максимум 255 символов', "trigger": 'blur'}
                    ]
                }
                # data["potential_contractor_company"] = {
                #         "title": "Организация",
                #         "label-col": {"span": 5},
                #         "wrapper-col": {"span": 12},
                #         "rules": [
                #             {"required": False, "message": 'Обязательно для заполнения', "trigger": 'blur'},
                #             {"max": 255, "message": 'Максимум 255 символов', "trigger": 'blur'}
                #         ]
                #     }
                data["phone"] = {
                    "title": "Телефон",
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "rules": [
                        {"required": True, "message": 'Обязательно для заполнения', "trigger": 'blur'},
                        {"max": 20, "message": 'Максимум 255 символов', "trigger": 'blur'}
                    ]
                }
                data["email"] = {
                    "title": "Электронная почта",
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "rules": [
                        {"required": False, "message": 'Обязательно для заполнения', "trigger": 'blur'},
                        {"max": 255, "message": 'Максимум 255 символов', "trigger": 'blur'},
                        {"type": "email", "message": "Адрес электронной почты должен быть в формате имя@домен",
                         "trigger": "blur"}
                    ]
                }
                data["lead_source"] = {
                    "title": "Источник обращения",
                    "label-col": {"span": 5},
                    "wrapper-col": {"span": 12},
                    "rules": [
                        {"required": False},
                    ]
                }
        if task_type == 'interest':
            data.pop("contractor", None)
            data["customer_card"] = {
                "title": "Клиент",
                "label-col": {"span": 5},
                "wrapper-col": {"span": 12},
                "dataPath": "/app_info/filtered_select_list/?model=help_desk.CustomerCardModel",
                "listObject": "filteredSelectList",
                "rules": [
                    {"required": False, "message": 'Обязательно для заполнения', "trigger": 'change'},
                ],
            }
        return Response(data)


class DriverListView(generics.ListAPIView):
    queryset = ProfileModel.objects.select_related(
        'user',
        'avatar',
    ).prefetch_related(
        Prefetch(
            'operator_tasks',
            queryset=models.TaskModel.objects.filter(
                is_active=True,
                task_type_id='logistic'
            ).exclude(status_id__in='completed', )
        )
    ).filter(is_active=True, c1_roles__is_driver=True)
    serializer_class = serializers.DriverSerializer
    permission_classes = (IsAuthenticated, permissions.LogistPermission)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = common_utils.get_filter_queryset(self.request, ProfileModel, self.queryset)
        return queryset


class DeleteVoidLogisticTasks(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        from .cron import delete_void_logistic_tasks
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied()
        expire = request.data.get('expire', 60)
        if not isinstance(expire, int):
            raise exceptions.ValidationError('Expire type must be int.')
        message = delete_void_logistic_tasks(expire)
        return Response({"message": message})


class EfficiencyView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        obj = BaseModel.objects.super_get(pk=self.kwargs.get('pk'))
        if obj is None:
            raise exceptions.NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        request_user_organizations = request.user.profile.my_organizations
        permitted_organizations = get_tree_departments_related_organizations(request_user_organizations)
        instance = self.get_object()
        instance_model_name = instance.__class__.__name__
        models_list = [
            'ProfileModel',
            'ContractorModel',
            'ContractorDepartmentModel'
        ]
        if instance_model_name not in models_list:
            raise Http404

        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        project = request.query_params.get('project', None)

        lookup = Q()

        if instance_model_name == 'ProfileModel':  # Сотрудник
            if not permitted_organizations & set(instance.my_organizations):
                raise exceptions.ValidationError('Access is denied.')
            lookup &= Q(operator=instance)
        if instance_model_name == 'ContractorModel':  # Организация
            if instance.id not in permitted_organizations:
                raise exceptions.ValidationError('Access is denied.')
            lookup &= Q(contractor=instance)
        if instance_model_name == 'ContractorDepartmentModel':  # Отдел
            # TODO Дописать логику для отделов, когда появится возможность указывать их в задаче
            return Response({})

        if start is not None:
            lookup &= Q(created_at__gte=start)
        if end is not None:
            lookup &= Q(created_at__lte=end)
        if project is not None:
            lookup &= Q(project=project)

        not_complete_statuses = models.TaskStatusTypeModel.objects.filter(
            is_active=True,
            task_type='task',
            is_complete=False
        ).values_list('task_status', flat=True)
        complete_statuses = models.TaskStatusTypeModel.objects.filter(
            is_active=True,
            task_type='task',
            is_complete=True
        ).values_list('task_status', flat=True)

        qs = models.TaskModel.objects.filter(
            lookup,
            is_active=True
        ).aggregate(
            total=Count('id'),
            active=Coalesce(
                Sum(
                    Case(
                        When(
                            ~Q(status_id='new') &
                            ~Q(status_id='completed'),
                            then=1
                        ),
                        output_field=IntegerField(),
                        default=0
                    ),
                    default=0
                ),
                Value(0)
            ),
            overdue=Coalesce(
                Sum(
                    Case(
                        When(
                            Q(
                                dead_line__isnull=False,
                                dead_line__lte=timezone.now(),
                                status__in=not_complete_statuses
                            ),
                            then=1
                        ),
                        output_field=IntegerField(),
                        default=0
                    ),
                    default=0
                ),
                Value(0)
            ),
            completed=Coalesce(
                Sum(
                    Case(
                        When(
                            status_id__in=complete_statuses,
                            then=1
                        ),
                        output_field=IntegerField(),
                        default=0
                    ),
                    default=0
                ),
                Value(0)
            ),
            new=Coalesce(
                Sum(
                    Case(
                        When(
                            status_id='new',
                            then=1,
                        ),
                        output_field=IntegerField(),
                        default=0
                    ),
                    default=0
                ),
                Value(0)
            )
        )
        return Response(qs)


class TaskModelViewSet(BaseModelViewSet):
    """Этот вьюсет нужен, чтобы были стандартные эндпойнты DRF для CRUD-операций.
    Действует как прокси для других (рабочих) вьюсетов. Для ИИ-ассистента."""
    model = models.TaskModel
    permission_classes = (IsAuthenticated,)
    queryset = models.TaskModel.objects.filter(is_active=True)

    def get_queryset(self):
        return models.TaskModel.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        """Перенаправляет запрос на существующий CreateTaskView."""
        # Создаем новый request с теми же данными
        from django.test import RequestFactory
        from django.http import JsonResponse
        import json

        factory = RequestFactory()
        new_request = factory.post(
            '/api/tasks/task/create/',
            data=json.dumps(request.data),
            content_type='application/json'
        )
        new_request.user = request.user
        new_request.META.update(request.META)

        create_view = CreateTaskView.as_view()
        return create_view(new_request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """Перенаправляет запрос на существующий ListTaskView."""
        # Создаем новый request с теми же параметрами
        from django.test import RequestFactory

        factory = RequestFactory()
        new_request = factory.get(
            '/api/tasks/task/list/',
            data=request.query_params
        )
        new_request.user = request.user
        new_request.META.update(request.META)

        list_view = ListTaskView.as_view()
        return list_view(new_request, *args, **kwargs)

    def get_permissions(self):
        """Возвращает permissions в зависимости от действия."""
        if self.action == 'retrieve':
            return [IsAuthenticated(), permissions.DetailTaskPermission()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        """Обрабатывает GET-запросы для детального просмотра задачи."""
        obj = self.get_object()
        serializer = serializers.DetailTaskSerializer(obj, context={'request': request})
        data = serializer.data
        data['editable'] = obj.get_update_permission(request)
        if obj.task_type_id == 'interest':
            # CRM: фронт скрывает/поясняет кнопку LLM-анализа по этим полям.
            data.update(get_interest_analyze_permission_info(obj, request))
        return Response(data)

    @action(detail=True, methods=['post'], url_path='analyze_interest', url_name='analyze-interest')
    def analyze_interest(self, request, *args, **kwargs):
        """LLM-анализ интереса: выявить потребности и сопоставить их с каталогом."""
        obj = self.get_object()
        if obj.task_type_id != 'interest':
            raise exceptions.ValidationError({'task': 'LLM-анализ потребностей доступен только для интереса.'})
        # CRM: анализ изменяет интерес, поэтому проверяем update-доступ заранее
        # и возвращаем структурированную причину вместо общего "нельзя".
        permission_info = get_interest_analyze_permission_info(obj, request)
        if not permission_info.get('can_analyze_interest'):
            raise exceptions.PermissionDenied({
                'reason': 'interest_update_forbidden',
                'message': permission_info.get('analyze_interest_permission_message'),
                'current_roles': permission_info.get('current_roles', ()),
                'allowed_roles': permission_info.get('allowed_roles', ()),
            })

        from bpms.tasks.crm_lead_interest import analyze_interest_task

        force_create = request.data.get('force_create', True)
        refresh = request.data.get('refresh', False)
        result = analyze_interest_task(
            obj,
            request,
            force_create=force_create,
            refresh=refresh,
        )
        return Response(result)

    @action(detail=False, methods=['get'], url_path='my_day', url_name='my-day')
    def my_day(self, request, *args, **kwargs):
        """Список задач пользователя для 'Моего дня'."""

        def get_empty_paginated_response():
            queryset = models.TaskModel.objects.none()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = serializers.MyDayTaskSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = serializers.MyDayTaskSerializer(queryset, many=True)
            return Response(serializer.data)

        start = get_datetime_param(request, 'start')
        end = get_datetime_param(request, 'end')

        task_id_param = request.query_params.get('id')
        profile_param = request.query_params.get('user')
        profile_id = request.user.profile.pk

        if profile_param:
            profile_ids = profile_param.split(',')
        else:
            profile_ids = [str(profile_id)]

        # Если start и end не переданы, используем начало и конец текущего дня в часовом поясе сервера
        if not start and not end:
            current_date = timezone.localdate()
            start_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.min))
            end_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.max))
            start = start_of_day.isoformat()
            end = end_of_day.isoformat()

        # Извлекаем только дату из ISO строки (игнорируя время и часовой пояс)
        # Это нужно для фильтрации по полям типа date (например, TaskExecutionTimeModel.date)
        start_date = parse_date(start.split('T')[0])
        end_date = parse_date(end.split('T')[0])

        tasks_qs = get_my_day_task_queryset(request)

        if not tasks_qs.exists():
            return get_empty_paginated_response()
        tasks_qs = utils.prepare_my_day_task_queryset(
            tasks_qs,
            request,
            start=start,
            end=end,
            profile_ids=profile_ids
        )

        page = self.paginate_queryset(tasks_qs)
        if page is None:
            page = list(tasks_qs)

        if not page:
            return get_empty_paginated_response()

        analytics_data_map = build_my_day_analytics(
            tasks=page,
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
            profile_ids=profile_ids,
        )

        serializer = serializers.MyDayTaskSerializer(
            page,
            many=True,
            context={'analytics_data_map': analytics_data_map},
        )

        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='task_watchlist', url_name='task-watchlist')
    def task_watchlist(self, request, *args, **kwargs):
        """
        Список задач, требующих внимания:
        - group=overdue|stalled
        - role=is_executor|is_project_moderator|is_owner
        """

        def get_empty_paginated_response():
            queryset = models.TaskModel.objects.none()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = serializers.MyDayTaskSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = serializers.MyDayTaskSerializer(queryset, many=True)
            return Response(serializer.data)

        group_param = request.query_params.get('group')
        role_param = request.query_params.get('role')
        profile_id = request.user.profile.pk
        profile_ids = [str(profile_id)]

        if group_param not in ('overdue', 'stalled'):
            raise exceptions.ValidationError({'group': ['Allowed values: overdue, stalled']})
        if role_param not in ('is_executor', 'is_project_moderator', 'is_owner'):
            raise exceptions.ValidationError({'role': ['Allowed values: is_executor, is_project_moderator, is_owner']})

        # Для совместимости с существующей подготовкой queryset.
        current_date = timezone.localdate()
        start_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.min))
        end_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.max))
        start = start_of_day.isoformat()
        end = end_of_day.isoformat()

        cached_statuses = get_cached_statuses()
        not_complete_statuses = cached_statuses[1]

        tasks_qs = models.TaskModel.objects.filter(
            is_active=True,
            task_type_id='task',
            status__in=not_complete_statuses,
            is_auto_created=False,
        )

        if role_param == 'is_executor':
            tasks_qs = tasks_qs.filter(operator_id=profile_id)
        elif role_param == 'is_owner':
            tasks_qs = tasks_qs.filter(owner_id=profile_id)
        elif role_param == 'is_project_moderator':
            tasks_qs = tasks_qs.filter(
                project__isnull=False,
                project__workgroupmembersmodel__is_active=True,
                project__workgroupmembersmodel__member_id=profile_id,
                project__workgroupmembersmodel__membership_request_status__code='APPROVED',
                project__workgroupmembersmodel__membership_role__code__in=('FOUNDER', 'MODERATOR'),
            )

        if group_param == 'overdue':
            tasks_qs = tasks_qs.filter(
                dead_line__isnull=False,
                dead_line__lt=timezone.now(),
            )
        else:  # stalled
            stale_since_datetime = timezone.now() - datetime.timedelta(days=30)
            stale_since_date = stale_since_datetime.date()
            has_recent_execution_time = models.TaskExecutionTimeModel.objects.filter(
                is_active=True,
                task_id=OuterRef('pk'),
                date__gte=stale_since_date,
            )
            has_recent_comments = CommentModel.objects.filter(
                is_active=True,
                related_object_id=OuterRef('pk'),
                created_at__gte=stale_since_datetime,
            )
            tasks_qs = tasks_qs.annotate(
                has_recent_execution_time=Exists(has_recent_execution_time),
                has_recent_comments=Exists(has_recent_comments),
            ).filter(
                has_recent_execution_time=False,
                has_recent_comments=False,
            )

        tasks_qs = tasks_qs.distinct()
        tasks_qs = get_filter_queryset(request, models.TaskModel, tasks_qs)
        tasks_qs = filter_by_permissions(tasks_qs, request.user.profile)

        if not tasks_qs.exists():
            return get_empty_paginated_response()

        tasks_qs = utils.prepare_my_day_task_queryset(
            tasks_qs,
            request,
            start=start,
            end=end,
            profile_ids=profile_ids,
        )

        page = self.paginate_queryset(tasks_qs)
        if page is None:
            page = list(tasks_qs)

        if not page:
            return get_empty_paginated_response()

        analytics_data_map = build_my_day_analytics(
            tasks=page,
            profile_id=profile_id,
            profile_ids=profile_ids,
        )
        action_info_map = build_action_info_map(
            tasks=page,
            profile_id=profile_id,
        )

        serializer = serializers.MyDayTaskSerializer(
            page,
            many=True,
            context={
                'analytics_data_map': analytics_data_map,
                'action_info_map': action_info_map,
            },
        )

        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='task_watchlist_count', url_name='task-watchlist-count')
    def task_watchlist_count(self, request, *args, **kwargs):
        """
        Возвращает количества контрольных задач текущего пользователя:
        - overdue: просроченные
        - stalled: висячие (без трудозатрат и комментариев за последние 30 дней)
        - start_date/end_date: период текущей недели (понедельник-пятница)
        Роли учитываются одновременно: operator, owner, project moderator.
        """
        profile_id = request.user.profile.pk
        now_at = timezone.now()
        week_today = timezone.localdate()
        week_start_date = week_today - datetime.timedelta(days=week_today.weekday())
        week_end_date = week_start_date + datetime.timedelta(days=4)
        stale_since_datetime = now_at - datetime.timedelta(days=30)
        stale_since_date = stale_since_datetime.date()

        cached_statuses = get_cached_statuses()
        not_complete_statuses = cached_statuses[1]

        executor_lookup = Q(operator_id=profile_id)
        owner_lookup = Q(owner_id=profile_id)
        project_moderator_lookup = Q(
            project__isnull=False,
            project__is_project=True,
            project__workgroupmembersmodel__is_active=True,
            project__workgroupmembersmodel__member_id=profile_id,
            project__workgroupmembersmodel__membership_request_status__code='APPROVED',
            project__workgroupmembersmodel__membership_role__code__in=('FOUNDER', 'MODERATOR'),
        )

        role_lookup = executor_lookup | owner_lookup | project_moderator_lookup

        base_qs = models.TaskModel.objects.filter(
            is_active=True,
            task_type_id='task',
            status__in=not_complete_statuses,
            is_auto_created=False,
        ).filter(role_lookup).distinct()

        base_qs = get_filter_queryset(request, models.TaskModel, base_qs)
        base_qs = filter_by_permissions(base_qs, request.user.profile).distinct()

        has_recent_execution_time = models.TaskExecutionTimeModel.objects.filter(
            is_active=True,
            task_id=OuterRef('pk'),
            date__gte=stale_since_date,
        )
        has_recent_comments = CommentModel.objects.filter(
            is_active=True,
            related_object_id=OuterRef('pk'),
            created_at__gte=stale_since_datetime,
        )

        def get_problem_counts(queryset):
            overdue_count_value = queryset.filter(
                dead_line__isnull=False,
                dead_line__lt=now_at,
            ).values('pk').distinct().count()

            stalled_count_value = queryset.annotate(
                has_recent_execution_time=Exists(has_recent_execution_time),
                has_recent_comments=Exists(has_recent_comments),
            ).filter(
                has_recent_execution_time=False,
                has_recent_comments=False,
            ).values('pk').distinct().count()
            return {
                'overdue': overdue_count_value,
                'stalled': stalled_count_value,
            }

        total_counts = get_problem_counts(base_qs)

        role_counts = {
            'is_executor': get_problem_counts(base_qs.filter(executor_lookup)),
            'is_owner': get_problem_counts(base_qs.filter(owner_lookup)),
        }

        has_project_moderator_role = WorkgroupMembersModel.objects.filter(
            is_active=True,
            member_id=profile_id,
            work_group__is_project=True,
            membership_request_status__code='APPROVED',
            membership_role__code__in=('FOUNDER', 'MODERATOR'),
        ).exists()
        if has_project_moderator_role:
            role_counts['is_project_moderator'] = get_problem_counts(base_qs.filter(project_moderator_lookup))

        return Response({
            'start_date': week_start_date.isoformat(),
            'end_date': week_end_date.isoformat(),
            'overdue': total_counts['overdue'],
            'stalled': total_counts['stalled'],
            'roles': role_counts,
        })

    @action(detail=True, methods=['post'], url_path='watchlist_snooze', url_name='watchlist-snooze')
    def watchlist_snooze(self, request, *args, **kwargs):
        task = self.get_object()
        now_at = timezone.localtime()

        if not task.get_detail_permission(request):
            raise exceptions.PermissionDenied('Недостаточно прав для задачи.')

        days_until_friday = (4 - now_at.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        next_friday_date = (now_at + datetime.timedelta(days=days_until_friday)).date()
        snoozed_until = next_friday_date - datetime.timedelta(days=1)
        task.watchlist_snoozed_until = snoozed_until
        task.save(update_fields=['watchlist_snoozed_until'])

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='show_task_watchlist', url_name='show-task-watchlist')
    def show_task_watchlist(self, request, *args, **kwargs):
        """
        Флаг показа виджета контрольных задач.
        Расписание берется из AppInfo(code='task_watchlist_show', is_active=True).metadata.
        Если запись отсутствует или metadata невалидная — дефолт: пятница, 08:00-20:00.
        """
        config = {
            'is_enabled': True,
            'weekdays': [4],  # 0=Monday ... 6=Sunday
            'start_hour': 8,  # inclusive
            'end_hour': 20,  # exclusive
        }

        try:
            app_info = AppInfo.objects.get(code='task_watchlist_show', is_active=True)
        except AppInfo.DoesNotExist:
            app_info = None

        if app_info is not None:
            metadata = app_info.metadata
            if isinstance(metadata, dict):
                is_enabled_value = metadata.get('is_enabled')
                if isinstance(is_enabled_value, bool):
                    config['is_enabled'] = is_enabled_value

                weekdays_value = metadata.get('weekdays')
                if isinstance(weekdays_value, list):
                    parsed_weekdays = []
                    for weekday_raw in weekdays_value:
                        try:
                            weekday_value = int(weekday_raw)
                        except (TypeError, ValueError):
                            continue
                        if 0 <= weekday_value <= 6:
                            parsed_weekdays.append(weekday_value)
                    if parsed_weekdays:
                        config['weekdays'] = parsed_weekdays
                else:
                    weekday_raw = metadata.get('weekday')
                    try:
                        weekday_value = int(weekday_raw)
                    except (TypeError, ValueError):
                        weekday_value = None
                    if weekday_value is not None and 0 <= weekday_value <= 6:
                        config['weekdays'] = [weekday_value]

                for hour_key in ('start_hour', 'end_hour'):
                    hour_raw = metadata.get(hour_key)
                    if isinstance(hour_raw, str) and ':' in hour_raw:
                        hour_raw = hour_raw.split(':', 1)[0]
                    try:
                        hour_value = int(hour_raw)
                    except (TypeError, ValueError):
                        continue
                    if 0 <= hour_value <= 24:
                        config[hour_key] = hour_value

        now = timezone.localtime()
        is_allowed_day = now.weekday() in config['weekdays']
        is_allowed_hour = config['start_hour'] <= now.hour < config['end_hour']
        should_show = config['is_enabled'] and is_allowed_day and is_allowed_hour
        return Response({'show_task_watchlist': bool(should_show)})

    @action(detail=False, methods=['get'], url_path='my_day_tasks_count', url_name='my-day-tasks-count')
    def my_day_tasks_count(self, request, *args, **kwargs):
        """Возвращает количество задач, событий, встреч и обращений хелпдеска для 'Моего дня'."""
        profile = request.user.profile
        profile_id = str(profile.pk)
        tariff_section_codes = set(get_tariff_section_codes(profile))

        # Соответствие между ключом ответа и code секции приложения
        response_key_to_section_code = {
            'tasks': 'tasks',
            'events': 'calendar',
            'meetings': 'meetings',
            'helpdesk': 'help_desk',
        }

        response_data = dict()

        # 1. Задачи, где я исполнитель или соисполнитель
        if response_key_to_section_code['tasks'] in tariff_section_codes:
            tasks_qs = get_my_day_task_queryset(request)
            tasks_qs = tasks_qs.filter(
                Q(operator_id=profile_id) | Q(cooperators__id=profile_id)
            ).distinct()
            response_data['tasks'] = tasks_qs.count()

        # 2. События "Мой день"
        if response_key_to_section_code['events'] in tariff_section_codes:
            events_qs = get_my_day_event_queryset(request)
            response_data['events'] = events_qs.count()

        # 3. Видеовстречи "Мой день"
        if response_key_to_section_code['meetings'] in tariff_section_codes:
            meetings_qs = get_my_day_meeting_sections_queryset(request)
            response_data['meetings'] = meetings_qs.count()

        # 4. Обращения хелпдеска "Мой день"
        if response_key_to_section_code['helpdesk'] in tariff_section_codes:
            response_data['helpdesk'] = get_my_day_tickets_queryset(request).count()

        return Response(response_data)

    def update(self, request, *args, **kwargs):
        """Перенаправляет запрос на существующий UpdateTaskView."""
        # Создаем новый request с теми же данными
        from django.test import RequestFactory
        import json

        factory = RequestFactory()
        new_request = factory.put(
            f'/api/tasks/task/{kwargs["pk"]}/update/',
            data=json.dumps(request.data),
            content_type='application/json'
        )
        new_request.user = request.user
        new_request.META.update(request.META)

        update_view = UpdateTaskView.as_view()
        return update_view(new_request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Перенаправляет запрос на существующий UpdateTaskView."""
        # Создаем новый request с теми же данными
        from django.test import RequestFactory
        import json

        factory = RequestFactory()
        new_request = factory.patch(
            f'/api/tasks/task/{kwargs["pk"]}/update/',
            data=json.dumps(request.data),
            content_type='application/json'
        )
        new_request.user = request.user
        new_request.META.update(request.META)

        update_view = UpdateTaskView.as_view()
        return update_view(new_request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Перенаправляет запрос на существующий DeleteTaskView.
        DeleteTaskView ожидает PUT-запрос с id в теле запроса."""
        # Получаем id из URL параметров
        task_id = kwargs.get('pk')

        # Создаем mock объект с нужными атрибутами
        class MockRequest:
            def __init__(self, original_request, data):
                self.user = original_request.user
                self.META = original_request.META.copy()
                self.method = 'PUT'
                self.path = '/api/tasks/task/delete/'
                self._data = data

            @property
            def data(self):
                return self._data

        mock_request = MockRequest(request, {'id': task_id})

        # Создаем экземпляр DeleteTaskView и выполняем запрос
        delete_view = DeleteTaskView()
        delete_view.setup(mock_request, *args, **kwargs)
        return delete_view.update(mock_request, *args, **kwargs)


class OnboardingTasksViewSet(BaseModelViewSet):
    """
    ViewSet для управления обучающими задачами пользователя
    """
    permission_classes = (IsAuthenticated,)
    queryset = models.TaskModel.objects.filter(is_active=True, is_onboarding=True)

    @action(detail=False, methods=['post'], url_path='create')
    def create_onboarding_tasks(self, request):
        """
        Создает обучающие задачи для текущего пользователя
        """
        user = request.user.profile

        try:
            # Проверяем, есть ли уже обучающие задачи
            existing_onboarding_tasks = user.owner_tasks.filter(
                is_onboarding=True,
                is_active=True
            )

            if existing_onboarding_tasks.exists():
                return Response(
                    {
                        'success': False,
                        'message': 'У пользователя уже есть обучающие задачи',
                        'existing_tasks_count': existing_onboarding_tasks.count()
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Создаем обучающие задачи
            from .utils import create_onboarding_data
            result = create_onboarding_data(user.pk)

            if result['success']:
                return Response(
                    {
                        'success': True,
                        'message': result['message']
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {
                        'success': False,
                        'message': result['message'],
                        'error': result.get('error')
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'message': f'Ошибка при создании обучающих задач: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='delete')
    def delete_onboarding_tasks(self, request):
        """
        Удаляет (деактивирует) обучающие задачи текущего пользователя
        """
        user = request.user.profile

        try:
            # Удаляем обучающие задачи
            from .utils import delete_onboarding_data
            result = delete_onboarding_data(user.pk)

            if result['success']:
                return Response(
                    {
                        'success': True,
                        'message': result['message']
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'success': False,
                        'message': result['message'],
                        'error': result.get('error')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'message': f'Ошибка при удалении обучающих задач: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskListFromReason(generics.ListAPIView):
    queryset = models.TaskModel.objects.filter(is_active=True).order_by('counter', 'name')
    serializer_class = serializers.ShortTaskSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        reason_id = self.request.query_params.get('reason')
        if not reason_id:
            return queryset.none()
        reason = utils.get_reason_object(reason_id)
        if not reason:
            return queryset.none()
        if not reason.get_detail_permission(self.request):
            return queryset.none()
        queryset = queryset.filter(reason=reason_id)
        return queryset
