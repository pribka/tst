import math
from datetime import timedelta, time, datetime

import pandas as pd
from uuid import UUID
from django.db.models import Q, Sum, Value, DecimalField, IntegerField, Exists, OuterRef
from django.db.models.functions import Coalesce
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone, dateparse
from django.core.cache import cache
from change_history.models import ChangeHistoryModel
from bpms.comments.models import CommentModel
from bpms.workgroups.models import WorkgroupMembersModel
from . import models
from .utils import get_task_queryset, get_cached_statuses, get_user_today_from_iso, filter_by_permissions
from common.utils import get_datetime_param, get_filter_queryset


# Константы для анализа истории изменений
STATUS_INWORK_CODES = {"in_work", "in_process", "on_check", "on_testing"}
STATUS_REWORK_CODES = {"on_rework", "need_help"}
STATUS_COMPLETED_CODES = {"completed", "successfully_completed", "failed"}
PROP_TASK_STATUS = "task__status"


def _to_uuid(val):
    """Преобразует значение в UUID."""
    try:
        return UUID(str(val))
    except Exception:
        return None


def get_task_execution_time_dataframe(task_ids, profile_ids, start_date=None, end_date=None):
    """
    Получает DataFrame с трудозатратами для задач.
    
    Args:
        task_ids: список UUID задач
        profile_ids: список ID профилей (строки) для фильтрации по user_id
        start_date: начальная дата для hours_total_range (опционально)
        end_date: конечная дата для hours_total_range (опционально)
    
    Returns:
        pd.DataFrame с колонками: task_id, hours_total_all, hours_total_range, duration_total_all, duration_total_range
    """
    zero_dec = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
    zero_int = Value(0, output_field=IntegerField())
    tet_qs = (
        models.TaskExecutionTimeModel.objects
        .filter(is_active=True, task_id__in=task_ids, user_id__in=profile_ids)
    )
    
    tet_qs = tet_qs.values("task_id").annotate(
        hours_total_all=Coalesce(
            Sum("hours", output_field=DecimalField(max_digits=12, decimal_places=2)),
            zero_dec
        ),
        hours_total_range=Coalesce(
            Sum(
                "hours",
                filter=Q(
                    date__gte=start_date,
                    date__lte=end_date
                ) if start_date and end_date else Q(),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            zero_dec
        ),
        duration_total_all=Coalesce(
            Sum("duration", output_field=IntegerField()),
            zero_int
        ),
        duration_total_range=Coalesce(
            Sum(
                "duration",
                filter=Q(
                    date__gte=start_date,
                    date__lte=end_date
                ) if start_date and end_date else Q(),
                output_field=IntegerField(),
            ),
            zero_int
        ),
    )
    tet_df = pd.DataFrame.from_records(tet_qs) if tet_qs else pd.DataFrame(
        columns=["task_id", "hours_total_all", "hours_total_range", "duration_total_all", "duration_total_range"])
    if not tet_df.empty:
        tet_df["task_id"] = tet_df["task_id"].map(lambda x: str(x))
    
    return tet_df


def get_task_status_history_dataframes(task_ids):
    """
    Получает DataFrame с first_start_at, completed_at и last_completed_at для задач на основе истории изменений статусов.
    
    Args:
        task_ids: список UUID задач
    
    Returns:
        tuple: (df_first_start, df_completed, df_last_completed) - три DataFrame с колонками task_id и соответствующими датами
    """
    from change_history.models import ChangeHistoryModel
    
    # Получаем ContentType для TaskModel
    task_ct = ContentType.objects.get_for_model(models.TaskModel)
    
    # Получаем маппинг статусов для извлечения кодов из истории изменений
    status_id_to_code = dict(models.TaskStatusModel.objects.values_list("id", "code"))
    
    # Получаем историю изменений статусов
    hist_all_qs = (
        ChangeHistoryModel.objects
        .filter(is_active=True, related_object__ct=task_ct, related_object_id__in=task_ids)
        .select_related("object_property")
        .only("id", "related_object_id", "action_date", "object_property__code", "before_data", "after_data")
        .order_by("related_object_id", "action_date", "id")
    )
    hist_all_df = pd.DataFrame.from_records(
        hist_all_qs.values("id", "related_object_id", "action_date", "object_property__code", "before_data",
                           "after_data")
    ).rename(columns={"related_object_id": "task_id", "object_property__code": "prop_code"})
    
    if hist_all_df.empty:
        hist_all_df = pd.DataFrame(columns=["id", "task_id", "action_date", "prop_code", "before_data", "after_data"])
    else:
        hist_all_df["action_date"] = pd.to_datetime(hist_all_df["action_date"], errors="coerce")
        hist_all_df["task_id"] = hist_all_df["task_id"].map(lambda x: str(x))
    
    # Маппинг статусов
    def status_after_code(row):
        if row["prop_code"] != PROP_TASK_STATUS:
            return None
        ad = row.get("after_data")
        if ad is None:
            return None
        # Для task__status в after_data всегда хранится строка UUID
        if isinstance(ad, str):
            uid = _to_uuid(ad)
            return status_id_to_code.get(uid) if uid else None
        return None
    
    df_status = hist_all_df[hist_all_df["prop_code"] == PROP_TASK_STATUS].copy()
    if not df_status.empty:
        df_status["after_status_code"] = df_status.apply(status_after_code, axis=1)
        
        df_first_start = (
            df_status[df_status["after_status_code"].isin(STATUS_INWORK_CODES)]
            .sort_values(["task_id", "action_date"])
            .groupby("task_id", as_index=False)["action_date"].first()
            .rename(columns={"action_date": "first_start_at"})
        )
        df_completed = (
            df_status[df_status["after_status_code"].isin(STATUS_COMPLETED_CODES)]
            .sort_values(["task_id", "action_date"])
            .groupby("task_id", as_index=False)["action_date"].first()
            .rename(columns={"action_date": "completed_at"})
        )
        df_last_completed = (
            df_status[df_status["after_status_code"].isin(STATUS_COMPLETED_CODES)]
            .groupby("task_id", as_index=False)["action_date"].max()
            .rename(columns={"action_date": "last_completed_at"})
        )
    else:
        df_first_start = pd.DataFrame(columns=["task_id", "first_start_at"])
        df_completed = pd.DataFrame(columns=["task_id", "completed_at"])
        df_last_completed = pd.DataFrame(columns=["task_id", "last_completed_at"])
    
    return df_first_start, df_completed, df_last_completed


def _build_participant_filter(profile_ids):
    """
    Фильтр: пользователь является участником задачи (любая роль).
    Используем Exists вместо прямых M2M lookups, чтобы избежать LEFT JOIN
    и вызванного ими умножения строк (+ необходимости DISTINCT).
    """
    return (
        Q(operator_id__in=profile_ids) |
        Q(owner_id__in=profile_ids) |
        Exists(models.TaskVisor.objects.filter(task_id=OuterRef('pk'), user_id__in=profile_ids)) |
        Exists(models.TaskCooperator.objects.filter(task_id=OuterRef('pk'), user_id__in=profile_ids))
    )


def get_history_task_ids(start, end, profile_ids=None):
    """
    Возвращает set task_ids из истории изменений за период.
    
    Args:
        start: начальная дата/время
        end: конечная дата/время
        profile_ids: опциональный список ID профилей для фильтрации по автору
    """
    task_ct = ContentType.objects.get_for_model(models.TaskModel)
    hist_window_qs = (
        ChangeHistoryModel.objects
        .filter(
            is_active=True,
            related_object__ct=task_ct,
            action_date__gte=start,
            action_date__lt=end,
        )
    )
    # Если передан profile_ids, фильтруем по автору
    if profile_ids:
        hist_window_qs = hist_window_qs.filter(author_id__in=profile_ids)
    
    hist_window_qs = hist_window_qs.only("id", "related_object_id")
    return set(hist_window_qs.values_list("related_object_id", flat=True).distinct())


def get_comment_task_ids(start, end, profile_ids=None):
    """
    Возвращает set task_ids из комментариев пользователей за период.
    
    Args:
        start: начальная дата/время
        end: конечная дата/время
        profile_ids: опциональный список ID профилей для фильтрации по автору
    """
    task_ct = ContentType.objects.get_for_model(models.TaskModel)
    comments_qs = (
        CommentModel.objects
        .filter(
            is_active=True,
            related_object__ct=task_ct,
            created_at__gte=start,
            created_at__lt=end,
        )
    )
    # Если передан profile_ids, фильтруем по автору
    if profile_ids:
        comments_qs = comments_qs.filter(author_id__in=profile_ids)
    
    comments_qs = comments_qs.only("id", "related_object_id")
    comment_task_ids = comments_qs.values_list("related_object_id", flat=True).distinct()
    return set(comment_task_ids)


def get_in_work_task_ids_for_period(start, end, profile_ids, only_operators=False):
    """
    Возвращает set task_ids со статусом in_work, если период включает текущую дату.
    """
    start_date = dateparse.parse_date(start.split('T')[0])
    end_date = dateparse.parse_date(end.split('T')[0])
    if not (start_date and end_date):
        return set()

    user_today = get_user_today_from_iso(start)
    if not (start_date <= user_today <= end_date):
        return set()
    
    in_work_qs = models.TaskModel.objects.filter(
        is_active=True,
        task_type_id='task',
        status__code='in_work'
    )
    operator_filter = Q(operator_id__in=profile_ids)
    cooperators_filter = Q(cooperators__in=profile_ids)
    owner_filter = Q(owner_id__in=profile_ids)
    visors_filter = Q(visors__in=profile_ids)
    
    if only_operators:
        profile_filter = operator_filter | cooperators_filter
    else:
        profile_filter = operator_filter | owner_filter | visors_filter | cooperators_filter
    in_work_qs = in_work_qs.filter(profile_filter).distinct()
    in_work_task_ids = in_work_qs.values_list('id', flat=True)
    return set(in_work_task_ids)


def get_execution_time_task_ids(start, end, profile_ids):
    """
    Возвращает set task_ids, где выбранные пользователи оставляли трудозатраты за период.
    """
    start_date = dateparse.parse_date(start.split('T')[0])
    end_date = dateparse.parse_date(end.split('T')[0])
    if not (start_date and end_date):
        return set()
    
    exec_qs = (
        models.TaskExecutionTimeModel.objects
        .filter(
            is_active=True,
            user_id__in=profile_ids,
            date__gte=start_date,
            date__lte=end_date,
        )
        .only("id", "task_id")
    )
    execution_task_ids = exec_qs.values_list("task_id", flat=True).distinct()
    return set(execution_task_ids)


def get_planned_task_ids(start, end, profile_ids):
    """
    Возвращает set task_ids задач в незавершающих статусах:
    - у которых date_start_plan входит в календарные недели, покрывающие start—end;
    - либо dead_line не позже конца недели, в которую входит end (просроченные или сдать на этой неделе).
    Возвращает только те задачи, где profile_ids являются исполнителями или соисполнителями.
    """
    # Преобразуем start и end в даты
    start_date = dateparse.parse_date(start.split('T')[0])
    end_date = dateparse.parse_date(end.split('T')[0])
    
    # Находим ближайший к start понедельник (минимальное время)
    start_weekday = start_date.weekday()  # 0 = понедельник, 6 = воскресенье
    monday_date = start_date - timedelta(days=start_weekday)
    start_dt = timezone.make_aware(datetime.combine(monday_date, time.min))
    
    # Находим ближайшее к end воскресенье (максимальное время)
    end_weekday = end_date.weekday()  # 0 = понедельник, 6 = воскресенье
    days_to_sunday = 6 - end_weekday
    sunday_date = end_date + timedelta(days=days_to_sunday)
    end_dt = timezone.make_aware(datetime.combine(sunday_date, time.max))
    
    # Получаем завершающие статусы для исключения
    complete_statuses = get_cached_statuses()[2]
    
    # Конец дня start_date (макс. время дня)
    end_of_day_dt = timezone.make_aware(datetime.combine(start_date, time.max))
    
    # Задача запланирована на выбранный день или раньше (date_start_plan <= конец дня) ИЛИ дедлайн <= конец недели
    planned_qs = (
        models.TaskModel.objects
        .filter(
            Q(is_active=True) &
            ~Q(status_id__in=complete_statuses) &
            (
                Q(date_start_plan__lte=end_of_day_dt) |
                Q(dead_line__isnull=False, dead_line__lte=end_dt)
            )
        )
    )
    
    # Фильтруем по исполнителям и соисполнителям (аналогично only_operators=True)
    operator_filter = Q(operator_id__in=profile_ids)
    cooperators_filter = Q(cooperators__in=profile_ids)
    profile_filter = operator_filter | cooperators_filter
    planned_qs = planned_qs.filter(profile_filter).distinct()
    
    planned_task_ids = planned_qs.values_list("id", flat=True)
    return set(planned_task_ids)


def get_my_day_task_ids_grouped(start, end, request, profile_ids):
    """
    Разделяет задачи "Мой день" на группы pinned и activity.
    Группа other считается отдельно как queryset, чтобы не материализовывать
    большой список task_id в Python.
    """
    current_profile_id = str(request.user.profile.pk)
    cache_key = f"my_day_grouped_{current_profile_id}_{start}_{end}_{'_'.join(sorted(profile_ids))}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return {
            'pinned': set(cached_result['pinned']),
            'activity': set(cached_result['activity']),
        }
    
    # 1. Получить pinned (закрепленные задачи)
    # Для СВОЕГО рабочего дня за СЕГОДНЯ показываем только активные pinned задачи
    start_date = dateparse.parse_date(start.split('T')[0])
    end_date = dateparse.parse_date(end.split('T')[0])
    profile_id = str(request.user.profile.pk)
    
    user_today = get_user_today_from_iso(start)
    is_today = start_date <= user_today <= end_date
    is_my_day = profile_id in profile_ids
        
    if is_today:
        # Мой рабочий день за сегодня - только активные pinned
        my_pinned_task_ids = set(
            models.TaskPinnedModel.objects
            .filter(user_id=profile_id, is_active=True)
            .values_list('task_id', flat=True)
        )
    elif end_date < user_today:
        # История - учитываем временной промежуток
        # Задача считается закрепленной в промежутке, если:
        # - была закреплена до конца промежутка (created_at <= end)
        # - и либо все еще закреплена (is_active=True), либо была откреплена после начала промежутка (deleted_at >= start)
        my_pinned_task_ids = set(
            models.TaskPinnedModel.objects
            .filter(
                user_id=profile_id,
                created_at__lte=end
            )
            .filter(
                Q(is_active=True) | Q(deleted_at__gte=start)
            )
            .values_list('task_id', flat=True)
        )
    else:
        # Будущее - закрепленных задач еще нет
        my_pinned_task_ids = set()
    
    # 2. Получить activity (задачи с изменениями за период из комментариев, истории и трудозатрат по дате)
    activity_task_ids = set()
    activity_task_ids.update(get_comment_task_ids(start, end, profile_ids))
    activity_task_ids.update(get_history_task_ids(start, end, profile_ids))
    activity_task_ids.update(get_execution_time_task_ids(start, end, profile_ids))
    
    # 3. Разделить на группы с учетом приоритета pinned > activity > other.
    # Если смотрю другого пользователя, то в pinned попадают только его задачи, которые закреплены у меня.
    if is_my_day:
        pinned_task_ids = my_pinned_task_ids
    else:
        complete_statuses = get_cached_statuses()[2]
        other_pinned_task_ids = set(
            models.TaskModel.objects
            .filter(
                is_active=True,
                task_type_id='task',
                pk__in=my_pinned_task_ids,
            )
            .exclude(status_id__in=complete_statuses)
            .filter(_build_participant_filter(profile_ids))
            .values_list('pk', flat=True)
        )
        pinned_task_ids = (my_pinned_task_ids & activity_task_ids) | other_pinned_task_ids
    result = {
        'pinned': pinned_task_ids,
        'activity': activity_task_ids - pinned_task_ids,
    }
    
    # Сохраняем в кэш (преобразуем set в list для сериализации)
    cache.set(cache_key, {
        'pinned': list(result['pinned']),
        'activity': list(result['activity']),
    }, timeout=10)
    
    return result


def _build_role_filter(profile_ids, role=None):
    """
    Строит фильтр участника задачи, опционально ограниченный конкретной ролью.
    Без role — полный фильтр по всем ролям (== _build_participant_filter).
    """
    if role == 'is_executor':
        return (
            Q(operator_id__in=profile_ids) |
            Exists(models.TaskCooperator.objects.filter(task_id=OuterRef('pk'), user_id__in=profile_ids))
        )
    if role == 'is_owner':
        return Q(owner_id__in=profile_ids)
    if role == 'is_visor':
        return Exists(
            models.TaskVisor.objects.filter(task_id=OuterRef('pk'), user_id__in=profile_ids)
        )
    return _build_participant_filter(profile_ids)


def get_my_day_task_queryset(request):
    """
    Получает base_queryset для "Моего дня" и применяет фильтрацию по правам.

    Поток фильтрации:
    1. Формируем «форму» выборки по группе (pinned / activity / other / all)
       — без фильтра по участнику, только структура группы.
    2. Единообразно применяем profile_filter (роль/участник) ко всем группам.
    3. Накладываем project / workgroup / права.
    """
    task_id_param = request.query_params.get('id')
    start = get_datetime_param(request, 'start')
    end = get_datetime_param(request, 'end')

    profile_param = request.query_params.get('user')
    project_param = request.query_params.get('project')
    workgroup_param = request.query_params.get('workgroup')
    group_param = request.query_params.get('group')
    role_filter = request.query_params.get('role')

    profile_id = request.user.profile.pk
    if profile_param:
        profile_ids = profile_param.split(',')
    else:
        profile_ids = [str(profile_id)]

    profile_filter = _build_role_filter(profile_ids, role_filter)

    project_ids = project_param.split(',') if project_param else None
    workgroup_ids = workgroup_param.split(',') if workgroup_param else None

    if task_id_param:
        base_queryset = models.TaskModel.objects.filter(
            is_active=True,
            pk=task_id_param
        )
    else:
        grouped_task_ids = get_my_day_task_ids_grouped(start, end, request, profile_ids)
        pinned_task_ids = grouped_task_ids['pinned']
        activity_task_ids = grouped_task_ids['activity']
        complete_statuses = get_cached_statuses()[2]

        if group_param == 'pinned':
            if not pinned_task_ids:
                return models.TaskModel.objects.none()
            base_queryset = models.TaskModel.objects.filter(
                is_active=True,
                task_type_id='task',
                pk__in=pinned_task_ids,
            )
        elif group_param == 'activity':
            if not activity_task_ids:
                return models.TaskModel.objects.none()
            base_queryset = models.TaskModel.objects.filter(
                is_active=True,
                task_type_id='task',
                pk__in=activity_task_ids,
            )
        elif group_param == 'other':
            base_queryset = (
                models.TaskModel.objects
                .filter(is_active=True, task_type_id='task')
                .exclude(status_id__in=complete_statuses)
                .exclude(pk__in=pinned_task_ids)
                .exclude(pk__in=activity_task_ids)
            )
        elif group_param:
            base_queryset = models.TaskModel.objects.none()
        else:
            special_task_ids = pinned_task_ids | activity_task_ids
            special_qs = models.TaskModel.objects.filter(
                is_active=True,
                task_type_id='task',
                pk__in=special_task_ids,
            )
            other_qs = (
                models.TaskModel.objects
                .filter(is_active=True, task_type_id='task')
                .exclude(status_id__in=complete_statuses)
                .exclude(pk__in=special_task_ids)
            )
            base_queryset = other_qs | special_qs

        base_queryset = base_queryset.filter(profile_filter)

    if project_ids:
        base_queryset = base_queryset.filter(project_id__in=project_ids)
    if workgroup_ids:
        base_queryset = base_queryset.filter(workgroup_id__in=workgroup_ids)

    base_queryset = get_filter_queryset(request, models.TaskModel, base_queryset)
    tasks_qs = filter_by_permissions(base_queryset, request.user.profile)

    return tasks_qs


def calculate_actual_duration(base_df):
    """
    Вычисляет actual_duration_days для задач в зависимости от текущего статуса.
    Возвращает 0 вместо None для упрощения обработки.
    
    Args:
        base_df: DataFrame с колонками: status_code, first_start_at, last_completed_at
    
    Returns:
        Series с actual_duration_days (0 вместо None)
    """
    def td_days(a, b):
        if pd.isna(a) or pd.isna(b):
            return 0
        days = (a - b).total_seconds() / 86400.0
        return int(math.ceil(days))
    
    now = timezone.now()
    
    def calculate_row(row):
        status_code = row.get("status_code")
        first_start_at = row.get("first_start_at")
        last_completed_at = row.get("last_completed_at")
        
        # Если нет first_start_at, возвращаем 0
        if pd.isna(first_start_at):
            return 0
        
        # 1. Если задача в завершающем статусе - показываем время от первого старта до последнего завершения
        if status_code in STATUS_COMPLETED_CODES:
            if pd.isna(last_completed_at):
                return 0
            return td_days(last_completed_at, first_start_at)
        
        # 2. Если задача в рабочем статусе или в статусе переработки - показываем время от первого старта до текущего момента
        if status_code in STATUS_INWORK_CODES or status_code in STATUS_REWORK_CODES:
            return td_days(now, first_start_at)
        
        # 3. В противном случае (задача новая) - возвращаем 0
        return 0
    
    return base_df.apply(calculate_row, axis=1)


def calculate_related_profile_ids(base_df, profile_ids):
    """
    Вычисляет связанные profile_ids для каждой задачи.
    Задача попадает в список, если хотя бы один profile_id связан с ней 
    (operator/cooperator/owner/visor).
    
    Args:
        base_df: DataFrame с колонками: task_id, operator, owner, visors, cooperators
        profile_ids: список profile_ids для проверки (строки)
    
    Returns:
        Series со списками связанных profile_ids для каждой задачи
    """
    profile_ids_set = set(profile_ids)
    
    def calculate_row(row):
        related_ids = []
        remaining_ids = profile_ids_set.copy()
        
        # Проверяем operator (уже строка или None)
        operator_id = row.get("operator")
        if operator_id and operator_id in remaining_ids:
            related_ids.append(operator_id)
            remaining_ids.discard(operator_id)
            if not remaining_ids:
                return related_ids
        
        # Проверяем owner (уже строка или None)
        owner_id = row.get("owner")
        if owner_id and owner_id in remaining_ids:
            related_ids.append(owner_id)
            remaining_ids.discard(owner_id)
            if not remaining_ids:
                return related_ids
        
        # Проверяем visors (всегда список при создании)
        visors = row.get("visors", [])
        for visor_id in visors:
            if visor_id in remaining_ids:
                related_ids.append(visor_id)
                remaining_ids.discard(visor_id)
                if not remaining_ids:
                    return related_ids
        
        # Проверяем cooperators (всегда список при создании)
        cooperators = row.get("cooperators", [])
        for cooperator_id in cooperators:
            if cooperator_id in remaining_ids:
                related_ids.append(cooperator_id)
                remaining_ids.discard(cooperator_id)
                if not remaining_ids:
                    return related_ids
        
        return related_ids
    
    return base_df.apply(calculate_row, axis=1)


def build_my_day_analytics(tasks, profile_id, start_date=None, end_date=None, profile_ids=None):
    """
    Строит analytics_data_map для 'Моего дня' по списку задач.

    Args:
        tasks: итерируемый список TaskModel
        start_date: начальная дата для диапазона трудозатрат
        end_date: конечная дата для диапазона трудозатрат
        profile_ids: список ID профилей (строки) для расчета related_profile_ids
        profile_id: ID профиля (строка или UUID) текущего пользователя (обязателен)

    Returns:
        dict: {task_id: {...}} для передачи в MyDayTaskSerializer через analytics_data_map
    """
    if profile_ids is None:
        profile_ids = []

    tasks_list = list(tasks)
    if not tasks_list:
        return {}

    # Собираем данные задач в DataFrame
    rows = []
    for task in tasks_list:
        visor_ids = [str(profile.id) for profile in task.visors.all()]
        cooperator_ids = [str(profile.id) for profile in task.cooperators.all()]

        rows.append({
            "task_id": str(task.pk),
            "counter": task.counter,
            "name": task.name,
            "created_at": task.created_at,
            "status_id": str(task.status_id) if task.status_id else None,
            "status_code": task.status.code if task.status else None,
            "project_id": str(task.project_id) if task.project_id else None,
            "organization_id": str(task.organization_id) if task.organization_id else None,
            "date_start_plan": task.date_start_plan,
            "dead_line": task.dead_line,
            "priority": task.priority,
            "author": str(task.author_id) if task.author_id else None,
            "operator": str(task.operator_id) if task.operator_id else None,
            "owner": str(task.owner_id) if task.owner_id else None,
            "visors": visor_ids,
            "cooperators": cooperator_ids,
        })

    tasks_df = pd.DataFrame(rows)
    if tasks_df.empty:
        return {}

    tasks_df["task_id"] = tasks_df["task_id"].astype(str)

    for column_name in ("created_at", "date_start_plan", "dead_line"):
        if column_name in tasks_df.columns:
            tasks_df[column_name] = pd.to_datetime(tasks_df[column_name], errors="coerce")

    paginated_task_ids_uuid = [task.id for task in tasks_list]

    # Вычисляем задачи с непросмотренными комментариями для текущего пользователя
    unviewed_comments_qs = CommentModel.objects.filter(
        related_object_id__in=paginated_task_ids_uuid,
        is_active=True
    ).exclude(
        object_viewer_relations__profile_id=profile_id
    ).values_list("related_object_id", flat=True).distinct()
    tasks_with_unviewed_comments = set(str(task_id) for task_id in unviewed_comments_qs)

    df_first_start, df_completed, df_last_completed = get_task_status_history_dataframes(
        paginated_task_ids_uuid
    )

    tet_df = get_task_execution_time_dataframe(
        paginated_task_ids_uuid, profile_ids, start_date=start_date, end_date=end_date
    )

    base = tasks_df.copy()

    base = base.merge(df_first_start, how="left", on="task_id")
    base = base.merge(df_completed, how="left", on="task_id")
    base = base.merge(df_last_completed, how="left", on="task_id")
    base = base.merge(tet_df, how="left", on="task_id")

    for column_name in ("hours_total_all", "hours_total_range", "duration_total_all", "duration_total_range"):
        if column_name in base.columns:
            base[column_name] = base[column_name].fillna(0)

    base["actual_duration_days"] = calculate_actual_duration(base)
    base["related_profile_ids"] = calculate_related_profile_ids(base, profile_ids)

    analytics_data_map = {}

    # Текущие (is_current=True) логи пользователя по задачам.
    # Одним запросом строим:
    # - current_timer_task_ids: наличие активного таймера
    # - current_log_created_at_map: created_at "первого" лога (минимальный pk),
    #   чтобы совпасть с tasks.utils.get_work_log_duration() где стоит .first() без ordering.
    current_timer_task_ids = set()
    current_log_created_at_map = {}
    current_logs_qs = (
        models.TaskExecutionTimeModel.objects.filter(
            task__in=tasks,
            is_active=True,
            is_current=True,
            user_id=profile_id,
        ).order_by("task_id", "pk").values("task_id", "created_at")
    )
    for item in current_logs_qs:
        task_id = item["task_id"]
        task_id_str = str(task_id)
        current_timer_task_ids.add(task_id_str)

        if task_id_str not in current_log_created_at_map:
            current_log_created_at_map[task_id_str] = item["created_at"]
    now = timezone.now()

    for _, row in base.iterrows():
        task_id = row["task_id"]
        actual_duration = float(row.get("actual_duration_days", 0))
        related_ids = row.get("related_profile_ids", [])

        # is_current: есть ли активный таймер для текущего пользователя
        is_current = task_id in current_timer_task_ids

        # duration_incomplete: секунды "незавершённого" лога (только если is_current=True)
        duration_incomplete = 0
        task_id_str = str(task_id)
        if is_current:
            created_at = current_log_created_at_map.get(task_id_str)
            if created_at:
                duration_incomplete = (now - created_at).seconds

        analytics_data_map[task_id] = {
            "hours_total_all": float(row.get("hours_total_all", 0)),
            "hours_total_range": float(row.get("hours_total_range", 0)),
            "duration_total_all": int(row.get("duration_total_all", 0)),
            "duration_total_range": int(row.get("duration_total_range", 0)),
            "actual_duration_days": actual_duration,
            "has_new_comments": task_id in tasks_with_unviewed_comments,
            "related_profile_ids": related_ids,
            "is_current": is_current,
            "duration_incomplete": duration_incomplete,
        }

    return analytics_data_map


def build_action_info_map(tasks, profile_id):
    project_ids = {task.project_id for task in tasks if task.project_id}
    moderated_project_ids = set()
    if project_ids:
        moderated_project_ids = set(
            WorkgroupMembersModel.objects.filter(
                is_active=True,
                member_id=profile_id,
                work_group_id__in=project_ids,
                membership_request_status__code='APPROVED',
                membership_role__code__in=('FOUNDER', 'MODERATOR'),
            ).values_list('work_group_id', flat=True)
        )

    return {
        str(task.id): {
            'edit': {
                'availability': (task.owner_id == profile_id) or (task.project_id in moderated_project_ids)
            }
        }
        for task in tasks
    }

