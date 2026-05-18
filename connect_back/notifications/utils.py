from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.template import Template, Context, loader
import socket

from django_q.tasks import async_task

from bkz3.settings import EMAIL_HOST_USER, BASE_DIR

from . import models
from . import event_types
from .sms_backends import sms_api


def send_sms_message(text: str, phone: str):
    notification = models.SMSNotificationModel.objects.create(
        message=text,
        recipient=phone,
    )
    async_task(sms_api.send_message, notification.pk)


def send_email(email_notification_pk, **kwargs):
    email_notification = models.EmailNotificationModel.objects.get(
        pk=email_notification_pk,
        is_active=True
    )
    connection = mail.get_connection()
    
    # Добавляем таймауты для SMTP
    connection.timeout = 10  # Таймаут на открытие соединения
    connection.open_timeout = 10  # Таймаут на установку соединения
    
    try:
        connection.open()
    except (socket.timeout, Exception) as ex:
        # bot.send_message(chat_id=TELEBOT_EMAIL_NOTIFICATION_LOGGER['recipients'][0],
        #                  text='SMTP connection error! Details: ' + str(ex))
        models.EmailNotificationErrorLog.objects.create(
            text=ex,
            description='Connection error'
        )
        return
    # Получаем шаблон и subject
    email_template = None
    try:
        email_template = models.EmailTemplateModel.objects.get(
            code=email_notification.template,
            is_active=True
        )
        html_template = Template(email_template.html)
    except ObjectDoesNotExist:
        html_template = loader.get_template(template_name=f'email_templates/{email_notification.template}.html')
    
    # Определяем subject: из шаблона если есть и не пустой, иначе из уведомления
    subject = email_notification.subject
    if email_template and email_template.subject:
        subject = email_template.subject
    
    try:
        html_message = html_template.render(email_notification.context)
    except AttributeError:
        html_message = html_template.render(Context(email_notification.context))
    for recipient in email_notification.recipients.all():
        sending = mail.EmailMultiAlternatives(
            subject=subject,
            body=email_notification.message,
            from_email=EMAIL_HOST_USER,
            to=[recipient.recipient],
            connection=connection,
        )
        sending.attach_alternative(content=html_message, mimetype='text/html')
        attachments = email_notification.email_attachments.filter(is_active=True)
        for attachment in attachments:
            sending.attach_file(f"{BASE_DIR}/{attachment.path}")
        try:
            # Таймаут для отправки каждого письма
            connection.timeout = 30
            sending.send(fail_silently=True)
        except socket.timeout:
            models.EmailNotificationErrorLog.objects.create(
                email_notification=email_notification,
                email=recipient,
                text="SMTP timeout - server didn't respond in 30 seconds",
                description='Sending Timeout'
            )
        except Exception as ex:
            models.EmailNotificationErrorLog.objects.create(
                email_notification=email_notification,
                email=recipient,
                text=ex,
                description='Sending Error'
            )
        recipient.sent = timezone.now()
        recipient.save(update_fields=('sent',))
    connection.close()
    email_notification.sent = timezone.now()
    email_notification.save(update_fields=('sent',))
    return f'email notification {email_notification_pk} is sent.'


def send_test_message(user_id, initiator):
    event_types.TestSignal().create_notification((user_id,), initiator=initiator)
    return 'complete'
