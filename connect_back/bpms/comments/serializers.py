from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, exceptions as drf_exceptions

from django_q.tasks import async_task

from bpms.tasks.models import TaskModel

from common.utils import get_serialized_attachments

from common.models import File

from bpms.reactions.utils import get_reactions_data

from users.models import ProfileModel
from users.serializers import AppUserSerializer, CachedAppUserSerializer, CachedAppUserPreviewSerializer

from . import notifications, utils
from .models import CommentModel


class CommentShortReplySerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id', allow_null=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = CommentModel
        fields = (
            'id',
            'text',
            'text_clear',
            'attachments',
            'author',
            'is_active',
            'created_at',
            'updated_at',
            'is_updated',
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_active:
            return data
        else:
            data['text'] = 'Комментарий удалён'
            data['text_clear'] = 'Комментарий удалён'
            data['attachments'] = []
            return data


class CommentListFullSerializer(serializers.ModelSerializer):
    # parent = CommentShortReplySerializer()
    # author = AppUserSerializer(
    #     required=False,
    #     read_only=True,
    # )
    # children_count = serializers.SerializerMethodField()
    # attachments = serializers.SerializerMethodField()

    class Meta:
        model = CommentModel
        fields = (
            #      'id',
            #   'parent',
            #       'is_personal',
            'text',
            #   'author',
            #    'created_at',
            #  'children_count',
            # 'related_object',
            # 'attachments',
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['children'] = []
        data['author'] = instance.author.full_name if instance.author else None

        for child in instance.children.filter(is_active=True):
            child_data = CommentListFullSerializer(child).data
            data['children'].append(child_data)

        return data


class CommentListSerializer(serializers.ModelSerializer):
    parent = CommentShortReplySerializer()
    author = CachedAppUserPreviewSerializer(source='author_id', allow_null=True)
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = CommentModel
        fields = (
            'id',
            'parent',
            'is_personal',
            'is_system',
            'text',
            'text_clear',
            'author',
            'created_at',
            'updated_at',
            'is_updated',
            'related_object',
            'attachments',
            'mentions',
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        viewer_count = getattr(instance, 'viewer_count', None)
        if viewer_count is None:
            viewer_count = instance.viewers.count()
        data['viewer_count'] = viewer_count
        
        if 'user_profile' in self.context:
            user_profile = self.context.get('user_profile')
        else:
            request = self.context.get('request')
            if request:
                user_profile = request.user.profile

            else:
                user_profile = None
            self.context['user_profile'] = user_profile
        if user_profile:
            prefetched_reaction_id = self.context.get('user_reactions_by_object_id', {}).get(instance.pk)
            data['reactions'] = get_reactions_data(
                instance,
                user_profile,
                prefetched_user_reaction_id=prefetched_reaction_id,
            )

        task_count = getattr(instance, 'task_count', None)
        if task_count is None:
            task_count = TaskModel.objects.filter(is_active=True, reason=instance.pk).count()
        data['task_count'] = task_count
        return data


class CommentCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    mentions = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_null=True, allow_empty=True, queryset=ProfileModel.objects.all()
    )

    class Meta:
        model = CommentModel
        fields = (
            'id',
            'parent',
            'text',
            'related_object',
            'attachments',
            # 'readers',
            'is_personal',
            'mentions',
        )

    def to_internal_value(self, data):
        # Если пришел null в поле mentions, заменяем его на пустой список
        if 'mentions' in data and data['mentions'] is None:
            data['mentions'] = []
        return super().to_internal_value(data)

    def validate(self, attrs):
        if not attrs.get('attachments') and not attrs.get('text'):
            raise drf_exceptions.ValidationError(_('Комментарий не может быть пустым'))
        return attrs

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', None)
        # readers = validated_data.pop('readers', None)
        mentions = validated_data.pop('mentions', None)
        with transaction.atomic():
            # if readers:
            #     validated_data['is_personal'] = True
            comment = CommentModel.objects.create(**validated_data)
            if attachments:
                comment.attachments.set(attachments)
            # if readers:
            #     comment.readers.set(readers)
            if mentions:
                comment.mentions.set(mentions)
                # TODO уведомить об упоминании в transaction.on_commit?
        async_task(notifications.notify_about_new_comment, str(comment.pk))
        # notifications.notify_about_new_comment(str(comment.pk))

        return comment

    def to_representation(self, instance):
        instance.refresh_from_db()
        return CommentListSerializer(instance).data


class CommentUpdateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    mentions = serializers.PrimaryKeyRelatedField(
        many=True, required=False, allow_null=True, allow_empty=True, queryset=ProfileModel.objects.all()
    )

    class Meta:
        model = CommentModel
        fields = (
            'id',
            'text',
            'attachments',
            'mentions',
        )

    def to_internal_value(self, data):
        # Если пришел null в поле mentions, заменяем его на пустой список
        if 'mentions' in data and data['mentions'] is None:
            data['mentions'] = []
        return super().to_internal_value(data)

    def validate(self, attrs):
        if not self.partial and not attrs.get('attachments') and not attrs.get('text'):
            raise drf_exceptions.ValidationError(_('Комментарий не может быть пустым'))
        return attrs

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', None)
        mentions = validated_data.pop('mentions', None)

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if attachments is not None:
                instance.attachments.set(attachments)
            if mentions is not None:
                instance.mentions.set(mentions)
                # TODO уведомить об упоминании в transaction.on_commit?
            if self.partial and not instance.text and not instance.attachments.exists():
                raise drf_exceptions.ValidationError(_('Комментарий не может быть пустым'))
            instance.is_updated = True
            instance.save(update_fields=('is_updated',))
        async_task(utils.send_socketio_about_update_comment, str(instance.pk))
        return instance

    def to_representation(self, instance):
        instance.refresh_from_db()
        return CommentListSerializer(instance).data


class CommentNotifySerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id', allow_null=True)
    attachments = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    def get_text(self, instance):
        text_clear = instance.text_clear
        return text_clear[:167] + '...' if len(text_clear) >= 170 else text_clear

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    class Meta:
        model = CommentModel
        fields = (
            'id',
            'parent',
            'text',
            'author',
            'created_at',
            'updated_at',
            'is_updated',
            'related_object',
            'attachments',
            'is_personal',
            'is_system',
            'mentions',
        )

