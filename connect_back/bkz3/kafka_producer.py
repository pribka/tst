import json
import atexit
from confluent_kafka import Producer
from django.conf import settings

def _delivery_report(err, msg):
    if err is not None:
        # Логируйте/алерт — не теряйте ошибку
        print(f"Delivery failed: {err}")
    else:
        # Удобно для отладки
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

producer = Producer({
    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
    "security.protocol": settings.KAFKA_SECURITY_PROTOCOL,
    "enable.idempotence": True,   # безопасная отправка без дублей
    "acks": "all",
    "retries": 5,
    "linger.ms": 5,
    "batch.num.messages": 10000,
})

atexit.register(lambda: producer.flush(5))

def send_event(topic, key, value):
    payload = json.dumps(value, ensure_ascii=False, default=str)
    producer.produce(
        topic=topic,
        key=key.encode("utf-8") if key else None,
        value=payload.encode("utf-8"),
        on_delivery=_delivery_report,
    )
    # освобождаем буферы в фоне
    producer.poll(0)
