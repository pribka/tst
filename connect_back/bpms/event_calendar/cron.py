from django.utils import timezone
from django.db.models import Q

from . import models

from notifications.event_types import EventCalendarMention


def notify_event_mention(instance_count=100):
    notification = EventCalendarMention()
    now = timezone.now()
    events = models.EventCalendarModel.objects.filter(
        Q(is_notified=False) | Q(event_members__is_notified=False),
        is_active=True,
        calendar__is_active=True,
        is_finished=False,
        start_at__gte=now,
        notify_at__lte=now,
    ).order_by('notify_at').distinct()[:instance_count]
    event_log_list = []
    for event in events:
        recipients = []
        if not event.is_notified:
            recipients.append(event.author_id)
        members = list(event.event_members.filter(is_notified=False).values_list('user', flat=True))
        recipients = set(recipients + members)
        recipients.discard(None)
        if recipients:
            notification.create_notification(tuple(recipients), subj=event)
        event.is_notified = True
        event.save()
        event.event_members.filter(is_notified=False).update(is_notified=True)
        event_log_list.append(f'{event.pk} {event.name} ')
    return event_log_list


