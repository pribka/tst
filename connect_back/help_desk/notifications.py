import telebot

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from users.utils import get_invite_url
from users.models import ProfileModel

from notifications import event_types, models as notification_models
from notifications.utils import send_email

from bkz3.settings import COMPANY_NAME

from contractor_permissions.utils import users_that_have_app_section_role_in_contractors

from . import models, utils


def notify_about_new_ticket(ticket_id):
    ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    contact_person_user = ticket.contact_person.user
    if contact_person_user:
        event_type = event_types.TicketNewForContactPerson()
        event_type.create_notification(recipients=(contact_person_user,), subj=ticket,)
    message_text = f'Ваше обращение №{ticket.number} зарегистрировано в системе'
    # message_text = f'Сіздің өтінішіңіз №{ticket.number} жүйеде тіркелді. \n' \
    #                f'Ваше обращение №{ticket.number} зарегистрировано в системе'
    send_notify_for_channel(ticket, message_text)
    customer_card = ticket.customer_card
    ticket_type_id = ticket.ticket_type_id
    org_admin = ticket.customer_card.org_admin
    admins = set(users_that_have_app_section_role_in_contractors((org_admin.pk,), 'help_desk', 'admin'))
    specialists = set(customer_card.actual_specialists.values_list('user', flat=True))
    if ticket_type_id == 'issue':
        specialist = ticket.specialist
        if specialist:
            event_type = event_types.TicketNewForSpecialists()
            recipients = (specialist,)
            event_type.create_notification(recipients=recipients, subj=ticket, obj=customer_card)
        elif specialists:
            event_type = event_types.TicketNewForSpecialists()
            event_type.create_notification(recipients=tuple(specialists), subj=ticket, obj=customer_card)
        visors = set(ticket.visors.all().values_list('pk', flat=True))
        recipients = visors | admins
        if specialist:
            recipients.discard(specialist.pk)
        if not specialist:
            recipients = recipients - specialists
        event_type = event_types.TicketNewForAdmins()
        event_type.create_notification(recipients=tuple(recipients), subj=ticket, obj=customer_card)

    elif ticket_type_id == 'lead':
        if admins:
            event_type = event_types.LeadNewForSpecialists()
            event_type.create_notification(recipients=tuple(admins), subj=ticket, obj=customer_card)


def notify_about_new_ticket_client_message(ticket_id, message_id):
    """Уведомление специалисту о новом сообщение от пользователя в тикете."""
    ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    org_admin = ticket.customer_card.org_admin
    if ticket.specialist:
        recipients = [str(ticket.specialist.pk), ]
    else:
        recipients = set(users_that_have_app_section_role_in_contractors((org_admin.pk,), 'help_desk', 'admin'))
    initiator = ticket.customer_card
    message = models.ContactPersonMessageModel.objects.get(pk=message_id)
    event_type = event_types.NewTicketClientMessageForSpecialist()
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=ticket, obj=message)    
    return 'done.'


def notify_about_new_ticket_specialist_message(ticket_id, message_id):
    """Уведомление клиенту о новом сообщение от специалиста в тикете."""
    ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    message = models.ContactPersonMessageModel.objects.get(pk=message_id)
    initiator = message.author
    contact_person = ticket.contact_person
    recipients = []
    if contact_person:
        contact_person_user = contact_person.user
        if contact_person_user:
            recipients = [contact_person_user, ]
    if recipients:
        event_type = event_types.NewTicketSpecialistMessageForClient()
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=ticket, obj=message)
        return 'done.'
    else:
        return 'no contact person user'


def notify_about_assign_specialist(ticket_id, specialist_id):
    """Уведомление специалисту о назначении тикета."""
    ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    specialist = ProfileModel.objects.filter(pk=specialist_id)
    event_type = event_types.TicketSpecialistAssign()
    event_type.create_notification(recipients=tuple(specialist), subj=ticket,)
    return 'done.'


def notify_about_assign_member(ticket_id: str, members_id: list):
    ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    members = ProfileModel.objects.filter(pk__in=members_id)
    event_type = event_types.TicketMemberAssign()
    event_type.create_notification(recipients=tuple(members), subj=ticket)


def notify_about_new_status(user_id, ticket_id, status_code):

    ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    status = models.HelpDeskTicketStatusModel.objects.get(code=status_code)
    contact_person_user = ticket.contact_person.user

    if contact_person_user:
        event_type = event_types.TicketStatusNew()
        event_type.create_notification(recipients=(contact_person_user,), subj=ticket, obj=status)
    user = ProfileModel.objects.filter(pk=user_id).first()
    recipients = set()
    specialist = ticket.specialist
    if specialist:
        recipients.add(specialist.pk)
    visors = set(ticket.visors.all().values_list('pk', flat=True))
    members = set(ticket.members.all().values_list('pk', flat=True))
    recipients = recipients | visors | members
    if user:
        recipients.discard(user.pk)
    if recipients:
        event_type = event_types.TicketStatusNewSpecialist()
        event_type.create_notification(recipients=tuple(recipients), subj=ticket, obj=status)
    # message_text = f'Өтініш №{ticket.number} күйі «{status.name_kk}» болып өзгертілді. \n ' \
    #                f'Обращение №{ticket.number} сменило статус на "{status.name_ru}"'
    message_text = f'Обращение №{ticket.number} сменило статус на "{status.name_ru}"'
    send_notify_for_channel(ticket, message_text)


def send_notify_for_channel(ticket, message_text):
    try:
        config = ticket.customer_card.org_admin.help_desk_config
    except ObjectDoesNotExist:
        config = None
    channel = ticket.channel

    if channel.code == 'telegram' and config:
        telegram_id = ticket.contact_person.telegram_id
        if not telegram_id:
            return
        with transaction.atomic():
            message = models.ContactPersonMessageModel()
            message.text = message_text
            message.contact_person = ticket.contact_person
            message.channel = channel
            message.is_help_desk = True
            message.save(ticket=ticket)
            transaction.on_commit(lambda: utils.send_tg_message(config, telegram_id, message))
    elif channel.code == 'email' and config:
        email_address = ticket.contact_person.email
        if not email_address:
            return

        with transaction.atomic():
            message = models.ContactPersonMessageModel()
            message.email_subject = f"Обращение # {ticket.number}"
            last_message = ticket.messages.filter(is_active=True).order_by('-created_at').first()
            email_subject = last_message.email_subject
            if not email_subject:
                email_subject = f"Обращение #{ticket.number}"
            if email_subject:
                if email_subject.lower().startswith('re: '):
                    message.email_subject = email_subject
                else:
                    message.email_subject = f"Re: {email_subject}"
            message.message_id = utils.get_message_id(config)
            message.text = message_text
            message.contact_person = ticket.contact_person
            message.channel = channel
            message.message_date = timezone.now()
            message.is_help_desk = True
            message.save(ticket=ticket)
            transaction.on_commit(lambda: utils.send_email(config, email_address, message))
    elif channel.code == 'internal_chat':
        chat_message = utils.get_ticket_first_chat_message(ticket)
        if not chat_message:
            return
        chat = chat_message.chat
        with transaction.atomic():
            message = models.ContactPersonMessageModel()
            message.text = message_text
            message.contact_person = ticket.contact_person
            message.channel = channel
            message.message_date = timezone.now()
            message.is_help_desk = True
            message.save(ticket=ticket)
            if chat.is_public:
                transaction.on_commit(lambda: utils.send_internal_chat_message(chat, message, chat_message, ticket))
    elif channel.code == 'internal':
        with transaction.atomic():
            message = models.ContactPersonMessageModel()
            message.text = message_text
            message.contact_person = ticket.contact_person
            message.channel = channel
            message.message_date = timezone.now()
            message.is_help_desk = True
            message.save(ticket=ticket)


def send_email_invite(contact_person: models.ContactPersonModel):
    with transaction.atomic():
        notification = notification_models.EmailNotificationModel.objects.create(
            template='helpdesk_email_invite',
            subject='Приглашение',
            context={
                "company_name": COMPANY_NAME,
                "url": get_invite_url(contact_person.invite_token),
                "contact_person_name": contact_person.name,
                "org_admin_name": contact_person.customer_card.org_admin.name
            }
        )
        notification_models.EmailNotificationRecipientModel.objects.create(
            recipient=contact_person.email,
            email_notification=notification
        )
        contact_person.letter_sent = True
        contact_person.letter_sent_date = timezone.now()
        contact_person.save(update_fields=('letter_sent', 'letter_sent_date',))
    send_email(notification.pk)
