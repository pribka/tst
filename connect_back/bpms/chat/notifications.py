from . import models

from notifications import event_types


def send_notify_about_mentions(message_id):
    message = models.MessageModel.objects.get(pk=message_id)
    mentions = message.mentions.all().values_list('pk', flat=True)
    event_type = event_types.ChatMention()
    event_type.create_notification(recipients=tuple(mentions), subj=message)


def send_notify_about_summary_ready(chat_summary_id):
    chat_summary = models.ChatSummaryModel.objects.select_related(
        'chat'
    ).prefetch_related(
        'chat__members__user'
    ).get(pk=chat_summary_id)
    event_type = event_types.ChatSummaryReady()
    event_type.create_notification(recipients=(chat_summary.user,), subj=chat_summary)
