from users.models import ProfileModel
from notifications import event_types
from bpms.bpms_common.models import NewsModel


def notify_about_new_news(news, initiator):
    recipients = set(ProfileModel.objects.filter(is_active=True))  # TODO убрать публикующего новость после тестов
    recipients.discard(initiator)
    event_type = event_types.NewIndependentNewsCreated()
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=news)
    return 'done'
