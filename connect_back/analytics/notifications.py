from . import models
from notifications import event_types


def send_notify_about_activity_summary_ready(activity_summary_id):
    activity_summary = models.ActivitySummaryModel.objects.get(
        pk=activity_summary_id, is_active=True
    )
    if not activity_summary.user_id:
        return
    event_type = event_types.ActivitySummaryReady()
    event_type.create_notification(
        recipients=(activity_summary.user,),
        subj=activity_summary,
    )
