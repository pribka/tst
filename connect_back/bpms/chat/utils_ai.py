import json
import re
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from django.utils import timezone
from django.utils.functional import Promise
from django.core.serializers.json import DjangoJSONEncoder

from common.redis import socketio_redis
from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL


# ============================================================
# CHAT SUMMARY ANALYSIS UTILITIES
# ============================================================


def normalize_for_json(value):
    """Normalize Django types for JSON serialization."""
    if isinstance(value, Promise):  # gettext_lazy / __proxy__
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)  # для LLM лучше строкой, без float-ошибок
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_for_json(v) for v in value]
    return value


# HTML cleanup regex
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


def get_task_comments(task_id):
    """Get comments for a task (like CommentListView, without request)."""
    from bpms.comments.models import CommentModel
    from bpms.comments.serializers import CommentListSerializer
    
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
        )
        .order_by("created_at")
    )
    return CommentListSerializer(qs, many=True).data


def get_task_execution_times(task_id):
    """Get execution times for a task (list serializer)."""
    from bpms.tasks.models import TaskExecutionTimeModel
    from bpms.tasks.serializers import TaskExecutionTimeModelListSerializer
    
    qs = (
        TaskExecutionTimeModel.objects
        .filter(task_id=task_id, is_active=True)
        .select_related(
            "measure_unit",
            "work_type",
            "event_calendar",
            "meeting_section",
        )
        .order_by("-created_at")
    )
    return TaskExecutionTimeModelListSerializer(qs, many=True).data


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


def compact_task(share: dict) -> dict:
    """
    Compact task data for LLM.
    IMPORTANT: Do not remove task number.
    Task number is in share['counter'] (example: "12580", "12684").
    """
    status = share.get("status")
    status_name = status.get("name") if isinstance(status, dict) else status

    project = share.get("project")
    project_name = project.get("name") if isinstance(project, dict) else None

    workgroup = share.get("workgroup")
    workgroup_name = workgroup.get("name") if isinstance(workgroup, dict) else None

    task_number = share.get("counter")
    if not task_number:
        task_number = share.get("number") or share.get("code")

    return {
        "number": task_number,  # <<< DO NOT REMOVE
        "name": share.get("name"),
        "status": status_name,
        "priority": share.get("priority"),
        "deadline": share.get("dead_line"),
        "finished_date": share.get("finished_date"),
        "owner": person_to_name(share.get("owner")),
        "operator": person_to_name(share.get("operator")),
        "project": project_name,
        "workgroup": workgroup_name,
        "result": clean_html(share.get("result") or ""),
        "comments": compact_comments(share.get("comments") or []),
        "execution_times": compact_execution_times(share.get("execution_times") or []),
    }


def compact_message(m: dict):
    """Compact message data for LLM."""
    text = clean_html(m.get("text") or "")
    author = person_to_name(m.get("message_author"))

    out = {
        "created": m.get("created"),
        "author": author,
        "text": text,
        "is_system": bool(m.get("is_system", False)),
        "task": None,
    }

    share = m.get("share")
    if share and isinstance(share, dict) and share.get("type") == "tasks.TaskModel":
        out["task"] = compact_task(share)

    if not out["text"] and out["task"] is None:
        return None

    return out


def create_chat_message(chat, message_author, text, is_system=False, is_ai_message=False):
    """
    Create a new message in chat and send it via socketio.
    """
    from bpms.chat import models
    from bpms.chat import serializers
    
    message = models.MessageModel()
    message.chat = chat
    if message_author is not None:
        message.message_author = message_author
    message.is_system = is_system
    message.is_ai_message = is_ai_message
    message.created = timezone.now()
    message.text = text
    message.save()
    
    # Serialize message and send via socketio
    message_data = serializers.MessageListSerializer(message).data
    message_data['chat_uid'] = str(message.chat.chat_uid)
    message_data['chat_name'] = message.chat.name
    message_data['is_public'] = message.chat.is_public
    message_data['is_new'] = True
    data = json.dumps(
        {
            "event": "chat_message",
            "data": message_data,
        },
        cls=DjangoJSONEncoder
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
    
    return message_data

