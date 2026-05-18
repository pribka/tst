from notifications import event_types
from notifications.models import MobilePushDeviceModel
from notifications.push import (
    send_data_push_to_devices,
    send_meeting_invite_push,
)
from . import models


def notify_about_invite_to_meeting(meeting, recipients):
    initiator = meeting.author
    event_type = event_types.InviteToMeeting()
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=meeting)
    return 'done'


def notify_about_start_meeting(meeting, initiator, notify_user_ids=None):
    """
    notify_user_ids: None = всем участникам кроме инициатора; [] = никому; [uuid, ...] = только перечисленным.
    """
    if notify_user_ids is not None:
        recipients = meeting.members.filter(pk__in=notify_user_ids).exclude(pk=initiator.pk).distinct()
    else:
        recipients = meeting.members.exclude(user=initiator.user).distinct()
    if not recipients.exists():
        return 'no recipients'
    event_type = event_types.MeetingStart()
    notification = event_type.create_notification(
        recipients=tuple(recipients),
        initiator=initiator,
        subj=meeting,
    )
    if notification is not None:
        send_meeting_invite_push(notification)
    return 'done'


def notify_about_call_updated_notification(call_obj, initiator, recipients):
    """Обычное уведомление об изменении состояния звонка (без push)."""
    recipients_profile_ids = tuple(recipients or tuple())
    if not recipients_profile_ids:
        return 'no recipients'
    event_type = event_types.CallUpdated()
    event_type.create_notification(
        recipients=recipients_profile_ids,
        initiator=initiator,
        subj=call_obj,
        ticket=call_obj.ticket,
    )
    return 'done'


def notify_about_start_call_notification(call_obj, initiator, recipients):
    """Обычное уведомление о старте звонка (без push)."""
    recipients_profile_ids = tuple(recipients or tuple())
    if not recipients_profile_ids:
        return 'no recipients'
    event_type = event_types.CallStart()
    event_type.create_notification(
        recipients=recipients_profile_ids,
        initiator=initiator,
        subj=call_obj,
        ticket=call_obj.ticket,
    )
    return 'done'


def _send_call_push_without_notification(
    call_obj,
    recipients,
    initiator,
    push_type,
    source,
    title,
    default_body,
    old_status=None,
    extra_payload=None,
):
    recipients_profile_ids = tuple(set(recipients or tuple()))
    if not recipients_profile_ids:
        return 'no recipients'

    serializer_class = models.CallModel.get_serializer_class(action='notify')
    call_data = serializer_class(instance=call_obj).data
    message = {
        'event_type': source,
        'call': call_data,
        'old_status': old_status,
        'new_status': str(getattr(call_obj, 'status_id', '')),
    }
    if isinstance(extra_payload, dict) and extra_payload.get('receiver_id'):
        message['receiver_id'] = extra_payload.get('receiver_id')

    payload = {
        'type': push_type,
        'source': source,
        'message': message,
        'notification_id': '',
        'title': title,
        'body': default_body,
        'sent_at': '',
    }
    if isinstance(extra_payload, dict):
        payload.update(extra_payload)

    devices = MobilePushDeviceModel.objects.filter(
        profile_id__in=recipients_profile_ids,
        is_active=True,
        push_provider=MobilePushDeviceModel.PROVIDER_FCM,
    ).exclude(token='')

    send_data_push_to_devices(
        devices,
        data=payload,
        high_priority=True,
        show_system_notification=False,
        notification_title=title,
        notification_body=default_body,
        android_channel_id='connect_calls',
    )
    return 'done'


def notify_about_start_call_push(call_obj, recipients):
    """Push о старте звонка без создания web notification."""
    return _send_call_push_without_notification(
        call_obj=call_obj,
        recipients=recipients,
        initiator=call_obj.initiator,
        push_type='call_invite',
        source='call_created',
        title='Начался звонок',
        default_body='Откройте звонок в Connect.',
    )


def notify_about_call_updated_push(call_obj, initiator, recipients, old_status=None):
    """Push об изменении состояния звонка без создания web notification."""
    return _send_call_push_without_notification(
        call_obj=call_obj,
        recipients=recipients,
        initiator=initiator,
        push_type='call_update',
        source='call_updated',
        title='Статус звонка изменился',
        default_body='Изменился статус звонка.',
        old_status=old_status,
    )


def notify_about_call_receiver_presence_push(call_obj, receiver, recipients):
    """Push о том, что получатель на связи и слышит звонок."""
    return _send_call_push_without_notification(
        call_obj=call_obj,
        recipients=recipients,
        initiator=call_obj.initiator,
        push_type='call_presence',
        source='call_receiver_presence',
        title='Собеседник на связи',
        default_body='Получатель слышит звонок.',
        extra_payload={'receiver_id': str(receiver.pk)},
    )


def notify_about_call_receiver_joined_bbb_push(call_obj, receiver, recipients):
    """Push о том, что получатель полностью подключился к BBB."""
    return _send_call_push_without_notification(
        call_obj=call_obj,
        recipients=recipients,
        initiator=call_obj.initiator,
        push_type='call_receiver_joined_bbb',
        source='call_receiver_joined_bbb',
        title='Собеседник подключился',
        default_body='Получатель полностью подключился к звонку.',
        extra_payload={'receiver_id': str(receiver.pk)},
    )


def notify_about_set_record_ready(meeting):
    recipients = [meeting.author]
    event_type = event_types.MeetingSetRecordReady()
    event_type.create_notification(recipients=tuple(recipients), subj=meeting)
    return 'done'


def notify_about_record_summary_ready(section: models.MeetingSectionModel):
    members_qs = section.members.all()
    if not members_qs.exists():
        return 'no recipients'
    recipients = tuple(members_qs)

    event_type = event_types.MeetingSummaryReady()
    event_type.create_notification(recipients=recipients, subj=section.meeting)
    return 'done'
