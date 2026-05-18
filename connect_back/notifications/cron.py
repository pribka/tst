from datetime import timedelta

from django.utils import timezone

from .models import WebPushSubscriptionModel


def delete_inactive_web_push_subscriptions(retention_days: int = 30):
    """Удаляет неактивные web-push подписки старше retention_days."""
    cutoff_time = timezone.now() - timedelta(days=retention_days)
    WebPushSubscriptionModel.objects.filter(
        is_active=False,
        last_seen_at__lt=cutoff_time,
    ).delete()
