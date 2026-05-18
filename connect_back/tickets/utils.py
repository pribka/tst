from bkz3.settings import GLOBAL_FRONT_SETTINGS
from notifications.models import (EmailNotificationModel,
                                  EmailNotificationRecipientModel)
from notifications.utils import send_email
from users.serializers import EmailNotifiProfileSerializer


def send_new_ticket_confirmation_email(ticket):
    '''
    Оповещение о создании новой заявки
    '''

    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']

    notification = EmailNotificationModel.objects.create(
        template='new_ticket',
        subject='Заявка успешно создана',
        context=context
    )
    EmailNotificationRecipientModel.objects.create(
        email_notification=notification,
        recipient=ticket.email
    )
    send_email(notification.id)


def send_ticket_approved_email(ticket, manager):
    '''
    Оповещение об одобрении заявки
    '''

    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']

    manager_data = EmailNotifiProfileSerializer(instance=manager).data
    context['manager_name'] = manager_data['full_name']
    context['manager_phone'] = manager_data['phone']
    context['manager_email'] = manager_data['email']

    notification = EmailNotificationModel.objects.create(
        template='ticket_approved',
        subject='Заявка одобрена',
        context=context
    )
    EmailNotificationRecipientModel.objects.create(
        email_notification=notification,
        recipient=ticket.email
    )
    send_email(notification.id)


def send_ticket_rejected_email(ticket, manager):
    '''
    Оповещение об отклонении заявки
    '''

    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']

    manager_data = EmailNotifiProfileSerializer(instance=manager).data
    context['manager_name'] = manager_data['full_name']
    context['manager_phone'] = manager_data['phone']
    context['manager_email'] = manager_data['email']

    notification = EmailNotificationModel.objects.create(
        template='ticket_rejected',
        subject='Заявка отклонена',
        context=context
    )
    EmailNotificationRecipientModel.objects.create(
        email_notification=notification,
        recipient=ticket.email
    )
    send_email(notification.id)
