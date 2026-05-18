import json
from urllib.parse import quote
from datetime import datetime, timedelta
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task
from django.core.serializers.json import DjangoJSONEncoder

from haystack.query import RelatedSearchQuerySet
from haystack.inputs import Raw

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import DateTimeField

from bkz3.settings import BACKEND_URL, DOWNLOADER_PATH, SOCKETIO_SYSTEM_CHANNEL
from users.models import ProfileModel
from common.redis import socketio_redis
from common.utils import profile_is_online, get_search_bool
from common.serializers import AppFileSerializer

from telegram_bot.base import base_bot
from bpms.chat_ai.utils.messages import invoke_role_prompt

from . import models
from . import serializers
from . import utils_ai
from . import notifications
from . import search_indexes


class ChatHandler:
    mapping = {
        'message': 'create_message',
        'create_chat': 'create_chat',
        'chat_pin_message': 'pin_message',
        'chat_unpin_message': 'unpin_message',
        'chat_unpin_all_message': 'unpin_all_messages',
        'chat_rename': 'rename_chat',
        'chat_change_rights': 'change_chat_rights',
        'chat_add_user': 'add_chat_member',
        'chat_delete': 'delete_chat',
        'chat_delete_user': 'delete_chat_member',
        'chat_member_update_last_message': 'update_last_message_member',
        'chat_delete_message': 'delete_message',
        'message_update': 'update_message',
        'chat_delete_message_from_cache': 'delete_message_from_cache',
    }

    def select_handler(self, name: str, data: dict):
        handler = getattr(self, self.mapping.get(name, 'none'), None)
        print(handler)
        if callable(handler):
            return handler(data)

    def create_message(self, data: dict):
        """Создание сообщения"""
        if data.get('attachments') is None or data.get('attachments') == [None]:
            data['attachments'] = []
        s_data = serializers.MessageCreateSerializer(data=data)
        try:
            s_data.is_valid(raise_exception=True)
        except Exception as ex:
            socketio_redis.hdel(f'messages:{data.get("chat")}', data.get('message_uid'))
            print(ex)
            return
        try:
            s_data.save()
        except Exception as ex:
            socketio_redis.hdel(f'messages:{data.get("chat")}', data.get('message_uid'))
            print(ex)
            return
        socketio_redis.hdel(f'messages:{data.get("chat")}', data.get('message_uid'))

        print(s_data.data)

    def update_message(self, data: dict):
        """Изменение сообщения"""
        if data.get('attachments') is None or data.get('attachments') == [None]:
            data['attachments'] = []
        message_uid = data.get('message_uid')
        if not message_uid:
            print('message_uid required')
        try:
            message = models.MessageModel.objects.get(message_uid=message_uid)
        except (ValidationError, ObjectDoesNotExist):
            print('message_uid not found')
            socketio_redis.hdel(f'updated_messages:{data.get("chat")}', message_uid)
            return
        serializer = serializers.MessageUpdateSerializer(message, data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as ex:
            socketio_redis.hdel(f'updated_messages:{data.get("chat")}', message_uid)
            print(ex)
            return
        try:
            serializer.save()
        except Exception as ex:
            socketio_redis.hdel(f'updated_messages:{data.get("chat")}', message_uid)
            print(ex)
            return
        socketio_redis.hdel(f'updated_messages:{data.get("chat")}', message_uid)
        print(serializer.data)

    def delete_message(self, data: dict):
        """Удаление сообщения"""
        message_uid = data.get('message_uid')
        chat_uid = data.get('chat_uid')
        if message_uid and chat_uid:
            try:
                message = models.MessageModel.objects.get(message_uid=message_uid, chat=chat_uid)
            except models.MessageModel.DoesNotExist:
                print('Message not found')
                return
            message.text = ''
            message.is_deleted = True
            message.share = None
            message.save()
            chat = message.chat
            last_message = chat.messages.filter(is_active=True, is_deleted=False).order_by('-created_at').first()
            if last_message:
                last_sent = last_message.created_at
            else:
                last_sent = None
            chat.last_sent = last_sent
            chat.save(update_fields=('last_sent',),)
            print('message deleted')
        else:
            print('invalid message_uid or chat_uid')
            return

    def delete_message_from_cache(self, data: dict):
        """Удаление сообщения из кэша."""
        socketio_redis.hdel(f'messages:{data.get("chat_uid")}', data.get('message_uid'))
        print('deleted.')

    def pin_message(self, data: dict):
        """Закрепление сообщения в чате"""
        try:
            message = models.MessageModel.objects.get(message_uid=data.get('message_uid'))
        except models.MessageModel.DoesNotExist:
            print('message does not exist')
            return
        chat = message.chat
        try:
            user = ProfileModel.objects.get(pk=data.get('user'))
        except ProfileModel.DoesNotExist:
            print('user does not exist')
            return
        if chat.is_public is True:
            moderators = models.MemberModel.objects.filter(chat=chat, is_moderator=True).values_list('user', flat=True)
            if user.pk in moderators or user == chat.chat_author:
                message.is_pinned = True
                message.pin_author = user
                message.pin_date = data.get('pin_date')
                message.save()
            else:
                print('permission denied for this user')
        else:
            if chat.members.filter(user=user).exists():
                message.is_pinned = True
                message.pin_author = user
                message.pin_date = data.get('pin_date')
                message.save()
            else:
                print('permission denied for this user')

    def unpin_message(self, data: dict):
        """Снимает закрепление сообщения"""
        message_uid = data.get('message_uid')
        try:
            message = models.MessageModel.objects.get(message_uid=message_uid)
        except models.MessageModel.DoesNotExist:
            print('message not found')
            return
        message.is_pinned = False
        message.pin_author = None
        message.pin_date = None
        message.save()

    def unpin_all_messages(self, data: dict):
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except models.ChatModel.DoesNotExist:
            print('chat not found')
            return
        chat.messages.filter(is_pinned=True).update(is_pinned=False, pin_author=None, pin_date=None)

    def update_last_message_member(self, data: dict):
        chat_uid = data.get('chat')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except models.ChatModel.DoesNotExist:
            print('chat not found')
            return
        user_id = data.get('user') or data.get('user_id')
        try:
            member = chat.members.get(user_id=user_id)
        except ObjectDoesNotExist:
            print('chat member not found')
            return
        new_last_message_created = datetime.fromisoformat(data.get('created').replace('Z', '+00:00'))
        if not member.last_message_created or (member.last_message_created < new_last_message_created):
            member.last_message_created = new_last_message_created
            member.save(update_fields=('last_message_created',))
            socketio_redis.hset(
                f"member_last_message_date_{user_id}",
                str(chat_uid),
                new_last_message_created.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            )
            print('last message updated')
        else:
            print("new_last_message < old_last_message")

        # Для других сессий того же пользователя нужно рассылать
        # не просто новый last_message_created, а точный остаток unread.
        if 'unread_count' in data or 'unread_mention_count' in data:
            publish_chat_member_read_progress(
                chat_uid=chat_uid,
                user_id=user_id,
                created=new_last_message_created,
                unread_count=data.get('unread_count', 0),
                unread_mention_count=data.get('unread_mention_count', 0),
            )

    def create_chat(self, data: dict):
        """Создание чата."""
        if data.get('name') is None:
            data['name'] = 'some chat'
        s_data = serializers.ChatCreateSerializer(data=data)
        try:
            s_data.is_valid(raise_exception=True)
            print('is valid.')
            s_data.save()
            print('saved.')
        except Exception as ex:
            print(str(ex))
            return
        print(s_data.data)

    def delete_chat(self, data: dict):
        """Удаление чата."""
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except models.ChatModel.DoesNotExist:
            print('chat not found')
            return
        chat.is_active = False
        chat.save(update_fields=('is_active',))
        print(f'chat {chat_uid} deleted.')

    def rename_chat(self, data: dict):
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except models.ChatModel.DoesNotExist:
            print('chat not found')
            return
        chat_name = data.get('chat_name')
        if isinstance(chat_name, str):
            chat.name = chat_name[:255]
            chat.save()
        else:
            print('invalid chat_name')
            return

    def update_chat_metadata(self, data: dict):
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except models.ChatModel.DoesNotExist:
            print('chat not found')
            return
        metadata = data.get('metadata')
        chat.metadata = metadata
        chat.save()

    def change_chat_rights(self, data: dict):
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except models.ChatModel.DoesNotExist:
            print('chat not found')
            return
        members = data.get('members')
        if isinstance(members, list):
            for member_dict in members:
                try:
                    member = chat.members.get(user_id=member_dict.get('user'))
                except ObjectDoesNotExist:
                    continue
                is_moderator = member_dict.get('is_moderator')
                if isinstance(is_moderator, bool):
                    member.is_moderator = is_moderator
                    member.save()
        else:
            print('invalid members list')
            return

    def add_chat_member(self, data: dict):
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except ObjectDoesNotExist:
            print('chat not found')
            return
        members = data.get('members')
        if isinstance(members, list):
            for member_dict in members:
                if isinstance(member_dict, dict):
                    try:
                        member, created = models.MemberModel.objects.get_or_create(
                            chat=chat, user_id=member_dict.get('user')
                        )
                    except IntegrityError:
                        print('invalid member')
                        continue
                    member.is_active = True
                    member.is_moderator = member_dict.get('is_moderator', False)
                    if created:
                        member.save()
                    else:
                        member.last_message_created = timezone.now()
                        member.save(update_fields=('is_active', 'is_moderator', 'last_message_created'))
                else:
                    print('member is not dict.')
        else:
            print('invalid member list')
            return

    def delete_chat_member(self, data: dict):
        chat_uid = data.get('chat_uid')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except ObjectDoesNotExist:
            print('chat not found')
            return
        members_dict = data.get('members')
        if isinstance(members_dict, list):
            member_uids = [member_dict.get('user') for member_dict in members_dict]
            members = chat.members.filter(user_id__in=member_uids)
            for member in members:
                member.is_active = False
                member.save(update_fields=('is_active',))
        else:
            print('members is not list')
            return


def update_chat_index(chat):
    search_indexes.ChatIndex().update_object(chat)
    return 'chat index updated.'


def send_message_to_tg(chat_message_id) -> None:
    """
    Отправка уведомление о новом сообщении в чате всем у кого подвязан телеграм и кто не в сети
    """
    chat_message = models.MessageModel.objects.get(pk=chat_message_id)
    chat = chat_message.chat
    members = chat.members.select_related('user').filter(is_active=True,
                                                         user__telegram_id__isnull=False).exclude(
        user=chat_message.message_author)
    if chat_message.is_system:
        sender_fio = 'Системное сообщение'
    else:
        sender_fio = chat_message.message_author.user.get_full_name()
    chat_name = ''
    if chat.is_public:
        chat_name = F'В чате {chat.name}\n'

    message_text = F'У вас новое сообщение!\n' + \
                   chat_name + \
                   F'Отправитель: {sender_fio}\n' \
                   F'{chat_message.clear_text}'
    for member in members:
        if not profile_is_online(member.user.id):
            base_bot.send_message(chat_id=member.user.telegram_id,
                                  text=message_text)

def recover_chat_rooms():
    # Создаем комнаты для каждого пользователя:
    users = ProfileModel.objects.select_related('user').filter(is_active=True)
    print("\nCreate rooms for users...")
    for user in users:
        chats = set(str(chat_id) for chat_id in user.membermodel_set.filter(
            is_active=True,
            chat__is_active=True
        ).values_list('chat_id', flat=True))
        socketio_redis.delete(f"user:rooms:{user.user_id}")
        if chats:
            socketio_redis.lpush(f"user:rooms:{user.user_id}", *chats)
            print(f"Created rooms for user {user.user.username} chats: {chats}")
    public_chats = models.ChatModel.objects.filter(is_active=True, is_public=True)
    # добавляем хэшмапы для публичных чатов:
    print("\nCreate hashmaps for public chats...")
    for public_chat in public_chats:
        data = {
            'name': public_chat.name,
            'admin': str(public_chat.chat_author_id),
        }
        members = {
            str(member.user_id): str(member.is_moderator).lower() for member in
            public_chat.members.filter(is_active=True)
        }
        data.update(members)
        socketio_redis.delete(f"room:{public_chat.chat_uid}")
        socketio_redis.hset(f"room:{public_chat.chat_uid}", mapping=data)
        print(f"Created hashmap for chat {public_chat.name} {public_chat.chat_uid}")


def get_chat_search_queryset(user, text):
    search_bool = get_search_bool()
    my_users = models.MemberModel.objects.filter(
        Q(chat__member__user_id=user.pk, chat__member__is_active=True),
        chat__is_public=False,
    ).exclude(
        user_id=user.pk
    ).values_list('user_id', flat=True)
    search_queryset = RelatedSearchQuerySet().filter_or(
        content=text,
        chat_members__in=[str(user.pk)],
        chat_is_active=search_bool,
    ).filter_or(
        content=text,
        profile_id=Raw("[* TO *]")
    ).exclude(
        profile_id=str(user.pk)
    ).exclude(
        profile_id__in=my_users
    ).models(models.ChatModel, ProfileModel).load_all()
    return search_queryset


def get_support_chat(profile):
    """
    Возвращает UID активного чата поддержки для указанного профиля.
    Создает чат, если он не найден.
    """
    if profile.is_support:
        return None

    chat = models.ChatModel.objects.filter(
        is_active=True,
        chat_author=profile,
        is_support=True,
        ).order_by('-last_sent').first()

    # Создаем чат с техподдержкой, если его еще нет
    if not chat:
        chat = models.ChatModel.objects.create(
            is_public=True,
            chat_author=profile,
            name=f'{_("Техподдержка")} {profile.full_name}',
            last_sent=datetime(2000, 1, 1, tzinfo=timezone.get_current_timezone()),
            is_support=True,
        )
        
        # Список для хранения всех участников чата
        chat_members = []
        
        # Добавляем туда весь персонал техподдержки как модераторов.
        support_staff = ProfileModel.objects.filter(
            is_active=True, temporary_blocked=False, is_support=True
            )
        for each in support_staff:
            member = models.MemberModel()
            member.chat = chat
            member.user_id = each.pk
            member.is_moderator = True
            try:
                member.save()
                chat_members.append(member)
            except IntegrityError:
                pass

        # Добавляем самого пользователя, закрепляем ему чат.
        member = models.MemberModel()
        member.chat = chat
        member.user_id = profile.pk
        member.is_pinned = True
        try:
            member.save()
            chat_members.append(member)
        except IntegrityError:
            pass

        data = json.dumps(
            {"event": "chat_create_chat",
                "data": {
                    "chat_uid": str(chat.chat_uid),
                    "is_public": True,
                    "members": [{"user": str(each.user.id), "is_moderator": str(each.is_moderator)} for each in
                                chat_members],
                    "name": chat.name,
                    "chat_author": str(chat.chat_author.pk),
                    "last_sent": DateTimeField().to_representation(chat.last_sent),
                    "new_message_count": 0,
                    "member_count": len(chat_members),
                    "is_active": True,
                }
                }
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


    return chat.chat_uid


def send_message_to_help_desk(message_id):
    message = models.MessageModel.objects.get(pk=message_id)
    chat = message.chat
    chat_members_id = list(chat.members.all().values_list('user', flat=True))
    from help_desk.models import HelpDeskTicketModel, ContactPersonMessageModel, ContactPersonModel
    from help_desk.utils import get_completed_statuses_id
    ticket = HelpDeskTicketModel.objects.filter(
        Q(specialist_id=chat_members_id[0], contact_person__user_id=chat_members_id[1]) |
        Q(specialist_id=chat_members_id[1], contact_person__user_id=chat_members_id[0]),
        channel_id='internal_chat',
        is_active=True
    ).exclude(status_id__in=get_completed_statuses_id()).order_by('-created_at',).first()
    if not ticket:
        return f'ticket not found members {chat_members_id}'

    contact_person = ticket.contact_person
    customer_card = contact_person.customer_card
    if contact_person.is_active and customer_card.is_active:
        cp_message = ContactPersonMessageModel()
        cp_message.channel_id = 'internal_chat'
        cp_message.contact_person = contact_person
        cp_message.text = message.text
        cp_message.source_message = dict()
        cp_message.message_date = message.created
        cp_message.message_id = message.message_uid
        if not contact_person.user == message.message_author:
            cp_message.is_help_desk = True
            cp_message.author = message.message_author
        message_reply = message.message_reply
        if message_reply:
            message_reply_uid = message_reply.message_uid
            cp_message_reply = ContactPersonMessageModel.objects.filter(
                channel_id='internal_chat',
                message_id=message_reply_uid,
                contact_person=contact_person,
            ).order_by('-created_at').first()
            cp_message.reply = cp_message_reply
        with transaction.atomic():
            cp_message.save(ticket=ticket)
            attachments = list(message.attachments.all())
            cp_message.attachments.set(attachments)


def get_last_message_data(chat: models.ChatModel):
    sorted_messages_list = get_cached_messages_list(chat)
    if sorted_messages_list:
        return sorted_messages_list[0]
    else:
        return None


def get_cached_messages_list(chat):
    if isinstance(chat, dict):
        chat_uid = chat['chat_uid']
    else:
        chat_uid = chat.chat_uid
    cached_messages = socketio_redis.hgetall(f'messages:{chat_uid}')
    if cached_messages:
        cached_messages_list = list()
        for key, message_str in cached_messages.items():
            cached_messages_list.append(json.loads(message_str))
        sorted_messages_list = sorted(cached_messages_list, key=lambda x: x['created'], reverse=True)
        return sorted_messages_list
    else:
        return None


def get_last_message_count(chat, user: ProfileModel):
    if not user:
        return 0, 0
    user_id = user.pk
    if isinstance(chat, dict):
        new_message_count = chat.get('new_message_count', 0)
        new_mention_count = chat.get('new_mention_count', 0)
        last_message_created = chat.get('last_message_created', None)
        chat_uid = chat.get('chat_uid')
        has_precomputed_counts = 'new_message_count' in chat and 'new_mention_count' in chat
    else:
        new_message_count = getattr(chat, 'new_message_count', 0)
        new_mention_count = getattr(chat, 'new_mention_count', 0)
        last_message_created = getattr(chat, 'last_message_created', None)
        chat_uid = chat.chat_uid
        has_precomputed_counts = hasattr(chat, 'new_message_count') and hasattr(chat, 'new_mention_count')
    cached_last_message_created_str = socketio_redis.hget(f"member_last_message_date_{user_id}", str(chat_uid))
    if cached_last_message_created_str:
        cached_last_message_created = datetime.fromisoformat(cached_last_message_created_str.replace('Z', '+00:00'))
        if not last_message_created or cached_last_message_created > last_message_created:
            last_message_created = cached_last_message_created
            has_precomputed_counts = False
    if not has_precomputed_counts:
        base_queryset = models.MessageModel.objects.filter(
            chat_id=chat_uid,
            is_active=True,
            is_deleted=False,
        )
        mention_queryset = models.MessageModel.objects.filter(
            mentions=user,
            chat_id=chat_uid,
            is_active=True,
            is_deleted=False,
        )
        if last_message_created:
            base_queryset = base_queryset.filter(created__gt=last_message_created)
            mention_queryset = mention_queryset.filter(created__gt=last_message_created)
        new_message_count = base_queryset.count()
        new_mention_count = mention_queryset.count()
    if last_message_created:
        last_message_created_str = last_message_created.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        cached_messages_list = get_cached_messages_list(chat)
        if cached_messages_list:
            for each in cached_messages_list:
                if each.get('created', '') > last_message_created_str:
                    new_message_count += 1
                    if user_id in each.get('mentions', []):
                        new_mention_count += 1
    return new_message_count, new_mention_count


def generate_chat_summary(chat_summary_id):
    """
    Асинхронная задача для генерации саммари чата.
    Любое необработанное исключение переводит запись в status='failed'.
    """
    try:
        chat_summary = models.ChatSummaryModel.objects.get(pk=chat_summary_id)
    except models.ChatSummaryModel.DoesNotExist:
        return

    try:
        chat = chat_summary.chat
        chat_uid = chat.chat_uid

        # Calculate date range from start_date and end_date
        # For start_date, use beginning of day
        date_from = timezone.make_aware(datetime.combine(chat_summary.start_date, datetime.min.time()))
        # For end_date, include the entire day (extend to end of day)
        date_to = timezone.make_aware(datetime.combine(chat_summary.end_date, datetime.max.time()))

        # Query messages in date range
        messages_qs = (
            models.MessageModel.objects
            .filter(
                chat_id=chat_uid,
                created__gte=date_from,
                created__lte=date_to,
                is_active=True,
                is_ai_message=False,
            )
            .select_related("message_author", "share")
            .order_by("created")
        )

        # Convert to list to allow reverse iteration
        messages_list = list(messages_qs)

        # If no messages found, save completed record with info message (no LLM call)
        if not messages_list:
            date_from_formatted = chat_summary.start_date.strftime('%d.%m.%Y')
            date_to_formatted = chat_summary.end_date.strftime('%d.%m.%Y')
            chat_summary.status = 'completed'
            chat_summary.summary = (
                f'За период {date_from_formatted} — {date_to_formatted} сообщений в чате не найдено.'
            )
            chat_summary.completed_at = timezone.now()
            chat_summary.save()
            async_task(notifications.send_notify_about_summary_ready, str(chat_summary.pk))
            return

        # Build llm_result from the most recent messages, respecting 60000 char limit
        llm_result = []
        max_llm_chars = 60000
        earliest_message_date = None
        period_truncated = False
        current_size = 0

        # Iterate messages in reverse order (from newest to oldest)
        for message in reversed(messages_list):
            serialized_message = serializers.MessageListSerializer(message).data

            # If share = task, add comments + execution_times
            share = serialized_message.get("share")
            if share and isinstance(share, dict) and share.get("type") == "tasks.TaskModel":
                task_id = share.get("id")
                if task_id:
                    share["comments"] = utils_ai.get_task_comments(task_id)
                    share["execution_times"] = utils_ai.get_task_execution_times(task_id)

            compacted = utils_ai.compact_message(serialized_message)
            if not compacted:
                continue

            # Estimate size using str() - difference with JSON is less than 1%
            message_size = len(str(compacted))

            if current_size + message_size <= max_llm_chars:
                # Add message to the beginning (since we're iterating backwards)
                llm_result.insert(0, compacted)
                current_size += message_size
                earliest_message_date = message.created
            else:
                # This message would exceed the limit, stop here
                period_truncated = True
                break

        # Build user prompt with chat data and call LLM
        # Normalize and serialize the entire list once
        normalized_result = utils_ai.normalize_for_json(llm_result)
        chat_text = json.dumps(normalized_result, ensure_ascii=False, indent=2)
        user_message = chat_text
        
        summary_text = invoke_role_prompt(
            user_message=user_message,
            role_code="chat_summary",
            context={},
            consumer=chat,
            format_schema=None,
            url_query_param=f"chat_summary&chat={chat.pk}",
        )
        
        if not summary_text:
            summary_text = "Не удалось получить анализ от модели."
        
        # Format dates for header (use .date() to get date only, without time)
        date_from_formatted = chat_summary.start_date.strftime('%d.%m.%Y')
        date_to_formatted = chat_summary.end_date.strftime('%d.%m.%Y')
        
        # Check if period was truncated
        period_note = ""
        
        if period_truncated and earliest_message_date:
            # Period was automatically reduced
            earliest_date_formatted = earliest_message_date.date().strftime('%d.%m.%Y')
            period_note = f"Период автоматически сокращен до {earliest_date_formatted} - {date_to_formatted}<br><br>"
        
        # Create message text with header
        # Replace \n with <br> for proper line breaks in chat
        summary_text_html = summary_text.replace('\n', '<br>')
        message_text = f"Анализ чата за период {date_from_formatted} - {date_to_formatted}<br>{period_note}<br>{summary_text_html}"
        
        # Update ChatSummaryModel with completed status and summary
        chat_summary.status = 'completed'
        chat_summary.summary = message_text
        chat_summary.completed_at = timezone.now()
        chat_summary.save()
        
        # Send notification about summary ready
        async_task(notifications.send_notify_about_summary_ready, str(chat_summary.pk))
    except Exception as e:
        chat_summary.status = 'failed'
        chat_summary.error_message = str(e)
        chat_summary.completed_at = timezone.now()
        chat_summary.save()
        raise


def delete_chat_members(chat_uid, profiles_id: tuple):
    """
    Отправляет в системный канал команду для удаления участников чата
    chat_uid - уид чата
    profiles_id - профили пользователей участников чата, которых нужно удалить
    """
    data = json.dumps(
        {
            'event': 'chat_delete_user',
            'data': {
                "chat_uid": str(chat_uid),
                "members": [{"user": str(profile_id)} for profile_id in profiles_id]
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def add_chat_members(chat_uid, chat_members: tuple):
    data = json.dumps(
        {
            'event': 'chat_add_user',
            'data': {
                "chat_uid": str(chat_uid),
                "members": [{"user": str(each.user_id), "is_moderator": str(each.is_moderator)} for each in chat_members],
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def publish_chat_member_read_progress(chat_uid, user_id, created, unread_count, unread_mention_count):
    data = json.dumps(
        {
            'event': 'chat_member_update_last_message',
            'data': {
                'chat': str(chat_uid),
                'created': DateTimeField().to_representation(created),
                'user_id': str(user_id),
                'unread_count': int(unread_count or 0),
                'unread_mention_count': int(unread_mention_count or 0),
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
