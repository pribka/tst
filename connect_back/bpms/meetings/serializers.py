import uuid
from urllib.parse import urlparse, quote
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import ObjectDoesNotExist

from rest_framework import serializers, exceptions
from rest_framework.utils import model_meta
from rest_framework.exceptions import ValidationError

from django_q.tasks import async_task
from drf_haystack.serializers import HaystackSerializer

from users.serializers import AppUserSerializer, CachedAppUserPreviewSerializer
from users.models import ProfileModel
from common.serializers import RelatedObjectSerializer, AppFileSerializer, CachedBaseModelSerializer, SelectListSerializer
from common.models import BaseModel
from bpms.tasks.models import TaskExecutionTimeModel, TaskModel, TaskWorkTypeModel
from bpms.workgroups.models import WorkgroupModel
from bpms.workgroups.serializers import WorkgroupNameLogoSerializer
from bkz3.settings import DOWNLOADER_PATH, BACKEND_URL
from . import models
from . import notifications
from .utils import get_invite_link, get_connect_meeting_url, get_webcams_file_url
from . import search_indexes
from telegram_bot.base import base_bot
from bpms.chat_ai.serializers import IntentListSerializer
from bpms.event_calendar.utils import create_calendar_event_for_meeting
from help_desk import serializers as help_desk_serializers


def _get_record_file_download_url(instance):
    if not (instance.record_file_id and instance.record_file and instance.record_file.is_active):
        return None
    record_file_data = AppFileSerializer(instance.record_file).data
    record_file_path = record_file_data.get('path')
    if DOWNLOADER_PATH is not None:
        parent_path = quote(f"?obj={instance.pk}&id={record_file_data.get('id')}&target=record_file")
        record_file_path = f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'
    return record_file_path


def _get_section_intents_stats(section):
    total_intents = 0
    accepted_intents = 0
    deleted_intents = 0

    records = section.records.all().prefetch_related('intents')
    for record in records:
        intents_qs = record.intents.all()
        total_intents += intents_qs.count()
        accepted_intents += intents_qs.filter(related_object__isnull=False).count()
        deleted_intents += intents_qs.filter(is_active=False).count()

    return {
        'total': total_intents,
        'accepted': accepted_intents,
        'deleted': deleted_intents,
        'unprocessed': total_intents - accepted_intents - deleted_intents,
    }



class MeetingRecordSerializer(serializers.ModelSerializer):
    record_file = serializers.SerializerMethodField()
    storage_provider_display = serializers.SerializerMethodField()

    class Meta:
        model = models.MeetingRecordsModel
        fields = (
            'id',
            'url',
            'is_external',
            'own_file',
            'storage_provider',
            'storage_provider_display',
            'created_at',
            'status',
            'record_file',
        )

    def get_record_file(self, instance):
        if instance.record_file_id and instance.record_file and instance.record_file.is_active:
            record_file_data = AppFileSerializer(instance.record_file).data
            record_file_path = _get_record_file_download_url(instance)
            if record_file_path:
                record_file_data['path'] = record_file_path
            return record_file_data
        return None

    def get_storage_provider_display(self, instance):
        return instance.get_storage_provider_display()


class MeetingRecordDetailSerializer(serializers.ModelSerializer):
    storage_provider_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField() # ссылка только на аудио на сервере BBB
    record_file = serializers.SerializerMethodField() # ссылка на склеенное аудио+видео на нашем сервере

    class Meta:
        model = models.MeetingRecordsModel
        fields = (
            'id',
            'url',
            'is_external',
            'own_file',
            'storage_provider',
            'storage_provider_display',
            'created_at',
            'status',
            'file_url',
            'record_file',
            'transcribe',
        )

    def get_file_url(self, instance):
        if getattr(instance, 'own_file', False):
            return instance.url
        return get_webcams_file_url(instance.url)

    def get_record_file(self, instance):
        if instance.record_file_id and instance.record_file and instance.record_file.is_active:
            record_file_data = AppFileSerializer(instance.record_file).data
            record_file_path = _get_record_file_download_url(instance)
            if record_file_path:
                record_file_data['path'] = record_file_path
            return record_file_data
        return None

    def get_storage_provider_display(self, instance):
        return instance.get_storage_provider_display()


class MeetingMemberListSerializer(serializers.ModelSerializer):
    user = AppUserSerializer()

    class Meta:
        model = models.MeetingMemberModel
        fields = (
            'user',
            'is_moderator'
        )


class PlannedMeetingListSerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    members_count = serializers.SerializerMethodField()
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)

    class Meta:
        model = models.PlannedMeetingModel
        fields = (
            'id',
            'name',
            'status',
            'is_external',
            'date_begin',
            'duration',
            'author',
            'members_count',
            'project',
        )

    def get_members_count(self, instance):
        annotated_members_count = getattr(instance, 'members_count', None)
        if annotated_members_count is not None:
            return annotated_members_count
        return instance.members.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_external:
            data['target'] = ''
            data['invite_link'] = ''
        else:
            data['target'] = get_connect_meeting_url(instance.id)
            data['invite_link'] = get_invite_link(instance.invite_link)
        return data


class PlannedMeetingDetailSerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    members_count = serializers.SerializerMethodField()
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)

    class Meta:
        model = models.PlannedMeetingModel
        fields = (
            'id',
            'name',
            'description',
            'status',
            'is_external',
            'date_begin',
            'duration',
            'author',
            'members_count',
            'has_record',
            'metadata',
            'project',
        )

    def get_members_count(self, instance):
        return instance.members.all().count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_external:
            data['target'] = ''
            data['invite_link'] = ''
        else:
            data['target'] = get_connect_meeting_url(instance.id)
            data['invite_link'] = get_invite_link(instance.invite_link)
        return data


class PlannedMeetingMyDaySerializer(serializers.ModelSerializer):
    related_object = RelatedObjectSerializer()
    project = SelectListSerializer()

    class Meta:
        model = models.PlannedMeetingModel
        fields = (
            'id',
            'name',
            'related_object',
            'project',
        )


class MeetingMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeetingMemberModel
        fields = (
            'user',
            'is_moderator',
        )
    def to_internal_value(self, data):
        """Позволяем элементу списка быть либо:
          - строкой (uuid): - для создания собраний из AI-чата
          - словарём: {"user": "...", "is_moderator": true}
        """
        if isinstance(data, str):
            data = {"user": data}
        return super().to_internal_value(data)

class MeetingMemberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeetingMemberModel
        fields = (
            'meeting',
            'user',
            'is_moderator',
        )

    def create(self, validated_data):
        meeting = validated_data.get('meeting')
        user = validated_data.get('user')
        is_moderator = validated_data.get('is_moderator', False)
        member, created = models.MeetingMemberModel.objects.update_or_create(
            meeting=meeting,
            user=user,
            defaults={'is_active': True, 'is_moderator': is_moderator}
        )
        return member


class MeetingMemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeetingMemberModel
        fields = (
            'id',
            'is_moderator',
        )


class PlannedMeetingUpdateSerializer(serializers.ModelSerializer):
    duration = serializers.IntegerField(default=0)
    date_begin = serializers.DateTimeField(allow_null=False)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    name = serializers.CharField(allow_null=False, max_length=255)
    project = serializers.PrimaryKeyRelatedField(
        queryset=WorkgroupModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.PlannedMeetingModel
        fields = (
            'id',
            'name',
            'description',
            'date_begin',
            'duration',
            'metadata',
            'project',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            result = super().update(instance, validated_data)
            new_members = self.add_edit_delete_members(instance)
        # Рассылаем приглашение к собранию только если нет привязанных событий (уведомления события уйдут сами)
        has_calendar_events = instance.calendar_events.filter(is_active=True).exists()
        if not has_calendar_events and new_members:
            async_task(notifications.notify_about_invite_to_meeting, instance, tuple(new_members))
        return result

    def add_edit_delete_members(self, instance):
        new_members = self.add_members(instance)
        self.edit_members(instance)
        self.delete_members(instance)
        return new_members

    def add_members(self, instance):
        try:
            create_list = self.initial_data.get('members', dict()).get('add', [])
        except AttributeError:
            raise exceptions.ValidationError('members is not valid')
        if not isinstance(create_list, list):
            raise exceptions.ValidationError('members create list is not list')
        new_members = []
        for each in create_list:
            if not isinstance(each, dict):
                raise exceptions.ValidationError('created member is not valid')
            each['meeting'] = instance.pk
            member_serializer = MeetingMemberCreateSerializer(data=each)
            member_serializer.is_valid(raise_exception=True)
            try:
                member_serializer.save()
                new_members.append(member_serializer.instance.user_id)
            except IntegrityError:
                raise exceptions.ValidationError('created member is not valid')
        return new_members

    def edit_members(self, instance):
        try:
            edit_list = self.initial_data.get('members', dict()).get('edit', [])
        except AttributeError:
            raise exceptions.ValidationError('members is not valid')
        if not isinstance(edit_list, list):
            raise exceptions.ValidationError('members edit list is not list')
        for each in edit_list:
            try:
                member = instance.meetingmembermodel_set.get(user_id=each.get('user', ''))
            except (ObjectDoesNotExist, AttributeError):
                raise exceptions.ValidationError('edited member is not valid')
            member_serializer = MeetingMemberUpdateSerializer(instance=member, data=each, partial=True)
            member_serializer.is_valid(raise_exception=True)
            try:
                member_serializer.save()
            except IntegrityError:
                raise exceptions.ValidationError('edited member is not valid')

    def delete_members(self, instance):
        try:
            delete_list = self.initial_data.get('members', dict()).get('delete', [])
        except AttributeError:
            raise exceptions.ValidationError('members is not valid')
        if not isinstance(delete_list, list):
            raise exceptions.ValidationError('members delete list is not list')
        try:
            members = instance.meetingmembermodel_set.filter(user_id__in=delete_list).exclude(
                user=instance.author,
            )
        except AttributeError:
            raise exceptions.ValidationError('members delete list is not valid')
        members.delete()

    def to_representation(self, instance):
        return PlannedMeetingDetailSerializer(instance, context={'request': self.context.get('request')}).data


class PlannedMeetingAddMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeetingMemberModel
        fields = (
            'id',
            'user'
        )

    def create(self, validated_data):
        view = self.context.get('view')
        meeting_id = view.kwargs['pk']
        member, created = models.MeetingMemberModel.objects.create_or_update(
            user=validated_data.get('user'),
            meeting_id=meeting_id,
            defaults={'is_active': True}
        )
        return member


class PlannedMeetingCreateSerializer(serializers.ModelSerializer):
    members = MeetingMemberSerializer(many=True, required=False)
    name = serializers.CharField(allow_null=False, max_length=255)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    duration = serializers.IntegerField(default=50)
    date_begin = serializers.DateTimeField(allow_null=False)
    project = serializers.PrimaryKeyRelatedField(
        queryset=WorkgroupModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.PlannedMeetingModel
        fields = (
            'id',
            'date_begin',
            'duration',
            'name',
            'description',
            'members',
            'metadata',
            'project',
        )

    def create(self, validated_data):
        date_begin = validated_data.get('date_begin')
        duration = validated_data.get('duration')
        server = 'default'
        # if 'request' in self.context:
        #     request = self.context.get('request')
        #     host = request.get_host()
        #     if host.find('.ru') > 0:
        #         server = 'ru'
        with transaction.atomic():
            meeting = models.PlannedMeetingModel.objects.create(
                date_begin=date_begin,
                duration=duration,
                description=validated_data.get('description'),
                name=validated_data.get('name'),
                server_id=server,
                metadata=validated_data.get('metadata', {}),
                project=validated_data.get('project'),
            )
            author = meeting.author
            members = validated_data.get('members', [])
            for member in members:
                if member['user'] == author:
                    continue
                try:
                    models.MeetingMemberModel.objects.create(
                        meeting=meeting, user=member['user'], is_moderator=member.get('is_moderator', False))
                except IntegrityError:
                    pass
            try:
                models.MeetingMemberModel.objects.create(meeting=meeting, user=author, is_moderator=True)
            except IntegrityError:
                pass
            if validated_data.get('attachments'):
                meeting.attachments.set(validated_data.get('attachments')[:5])
            if not self.context.get('from_event'):
                create_calendar_event_for_meeting(meeting, request=self.context.get('request'))
        return meeting

    def to_representation(self, instance):
        return PlannedMeetingDetailSerializer(instance, context={'request': self.context.get('request')}).data


class MeetingModeratorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeetingMemberModel
        fields = (
            'user',
            'meeting',
            'is_moderator'
        )


class MeetingSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [search_indexes.MeetingIndex]
        fields = (
            'meeting_id',
        )

    def to_representation(self, instance):
        return PlannedMeetingListSerializer(
            instance.object, context={'request': self.context.get('request')}, many=False).data


class MeetingSectionMemberListSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')

    class Meta:
        model = models.MeetingSectionMemberModel
        fields = (
            'user',
            'duration',
            'is_execution_time_created',
        )


class MeetingSectionListSerializer(serializers.ModelSerializer):
    members = MeetingSectionMemberListSerializer(
        many=True,
        read_only=True,
        source='meeting_section_members'
    )
    execution_time_project = SelectListSerializer()
    actions = serializers.SerializerMethodField()

    def get_actions(self, instance):
        request = self.context.get('request')
        if not request:
            return {"update": {"availability": False}}
        return {
            "update": {"availability": instance.get_update_permission(request)}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['intents'] = _get_section_intents_stats(instance)

        return data

    class Meta:
        model = models.MeetingSectionModel
        fields = (
            'id',
            'name',
            'status',
            'date_start',
            'date_end',
            'duration',
            'members',
            'execution_time_project',
            'actions',
        )


class MeetingSectionDetailSerializer(serializers.ModelSerializer):
    members = MeetingSectionMemberListSerializer(
        many=True,
        read_only=True,
        source='meeting_section_members'
    )
    visors = CachedAppUserPreviewSerializer(many=True)
    records = MeetingRecordDetailSerializer(
        many=True,
        read_only=True,
    )
    execution_time_project = SelectListSerializer()

    class Meta:
        model = models.MeetingSectionModel
        fields = (
            'id',
            'name',
            'status',
            'date_start',
            'date_end',
            'duration',
            'members',
            'visors',
            'records',
            'execution_time_project',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Транскрибация и краткое содержание
        records_qs = instance.records.order_by('created_at')
        # transcribes = [text for text in records_qs.values_list('transcribe', flat=True) if text]
        summaries = [
            text
            for text in records_qs.filter(is_summary_ready=True).values_list('summary', flat=True)
            if text
        ]
        efficiencies = [text for text in records_qs.values_list('efficiency', flat=True) if text]
        
        summary_parts = []
        if summaries:
            summary_parts.append("\n".join(summaries))
        if summaries and efficiencies:
            summary_parts.extend(["", ""])
            summary_parts.append("<b>Анализ эффективности</b>")
            summary_parts.append("\n".join(efficiencies))
        
        data['summary'] = "\n".join(summary_parts)
        # data['transcribe'] = "\n".join(transcribes) # транскрибация на фронте берется из records

        # Намерения
        from bpms.chat_ai.models import IntentModel
        record_ids = list(instance.records.values_list('id', flat=True))
        intents_qs = IntentModel.objects.filter(source_object_id__in=record_ids)

        intents_data = []
        for intent in intents_qs:
            if intent.is_active:
                intents_data.append(IntentListSerializer(intent).data)
            else:
                intents_data.append({
                    'id': intent.id,
                    'is_active': intent.is_active
                })

        data['intents'] = intents_data

        # Участники собрания, которые не присутствовали на секции
        section_member_ids = set(member.id for member in instance.members.all())
        absent_members = [
            member for member in instance.meeting.members.all()
            if member.id not in section_member_ids
        ]
        data['absent_members'] = CachedAppUserPreviewSerializer(
            absent_members,
            many=True,
            context=self.context
        ).data

        return data


class MeetingSectionIntentsSerializer(serializers.ModelSerializer):
    meeting = PlannedMeetingMyDaySerializer()
    records = MeetingRecordDetailSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = models.MeetingSectionModel
        fields = (
            'id',
            'name',
            'meeting',
            'records',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Транскрибация и краткое содержание (аналогично MeetingSectionDetailSerializer)
        records = list(instance.records.all())
        records_sorted = sorted(records, key=lambda record_obj: record_obj.created_at)
        transcribes = [record_obj.transcribe for record_obj in records_sorted if record_obj.transcribe]
        summaries = [record_obj.summary for record_obj in records_sorted if record_obj.summary]
        efficiencies = [record_obj.efficiency for record_obj in records_sorted if record_obj.efficiency]
        summary_parts = []
        if summaries:
            summary_parts.append("\n".join(summaries))
        if efficiencies:
            summary_parts.extend(["", ""])
            summary_parts.append("<b>Анализ эффективности</b>")
            summary_parts.append("\n".join(efficiencies))
        data['summary'] = "\n".join(summary_parts)
        data['transcribe'] = "\n".join(transcribes)

        intents_data = []
        for record in records_sorted:
            record_intents = record.intents.all()
            for intent in record_intents:
                if intent.is_active:
                    intents_data.append(IntentListSerializer(intent, context=self.context).data)
                else:
                    intents_data.append({
                        'id': intent.id,
                        'is_active': intent.is_active
                    })

        data['intents'] = intents_data
        return data


class MeetingRecordUntranscribedSerializer(serializers.ModelSerializer):
    section = MeetingSectionListSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = models.MeetingRecordsModel
        fields = (
            'id',
            'file_url',
            'members_count',
            'section',
        )

    def get_file_url(self, instance):
        return get_webcams_file_url(instance.url)

    def get_members_count(self, instance):
        section = instance.section
        if section is None:
            return 0
        return len(section.meeting_section_members.all())


class MeetingSectionVisorsUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления наблюдателей секции собрания."""
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.MeetingSectionModel
        fields = ('id', 'visors')

    def update(self, instance, validated_data):
        visors = validated_data.pop('visors', None)
        with transaction.atomic():
            if visors is not None:
                instance.visors.clear()
                instance.visors.set(visors)
        return instance

    def to_representation(self, instance):
        return {
            'visors': CachedAppUserPreviewSerializer(
                instance.visors.all(),
                many=True,
                context=self.context
            ).data
        }


class MeetingSectionNameUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления названия секции собрания."""
    name = serializers.CharField(max_length=255, required=True, allow_blank=True)

    class Meta:
        model = models.MeetingSectionModel
        fields = ('id', 'name')


class MeetingSectionMyDaySerializer(serializers.ModelSerializer):
    meeting = PlannedMeetingMyDaySerializer()
    execution_time_project = SelectListSerializer()
    members = MeetingSectionMemberListSerializer(
        many=True,
        read_only=True,
        source='meeting_section_members'
    )
    visors = CachedAppUserPreviewSerializer(many=True)
    actions = serializers.SerializerMethodField()

    def get_actions(self, instance):
        request = self.context.get('request')
        if not request:
            return {"update": {"availability": False}}
        return {
            "update": {"availability": instance.get_update_permission(request)}
        }

    class Meta:
        model = models.MeetingSectionModel
        fields = (
            'id',
            'name',
            'status',
            'date_start',
            'date_end',
            'duration',
            'members',
            'visors',
            'meeting',
            'execution_time_project',
            'actions',
        )
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Сериализуем связанных пользователей (те profile_ids, благодаря которым секция попала в список)
        user_ids = self.context.get('user_ids', [])
        user_ids_set = set(user_ids)
        related_members = [
            member for member in instance.members.all()
            if str(member.pk) in user_ids_set
        ]
        data['related_users'] = CachedAppUserPreviewSerializer(
            related_members,
            many=True,
            context=self.context
        ).data if related_members else []

        data['intents'] = _get_section_intents_stats(instance)
        
        return data


class CallStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CallStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
        )


class CallListSerializer(serializers.ModelSerializer):
    initiator = CachedAppUserPreviewSerializer(source='initiator_id')
    accepted_by = CachedAppUserPreviewSerializer(source='accepted_by_id')
    current_target = CachedAppUserPreviewSerializer(many=True)
    meeting = serializers.SerializerMethodField()
    ticket = help_desk_serializers.HelpDeskTicketCallShortSerializer(read_only=True)
    status = CallStatusSerializer()

    class Meta:
        model = models.CallModel
        fields = (
            'id',
            'status',
            'chat_uid',
            'initiator',
            'accepted_by',
            'current_target',
            'ring_attempt',
            'ring_started_at',
            'started_at',
            'answered_at',
            'ended_at',
            'meeting',
            'ticket',
            'created_at',
        )

    def get_meeting(self, instance):
        meeting = instance.meeting
        if not meeting:
            return None
        return meeting.get_connect_info()


class CallNotifySerializer(serializers.ModelSerializer):
    """
    Отдельный сериализатор для socket-событий по звонкам.
    Изменять осторожно: это notify-контракт, а не REST-ответ.
    """
    initiator = CachedAppUserPreviewSerializer(source='initiator_id')
    accepted_by = CachedAppUserPreviewSerializer(source='accepted_by_id')
    current_target = CachedAppUserPreviewSerializer(many=True)
    meeting = serializers.SerializerMethodField()
    ticket = help_desk_serializers.HelpDeskTicketCallShortSerializer(read_only=True)
    status = CallStatusSerializer()

    class Meta:
        model = models.CallModel
        fields = (
            'id',
            'status',
            'chat_uid',
            'initiator',
            'accepted_by',
            'current_target',
            'ring_attempt',
            'ring_started_at',
            'started_at',
            'answered_at',
            'ended_at',
            'meeting',
            'ticket',
            'created_at',
        )

    def get_meeting(self, instance):
        meeting = instance.meeting
        if not meeting:
            return None
        return meeting.get_connect_info()
