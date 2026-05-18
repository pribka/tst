# myapp/signals.py
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_q.tasks import async_task

from bpms.tasks import models as t_models

from . import models as wl_models
from . import utils
from users import models as u_models


@receiver(post_save, sender=u_models.ProfileModel)
def add_schedule(sender, instance, created, **kwargs):
    if created:
        wl_models.WorkScheduleModel.objects.create(profile=instance)


@receiver(post_save, sender=wl_models.ExceptionModel)
def exception_create_or_update(sender, instance, created, **kwargs):
    instance = instance

    if not created:
        (
            wl_models.ExceptionDatesModel.objects
            .filter(exception=instance).delete()
        )
        async_task(utils.signal_exception_dates_create_and_update, instance)

    if created:
        async_task(utils.signal_exception_dates_create_and_update, instance)


# @receiver(post_save, sender=t_models.TaskModel)
# def task_created_or_updated(sender, instance, created, **kwargs):
#     instance = instance
#     profile = instance.operator

#     try:
#         start_date = instance.date_start_plan.date()
#         end_date = instance.dead_line.date()
#         date_range = utils.get_dates_range(start_date, end_date)
#     except:  # noqa: E722
#         date_range = []

#     if not created:
#         workload_set = wl_models.WorkLoadModel.objects.filter(tasks=instance)
#         if not instance.is_active:
#             for workload in workload_set:
#                 utils.signal_remove_task(workload, instance, profile)
#         if workload_set.values_list('date') not in date_range:
#             for workload in workload_set:
#                 workload.tasks.remove(instance)
#                 workload.save()
#         if instance.is_active:
#             utils.signal_add_tasks(instance, date_range, profile)

#     if created:
#         utils.signal_add_tasks(instance, date_range, profile)


# @receiver(post_delete, sender=t_models.TaskModel)
# def task_delete(sender, instance, **kwargs):
#     workload = wl_models.WorkLoadModel.objects.filter(tasks=instance)
#     for date in workload:
#         date.tasks.remove(instance)
#         date.save()


@receiver(post_save, sender=wl_models.TaskDurationModel)
def task_update(sender, instance, created, **kwargs):
    if not created:
        task = t_models.TaskModel.objects.get(duration=instance)
        task.save()
