from notifications import event_types
from users.models import ProfileModel


def notify_about_new_base_1c_ticket(ticket, initiator):
    event_type = event_types.New1CTicketEvent()
    recipients = ProfileModel.objects.filter(
        is_active=True,
        profile_type__code='administrator_1c'
    )
    event_type.create_notification(recipients=recipients,
                                   initiator=initiator,
                                   subj=ticket)
    return 'done.'


def notify_ticket_has_approved(ticket, initiator, recipient):
    event_type = event_types.Ticket1CHasApprovedEvent()
    event_type.create_notification(recipients=(recipient, ),
                                   initiator=initiator,
                                   subj=ticket)
    return 'done.'


def notify_ticket_has_rejected(ticket, initiator, recipient):
    event_type = event_types.Ticket1CHasRejectedEvent()
    event_type.create_notification(recipients=(recipient, ),
                                   initiator=initiator,
                                   subj=ticket)
    return 'done.'
