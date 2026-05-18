from datetime import timedelta
import random
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions
from rest_framework.exceptions import ValidationError
from django_q.tasks import async_task

from common.models import File
from common.serializers import BaseCatalogRetrieveSerializer, RelatedObjectSerializer
from common.utils import get_serialized_attachments, convert_to_local_timezone
from common.humanize import get_humanized_timezone

from bpms.favorites.utils import get_in_favorites

from users.models import ProfileModel
from users.serializers import AppUserSerializer, CachedAppUserSerializer, CachedAppUserPreviewSerializer
from bpms.tasks.models import TaskExecutionTimeModel, TaskModel, TaskWorkTypeModel
from . import models, utils, notifications


class CalendarGroupModelSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = models.CalendarGroupModel
        fields = (
            'id',
            'name',
            'color',
        )

    def get_id(self, instance):
        return instance.code


class CalendarModelDetailSerializer(serializers.ModelSerializer):
    related_object = serializers.SerializerMethodField()
    calendar_group = CalendarGroupModelSerializer()

    class Meta:
        model = models.CalendarModel
        fields = (
            'id',
            'calendar_group',
            'color',
            'name',
            'related_object',
        )

    def get_related_object(self, instance):
        if instance.related_object:
            related_object = instance.related_object.original_object
            data = related_object.get_serializer_class()(related_object).data
            data['type'] = related_object.get_label()
            return data
        else:
            return None


class CalendarModelListSerializer(serializers.ModelSerializer):
    checked = serializers.SerializerMethodField()

    class Meta:
        model = models.CalendarModel
        fields = (
            'id',
            'name',
            'checked',
            'color',
            'sort',
        )

    def get_checked(self, instance):
        return getattr(instance, 'checked', False)


class CalendarModelShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CalendarModel
        fields = (
            'id',
            'name',
            'code',
            'color',
        )


class CalendarModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CalendarModel
        fields = (
            'id',
            'name',
            'color'
        )

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            request = self.context.get('request')
            if request:
                custom_set = utils.get_custom_set(request)
                personal_calendars = custom_set.personal_calendars
                if isinstance(personal_calendars, str) and personal_calendars == 'all':
                    pass
                elif isinstance(personal_calendars, list):
                    personal_calendars.append(str(instance.pk))
                else:
                    personal_calendars = 'all'
                custom_set.personal_calendars = personal_calendars
                custom_set.save(update_fields=('personal_calendars',))
        return instance


class CalendarModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CalendarModel
        fields = (
            'id',
            'name',
            'color',
        )


class EventCalendarModelNotifySerializer(serializers.ModelSerializer):
    author = AppUserSerializer()

    class Meta:
        model = models.EventCalendarModel
        fields = (
            'id',
            'author',
            'name',
            'end_at',
            'start_at',
            'is_finished',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        timezone_code = self.context.get('timezone_code')
        date = convert_to_local_timezone(instance.start_at, timezone_code=timezone_code)
        data['start_at_humanized'] = (
            f"{date.strftime('%d.%m.%Y %H:%M')} "
            f"{get_humanized_timezone(timezone_code=timezone_code, value=instance.start_at)}"
        )
        return data


class EventCalendarModelListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.EventCalendarModel
        fields = (
            'id',
            'all_day',
            'color',
            'end_at',
            'is_finished',
            'name',
            'start_at',
            'calendar_id',
            'meeting',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['in_favorites'] = get_in_favorites(instance)
        return data


class EventCalendarModelMyDaySerializer(serializers.ModelSerializer):
    related_object = RelatedObjectSerializer(source='calendar.related_object', read_only=True)

    class Meta:
        model = models.EventCalendarModel
        fields = (
            'id',
            'all_day',
            'color',
            'end_at',
            'is_finished',
            # 'name',
            'start_at',
            'related_object',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request:
            profile = request.user.profile
            # Получаем event_member одним запросом
            event_member = instance.event_members.filter(user=profile).first()
            is_member = event_member is not None
            
            # Показываем реальное название или заглушку
            if instance.privacy_id == 'private':
                is_public = is_member
            elif instance.privacy_id == 'public':
                is_public = True
            else:
                is_public = False
        
            data['is_public'] = is_public
            if is_public:
                data['name'] = instance.name
            else:
                data['name'] = _('Событие')
        
            # Кнопки Иду/Не иду
            data['is_member'] = is_member
            if event_member:
                data['is_attending'] = event_member.is_attending
        
        # Сериализуем связанных пользователей (те profile_ids, благодаря которым событие попало в список)
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
                
        return data


class EventCalendarMemberUpdateSerializer(serializers.ModelSerializer):
    is_attending = serializers.BooleanField(allow_null=True, required=True)

    class Meta:
        model = models.EventCalendarMemberModel
        fields = (
            'is_attending',
        )


class EventCalendarModelDetailSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    author = AppUserSerializer()
    calendar = CalendarModelDetailSerializer()
    event_type = BaseCatalogRetrieveSerializer()
    members = serializers.SerializerMethodField()
    meeting = serializers.SerializerMethodField()
    external_meeting_records = serializers.SerializerMethodField()
    privacy = BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.EventCalendarModel
        fields = (
            'id',
            'address',
            'all_day',
            'attachments',
            'author',
            'calendar',
            'color',
            'description',
            'end_at',
            'event_type',
            'is_finished',
            'meeting',
            'external_meeting_records',
            'meeting_url',
            'members',
            'name',
            'notify_at',
            'privacy',
            'start_at',
            'metadata',
            'calendar_id',
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def get_members(self, instance):
        event_members = instance.event_members.all()
        members_data = []
        for event_member in event_members:
            user_data = CachedAppUserSerializer(event_member.user_id).data
            user_data['is_attending'] = event_member.is_attending
            user_data['membership_role'] = event_member.membership_role
            members_data.append(user_data)
        return members_data

    def get_meeting(self, instance):
        from bpms.meetings.serializers import PlannedMeetingListSerializer

        meeting = getattr(instance, 'meeting', None)
        if meeting is None:
            return None
        return PlannedMeetingListSerializer(meeting).data

    def get_external_meeting_records(self, instance):
        from bpms.meetings.serializers import MeetingRecordSerializer

        meeting = getattr(instance, 'meeting', None)
        if meeting is None:
            return []
        records_qs = meeting.records.filter(
            is_active=True,
            is_external=True,
        ).order_by('-created_at')[:1]
        return MeetingRecordSerializer(records_qs, many=True, context=self.context).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['in_favorites'] = get_in_favorites(instance)
        return data


class EventCalendarModelCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True,)
    )
    external_meeting = serializers.BooleanField(required=False, write_only=True)
    external_meeting_url = serializers.URLField(required=False, write_only=True)
    external_meeting_storage_provider = serializers.CharField(required=False, write_only=True)
    external_meeting_record_file = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.filter(is_active=True),
        required=False,
        write_only=True,
    )

    class Meta:
        model = models.EventCalendarModel
        fields = (
            'id',
            'address',
            'all_day',
            'attachments',
            'calendar',
            'color',
            'description',
            'end_at',
            'event_type',
            'meeting',
            'meeting_url',
            'members',
            'external_meeting',
            'external_meeting_url',
            'external_meeting_storage_provider',
            'external_meeting_record_file',
            'name',
            'notify_at',
            'privacy',
            'start_at',
            'metadata',
            'calendar_id',
        )

    def validate_calendar(self, attr):
        if not attr:
            raise drf_exceptions.ValidationError({"message": "Это поле не может быть пустым"})
        request = self.context.get('request')
        if not request:
            return attr
        related_object = attr.related_object
        if related_object:
            original_related_object = related_object.original_object
            if not original_related_object.get_detail_permission(request):
                raise drf_exceptions.PermissionDenied()
        return attr

    def validate(self, attrs):
        attrs = super().validate(attrs)
        external_meeting = attrs.get('external_meeting', False)
        has_external_payload = (
            'external_meeting_url' in attrs or
            'external_meeting_storage_provider' in attrs or
            'external_meeting_record_file' in attrs
        )

        if has_external_payload and not external_meeting:
            raise ValidationError({
                'external_meeting': _('Set this flag to true when passing external meeting fields.')
            })

        if external_meeting:
            has_url = bool(attrs.get('external_meeting_url'))
            has_file = bool(attrs.get('external_meeting_record_file'))
            if has_url and has_file:
                raise ValidationError({
                    'external_meeting_record_file': _('Choose either external URL or uploaded file, not both.')
                })
            if not has_url and not has_file:
                raise ValidationError({'external_meeting_url': _('This field is required.')})
            if has_url and not attrs.get('external_meeting_storage_provider'):
                raise ValidationError({'external_meeting_storage_provider': _('This field is required.')})
        return attrs

    def create(self, validated_data):
        external_meeting = validated_data.pop('external_meeting', False)
        external_meeting_url = validated_data.pop('external_meeting_url', None)
        external_meeting_storage_provider = validated_data.pop('external_meeting_storage_provider', None)
        external_meeting_record_file = validated_data.pop('external_meeting_record_file', None)
        attachments = validated_data.pop('attachments', [])
        members = validated_data.pop('members', [])
        calendar = validated_data.get('calendar', None)
        request = self.context.get('request')
        author = self.context.get('author') or (request and request.user.profile)
        if not author:
            raise drf_exceptions.ValidationError({"message": "Не указан автор"})

        # Если календарь не передан, берем первый по дате создания календарь пользователя (для AI-бота)
        if not calendar:
            calendar = models.CalendarModel.objects.filter(
                author=author,
                related_object__isnull=True,
                is_active=True
            ).order_by('created_at').first()
            validated_data['calendar'] = calendar

        if not validated_data.get('color'):
            validated_data['color'] = calendar.color

        # Если не передано end_at, устанавливаем start_at + 1 час
        if not validated_data.get('end_at') and validated_data.get('start_at'):
            validated_data['end_at'] = validated_data['start_at'] + timedelta(hours=1)

        # Если не передано notify_at, устанавливаем start_at - 30 минут
        if not validated_data.get('notify_at') and validated_data.get('start_at'):
            validated_data['notify_at'] = validated_data['start_at'] - timedelta(minutes=30)

        with transaction.atomic():
            instance = models.EventCalendarModel.objects.create(**validated_data)
            if attachments:
                instance.attachments.set(attachments)

            members_without_author = [member for member in members if member.pk != author.pk]
            models.EventCalendarMemberModel.objects.create(
                user=author,
                event=instance,
                membership_role='author'
            )
            if members_without_author:
                instance.event_members.add(
                    *[models.EventCalendarMemberModel(user=each, event=instance) for each in members_without_author],
                    bulk=False
                )

            if external_meeting:
                utils.create_external_meeting_record_for_event(
                    event=instance,
                    record_url=external_meeting_url,
                    storage_provider=external_meeting_storage_provider,
                    record_file=external_meeting_record_file,
                    request=request,
                )

            if instance.start_at > timezone.now():
                transaction.on_commit(lambda: async_task(notifications.notify_about_new_event, instance))
        return instance


class EventCalendarModelUpdateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    external_meeting = serializers.BooleanField(required=False, write_only=True)
    external_meeting_url = serializers.URLField(required=False, write_only=True)
    external_meeting_storage_provider = serializers.CharField(required=False, write_only=True)
    external_meeting_record_file = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.filter(is_active=True),
        required=False,
        write_only=True,
    )

    class Meta:
        model = models.EventCalendarModel
        fields = (
            'id',
            'address',
            'all_day',
            'attachments',
            'color',
            'description',
            'end_at',
            'event_type',
            'is_finished',
            'meeting',
            'meeting_url',
            'members',
            'external_meeting',
            'external_meeting_url',
            'external_meeting_storage_provider',
            'external_meeting_record_file',
            'name',
            'notify_at',
            'privacy',
            'start_at',
            'metadata',
            'calendar',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        external_meeting = attrs.get('external_meeting', False)
        has_external_payload = (
            'external_meeting_url' in attrs or
            'external_meeting_storage_provider' in attrs or
            'external_meeting_record_file' in attrs
        )

        if has_external_payload and not external_meeting:
            raise ValidationError({
                'external_meeting': _('Set this flag to true when passing external meeting fields.')
            })

        if external_meeting:
            has_url = bool(attrs.get('external_meeting_url'))
            has_file = bool(attrs.get('external_meeting_record_file'))
            if has_url and has_file:
                raise ValidationError({
                    'external_meeting_record_file': _('Choose either external URL or uploaded file, not both.')
                })
            if not has_url and not has_file:
                raise ValidationError({'external_meeting_url': _('This field is required.')})
            if has_url and not attrs.get('external_meeting_storage_provider'):
                raise ValidationError({'external_meeting_storage_provider': _('This field is required.')})
        return attrs

    def update(self, instance, validated_data):
        external_meeting = validated_data.pop('external_meeting', False)
        external_meeting_url = validated_data.pop('external_meeting_url', None)
        external_meeting_storage_provider = validated_data.pop('external_meeting_storage_provider', None)
        external_meeting_record_file = validated_data.pop('external_meeting_record_file', None)
        attachments = validated_data.pop('attachments', None)
        old_members = set(instance.members.all())
        old_start_at = instance.start_at
        members = validated_data.pop('members', None)
        author = instance.author
        with transaction.atomic():
            # Сначала обновляем участников, чтобы к моменту post_save (в super().update) в БД уже был новый состав
            if members is not None:
                new_members_ids = {member.pk for member in members}
                new_members_ids.add(author.pk)
                current_event_members_ids = set(
                    instance.event_members.values_list('user_id', flat=True)
                )
                members_to_remove = current_event_members_ids - new_members_ids
                if members_to_remove:
                    instance.event_members.filter(user_id__in=members_to_remove).delete()
                members_to_add = new_members_ids - current_event_members_ids
                if members_to_add:
                    members_to_add_list = [
                        models.EventCalendarMemberModel(
                            user_id=member_id,
                            event=instance,
                            membership_role='author' if member_id == author.pk else 'member',
                        )
                        for member_id in members_to_add
                    ]
                    instance.event_members.add(*members_to_add_list, bulk=False)
            instance = super().update(instance, validated_data)
            if attachments is not None:
                instance.attachments.set(attachments)
            if external_meeting:
                utils.create_external_meeting_record_for_event(
                    event=instance,
                    record_url=external_meeting_url,
                    storage_provider=external_meeting_storage_provider,
                    record_file=external_meeting_record_file,
                    request=self.context.get('request'),
                )
        now = timezone.now()
        if members and instance.start_at > now:
            new_members = set(members) - old_members
            if new_members:
                async_task(notifications.notify_about_new_event, instance, tuple(new_members))
        if old_start_at != instance.start_at and instance.start_at > now:
            request = self.context.get('request')
            if request:
                user = request.user.profile
                async_task(notifications.notify_about_change_dates, instance, user)
        return instance


class UserEventCalendarListSerializer(serializers.ModelSerializer):
    events = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = ProfileModel
        fields = (
            'id',
            'full_name',
            'avatar',
            'is_support',
            'events',
        )

    def get_avatar(self, instance):
        return {"path": instance.avatar.avatar_url} if instance.avatar else None

    def get_events(self, instance):
        query_params = self.context.get('request').query_params
        import datetime
        plane_date_gte = serializers.DateTimeField().to_internal_value(query_params.get('start'))
        plane_date_lte = serializers.DateTimeField().to_internal_value(query_params.get('end'))
        if not plane_date_gte or not plane_date_lte:
            return []
        gte = plane_date_gte
        day_list = []
        event_calendar_qs = models.EventCalendarModel.objects.filter(
            is_active=True,
            calendar__is_active=True,
            members=instance,
        )
        for each in range(0, (plane_date_lte - plane_date_gte).days + 1):
            lt = gte + datetime.timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
            event_count = event_calendar_qs.filter(
                Q(start_at__gte=gte) | Q(end_at__gte=gte),
                Q(start_at__lte=lt) | Q(end_at__lte=lt),
            ).count()
            day_list.append({'start': gte, 'end': lt, 'count': event_count})
            gte += datetime.timedelta(days=1)
        return day_list


class EventCalendarAccessProfileMetadataModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventCalendarAccessProfileMetadataModel
        fields = (
            'metadata',
        )
