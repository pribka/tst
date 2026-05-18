from django.utils import timezone
from django.db.models import Q

from notifications.event_types import (UpdateObjectiveReminderWeekly, UpdateObjectiveReminderFortnightly,
                                       UpdateObjectiveReminderMonthly, UpdateObjectiveReminderQuarterly)

from . import models
from .utils import calculate_next_notification_run


def update_objective_reminder(instance_count=100):
    """Рассылка напоминаний о необходимости актуализировать цель и ее ключевые результаты.
    Оповещаем постановщика, ответственого за цель, ответственных за ключевые результаты цели."""
    notification_classes = {
        'weekly': UpdateObjectiveReminderWeekly,
        'fortnightly': UpdateObjectiveReminderFortnightly,
        'monthly': UpdateObjectiveReminderMonthly,
        'quarterly': UpdateObjectiveReminderQuarterly,
    }
    now = timezone.now()
    objectives = models.ObjectivesModel.objects.filter(
        is_active=True,
        status__is_closed=False,
        notify_at__lte=now,
    ).order_by('notify_at').distinct()[:instance_count]
    objectives_log_list = []
    for objective in objectives:
        notification_class = notification_classes.get(objective.notification_id)
        if notification_class:
            notification = notification_class()
        else:
            return
        if objective.is_public:
            recipients = []
            recipients.extend([objective.author_id, objective.owner_id, objective.operator_id]) # TODO должно ли приходить уведомление автору?
            key_result_operators = list(objective.key_results.filter(is_active=True).values_list('operator', flat=True))
            recipients = set(recipients + key_result_operators)
            recipients.discard(None)
        else:
            recipients = set([objective.author_id])
        if recipients:
            notification.create_notification(tuple(recipients), subj=objective)
        objective.notify_at = calculate_next_notification_run(
            objective.notification.code,
            objective.notification.cron,
            objective.date_start,
            objective.date_end)
        objective.save()
        objectives_log_list.append(f'{objective.pk} {objective.objective} ')
    return objectives_log_list


