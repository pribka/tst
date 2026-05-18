import json
from urllib.parse import quote

from django_q.tasks import async_task

from django.db.models import Q
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from drf_haystack.serializers import HaystackSerializer
# from apps.core.search_indexes import ProfileIndex

from bkz3.settings import DOWNLOADER_PATH, BACKEND_URL
from users.models import ProfileModel
from users.serializers import (
    AppUserSerializer,
    CachedAppUserSerializer,
    CachedAppUserPreviewSerializer,
    CachedUserPreviewSerializer,
)
from users.search_indexes import ProfileIndex
from common.models import File, BaseModel
from common.serializers import AppFileSerializer, CachedAppFileSerializer
from common.redis import socketio_redis

from bpms.favorites.utils import get_in_favorites
from bpms.reactions.utils import get_reactions_data

from . import search_indexes
from . import models
from . import notifications
from . import utils


def get_serialized_chat_attachments(message, filter_lookup=None):
    qs = message.attachments.filter(is_active=True)
    if filter_lookup:
        qs = qs.filter(**filter_lookup)
    s_data = CachedAppFileSerializer(qs.values_list('pk', flat=True), many=True).data
    if DOWNLOADER_PATH is not None:
        for each in s_data:
            parent_path = quote(
                f"?chat_uid={message.chat_id}&message_uid={message.message_uid}&id={each.get('id')}&target=chat_attachments"
            )
            each['path'] = f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'
    return s_data


class MemberSerializer(serializers.ModelSerializer):
    user = AppUserSerializer()

    class Meta:
        model = models.MemberModel
        fields = (
            'chat',
            'is_moderator',
            'is_active',
            'user',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_author'] = instance.chat.chat_author_id == instance.user_id
        return data


class ChatCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=3, max_length=255)

    class Meta:
        model = models.ChatModel
        fields = (
            'id',
            'name',
            'is_public',
            'chat_uid',
            'chat_author',
            'color',
            'metadata',
        )

    def create(self, validated_data):
        chat_author = validated_data.get('chat_author')
        user_dict = {'user': chat_author.pk, 'is_moderator': True}
        members = self.initial_data.get('members')
        if not isinstance(members, (list, type(None))):
            raise ValidationError('Некорректный список участников')
        is_public = validated_data.get('is_public')
        if is_public is True:
            name = validated_data.get('name')
            if not name:
                raise ValidationError('Не указано имя чата')
            chat = models.ChatModel.objects.create(
                **validated_data
            )
            if members:
                members.append(user_dict)
                self.create_member(chat, members)
            else:
                self.create_member(chat, [user_dict])
            return chat
        else:
            if not members:
                raise ValidationError('Некорректный список участников')
            try:
                ProfileModel.objects.get(is_active=True, pk=members[0].get('user'))
            except ObjectDoesNotExist:
                raise ValidationError("Пользователь не найден")
            except ValueError:
                raise ValidationError("Пользователь не найден")
            chat = models.ChatModel.objects.create(
                **validated_data
            )
            self.create_member(chat, [user_dict, members[0]])
            return chat

    @staticmethod
    def create_member(chat, members, inactive_members=tuple()):
        for each in members:
            member = models.MemberModel()
            member.chat = chat
            member.user_id = each.get('user')
            member.is_moderator = each.get('is_moderator', False)
            try:
                member.save()
            except IntegrityError:
                pass
        if inactive_members:
            for each in inactive_members:
                member = models.MemberModel()
                member.chat = chat
                member.user_id = each.get('user')
                member.is_active = False
                member.is_moderator = each.get('is_moderator', False)
                try:
                    member.save()
                except IntegrityError:
                    pass


class ChatRenameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=3, max_length=255)

    class Meta:
        model = models.ChatModel
        fields = (
            'name',
        )


class MessageReplySerializer(serializers.ModelSerializer):
    message_author = CachedAppUserSerializer(source='message_author_id')

    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_uid',
            'message_author',
            'text',
            'created_at',
            'is_system',
            'is_ai_message',
            'is_deleted',
            'chat',
        )


class MessageCreateSerializer(serializers.ModelSerializer):
    text = serializers.CharField(max_length=4096, allow_blank=True, default="")
    attachments = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=File.objects.filter(is_active=True))
    mentions = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_null=True, allow_empty=True, queryset=ProfileModel.objects.all()
    )

    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_uid',
            'text',
            'chat',
            'message_reply',
            'message_author',
            'attachments',
            'created',
            'is_system',
            'is_ai_message',
            'share',
            'forwarded',
            'message_forwarded',
            'mentions',
        )

    def to_internal_value(self, data):
        # Если пришел null в поле mentions, заменяем его на пустой список
        if 'mentions' in data and data['mentions'] is None:
            data['mentions'] = []
        return super().to_internal_value(data)

    def create(self, validated_data):
        chat = validated_data.get('chat')
        message_author = validated_data.get('message_author')
        is_system = validated_data.get('is_system', False)
        is_ai_message = validated_data.get('is_ai_message', False)
        if not is_system:
            try:
                member = models.MemberModel.objects.get(is_active=True, user=message_author, chat=chat)
            except ObjectDoesNotExist:
                raise ValidationError("Чат не найден")
        else:
            member = None
        forwarded = validated_data.get('forwarded')
        if forwarded:
            message = models.MessageModel.objects.create(
                chat=chat,
                message_uid=validated_data.get('message_uid'),
                message_author=message_author,
                text='',
                message_forwarded=validated_data.get('message_forwarded'),
                forwarded=validated_data.get('forwarded'),
                created=validated_data.get('created'),
                is_system=is_system,
                is_ai_message=is_ai_message,
            )
        else:
            message = models.MessageModel.objects.create(
                chat=chat,
                message_uid=validated_data.get('message_uid'),
                message_author=message_author,
                text=validated_data.get('text'),
                message_reply=validated_data.get('message_reply'),
                created=validated_data.get('created'),
                is_system=is_system,
                is_ai_message=is_ai_message,
                share=validated_data.get('share')
            )
            if validated_data.get('attachments'):
                message.attachments.set(validated_data.get('attachments')[:5])
            if validated_data.get('mentions'):
                message.mentions.set(validated_data.get('mentions'))
                transaction.on_commit(lambda: async_task(notifications.send_notify_about_mentions, str(message.pk)))
        if chat.is_public is False:
            chat.members.filter(is_active=False).update(is_active=True)
        # member.last_message = message.pk
        # member.save(update_fields=('last_message',))
        chat.last_sent = message.created
        chat.save(update_fields=('last_sent',))
        if member:
            member.last_message_created = message.created
            member.save(update_fields=('last_message_created',))
        # if not chat.is_public:
        #     from .utils import send_message_to_help_desk
        #     transaction.on_commit(lambda: async_task(send_message_to_help_desk, str(message.pk)))
        return message

    def validate_message_reply(self, data):
        if data and str(data.chat_id) != self.initial_data.get('chat', ''):
            raise ValidationError('Отвечаемое сообщение не существует')
        return data


class MessageUpdateSerializer(serializers.ModelSerializer):
    text = serializers.CharField(max_length=4096, allow_blank=True, default="")
    attachments = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=File.objects.filter(is_active=True))
    mentions = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=ProfileModel.objects.all()
    )

    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'text',
            'message_reply',
            'attachments',
            'updated',
            'mentions',
        )

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', None)
        mentions = validated_data.pop('mentions', None)
        instance.text = validated_data.get('text')
        instance.message_reply = validated_data.get('message_reply')
        instance.is_updated = True
        instance.updated = validated_data.get('updated')
        instance.save()
        if attachments:
            instance.attachments.set(attachments[:5])
        else:
            instance.attachments.clear()
        if mentions:
            instance.mentions.set(mentions)
        else:
            instance.mentions.clear()
        return instance

    def validate_message_reply(self, data):
        if data and str(data.chat_id) != self.initial_data.get('chat', ''):
            raise ValidationError('Отвечаемое сообщение не существует')
        return data


class ChatDetailSerializer(serializers.ModelSerializer):
    chat_author = AppUserSerializer()
    last_message = serializers.SerializerMethodField()
    workgroup = serializers.SerializerMethodField()
    readed_at = serializers.SerializerMethodField()
    my_readed_at = serializers.SerializerMethodField()

    def get_last_message(self, instance):
        cached_last_message_data = utils.get_last_message_data(instance)
        if cached_last_message_data:
            return cached_last_message_data
        else:
            last_message = instance.messages.filter(is_deleted=False, is_active=True).order_by('-created').first()
        if last_message:
            return MessageListSerializer(last_message).data
        else:
            return None

    def get_workgroup(self, instance):
        work_group = instance.workgroupmodel_set.filter(is_active=True, with_chat=True).last()
        if work_group:
            data = {
                'uid': work_group.id,
                'name': work_group.name,
                'is_project': work_group.is_project
            }
            if work_group.is_project:
                data['date_start_plan'] = work_group.date_start_plan
                data['dead_line'] = work_group.dead_line
            return data
        else:
            return None

    def get_readed_at(self, instance):
        request = self.context.get('request')
        user = request.user.profile
        last_read_member = instance.members.exclude(user=user).order_by('-last_message_created').first()
        if last_read_member:
            readed_at = last_read_member.last_message_created
            if readed_at:
                return serializers.DateTimeField().to_representation(readed_at)
            else:
                return None
        else:
            return None

    def get_my_readed_at(self, instance):
        readed_at = getattr(instance, 'last_message_created', None)
        if not readed_at:
            request = self.context.get('request')
            user = getattr(getattr(request, 'user', None), 'profile', None)
            if user:
                member = instance.members.filter(user=user).only('last_message_created').first()
                readed_at = getattr(member, 'last_message_created', None)
        if readed_at:
            return serializers.DateTimeField().to_representation(readed_at)
        return None

    class Meta:
        model = models.ChatModel
        fields = (
            'id',
            'name',
            'chat_uid',
            'chat_author',
            'last_sent',
            'is_public',
            'is_active',
            'last_message',
            'workgroup',
            'color',
            'metadata',
            'readed_at',
            'my_readed_at',
            'is_support',
        )

    def to_representation(self, instance):
        user = self.context.get('request').user.profile
        data = super().to_representation(instance)
        members = MemberSerializer(instance.members, many=True).data
        member_count = 0
        if instance.is_public is False:
            for member in members:
                member_count += 1
                if member.get('user').get('id') != str(user.pk):
                    data['name'] = member.get('user').get('full_name')
                    data['recipient'] = member.get('user')
        else:
            data['is_moderator'] = False
            for member in members:
                if member.get('user') and member.get('user').get('id') == str(user.pk) and member.get(
                        'is_moderator') is True:
                    data['is_moderator'] = True
                if member.get('is_active') is True:
                    member_count += 1
        data['new_message_count'], data['new_mention_count'] = utils.get_last_message_count(instance, user)
        data['member_count'] = member_count
        data['is_open'] = False
        data['is_pinned'] = getattr(instance, 'is_pinned', False) # Добавляем is_pinned из аннотации
        data['in_favorites'] = get_in_favorites(instance)
        return data


class ChatShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChatModel
        fields = (
            'id',
            'name',
            'chat_uid',
            'is_public',
            'is_active',
            'color',
            'is_support',
        )


class ChatNotifySerializer(serializers.ModelSerializer):
    """Сериализатор для уведомлений, не требует request в context.
    name: для группового чата — chat.name, для приватного — full_name другого участника
    (если в context передан profile_id — pk ProfileModel, для которого строится имя)."""
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.ChatModel
        fields = (
            'id',
            'name',
            'chat_uid',
            'is_public',
            'is_active',
            'color',
            'is_support',
        )

    def get_name(self, instance):
        chat = instance
        if not chat:
            return ''
        if chat.is_public:
            return chat.name or ''
        profile_id = self.context.get('profile_id')
        if profile_id is None:
            return chat.name or ''
        qs = chat.members.filter(is_active=True).exclude(user_id=profile_id).select_related('user')
        other_member = qs.first()
        if other_member and other_member.user:
            return other_member.user.full_name
        return chat.name or ''


class MessageForwardedSerializer(serializers.ModelSerializer):

    message_author = CachedAppUserSerializer(source='message_author_id')
    attachments = serializers.SerializerMethodField()
    message_reply = MessageReplySerializer()
    share = serializers.SerializerMethodField()
    chat = ChatShortSerializer()

    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_author',
            'message_uid',
            'text',
            'created',
            'is_system',
            'is_ai_message',
            'is_deleted',
            'is_pinned',
            'attachments',
            'chat',
            'message_reply',
            'share',
        )

    def get_attachments(self, instance):
        return get_serialized_chat_attachments(instance)

    def get_share(self, instance):
        share_id = instance.share_id
        if share_id:
            try:
                share_obj = BaseModel.objects.super_get(pk=share_id)
            except BaseModel.DoesNotExist:
                return None
            s_data = share_obj.get_serializer_class(action='list')(instance=share_obj).data
            s_data['type'] = share_obj.get_label()
            return s_data


class LastMessageSerializer(serializers.ModelSerializer):
    message_author = CachedUserPreviewSerializer(source='message_author_id')
    chat = serializers.UUIDField(source='chat_id', read_only=True)
    attachments = serializers.SerializerMethodField()
    message_reply = MessageReplySerializer()
    share = serializers.SerializerMethodField()
    message_forwarded = MessageForwardedSerializer()

    def get_attachments(self, instance):
        return get_serialized_chat_attachments(instance)

    def get_share(self, instance):
        share_id = instance.share_id
        if share_id:
            try:
                share_obj = BaseModel.objects.super_get(pk=share_id)
            except BaseModel.DoesNotExist:
                return None
            s_data = share_obj.get_serializer_class(action='chat_share')(instance=share_obj).data
            s_data['type'] = share_obj.get_label()
            return s_data

    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_author',
            'message_uid',
            'text',
            'created',
            'is_system',
            'is_ai_message',
            'is_deleted',
            'is_pinned',
            'attachments',
            'chat',
            'message_reply',
            'share',
            'message_forwarded',
            'forwarded',
            'updated',
            'is_updated',
            'mentions',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'updated_messages' in self.context:
            updated_messages = self.context.get('updated_messages')
        else:
            updated_messages = socketio_redis.hgetall(f'updated_messages:{instance.chat_id}')
            self.context['updated_messages'] = updated_messages
        if updated_messages:
            updated_instance_str = updated_messages.get(str(instance.message_uid))
            if updated_instance_str:
                updated_instance_dict = json.loads(updated_instance_str)
                data['text'] = updated_instance_dict.get('text')
                data['attachments'] = updated_instance_dict.get('attachments')
                data['message_reply'] = updated_instance_dict.get('message_reply')
        return data


class ChatListSerializer(serializers.ModelSerializer):
    chat_author = CachedUserPreviewSerializer(source='author_id')
    last_message = serializers.SerializerMethodField()
    my_readed_at = serializers.SerializerMethodField()
    readed_at = serializers.SerializerMethodField()

    def get_last_message(self, instance):
        last_messages_by_chat_uid = self.context.get('last_messages_by_chat_uid', {})
        last_message = last_messages_by_chat_uid.get(instance.chat_uid)
        if last_message:
            return LastMessageSerializer(last_message, context=self.context).data
        return None

    def get_readed_at(self, instance):
        request = self.context.get('request')
        if request:
            user = request.user.profile
            last_read_member = instance.members.exclude(user=user).order_by('-last_message_created').first()
            if last_read_member:
                readed_at = last_read_member.last_message_created
                if readed_at:
                    return serializers.DateTimeField().to_representation(readed_at)
                else:
                    return None
            else:
                return None
        else:
            return None

    def get_my_readed_at(self, instance):
        readed_at = getattr(instance, 'last_message_created', None)
        if not readed_at:
            request = self.context.get('request')
            user = getattr(getattr(request, 'user', None), 'profile', None)
            if user:
                member = instance.members.filter(user=user).only('last_message_created').first()
                readed_at = getattr(member, 'last_message_created', None)
        if readed_at:
            return serializers.DateTimeField().to_representation(readed_at)
        return None

    class Meta:
        model = models.ChatModel
        fields = (
            'id',
            'name',
            'chat_uid',
            'chat_author',
            'last_sent',
            'is_public',
            'is_active',
            'last_message',
            'color',
            'my_readed_at',
            'readed_at',
            'is_support',
        )

    def to_representation(self, instance):
        user = self.context.get('request').user.profile
        data = super().to_representation(instance)
        members = tuple(instance.members.all())
        member_count = 0
        if instance.is_public is False:
            for member in members:
                member_count += 1
                if member.user_id != user.pk:
                    recipient_data = CachedUserPreviewSerializer(member.user_id).data
                    data['name'] = recipient_data.get('full_name')
                    data['recipient'] = recipient_data
                    break
        else:
            data['is_moderator'] = False
            for member in members:
                if member.user_id == user.pk and member.is_moderator is True:
                    data['is_moderator'] = True
                if member.is_active is True:
                    member_count += 1
        data['new_message_count'], data['new_mention_count'] = utils.get_last_message_count(instance, user)
        data['member_count'] = member_count
        data['is_open'] = False
        data['is_pinned'] = getattr(instance, 'is_pinned', False)  # Добавляем is_pinned из аннотации
        return data


class ChatListShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChatModel
        fields = (
            'id',
            'name',
            'chat_uid',
            'is_public',
            'is_active',
            'color',
            'is_support',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get('request').user.profile
        if instance.is_public is False:
            for member in instance.members.all():
                if member.user_id != user.pk:
                    recipient_data = CachedUserPreviewSerializer(member.user_id).data
                    data['name'] = recipient_data.get('full_name')
                    data['recipient'] = recipient_data
                    break
        return data


class MessageListSerializer(serializers.ModelSerializer):
    message_author = AppUserSerializer()
    pin_author = AppUserSerializer()
    attachments = serializers.SerializerMethodField()
    message_reply = MessageReplySerializer()
    share = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    message_forwarded = MessageForwardedSerializer()

    def get_attachments(self, instance):
        return get_serialized_chat_attachments(instance)

    def get_share(self, instance):
        share_id = instance.share_id
        if share_id:
            try:
                share_obj = BaseModel.objects.super_get(pk=share_id)
            except BaseModel.DoesNotExist:
                return None
            s_data = share_obj.get_serializer_class(action='chat_share')(instance=share_obj).data
            s_data['type'] = share_obj.get_label()
            return s_data

    def get_is_new(self, instance):
        return bool(getattr(instance, 'is_new', 1))

    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_author',
            'message_uid',
            'text',
            'created',
            'is_system',
            'is_ai_message',
            'is_deleted',
            'is_pinned',
            'pin_author',
            'attachments',
            'chat',
            'message_reply',
            'share',
            'is_new',
            'message_forwarded',
            'forwarded',
            'updated',
            'is_updated',
            'mentions',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            user = request.user.profile
        else:
            user = None
        data['reactions'] = get_reactions_data(instance, user)
        if 'updated_messages' in self.context:
            updated_messages = self.context.get('updated_messages')
        else:
            updated_messages = socketio_redis.hgetall(f'updated_messages:{instance.chat_id}')
            self.context['updated_messages'] = updated_messages
        if updated_messages:
            updated_instance_str = updated_messages.get(str(instance.message_uid))
            if updated_instance_str:
                updated_instance_dict = json.loads(updated_instance_str)
                data['text'] = updated_instance_dict.get('text')
                data['attachments'] = updated_instance_dict.get('attachments')
                data['message_reply'] = updated_instance_dict.get('message_reply')
        return data


class MessageChatShareSerializer(serializers.ModelSerializer):
    """Для отображения в поле reason связанной задачи"""
    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_uid',
            'chat',
        )

class MessageNotifySerializer(serializers.ModelSerializer):
    chat = ChatShortSerializer()
    message_author = CachedAppUserSerializer(source='message_author_id')
    class Meta:
        model = models.MessageModel
        fields = (
            'id',
            'message_uid',
            'message_author',
            'chat',
        )


class ChatSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [search_indexes.ChatIndex, ProfileIndex]
        fields = (
            'content'
        )

    def to_representation(self, instance):
        obj = instance.object
        data = obj.get_serializer_class(action='list')(instance=obj, context=self.context).data
        data['type'] = obj.get_label()
        return data


class AltChatSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        original_object = instance.original_object
        obj_type = original_object.get_label()
        if obj_type == 'users.ProfileModel':
            data = CachedAppUserSerializer(instance=original_object, context=self.context).data
        else:
            data = original_object.get_serializer_class(action='list')(
                instance=original_object,
                context=self.context
            ).data
        data['type'] = obj_type
        return data


class SupportMessageTemplateModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SupportMessageTemplateModel
        fields = (
            'id',
            'is_public',
            'text',
            'title'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context['request']
        data['update_available'] = instance.get_update_permission(request)
        return data


class ChatSummarySerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer()
    
    class Meta:
        model = models.ChatSummaryModel
        fields = (
            'id',
            'chat',
            'user',
            'start_date',
            'end_date',
            'summary',
            'status',
            'started_at',
            'completed_at',
        )


class ChatSummaryNotifySerializer(serializers.ModelSerializer):
    """Сериализатор для уведомления ChatSummaryReady."""
    chat = serializers.SerializerMethodField()

    class Meta:
        model = models.ChatSummaryModel
        fields = ('id', 'user', 'start_date', 'end_date', 'chat')

    def get_chat(self, instance):
        if not instance.chat:
            return None
        context = {**self.context, 'profile_id': instance.user_id}
        return ChatNotifySerializer(instance.chat, context=context).data
