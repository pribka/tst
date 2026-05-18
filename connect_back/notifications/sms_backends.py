import requests
import json
from abc import ABC, abstractmethod
from urllib.parse import quote

from django.utils import timezone
from django.utils.module_loading import import_string

from bkz3.settings import SMS_API
from .models import SMSNotificationErrorLog, SMSNotificationModel


class AbstractSMSBackend(ABC):
    """Абстрактный класс бэкенда для api отправки SMS-сообщений."""
    @abstractmethod
    def send_message(self, notification_id: str) -> None:
        """Отправить СМС одному адресату."""
        pass


class MobizonSMSBackend(AbstractSMSBackend):
    """"Бэкенд для взаимодействия с сервисом mobizon.kz."""
    def send_message(self, notification_id: str):
        try:
            notification = SMSNotificationModel.objects.get(pk=notification_id)
        except SMSNotificationModel.DoesNotExist:
            SMSNotificationErrorLog.objects.create(
                sms_notification=None,
                phone="",
                description=f"notification {notification_id} not found.",
                text="",
            )
            return
        url = f"{SMS_API.get('host', '')}/message/sendSmsMessage?output=json&api=v1&apiKey={SMS_API.get('key', '')}"
        recipient = notification.recipient
        data = f"recipient={quote(recipient)}&text={quote(notification.message)}"
        resp = requests.post(
            url,
            data,
            headers={
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded"
            }
        )
        if not resp.status_code == 200:
            SMSNotificationErrorLog.objects.create(
                sms_notification=notification,
                phone=recipient,
                description=f"Status code {resp.status_code}",
                text=resp.text,
            )
            return
        resp_data = json.loads(resp.text)
        api_code = resp_data.get('code', -1)
        if not api_code == 0:
            SMSNotificationErrorLog.objects.create(
                sms_notification=notification,
                phone=recipient,
                description=f"Api code {api_code}",
                text=resp_data.get('data', '')
            )
            return
        notification.sent = timezone.now()
        notification.save(update_fields=('sent',),)


# Текущий класс для отправки SMS-сообщений. Этот класс необходимо использовать в проекте.
sms_api = import_string(SMS_API.get('backend'))()
