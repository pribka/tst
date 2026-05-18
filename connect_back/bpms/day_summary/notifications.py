from notifications import event_types

from .models import DaySummaryNoteModel


def send_notify_day_summary_ready(day_summary_note_id):
    note = DaySummaryNoteModel.objects.filter(pk=day_summary_note_id).first()
    if not note or not note.author_id:
        return
    event_type = event_types.DaySummaryReady()
    event_type.create_notification(
        recipients=(note.author,),
        subj=note,
    )
