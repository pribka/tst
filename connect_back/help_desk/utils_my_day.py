import re
import datetime
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q, Sum, Value, IntegerField, Exists, OuterRef
from django.db.models.functions import Coalesce
from django.utils import timezone, dateparse
from change_history.models import ChangeHistoryModel
from . import models
from .utils import get_completed_statuses_id


def get_activity_ticket_ids(start, end, profile_ids=None):
    """
    Возвращает set ticket_ids из истории изменений за период.
    Использует кэширование на 60 секунд для оптимизации при одновременных запросах.
    
    Args:
        start: начальная дата/время (строка ISO или datetime)
        end: конечная дата/время (строка ISO или datetime)
        profile_ids: опциональный список ID профилей для фильтрации по автору
    
    Returns:
        set: множество ticket_ids
    """
    # Парсим start и end в datetime если они строки
    # parse_datetime может не работать с ISO строками с +, поэтому используем timezone-aware парсинг
    if isinstance(start, str):
        # Исправляем проблему с декодированием URL: знак + декодируется как пробел
        start_fixed = re.sub(r'\s(\d{2}:\d{2}(:\d{2}(\.\d+)?)?)$', r'+\1', start)
        start_dt = dateparse.parse_datetime(start_fixed)
        if not start_dt:
            return set()
        # Если parse_datetime вернул naive datetime, делаем его aware
        if start_dt and not timezone.is_aware(start_dt):
            start_dt = timezone.make_aware(start_dt)
    else:
        start_dt = start
    
    if isinstance(end, str):
        # Исправляем проблему с декодированием URL: знак + декодируется как пробел
        end_fixed = re.sub(r'\s(\d{2}:\d{2}(:\d{2}(\.\d+)?)?)$', r'+\1', end)
        end_dt = dateparse.parse_datetime(end_fixed)
        if not end_dt:
            return set()
        # Если parse_datetime вернул naive datetime, делаем его aware
        if end_dt and not timezone.is_aware(end_dt):
            end_dt = timezone.make_aware(end_dt)
    else:
        end_dt = end
    
    if not start_dt or not end_dt:
        return set()
    
    # Формируем ключ кэша
    cache_key_parts = ['my_day_activity_tickets', str(start_dt), str(end_dt)]
    if profile_ids:
        cache_key_parts.extend(sorted(str(pid) for pid in profile_ids))
    cache_key = '_'.join(cache_key_parts)
    
    # Проверяем кэш
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return set(cached_result)
    
    # Получаем ContentType для HelpDeskTicketModel
    ticket_ct = ContentType.objects.get_for_model(models.HelpDeskTicketModel)
    
    # Запрос к истории изменений
    hist_window_qs = (
        ChangeHistoryModel.objects
        .filter(
            is_active=True,
            related_object__ct=ticket_ct,
            action_date__gte=start_dt,
            action_date__lt=end_dt,
        )
    )
    
    # Если передан profile_ids, фильтруем по автору
    if profile_ids:
        hist_window_qs = hist_window_qs.filter(author_id__in=profile_ids)
    
    hist_window_qs = hist_window_qs.only("id", "related_object_id")
    ticket_ids = set(hist_window_qs.values_list("related_object_id", flat=True).distinct())
    
    # Сохраняем в кэш на 10 секунд
    cache.set(cache_key, list(ticket_ids), timeout=10)
    
    return ticket_ids


def get_my_day_tickets_queryset(request):
    """QuerySet обращений для вкладки "Мой день"."""
    from common.utils import get_datetime_param
    from help_desk.views import HelpDeskTicketViewSet

    group_param = request.query_params.get('group')
    role_filter = request.query_params.get('role')
    profile_param = request.query_params.get('user')
    id_param = request.query_params.get('id')

    help_desk_viewset = HelpDeskTicketViewSet()
    help_desk_viewset.setup(request)
    base_qs = help_desk_viewset.get_tickets_queryset(request)

    # Если явно передан id тикета — работаем только с ним, без выборки по истории и без фильтра по ролям
    if id_param:
        return base_qs.filter(pk=id_param)

    start = get_datetime_param(request, 'start')
    end = get_datetime_param(request, 'end')

    profile_id = str(request.user.profile.pk)

    if profile_param:
        profile_ids = profile_param.split(',')
    else:
        profile_ids = [profile_id]

    # Только тикеты, где profile_ids — ответственные или авторы
    base_qs = base_qs.filter(
        Q(specialist_id__in=profile_ids) | Q(author_id__in=profile_ids)
    )

    if not start and not end:
        current_date = timezone.localdate()
        start_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.min))
        end_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.max))
        start = start_of_day.isoformat()
        end = end_of_day.isoformat()

    activity_ticket_ids = get_activity_ticket_ids(start, end, profile_ids=profile_ids)

    completed_statuses = get_completed_statuses_id()

    if not activity_ticket_ids:
        base_qs = base_qs.exclude(status_id__in=completed_statuses).distinct()
    else:
        lookup = Q(pk__in=activity_ticket_ids) | ~Q(status_id__in=completed_statuses)
        base_qs = base_qs.filter(lookup).distinct()

    if group_param == 'activity':
        if not activity_ticket_ids:
            return base_qs.model.objects.none()
        base_qs = base_qs.filter(pk__in=activity_ticket_ids).distinct()
    elif group_param == 'other':
        base_qs = base_qs.exclude(pk__in=activity_ticket_ids).distinct()

    if role_filter == 'is_operator':
        base_qs = base_qs.filter(specialist_id__in=profile_ids)
    elif role_filter == 'is_owner':
        base_qs = base_qs.filter(author_id__in=profile_ids)

    return base_qs


def build_my_day_ticket_analytics(ticket_ids, request, start_date=None, end_date=None):
    """
    Строит analytics_data_map для 'Моего дня' по списку id тикетов.

    Args:
        ticket_ids: список id тикетов
        request: объект request для получения текущего пользователя
        start_date: начальная дата для диапазона трудозатрат (date объект)
        end_date: конечная дата для диапазона трудозатрат (date объект)

    Returns:
        dict: {ticket_id: {...}} для передачи в HelpDeskTicketMyDaySerializer через analytics_data_map
    """
    ticket_ids = list(ticket_ids)
    if not ticket_ids:
        return {}

    ticket_data_qs = models.HelpDeskTicketModel.objects.filter(
        pk__in=ticket_ids,
        is_active=True,
    ).values(
        'id',
        'start_date',
        'end_date',
        'duration',
    )
    ticket_data_map = {
        str(item['id']): item
        for item in ticket_data_qs
    }

    user = request.user.profile

    # Получаем duration_total_range для всех тикетов за период одним запросом
    zero_int = Value(0, output_field=IntegerField())
    
    work_log_qs = (
        models.HelpDeskWorkLogModel.objects
        .filter(
            is_active=True,
            ticket_id__in=ticket_ids,
            is_current=False
        )
    )
    
    if start_date and end_date:
        work_log_qs = work_log_qs.filter(
            date__gte=start_date,
            date__lte=end_date
        )
    
    duration_range_data = (
        work_log_qs
        .values("ticket_id")
        .annotate(
            duration_total_range=Coalesce(
                Sum("duration", output_field=IntegerField()),
                zero_int
            )
        )
    )
    
    duration_range_map = {
        str(item["ticket_id"]): int(item["duration_total_range"])
        for item in duration_range_data
    }
    
    # Текущие (is_current=True) логи пользователя по тикетам.
    # Одним запросом строим:
    # - current_timer_ticket_ids: наличие активного таймера
    # - current_log_created_at_map: created_at "первого" лога (минимальный pk),
    #   чтобы совпасть с help_desk.utils.get_work_log_duration() где стоит .first() без ordering.
    current_timer_ticket_ids = set()
    current_log_created_at_map = {}
    current_logs_qs = (
        models.HelpDeskWorkLogModel.objects
        .filter(
            ticket_id__in=ticket_ids,
            is_active=True,
            is_current=True,
            user_id=user.pk,
        )
        .order_by("ticket_id", "pk")
        .values("ticket_id", "created_at")
    )
    for item in current_logs_qs:
        ticket_id = item["ticket_id"]
        current_timer_ticket_ids.add(ticket_id)
        ticket_id_str = str(ticket_id)
        if ticket_id_str not in current_log_created_at_map:
            current_log_created_at_map[ticket_id_str] = item["created_at"]
    
    # Формируем analytics_data_map
    analytics_data_map = {}
    now = timezone.now()
    
    for ticket_id in ticket_ids:
        ticket_id_str = str(ticket_id)
        ticket_data = ticket_data_map.get(ticket_id_str, {})
        ticket_start_date = ticket_data.get('start_date')
        ticket_end_date = ticket_data.get('end_date')
        ticket_duration = ticket_data.get('duration')
        
        # actual_duration_days: от start_date до end_date или до now
        actual_duration_days = None
        if ticket_start_date:
            if ticket_end_date:
                # Тикет завершен
                delta = ticket_end_date - ticket_start_date
                actual_duration_days = max(0, int(delta.total_seconds() / 86400))
            else:
                # Тикет не завершен
                delta = now - ticket_start_date
                actual_duration_days = max(0, int(delta.total_seconds() / 86400))
        else:
            actual_duration_days = 0
        
        # duration_total_all: уже есть в ticket.duration (в секундах)
        duration_total_all = ticket_duration or 0
        
        # duration_total_range: из запроса выше
        duration_total_range = duration_range_map.get(ticket_id_str, 0)
        
        # is_current: есть ли активный таймер для текущего пользователя
        is_current = ticket_id in current_timer_ticket_ids

        # duration_incomplete: секунды "незавершённого" лога (только если is_current=True)
        duration_incomplete = 0
        if is_current:
            created_at = current_log_created_at_map.get(ticket_id_str)
            if created_at:
                duration_incomplete = (now - created_at).seconds
        
        analytics_data_map[ticket_id_str] = {
            "actual_duration_days": actual_duration_days,
            "duration_total_all": duration_total_all,
            "duration_total_range": duration_total_range,
            "is_current": is_current,
            "duration_incomplete": duration_incomplete,
        }
    
    return analytics_data_map
