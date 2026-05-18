import logging
import os
import json
from typing import Dict, Iterable, Optional

import firebase_admin
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from firebase_admin import credentials, messaging
from pywebpush import WebPushException, webpush

from .models import MobilePushDeviceModel, WebNotificationModel, WebPushSubscriptionModel

logger = logging.getLogger(__name__)


def _get_service_account_path() -> str:
    return str(getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH', '') or '').strip()


def _get_service_account_info() -> Dict:
    service_account_info = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_INFO', None)
    if isinstance(service_account_info, dict):
        return service_account_info
    return {}


def get_firebase_app():
    service_account_info = _get_service_account_info()
    service_account_path = _get_service_account_path()
    if not service_account_info and not service_account_path:
        return None

    credential_source = service_account_info
    if not credential_source:
        if not os.path.exists(service_account_path):
            logger.warning(
                'Firebase service account file not found: %s',
                service_account_path,
            )
            return None
        credential_source = service_account_path

    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(credential_source)
        return firebase_admin.initialize_app(cred)


def _normalize_data(data: Optional[Dict] = None) -> Dict[str, str]:
    payload: Dict[str, str] = {}
    for key, value in (data or {}).items():
        if value is None:
            continue
        payload[str(key)] = str(value)
    return payload


def _deactivate_invalid_device(device: MobilePushDeviceModel, error_text: str) -> None:
    lowered = error_text.lower()
    if 'unregistered' not in lowered and 'not a valid fcm registration token' not in lowered:
        return
    device.is_active = False
    device.last_error = error_text[:2000]
    device.last_seen_at = timezone.now()
    device.save(update_fields=('is_active', 'last_error', 'last_seen_at'))


def _deactivate_subscription(subscription: WebPushSubscriptionModel, error_text: str) -> None:
    subscription.is_active = False
    subscription.last_error = error_text[:2000]
    subscription.last_seen_at = timezone.now()
    subscription.save(update_fields=('is_active', 'last_error', 'last_seen_at'))


def send_web_push_notifications_for_payload(
    *,
    recipients: Optional[Iterable[str]] = None,
    notification_id: str,
    title: str,
    body: str,
    url: str = '',
) -> Dict[str, int]:
    if not bool(getattr(settings, 'WEBPUSH_ENABLED', False)):
        return {'sent': 0, 'failed': 0, 'skipped': 0}
    public_key = str(getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', '') or '').strip()
    private_key = str(getattr(settings, 'WEBPUSH_VAPID_PRIVATE_KEY', '') or '').strip()
    if not (public_key and private_key):
        logger.warning('Web push skipped: VAPID credentials are missing.')
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    recipient_ids = list(recipients or [])
    subscriptions = WebPushSubscriptionModel.objects.filter(is_active=True)
    if recipient_ids:
        subscriptions = subscriptions.filter(profile_id__in=recipient_ids)

    subscriptions_list = list(subscriptions)
    if not subscriptions_list:
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    payload = {
        'notification_id': str(notification_id),
        'title': str(title or ''),
        'body': str(body or ''),
        'click_action': str(url or settings.FRONTEND_URL),
    }
    sent = 0
    failed = 0
    now = timezone.now()

    for subscription in subscriptions_list:
        subscription_data = {
            'endpoint': subscription.endpoint,
            'keys': {
                'auth': subscription.auth,
                'p256dh': subscription.p256dh,
            },
        }
        try:
            webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload, ensure_ascii=False, cls=DjangoJSONEncoder),
                vapid_private_key=private_key,
                vapid_claims={'sub': settings.WEBPUSH_VAPID_SUBJECT},
            )
            sent += 1
            subscription.last_error = ''
            subscription.last_seen_at = now
            subscription.save(update_fields=('last_error', 'last_seen_at'))
        except WebPushException as error:
            failed += 1
            status_code = None
            response = getattr(error, 'response', None)
            if response is not None:
                status_code = getattr(response, 'status_code', None)
            error_text = str(error)
            if status_code in (404, 410):
                _deactivate_subscription(subscription, error_text)
                continue
            subscription.last_error = error_text[:2000]
            subscription.last_seen_at = now
            subscription.save(update_fields=('last_error', 'last_seen_at'))
            logger.exception(
                'Failed to send web push subscription_id=%s profile_id=%s',
                subscription.id,
                subscription.profile_id,
            )
        except Exception as error:  # noqa: BLE001
            failed += 1
            error_text = str(error)
            subscription.last_error = error_text[:2000]
            subscription.last_seen_at = now
            subscription.save(update_fields=('last_error', 'last_seen_at'))
            logger.exception(
                'Failed to send web push subscription_id=%s profile_id=%s',
                subscription.id,
                subscription.profile_id,
            )

    return {'sent': sent, 'failed': failed, 'skipped': 0}


def send_data_push_to_devices(
    devices: Iterable[MobilePushDeviceModel],
    *,
    data: Optional[Dict] = None,
    high_priority: bool = False,
    show_system_notification: bool = False,
    notification_title: str = '',
    notification_body: str = '',
    android_channel_id: str = '',
) -> Dict[str, int]:
    app = get_firebase_app()
    devices = [device for device in devices if device.is_active and device.token]
    if app is None or not devices:
        logger.info(
            'Push send skipped app_ready=%s devices=%s type=%s',
            app is not None,
            len(devices),
            (data or {}).get('type', ''),
        )
        return {'sent': 0, 'failed': 0, 'skipped': len(devices)}

    payload = _normalize_data(data)
    sent = 0
    failed = 0
    now = timezone.now()

    base_notification = None
    normalized_title = notification_title.strip()
    normalized_body = notification_body.strip()
    if show_system_notification and (normalized_title or normalized_body):
        base_notification = messaging.Notification(
            title=normalized_title or None,
            body=normalized_body or None,
        )

    for device in devices:
        android_config = None
        apns_config = None

        if device.push_provider == MobilePushDeviceModel.PROVIDER_FCM:
            android_notification = None
            if show_system_notification:
                android_notification = messaging.AndroidNotification(
                    channel_id=android_channel_id or None,
                    sound='default',
                    tag=payload.get('type', ''),
                )

            android_config = messaging.AndroidConfig(
                priority='high' if high_priority else 'normal',
                notification=android_notification,
            )
            apns_config = messaging.APNSConfig(
                headers={
                    'apns-priority': '10' if high_priority else '5',
                    'apns-push-type': 'background',
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(content_available=True),
                ),
            )

        message = messaging.Message(
            token=device.token,
            data=payload,
            notification=base_notification,
            android=android_config,
            apns=apns_config,
        )

        try:
            messaging.send(message, app=app)
            sent += 1
            device.last_error = ''
            device.last_seen_at = now
            device.save(update_fields=('last_error', 'last_seen_at'))
            logger.info(
                'Push sent profile_id=%s device_id=%s platform=%s provider=%s type=%s system_notification=%s',
                device.profile_id,
                device.id,
                device.platform,
                device.push_provider,
                payload.get('type', ''),
                show_system_notification,
            )
        except Exception as error:  # noqa: BLE001
            failed += 1
            error_text = str(error)
            device.last_error = error_text[:2000]
            device.last_seen_at = now
            device.save(update_fields=('last_error', 'last_seen_at'))
            _deactivate_invalid_device(device, error_text)
            logger.exception(
                'Failed to send Firebase push device_id=%s profile_id=%s',
                device.id,
                device.profile_id,
            )

    return {'sent': sent, 'failed': failed, 'skipped': 0}


def send_meeting_invite_push(notification: WebNotificationModel) -> dict:
    if notification.event_type_id != 'meetings_start_new_meeting_notification':
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    recipient_ids = list(notification.recipients.values_list('id', flat=True))
    if not recipient_ids:
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    meeting_data = notification.data.get('subj') if isinstance(notification.data, dict) else {}
    if not isinstance(meeting_data, dict):
        meeting_data = {}

    payload = {
        'type': 'meeting_invite',
        'source': 'meeting_start',
        'notification_id': notification.id,
        'meeting_id': meeting_data.get('id', ''),
        'meeting_name': meeting_data.get('name', ''),
        'open_url': notification.url,
        'title': 'Началось собрание',
        'body': notification.body,
        'ring_timeout_sec': 30,
        'sent_at': notification.created_at.isoformat() if notification.created_at else '',
    }

    devices = MobilePushDeviceModel.objects.filter(
        profile_id__in=recipient_ids,
        is_active=True,
        push_provider=MobilePushDeviceModel.PROVIDER_FCM,
    ).exclude(token='')

    logger.info(
        'Preparing meeting invite push notification_id=%s recipients=%s devices=%s url=%s',
        notification.id,
        len(recipient_ids),
        devices.count(),
        notification.url,
    )

    return send_data_push_to_devices(
        devices,
        data=payload,
        high_priority=True,
        # Send meeting invites as data-only so Android can start the call flow
        # from the background handler without waiting for a notification tap.
        show_system_notification=False,
        notification_title='Началось собрание',
        notification_body=(notification.body or 'Откройте приглашение в Connect.'),
        android_channel_id='connect_meeting_invites',
    )


def send_call_start_push(notification: WebNotificationModel) -> dict:
    if notification.event_type_id != 'call_start_notification':
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    recipient_ids = list(notification.recipients.values_list('id', flat=True))
    if not recipient_ids:
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    call_data = notification.data.get('subj') if isinstance(notification.data, dict) else {}
    if not isinstance(call_data, dict):
        call_data = {}

    status_data = call_data.get('status') if isinstance(call_data.get('status'), dict) else {}
    meeting_data = call_data.get('meeting') if isinstance(call_data.get('meeting'), dict) else {}
    initiator_data = call_data.get('initiator') if isinstance(call_data.get('initiator'), dict) else {}
    current_target_data = call_data.get('current_target') if isinstance(call_data.get('current_target'), list) else []
    accepted_by_data = call_data.get('accepted_by') if isinstance(call_data.get('accepted_by'), dict) else {}

    payload = {
        'type': 'call_invite',
        'source': 'call_start',
        'notification_id': notification.id,
        'call_id': call_data.get('id', ''),
        'call_status': status_data.get('code', ''),
        'initiator_id': initiator_data.get('id', ''),
        'current_target_ids': [target_data.get('id', '') for target_data in current_target_data if isinstance(target_data, dict)],
        'accepted_by_id': accepted_by_data.get('id', ''),
        'meeting_id': meeting_data.get('id', ''),
        'open_url': meeting_data.get('url_external', ''),
        'title': 'Начался звонок',
        'body': notification.body or 'Откройте звонок в Connect.',
        'sent_at': notification.created_at.isoformat() if notification.created_at else '',
    }

    devices = MobilePushDeviceModel.objects.filter(
        profile_id__in=recipient_ids,
        is_active=True,
        push_provider=MobilePushDeviceModel.PROVIDER_FCM,
    ).exclude(token='')

    logger.info(
        'Preparing call start push notification_id=%s recipients=%s devices=%s call_id=%s url=%s',
        notification.id,
        len(recipient_ids),
        devices.count(),
        payload.get('call_id', ''),
        payload.get('open_url', ''),
    )

    return send_data_push_to_devices(
        devices,
        data=payload,
        high_priority=True,
        show_system_notification=False,
        notification_title='Начался звонок',
        notification_body=(notification.body or 'Откройте звонок в Connect.'),
        android_channel_id='connect_calls',
    )


def send_call_updated_push(notification: WebNotificationModel) -> dict:
    if notification.event_type_id != 'call_updated_notification':
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    recipient_ids = list(notification.recipients.values_list('id', flat=True))
    if not recipient_ids:
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    call_data = notification.data.get('subj') if isinstance(notification.data, dict) else {}
    if not isinstance(call_data, dict):
        call_data = {}

    status_data = call_data.get('status') if isinstance(call_data.get('status'), dict) else {}
    meeting_data = call_data.get('meeting') if isinstance(call_data.get('meeting'), dict) else {}
    initiator_data = call_data.get('initiator') if isinstance(call_data.get('initiator'), dict) else {}
    current_target_data = call_data.get('current_target') if isinstance(call_data.get('current_target'), list) else []
    accepted_by_data = call_data.get('accepted_by') if isinstance(call_data.get('accepted_by'), dict) else {}

    payload = {
        'type': 'call_update',
        'source': 'call_updated',
        'notification_id': notification.id,
        'call_id': call_data.get('id', ''),
        'call_status': status_data.get('code', ''),
        'initiator_id': initiator_data.get('id', ''),
        'current_target_ids': [target_data.get('id', '') for target_data in current_target_data if isinstance(target_data, dict)],
        'accepted_by_id': accepted_by_data.get('id', ''),
        'meeting_id': meeting_data.get('id', ''),
        'open_url': meeting_data.get('url_external', ''),
        'title': 'Статус звонка изменился',
        'body': notification.body or 'Изменился статус звонка.',
        'sent_at': notification.created_at.isoformat() if notification.created_at else '',
    }

    devices = MobilePushDeviceModel.objects.filter(
        profile_id__in=recipient_ids,
        is_active=True,
        push_provider=MobilePushDeviceModel.PROVIDER_FCM,
    ).exclude(token='')

    logger.info(
        'Preparing call updated push notification_id=%s recipients=%s devices=%s call_id=%s new_status=%s',
        notification.id,
        len(recipient_ids),
        devices.count(),
        payload.get('call_id', ''),
        payload.get('call_status', ''),
    )

    return send_data_push_to_devices(
        devices,
        data=payload,
        high_priority=True,
        show_system_notification=False,
        notification_title='Статус звонка изменился',
        notification_body=(notification.body or 'Изменился статус звонка.'),
        android_channel_id='connect_calls',
    )
