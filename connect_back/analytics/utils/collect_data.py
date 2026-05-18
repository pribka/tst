"""
Сбор контекста по деятельности организации за период для последующей передачи в LLM.
Данные берутся из bpms (проекты, команды, задачи, собрания, календарь), без собственных моделей analytics.
"""

import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import ROUND_UP, Decimal
from uuid import UUID

from django.db.models import Q
from django.utils.functional import Promise

from bpms.comments.models import CommentModel
from bpms.comments.serializers import CommentListSerializer
from bpms.event_calendar.models import CalendarModel, EventCalendarModel
from bpms.meetings.models import MeetingRecordsModel, MeetingSectionModel, MeetingSectionMemberModel
from bpms.tasks.models import TaskExecutionTimeModel, TaskModel
from bpms.tasks.serializers import TaskExecutionTimeModelListSerializer
from bpms.workgroups.models import WorkgroupMembersModel, WorkgroupModel
from bpms.day_summary.models import DaySummaryNoteModel

from common.catalogs.models import ContractorProfileModel

from bpms.chat import models as chat_models
from bpms.chat import serializers as chat_serializers
from help_desk.models import ContactPersonMessageModel, HelpDeskTicketModel, HelpDeskWorkLogModel
from users.utils import get_descendants_departments_related_organizations


# ---- Локальные копии утилит для компактного контекста (не импортируем из bpms.chat) ----

_HTML_RE = re.compile(r"<[^>]+>")


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    if "<" in text and ">" in text:
        text = _HTML_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def person_to_name(person):
    """Extract person name from serializer data."""
    if not person:
        return None
    if isinstance(person, str):
        return person
    return person.get("full_name") or person.get("short_name")


def get_task_comments(task_id, date_from, date_to):
    """Get comments for a task за [date_from, date_to], по возрастанию даты."""
    qs = (
        CommentModel.objects
        .select_related(
            "parent",
        )
        .prefetch_related(
            "attachments__mime_type__file_type",
            "parent__attachments__mime_type__file_type",
        )
        .filter(
            related_object_id=task_id,
            is_active=True,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .order_by("created_at")
    )
    return CommentListSerializer(qs, many=True).data


def get_task_execution_times(task_id, date_from, date_to):
    """Get execution times for a task за [date_from, date_to], по возрастанию даты."""
    qs = (
        TaskExecutionTimeModel.objects
        .filter(
            task_id=task_id,
            is_active=True,
            date__gte=date_from,
            date__lte=date_to,
        )
        .select_related(
            "measure_unit",
            "work_type",
            "event_calendar",
            "meeting_section",
        )
        .order_by("date")
    )
    return TaskExecutionTimeModelListSerializer(qs, many=True).data


def get_ticket_comments(ticket_id, date_from, date_to):
    """Комментарии по обращению в техподдержку за [date_from, date_to], по возрастанию даты."""
    qs = (
        CommentModel.objects
        .select_related(
            "author__user",
            "parent__author__user",
            "author__avatar",
            "parent__author__avatar",
        )
        .prefetch_related(
            "attachments__mime_type__file_type",
            "parent__attachments__mime_type__file_type",
        )
        .filter(
            related_object_id=ticket_id,
            is_active=True,
            # created_at__date__gte=date_from,
            # created_at__date__lte=date_to,
        )
        .order_by("created_at")
    )
    return CommentListSerializer(qs, many=True).data


def compact_comments(comments: list) -> list:
    """Compact comment data for LLM."""
    out = []
    for c in comments or []:
        c_text = c.get("text") or c.get("comment") or c.get("message") or ""
        out.append({
            "author": person_to_name(c.get("author")),
            "created": c.get("created_at") or c.get("created") or c.get("date"),
            "text": clean_html(c_text),
        })
    return [x for x in out if x.get("text") or x.get("author")]


def compact_execution_times(times: list) -> list:
    """Compact execution time data for LLM."""
    out = []
    for t in times or []:
        wt = t.get("work_type")
        work_type_name = wt.get("name") if isinstance(wt, dict) else wt

        desc = t.get("description") or ""
        out.append({
            "user": person_to_name(t.get("user") or t.get("author")),
            "work_type": work_type_name,
            "hours": t.get("hours"),
            "date": t.get("date"),
            "description": clean_html(desc),
        })
    return [x for x in out if x.get("description") or x.get("hours")]


def _compact_ticket_message(message):
    """Один элемент переписки по обращению для контекста LLM."""
    author = None
    if getattr(message, "is_help_desk", False):
        author = _profile_display_name(getattr(message, "author", None))
    else:
        contact_person = getattr(message, "contact_person", None)
        if contact_person:
            author = _profile_display_name(getattr(contact_person, "user", None)) or getattr(contact_person, "name", None) or str(message.contact_person_id)
    return {
        "date": _normalize_for_json(getattr(message, "message_date", None)),
        "author": author,
        "text": clean_html(getattr(message, "text", None) or ""),
    }


# ---- Контекст организации ----

def _normalize_for_json(value):
    """Приведение значений к JSON-сериализуемому виду (для LLM). Даты — только YYYY-MM-DD, без времени и таймзоны."""
    if isinstance(value, Promise):
        return str(value)
    if isinstance(value, datetime):
        return value.date().isoformat() if value else None
    if isinstance(value, date):
        return value.isoformat() if value else None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_for_json(v) for v in value]
    return value


def _profile_display_name(profile):
    """Краткое отображение профиля для контекста."""
    if not profile:
        return None
    return getattr(profile, "full_name", None) or getattr(profile, "short_name", None) or str(profile.pk)


def _task_is_overdue(task):
    """Задача просрочена: не завершена и крайний срок уже прошёл."""
    if task.finished_date:
        return False
    if not task.dead_line:
        return False
    deadline_date = task.dead_line.date() if hasattr(task.dead_line, "date") else task.dead_line
    return deadline_date < date.today()


def _collect_projects(organization_id, date_from, date_to, project_id=None, workgroup_id=None, user_id=None):
    """
    Проекты организации: дата начала, крайний срок, участники. Список задач не включаем — он есть в самих задачах.
    Если передан project_id — только этот проект.
    """
    qs = (
        WorkgroupModel.objects
        .filter(
            organization_id=organization_id,
            is_project=True,
            is_active=True,
        )
    )
    if project_id is not None:
        qs = qs.filter(pk=project_id)
    qs = (
        qs
        .select_related("author")
        .prefetch_related("workgroupmembersmodel_set__member")
    )
    out = []
    for workgroup in qs:
        members = list(
            WorkgroupMembersModel.objects
            .filter(
                work_group=workgroup,
                is_active=True,
                membership_request_status__code="APPROVED",
            )
            .select_related("member")
        )
        out.append({
            "id": str(workgroup.pk),
            "name": workgroup.name,
            "date_start": _normalize_for_json(workgroup.date_start_plan),
            "dead_line": _normalize_for_json(workgroup.dead_line),
            "participants": [_profile_display_name(m.member) for m in members],
        })
    return out


def _collect_workgroups(organization_id, date_from, date_to, project_id=None, workgroup_id=None, user_id=None):
    """
    Команды организации: дата начала, крайний срок, участники. Список задач не включаем — он есть в самих задачах.
    Если передан workgroup_id — только эта команда.
    """
    qs = (
        WorkgroupModel.objects
        .filter(
            organization_id=organization_id,
            is_project=False,
            is_active=True,
        )
    )
    if workgroup_id is not None:
        qs = qs.filter(pk=workgroup_id)
    qs = (
        qs
        .select_related("author")
        .prefetch_related("workgroupmembersmodel_set__member")
    )
    out = []
    for workgroup in qs:
        members = list(
            WorkgroupMembersModel.objects
            .filter(
                work_group=workgroup,
                is_active=True,
                membership_request_status__code="APPROVED",
            )
            .select_related("member")
        )
        out.append({
            "id": str(workgroup.pk),
            "name": workgroup.name,
            "date_start": _normalize_for_json(workgroup.date_start_plan),
            "dead_line": _normalize_for_json(workgroup.dead_line),
            "participants": [_profile_display_name(m.member) for m in members],
        })
    return out


def _get_base_task_qs(related_object_id, scope_type, date_from):
    """Базовый queryset задач в рамках scope, с отсечением задач, завершённых до начала периода."""
    base_task_filters = {}
    # TODO На будущее: разделить анализ всей организации с подразделениями и только одного подразделения.
    # if scope_type == "organization":
    #     organization_ids = get_descendants_departments_related_organizations([related_object_id], include_self=True)
    #     base_task_filters["organization_id__in"] = organization_ids
    # elif scope_type == "structural_division":
    if scope_type == "organization":
        base_task_filters["organization_id"] = related_object_id
    elif scope_type == "structural_division":
        base_task_filters["organization_id"] = related_object_id
    elif scope_type == "project":
        base_task_filters["project_id"] = related_object_id
    elif scope_type == "workgroup":
        base_task_filters["workgroup_id"] = related_object_id
    elif scope_type == "contract":
        base_task_filters["contract_id"] = related_object_id
    elif scope_type in ("user", "user_day_summary"):
        base_task_filters["operator_id"] = related_object_id
    return (
        TaskModel.objects
        .filter(is_active=True, task_type__code="task", **base_task_filters)
        .exclude(finished_date__lt=date_from)
    )


def _get_comments_base_qs(related_object_id, scope_type, date_from, date_to):
    """
    Базовый queryset комментариев в рамках scope и периода.
    Без доп. уточнений по finished_date задачи — это делает вызывающий код при необходимости.
    """
    comments_task_filters = {
        "is_active": True,
        "created_at__date__gte": date_from,
        "created_at__date__lte": date_to,
    }
    # TODO На будущее: разделить анализ всей организации с подразделениями и только одного подразделения.
    # if scope_type == "organization":
    #     organization_ids = get_descendants_departments_related_organizations([related_object_id], include_self=True)
    #     comments_task_filters["related_object__taskmodel__organization_id__in"] = organization_ids
    # elif scope_type == "structural_division":
    if scope_type == "organization":
        comments_task_filters["related_object__taskmodel__organization_id"] = related_object_id
    elif scope_type == "structural_division":
        comments_task_filters["related_object__taskmodel__organization_id"] = related_object_id
    elif scope_type == "project":
        comments_task_filters["related_object__taskmodel__project_id"] = related_object_id
    elif scope_type == "workgroup":
        comments_task_filters["related_object__taskmodel__workgroup_id"] = related_object_id
    elif scope_type == "contract":
        comments_task_filters["related_object__taskmodel__contract_id"] = related_object_id
    elif scope_type in ("user", "user_day_summary"):
        comments_task_filters["author_id"] = related_object_id
    return CommentModel.objects.filter(**comments_task_filters)


def _get_execution_base_qs(related_object_id, scope_type, date_from, date_to):
    """
    Базовый queryset трудозатрат в рамках scope и периода.
    Без доп. уточнений по finished_date задачи — это делает вызывающий код при необходимости.
    """
    execution_task_filters = {
        "is_active": True,
        "date__gte": date_from,
        "date__lte": date_to,
    }
    # TODO На будущее: разделить анализ всей организации с подразделениями и только одного подразделения.
    # if scope_type == "organization":
    #     organization_ids = get_descendants_departments_related_organizations([related_object_id], include_self=True)
    #     execution_task_filters["task__organization_id__in"] = organization_ids
    # elif scope_type == "structural_division":
    if scope_type == "organization":
        execution_task_filters["task__organization_id"] = related_object_id
    elif scope_type == "structural_division":
        execution_task_filters["task__organization_id"] = related_object_id
    elif scope_type == "project":
        execution_task_filters["task__project_id"] = related_object_id
    elif scope_type == "workgroup":
        execution_task_filters["task__workgroup_id"] = related_object_id
    elif scope_type == "contract":
        execution_task_filters["task__contract_id"] = related_object_id
    elif scope_type in ("user", "user_day_summary"):
        execution_task_filters["user_id"] = related_object_id
    return TaskExecutionTimeModel.objects.filter(**execution_task_filters)


def _collect_tasks(related_object_id, scope_type, date_from, date_to):
    """
    Задачи для контекста аналитики.
    Охват: related_object_id + scope_type
    (organization | structural_division | project | workgroup | contract | user | user_day_summary).
    Для user/user_day_summary — задачи, где пользователь проявил активность (комменты, трудозатраты),
    а также незакрытые/актуальные задачи из его базового скоупа.
    """
    base_task_qs = _get_base_task_qs(
        related_object_id=related_object_id,
        scope_type=scope_type,
        date_from=date_from,
    )
    comments_finished_before_filters = {
        "related_object__taskmodel__finished_date__lt": date_from,
    }
    execution_finished_before_filters = {
        "task__finished_date__lt": date_from,
    }
    comments_base_qs = (
        _get_comments_base_qs(
            related_object_id=related_object_id,
            scope_type=scope_type,
            date_from=date_from,
            date_to=date_to,
        )
        .exclude(**comments_finished_before_filters)
    )
    execution_base_qs = (
        _get_execution_base_qs(
            related_object_id=related_object_id,
            scope_type=scope_type,
            date_from=date_from,
            date_to=date_to,
        )
        .exclude(**execution_finished_before_filters)
    )

    task_ids_with_comments = set(
        comments_base_qs
        .values_list("related_object_id", flat=True)
        .distinct()
    )
    task_ids_with_execution = set(
        execution_base_qs
        .values_list("task_id", flat=True)
        .distinct()
    )
    task_ids = task_ids_with_comments | task_ids_with_execution
    if not task_ids:
        return []
    filtered_task_qs = base_task_qs.filter(pk__in=task_ids)

    comments_qs = (
        comments_base_qs
        .select_related(
            "author__user",
            "parent__author__user",
            "author__avatar",
            "parent__author__avatar",
        )
        .prefetch_related(
            "attachments__mime_type__file_type",
            "parent__attachments__mime_type__file_type",
        )
        .order_by("created_at")
    )
    comments_by_task = defaultdict(list)
    for comment in comments_qs:
        comments_by_task[comment.related_object_id].append(comment)

    execution_qs = (
        execution_base_qs
        .select_related(
            "measure_unit",
            "work_type",
            "event_calendar",
            "meeting_section",
        )
        .order_by("date")
    )
    execution_by_task = defaultdict(list)
    for execution in execution_qs:
        execution_by_task[execution.task_id].append(execution)

    tasks_qs = (
        filtered_task_qs
        .select_related("status", "owner", "operator", "project", "workgroup")
        .prefetch_related("object_tags")
        .order_by("-created_at")
    )
    out = []
    for task in tasks_qs:
        comments_data = CommentListSerializer(comments_by_task.get(task.pk, []), many=True).data
        execution_data = TaskExecutionTimeModelListSerializer(execution_by_task.get(task.pk, []), many=True).data
        comments_compact = compact_comments(comments_data)
        execution_compact = compact_execution_times(execution_data)
        out.append({
            "counter": getattr(task, "counter", None) or str(task.pk),
            "name": task.name,
            "status": getattr(task.status, "name", None) if task.status else None,
            "owner": _profile_display_name(task.owner),
            "operator": _profile_display_name(task.operator),
            "dead_line": _normalize_for_json(task.dead_line),
            "project": (
                {
                    "id": str(task.project.pk),
                    "name": task.project.name,
                    "dead_line": _normalize_for_json(getattr(task.project, "dead_line", None)),
                }
                if task.project else None
            ),
            "workgroup": (
                {
                    "id": str(task.workgroup.pk),
                    "name": task.workgroup.name
                    }
                if task.workgroup else None
            ),
            "blockers": [tag.name for tag in task.object_tags.all()],
            "is_overdue": _task_is_overdue(task),
            "execution_times": execution_compact,
            "comments": comments_compact,
        })
    return out


def _collect_meeting_summaries(related_object_id, scope_type, date_from, date_to):
    """
    Секции собраний по участникам. Охват: related_object_id + scope_type.
    - organization: секции, в которых участвовали участники организации (contractor_id).
    - project / workgroup: секции, где участники — члены проекта/команды (work_group_id).
    - user / user_day_summary: секции, где участник — related_object_id (profile).
    Собираем: данные секции, имена и продолжительность участия, meeting.project (если есть),
    summary видеозаписей секции (если есть записи).
    """
    sections_qs = (
        MeetingSectionModel.objects
        .filter(
            is_active=True,
            date_start__date__gte=date_from,
            date_start__date__lte=date_to,
        )
        .select_related("meeting", "meeting__project")
        .prefetch_related(
            "meeting_section_members__user",
        )
        .order_by("date_start")
    )

    if scope_type == "organization":
        org_member_ids = ContractorProfileModel.objects.filter(
            contractor_id=related_object_id,
            is_active=True,
        ).values_list("user_id", flat=True)
        sections_qs = sections_qs.filter(
            meeting_section_members__user_id__in=org_member_ids,
        ).distinct()
    elif scope_type in ("project", "workgroup"):
        wg_member_ids = WorkgroupMembersModel.objects.filter(
            work_group_id=related_object_id,
            is_active=True,
            membership_request_status__code="APPROVED",
        ).values_list("member_id", flat=True)
        sections_qs = sections_qs.filter(
            meeting_section_members__user_id__in=wg_member_ids,
        ).distinct()
    elif scope_type in ("user", "user_day_summary"):
        sections_qs = sections_qs.filter(
            meeting_section_members__user_id=related_object_id,
        ).distinct()

    section_ids = list(sections_qs.values_list("pk", flat=True))
    if not section_ids:
        return []

    records_qs = (
        MeetingRecordsModel.objects
        .filter(section_id__in=section_ids, is_active=True)
        .order_by("section_id", "-created_at")
    )
    section_id_to_summaries = defaultdict(list)
    for rec in records_qs:
        if getattr(rec, "summary", None) and rec.summary.strip():
            section_id_to_summaries[rec.section_id].append(clean_html(rec.summary))

    out = []
    is_user_scope = scope_type in ("user", "user_day_summary")
    for section in sections_qs:
        participants = []
        user_duration = None
        for m in section.meeting_section_members.all():
            name = _profile_display_name(m.user)

            participants.append({
                "name": name,
            })
            if is_user_scope and m.user_id == related_object_id:
                duration_str = None
                if m.duration is not None:
                    total = int(m.duration.total_seconds())
                    total_minutes = total // 60
                    hours, minutes = divmod(total_minutes, 60)
                    duration_str = f"{hours:02d}:{minutes:02d}"
                user_duration = duration_str

        meeting = section.meeting
        project_info = None
        if meeting and meeting.project:
            project_info = {
                "name": meeting.project.name,
            }

        section_duration = None
        if section.duration is not None:
            total = int(section.duration.total_seconds())
            total_minutes = total // 60
            hours, minutes = divmod(total_minutes, 60)
            section_duration = f"{hours:02d}:{minutes:02d}"

        video_summaries = section_id_to_summaries.get(section.pk, [])
        section_data = {
            "section_name": section.name.strip() or None,
            "date_start": _normalize_for_json(section.date_start),
            "duration": section_duration,
            "participants": participants,
            "project": project_info,
            "video_summaries": video_summaries if video_summaries else None,
        }
        if is_user_scope:
            section_data["user_duration"] = user_duration
        out.append(section_data)
    return out


def _collect_events(related_object_id, scope_type, date_from, date_to):
    """
    События календарей, привязанных к задачам и workgroup.
    Охват: related_object_id + scope_type.
    """
    tasks_qs = TaskModel.objects.filter(is_active=True)
    if scope_type == "organization":
        tasks_qs = tasks_qs.filter(organization_id=related_object_id)
    elif scope_type == "project":
        tasks_qs = tasks_qs.filter(project_id=related_object_id)
    elif scope_type == "workgroup":
        tasks_qs = tasks_qs.filter(workgroup_id=related_object_id)
    elif scope_type in ("user", "user_day_summary"):
        tasks_qs = tasks_qs.filter(Q(owner_id=related_object_id) | Q(operator_id=related_object_id))
    task_ids = set(tasks_qs.values_list("pk", flat=True))

    workgroups_qs = WorkgroupModel.objects.filter(is_active=True)
    if scope_type == "organization":
        workgroups_qs = workgroups_qs.filter(organization_id=related_object_id)
    elif scope_type == "project":
        workgroups_qs = workgroups_qs.filter(pk=related_object_id)
    elif scope_type == "workgroup":
        workgroups_qs = workgroups_qs.filter(pk=related_object_id)
    elif scope_type in ("user", "user_day_summary"):
        workgroups_qs = workgroups_qs.filter(
            workgroupmembersmodel_set__member_id=related_object_id,
            workgroupmembersmodel_set__is_active=True,
            workgroupmembersmodel_set__membership_request_status__code="APPROVED",
        ).distinct()
    workgroup_ids = set(workgroups_qs.values_list("pk", flat=True))

    related_ids = task_ids | workgroup_ids
    if not related_ids:
        return []

    calendar_ids = list(
        CalendarModel.objects
        .filter(related_object_id__in=related_ids, is_active=True)
        .values_list("pk", flat=True)
    )
    if not calendar_ids:
        return []

    events_qs = (
        EventCalendarModel.objects
        .filter(
            calendar_id__in=calendar_ids,
            is_active=True,
            calendar__is_active=True,
        )
        .filter(
            start_at__date__lte=date_to,
            end_at__date__gte=date_from,
        )
        .select_related("calendar", "author")
        .prefetch_related("members")
        .order_by("start_at")
    )
    out = []
    for event in events_qs:
        out.append({
            "id": str(event.pk),
            "name": event.name,
            "start_at": _normalize_for_json(event.start_at),
            "end_at": _normalize_for_json(event.end_at),
            "description": clean_html(event.description or "").strip() or None,
            "participants": [_profile_display_name(m) for m in event.members.all()],
        })
    return out


def _collect_helpdesk_tickets(related_object_id, scope_type, date_from, date_to):
    """
    Обращения в техподдержку. Охват: related_object_id + scope_type (organization | user).
    """
    tickets_qs = HelpDeskTicketModel.objects.filter(
        is_active=True,
        updated_at__date__gte=date_from,
        updated_at__date__lte=date_to,
    )
    if scope_type == "organization":
        tickets_qs = tickets_qs.filter(customer_card__org_admin_id=related_object_id)
    elif scope_type in ("user", "user_day_summary"):
        tickets_qs = tickets_qs.filter(specialist_id=related_object_id)
    tickets_qs = (
        tickets_qs
        .select_related("status", "customer_card", "specialist", "author")
        .prefetch_related("messages__contact_person__user", "messages__author")
        .order_by("receipt_date", "created_at")
    )
    tickets_list = list(tickets_qs)
    ticket_ids = [t.pk for t in tickets_list]
    reason_to_counters = {}
    if ticket_ids:
        linked_tasks = (
            TaskModel.objects
            .filter(
                reason__in=[str(ticket_id) for ticket_id in ticket_ids],
                is_active=True,
                task_type__code="task",
            )
            .values_list("reason", "counter")
        )
        for reason, counter in linked_tasks:
            if reason not in reason_to_counters:
                reason_to_counters[reason] = []
            reason_to_counters[reason].append(counter)
    worklog_filters = {
        "is_active": True,
        "ticket_id__in": ticket_ids,
        "date__gte": date_from,
        "date__lte": date_to,
    }
    if scope_type in ("user", "user_day_summary"):
        worklog_filters["user_id"] = related_object_id
    worklogs_qs = (
        HelpDeskWorkLogModel.objects
        .filter(**worklog_filters)
        .select_related("user")
        .order_by("date", "created_at")
    )
    worklogs_by_ticket = defaultdict(list)
    for worklog in worklogs_qs:
        worklogs_by_ticket[worklog.ticket_id].append({
            "user": _profile_display_name(worklog.user),
            "hours": _normalize_for_json(worklog.hours),
            "date": _normalize_for_json(worklog.date),
            "description": clean_html(worklog.description or "").strip() or None,
        })
    out = []
    for ticket in tickets_list:
        comments_data = get_ticket_comments(ticket.pk, date_from, date_to)
        comments_compact = compact_comments(comments_data)
        messages_sorted = ticket.messages.all().order_by("message_date")
        messages_compact = [_compact_ticket_message(msg) for msg in messages_sorted]
        duration_value = ticket.duration if ticket.duration is not None else 0
        hours_value = (
            Decimal(duration_value) / Decimal("3600")
        ).quantize(Decimal("0.01"), rounding=ROUND_UP)
        out.append({
            "counter": ticket.number,
            "name": ticket.name,
            "description": clean_html(ticket.description or "").strip() or None,
            "status": getattr(ticket.status, "name", None) if ticket.status else None,
            "customer": getattr(ticket.customer_card, "name", None) if ticket.customer_card else None,
            "specialist": _profile_display_name(ticket.specialist),
            "author": _profile_display_name(ticket.author),
            "execution_result": (ticket.execution_result or "").strip() or None,
            "receipt_date": _normalize_for_json(ticket.receipt_date),
            "dead_line": _normalize_for_json(ticket.dead_line),
            "hours": _normalize_for_json(hours_value),
            "tasks": reason_to_counters.get(str(ticket.pk), []),
            "execution_times": worklogs_by_ticket.get(ticket.pk, []),
            "comments": comments_compact,
            "messages": messages_compact,
        })
    return out


def _collect_day_summaries(related_object_id, scope_type, date_from, date_to):
    """
    Итоги дня пользователей (опубликованные заметки) за период.
    Охват: related_object_id + scope_type (organization | project | workgroup | user).
    """
    qs = (
        DaySummaryNoteModel.objects
        .filter(
            is_active=True,
            status_id="published",
            date__gte=date_from,
            date__lte=date_to,
        )
        .select_related("author", "status", "category")
        .order_by("date", "author_id", "created_at")
    )

    if scope_type == "organization":
        org_member_ids = ContractorProfileModel.objects.filter(
            contractor_id=related_object_id,
            is_active=True,
        ).values_list("user_id", flat=True)
        qs = qs.filter(author_id__in=org_member_ids)
    elif scope_type in ("project", "workgroup"):
        wg_member_ids = WorkgroupMembersModel.objects.filter(
            work_group_id=related_object_id,
            is_active=True,
            membership_request_status__code="APPROVED",
        ).values_list("member_id", flat=True)
        qs = qs.filter(author_id__in=wg_member_ids)
    elif scope_type in ("user",):
        qs = qs.filter(author_id=related_object_id)
    else:
        return []

    out = []
    for note in qs:
        content = clean_html(note.content or "").strip()
        out.append({
            "date": _normalize_for_json(note.date),
            "user": _profile_display_name(getattr(note, "author", None)),
            "content": content or None,
        })
    return out


def _compact_chat_message(serialized_message):
    """
    Компактное представление сообщения чата для контекста LLM.
    Для share-задачи только counter (без comments/execution_times).
    """
    text = clean_html(serialized_message.get("text") or "")
    author = person_to_name(serialized_message.get("message_author"))
    share = serialized_message.get("share")
    task_counter = None
    if share and isinstance(share, dict) and share.get("type") == "tasks.TaskModel":
        task_counter = share.get("counter")
    if not text and task_counter is None:
        return None
    return {
        "created": _normalize_for_json(serialized_message.get("created")),
        "author": author,
        "text": text or None,
        "is_system": bool(serialized_message.get("is_system", False)),
        "task": _normalize_for_json(task_counter) if task_counter is not None else None,
    }


def _collect_chats(related_object_id, scope_type, date_from, date_to):
    """
    Чаты, привязанные к проектам/командам (workgroups). Охват: related_object_id + scope_type.
    Для scope_type "user" чаты не фильтруются по пользователю — пустой список.
    """
    chat_uids = set()
    if scope_type in ("organization", "project", "workgroup"):
        workgroups_qs = WorkgroupModel.objects.filter(
            is_active=True,
            linked_chat_id__isnull=False,
        )
        if scope_type == "organization":
            workgroups_qs = workgroups_qs.filter(organization_id=related_object_id)
        elif scope_type in ("project", "workgroup"):
            workgroups_qs = workgroups_qs.filter(pk=related_object_id)
        chat_uids.update(
            workgroups_qs.values_list("linked_chat_id", flat=True).distinct()
        )

    if not chat_uids:
        return []

    messages_qs = (
        chat_models.MessageModel.objects
        .filter(
            chat_id__in=chat_uids,
            created__date__gte=date_from,
            created__date__lte=date_to,
            is_active=True,
            is_ai_message=False,
        )
        .select_related("chat", "message_author", "share")
        .order_by("chat_id", "created")
    )

    out = []
    current_chat = None
    current_chat_uid = None
    for message in messages_qs:
        serialized = chat_serializers.MessageListSerializer(message).data
        compacted = _compact_chat_message(serialized)
        if compacted is None:
            continue
        if message.chat_id != current_chat_uid:
            current_chat_uid = message.chat_id
            current_chat = {
                "chat_uid": str(current_chat_uid),
                "name": message.chat.name if message.chat else "",
                "messages": [],
            }
            out.append(current_chat)
        current_chat["messages"].append(compacted)

    return out


def _to_date(value):
    """Приводит datetime или строку ISO к date. С фронта приходят start/end с таймзоной — берём только дату."""
    if value is None:
        return value
    if hasattr(value, "date") and callable(getattr(value, "date")):
        return value.date()
    if isinstance(value, str):
        # URL-декодирование превращает + в пробел (2026-01-01T00:00:00.000 03:00) — восстанавливаем +
        value = re.sub(r'\s(\d{2}:\d{2}(:\d{2}(\.\d+)?)?)$', r'+\1', value)
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return value


def collect_organization_activity_context(
    organization_id,
    date_from,
    date_to,
    project_id=None,
    workgroup_id=None,
    user_id=None,
):
    """
    Собирает контекст по деятельности организации за период для передачи в LLM.

    :param organization_id: pk организации (ContractorModel / catalogs.ContractorModel).
    :param date_from: начало периода (date, datetime или строка ISO).
    :param date_to: конец периода (date, datetime или строка ISO). Таймзона не используется — берётся только дата.
    :param project_id: опционально — только этот проект (WorkgroupModel pk).
    :param workgroup_id: опционально — только эта команда (WorkgroupModel pk).
    :param user_id: опционально — только задачи/тикеты, где пользователь owner/operator/specialist (profile pk).
    :return: dict с ключами projects, workgroups, tasks, meeting_summaries, events, helpdesk_tickets, chats.
    Чаты собираются только привязанные к проектам/командам (linked_chat_id workgroup).
    """
    date_from = _to_date(date_from)
    date_to = _to_date(date_to)

    return {
        # "projects": _collect_projects(organization_id, date_from, date_to, **extra),
        # "workgroups": _collect_workgroups(organization_id, date_from, date_to, **extra),
        "tasks": _collect_tasks(organization_id, "organization", date_from, date_to),
        # "meeting_summaries": _collect_meeting_summaries(organization_id, date_from, date_to, **extra),
        # "events": _collect_events(organization_id, date_from, date_to, **extra),
        # "helpdesk_tickets": _collect_helpdesk_tickets(organization_id, date_from, date_to, **extra),
        # "chats": _collect_chats(
        #     organization_id,
        #     date_from,
        #     date_to,
        #     **extra,
        # ),
    }


def collect_digests_for_period(date_from, date_to, related_object, sources=None, scope=None):
    """
    Собирает контекст для окончательного анализа в LLM из предсобранных дайджестов (ActivityDigestModel).

    :param date_from: начало периода (date).
    :param date_to: конец периода (date).
    :param related_object: UUID объекта среза (organization / project / workgroup / user).
    :param sources: список ключей — ['tasks', 'meetings', 'events', 'helpdesk', 'chats']. Если None или пустой — все источники.
    :param scope: охват среза (обязателен): organization | project | workgroup | user | user_day_summary.
    :return: список по дням только с непустыми источниками:
    [ {"day": "YYYY-MM-DD", "sources": {"tasks": {...}, ...}}, ... ].
    """
    from analytics.models import ActivityDigestModel, DIGEST_SOURCE_KEYS

    if date_from is None or date_to is None:
        return []
    if not scope:
        return []
    if isinstance(related_object, str):
        related_object = UUID(related_object)

    if not sources:
        source_keys = list(DIGEST_SOURCE_KEYS)
    else:
        source_keys = [k for k in sources if k in DIGEST_SOURCE_KEYS]

    qs = (
        ActivityDigestModel.objects
        .filter(
            related_object_id=related_object,
            date__gte=date_from,
            date__lte=date_to,
            scope=scope,
            source__in=source_keys,
        )
        .order_by("date", "source")
    )
    by_day = {}
    for row in qs:
        day_iso = row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date)
        if day_iso not in by_day:
            by_day[day_iso] = {}
        by_day[day_iso][row.source] = (row.summary or "").strip() or ""

    out = []
    current = date_from
    while current <= date_to:
        day_iso = current.isoformat() if hasattr(current, "isoformat") else str(current)
        day_sources = by_day.get(day_iso, {})
        sources_dict = {}
        for key in source_keys:
            source_summary = (day_sources.get(key) or "").strip()
            if not source_summary:
                continue
            sources_dict[key] = {"summary": source_summary}
        if sources_dict:
            out.append({"day": day_iso, "sources": sources_dict})
        current += timedelta(days=1)
    return out
