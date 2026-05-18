import logging
import os
import re
import json
import io
import uuid
import html as html_lib
from contextlib import nullcontext
import requests
from datetime import datetime, timedelta, time
from typing import Optional, Tuple, List
# ==============================
# Django и системная инициализация
# ==============================
import django
from django.apps import apps
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.template import Context, Template
from django.test import RequestFactory
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.safestring import mark_safe


# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()

logger = logging.getLogger(__name__)

# ==============================
# Константы и базовые импорты проекта
# ==============================
from bkz3.settings import FRONTEND_URL, BACKEND_URL, TG_MINI_APP_URL

profile_model = apps.get_model('users', 'ProfileModel')
from common.current_profile.middleware import user_context

# ==============================
# Телеграм (pyTelegramBotAPI)
# ==============================
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MessageEntity,
    WebAppInfo
)

from telegram_bot.base import welcome_bot  # основной бот

# ==============================
# Django Q (асинхронные задачи)
# ==============================
from django_q.tasks import async_task
from common.models import BaseModel
# ==============================
# BPMS (бизнес-процессы)
# ==============================
from bpms.tasks import notifications
from bpms.tasks.models import TaskModel, TaskStatusModel
from bpms.tasks.utils import filter_by_permissions, get_tasks_status_count

from bpms.event_calendar.models import EventCalendarModel
from bpms.meetings.models import PlannedMeetingModel
from bpms.meetings.utils import get_invite_link

from bpms.comments.models import CommentModel
from bpms.comments import notifications as comments_notifications

# ==============================
# Help Desk
# ==============================
from help_desk.models import HelpDeskTicketModel, HelpDeskTicketStatusModel
from help_desk import utils as help_desk_utils
# from help_desk import notifications as help_desk_notifications

# ==============================
# Notifications / Уведомления
# ==============================
from notifications.models import WebNotificationModel
from notifications.serializers import WebNotificationSerializer

# ==============================
# Common (общие модули)
# ==============================
from common.models import TGMessageModel, BaseModel as CommonBaseModel
from common.utils import wait_if_paused
from bpms.bpms_common.views import _recognize_voice_input
from bpms.chat_ai import models as chat_ai_models
from bpms.chat_ai.serializers import IntentCreateSerializer
from bpms.chat_ai.utils.messages import (
    INTENT_CLASSIFIER_SCHEMA,
    INTENT_RESPONSE_SOFT_SCHEMA,
)
from bpms.chat_ai.utils.reference_matching import split_reference_names as split_reference_names_for_profiles
from bpms.chat_ai.utils.workflow_requests import (
    is_workflow_request_intent,
    materialize_workflow_request_intent,
)
from openai import OpenAI

# ==============================
# Контроль прав доступа
# ==============================
from contractor_permissions.utils import check_user_app_section_role_permission

TG_LIMIT = 4096  # жесткий лимит Telegram
SAFE_HEAD = 100  # небольшой запас на сервисные символы/непредвиденные
CHUNK_LIMIT = 3600  # безопасный лимит текста в одном сообщении (UTF-16 юниты)
# Словарь соответствия кодов статусов обращений их названиям
TICKET_STATUS_NAMES = {
    'new': 'Новый',
    'in_work': 'В работе',
    'on_pause': 'На паузе',
    'completed': 'Завершён',
    'on_testing': 'На приёмке',
    'on_rework': 'На доработке',
}


TG_AI_CHAT_NAME = "Telegram AI Chat"
TG_AI_SESSION_TTL_SECONDS = 60 * 60 * 12
TG_AI_CALLBACK_CONFIRM_PREFIX = "tgai_confirm_"
TG_AI_CALLBACK_CANCEL_PREFIX = "tgai_cancel_"
TG_AI_ACCESS_DENIED_TEXT = "Доступ к AI-боту отключён для вашего профиля. Обратитесь к администратору."
def _tg_ai_cache_key(profile_id) -> str:
    return f"tg_ai_dialog:{profile_id}"


def _tg_ai_profile_has_access(profile) -> bool:
    user = getattr(profile, "user", None)
    if not user:
        return False
    if not bool(getattr(user, "is_authenticated", False)):
        return False
    return bool(getattr(profile, "use_ai_bot", False))


def _tg_ai_get_state(profile_id) -> dict:
    return cache.get(_tg_ai_cache_key(profile_id), {}) or {}


def _tg_ai_set_state(profile_id, state: dict) -> None:
    cache.set(_tg_ai_cache_key(profile_id), state, TG_AI_SESSION_TTL_SECONDS)


def _tg_ai_clear_state(profile_id) -> None:
    cache.delete(_tg_ai_cache_key(profile_id))


def _tg_ai_deactivate_intents_for_bot_message(bot_message_id):
    if not bot_message_id:
        return
    try:
        bot_message = chat_ai_models.AIMessageModel.objects.get(pk=bot_message_id, is_bot=True)
    except chat_ai_models.AIMessageModel.DoesNotExist:
        return

    now = timezone.now()
    bot_message.intents.filter(is_active=True).update(is_active=False, deleted_at=now)


def _tg_ai_build_request_for_profile(profile):
    request = RequestFactory().post("/api/v1/chat_ai/messages/")
    request.user = profile.user
    request.profile = profile
    request.query_params = request.GET
    return request


def _tg_ai_get_or_create_chat(profile):
    chat = chat_ai_models.AIChatModel.objects.filter(
        chat_author=profile,
        is_active=True,
        name=TG_AI_CHAT_NAME,
    ).first()
    if chat:
        return chat
    return chat_ai_models.AIChatModel.objects.create(
        chat_author=profile,
        name=TG_AI_CHAT_NAME,
        is_active=True,
    )


def _tg_ai_extract_voice_text(message) -> str:
    audio_obj = None
    content_type = "application/octet-stream"
    filename = "voice-input.bin"

    if getattr(message, "voice", None):
        audio_obj = message.voice
        content_type = getattr(audio_obj, "mime_type", None) or "audio/ogg"
        filename = "voice-message.ogg"
    elif getattr(message, "audio", None):
        audio_obj = message.audio
        content_type = getattr(audio_obj, "mime_type", None) or "audio/mpeg"
        filename = getattr(audio_obj, "file_name", None) or "audio-message.mp3"
    else:
        return ""

    telegram_file = welcome_bot.get_file(audio_obj.file_id)
    raw_file = welcome_bot.download_file(telegram_file.file_path)
    file_obj = io.BytesIO(raw_file)

    payload = _recognize_voice_input(
        file_obj=file_obj,
        filename=filename,
        content_type=content_type,
    )
    return (payload or {}).get("text", "").strip()


def _tg_ai_parse_classifier_response(resp) -> str:
    allowed_intents = {"task", "event", "meet", "report", "workflow_request", "unknown"}
    parsed_intent = "unknown"
    if isinstance(resp, str):
        parsed_intent = resp.strip().lower()
    elif isinstance(resp, dict):
        parsed_intent = str(resp.get("intent", "")).strip().lower()
    if parsed_intent not in allowed_intents:
        parsed_intent = "unknown"
    return parsed_intent


def _tg_ai_normalize_intents(intents):
    if not isinstance(intents, list):
        return []
    result = []
    for item in intents:
        if not isinstance(item, dict):
            continue
        if item.get("error"):
            continue
        result.append(item)
    return result


def _tg_ai_clean_json(text):
    if not isinstance(text, str):
        return text
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return cleaned


def _tg_ai_get_role_safe(role_code: str):
    return (
        chat_ai_models.AIChatRoleModel.objects
        .select_related("provider")
        .defer("provider__api_key")
        .get(code=role_code)
    )


def _tg_ai_call_provider(role, *, system_message, user_prompt, format_schema=None, url_query_param=None, parse_json=True):
    provider = role.provider

    if provider.code == "gos24.kz":
        wait_if_paused()
        payload = {
            "model": role.model_name,
            "system": system_message,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": float(role.temperature),
                "repeat_penalty": 1.2,
                "top_p": float(role.top_p),
                "num_predict": role.max_output_tokens,
                "num_ctx": role.num_ctx,
            },
        }
        if format_schema:
            payload["format"] = format_schema

        request_url = provider.base_url
        if url_query_param:
            request_url = f"{provider.base_url}?{url_query_param}"

        response = requests.post(request_url, json=payload, timeout=(120, 600))
        response.raise_for_status()
        data = response.json()
        text_response = (data.get("response") or "").strip()
        return _tg_ai_clean_json(text_response) if parse_json else text_response

    # For non-gos providers we must read api_key, which may fail if encrypted data is invalid.
    try:
        api_key = provider.api_key
    except Exception as exc:
        raise RuntimeError(f"Provider api_key is unreadable: {exc}")

    client = OpenAI(api_key=api_key, base_url=(provider.base_url or None))
    response = client.chat.completions.create(
        model=role.model_name,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        temperature=float(role.temperature),
        max_tokens=role.max_output_tokens,
        top_p=float(role.top_p),
    )
    text_response = (response.choices[0].message.content or "").strip()
    return _tg_ai_clean_json(text_response) if parse_json else text_response


def _tg_ai_invoke_role_prompt_safe(user_message: str, role_code: str, context: dict, format_schema=None, url_query_param=None, parse_json=True):
    if not user_message:
        return None

    role = _tg_ai_get_role_safe(role_code)
    system_message = Template(role.system_message).render(Context(context or {}))
    user_context = (context or {}).copy()
    user_context["user_message"] = mark_safe(user_message)
    rendered_user_message = Template(role.user_message).render(Context(user_context))

    return _tg_ai_call_provider(
        role,
        system_message=system_message,
        user_prompt=rendered_user_message,
        format_schema=format_schema,
        url_query_param=url_query_param,
        parse_json=parse_json,
    )


def _tg_ai_classify_and_parse(session_text):
    try:
        classify_resp = _tg_ai_invoke_role_prompt_safe(
            user_message=session_text,
            role_code="intent_classifier",
            context={},
            format_schema=INTENT_CLASSIFIER_SCHEMA,
            url_query_param="tg_welcome_bot_classify=1",
            parse_json=True,
        )
    except Exception:
        logger.exception("Intent classification failed")
        return "unknown", []

    intent_label = _tg_ai_parse_classifier_response(classify_resp)

    if intent_label == "unknown":
        return intent_label, []

    parser_role_code = "intent_parser"
    if intent_label == "report" and chat_ai_models.AIChatRoleModel.objects.filter(code="intent_parser_report").exists():
        parser_role_code = "intent_parser_report"
    if (
        intent_label == "workflow_request"
        and chat_ai_models.AIChatRoleModel.objects.filter(code="intent_parser_workflow_request").exists()
    ):
        parser_role_code = "intent_parser_workflow_request"

    parser_context = _tg_ai_build_parser_context()
    try:
        parser_resp = _tg_ai_invoke_role_prompt_safe(
            user_message=session_text,
            role_code=parser_role_code,
            context=parser_context,
            format_schema=INTENT_RESPONSE_SOFT_SCHEMA,
            url_query_param="tg_welcome_bot_parse=1",
            parse_json=True,
        )
    except Exception:
        logger.exception("Intent parser failed")
        return intent_label, []

    return intent_label, _tg_ai_normalize_intents(parser_resp)


def _tg_ai_build_parser_context():
    today = datetime.today().date()
    weekdays_ru = [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
        "воскресенье",
    ]
    weekday_items = []
    for day_offset in range(7):
        date_value = today + timedelta(days=day_offset)
        weekday_items.append(f"{weekdays_ru[date_value.weekday()]}: {date_value.isoformat()}")
    return {
        "current_date": today.strftime("%Y-%m-%d"),
        "current_weekday": datetime.today().strftime("%A"),
        "weekday_reference": "; ".join(weekday_items),
    }


def _tg_ai_invoke_classifier_provider_text(system_message: str, user_message: str) -> str:
    role = _tg_ai_get_role_safe("intent_classifier")
    text_response = _tg_ai_call_provider(
        role,
        system_message=system_message,
        user_prompt=user_message,
        format_schema=None,
        url_query_param="tg_welcome_bot_reply=1",
        parse_json=False,
    )
    return (text_response or "").strip()


def _tg_ai_fallback_reply(intent_label, intents):
    if intents:
        first = intents[0]
        intent_type = first.get("intent_type") or "unknown"
        details = []
        for key, value in first.items():
            if key == "intent_type" or value in (None, "", [], {}):
                continue
            details.append(f"{key}: {value}")
        if details:
            return f"Похоже на намерение типа {intent_type}. Вижу параметры: {'; '.join(details[:6])}."
        return f"Похоже на намерение типа {intent_type}. Можем уточнить детали и нажать Готово."

    if intent_label != "unknown":
        return f"Похоже на намерение типа {intent_label}, но пока недостаточно данных. Уточните, пожалуйста."

    return "Привет. Опишите, что хотите сделать, и я помогу сформировать намерение."


def _tg_ai_generate_dialog_reply(session_text, intent_label, intents):
    intents_json = json.dumps(intents, ensure_ascii=False)
    system_prompt = (
        "Ты ассистент корпоративного Telegram-бота. Отвечай только на русском, коротко и понятно, без markdown. "
        "Если intent_label не unknown, объясни что за намерение найдено и перечисли его ключевые характеристики. "
        "Если intent_label unknown, сделай приветственный и направляющий ответ."
    )
    user_prompt = (
        f"session_text:\n{session_text}\n\n"
        f"intent_label: {intent_label}\n"
        f"intents_json: {intents_json}\n\n"
        "Сформируй финальный ответ пользователю."
    )
    try:
        reply = _tg_ai_invoke_classifier_provider_text(system_prompt, user_prompt)
        reply = (reply or "").strip()
        if reply:
            return reply
    except Exception:
        logger.exception("Failed to generate dialog reply via classifier provider")
    return _tg_ai_fallback_reply(intent_label, intents)


def _tg_ai_create_intents_for_bot_message(bot_message, intents, request):
    created_ids = []
    for item in intents:
        intent_type = item.get("intent_type")
        if not intent_type:
            continue
        raw_data = item.copy()
        raw_data.pop("intent_type", None)

        serializer = IntentCreateSerializer(
            data={
                "source_object": bot_message.pk,
                "intent_type": intent_type,
                "raw_data": raw_data,
            },
            context={"request": request},
        )
        actor_user = getattr(request, "user", None)
        context_guard = user_context(actor_user) if actor_user else nullcontext()
        with context_guard:
            serializer.is_valid(raise_exception=True)
            intent_obj = serializer.save()
        created_ids.append(str(intent_obj.pk))
    return created_ids


def _tg_ai_materialize_intent(intent_obj, request):
    if not intent_obj.get_update_permission(request):
        raise ValueError("You do not have permission to materialize this intent.")

    if intent_obj.status_id != "ready":
        raise ValueError(f'Intent status must be "ready", current status: {intent_obj.status_id}')

    metadata = getattr(intent_obj.intent_type, "metadata", {})
    target_info = metadata.get("target", {})
    model_path = target_info.get("model")
    action = target_info.get("action", "create")
    backend_base_url = str(metadata.get("backend_base_url") or "").strip()

    if is_workflow_request_intent(intent_obj):
        return materialize_workflow_request_intent(intent_obj, request)

    if not model_path and backend_base_url:
        report_result = _tg_ai_materialize_report_intent(intent_obj, request, backend_base_url)
        intent_obj.status_id = "done"
        intent_obj.errors = []
        intent_obj.save(update_fields=["status", "errors"])
        return report_result

    if not model_path:
        raise ValueError("Target model is not configured for this intent type.")

    with transaction.atomic():
        app_label, model_name = model_path.split(".", 1)
        model_class = apps.get_model(app_label, model_name)
        serializer_class = model_class.get_serializer_class(action=action)
        serializer = serializer_class(
            data=intent_obj.resolved_data,
            context={"request": request},
        )
        actor_user = getattr(request, "user", None)
        context_guard = user_context(actor_user) if actor_user else nullcontext()
        with context_guard:
            serializer.is_valid(raise_exception=True)
            created_object = serializer.save()

            intent_obj.related_object = created_object
            intent_obj.status_id = "done"
            intent_obj.errors = []
            intent_obj.save(update_fields=["related_object", "status", "errors"])
            return created_object


def _tg_ai_materialize_report_intent(intent_obj, request, backend_base_url):
    from rest_framework.test import APIRequestFactory, force_authenticate
    from reports.views import ReportSettingsModelViewSet

    payload = (intent_obj.resolved_data or {}).copy()
    metadata = getattr(intent_obj.intent_type, "metadata", {}) or {}
    fixed_values = metadata.get("fixed_values", {}) if isinstance(metadata, dict) else {}
    if not payload.get("report_code"):
        payload["report_code"] = fixed_values.get("report_code")

    report_code = str(payload.get("report_code") or "").strip()
    if not report_code:
        raise ValueError("Report code is missing for this intent type.")

    request_path = str(backend_base_url or "").strip() or "/reports/report_settings/run_from_chat/"
    if not request_path.startswith("/"):
        request_path = f"/{request_path}"
    if not request_path.startswith("/api/"):
        request_path = f"/api/v1{request_path}"

    internal_request = APIRequestFactory().post(request_path, payload, format="json")
    force_authenticate(internal_request, user=request.user)
    internal_view = ReportSettingsModelViewSet.as_view({"post": "run_from_chat"})
    response = internal_view(internal_request)

    status_code = int(getattr(response, "status_code", 500) or 500)
    if status_code >= 400:
        error_payload = None
        if hasattr(response, "data"):
            error_payload = response.data
        elif hasattr(response, "content"):
            error_payload = (response.content or b"").decode("utf-8", errors="ignore")
        raise ValueError(f"Failed to run report intent (status={status_code}): {error_payload}")

    content = bytes(getattr(response, "content", b"") or b"")
    content_type = str(getattr(response, "get", lambda *_: "")("Content-Type") or "").lower()
    is_file = bool(content) and (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in content_type
        or "application/octet-stream" in content_type
    )
    if is_file:
        filename = f"{report_code}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return {
            "kind": "report_file",
            "report_code": report_code,
            "filename": filename,
            "content": content,
            "caption": f'Отчет "{intent_obj.intent_type.name}"',
        }

    return {
        "kind": "report_result",
        "report_code": report_code,
        "caption": f'Отчет "{intent_obj.intent_type.name}"',
    }


def _tg_ai_build_actions_markup(bot_message_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="Готово", callback_data=f"{TG_AI_CALLBACK_CONFIRM_PREFIX}{bot_message_id}"),
        InlineKeyboardButton(text="Отмена", callback_data=f"{TG_AI_CALLBACK_CANCEL_PREFIX}{bot_message_id}"),
    )
    return markup


def _tg_ai_collect_created_intents_debug(created_intent_ids):
    if not created_intent_ids:
        return []

    result = []
    intents_qs = chat_ai_models.IntentModel.objects.filter(pk__in=created_intent_ids).select_related("intent_type")
    by_id = {str(item.pk): item for item in intents_qs}

    for intent_id in created_intent_ids:
        intent_obj = by_id.get(str(intent_id))
        if not intent_obj:
            continue

        field_debug = {}
        resolutions = intent_obj.resolutions if isinstance(intent_obj.resolutions, dict) else {}
        metadata = getattr(intent_obj.intent_type, "metadata", {}) if intent_obj.intent_type else {}
        schema = metadata.get("fields", {}) if isinstance(metadata, dict) else {}
        raw_data = intent_obj.raw_data if isinstance(intent_obj.raw_data, dict) else {}
        for field_name, resolution in resolutions.items():
            if not isinstance(resolution, dict):
                continue
            field_def = schema.get(field_name, {}) if isinstance(schema, dict) else {}
            candidates = resolution.get("candidates") or []
            candidate_preview = []
            for candidate in candidates[:3]:
                if isinstance(candidate, dict):
                    candidate_preview.append({
                        "id": candidate.get("id"),
                        "repr": candidate.get("repr"),
                        "for_name": candidate.get("for_name"),
                    })
            field_debug[field_name] = {
                "status": resolution.get("status"),
                "value": resolution.get("value"),
                "resolved": resolution.get("resolved"),
                "candidates_count": len(candidates),
                "candidates_preview": candidate_preview,
                "model": field_def.get("model"),
                "field_type": field_def.get("type"),
                "raw_value": raw_data.get(field_name),
            }

        result.append({
            "id": str(intent_obj.pk),
            "intent_type": intent_obj.intent_type_id,
            "status": intent_obj.status_id,
            "raw_data": intent_obj.raw_data,
            "resolved_data": intent_obj.resolved_data,
            "fields": field_debug,
        })

    return result


def _tg_ai_build_debug_payload(*, intent_label, is_intent, intents, created_intent_ids, created_intents_debug, session_chunks):
    return {
        "intent_label": intent_label,
        "is_intent": bool(is_intent),
        "session_chunks": int(session_chunks or 0),
        "generated_intents": intents if isinstance(intents, list) else [],
        "created_intent_ids": created_intent_ids or [],
        "created_intents_debug": created_intents_debug or [],
    }


def _tg_ai_render_debug_block(payload, max_chars=2400):
    debug_json = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(debug_json) > max_chars:
        debug_json = debug_json[: max_chars - 3] + "..."
    return f"TECH DEBUG:\n{debug_json}"


TG_AI_INTENT_TYPE_TITLES = {
    "create_task": "Создание задачи",
    "create_event": "Создание события",
    "create_meet": "Создание онлайн-встречи",
    "create_workflow_request": "Создание заявки на согласование",
}

TG_AI_INTENT_FIELDS_ORDER = {
    "create_task": [
        "name",
        "description",
        "operator",
        "cooperators",
        "visors",
        "project",
        "workgroup",
        "date_start_plan",
        "dead_line",
    ],
    "create_event": [
        "name",
        "description",
        "start_at",
        "members",
    ],
    "create_meet": [
        "name",
        "date_begin",
        "members",
    ],
    "create_workflow_request": [
        "request_type",
        "organization",
        "description",
        "amount_requested",
        "project",
        "dead_line",
        "event_date_start",
        "event_date_end",
        "money_under_report",
    ],
}

TG_AI_INTENT_FIELD_TITLES = {
    "name": "Название",
    "description": "Описание",
    "operator": "сполнитель",
    "cooperators": "Соисполнители",
    "visors": "Наблюдатели",
    "project": "Проект",
    "workgroup": "Рабочая группа",
    "date_start_plan": "Плановый старт",
    "dead_line": "Срок",
    "start_at": "Начало",
    "members": "Участники",
    "date_begin": "Начало",
    "request_type": "Тип заявки",
    "organization": "Организация",
    "amount_requested": "Сумма",
    "event_date_start": "Дата начала события",
    "event_date_end": "Дата окончания события",
    "money_under_report": "Деньги под отчет",
}


def _tg_ai_is_empty_value(value):
    if value in (None, "", [], {}):
        return True
    if isinstance(value, str) and value.strip().lower() == "null":
        return True
    return False


def _tg_ai_value_to_text(value):
    if _tg_ai_is_empty_value(value):
        return "не указано"
    if isinstance(value, dict):
        for key in ("repr", "name", "title", "id"):
            if value.get(key):
                return str(value.get(key))
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        items = [_tg_ai_value_to_text(item) for item in value if not _tg_ai_is_empty_value(item)]
        return ", ".join(items) if items else "не указано"
    return str(value)


def _tg_ai_get_debug_item_by_index(created_intents_debug, index):
    if isinstance(created_intents_debug, list) and index < len(created_intents_debug):
        item = created_intents_debug[index]
        if isinstance(item, dict):
            return item
    return {}


def _tg_ai_get_resolved_field_value_from_debug(intent_debug, field_name):
    if not isinstance(intent_debug, dict):
        return None

    field_debug = (intent_debug.get("fields") or {}).get(field_name) or {}
    if isinstance(field_debug, dict):
        status = field_debug.get("status")
        resolved = field_debug.get("resolved")
        value = field_debug.get("value")
        if status == "ready" and not _tg_ai_is_empty_value(resolved):
            if not _tg_ai_is_empty_value(value):
                return value
            return resolved

    resolved_data = intent_debug.get("resolved_data") or {}
    resolved_value = resolved_data.get(field_name)
    if not _tg_ai_is_empty_value(resolved_value):
        return resolved_value
    return None


def _tg_ai_collect_empty_fields_from_debug(intent_debug, field_order):
    if isinstance(intent_debug, dict):
        fields_debug = intent_debug.get("fields") or {}
        resolved_data = intent_debug.get("resolved_data") or {}
    else:
        fields_debug = {}
        resolved_data = {}

    result = []
    for field_name in field_order:
        info = fields_debug.get(field_name)
        if isinstance(info, dict):
            status = info.get("status")
            resolved = info.get("resolved")
            if status != "ready" or _tg_ai_is_empty_value(resolved):
                if _tg_ai_is_empty_value(resolved_data.get(field_name)):
                    result.append(field_name)
            continue

        if _tg_ai_is_empty_value(resolved_data.get(field_name)):
            result.append(field_name)
    return result


def _tg_ai_count_selected_people(value):
    if _tg_ai_is_empty_value(value):
        return 0
    if isinstance(value, dict):
        return 1
    if isinstance(value, list):
        count = 0
        for item in value:
            if _tg_ai_is_empty_value(item):
                continue
            count += 1
        return count
    return 1


def _tg_ai_collect_unresolved_profile_fields(intent_item, intent_debug, field_order):
    if not isinstance(intent_debug, dict):
        return []

    fields_debug = intent_debug.get("fields") or {}
    result = []
    for field_name in field_order:
        info = fields_debug.get(field_name)
        if not isinstance(info, dict):
            continue
        if str(info.get("model") or "") != "users.ProfileModel":
            continue

        raw_value = info.get("raw_value")
        if _tg_ai_is_empty_value(raw_value):
            if isinstance(intent_item, dict):
                raw_value = intent_item.get(field_name)
        if _tg_ai_is_empty_value(raw_value):
            continue

        requested_names = split_reference_names_for_profiles(raw_value, "users.ProfileModel")
        requested_count = len(requested_names) if requested_names else 1

        matched_payload = info.get("value")
        if _tg_ai_is_empty_value(matched_payload):
            matched_payload = info.get("resolved")
        matched_count = _tg_ai_count_selected_people(matched_payload)

        if matched_count < requested_count:
            result.append((field_name, raw_value))
    return result


def _tg_ai_get_display_field_value(intent_item, intent_debug, field_name):
    if isinstance(intent_debug, dict):
        field_debug = (intent_debug.get("fields") or {}).get(field_name) or {}
        value = field_debug.get("value")
        if not _tg_ai_is_empty_value(value):
            return value

    if isinstance(intent_item, dict):
        value = intent_item.get(field_name)
        if not _tg_ai_is_empty_value(value):
            return value

    if isinstance(intent_debug, dict):
        raw_value = (intent_debug.get("raw_data") or {}).get(field_name)
        if not _tg_ai_is_empty_value(raw_value):
            return raw_value

        resolved_value = (intent_debug.get("resolved_data") or {}).get(field_name)
        if not _tg_ai_is_empty_value(resolved_value):
            return resolved_value

    return None


def _tg_ai_collect_ambiguous_fields(intent_debug, field_order):
    if not isinstance(intent_debug, dict):
        return []
    fields_debug = intent_debug.get("fields") or {}
    result = []
    for field_name in field_order:
        info = fields_debug.get(field_name)
        if not isinstance(info, dict):
            continue
        resolved = info.get("resolved")
        candidates_count = int(info.get("candidates_count") or 0)
        if _tg_ai_is_empty_value(resolved) and candidates_count > 1:
            result.append(field_name)
    return result


def _tg_ai_render_intent_preview(intent_item, intent_debug, index):
    intent_type = (intent_item or {}).get("intent_type") or "unknown"
    title = TG_AI_INTENT_TYPE_TITLES.get(intent_type, f"Намерение: {intent_type}")
    lines = [f"{index}. {title}"]

    field_order = TG_AI_INTENT_FIELDS_ORDER.get(intent_type)
    if not field_order and isinstance(intent_item, dict):
        field_order = [key for key in intent_item.keys() if key != "intent_type"]
    field_order = field_order or []

    filled_lines = []
    for field_name in field_order:
        value = _tg_ai_get_resolved_field_value_from_debug(intent_debug, field_name)
        if _tg_ai_is_empty_value(value):
            continue
        field_title = TG_AI_INTENT_FIELD_TITLES.get(field_name, field_name)
        filled_lines.append(f"- {field_title}: {_tg_ai_value_to_text(value)}")

    if filled_lines:
        lines.append("Подтверждено:")
        lines.extend(filled_lines)
    else:
        lines.append("Подтверждено: пока нет заполненных полей")

    unresolved_profile_fields = _tg_ai_collect_unresolved_profile_fields(intent_item, intent_debug, field_order)
    if unresolved_profile_fields:
        lines.append("Не сопоставлено в базе:")
        for field_name, raw_value in unresolved_profile_fields:
            field_title = TG_AI_INTENT_FIELD_TITLES.get(field_name, field_name)
            lines.append(f"- {field_title}: {_tg_ai_value_to_text(raw_value)} (НЕИЗВ.)")

    empty_fields = _tg_ai_collect_empty_fields_from_debug(intent_debug, field_order)
    if empty_fields:
        empty_titles = [TG_AI_INTENT_FIELD_TITLES.get(name, name) for name in empty_fields]
        lines.append(f"Пустые поля: {', '.join(empty_titles)}")
    else:
        lines.append("Пустые поля: нет")

    return "\n".join(lines)


def _tg_ai_build_presentable_reply(reply_text, intent_label, intents, created_intents_debug):
    base_text = (reply_text or "").strip()
    if intent_label == "unknown" or not isinstance(intents, list) or not intents:
        return base_text

    sections = ["Намерение распознано. Ниже структурированный результат перед выполнением."]
    sections.append("Предварительный результат:")
    for idx, intent_item in enumerate(intents, start=1):
        intent_debug = _tg_ai_get_debug_item_by_index(created_intents_debug, idx - 1)
        sections.append(_tg_ai_render_intent_preview(intent_item, intent_debug, idx))

    sections.append('Если всё верно, нажмите "Готово". Для правок напишите уточнение или нажмите "Отмена".')
    return "\n\n".join(section for section in sections if section).strip()


def _tg_ai_compose_reply_with_debug(reply_text, payload):
    text = (reply_text or "").strip()
    if len(text) > 3900:
        return text[:3897] + "..."
    return text


def _tg_ai_progress_start(chat_id, text):
    try:
        msg = welcome_bot.send_message(chat_id=chat_id, text=text)
        return getattr(msg, "message_id", None)
    except Exception:
        logger.exception("Failed to send progress message")
        return None


def _tg_ai_progress_update(chat_id, progress_message_id, text):
    try:
        welcome_bot.send_chat_action(chat_id, 'typing')
    except Exception:
        pass

    if not progress_message_id:
        return

    try:
        welcome_bot.edit_message_text(chat_id=chat_id, message_id=progress_message_id, text=text)
    except Exception:
        pass


def _tg_ai_progress_finish(chat_id, progress_message_id, text):
    if not progress_message_id:
        return
    try:
        welcome_bot.edit_message_text(chat_id=chat_id, message_id=progress_message_id, text=text)
    except Exception:
        pass


def _tg_ai_build_frontend_object_url(obj):
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return str(obj.get("frontend_url") or "").strip()

    raw_route = getattr(obj, "frontend_route", "") or ""
    route = str(raw_route).strip()

    if route:
        if route.startswith(("http://", "https://")):
            return route
        if route.startswith("/"):
            return f"{FRONTEND_URL}{route}"
        return f"{FRONTEND_URL}/{route}"

    model_label = getattr(getattr(obj, "_meta", None), "label_lower", "")
    obj_id = getattr(obj, "pk", None)
    if not obj_id:
        return ""

    if model_label == "event_calendar.eventcalendarmodel":
        return f"{FRONTEND_URL}?event={obj_id}"
    if model_label == "meetings.plannedmeetingmodel":
        return f"{FRONTEND_URL}?meeting={obj_id}"
    if model_label == "help_desk.helpdeskticketmodel":
        return f"{FRONTEND_URL}/helpdesk/tickets?ticketView={obj_id}"
    if model_label == "tasks.taskmodel":
        return f"{FRONTEND_URL}/?task={obj_id}"
    if model_label == "processes.workflowrequestmodel":
        return f"{FRONTEND_URL}/?approvals={obj_id}"
    return ""


def _tg_ai_build_created_object_caption(intent_obj, created_object):
    if isinstance(created_object, dict):
        caption = str(created_object.get("caption") or "").strip()
        if caption:
            return caption

    model_label = getattr(getattr(created_object, "_meta", None), "label_lower", "")
    name = str(getattr(created_object, "name", "") or "").strip()

    if model_label == "tasks.taskmodel":
        counter = getattr(created_object, "counter", None)
        if counter:
            return f'Задача №{counter} "{name}"' if name else f"Задача №{counter}"
        return f'Задача "{name}"' if name else "Задача"

    if model_label == "event_calendar.eventcalendarmodel":
        return f'Событие "{name}"' if name else "Событие"

    if model_label == "meetings.plannedmeetingmodel":
        return f'Встреча "{name}"' if name else "Встреча"

    if model_label == "help_desk.helpdeskticketmodel":
        number = getattr(created_object, "number", None)
        if number:
            return f"Обращение №{number}"
        return "Обращение"

    if model_label == "processes.workflowrequestmodel":
        number = getattr(created_object, "number", "") or getattr(created_object, "counter", "")
        request_type = getattr(created_object, "request_type", None)
        request_type_name = str(getattr(request_type, "name", "") or "").strip()
        if number and request_type_name:
            return f'Заявка №{number} "{request_type_name}"'
        if number:
            return f"Заявка №{number}"
        return f'Заявка "{request_type_name}"' if request_type_name else "Заявка"

    intent_type = getattr(intent_obj, "intent_type_id", "") or ""
    if intent_type == "create_task":
        return f'Задача "{name}"' if name else "Задача"
    if intent_type == "create_event":
        return f'Событие "{name}"' if name else "Событие"
    if intent_type == "create_meet":
        return f'Встреча "{name}"' if name else "Встреча"
    if intent_type == "create_workflow_request":
        return "Заявка"

    return f'Объект "{name}"' if name else "Объект"


def _tg_ai_handle_dialog_input(message, profile, incoming_text):
    chat_id = message.chat.id
    if not _tg_ai_profile_has_access(profile):
        welcome_bot.send_message(chat_id, TG_AI_ACCESS_DENIED_TEXT)
        return
    progress_message_id = _tg_ai_progress_start(chat_id, "Обрабатываю запрос: анализирую сообщение.")

    try:
        _tg_ai_progress_update(chat_id, progress_message_id, "Обрабатываю запрос: готовлю контекст диалога.")
        state = _tg_ai_get_state(profile.pk)
        if not isinstance(state, dict):
            state = {}
        if not state.get("session_id"):
            state["session_id"] = str(uuid.uuid4())
        if not isinstance(state.get("chunks"), list):
            state["chunks"] = []

        previous_bot_message_id = state.get("last_bot_message_id")
        if previous_bot_message_id:
            _tg_ai_deactivate_intents_for_bot_message(previous_bot_message_id)

        state["chunks"].append((incoming_text or "").strip())
        state["chunks"] = [item for item in state["chunks"] if item]
        if len(state["chunks"]) > 12:
            state["chunks"] = state["chunks"][-12:]
        session_text = "\n".join(state["chunks"]).strip()

        _tg_ai_progress_update(chat_id, progress_message_id, "Обрабатываю запрос: распознаю намерение.")
        intent_label, intents = _tg_ai_classify_and_parse(session_text)
        reply_text = _tg_ai_generate_dialog_reply(session_text, intent_label, intents)
        is_intent = intent_label != "unknown" and bool(intents)

        _tg_ai_progress_update(chat_id, progress_message_id, "Обрабатываю запрос: формирую ответ.")
        chat = _tg_ai_get_or_create_chat(profile)
        user_message = chat_ai_models.AIMessageModel.objects.create(
            chat=chat,
            message_author=profile,
            text=incoming_text,
            is_bot=False,
            status_id="done",
            is_intent=is_intent,
        )
        created_intent_ids = []
        created_intents_debug = []
        request = None
        if is_intent:
            request = _tg_ai_build_request_for_profile(profile)

        debug_payload = _tg_ai_build_debug_payload(
            intent_label=intent_label,
            is_intent=is_intent,
            intents=intents,
            created_intent_ids=[],
            created_intents_debug=[],
            session_chunks=len(state.get("chunks", [])),
        )
        presentable_reply_text = _tg_ai_build_presentable_reply(
            reply_text=reply_text,
            intent_label=intent_label,
            intents=intents,
            created_intents_debug=[],
        )
        reply_text_with_debug = _tg_ai_compose_reply_with_debug(presentable_reply_text, debug_payload)

        bot_message = chat_ai_models.AIMessageModel.objects.create(
            chat=chat,
            message_author=None,
            reply_to=user_message,
            text=reply_text_with_debug,
            is_bot=True,
            status_id="done",
            is_intent=is_intent,
        )

        if is_intent:
            _tg_ai_progress_update(chat_id, progress_message_id, "Обрабатываю запрос: сохраняю намерение.")
            created_intent_ids = _tg_ai_create_intents_for_bot_message(bot_message, intents, request)
            created_intents_debug = _tg_ai_collect_created_intents_debug(created_intent_ids)

        debug_payload["created_intent_ids"] = created_intent_ids
        debug_payload["created_intents_debug"] = created_intents_debug
        presentable_reply_text = _tg_ai_build_presentable_reply(
            reply_text=reply_text,
            intent_label=intent_label,
            intents=intents,
            created_intents_debug=created_intents_debug,
        )
        reply_text_with_debug = _tg_ai_compose_reply_with_debug(presentable_reply_text, debug_payload)
        if bot_message.text != reply_text_with_debug:
            bot_message.text = reply_text_with_debug
            bot_message.save(update_fields=["text"])

        chat.last_sent = timezone.now()
        chat.save(update_fields=["last_sent"])
        _tg_ai_progress_finish(chat_id, progress_message_id, "Готово. Показываю результат.")

        if created_intent_ids:
            state["last_bot_message_id"] = str(bot_message.pk)
            state["last_intent_ids"] = created_intent_ids
            _tg_ai_set_state(profile.pk, state)
            welcome_bot.send_message(
                chat_id=chat_id,
                text=reply_text_with_debug,
                reply_markup=_tg_ai_build_actions_markup(str(bot_message.pk)),
            )
            return

        state["last_bot_message_id"] = None
        state["last_intent_ids"] = []
        _tg_ai_set_state(profile.pk, state)
        welcome_bot.send_message(chat_id=chat_id, text=reply_text_with_debug)
    except Exception:
        _tg_ai_progress_finish(chat_id, progress_message_id, "Не удалось обработать запрос. Попробуйте ещё раз.")
        raise

def get_main_menu(chat_id=None):
    """Создает главное меню бота"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = KeyboardButton("Мои задачи")
    item2 = KeyboardButton("Мои события")
    item3 = KeyboardButton("Мои собрания")

    # Проверяем права доступа к help_desk
    has_help_desk_access = False
    if chat_id:

        profile = profile_model.objects.filter(telegram_id=chat_id).first()
        if profile:
            has_help_desk_access = check_user_app_section_role_permission(profile.pk, 'help_desk')
        else:
            has_help_desk_access = False

    if has_help_desk_access:
        item4 = KeyboardButton("Мои обращения")
        markup.add(item1, item2)  # Первая строка: задачи и события
        markup.add(item3, item4)  # Вторая строка: собрания и обращения
    else:
        markup.add(item1, item2, item3)  # Все кнопки в обычном порядке

    return markup


def send_with_menu(chat_id, text, parse_mode=None, reply_markup=None):
    """
    Отправляет сообщение с автоматическим обновлением главного меню.
    Если reply_markup не указан, добавляет главное меню.
    """
    if reply_markup is None:
        reply_markup = get_main_menu(chat_id)

    welcome_bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup
    )


def hex_to_emoji(hex_color):
    try:
        color = hex_color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    except Exception:
        return '•'
    candidates = [
        ((255, 59, 48), '🔴'),
        ((52, 199, 89), '🟢'),
        ((0, 122, 255), '🔵'),
        ((255, 204, 0), '🟡'),
        ((175, 82, 222), '🟣'),
        ((142, 142, 147), '⚪')
    ]

    def dist(c):
        return (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2

    emoji = min(candidates, key=lambda x: dist(x[0]))[1]
    return emoji


def sanitize_html_for_telegram(html_text: str) -> str:
    if not html_text:
        return ''
    text = html_text
    # Normalize breaks/paragraphs
    text = re.sub(r'<\s*br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</\s*p\s*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*p\s*>', '', text, flags=re.IGNORECASE)
    # Strong/emphasis to Telegram supported tags
    replacements = [
        (r'<\s*strong\s*>', '<b>'), (r'</\s*strong\s*>', '</b>'),
        (r'<\s*em\s*>', '<i>'), (r'</\s*em\s*>', '</i>'),
        (r'<\s*u\s*>', '<u>'), (r'</\s*u\s*>', '</u>'),
        (r'<\s*s\s*>', '<s>'), (r'</\s*s\s*>', '</s>'),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # Simplify links, keep only href and inner text
    def _link_sub(m):
        href = m.group(1)
        inner = m.group(2)
        return f'<a href="{href}">{inner}</a>'

    text = re.sub(r'<\s*a[^>]*href\s*=\s*"([^"]+)"[^>]*>(.*?)</\s*a\s*>', _link_sub, text,
                  flags=re.IGNORECASE | re.DOTALL)
    # Drop other tags
    text = re.sub(r'<[^>]+>', '', text)
    return text


@welcome_bot.message_handler(regexp=r'^/start\s+')
def start(message):
    chat_id = message.chat.id
    token = message.text.split(' ')[-1]
    profile = None

    try:
        profile = profile_model.objects.get(telegram_connect_token=token)
    except ObjectDoesNotExist:
        welcome_bot.send_message(chat_id=chat_id,
                                 text='Пользователь не найден.')
    if profile:
        profile_model.objects.filter(telegram_id=chat_id).update(
            telegram_id=None)  # Добавлено 21.10.2025 Чтобы telegram_id был уникальным.
        profile.telegram_id = chat_id
        profile.save()

        welcome_message = 'Добро пожаловать!\nПрофиль успешно подтвержден'

        send_with_menu(chat_id=chat_id, text=welcome_message)


@welcome_bot.message_handler(commands=['start', ])
def start_handler(message):
    send_with_menu(
        chat_id=message.chat.id,
        text=('Чтобы подключить бота авторизуйтесь '
              f'на {FRONTEND_URL} и перейдите по ссылке-приглашению')
    )


@welcome_bot.message_handler(commands=['stop', ])
def stop_handle(message):
    chat_id = message.chat.id

    profiles = profile_model.objects.filter(
        telegram_id=chat_id
    )
    profiles.update(telegram_id=None)

    send_with_menu(
        chat_id=message.chat.id,
        text=('Вы больше не будете получать уведомления в этом чате')
    )


@welcome_bot.message_handler(func=lambda message: message.text == "Мои задачи")
def my_tasks_handler(message):
    chat_id = message.chat.id
    welcome_bot.send_chat_action(chat_id, 'typing')

    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Показываем кнопки фильтрации по статусам
    welcome_bot.send_message(
        chat_id=chat_id,
        text="Выберите статус задач для просмотра:",
        reply_markup=get_tasks_filter_menu()
    )


def get_tasks_by_status(profile, status_code=None):
    """Получает задачи по статусу"""
    # Базовый queryset: я исполнитель или соисполнитель; только обычные задачи
    qs = (TaskModel.objects
          .filter(is_active=True, task_type_id='task')
          .filter(Q(operator=profile) | Q(cooperators=profile)))

    # Дополнительная фильтрация по статусу если указан
    if status_code:
        qs = qs.filter(status_id=status_code)
    else:
        # Если статус не указан, исключаем завершённые
        qs = qs.filter(status__task_status_type__is_complete=False)

    qs = filter_by_permissions(qs, profile)
    qs = qs.select_related('project', 'status') \
        .order_by('project__name', 'dead_line', '-priority', 'counter') \
        .distinct()

    return qs


def show_tasks_with_filter(chat_id, status_code=None):
    """
    Показывает задачи пользователя с фильтрацией по статусу.

    Args:
        chat_id: ID чата в телеграм
        status_code: Код статуса для фильтрации (None = все статусы)
    """
    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Получаем задачи пользователя
    qs = get_tasks_by_status(profile, status_code)

    if qs.count() == 0:
        if not status_code:
            status_name = "всех статусов"
        else:
            # Получаем название статуса из базы данных

            try:
                status_obj = TaskStatusModel.objects.get(code=status_code, is_active=True)
                status_display_name = status_obj.name
            except TaskStatusModel.DoesNotExist:
                status_display_name = status_code
            status_name = f"в статусе '{status_display_name}'"
        send_with_menu(chat_id, f"У вас нет задач {status_name}")
        return

    # Отправляем заголовок
    if not status_code:
        status_name = "всех статусов"
    else:

        try:
            status_obj = TaskStatusModel.objects.get(code=status_code, is_active=True)
            status_display_name = status_obj.name
        except TaskStatusModel.DoesNotExist:
            status_display_name = status_code
        status_name = f"в статусе '{status_display_name}'"

    # спользуем существующую функцию send_tasks_list
    send_tasks_list(chat_id, qs, status_name)

    # Автоматически возвращаемся в главное меню после показа задач
    send_with_menu(chat_id, "Выберите действие:")


def send_tasks_list(chat_id, qs, status_name="Все задачи"):
    """Отправляет список задач"""
    if qs.count() == 0:
        welcome_bot.send_message(chat_id, f"Задач со статусом '{status_name}' нет")
        return

    # Список проектов
    project_id_to_name = {}
    for pid, pname in qs.values_list('project_id', 'project__name').distinct():
        project_id_to_name[pid] = pname or 'Без проекта'

    # Краткая сводка
    status_counts = get_tasks_status_count(qs)  # ожидается dict с ключевыми статусами
    projects_total = len(project_id_to_name)

    # Получаем названия и цвета статусов из TaskStatusModel

    status_data = {status.code: {'name': status.name, 'color': status.color} for status in
                   TaskStatusModel.objects.filter(is_active=True)}

    # Формируем строки статистики
    total_tasks = sum(count for status_code, count in status_counts.items() if status_code != 'overdue')
    overdue_count = status_counts.get('overdue', 0)

    summary_lines = [f"Проектов: {projects_total}"]
    summary_lines.append(f"Задач: {total_tasks}, из них просроченных: {overdue_count}")
    summary_lines.append("Статусы:")

    for status_code, count in status_counts.items():
        if count > 0 and status_code != 'overdue':
            status_info = status_data.get(status_code, {})
            status_name = status_info.get('name', status_code)
            status_color = status_info.get('color', 'default')
            emoji = status_color_to_emoji(status_color)
            summary_lines.append(f"{emoji} {status_name}: {count}")

    summary_line = "\n".join(summary_lines)

    # Выводим через HTML-спойлеры (совместимо со всеми клиентами)
    chunks = []
    for pid, pname in project_id_to_name.items():
        project_qs = qs.filter(project_id=pid)
        header = f"📁 <b>{pname or 'Без проекта'}</b> ({project_qs.count()})"
        lines = []
        for task in project_qs[:100]:
            fire = '🔥 ' if task.priority >= 4 else ''
            dot = status_color_to_emoji(getattr(task.status, 'color', ''))
            status_name = getattr(task.status, 'name', '') or ''
            counter = f"#{str(task.counter).zfill(5)}"
            name = task.name or ''
            deadline_str = ''
            if task.dead_line:
                dl_str = task.dead_line.strftime('%d.%m')
                overdue_prefix = ''
                try:
                    if task.dead_line < timezone.now():
                        overdue_prefix = '❗ '
                except Exception:
                    pass
                deadline_str = f" ({overdue_prefix}до {dl_str})"
            task_url = f"{FRONTEND_URL}/?task={task.id}"
            lines.append(f"- {fire}{dot} {status_name} — <a href=\"{task_url}\">{counter} {name}</a>{deadline_str}")
        body = "\n".join(lines) if lines else "Задач нет"
        chunks.append(header + "\n" + body)

    one_message = "\n\n".join(chunks) if chunks else "Задач нет"

    # делим по лимиту Telegram 4096 символов
    if len(one_message) <= 4096:
        welcome_bot.send_message(chat_id, one_message, parse_mode='HTML')
    else:
        # Разбиваем по проектам, чтобы не разрывать HTML-теги
        for chunk in chunks:
            if len(chunk) <= 4096:
                welcome_bot.send_message(chat_id, chunk, parse_mode='HTML')
            else:
                # Если один проект слишком большой, разбиваем по задачам
                lines = chunk.split('\n')
                current_chunk = lines[0] + '\n'  # заголовок проекта
                for line in lines[1:]:
                    if len(current_chunk + line + '\n') <= 4000:
                        current_chunk += line + '\n'
                    else:
                        if current_chunk.strip():
                            welcome_bot.send_message(chat_id, current_chunk.strip(), parse_mode='HTML')
                        current_chunk = lines[0] + '\n' + line + '\n'
                if current_chunk.strip():
                    welcome_bot.send_message(chat_id, current_chunk.strip(), parse_mode='HTML')

    welcome_bot.send_message(chat_id, summary_line)


def status_color_to_emoji(color_name: str) -> str:
    mapping = {
        'blue': '🔵',
        'cyan': '🟢',
        'default': '⚪',
        'grey': '⚫',
        'geekblue': '🔵',
        'green': '🟢',
        'orange': '🟠',
        'brown': '🟠',
        'pink': '🟣',
        'purple': '🟣',
        'red': '🔴',
        'yellow': '🟡',
        'black': '⚫',
    }

    return mapping.get((color_name or '').lower(), '🔵')


def get_priority_emoji(priority_code: str) -> str:
    """Возвращает эмоджи для приоритета тикета"""
    priority_emojis = {
        '0': '⏳',  # Очень низкий - песочные часы
        '1': '🕐',  # Низкий - часы
        '2': '⚠️',  # Обычный - восклицательный знак
        '3': '⚡',  # Высокий - молния
        '4': '🔥',  # Очень высокий - огонь
    }
    return priority_emojis.get(priority_code, '⚠️')


def meeting_status_to_emoji(status: str) -> str:
    """Преобразует статус собрания в эмоджи"""
    mapping = {
        'new': '🔵',  # синий
        'online': '🔴',  # красный
        'ended': '🟣',  # фиолетовый
    }
    return mapping.get(status, '⚪')

    # Убрали callback-режим; выводим разворачиваемые блоки сообщениями со spoiler


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith("task_status_set_"))
def check_task_handler(call):
    statuses = {
        'oncheck': ['on_check', 'на проверку'],
        'inwork': ['in_work', 'в работу']
    }
    task_id = call.data.split("_")[4]
    chat_id = call.message.chat.id
    welcome_bot.send_chat_action(chat_id, 'typing')
    message_id = call.message.message_id
    profile = profile_model.objects.filter(
        telegram_id=chat_id
    ).first()

    if profile:
        target_task = profile.operator_tasks.filter(status__task_status_type__is_complete=False,
                                                    id=task_id).first()
        target_task.status_id = statuses[call.data.split("_")[3]][0]

        try:
            target_task.save()
            async_task(notifications.notify_about_new_status, str(target_task.pk), statuses[call.data.split("_")[3]][0],
                       str(profile.pk))
            welcome_bot.send_message(chat_id=chat_id,
                                     text=f"Задача № {target_task.counter} отправлена {statuses[call.data.split('_')[3]][1]}")
            welcome_bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=call.message.text)
        except:
            welcome_bot.send_message(chat_id=chat_id,
                                     text=f"ВНМАНЕ! Не удалось сменить статус! Обратитесь к администратору.")
        return

    welcome_bot.send_message(chat_id=chat_id,
                             text=f"Понятия не имею, как к Вам попала эта кнопка, но ничего не произошло. Возможно, Вы когда-то были ответственным за эту задачу")


@welcome_bot.message_handler(func=lambda message: message.text == "Мои события")
def my_events_handler(message):
    chat_id = message.chat.id
    welcome_bot.send_chat_action(chat_id, 'typing')
    profile = profile_model.objects.filter(
        telegram_id=chat_id
    ).first()

    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Определяем интервал [сегодня 00:00; завтра 00:00) относительно локального времени
    today_local_date = timezone.localtime(timezone.now()).date()
    tz = timezone.get_current_timezone()
    start_range = timezone.make_aware(datetime.combine(today_local_date, time.min), tz)
    end_range = timezone.make_aware(datetime.combine(today_local_date + timedelta(days=1), time.min), tz)

    events_qs = EventCalendarModel.objects.filter(
        Q(author=profile) | Q(members=profile),
        is_active=True,
        calendar__is_active=True,
        is_finished=False,
    ).filter(
        Q(start_at__lt=end_range) & Q(end_at__gt=start_range)
    ).order_by('start_at', 'created_at').distinct()

    if events_qs.count() == 0:
        send_with_menu(chat_id, "На сегодня событий нет")
        return

    buttons = []
    for event in events_qs:
        if event.all_day:
            time_text = "Весь день"
        else:
            local_start = timezone.localtime(event.start_at)
            local_end = timezone.localtime(event.end_at)
            time_text = f"{local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}"

        emoji = hex_to_emoji(getattr(event, 'color', ''))
        title = f"{time_text} {emoji} {event.name}".strip()
        # Telegram inline button text limit ~64 chars
        if len(title) > 64:
            title = title[:61] + '…'
        buttons.append(InlineKeyboardButton(text=title, callback_data=f"event_detail_{event.id}"))

    # Сначала отправляем сообщение с главным меню
    send_with_menu(chat_id, "События на сегодня:")

    # Затем отправляем inline кнопки отдельным сообщением
    if buttons:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(*buttons)
        welcome_bot.send_message(
            chat_id=chat_id,
            text="Выберите событие:",
            reply_markup=markup
        )


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith("event_detail_"))
def event_detail_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    welcome_bot.send_chat_action(chat_id, 'typing')
    event_id = call.data.split('_')[-1]

    profile = profile_model.objects.filter(telegram_id=chat_id).first()
    if not profile:
        welcome_bot.answer_callback_query(call.id, "Профиль не найден")
        return

    event = EventCalendarModel.objects.filter(
        Q(author=profile) | Q(members=profile),
        is_active=True,
        calendar__is_active=True,
        pk=event_id
    ).distinct().first()

    if not event:
        welcome_bot.answer_callback_query(call.id, "Событие недоступно")
        return

    # Format detail text
    emoji = hex_to_emoji(getattr(event, 'color', ''))
    title_line = f"{emoji} {event.name}".strip()

    local_start = timezone.localtime(event.start_at)
    local_end = timezone.localtime(event.end_at)

    weekdays = [
        'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'
    ]
    months = [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]
    weekday = weekdays[local_start.weekday()]
    date_str = f"{local_start.day:02d} {months[local_start.month - 1]}"
    if event.all_day:
        when_line = f"{weekday}, {date_str} Весь день"
    else:
        when_line = f"{weekday}, {date_str} {local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}"

    participants_qs = list(event.members.all())
    participants = [p.user.get_short_name() for p in participants_qs if getattr(p, 'user', None)]

    # Escape unsafe parts as we will use HTML parse mode
    safe_title = title_line  # title_line уже содержит HTML-теги
    safe_when = when_line  # убираем жирное форматирование для даты
    safe_description = sanitize_html_for_telegram(event.description)
    # Убираем только хвостовые переносы/пробелы, чтобы не раздувать отступ перед блоком участников
    if safe_description:
        safe_description = safe_description.rstrip()
    if not safe_description:
        safe_description = '—'

    # Participants as a bullet list
    participants_items = []
    for name in [p for p in participants if p]:
        participants_items.append(f"• {name}")
    participants_list = '\n'.join(participants_items) if participants_items else '—'

    # Tighter layout: no extra blank lines, bold date with calendar emoji
    detail_html = (
        f"{safe_title}\n"
        f"📅 <b>{safe_when}</b>\n"
        f"<b>Описание:</b> {safe_description}\n"
        f"<b>Участники:</b>\n{participants_list}"
    )

    # Rebuild inline keyboard to keep event list (1 column) and add a big "Открыть" button
    existing_markup = call.message.reply_markup
    new_markup = InlineKeyboardMarkup(row_width=1)
    event_url = f"{FRONTEND_URL}?event={event.id}"
    # First row: primary action
    new_markup.add(InlineKeyboardButton(text="Открыть", url=event_url))
    try:
        rows = getattr(existing_markup, 'keyboard', None) or getattr(existing_markup, 'inline_keyboard', [])
        flat_buttons = []
        for row in rows:
            for btn in row:
                # reuse only event list buttons (callback ones), skip any previous URL buttons
                callback_data = getattr(btn, 'callback_data', '')
                if isinstance(callback_data, str) and callback_data.startswith('event_detail_'):
                    flat_buttons.append(btn)
        if flat_buttons:
            new_markup.add(*flat_buttons)
    except Exception:
        pass

    try:
        welcome_bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=detail_html, parse_mode='HTML',
                                      reply_markup=new_markup, disable_web_page_preview=True)
    except Exception:
        welcome_bot.send_message(chat_id=chat_id, text=detail_html, parse_mode='HTML', reply_markup=new_markup,
                                 disable_web_page_preview=True)


def get_tickets_filter_menu():
    """Создает меню фильтрации обращений"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton("Все"),
        KeyboardButton("Новые"),
        KeyboardButton("В работе"),
        KeyboardButton("На паузе"),
        KeyboardButton("На доработке"),
        KeyboardButton("Назад")
    )
    return markup


def get_tasks_filter_menu():
    """Создает меню фильтрации задач"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton("Все задачи"),
        KeyboardButton("Новые задачи"),
        KeyboardButton("Задачи в работе"),
        KeyboardButton("На проверке"),
        KeyboardButton("Задачи на доработке"),
        KeyboardButton("Назад")
    )
    return markup


@welcome_bot.message_handler(func=lambda message: message.text == "Мои обращения")
def my_tickets_handler(message):
    chat_id = message.chat.id
    welcome_bot.send_chat_action(chat_id, 'typing')

    profile = profile_model.objects.filter(telegram_id=chat_id).first()
    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Показываем кнопки фильтрации по статусам
    welcome_bot.send_message(
        chat_id=chat_id,
        text="Выберите статус обращений для просмотра:",
        reply_markup=get_tickets_filter_menu()
    )


def show_tickets_with_filter(chat_id, status_code=None):
    """
    Показывает обращения пользователя с фильтрацией по статусу.

    Args:
        chat_id: ID чата в телеграм
        status_code: Код статуса для фильтрации (None = все статусы)
    """
    profile = profile_model.objects.filter(telegram_id=chat_id).first()
    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Получаем обращения пользователя

    tickets_qs = profile.help_desk_tickets.filter(
        is_active=True
    ).select_related('status', 'category', 'priority').order_by('-created_at')

    # Применяем фильтр по статусу если указан
    if status_code:
        tickets_qs = tickets_qs.filter(status_id=status_code)

    if tickets_qs.count() == 0:
        if not status_code:
            status_name = "всех статусов"
        else:
            status_display_name = TICKET_STATUS_NAMES.get(status_code, status_code)
            status_name = f"в статусе '{status_display_name}'"
        send_with_menu(chat_id, f"У вас нет обращений {status_name}")
        return

    # Отправляем заголовок
    if not status_code:
        status_name = "всех статусов"
    else:
        status_display_name = TICKET_STATUS_NAMES.get(status_code, status_code)
        status_name = f"в статусе '{status_display_name}'"
    send_with_menu(chat_id, f"Ваши обращения {status_name}:")

    # Отправляем каждое обращение отдельным сообщением
    for ticket in tickets_qs:
        status_color = ticket.status.color
        status_emoji = status_color_to_emoji(status_color)

        ticket_url = f"{FRONTEND_URL}/helpdesk/tickets?ticketView={ticket.id}"

        # Получаем иконку приоритета
        priority_emoji = "⚠️"  # По умолчанию
        if hasattr(ticket, 'priority') and ticket.priority:
            priority_code = getattr(ticket.priority, 'code', '2')
            priority_emoji = get_priority_emoji(priority_code)

        # Основная информация (видимая) - статус + приоритет + номер + название
        ticket_number = f"#{ticket.number}" if ticket.number else ""
        main_text = f"{status_emoji} {priority_emoji} {ticket_number} {ticket.name or 'Без названия'}"

        # Подробная информация (в expandable_blockquote)
        details = []

        # Контактное лицо
        if ticket.contact_person:
            cp = ticket.contact_person
            post_inst = cp.post_inst
            if post_inst:
                post_name = post_inst.name
            else:
                post_name = ''
            contact_info = [
                f"мя: {cp.name}",
                # f"Должность: {post_name}",
                # f"Телефон: {cp.phone}",
                # f"Email: {cp.email}"
            ]
            details.append("👤 Контактное лицо:\n" + "\n".join(contact_info))

        # Клиент
        if ticket.customer_card:
            details.append(f"🏢 Клиент: {ticket.customer_card.name}")

        # Категория
        if ticket.category:
            details.append(f"📂 Категория: {ticket.category.name}")

        # Приоритет
        priority_code = ticket.priority.code
        priority_name = ticket.priority.name
        priority_emoji = get_priority_emoji(priority_code)

        details.append(f"{priority_emoji} Приоритет: {priority_name}")

        # Дата создания
        local_created = timezone.localtime(ticket.created_at)
        created_str = local_created.strftime('%d.%m.%Y %H:%M')
        details.append(f"📅 Создано: {created_str}")

        # Крайний срок
        if ticket.dead_line:
            local_deadline = timezone.localtime(ticket.dead_line)
            deadline_str = local_deadline.strftime('%d.%m.%Y %H:%M')
            details.append(f"⏰ Крайний срок: {deadline_str}")

        # SLA
        try:
            sla_value = ticket.sla_value
        except ObjectDoesNotExist:
            pass
        else:
            sla_color = sla_value.sla.color
            if sla_color:
                sla_color_emoji = status_color_to_emoji(sla_color)
            else:
                sla_color_emoji = ''
            details.append(f"{sla_color_emoji} SLA: {sla_value.sla.name}:")
            first_reaction_time = sla_value.first_reaction_time
            if first_reaction_time:
                first_reaction_time_str = get_sla_duration(first_reaction_time)
                first_reaction = f"⏱ Время реагирования: {first_reaction_time_str}"
                receipt_date = ticket.receipt_date
                if receipt_date:
                    in_work_to = receipt_date + timedelta(seconds=first_reaction_time)
                    in_work_to_str = timezone.localtime(in_work_to).strftime('%d.%m.%Y %H:%M')
                    first_reaction = first_reaction + f" (взять в работу до {in_work_to_str})"
                details.append(first_reaction)
            solve_time = sla_value.solve_time
            if solve_time:
                details.append(f"⌛ Время первой реакции: {get_sla_duration(solve_time)}")

        # Объединяем подробную информацию
        details_text = "\n\n".join(details) if details else "Подробная информация недоступна"

        # Формируем итоговое сообщение с expandable_blockquote и URL внизу
        full_text = f"{main_text}\n{details_text}\n{ticket_url}"

        # Создаем entities для expandable_blockquote

        entities = []
        if details_text:
            # Находим позицию начала и конца текста цитаты в UTF-16 символах
            main_text_utf16 = len(main_text.encode('utf-16le')) // 2
            quote_start = main_text_utf16 + 1  # +1 для \n
            # спользуем длину details_text в UTF-16 символах
            quote_length = len(details_text.encode('utf-16le')) // 2

            entities.append(MessageEntity(
                type="expandable_blockquote",
                offset=quote_start,
                length=quote_length
            ))

        # # Добавляем URL entity - используем фактическую позицию в full_text
        # url_start = full_text.find(ticket_url)
        # url_length = len(ticket_url)
        # if url_start >= 0:  # Проверяем, что URL найден
        #     entities.append(MessageEntity(
        #         type="url",
        #         offset=url_start,
        #         length=url_length
        #     ))
        # Добавляем URL entity — позицию/длину считаем в UTF-16 code units (как требует Telegram)
        url_start_utf16 = _utf16_find(full_text, ticket_url)
        url_len_utf16 = _utf16_len(ticket_url)

        if url_start_utf16 >= 0:
            entities.append(MessageEntity(
                type="url",
                offset=url_start_utf16,
                length=url_len_utf16
            ))
        # Создаем кнопки для смены статуса
        markup = get_ticket_status_buttons(ticket)
        costs_button = get_costs_button(ticket.pk)
        if costs_button:
            markup.add(costs_button)
        # Отправляем одно сообщение с entities и кнопками
        welcome_bot.send_message(
            chat_id=chat_id,
            text=full_text,
            parse_mode=None,  # Отключаем HTML парсинг, используем entities
            entities=entities,
            reply_to_message_id=None,
            reply_markup=markup
        )

    if tickets_qs.count() > 10:
        send_with_menu(chat_id, f"... и еще {tickets_qs.count() - 10} обращений")


def get_sla_duration(duration_sec):
    duration_min = duration_sec // 60
    duration_str = f"{duration_min} мин"
    duration_remainder = duration_sec % 60
    if duration_remainder:
        duration_str = duration_str + f" {duration_remainder} сек"
    return duration_str


# Обработчики для обращений
@welcome_bot.message_handler(func=lambda message: message.text == "Все")
def all_tickets_handler(message):
    """Показывает все обращения"""
    show_tickets_with_filter(message.chat.id, None)


@welcome_bot.message_handler(func=lambda message: message.text == "Новые")
def new_tickets_handler(message):
    """Показывает новые обращения"""
    show_tickets_with_filter(message.chat.id, 'new')


@welcome_bot.message_handler(func=lambda message: message.text == "В работе")
def in_work_tickets_handler(message):
    """Показывает обращения в работе"""
    show_tickets_with_filter(message.chat.id, 'in_work')


@welcome_bot.message_handler(func=lambda message: message.text == "На паузе")
def on_pause_tickets_handler(message):
    """Показывает обращения на паузе"""
    show_tickets_with_filter(message.chat.id, 'on_pause')


@welcome_bot.message_handler(func=lambda message: message.text == "На доработке")
def on_rework_tickets_handler(message):
    """Показывает обращения на доработке"""
    show_tickets_with_filter(message.chat.id, 'on_rework')


@welcome_bot.message_handler(func=lambda message: message.text == "Назад")
def back_to_main_menu_handler(message):
    """Возврат в основное меню"""
    send_with_menu(message.chat.id, "Выберите действие:")


@welcome_bot.message_handler(func=lambda message: message.text == "На проверке")
def on_check_tasks_handler(message):
    """Показывает задачи на проверке"""
    show_tasks_with_filter(message.chat.id, 'on_check')


# Обработчики для задач (отдельные функции с уникальными названиями кнопок)
@welcome_bot.message_handler(func=lambda message: message.text == "Все задачи")
def all_tasks_handler(message):
    """Показывает все задачи"""
    show_tasks_with_filter(message.chat.id, None)


@welcome_bot.message_handler(func=lambda message: message.text == "Новые задачи")
def new_tasks_handler(message):
    """Показывает новые задачи"""
    show_tasks_with_filter(message.chat.id, 'new')


@welcome_bot.message_handler(func=lambda message: message.text == "Задачи в работе")
def in_work_tasks_handler(message):
    """Показывает задачи в работе"""
    show_tasks_with_filter(message.chat.id, 'in_work')


@welcome_bot.message_handler(func=lambda message: message.text == "Задачи на доработке")
def on_rework_tasks_handler(message):
    """Показывает задачи на доработке"""
    show_tasks_with_filter(message.chat.id, 'on_rework')


@welcome_bot.message_handler(func=lambda message: message.text == "Мои собрания")
def my_meetings_handler(message):
    chat_id = message.chat.id
    welcome_bot.send_chat_action(chat_id, 'typing')
    profile = profile_model.objects.filter(
        telegram_id=chat_id
    ).first()

    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Определяем интервал [сегодня 00:00; завтра 00:00) относительно локального времени
    today_local_date = timezone.localtime(timezone.now()).date()
    tz = timezone.get_current_timezone()
    start_range = timezone.make_aware(datetime.combine(today_local_date, time.min), tz)
    end_range = timezone.make_aware(datetime.combine(today_local_date + timedelta(days=1), time.min), tz)

    meetings_qs = PlannedMeetingModel.objects.filter(
        Q(author=profile) | Q(members=profile),
        is_active=True,
    ).filter(
        Q(date_begin__lt=end_range) & Q(date_begin__gte=start_range)
    ).order_by('date_begin', 'created_at').distinct()

    if meetings_qs.count() == 0:
        send_with_menu(chat_id, "На сегодня собраний нет")
        return

    buttons = []
    for meeting in meetings_qs:
        if meeting.date_begin:
            local_start = timezone.localtime(meeting.date_begin)
            time_text = local_start.strftime('%H:%M')
        else:
            time_text = "Время не указано"

        emoji = meeting_status_to_emoji(meeting.status)
        title = f"{time_text} {emoji} {meeting.name}".strip()
        # Telegram inline button text limit ~64 chars
        if len(title) > 64:
            title = title[:61] + '…'
        buttons.append(InlineKeyboardButton(text=title, callback_data=f"meeting_detail_{meeting.id}"))

    # Сначала отправляем сообщение с главным меню
    send_with_menu(chat_id, "Собрания на сегодня:")

    # Затем отправляем inline кнопки отдельным сообщением
    if buttons:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(*buttons)
        welcome_bot.send_message(
            chat_id=chat_id,
            text="Выберите собрание:",
            reply_markup=markup
        )


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith("meeting_detail_"))
def meeting_detail_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    welcome_bot.send_chat_action(chat_id, 'typing')
    meeting_id = call.data.split('_')[-1]

    profile = profile_model.objects.filter(telegram_id=chat_id).first()
    if not profile:
        welcome_bot.answer_callback_query(call.id, "Профиль не найден")
        return

    meeting = PlannedMeetingModel.objects.filter(
        Q(author=profile) | Q(members=profile),
        is_active=True,
        pk=meeting_id
    ).distinct().first()

    if not meeting:
        welcome_bot.answer_callback_query(call.id, "Собрание недоступно")
        return

    # Format detail text
    emoji = meeting_status_to_emoji(meeting.status)
    # Получаем перевод статуса из STATUS_CHOICES
    status_translations = {
        'new': 'Новое',
        'online': 'Онлайн',
        'ended': 'Завершено'
    }
    status_name = status_translations.get(meeting.status, meeting.status)
    title_line = f"<b>{meeting.name}</b> {emoji} {status_name}".strip()

    if meeting.date_begin:
        local_start = timezone.localtime(meeting.date_begin)
        weekdays = [
            'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'
        ]
        months = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        ]
        weekday = weekdays[local_start.weekday()]
        date_str = f"{local_start.day:02d} {months[local_start.month - 1]}"
        when_line = f"{weekday}, {date_str} {local_start.strftime('%H:%M')}"
    else:
        when_line = "Время не указано"

    participants_qs = list(meeting.members.all())
    participants = [p.user.get_short_name() for p in participants_qs if getattr(p, 'user', None)]

    # Escape unsafe parts as we will use HTML parse mode
    safe_title = title_line  # title_line уже содержит HTML-теги
    safe_when = when_line  # убираем жирное форматирование для даты
    safe_description = sanitize_html_for_telegram(meeting.description)
    # Убираем только хвостовые переносы/пробелы, чтобы не раздувать отступ перед блоком участников
    if safe_description:
        safe_description = safe_description.rstrip()
    if not safe_description:
        safe_description = '—'

    # Participants as a bullet list
    participants_items = []
    for name in [p for p in participants if p]:
        participants_items.append(f"• {name}")
    participants_list = '\n'.join(participants_items) if participants_items else '—'

    # Tighter layout: no extra blank lines, bold date with calendar emoji
    detail_html = (
        f"{safe_title}\n"
        f"📅 <b>{safe_when}</b>\n"
        f"<b>Описание:</b> {safe_description}\n"
        f"<b>Участники:</b>\n{participants_list}"
    )

    # Rebuild inline keyboard to keep meeting list (1 column) and add action buttons
    existing_markup = call.message.reply_markup
    new_markup = InlineKeyboardMarkup(row_width=2)
    meeting_url = f"{FRONTEND_URL}?meeting={meeting.id}"

    # First row: action buttons - показываем кнопку "Подключиться" только для статусов new и online
    action_buttons = [InlineKeyboardButton(text="Открыть", url=meeting_url)]
    if meeting.status in ['new', 'online']:
        meeting_connect_url = get_invite_link(meeting.invite_link)
        action_buttons.append(InlineKeyboardButton(text="Подключиться", url=meeting_connect_url))

    new_markup.add(*action_buttons)
    try:
        rows = getattr(existing_markup, 'keyboard', None) or getattr(existing_markup, 'inline_keyboard', [])
        flat_buttons = []
        for row in rows:
            for btn in row:
                # reuse only meeting list buttons (callback ones), skip any previous URL buttons
                callback_data = getattr(btn, 'callback_data', '')
                if isinstance(callback_data, str) and callback_data.startswith('meeting_detail_'):
                    flat_buttons.append(btn)
        if flat_buttons:
            new_markup.add(*flat_buttons)
    except Exception:
        pass

    try:
        welcome_bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=detail_html, parse_mode='HTML',
                                      reply_markup=new_markup, disable_web_page_preview=True)
    except Exception:
        welcome_bot.send_message(chat_id=chat_id, text=detail_html, parse_mode='HTML', reply_markup=new_markup,
                                 disable_web_page_preview=True)


def get_ticket_status_buttons(ticket):
    """Создает кнопки для смены статуса тикета в зависимости от текущего статуса."""
    current_status_code = ticket.status_id
    buttons = []
    if current_status_code == 'new':
        buttons.append([InlineKeyboardButton("В работу", callback_data=f"ticket_status__{ticket.id}__in_work")])
    elif current_status_code == 'in_work':
        buttons.append([
            InlineKeyboardButton("На паузу", callback_data=f"ticket_status__{ticket.id}__on_pause"),
            InlineKeyboardButton("Завершить", callback_data=f"ticket_status__{ticket.id}__completed")
        ])
    elif current_status_code == 'on_pause':
        buttons.append([InlineKeyboardButton("В работу", callback_data=f"ticket_status__{ticket.id}__in_work")])
    elif current_status_code == 'on_rework':
        buttons.append([InlineKeyboardButton("В работу", callback_data=f"ticket_status__{ticket.id}__in_work")])

    if buttons:
        return InlineKeyboardMarkup(buttons)
    return None


def get_costs_button(ticket_id):
    """
    Возвращает кнопку со ссылкой миниапп на материальные затраты тикета
    или None, если TG_MINI_APP_URL отсутствует
    """
    if TG_MINI_APP_URL:
        redirect_to = f"/api/v1/help_desk/{ticket_id}/help_desk_costs/"
        web_app_info = WebAppInfo(url=f'{TG_MINI_APP_URL}?redirect_to={redirect_to}')
        button = InlineKeyboardButton(
            text="📝 Расходники",
            web_app=web_app_info
        )
        return button
    else:
        return None


def change_ticket_status_from_telegram(ticket_id, chat_id, status_code, call_id=None, assign_specialist=False):
    """Универсальная функция для смены статуса тикета из телеграм бота."""
    try:
        ticket = HelpDeskTicketModel.objects.select_related('status').get(id=ticket_id, is_active=True)
    except HelpDeskTicketModel.DoesNotExist:
        if call_id:
            try:
                welcome_bot.answer_callback_query(call_id, show_alert=True, text=f"Заявка #{ticket_id} не найдена.")
            except Exception:
                pass
        return False

    profile = profile_model.objects.filter(telegram_id=chat_id).first()
    if not profile:
        if call_id:
            try:
                welcome_bot.answer_callback_query(
                    call_id, show_alert=True,
                    text="Профиль пользователя не найден."
                )
            except Exception:
                pass
        return False
    with user_context(profile.user):
        try:
            help_desk_utils.change_ticket_status(ticket, profile, status_code, assign_specialist)
        except Exception as ex:
            logging.exception("*******ERROR: change_ticket_status*******")
            if call_id:
                try:
                    welcome_bot.answer_callback_query(
                        call_id, show_alert=True,
                        text=f"Не удалось изменить статус обращения: {ex}"
                    )
                except Exception:
                    pass
        else:
            # Получаем название нового статуса для сообщения
            try:
                new_status = HelpDeskTicketStatusModel.objects.get(code=status_code, is_active=True)
                status_name = new_status.name
            except HelpDeskTicketStatusModel.DoesNotExist:
                status_name = status_code

            if call_id:
                try:
                    welcome_bot.answer_callback_query(
                        call_id,
                        text=f"Обращение №{ticket.number} переведено в статус \"{status_name}\"."
                    )
                except Exception:
                    pass


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith("newtick_"))
def newtick_handler(call):
    """Обработчик кнопки 'В работу' из уведомлений ticket_new_for_specialists"""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    ticket_id = call.data.split("_", 1)[-1]  # извлекаем ID после newtick_

    # Сразу уберём клавиатуру у сообщения, чтобы нельзя было жать повторно
    try:
        welcome_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception:
        # Если не получилось (например, сообщение уже отредактировано) — игнорируем
        pass

    # спользуем универсальную функцию для смены статуса
    change_ticket_status_from_telegram(ticket_id, chat_id, 'in_work', call.id, assign_specialist=True)


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith("ticket_status__"))
def ticket_status_handler(call):
    """Обработчик кнопок смены статуса тикета из списка 'Мои обращения'"""

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    parts = call.data.split("__")
    ticket_id = parts[1]
    status_code = parts[2]

    try:
        welcome_bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception:
        pass

    change_ticket_status_from_telegram(ticket_id, chat_id, status_code, call.id)


# --- ОБРАБОТЧК ОТВЕТА НА СООБЩЕНЕ БОТА ---
def _tg_ai_reset_dialog(profile, deactivate_pending=True):
    state = _tg_ai_get_state(profile.pk)
    if deactivate_pending:
        _tg_ai_deactivate_intents_for_bot_message(state.get("last_bot_message_id"))
    _tg_ai_clear_state(profile.pk)


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith(TG_AI_CALLBACK_CONFIRM_PREFIX))
def tg_ai_confirm_handler(call):
    chat_id = call.message.chat.id
    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        welcome_bot.answer_callback_query(call.id, "Профиль не найден.", show_alert=True)
        return
    if not _tg_ai_profile_has_access(profile):
        welcome_bot.answer_callback_query(call.id, "Доступ запрещён.", show_alert=True)
        welcome_bot.send_message(chat_id, TG_AI_ACCESS_DENIED_TEXT)
        return

    bot_message_id = call.data.replace(TG_AI_CALLBACK_CONFIRM_PREFIX, "", 1).strip()
    try:
        bot_message = chat_ai_models.AIMessageModel.objects.get(
            pk=bot_message_id,
            is_bot=True,
            chat__chat_author=profile,
        )
    except chat_ai_models.AIMessageModel.DoesNotExist:
        welcome_bot.answer_callback_query(call.id, "Намерение не найдено.", show_alert=True)
        return

    active_intents = bot_message.intents.filter(is_active=True)
    if not active_intents.exists():
        welcome_bot.answer_callback_query(call.id, "Нет активных намерений.", show_alert=True)
        return

    ready_intents = active_intents.filter(status_id="ready")
    if not ready_intents.exists():
        welcome_bot.answer_callback_query(call.id, "Намерение еще не готово.", show_alert=True)
        welcome_bot.send_message(chat_id, "Намерение пока не готово к исполнению. Уточните детали или нажмите Отмена.")
        return

    try:
        welcome_bot.answer_callback_query(call.id, "Принял. Выполняю.")
    except Exception:
        pass

    progress_message_id = _tg_ai_progress_start(chat_id, "Выполняю намерение: подготавливаю данные.")
    request = _tg_ai_build_request_for_profile(profile)
    created_lines = []
    failed_lines = []
    ready_intents_list = list(ready_intents)
    total_intents = len(ready_intents_list)
    for idx, intent_obj in enumerate(ready_intents_list, start=1):
        _tg_ai_progress_update(
            chat_id,
            progress_message_id,
            f"Выполняю намерение: шаг {idx} из {total_intents} ({intent_obj.intent_type_id}).",
        )
        try:
            created_object = _tg_ai_materialize_intent(intent_obj, request)
            object_url = _tg_ai_build_frontend_object_url(created_object)
            caption = _tg_ai_build_created_object_caption(intent_obj, created_object)

            if isinstance(created_object, dict) and created_object.get("kind") == "report_file":
                report_bytes = created_object.get("content")
                if isinstance(report_bytes, (bytes, bytearray)):
                    report_file = io.BytesIO(report_bytes)
                    report_file.name = str(created_object.get("filename") or "report.xlsx")
                    welcome_bot.send_document(chat_id, report_file, caption=caption)

            line = f"- {caption}"
            if object_url:
                line += f" | Открыть: {object_url}"
            created_lines.append(line)
        except Exception as exc:
            logger.exception("Failed to materialize telegram ai intent %s", intent_obj.pk)
            failed_lines.append(f"- Не удалось выполнить один из пунктов: {exc}")

    _tg_ai_progress_update(chat_id, progress_message_id, "Выполняю намерение: завершаю.")
    now = timezone.now()
    active_intents.exclude(status_id="done").update(is_active=False, deleted_at=now)
    _tg_ai_reset_dialog(profile, deactivate_pending=False)

    answer_text = "Готово, намерение исполнено."
    if created_lines:
        answer_text = "Готово, выполнил:\n" + "\n".join(created_lines)
    if failed_lines:
        answer_text += "\n\nНе удалось выполнить:\n" + "\n".join(failed_lines)

    _tg_ai_progress_finish(chat_id, progress_message_id, "Готово. Показываю результат.")
    try:
        welcome_bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    except Exception:
        pass
    welcome_bot.send_message(chat_id, answer_text)


@welcome_bot.callback_query_handler(func=lambda call: call.data.startswith(TG_AI_CALLBACK_CANCEL_PREFIX))
def tg_ai_cancel_handler(call):
    chat_id = call.message.chat.id
    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        welcome_bot.answer_callback_query(call.id, "Профиль не найден.", show_alert=True)
        return
    if not _tg_ai_profile_has_access(profile):
        welcome_bot.answer_callback_query(call.id, "Доступ запрещён.", show_alert=True)
        welcome_bot.send_message(chat_id, TG_AI_ACCESS_DENIED_TEXT)
        return

    bot_message_id = call.data.replace(TG_AI_CALLBACK_CANCEL_PREFIX, "", 1).strip()
    _tg_ai_deactivate_intents_for_bot_message(bot_message_id)
    _tg_ai_reset_dialog(profile, deactivate_pending=False)

    welcome_bot.answer_callback_query(call.id, "Отменено")
    try:
        welcome_bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    except Exception:
        pass
    welcome_bot.send_message(chat_id, "Ок, начинаем диалог заново.")


def _safe_get_obj_id_from_context(context_text: str) -> Optional[str]:
    try:
        ctx = json.loads(context_text or "{}")
        obj = ctx.get("obj") or {}

        if obj:
            return obj.get("id")
        subj = ctx.get("subj") or {}
        if subj:
            return subj.get("id")
        return None
    except Exception:
        return None


def _get_profile_by_chat_id(chat_id):
    return profile_model.objects.filter(telegram_id=chat_id).select_related("user").first()


# --- helpers ---


def _strip_html(s: str) -> str:
    """Грубое удаление HTML-тегов + декод сущностей"""
    if not s:
        return ""
    txt = re.sub(r"<[^>]+>", "", s)
    return html_lib.unescape(txt).strip()


def _fmt_dt_local(iso_str: str) -> str:
    """Парсит ISO и форматирует в локальное время dd.mm.yyyy HH:MM"""
    try:
        dt = parse_datetime(iso_str)
        if dt is None:
            return iso_str or ""
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        dt = timezone.localtime(dt)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str or ""


#
# def _build_history_block_from_webnotifications(serialized_list) -> Tuple[str, List]:
#     """
#     Возвращает (full_text, entities) для send_message.
#     full_text: 'Детали по полученному subj\n<история>'
#     entities: один expandable_blockquote, покрывающий историю.
#     """
#     header = "Детали по полученному subj"
#     if not serialized_list:
#         return f"{header}\nстория пуста", []
#
#     ICON_EMOJI = {
#         'нформация': 'ℹ️',
#         'Проекты': '📁',
#         'Группы': '👥',
#         'Задачи': '🗂️',
#         'Комментарии': '💬',
#         'Собрания': '🎥',
#         'Бизнес процессы': '⚙️',
#         'Логистика': '🚚',
#         'Файл': '📄',
#         'Напоминание': '⏰',
#         'Событие': '📅',
#         'default': '🔔'
#     }
#
#     lines = []
#     for item in serialized_list:
#         created = _fmt_dt_local(item.get("created_at"))
#         msg = _strip_html(item.get("message", ""))
#         icon_name = (item.get("icon_name") or "").strip()
#         emoji = ICON_EMOJI.get(icon_name, ICON_EMOJI['default'])
#         lines.append(f"{emoji} {created} — {msg}")
#
#     history_text = "\n".join(lines)
#     full_text = f"{header}\n{history_text}"
#
#     header_len_utf16 = len(header.encode("utf-16le")) // 2
#     quote_offset = header_len_utf16 + 1  # +1 за перевод строки после заголовка
#     quote_len = len(history_text.encode("utf-16le")) // 2
#     entities = [MessageEntity(type="expandable_blockquote", offset=quote_offset, length=quote_len)]
#     return full_text, entities
#

def _normalize_cmd(text: str) -> str:
    """в нижний регистр и без пробелов"""
    return re.sub(r"\s+", "", (text or "").lower())


def _safe_get_subj_id_from_context(context_text: str) -> Optional[str]:
    """Аккуратно достаёт subj.id из JSON в TGMessageModel.context"""
    try:
        ctx = json.loads(context_text or "{}")
        subj = ctx.get("subj") or {}
        return subj.get("id")
    except Exception:
        return None


def _build_history_text_from_webnotifications(serialized_list) -> (str, str):
    """
    Возвращает (header, history_text) БЕЗ entities.
    Отрисовка entities/разбиение делаем отдельно.
    """
    header = "Детали по полученному subj"
    if not serialized_list:
        return header, "стория пуста"

    ICON_EMOJI = {
        'нформация': 'ℹ️',
        'Проекты': '📁',
        'Группы': '👥',
        'Задачи': '🗂️',
        'Комментарии': '💬',
        'Собрания': '🎥',
        'Бизнес процессы': '⚙️',
        'Логистика': '🚚',
        'Файл': '📄',
        'Напоминание': '⏰',
        'Событие': '📅',
        'default': '🔔'
    }

    lines = []
    for item in serialized_list:
        created = _fmt_dt_local(item.get("created_at"))
        msg = _strip_html(item.get("message", ""))
        icon_name = (item.get("icon_name") or "").strip()
        emoji = ICON_EMOJI.get(icon_name, ICON_EMOJI['default'])
        lines.append(f"{emoji} {created} — {msg}")

    history_text = "\n".join(lines)
    return header, history_text


def _utf16_len(s: str) -> int:
    # Telegram считает длину в UTF-16 code units
    return len(s.encode('utf-16le')) // 2


def _utf16_find(haystack: str, needle: str) -> int:
    """
    Возвращает UTF-16 offset подстроки needle в haystack или -1, если не найдено.
    Telegram ожидает смещения/длину в UTF-16 code units.
    """
    idx = haystack.find(needle)
    if idx == -1:
        return -1
    return _utf16_len(haystack[:idx])


def _slice_utf16(s: str, max_units: int) -> (str, str):
    """
    Возвращает (head, tail), где head укладывается в max_units UTF-16 code units.
    Режем по ближайшей естественной границе (\\n, точка, пробел), если возможно.
    """
    if _utf16_len(s) <= max_units:
        return s, ""

    # Жесткое окно
    lo, hi = 0, len(s)
    # Бинарный поиск по символам, чтобы найти первую позицию, где длина > max_units
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _utf16_len(s[:mid]) <= max_units:
            lo = mid
        else:
            hi = mid - 1
    cut = lo

    # Попробуем откатиться к безопасной границе в пределах последней четверти окна
    window = s[:cut]
    backtrack = min(len(window), max(50, len(window) // 4))
    safe_zone = window[-backtrack:]
    candidates = []
    for sep in ['\n\n', '\n', '. ', '! ', '? ', '; ', ', ', ' ']:
        idx = safe_zone.rfind(sep)
        if idx != -1:
            candidates.append(len(window) - backtrack + idx + len(sep))
    if candidates:
        cut = max(candidates)

    return s[:cut].rstrip(), s[cut:].lstrip()


def _chunk_by_utf16(text: str, max_units: int):
    """
    Делит text на части по UTF-16 длине.
    """
    parts = []
    rest = text
    while rest:
        head, rest = _slice_utf16(rest, max_units)
        parts.append(head)
    return parts


def send_expandable_history(chat_id: int, header: str, history_text: str, bot):
    """
    Отправляет историю сообщениями с expandable_blockquote, аккуратно деля по UTF-16.
    Для каждого сообщения пересчитывает entities (offset/length).
    """
    if not history_text:
        bot.send_message(chat_id, f"{header}\nстория пуста")
        return

    # Максимум юнитов на один чанк истории, учитывая, что в сообщении будет еще и header/служебный текст.
    # Делаем запас и считаем entity отступ как len(header)+1 (перевод строки).
    header_units = _utf16_len(header) + _utf16_len("\n")
    per_chunk_units = max(1, CHUNK_LIMIT - header_units - SAFE_HEAD)

    chunks = _chunk_by_utf16(history_text, per_chunk_units)

    for i, chunk in enumerate(chunks, start=1):
        if i == 1:
            msg_header = header
        else:
            msg_header = f"{header} (продолжение {i}/{len(chunks)})"

        full_text = f"{msg_header}\n{chunk}"

        # entities: один expandable_blockquote на chunk
        quote_offset = _utf16_len(msg_header) + _utf16_len("\n")
        quote_len = _utf16_len(chunk)
        entities = [MessageEntity(
            type="expandable_blockquote",
            offset=quote_offset,
            length=quote_len
        )]

        # Контроль на крайний случай (не должен сработать при CHUNK_LIMIT)
        if _utf16_len(full_text) > TG_LIMIT:
            # как fallback — отправим без entities, чтобы не ронять поток
            bot.send_message(chat_id, full_text[:4000])  # последний предохранитель
        else:
            bot.send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode=None,  # используем entities
                entities=entities,
                disable_web_page_preview=True
            )


@welcome_bot.message_handler(
    func=lambda m: (getattr(m, 'reply_to_message', None)
                    and getattr(getattr(m.reply_to_message, 'from_user', None),
                                'is_bot',
                                False)),
    content_types=['text'])
def reply_to_bot_comment_thread_handler(message):
    """
    Если это ответ на сообщение бота, пытаемся найти TGMessageModel по replied message_id,
    вытащить context->obj.id и, если это комментарий, создать дочерний комментарий с текстом пользователя.
    Остальные тексты обрабатываются fallback_handler.
    """
    # Не ответ — отдаём управление другим хэндлерам
    replied = getattr(message, "reply_to_message", None)
    if not replied:
        return fallback_handler(message)

    # Ответ, но не на бота — тоже в основной поток
    replied_from_user = getattr(replied, "from_user", None)
    if not (replied_from_user and getattr(replied_from_user, "is_bot", False)):
        return fallback_handler(message)

    chat_id = message.chat.id
    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        return send_with_menu(chat_id, "Профиль не найден.")

    # щем исходное бот-сообщение в нашей таблице TGMessageModel
    try:
        tg_row = TGMessageModel.objects.get(message_id=replied.message_id)
    except ObjectDoesNotExist:
        # Не нашли сопоставление — обрабатываем как диалог с AI
        return fallback_handler(message)

    # --- НОВОЕ: обработка команды "детали" ---
    if _normalize_cmd(message.text) == "детали":
        subj_id = _safe_get_subj_id_from_context(getattr(tg_row, "context", "") or "")
        if subj_id:

            recs = WebNotificationModel.objects.filter(
                data__subj__id=subj_id
            ).order_by("created_at")

            r = BaseModel.objects.super_get(pk=subj_id)

            data = WebNotificationSerializer(recs, many=True).data

            if isinstance(r, TaskModel):

                needle = f'#{r.counter} '
                needle2 = f'"{r.name}"'
                needle3 = f'{r.name}'
                for item in data:
                    msg = item.get("message")
                    if isinstance(msg, str):
                        if needle in msg:
                            item["message"] = msg.replace(needle, "").strip()
                        if needle2 in msg:
                            item["message"] = item["message"].replace(needle2, "").strip()
                        if needle3 in msg:
                            item["message"] = item["message"].replace(needle3, "").strip()

                # --- НОРМАЛЗАЦЯ СООБЩЕНЙ ПО ШАБЛОНАМ (с сохранением инициатора) ---
                def _profile_display_name(p):
                    u = getattr(p, 'user', None)
                    if u and hasattr(u, 'get_short_name'):
                        nm = (u.get_short_name() or "").strip()
                        if nm:
                            return nm
                        first = (getattr(u, 'first_name', '') or '').strip()
                        last = (getattr(u, 'last_name', '') or '').strip()
                        email = (getattr(u, 'email', '') or '').strip()
                        if first or last:
                            return f"{first} {last}".strip()
                        if email:
                            return email
                    return (getattr(p, 'name', None) or str(p)).strip()

                def _format_recipients_lines(rec):
                    try:
                        names = [_profile_display_name(p) for p in rec.recipients.all()]
                        names = [n for n in names if n]
                        if not names:
                            return "—"
                        return "\n".join(f"• {n}" for n in names)
                    except Exception:
                        return "—"

                def _strip_leading_symbols(s: str) -> str:
                    # убираем ведущие эмодзи/пунктуацию/цифры маркера (встречается "🗂️ 24.10.2025 17:12 — ")
                    return s.lstrip('🗂️💬🔔📁👥🗂️🎥⚙️🚚📄⏰📅•-—–—: 0123456789.').strip()

                def _extract_actor(s: str, needles: list) -> str:
                    """
                    Возвращает инициатора: всё, что до первого совпадения needle.
                    Например: '1Ергалиева Дарига назначил(-а) Вам задачу .' -> '1Ергалиева Дарига'
                    """
                    s_clean = _strip_leading_symbols(s)
                    s_low = s_clean.lower()
                    pos = None
                    for nd in needles:
                        i = s_low.find(nd.lower())
                        if i != -1:
                            pos = i if (pos is None or i < pos) else pos
                    if pos is None:
                        return ""
                    actor = s_clean[:pos].rstrip(' -—:').strip()
                    return actor

                def _find_after(s: str, pattern: str) -> int:
                    """index сразу после pattern (case-insensitive) или -1"""
                    m = re.search(re.escape(pattern), s, flags=re.IGNORECASE)
                    return (m.end() if m else -1)

                def _simplify_message(rec, msg: str) -> str:
                    if not isinstance(msg, str) or not msg.strip():
                        return msg or ""

                    s = " ".join(msg.split())  # схлопываем пробелы
                    s_low = s.lower()

                    # ---- 1) Назначили наблюдателем ----
                    if "наблюдателем задачи" in s_low:
                        actor = _extract_actor(s, ["наблюдателем задачи"])
                        recips_block = _format_recipients_lines(rec)
                        base = f"Наблюдатели:\n{recips_block}"
                        return (base + (f"\nнициатор: {actor}" if actor else ""))

                    # ---- 2) Добавил новую задачу в проект ----
                    if "добавил(-а) новую задачу" in s_low or "добавил(-а) вашу задачу" in s_low or "добавил(-а) задачу" in s_low:
                        actor = _extract_actor(s, ["добавил(-а) новую задачу", "добавил(-а) вашу задачу",
                                                   "добавил(-а) задачу"])
                        # попытка вытащить проект
                        proj = None
                        m = re.search(r'в\s+проект\s+(.+)$', s, flags=re.IGNORECASE)
                        if m:
                            proj = m.group(1).strip().strip('«»"“”„‟\'')
                            # срезаем хвосты вроде " к спринту ..."
                            tails = [' к спринту ', ' к релизу ', ' к этапу ']
                            for t in tails:
                                cut = proj.lower().find(t.strip())
                                if cut > -1:
                                    proj = proj[:cut].strip()
                                    break
                        base = f"Указан проект: {proj or '—'}"
                        return (base + (f"\nнициатор: {actor}" if actor else ""))

                    # ---- 3) Назначил Вам задачу (исполнитель) ----
                    if "назначил(-а) вам задачу" in s_low or "назначил(-а) задачу" in s_low:
                        actor = _extract_actor(s, ["назначил(-а) вам задачу", "назначил(-а) задачу"])
                        recips_block = _format_recipients_lines(rec)
                        base = f"Назначен ответственный:\n{recips_block}"
                        return (base + (f"\nнициатор: {actor}" if actor else ""))

                    # ---- 4) Приступил(-а) к работе над задачей ----
                    if "приступил(-а) к работе над задачей" in s_low or "в работу" in s_low:
                        actor = _extract_actor(s, ["приступил(-а) к работе над задачей", "в работу"])
                        base = "Статус: В работе"
                        return (base + (f"\nнициатор: {actor}" if actor else ""))

                    # ---- 5) Отправил(-а) на проверку задачу ----
                    if "отправил(-а) на проверку задачу" in s_low or "на проверку задачу" in s_low:
                        actor = _extract_actor(s, ["отправил(-а) на проверку задачу", "на проверку задачу"])
                        base = "Статус: На проверке"
                        return (base + (f"\nнициатор: {actor}" if actor else ""))

                    # ---- 6) Оставил(-а) комментарий к задаче ----
                    if "оставил(-а) комментарий к задаче" in s_low or "оставил(-а)  комментарий к задаче" in s_low:
                        actor = _extract_actor(s, ["оставил(-а) комментарий к задаче",
                                                   "оставил(-а)  комментарий к задаче"])
                        # Попробуем вытащить текст комментария после двоеточия
                        # Пример: '... комментарий к задаче : Готово. ...'
                        # Берём первое ':' справа от ключевой фразы
                        idx = max(_find_after(s, "оставил(-а) комментарий к задаче"),
                                  _find_after(s, "оставил(-а)  комментарий к задаче"))
                        comment_text = None
                        if idx != -1:
                            tail = s[idx:].lstrip()
                            # после двоеточия
                            if tail.startswith(":"):
                                tail = tail[1:].lstrip()
                            # обрежем на первом ' http' / ' ссылка ' / ' отправил ' и т.п., чтобы не захватывать хвосты
                            cut_idx = len(tail)
                            for splitter in [" ссылка", " http", " https", " отправ", " к спринту", " в проект"]:
                                j = tail.lower().find(splitter)
                                if j != -1 and j < cut_idx:
                                    cut_idx = j
                            comment_text = tail[:cut_idx].strip()
                        if comment_text:
                            base = f"Комментарий:\n{comment_text}"
                        else:
                            base = "Комментарий: —"
                        return (base + (f"\nнициатор: {actor}" if actor else ""))

                    # по умолчанию — оставляем исходный текст
                    return msg

                for rec, item in zip(recs, data):
                    msg = item.get("message")
                    try:
                        item["message"] = _simplify_message(rec, msg)
                    except Exception:
                        item["message"] = msg

            header, history_text = _build_history_text_from_webnotifications(data)
            # send_with_menu(chat_id, f"ID subj: {subj_id}")
            # 2) отправляем историю безопасно, с разбиением и корректными entities на каждый чанк
            send_expandable_history(chat_id, header, history_text, welcome_bot)
            # (опционально) вернуть главное меню после истории
            send_with_menu(chat_id, "Выберите действие:")

            return
        else:
            return send_with_menu(chat_id, "В контексте нет subj.id.")

    obj_id = _safe_get_obj_id_from_context(getattr(tg_row, "context", "") or "")
    if not obj_id:
        return fallback_handler(message)

    # Создаём дочерний комментарий от имени текущего профиля
    text = (message.text or "").strip()
    if not text:
        return send_with_menu(chat_id, "Пустой комментарий не отправлен.")

    # Проверяем, что obj_id принадлежит комментарию
    parent_comment = (
        CommentModel.objects
        .filter(pk=obj_id, is_active=True)
        .select_related("related_object")
        .first()
    )

    if not parent_comment:
        # obj_id может быть любым BaseModel; по ТЗ реагируем только если это именно CommentModel
        # return send_with_menu(chat_id, "Это не тред комментариев — ответ из Telegram не поддержан.")
        related_object_id = obj_id
    else:
        related_object_id = parent_comment.related_object_id
    if not CommonBaseModel.objects.filter(pk=related_object_id, is_active=True).exists():
        return send_with_menu(chat_id, "Объект не найден или недоступен.")
    # with transaction.atomic():
    child = CommentModel(
        parent=parent_comment,
        text=text,
        related_object_id=related_object_id,
        author=profile,  # поле автора приходит из общего BaseModel
        is_personal=False,
        is_updated=False,
        is_active=True
    )
    child.save()
    # child = child.refresh_from_db() # С ним, почему-то по сокету следующая команда не выполняется
    async_task(comments_notifications.notify_about_new_comment, str(child.pk))

    # Подтверждение пользователю + кнопки главного меню
    send_with_menu(chat_id, "Комментарий добавлен ✅")

    # можно дополнительно убрать клавиатуру ответа в чате или отправить ссылку на объект
    # obj_url = f"{FRONTEND_URL}/?task={parent_comment.related_object_id}"  # если нужен URL
    # welcome_bot.send_message(chat_id, f"Открыть: {obj_url}")


@welcome_bot.message_handler(content_types=['voice', 'audio'])
def fallback_voice_handler(message):
    chat_id = message.chat.id
    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return
    if not _tg_ai_profile_has_access(profile):
        welcome_bot.send_message(chat_id, TG_AI_ACCESS_DENIED_TEXT)
        return

    try:
        voice_text = _tg_ai_extract_voice_text(message)
    except Exception as exc:
        logger.exception("Voice recognition failed in telegram bot")
        welcome_bot.send_message(chat_id, f"Не удалось распознать голосовое сообщение: {exc}")
        return

    if not voice_text:
        welcome_bot.send_message(chat_id, "Не удалось распознать текст в голосовом сообщении.")
        return

    try:
        _tg_ai_handle_dialog_input(message, profile, voice_text)
    except Exception:
        logger.exception("Failed to process voice dialog input")
        welcome_bot.send_message(chat_id, "Не получилось обработать голосовое сообщение. Попробуйте еще раз.")


@welcome_bot.message_handler(func=lambda message: True)
def fallback_handler(message):
    chat_id = message.chat.id
    profile = _get_profile_by_chat_id(chat_id)
    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return
    if not _tg_ai_profile_has_access(profile):
        welcome_bot.send_message(chat_id, TG_AI_ACCESS_DENIED_TEXT)
        return

    normalized = _normalize_cmd(getattr(message, "text", "") or "")
    if normalized in {"отмена", "cancel"}:
        _tg_ai_reset_dialog(profile, deactivate_pending=True)
        welcome_bot.send_message(chat_id, "Ок, начинаем диалог заново.")
        return

    incoming_text = (getattr(message, "text", "") or "").strip()
    if not incoming_text:
        welcome_bot.send_message(chat_id, "Сообщение пустое. Напишите текст запроса.")
        return

    try:
        _tg_ai_handle_dialog_input(message, profile, incoming_text)
    except Exception:
        logger.exception("Failed to process text dialog input")
        welcome_bot.send_message(chat_id, "Не получилось обработать сообщение. Попробуйте еще раз.")
    return

    """
    Универсальный обработчик для всех сообщений, не обработанных специфическими обработчиками.
    Очищает меню статусов и возвращает в главное меню.
    """
    chat_id = message.chat.id
    profile = profile_model.objects.filter(telegram_id=chat_id).first()

    if not profile:
        send_with_menu(chat_id, "Профиль не найден.")
        return

    # Возвращаемся в главное меню
    send_with_menu(chat_id, "Выберите действие:")


if __name__ == '__main__':
    welcome_bot.infinity_polling()

