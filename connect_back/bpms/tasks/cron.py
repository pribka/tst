import datetime

from django.utils import timezone

from . import models


def delete_void_logistic_tasks(expire: int = 60):
    now = timezone.now()
    expire_date = now - datetime.timedelta(minutes=expire)
    tasks = models.TaskModel.objects.filter(
        is_active=True,
        task_type_id='logistic',
        task_delivery_points__isnull=True,
        updated_at__lte=expire_date
    )
    tasks_count = tasks.count()
    for each in tasks:
        each.is_active = False
        each.save(update_fields=('is_active',))
    return f'deleted {tasks_count} logistic tasks'
