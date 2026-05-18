from re import compile

from django.utils import timezone
from django.core.cache import cache

from urllib.parse import quote
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.models import Events, Participants, NotificationTypes, BaseModel, FileBaseModel
from common.serializers import AppFileSerializer

from users.serializers import ProfileDetailSerializer, CustomUserDetailSerializer
from users.serializers import AppUserSerializer, CachedAppUserSerializer  # noqa

from . import models
from .models import NewsModel
from common.utils import get_serialized_attachments

try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None

from bkz3.settings import BACKEND_URL
from . import utils


HTML_TAGS_PATTERN = compile(r"<[^>]+>")
NBSP_PATTERN = compile(r"&nbsp;")


class SocialWebTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SocialWebType
        fields = [
            "id",
            "name"
        ]


class SocialURLsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SocialURLs
        fields = [
            "id",
            "social_web_type",
            "social_link",
        ]

    def validate(self, attrs):
        if attrs.get("social_link", None) is None or len(attrs.get("social_link", [])) == 0:
            raise ValidationError("social link should be included")
        return attrs

    def to_representation(self, instance: models.SocialURLs):
        data = super(SocialURLsSerializer, self).to_representation(instance)
        data["social_web_type"] = SocialWebTypeSerializer(instance.social_web_type).data
        return data


class NewsLiteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)
    author_profile = serializers.SerializerMethodField(read_only=True)

    def to_representation(self, news: NewsModel):
        fields = super().to_representation(news)
        content = news.content
        content = HTML_TAGS_PATTERN.sub("", content)
        content = NBSP_PATTERN.sub(" ", content)
        fields["short_description"] = f"{content[:100]}..."
        fields['attachments'] = get_serialized_attachments(news)
        fields['image'] = utils.get_serialized_image(news)
        return fields

    def get_author_name(self, news: NewsModel):
        if news.author and news.author.user.profile:
            return news.author.user.profile.full_name

    def get_author_profile(self, news: NewsModel):
        if news.author and news.author.user.profile:
            return AppUserSerializer(news.author.user.profile).data

    class Meta:
        model = NewsModel
        fields = [
            "id",
            "author_name",
            "author_profile",
            "title",
            "content",
            "pub_date",
            "image",
            "is_important",
        ]


class NotificationTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTypes
        fields = [
            'id',
            'name',
        ]


class EventParticipantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participants
        fields = [
            'participant_profiles'
        ]

    def to_representation(self, instance):
        timezone.now().isocalendar()

        data = super().to_representation(instance=instance)
        data["participants_profiles_names"] = ProfileDetailSerializer(instance.participant_profiles, many=True).data
        return data


class EventSerializer(serializers.ModelSerializer):
    participants = EventParticipantsSerializer(required=False)

    class Meta:
        model = Events
        fields = [
            'id',
            'name',
            'event_start',
            'event_end',
            'event_place',
            'participants',
            'notification',
            'event_description',
            'repetition_type',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        if instance.notification is not None:
            data['data_notification'] = NotificationTypesSerializer(instance.notification, many=True).data
        else:
            data['data_notification'] = None
        return data

    def validate(self, validated_data):
        if validated_data.get('event_start', None) is None:
            raise ValidationError({"error": "start_date_is_empty"})
        elif validated_data.get('event_end', None) is None:
            raise ValidationError({"error": "end_date_is_empty"})
        elif validated_data['event_end'] <= validated_data['event_start']:
            raise ValidationError({"error": "must_be_greater"})
        elif validated_data.get('name', None) is None:
            raise ValidationError({"error": "name_is_empty"})
        return validated_data

    def create_participants(self, participants, exist_participants=None):
        participants_to_return = exist_participants
        if participants_to_return is not None:
            participants_to_return.participant_profiles.filter(is_active=True)
        if exist_participants is None:
            participants_to_return = Participants.objects.create()
        if participants.get("participant_profiles", None) is not None:
            participants_to_return.participant_profiles.set(participants.get("participant_profiles"))
        participants_to_return.save()
        return participants_to_return

    def create(self, validated_data):
        creator = self.context['request'].user.profile
        data = {
            'creator': creator,
        }
        # Добавляет в модель участников события
        participants = validated_data.pop("participants", {})
        if len(participants):
            participants = self.create_participants(participants)
            data['participants'] = participants
        notification = validated_data.pop('notification', [])
        validated_data.update(data)
        # Создание события
        event = Events.objects.create(**validated_data)
        # Добавление в модель типов оповещения
        if len(notification):
            event.notification.set(notification)
        event.save()
        return event

    def update(self, instance, validated_data):
        participants = validated_data.pop("participants", {})
        data = {}
        if len(participants):
            participants = self.create_participants(participants, instance.participants)
            data["participants"] = participants
        validated_data.update(data)
        notification = validated_data.pop('notification', [])
        instance.notification.set(notification)
        instance.save()
        event = super().update(instance, validated_data)
        return event


class CostingObjectBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CostingObjectModel
        fields = (
            'id',
            'name',
        )


class ProgramBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProgramModel
        fields = (
            'id',
            'name',
        )


class CounterpartyModelBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CounterpartyModel
        fields = (
            'id',
            'name',
        )


class FolderAttachmentsSerializer(serializers.ModelSerializer):
    obj_type = serializers.CharField(default='folder', read_only=True)

    class Meta:
        model = models.BaseCatalog
        fields = (
            'id',
            'name',
            'obj_type',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = instance.foldermodel.description

        return data


class FileAttachmentSerializer(AppFileSerializer):
    path = serializers.SerializerMethodField()
    attachment_date = serializers.SerializerMethodField()
    obj_type = serializers.CharField(default='file')

    def get_path(self, instance):
        path = instance.author_url
        if DOWNLOADER_PATH is not None:
            related_obj_id = self.context.get('related_object', instance.pk)
            parent_path = quote(f"?obj={related_obj_id}&id={instance.pk}&target=attachments")
            path = f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'
        return path

    def get_attachment_date(self, instance):
        return instance.created_at

    class Meta(AppFileSerializer.Meta):
        fields = AppFileSerializer.Meta.fields + ('obj_type', 'attachment_date',)


class FileAndFolderSerializer(serializers.ModelSerializer):
    # folder_path = serializers.CharField(default='', read_only=True)
    # folder = serializers.CharField(default='', read_only=True)

    class Meta:
        model = models.BaseModel
        fields = (
            'id',
            # 'folder_path',
            # 'folder',
        )

    def get_folder_path(self, p):
        """Выстраивание полного пути от корня"""
        parents = p.get_ancestors(include_self=True)
        path = '/'
        for item in parents:
            path += item.name + '/'

        return path

    def to_representation(self, instance):
        ct = instance.ct
        if ct.model == 'file':
            data = FileAttachmentSerializer(instance.basecatalog.file, context=self.context).data
            data['folder_path'] = ''
            data['folder'] = ''
            related_object = self.context.get('related_object')
            file_base_model = FileBaseModel.objects.filter(
                related_object_id=related_object,
                file=instance
            ).order_by('-created_at').first()
            folder = getattr(file_base_model, 'folder', None)
        elif ct.model == 'foldermodel':
            data = FolderAttachmentsSerializer(instance.basecatalog).data
            data['folder_path'] = ''
            data['folder'] = ''

            folder = instance.basecatalog.foldermodel.parent
        else:
            return dict()
        if folder:
            data['folder'] = folder.pk
            data['folder_path'] = self.get_folder_path(folder)
        return data


class CachedFileAndFolderSerializer(serializers.Serializer):

    def to_representation(self, instance):
        related_object = self.context.get('related_object')
        data = cache.get(f'CachedFileAndFolderSerializer_{instance}_ro_{related_object}')
        if not data:
            obj = BaseModel.objects.super_get(pk=instance)
            data = FileAndFolderSerializer(instance=obj, context=self.context).data
            cache.set(f'CachedFileAndFolderSerializer_{instance}_ro_{related_object}', data, timeout=None)
        return data
