"""
Синхронизация завершённого user_day_summary в DaySummaryNoteModel.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task

from analytics.models import ActivitySummaryModel

from .models import DaySummaryNoteModel
from .notifications import send_notify_day_summary_ready


@receiver(post_save, sender=ActivitySummaryModel)
def sync_user_day_summary_to_note(sender, instance, **kwargs):
    if instance.scope != "user_day_summary" or instance.status != "completed":
        return
    if not instance.user_id:
        return
    note = DaySummaryNoteModel.objects.create(
        author=instance.user,
        date=instance.end_date,
        content=instance.summary,
        is_ai_summary=True,
    )
    async_task(send_notify_day_summary_ready, str(note.pk))
