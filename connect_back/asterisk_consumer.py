import json
import os
import threading
import time
from datetime import datetime

import django
import pika

# Инициализация Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bkz3.settings")
django.setup()

from django.conf import settings
from django.db import DatabaseError, close_old_connections, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from help_desk.models import AsteriskCallRecord


FIELD_MAX_LENGTHS = {
    "call_id": 64,
    "manager_ext": 16,
    "client_number": 32,
    "src": 64,
    "dst": 64,
    "cnum": 64,
    "dstchannel": 255,
    "lastapp": 128,
    "dcontext": 128,
    "recordingfile": 512,
}


class PermanentMessageError(Exception):
    """The message is invalid and should not be requeued."""


def normalize_string(value):
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def normalize_bounded_string(field_name, value, max_length):
    text = normalize_string(value)
    if text is None:
        return None

    if len(text) <= max_length:
        return text

    if field_name == "call_id":
        raise PermanentMessageError(
            f"Payload field '{field_name}' exceeds {max_length} characters"
        )

    print(
        f"Field '{field_name}' exceeds {max_length} characters, "
        "truncating before save"
    )
    return text[:max_length]


def normalize_call_date(value):
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = parse_datetime(normalize_string(value) or "")

    if parsed is None:
        print(f"Invalid call_date value: {value!r}")
        return None

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())

    return parsed


def normalize_duration(value):
    try:
        duration = int(value or 0)
    except (TypeError, ValueError):
        return 0

    return max(duration, 0)


def normalize_queue_names(values):
    normalized = []
    for value in values:
        queue_name = normalize_string(value)
        if queue_name:
            normalized.append(queue_name)
    return normalized



def get_rabbitmq_queues(raw_value=None):
    """
    Возвращает список очередей из Django settings.
    Поддерживает list/tuple, обычную строку и JSON-строку.
    """
    if raw_value is None:
        raw_value = getattr(settings, "RABBITMQ_QUEUE", [])

    if isinstance(raw_value, (list, tuple)):
        return normalize_queue_names(raw_value)

    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if not raw_value:
            return []

        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return [raw_value]

        if isinstance(parsed, list):
            return normalize_queue_names(parsed)

        if isinstance(parsed, str):
            queue_name = normalize_string(parsed)
            return [queue_name] if queue_name else []

    return []


RABBITMQ_HOST = getattr(settings, "RABBITMQ_HOST", None)
RABBITMQ_USER = getattr(settings, "RABBITMQ_USER", None)
RABBITMQ_PASS = getattr(settings, "RABBITMQ_PASSWORD", None)
RABBITMQ_QUEUES = get_rabbitmq_queues()


def connect():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                credentials=credentials,
                heartbeat=30,
            )
            return pika.BlockingConnection(params)
        except Exception as e:
            print("RabbitMQ connection error:", e)
            time.sleep(3)


def normalize_payload(payload: dict) -> dict:
    """
    Нормализация входящего payload перед сохранением.
    """
    if not isinstance(payload, dict):
        raise PermanentMessageError("Payload must be a JSON object")

    return {
        "call_id": normalize_bounded_string(
            "call_id", payload.get("call_id"), FIELD_MAX_LENGTHS["call_id"]
        )
        or "",
        "call_date": normalize_call_date(payload.get("call_date")),
        "manager_ext": normalize_bounded_string(
            "manager_ext", payload.get("manager_ext"), FIELD_MAX_LENGTHS["manager_ext"]
        ),
        "client_number": normalize_bounded_string(
            "client_number",
            payload.get("client_number"),
            FIELD_MAX_LENGTHS["client_number"],
        ),
        "duration_seconds": normalize_duration(payload.get("duration_seconds")),
        "src": normalize_bounded_string(
            "src", payload.get("src"), FIELD_MAX_LENGTHS["src"]
        ),
        "dst": normalize_bounded_string(
            "dst", payload.get("dst"), FIELD_MAX_LENGTHS["dst"]
        ),
        "cnum": normalize_bounded_string(
            "cnum", payload.get("cnum"), FIELD_MAX_LENGTHS["cnum"]
        ),
        "dstchannel": normalize_bounded_string(
            "dstchannel",
            payload.get("dstchannel"),
            FIELD_MAX_LENGTHS["dstchannel"],
        ),
        "lastapp": normalize_bounded_string(
            "lastapp", payload.get("lastapp"), FIELD_MAX_LENGTHS["lastapp"]
        ),
        "lastdata": normalize_string(payload.get("lastdata")),
        "dcontext": normalize_bounded_string(
            "dcontext", payload.get("dcontext"), FIELD_MAX_LENGTHS["dcontext"]
        ),
        "recordingfile": normalize_bounded_string(
            "recordingfile",
            payload.get("recordingfile"),
            FIELD_MAX_LENGTHS["recordingfile"],
        ),
        "raw_payload": payload,
    }


def save_payload(payload: dict):
    """
    Сохранение payload в Django-модель.
    """
    data = normalize_payload(payload)

    if not data["call_id"]:
        raise PermanentMessageError("Payload does not contain call_id")

    call_id = data.pop("call_id")

    close_old_connections()

    with transaction.atomic():
        obj, created = AsteriskCallRecord.objects.update_or_create(
            call_id=call_id,
            defaults=data,
        )

    return obj, created


def process_message(queue, body):
    raw_text = body.decode(errors="replace")
    print(f"[{queue}] Received:", raw_text)

    payload = json.loads(raw_text)
    if not isinstance(payload, dict):
        raise PermanentMessageError("RabbitMQ message is not a JSON object")

    obj, created = save_payload(payload)

    print(
        f"[{queue}] Saved call_id={obj.call_id}, "
        f"{'created' if created else 'updated'}"
    )


def handle_delivery(ch, method, queue, body):
    try:
        process_message(queue, body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except (json.JSONDecodeError, PermanentMessageError) as exc:
        print(f"[{queue}] Permanent message error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except DatabaseError as exc:
        print(f"[{queue}] Database error, message will be requeued: {exc}")
        close_old_connections()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as exc:
        print(f"[{queue}] Unexpected error while processing message: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer(queue):
    """
    Запуск консьюмера для одной очереди.
    Если соединение падает, пытается переподключиться.
    """
    while True:
        connection = None
        channel = None

        try:
            connection = connect()
            channel = connection.channel()

            channel.queue_declare(queue=queue, passive=True)
            channel.basic_qos(prefetch_count=1)

            print(f"Started consumer for: {queue}")

            def callback(ch, method, properties, body):
                handle_delivery(ch, method, queue, body)

            channel.basic_consume(queue=queue, on_message_callback=callback)
            channel.start_consuming()

        except Exception as e:
            print(f"Error in consumer {queue}: {e}")
            time.sleep(3)

        finally:
            try:
                if channel and channel.is_open:
                    channel.close()
            except Exception:
                pass

            try:
                if connection and connection.is_open:
                    connection.close()
            except Exception:
                pass

            close_old_connections()


if __name__ == "__main__":
    if not RABBITMQ_QUEUES:
        print("No queues defined in Django settings (RABBITMQ_QUEUE)")
        raise SystemExit(1)

    if not RABBITMQ_HOST or not RABBITMQ_USER or not RABBITMQ_PASS:
        print("RabbitMQ settings are not fully configured")
        raise SystemExit(1)

    print("Starting consumers:", RABBITMQ_QUEUES)

    threads = []
    for queue in RABBITMQ_QUEUES:
        t = threading.Thread(target=start_consumer, args=(queue,), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
