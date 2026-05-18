from datetime import datetime, timedelta
import json
import logging
import time

import requests
from openai import OpenAI

from django.core.serializers.json import DjangoJSONEncoder
from django.template import Context, Template
from django.test import RequestFactory
from django.utils import timezone
from django.utils.safestring import mark_safe

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL
from common.redis import socketio_redis
from common.utils import wait_if_paused
from users.models import ProfileModel

from bpms.chat_ai import models


logger = logging.getLogger(__name__)

AI_CHAT_EVENT_TYPE = "ai_chat_event"


class IntentCreationError(Exception):
    pass


INTENT_RESPONSE_SOFT_SCHEMA = {
    "type": "array",
    "items": {"type": "object"},
}

SUMMARY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
}

EFFICIENCY_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
}

INTENT_CLASSIFIER_SCHEMA = {
    "type": "string",
    "enum": ["task", "event", "meet", "report", "workflow_request", "unknown"],
    "description": "Ответ только одним словом: task, event, meet, report, workflow_request или unknown.",
}

INTENTS_SCHEMA = {
    "type": "array",
    "minItems": 1,
    "items": {
        "oneOf": [
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "intent_type": {"const": "create_task"},
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "operator": {"type": ["string", "null"]},
                    "date_start_plan": {"type": ["string", "null"]},
                    "dead_line": {"type": ["string", "null"]},
                    "project": {"type": ["string", "null"]},
                    "cooperators": {"type": ["string", "null"]},
                    "visors": {"type": ["string", "null"]},
                    "workgroup": {"type": ["string", "null"]},
                },
                "required": [
                    "intent_type",
                    "name",
                    "description",
                    "operator",
                    "date_start_plan",
                    "dead_line",
                    "project",
                    "cooperators",
                    "visors",
                    "workgroup",
                ],
            },
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "intent_type": {"const": "create_event"},
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "start_at": {"type": ["string", "null"]},
                    "members": {"type": ["string", "null"]},
                },
                "required": ["intent_type", "name", "description", "start_at", "members"],
            },
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "intent_type": {"const": "create_meet"},
                    "name": {"type": "string"},
                    "date_begin": {"type": ["string", "null"]},
                    "members": {"type": ["string", "null"]},
                },
                "required": ["intent_type", "name", "date_begin", "members"],
            },
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "error": {"type": "string"},
                },
                "required": ["error"],
            },
        ]
    },
}


def _set_status(instance, status_value: str) -> None:
    if hasattr(instance, "status"):
        setattr(instance, "status_id", status_value)
        instance.save(update_fields=["status"])


def _build_request_for_profile(profile_id):
    profile = ProfileModel.objects.select_related("user").get(pk=profile_id)
    request = RequestFactory().get("/api/v1/chat_ai/messages/")
    request.user = profile.user
    request.query_params = request.GET
    request.profile = profile
    return request


def _serialize_message(message):
    serializer_class = message.get_serializer_class(action="detail")
    return serializer_class(message).data


def _publish_ai_chat_event(profile_id, chat_id, assistant_message_id, subtype, **extra):
    payload = {
        "event_type": AI_CHAT_EVENT_TYPE,
        "type": subtype,
        "chat_id": str(chat_id),
        "assistant_message_id": str(assistant_message_id),
    }
    payload.update(extra)

    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": payload,
                "recipients": [str(profile_id)],
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def _chunk_text(text, max_chars=18):
    if not text:
        return []

    words = text.split(" ")
    chunks = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) > max_chars and current:
            chunks.append(current + " ")
            current = word
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


def _stream_reply_text(profile_id, chat_id, assistant_message_id, text):
    for chunk in _chunk_text(text):
        _publish_ai_chat_event(
            profile_id=profile_id,
            chat_id=chat_id,
            assistant_message_id=assistant_message_id,
            subtype="delta",
            text=chunk,
        )
        time.sleep(0.04)


def _create_bot_message(chat: models.AIChatModel, reply_to: models.AIMessageModel, text: str, status_id="done"):
    bot_msg = models.AIMessageModel.objects.create(
        chat=chat,
        message_author=None,
        text=text,
        is_bot=True,
        reply_to=reply_to,
        status_id=status_id,
    )
    chat.last_sent = timezone.now()
    chat.save(update_fields=["last_sent"])
    return bot_msg


def _update_bot_message(bot_msg, *, text=None, status_id=None, intent_data=None, is_intent=None):
    update_fields = []

    if text is not None:
        bot_msg.text = text
        update_fields.append("text")

    if status_id is not None:
        bot_msg.status_id = status_id
        update_fields.append("status")

    if intent_data is not None:
        bot_msg.intent_data = intent_data
        update_fields.append("intent_data")

    if is_intent is not None:
        bot_msg.is_intent = is_intent
        update_fields.append("is_intent")

    if update_fields:
        bot_msg.save(update_fields=update_fields)

    return bot_msg


def _create_intents_for_bot_message(bot_msg, intents, request):
    from ..serializers import IntentCreateSerializer

    if not intents:
        return 0

    created_count = 0
    errors = []
    valid_items = [item for item in intents if isinstance(item, dict) and not item.get("error")]

    for index, item in enumerate(intents):
        if not isinstance(item, dict):
            errors.append(f"Intent #{index + 1}: invalid payload type {type(item).__name__}")
            continue

        if item.get("error"):
            continue

        intent_type = item.get("intent_type")
        if not intent_type:
            errors.append(f"Intent #{index + 1}: intent_type is required")
            continue

        item_copy = item.copy()
        item_copy.pop("intent_type", None)
        serializer = IntentCreateSerializer(
            data={
                "source_object": bot_msg.pk,
                "intent_type": intent_type,
                "raw_data": item_copy,
            },
            context={"request": request},
        )
        if not serializer.is_valid():
            errors.append(f"Intent #{index + 1}: {serializer.errors}")
            continue

        try:
            serializer.save()
            created_count += 1
        except Exception as exc:
            logger.exception("Intent save failed for bot message %s", bot_msg.pk)
            errors.append(f"Intent #{index + 1}: save failed: {exc}")

    if errors:
        raise IntentCreationError("; ".join(errors))

    if valid_items and created_count == 0:
        raise IntentCreationError("No intents were created from parser output")

    return created_count


def clean_json(text: str):
    text = text.replace("```json", "")
    text = text.replace("```", "")

    try:
        text = json.loads(text)
    except json.JSONDecodeError:
        pass

    return text


def classify_message(message: models.AIMessageModel, text: str):
    if not text:
        return "unknown"

    role = models.AIChatRoleModel.objects.get(code="intent_classifier")
    user_template = Template(role.user_message)
    user_template.render(Context({"text_from_user": text}))

    resp = invoke_role_prompt(
        user_message=text,
        role_code="intent_classifier",
        context={},
        consumer=message,
        format_schema=INTENT_CLASSIFIER_SCHEMA,
        url_query_param=f"chat_ai_classify&message={message.pk}",
    )

    allowed_intents = {"task", "event", "meet", "report", "workflow_request", "unknown"}
    parsed_intent = "unknown"

    if isinstance(resp, str):
        parsed_intent = resp.strip().lower()
    elif isinstance(resp, dict):
        parsed_intent = str(resp.get("intent", "")).strip().lower()

    if parsed_intent not in allowed_intents:
        parsed_intent = "unknown"

    return parsed_intent


def build_intent_parser_context():
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


def invoke_role_prompt(user_message: str, role_code: str, context: dict, consumer=None, format_schema=None, url_query_param=None):
    if not user_message:
        return None

    try:
        role = models.AIChatRoleModel.objects.get(code=role_code)
    except models.AIChatRoleModel.DoesNotExist as exc:
        raise models.AIChatRoleModel.DoesNotExist(
            f"AIChatRoleModel with code '{role_code}' not found"
        ) from exc

    system_template = Template(role.system_message)
    system_message = system_template.render(Context(context))

    user_context = context.copy()
    user_context["user_message"] = mark_safe(user_message)
    user_template = Template(role.user_message)
    rendered_user_message = user_template.render(Context(user_context))

    provider = models.AIProvider.objects.defer("api_key").get(code=role.provider_id)
    prompt_tokens = 0
    completion_tokens = 0

    if provider.code == "gos24.kz":
        wait_if_paused()
        payload = {
            "model": role.model_name,
            "system": system_message,
            "prompt": rendered_user_message,
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

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                resp = requests.post(
                    request_url,
                    json=payload,
                    timeout=(120, 600),
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as err:
                code = getattr(getattr(err, "response", None), "status_code", None)
                if code is not None and code not in (502, 503, 504):
                    raise
                if attempt == max_attempts - 1:
                    raise
                logger.warning("invoke_role_prompt retry %s/%s: %s", attempt + 1, max_attempts, err)
                time.sleep(2)

        text_response = (data.get("response") or "").strip()
        if not text_response:
            logger.error("Empty response from Ollama-like backend, data=%r", data)
            return None

        parsed_response = clean_json(text_response) if format_schema else text_response
        prompt_tokens = data.get("prompt_eval_count") or 0
        completion_tokens = data.get("eval_count") or 0
    else:
        provider = role.provider
        messages_payload = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": rendered_user_message},
        ]

        client = OpenAI(api_key=provider.api_key, base_url=(provider.base_url or None))
        response = client.chat.completions.create(
            model=role.model_name,
            messages=messages_payload,
            temperature=float(role.temperature),
            max_tokens=role.max_output_tokens,
            top_p=float(role.top_p),
        )
        parsed_response = (response.choices[0].message.content or "").strip()
        parsed_response = clean_json(parsed_response)

        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens

    if consumer is not None:
        if consumer.get_label() == "chat_ai.AIMessageModel":
            author_id = consumer.chat.chat_author_id
        else:
            author_id = consumer.author_id

        models.TokenUsage.objects.create(
            author_id=author_id,
            consumer=consumer,
            model_name=role.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    return parsed_response


def generate_bot_reply(message, classification, intents):
    if isinstance(classification, dict):
        is_intent = bool(classification.get("is_intent"))
    else:
        is_intent = str(classification or "").strip().lower() != "unknown"

    if is_intent:
        if isinstance(intents, str):
            return "Не смог прочитать намерения: ответ модели не похож на JSON."

        if not isinstance(intents, list):
            return "Ожидал список намерений, но получил неожиданный формат ответа."

        if len(intents) == 0:
            return "Не увидел подходящих намерений в сообщении."

        for intent in intents:
            if "error" in intent:
                return intent["error"]

        return f"Я выявил {len(intents)} намерений. Проверьте и уточните данные при необходимости."

    return "Принял сообщение. Чем могу помочь дальше?"


def process_message(message_id: int, bot_message_id=None, profile_id=None, request=None) -> None:
    try:
        message = models.AIMessageModel.objects.get(pk=message_id)
    except models.AIMessageModel.DoesNotExist:
        logger.warning("process_message skipped: message %s does not exist", message_id)
        return None

    bot_msg = None
    if bot_message_id:
        try:
            bot_msg = models.AIMessageModel.objects.get(pk=bot_message_id)
        except models.AIMessageModel.DoesNotExist:
            logger.warning("process_message: bot message %s does not exist", bot_message_id)

    profile_id = profile_id or message.chat.chat_author_id

    if request is None and profile_id:
        request = _build_request_for_profile(profile_id)

    try:
        if bot_msg:
            _publish_ai_chat_event(
                profile_id=profile_id,
                chat_id=message.chat_id,
                assistant_message_id=bot_msg.pk,
                subtype="accepted",
                message=_serialize_message(bot_msg),
            )

        _set_status(message, "processing_classify")
        if bot_msg:
            _update_bot_message(bot_msg, status_id="processing_classify")
            _publish_ai_chat_event(
                profile_id=profile_id,
                chat_id=message.chat_id,
                assistant_message_id=bot_msg.pk,
                subtype="stage",
                stage="classify",
                text="Understanding request",
            )

        base_text = (message.text or "").strip()
        vosk_text = (getattr(message, "vosked_text", "") or "").strip()
        text = (base_text + " " + vosk_text).strip()

        intent_label = classify_message(message, text)
        is_intent = intent_label != "unknown"
        message.is_intent = is_intent
        message.save(update_fields=["is_intent"])
        if bot_msg:
            _update_bot_message(bot_msg, is_intent=is_intent)

        if is_intent:
            _set_status(message, "processing_intent")
            if bot_msg:
                _update_bot_message(bot_msg, status_id="processing_intent", is_intent=True)
                _publish_ai_chat_event(
                    profile_id=profile_id,
                    chat_id=message.chat_id,
                    assistant_message_id=bot_msg.pk,
                    subtype="stage",
                    stage="parse_intents",
                    text="Extracting details",
                )

            context = build_intent_parser_context()
            parser_role_code = "intent_parser"
            if intent_label == "report":
                parser_role_code = "intent_parser_report"
            if intent_label == "workflow_request" and models.AIChatRoleModel.objects.filter(
                code="intent_parser_workflow_request"
            ).exists():
                parser_role_code = "intent_parser_workflow_request"

            intents = invoke_role_prompt(
                user_message=text,
                role_code=parser_role_code,
                context=context,
                consumer=message,
                format_schema=INTENT_RESPONSE_SOFT_SCHEMA,
                url_query_param=f"chat_ai_intents&message={message.pk}",
            )
        else:
            intents = None

        _set_status(message, "generating_reply")
        if bot_msg and is_intent:
            try:
                intent_data = json.dumps(intents, ensure_ascii=False)
            except Exception:
                intent_data = str(intents)
            _update_bot_message(bot_msg, intent_data=intent_data, is_intent=True)
            if isinstance(intents, list):
                created_intents = _create_intents_for_bot_message(bot_msg, intents, request)
                if created_intents:
                    _publish_ai_chat_event(
                        profile_id=profile_id,
                        chat_id=message.chat_id,
                        assistant_message_id=bot_msg.pk,
                        subtype="intents_ready",
                        message=_serialize_message(bot_msg),
                    )

        if bot_msg:
            _update_bot_message(bot_msg, status_id="generating_reply", is_intent=is_intent)
            _publish_ai_chat_event(
                profile_id=profile_id,
                chat_id=message.chat_id,
                assistant_message_id=bot_msg.pk,
                subtype="stage",
                stage="generate_reply",
                text="Writing reply",
            )

        reply_text = generate_bot_reply(
            message=message,
            classification=intent_label,
            intents=intents,
        )

        chat = message.chat
        if bot_msg is None:
            bot_msg = _create_bot_message(
                chat=chat,
                reply_to=message,
                text="",
                status_id="queued",
            )

        _stream_reply_text(profile_id, message.chat_id, bot_msg.pk, reply_text)
        _update_bot_message(bot_msg, text=reply_text, status_id="done", is_intent=is_intent)
        _publish_ai_chat_event(
            profile_id=profile_id,
            chat_id=message.chat_id,
            assistant_message_id=bot_msg.pk,
            subtype="done",
            message=_serialize_message(bot_msg),
        )

        _set_status(message, "done")
        return bot_msg

    except Exception as exc:
        logger.exception("process_message failed for %s", message_id)
        _set_status(message, "failed")
        if bot_msg:
            fallback_text = "Request failed. Please try again."
            _update_bot_message(bot_msg, text=fallback_text, status_id="failed", is_intent=message.is_intent)
            _publish_ai_chat_event(
                profile_id=profile_id,
                chat_id=message.chat_id,
                assistant_message_id=bot_msg.pk,
                subtype="error",
                text=fallback_text,
                error=str(exc),
                message=_serialize_message(bot_msg),
            )
