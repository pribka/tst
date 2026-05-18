from notifications.event_types import EventCalendarCreate, EventCalendarEscape, EventCalendarChangeDates


def notify_about_new_event(event, recipients=None):
    event_type = EventCalendarCreate()
    if recipients is None:
        recipients = set(event.members.all())
        recipients.discard(event.author)
    if recipients:
        event_type.create_notification(tuple(recipients), subj=event)


def notify_about_escape_from_event(event, user):
    event_type = EventCalendarEscape()
    recipient = event.author
    if recipient:
        event_type.create_notification((recipient,), subj=event, obj=user)


def notify_about_change_dates(event, user):
    event_type = EventCalendarChangeDates()
    recipients = list(event.members.all())
    recipients.append(event.author)
    recipients = set(recipients)
    recipients.discard(None)
    recipients.discard(user)
    if recipients:
        event_type.create_notification(tuple(recipients), subj=event, obj=user)
