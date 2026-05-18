import json
from datetime import timedelta

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task, schedule

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL
from common.redis import socketio_redis
from bpms.chat.models import ChatModel
from contractor_permissions.utils import contractors_where_user_has_app_section_role_permission
from help_desk import models as help_desk_models
from help_desk import utils as help_desk_utils
from help_desk import serializers as help_desk_serializers
from rest_framework import exceptions as drf_exceptions
from users.models import ProfileModel

from . import models
from . import serializers as meetings_serializers

RING_TIMEOUT_SECONDS = 5
RING_TIMEOUT_SECONDS_SINGLE_TARGET = 20


def get_current_target_ids(call_obj: models.CallModel):
    return list(call_obj.current_target.values_list('pk', flat=True))


def set_current_targets(call_obj: models.CallModel, target_ids):
    target_ids_to_set = [target_id for target_id in (target_ids or []) if target_id]
    call_obj.current_target.set(target_ids_to_set)


def get_call_recipients(call_obj: models.CallModel):
    recipients = set()
    if call_obj.initiator_id:
        recipients.add(call_obj.initiator_id)
    if call_obj.accepted_by_id:
        recipients.add(call_obj.accepted_by_id)
    recipients.update(get_current_target_ids(call_obj))

    ticket = call_obj.ticket
    if ticket is not None:
        if ticket.specialist_id:
            recipients.add(ticket.specialist_id)
        contact_person = ticket.contact_person
        if contact_person and contact_person.user_id:
            recipients.add(contact_person.user_id)

        specialist_ids = ticket.customer_card.actual_specialists.filter(
            is_active=True,
            accepts_calls=True,
        ).values_list('user_id', flat=True)
        recipients.update(specialist_ids)
    elif call_obj.chat_id:
        chat_member_ids = call_obj.chat.members.filter(is_active=True).values_list('user_id', flat=True)
        recipients.update(chat_member_ids)
    return recipients


def get_call_notification_recipients(call_obj: models.CallModel):
    recipients = set()
    if call_obj.initiator_id:
        recipients.add(call_obj.initiator_id)
    if call_obj.accepted_by_id:
        recipients.add(call_obj.accepted_by_id)
    recipients.update(get_current_target_ids(call_obj))
    return recipients


def _get_specialists_queue(ticket: help_desk_models.HelpDeskTicketModel):
    specialists_qs = ticket.customer_card.actual_specialists.filter(
        is_active=True,
        accepts_calls=True,
    ).order_by(
        'is_reserve',
        'call_priority',
        'id',
    )
    return list(specialists_qs.values_list('user_id', flat=True))


def _get_same_priority_target_ids(ticket: help_desk_models.HelpDeskTicketModel, queue_ids):
    if not queue_ids:
        return []
    specialists_qs = ticket.customer_card.actual_specialists.filter(
        is_active=True,
        accepts_calls=True,
        user_id__in=queue_ids,
    ).values('user_id', 'is_reserve', 'call_priority')
    priority_by_user_id = {
        specialist_data['user_id']: (specialist_data['is_reserve'], specialist_data['call_priority'])
        for specialist_data in specialists_qs
    }
    first_target_id = queue_ids[0]
    first_priority_key = priority_by_user_id.get(first_target_id)
    if first_priority_key is None:
        return [first_target_id]
    return [
        target_id for target_id in queue_ids
        if priority_by_user_id.get(target_id) == first_priority_key
    ]


def _get_contact_person_user_id(ticket: help_desk_models.HelpDeskTicketModel):
    contact_person = ticket.contact_person
    if not contact_person:
        return None
    return contact_person.user_id


def _is_current_customer_specialist(ticket: help_desk_models.HelpDeskTicketModel, profile_id):
    if not ticket.customer_card_id:
        return False
    return ticket.customer_card.customer_support_specialists.filter(
        user_id=profile_id,
        is_active=True,
    ).exists()


def _get_call_queue_ids(call_obj: models.CallModel):
    current_target_ids = get_current_target_ids(call_obj)
    ticket = call_obj.ticket
    if ticket is None:
        if current_target_ids:
            return current_target_ids
        return []

    # Звонок из чата всегда направлен ровно одному человеку.
    # Даже если в модели уже есть ticket, очередь специалистов не нужна.
    if call_obj.chat_id is not None:
        if current_target_ids:
            return current_target_ids
        return []

    contact_person_user_id = _get_contact_person_user_id(ticket)

    # Если звонок инициирован контактным лицом обращения и у тикета есть ответственный специалист,
    # то дозваниваемся только ему и дальше не расширяем очередь.
    if (
        ticket.specialist_id
        and contact_person_user_id
        and call_obj.initiator_id == contact_person_user_id
    ):
        return [ticket.specialist_id]

    if (
        contact_person_user_id
        and contact_person_user_id in current_target_ids
        and call_obj.initiator_id != contact_person_user_id
    ):
        return [contact_person_user_id]
    return _get_specialists_queue(ticket)


def _get_next_target_id(queue_ids, current_target_ids):
    if not queue_ids:
        return None
    if not current_target_ids:
        return queue_ids[0]
    current_target_ids_set = {target_id for target_id in current_target_ids}
    current_indexes = [
        queue_index for queue_index, queue_target_id in enumerate(queue_ids)
        if queue_target_id in current_target_ids_set
    ]
    if not current_indexes:
        return queue_ids[0]
    next_index = max(current_indexes) + 1
    if next_index >= len(queue_ids):
        return None
    return queue_ids[next_index]


def schedule_ring_timeout_for_call(call_obj: models.CallModel, allow_queue_advance: bool = True):
    if call_obj.status_id not in ('connecting', 'ringing'):
        return
    current_target_ids = get_current_target_ids(call_obj)
    if not current_target_ids:
        return

    ring_timeout_seconds = RING_TIMEOUT_SECONDS
    if not allow_queue_advance:
        ring_timeout_seconds = RING_TIMEOUT_SECONDS_SINGLE_TARGET
    # "Только если с самого начала только один target":
    # первый scheduled timeout приходится на ring_attempt == 1.
    elif call_obj.ring_attempt == 1:
        queue_ids = _get_call_queue_ids(call_obj)
        if len(queue_ids) == 1:
            ring_timeout_seconds = RING_TIMEOUT_SECONDS_SINGLE_TARGET
    schedule(
        'bpms.meetings.utils_call.handle_call_ring_timeout',
        str(call_obj.pk),
        call_obj.ring_attempt,
        [str(target_id) for target_id in current_target_ids],
        allow_queue_advance,
        schedule_type=Schedule.ONCE,
        repeats=1,
        next_run=timezone.now() + timedelta(seconds=ring_timeout_seconds),
    )


def advance_call_queue(
    call_obj: models.CallModel,
    old_status: str,
    final_status_if_empty: str,
    from_profile_id,
    queue_ids=None,
):
    call_queue_ids = queue_ids if queue_ids is not None else _get_call_queue_ids(call_obj)
    current_target_ids = get_current_target_ids(call_obj)
    next_target_id = _get_next_target_id(call_queue_ids, current_target_ids)
    action_dt = timezone.now()
    if next_target_id:
        call_obj.status_id = 'ringing'
        call_obj.ring_attempt = (call_obj.ring_attempt or 0) + 1
        call_obj.ring_started_at = action_dt
        call_obj.save(update_fields=('status', 'ring_attempt', 'ring_started_at'))
        set_current_targets(call_obj, [next_target_id])
        recipients = get_call_notification_recipients(call_obj)
        if from_profile_id:
            recipients.add(from_profile_id)
        return True, recipients

    recipients = get_call_notification_recipients(call_obj)
    if from_profile_id:
        recipients.add(from_profile_id)
    call_obj.status_id = final_status_if_empty
    call_obj.ended_at = action_dt
    call_obj.save(update_fields=('status', 'ended_at'))
    set_current_targets(call_obj, [])
    return False, recipients


def handle_call_ring_timeout(
    call_id: str,
    expected_attempt: int,
    expected_target_ids,
    allow_queue_advance: bool,
):
    with transaction.atomic():
        call_obj = models.CallModel.objects.select_for_update(of=('self',)).select_related(
            'ticket',
            'chat',
        ).filter(
            pk=call_id,
            is_active=True,
        ).first()
        if not call_obj:
            return
        if call_obj.status_id not in ('connecting', 'ringing'):
            return
        if call_obj.accepted_by_id:
            return
        if call_obj.ring_attempt != expected_attempt:
            return
        current_target_ids = [str(target_id) for target_id in get_current_target_ids(call_obj)]
        normalized_expected_target_ids = expected_target_ids or []
        if isinstance(normalized_expected_target_ids, str):
            normalized_expected_target_ids = [normalized_expected_target_ids]
        expected_ids_normalized = sorted([str(target_id) for target_id in normalized_expected_target_ids])
        if sorted(current_target_ids) != expected_ids_normalized:
            return

        old_status = call_obj.status_id
        from_profile_id = None
        if current_target_ids:
            from_profile_id = current_target_ids[0]
        if allow_queue_advance:
            queue_ids = _get_call_queue_ids(call_obj)
            has_next_target, recipients = advance_call_queue(
                call_obj=call_obj,
                old_status=old_status,
                final_status_if_empty='missed',
                from_profile_id=from_profile_id,
                queue_ids=queue_ids,
            )
        else:
            recipients = get_call_notification_recipients(call_obj)
            if from_profile_id:
                recipients.add(from_profile_id)
            call_obj.status_id = 'missed'
            call_obj.ended_at = timezone.now()
            call_obj.save(update_fields=('status', 'ended_at'))
            set_current_targets(call_obj, [])
            has_next_target = False

    from . import notifications as meetings_notifications

    transaction.on_commit(
        lambda: send_socketio_about_call_updated(
            call_obj,
            old_status=old_status,
            recipients=recipients,
        )
    )
    transaction.on_commit(
        lambda: async_task(
            meetings_notifications.notify_about_call_updated_notification,
            call_obj,
            call_obj.initiator,
            recipients=list(recipients),
        )
    )
    transaction.on_commit(
        lambda: async_task(
            meetings_notifications.notify_about_call_updated_push,
            call_obj,
            call_obj.initiator,
            old_status=old_status,
            recipients=list(recipients),
        )
    )

    if has_next_target:
        transaction.on_commit(lambda: schedule_ring_timeout_for_call(call_obj))
    else:
        ticket = call_obj.ticket
        if ticket is not None:
            transaction.on_commit(lambda: help_desk_utils.send_socketio_about_update_ticket(ticket))


def _build_call_event_payload(call_obj: models.CallModel, old_status=None):
    serialized_call = meetings_serializers.CallNotifySerializer(instance=call_obj).data
    payload = {
        "event_type": "call_updated",
        "call": serialized_call,
        "old_status": old_status,
        "new_status": str(call_obj.status_id),
    }
    return payload


def send_socketio_about_call_created(call_obj: models.CallModel, recipients):
    payload = _build_call_event_payload(call_obj)
    payload["event_type"] = "call_created"
    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": payload,
                "recipients": list(recipients),
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_call_updated(call_obj: models.CallModel, old_status=None, recipients=None):
    target_recipients = recipients
    if target_recipients is None:
        target_recipients = get_call_notification_recipients(call_obj)
    payload = _build_call_event_payload(call_obj, old_status=old_status)
    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": payload,
                "recipients": list(target_recipients),
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_call_receiver_presence(call_obj: models.CallModel, recipients, receiver_id):
    payload = _build_call_event_payload(call_obj)
    payload["event_type"] = "call_receiver_presence"
    payload["receiver_id"] = str(receiver_id)
    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": payload,
                "recipients": list(recipients),
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_call_receiver_joined_bbb(call_obj: models.CallModel, recipients, receiver_id):
    payload = _build_call_event_payload(call_obj)
    payload["event_type"] = "call_receiver_joined_bbb"
    payload["receiver_id"] = str(receiver_id)
    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": payload,
                "recipients": list(recipients),
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def start_call_from_personal_chat(profile_id, chat_uid):
    """Старт звонка из личного чата (ровно 2 участника)."""
    with transaction.atomic():
        # 1) Personal chat validation
        chat = ChatModel.objects.filter(
            is_active=True,
            chat_uid=chat_uid,
        ).first()
        if not chat:
            raise drf_exceptions.ValidationError('Чат не найден')
        member_ids = list(chat.members.filter(is_active=True).values_list('user_id', flat=True).distinct())
        if len(member_ids) != 2:
            raise drf_exceptions.ValidationError('Звонок доступен только для личных чатов')
        if profile_id not in member_ids:
            raise drf_exceptions.PermissionDenied('Вы не участник этого чата')
        second_user_ids = [member_id for member_id in member_ids if member_id != profile_id]
        if len(second_user_ids) != 1:
            raise drf_exceptions.ValidationError('Некорректный состав участников чата')
        second_user_id = second_user_ids[0]

        # 2) Roles by organizations
        # Для клиентов используем секцию `request`, для менеджеров/поддержки - `help_desk`
        initiator_client_orgs = contractors_where_user_has_app_section_role_permission(profile_id, 'request')
        initiator_support_orgs = contractors_where_user_has_app_section_role_permission(profile_id, 'help_desk')
        second_client_orgs = contractors_where_user_has_app_section_role_permission(second_user_id, 'request')
        second_support_orgs = contractors_where_user_has_app_section_role_permission(second_user_id, 'help_desk')

        is_initiator_client = bool(initiator_client_orgs)
        is_initiator_support = bool(initiator_support_orgs)
        is_second_client = bool(second_client_orgs)
        is_second_support = bool(second_support_orgs)

        if is_initiator_client and is_second_support:
            client_user_id = profile_id
            support_user_id = second_user_id
            client_org_admin_ids = second_support_orgs
            is_client_initiator = True
            has_client_support_classification = True
        elif is_initiator_support and is_second_client:
            client_user_id = second_user_id
            support_user_id = profile_id
            client_org_admin_ids = initiator_support_orgs
            is_client_initiator = False
            has_client_support_classification = True
        else:
            # Звонок между любыми участниками личного чата.
            # Механику создания/разрешения обращений оставляем только когда из ролей можно
            # однозначно определить пару клиент-менеджер.
            has_client_support_classification = False
            client_user_id = None
            support_user_id = None
            client_org_admin_ids = None
            is_client_initiator = None

        ticket = None
        customer_card = None
        contact_person = None

        # 3) Contract relation via customer cards and actual specialists
        if has_client_support_classification:
            contact_persons_qs = help_desk_models.ContactPersonModel.objects.filter(
                is_active=True,
                user_id=client_user_id,
                customer_card__is_active=True,
                customer_card__org_admin__is_active=True,
                customer_card__org_admin_id__in=client_org_admin_ids,
            ).select_related('customer_card').order_by('-created_at')
            customer_cards = []
            seen_customer_card_ids = set()
            for contact_person in contact_persons_qs:
                customer_card_candidate = contact_person.customer_card
                if customer_card_candidate.pk in seen_customer_card_ids:
                    continue
                if customer_card_candidate.actual_specialists.filter(user_id=support_user_id).exists():
                    customer_cards.append(customer_card_candidate)
                    seen_customer_card_ids.add(customer_card_candidate.pk)

            # Если связь клиент-менеджер не находится или неоднозначна, просто звоним без ticket.
            if len(customer_cards) == 1:
                customer_card = customer_cards[0]
                contact_person = contact_persons_qs.filter(customer_card=customer_card).first()

        # 4) Existing active call in chat
        existing_call = models.CallModel.objects.select_for_update().filter(
            is_active=True,
            chat=chat,
            status_id__in=models.CallModel.ACTIVE_STATUSES,
        ).order_by('-created_at').first()

        if existing_call:
            ticket = existing_call.ticket
            call_obj = existing_call
            is_created = False
        else:
            # 5) Ticket resolve: open existing or create for client->support
            if customer_card is not None and contact_person is not None and support_user_id is not None:
                completed_statuses = help_desk_utils.get_completed_statuses_id()
                ticket = help_desk_models.HelpDeskTicketModel.objects.filter(
                    is_active=True,
                    customer_card=customer_card,
                    contact_person=contact_person,
                    channel_id='call',
                    specialist_id=support_user_id,
                ).exclude(
                    status_id__in=completed_statuses,
                ).order_by('-created_at').first()

                if ticket is None and is_client_initiator:
                    client_profile = ProfileModel.objects.get(pk=client_user_id)
                    ticket_name = f'Обращение по звонку от {client_profile.full_name}'
                    ticket_data = {
                        'name': ticket_name,
                        'description': 'Обращение создано автоматически по звонку от клиента',
                        'priority': '2',
                        'category': None,
                        'specialist': support_user_id,
                        'contact_person': str(contact_person.pk),
                        'customer_card': str(customer_card.pk),
                        'dead_line': None,
                        'created_from_messages': False,
                        'channel': 'call',
                        'receipt_date': timezone.now().isoformat(),
                    }
                    ticket_serializer = help_desk_serializers.HelpDeskTicketCreateSerializer(
                        data=ticket_data,
                        context={},
                    )
                    ticket_serializer.is_valid(raise_exception=True)
                    ticket = ticket_serializer.save()

            # В личном чате дозваниваемся ровно второму участнику.
            first_target_id = second_user_id
            action_dt = timezone.now()
            call_obj = models.CallModel.objects.create(
                ticket=ticket,
                chat=chat,
                status_id='ringing',
                initiator_id=profile_id,
                ring_attempt=1,
                ring_started_at=action_dt,
                started_at=action_dt,
            )
            set_current_targets(call_obj, [first_target_id])

            initiator_name = ProfileModel.objects.get(pk=profile_id).full_name
            target_name = ProfileModel.objects.get(pk=first_target_id).full_name
            meeting_name = f'Звонок {initiator_name} -> {target_name}'
            if ticket is not None:
                meeting_name = f'Звонок по обращению #{ticket.number}'
            meeting = models.PlannedMeetingModel.objects.create(
                name=meeting_name,
                date_begin=timezone.now(),
                duration=30,
            )

            chat_members = chat.members.filter(is_active=True).select_related('user')
            for member in chat_members:
                models.MeetingMemberModel.objects.get_or_create(
                    meeting=meeting,
                    user=member.user,
                    defaults={'is_moderator': True},
                )
            call_obj.meeting = meeting
            call_obj.save(update_fields=('meeting',))
            is_created = True

    return ticket, call_obj, is_created


def start_call_from_ticket(profile_id, ticket_id):
    """Старт звонка из существующего обращения (HelpDeskTicketModel)."""
    ticket = help_desk_models.HelpDeskTicketModel.objects.select_related(
        'contact_person',
        'specialist',
        'customer_card',
    ).filter(is_active=True, pk=ticket_id).first()
    if not ticket:
        raise drf_exceptions.ValidationError('Обращение не найдено')

    with transaction.atomic():
        existing_call = models.CallModel.objects.select_for_update().filter(
            is_active=True,
            ticket=ticket,
            status_id__in=models.CallModel.ACTIVE_STATUSES,
        ).order_by('-created_at').first()
        if existing_call:
            call_obj = existing_call
            is_created = False
            ticket = existing_call.ticket
        else:
            caller_profile_id = profile_id

            contact_person_user_id = _get_contact_person_user_id(ticket)

            specialist_user_id = ticket.specialist_id

            is_ticket_member = ticket.members.filter(pk=caller_profile_id)

            # 1) Если звонящий - ответственный по обращению или участник обращения => звоним контактному лицу
            if (specialist_user_id and caller_profile_id == specialist_user_id) or is_ticket_member:
                if not contact_person_user_id:
                    raise drf_exceptions.ValidationError('У обращения отсутствует контактное лицо')
                target_ids = [contact_person_user_id]
            # 2) Если звонящий - контактное лицо => звоним ответственному (если он есть) или в очередь
            elif contact_person_user_id and caller_profile_id == contact_person_user_id:
                if specialist_user_id:
                    target_ids = [specialist_user_id]
                else:
                    target_ids = _get_specialists_queue(ticket)
            else:
                # Поддержка может инициировать звонок тоже:
                # если пользователь входит в список actual_specialists, направляем звонок клиенту.
                if _is_current_customer_specialist(ticket, caller_profile_id):
                    if not contact_person_user_id:
                        raise drf_exceptions.ValidationError('У обращения отсутствует контактное лицо')
                    target_ids = [contact_person_user_id]
                else:
                    raise drf_exceptions.PermissionDenied('Звонок доступен только для участников обращения')

            if not target_ids:
                raise drf_exceptions.ValidationError('Специалисты сейчас недоступны')

            first_target_id = target_ids[0]
            current_target_ids = [first_target_id]
            if (
                contact_person_user_id
                and caller_profile_id == contact_person_user_id
                and not specialist_user_id
            ):
                current_target_ids = _get_same_priority_target_ids(ticket, target_ids)
            action_dt = timezone.now()
            call_obj = models.CallModel.objects.create(
                ticket=ticket,
                chat=None,
                status_id='ringing',
                initiator_id=profile_id,
                ring_attempt=1,
                ring_started_at=action_dt,
                started_at=action_dt,
            )
            set_current_targets(call_obj, current_target_ids)

            meeting_name = f'Звонок по обращению #{ticket.number}'
            meeting = models.PlannedMeetingModel.objects.create(
                name=meeting_name,
                date_begin=timezone.now(),
                duration=30,
            )
            models.MeetingMemberModel.objects.get_or_create(
                meeting=meeting,
                user_id=profile_id,
                defaults={'is_moderator': True},
            )
            call_obj.meeting = meeting
            call_obj.save(update_fields=('meeting',))
            is_created = True

    return ticket, call_obj, is_created


def start_call_to_org_support(profile_id, org_admin_id):
    """Старт звонка в организацию техподдержки от имени клиента."""
    contact_person = help_desk_models.ContactPersonModel.objects.filter(
        is_active=True,
        user_id=profile_id,
        customer_card__is_active=True,
        customer_card__org_admin__is_active=True,
        customer_card__org_admin_id=org_admin_id,
    ).select_related(
        'customer_card',
    ).order_by('-created_at').first()
    if not contact_person:
        raise drf_exceptions.ValidationError('Организация техподдержки не найдена')

    customer_card = contact_person.customer_card
    completed_statuses = help_desk_utils.get_completed_statuses_id()

    ticket = help_desk_models.HelpDeskTicketModel.objects.filter(
        is_active=True,
        customer_card=customer_card,
        contact_person=contact_person,
        channel_id='call',
        specialist__isnull=True,
    ).exclude(
        status_id__in=completed_statuses,
    ).order_by('-created_at').first()

    if ticket is None:
        profile = ProfileModel.objects.get(pk=profile_id)
        ticket_name = f'Обращение по звонку от {profile.full_name}'
        ticket_data = {
            'name': ticket_name,
            'description': 'Обращение создано автоматически по звонку от клиента',
            'priority': '2',
            'category': None,
            'specialist': None,
            'contact_person': str(contact_person.pk),
            'customer_card': str(customer_card.pk),
            'dead_line': None,
            'created_from_messages': False,
            'channel': 'call',
            'receipt_date': timezone.now().isoformat(),
        }
        ticket_serializer = help_desk_serializers.HelpDeskTicketCreateSerializer(
            data=ticket_data,
            context={},
        )
        ticket_serializer.is_valid(raise_exception=True)
        ticket = ticket_serializer.save()

    return start_call_from_ticket(profile_id=profile_id, ticket_id=ticket.pk)


def create_callback_call_to_org_support(profile_id, org_admin_id, description):
    """Создает тикет и звонок со статусом waiting_callback для запроса обратного звонка."""
    profile = ProfileModel.objects.get(pk=profile_id)
    ticket_name = f'Запрос на обратный звонок от {profile.full_name}'
    with transaction.atomic():
        ticket_data = {
            'user': str(profile_id),
            'name': ticket_name,
            'description': description,
            'org_admin': str(org_admin_id),
            'channel': 'call',
        }
        ticket_serializer = help_desk_serializers.TicketForClientCreateSerializer(
            data=ticket_data,
            context={},
        )
        ticket_serializer.is_valid(raise_exception=True)
        ticket = ticket_serializer.save()

        call_obj = models.CallModel.objects.create(
            ticket=ticket,
            chat=None,
            meeting=None,
            status_id='waiting_callback',
            initiator_id=profile_id,
            ring_attempt=0,
            ring_started_at=None,
            started_at=timezone.now(),
        )
    return ticket, call_obj
