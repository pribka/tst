"""
Анализ собранных данных за день (задачи, встречи, календарь, хелпдеск, чаты) в разрезе организации/проекта/команды/пользователя.
Чанки → LLM по ролям → сохранение в ActivityDigestModel.
"""

import json
import time
from datetime import date, timedelta
from typing import Any, List, Optional, Tuple

from django.db import connection
from django.utils import timezone
from django_q.tasks import async_task

from analytics.models import (
    ActivityDigestModel,
    DIGEST_SOURCE_KEYS,
    ActivitySummaryModel,
)
from analytics.notifications import send_notify_about_activity_summary_ready
from analytics.utils.collect_data import collect_digests_for_period
from analytics.utils.collect_data import (
    _collect_events,
    _collect_chats,
    _collect_helpdesk_tickets,
    _collect_meeting_summaries,
    _collect_tasks,
    _collect_day_summaries,
)

from bpms.chat_ai.utils.messages import invoke_role_prompt
from bpms.workgroups.models import WorkgroupModel
from common.catalogs.models import ContractorModel
from users.models import ProfileModel


# Источник данных → функция сбора данных (related_object_id, scope_type, date_from, date_to)
SOURCE_COLLECTORS = {
    "tasks": _collect_tasks,
    "meetings": _collect_meeting_summaries,
    "events": _collect_events,
    "helpdesk": _collect_helpdesk_tickets,
    "chats": _collect_chats,
    "day_summary": _collect_day_summaries,
}


def collect_raw_activity_context(
    related_object_id,
    scope_type: str,
    date_from: date,
    date_to: date,
    sources: Optional[List[str]] = None,
) -> dict:
    """
    Собирает сырые подготовленные данные за период по заданным источникам и охвату (до передачи в LLM).
    То же, что передаётся в LLM по дням в analyze_activity_for_day, но за весь период сразу.

    :param related_object_id: pk объекта среза (UUID).
    :param scope_type: "organization" | "project" | "workgroup" | "user".
    :param date_from: начало периода (date).
    :param date_to: конец периода (date).
    :param sources: список источников — "tasks" | "meetings" | "events" | "helpdesk" | "chats"; по умолчанию ["tasks"].
    :return: dict с ключами по источникам, значения — списки сырых данных (как в collect_organization_activity_context).
    """
    if sources is None:
        sources = ["tasks"]
    result = {}
    for source in sources:
        if source not in SOURCE_COLLECTORS:
            continue
        collector = SOURCE_COLLECTORS[source]
        result[source] = collector(
            related_object_id,
            scope_type,
            date_from,
            date_to,
        )
    return result


# Роль для анализа периода по охвату (собранные дайджесты за неделю и т.д.)
SCOPE_ANALYZE_ROLE = {
    "organization": "analyze_organization",
    "project": "analyze_project",
    "workgroup": "analyze_workgroup",
    "user": "analyze_user",
    "user_day_summary": "analyze_user_day_summary",
}

# Роли: (scope_type, subject) → (role_chunk, role_combine). Готовые только organization_tasks.
def _role_codes(scope_type: str, subject: str) -> Tuple[str, str]:
    base = f"{scope_type}_{subject}_summary"
    return base, f"{base}_combine"


def build_json_list_chunks(
    items: List[Any],
    max_llm_chars: int = 60000,
) -> List[str]:
    """
    Делит список верхнеуровневых элементов на чанки JSON-массивов по лимиту символов.
    На вход — любой список (задачи, встречи и т.д.); отбирает столько элементов,
    сколько помещается в max_llm_chars. Каждый чанк — валидный JSON-массив.
    """
    if not items:
        return []

    chunks: List[List[Any]] = []
    current: List[Any] = []
    current_len = 0

    for item in items:
        item_len = len(json.dumps(item, ensure_ascii=False))
        if current_len + item_len > max_llm_chars and current:
            chunks.append(current)
            current = [item]
            current_len = item_len
        else:
            current.append(item)
            current_len += item_len

    if current:
        chunks.append(current)

    return [json.dumps(chunk, ensure_ascii=False) for chunk in chunks]


def analyze_activity_for_day(
    target_date: date,
    subject: str,
    related_object_id,
    scope_type: str,
) -> Optional[ActivityDigestModel]:
    """
    Универсальный анализ активности за один день.

    :param target_date: дата (обязательно).
    :param subject: что анализируем — "tasks" | "meetings" | "events" | "helpdesk" | "chats".
    :param related_object_id: pk объекта среза (UUID).
    :param scope_type: "organization" | "project" | "workgroup" | "user".
    :return: ActivityDigestModel (update_or_create по related_object_id + date + source), либо None при ошибке.
    """
    role_chunk, role_combine = _role_codes(scope_type, subject)
    collector = SOURCE_COLLECTORS[subject]

    print(f"analyze_activity_for_day: scope={scope_type}, subject={subject}, date={target_date.isoformat()}")

    items = collector(
        related_object_id,
        scope_type,
        target_date,
        target_date,
    )

    context = {
        "date_from": target_date.isoformat(),
        "date_to": target_date.isoformat(),
    }
    if scope_type == "organization":
        org = ContractorModel.objects.filter(pk=related_object_id).first()
        context["organization_name"] = org.name
    elif scope_type == "project":
        wg = WorkgroupModel.objects.filter(pk=related_object_id).first()
        context["project_name"] = wg.name
    elif scope_type == "workgroup":
        wg = WorkgroupModel.objects.filter(pk=related_object_id).first()
        context["workgroup_name"] = wg.name
    elif scope_type in ("user", "user_day_summary"):
        profile = ProfileModel.objects.filter(pk=related_object_id).first()
        context["user_name"] = profile.full_name

    chunks = build_json_list_chunks(items, max_llm_chars=30000)
    print(f"  items: {len(items)}, chunks: {len(chunks)}")
    summaries: List[str] = []

    for idx, chunk_str in enumerate(chunks):
        if not chunk_str:
            continue
        print(f"  chunk {idx + 1}/{len(chunks)}")
        raw = invoke_role_prompt(
            user_message=chunk_str,
            role_code=role_chunk,
            context=context,
            consumer=None,
            format_schema=None,
            url_query_param=f"digest&scope={scope_type}&subject={subject}&date={target_date.isoformat()}",
        )
        part = (str(raw).strip() if raw else "")
        if part:
            summaries.append(part)

    if not summaries:
        final_text = ""
    elif len(summaries) == 1:
        final_text = summaries[0]
    else:
        print(f"  combining {len(summaries)} partial results")
        combined_user_message = "\n".join([f"- {item}" for item in summaries])
        combined_raw = invoke_role_prompt(
            user_message=combined_user_message,
            role_code=role_combine,
            context=context,
            consumer=None,
            format_schema=None,
            url_query_param=f"digest_combine&scope={scope_type}&subject={subject}&date={target_date.isoformat()}",
        )
        final_text = (str(combined_raw).strip() if combined_raw else "\n\n".join(summaries))

    digest, created = ActivityDigestModel.objects.update_or_create(
        related_object_id=related_object_id,
        date=target_date,
        scope=scope_type,
        source=subject,
        defaults={"summary": final_text},
    )
    print(f"  saved digest ({'created' if created else 'updated'}, source={subject})")
    return digest


def create_digest_data(
    start,
    end,
    related_object_id,
    scope_type: str,
    sources=None,
):
    """
    Создаёт дайджесты за период [start, end] включительно по заданным источникам и охвату.

    :param start: начало периода (date или datetime — берётся дата).
    :param end: конец периода (date или datetime).
    :param related_object_id: pk объекта среза (UUID).
    :param scope_type: "organization" | "project" | "workgroup" | "user".
    :param sources: список источников — "tasks" | "meetings" | "events" | "helpdesk" | "chats"; по умолчанию ["tasks"].
    """
    if sources is None:
        sources = ["tasks"]
    current = start
    while current <= end:
        for source in sources:
            analyze_activity_for_day(
                target_date=current,
                subject=source,
                related_object_id=related_object_id,
                scope_type=scope_type,
            )
        current += timedelta(days=1)


def get_missing_digest_pairs(
    related_object_id,
    date_from: date,
    date_to: date,
    sources: Optional[List[str]] = None,
    scope: Optional[str] = None,
) -> List[Tuple[date, str]]:
    """
    Возвращает список пар (дата, источник), для которых дайджест отсутствует или устарел.
    Для даты == date.today() пары всегда включаются (перегенерация за сегодня).
    Для диапазона из одного дня (date_from == date_to) пары также всегда включаются.
    scope обязателен (organization | project | workgroup | user | user_day_summary).
    """
    if date_from is None or date_to is None or date_from > date_to:
        return []
    if not scope:
        return []
    source_keys = (
        [s for s in (sources or []) if s in DIGEST_SOURCE_KEYS]
        or list(DIGEST_SOURCE_KEYS)
    )
    today = date.today()
    is_single_day_range = date_from == date_to

    needed = set()
    current = date_from
    while current <= date_to:
        for src in source_keys:
            needed.add((current, src))
        current += timedelta(days=1)

    ready = set()
    qs = ActivityDigestModel.objects.filter(
        related_object_id=related_object_id,
        date__gte=date_from,
        date__lte=date_to,
        scope=scope,
    )
    for row in qs:
        if row.date == today or is_single_day_range:
            continue
        ready.add((row.date, row.source))

    missing = needed - ready
    return sorted(missing, key=lambda pair: (pair[0], pair[1]))


def analyze_digest_period(collected, scope_type, date_from, date_to):
    """
    Анализирует собранные за период дайджесты через LLM (два шага: основной анализ по чанкам, при необходимости — склейка).
    Принимает результат collect_data.collect_digests_for_period: список [{"day": "...", "sources": {...}}, ...].

    :param collected: список по дням из collect_digests_for_period.
    :param scope_type: "organization" | "project" | "workgroup" | "user".
    :param date_from: начало периода (date).
    :param date_to: конец периода (date).
    :return: текст ответа LLM.
    """
    role_code = SCOPE_ANALYZE_ROLE.get(scope_type)
    role_combine = f"{role_code}_combine"
    context = {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }

    if not collected:
        return ""

    chunks = build_json_list_chunks(collected, max_llm_chars=60000)
    print(f"analyze_digest_period: scope={scope_type}, days={len(collected)}, chunks={len(chunks)}")
    summaries: List[str] = []

    for idx, chunk_str in enumerate(chunks):
        if not chunk_str:
            continue
        print(f"  chunk {idx + 1}/{len(chunks)}")
        raw = invoke_role_prompt(
            user_message=chunk_str,
            role_code=role_code,
            context=context,
            consumer=None,
            format_schema=None,
            url_query_param=f"analyze_period&scope={scope_type}",
        )
        part = (str(raw).strip() if raw else "")
        if part:
            summaries.append(part)

    if not summaries:
        return ""
    if len(summaries) == 1:
        return summaries[0]
    print(f"  combining {len(summaries)} partial results")
    combined_user_message = "\n".join([f"- {item}" for item in summaries])
    combined_raw = invoke_role_prompt(
        user_message=combined_user_message,
        role_code=role_combine,
        context=context,
        consumer=None,
        format_schema=None,
        url_query_param=f"analyze_period_combine&scope={scope_type}",
    )
    return (str(combined_raw).strip() if combined_raw else "\n\n".join(summaries))


def generate_activity_summary(activity_summary_pk: str, scope: Optional[str] = None) -> None:
    """
    Генерация саммари по ActivitySummaryModel.
    Собирает дайджесты за период, прогоняет их через LLM и сохраняет результат.
    Вызывается из task_klass (очередь). scope обязателен в самой модели.
    """
    try:
        summary_obj = ActivitySummaryModel.objects.get(pk=activity_summary_pk, is_active=True)
    except ActivitySummaryModel.DoesNotExist:
        return

    scope_type = summary_obj.scope

    try:
        sources = [s.strip() for s in (summary_obj.sources or "").split(",") if s.strip()]
        sources_list = sources if sources else None
        missing_pairs = get_missing_digest_pairs(
            related_object_id=summary_obj.related_object_id,
            date_from=summary_obj.start_date,
            date_to=summary_obj.end_date,
            sources=sources_list,
            scope=scope_type,
        )
        for target_date, source in missing_pairs:
            analyze_activity_for_day(
                target_date=target_date,
                subject=source,
                related_object_id=summary_obj.related_object_id,
                scope_type=scope_type,
            )

        context_list = collect_digests_for_period(
            date_from=summary_obj.start_date,
            date_to=summary_obj.end_date,
            related_object=str(summary_obj.related_object_id),
            sources=sources_list,
            scope=scope_type,
        )

        analysis = analyze_digest_period(
            collected=context_list,
            scope_type=scope_type,
            date_from=summary_obj.start_date,
            date_to=summary_obj.end_date,
        )

        summary_obj.summary = analysis or ""
        summary_obj.status = "completed"
        summary_obj.error_message = ""
        summary_obj.completed_at = timezone.now()
        summary_obj.save(update_fields=["summary", "status", "error_message", "completed_at"])
        if scope_type != "user_day_summary":
            async_task(send_notify_about_activity_summary_ready, activity_summary_pk)
    except Exception as exc:
        summary_obj.status = "failed"
        summary_obj.error_message = str(exc)
        summary_obj.completed_at = timezone.now()
        summary_obj.save(update_fields=["status", "error_message", "completed_at"])


# Очередь саммари: один процесс за раз (cron может запускать task_klass каждую минуту)
ADVISORY_LOCK_ID_ACTIVITY_SUMMARY = 0x0A170001


def process_activity_summary_queue() -> None:
    """
    Обрабатывает все pending ActivitySummaryModel из очереди.
    pg_try_advisory_lock гарантирует, что только один экземпляр в момент времени
    выполняет эту джобу.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [ADVISORY_LOCK_ID_ACTIVITY_SUMMARY])
        row = cursor.fetchone()
        if not row or not row[0]:
            return
        try:
            summaries = (
                ActivitySummaryModel.objects.filter(
                    status="pending",
                    is_active=True,
                )
                .order_by("created_at")
                .values_list("pk", flat=True)
            )
            for summary_pk in summaries:
                generate_activity_summary(str(summary_pk))
        finally:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [ADVISORY_LOCK_ID_ACTIVITY_SUMMARY])
