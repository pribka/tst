from django.db import models, transaction
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import datetime
from django.utils.translation import gettext as _
from django.core.validators import MinValueValidator

from rest_framework import exceptions as drf_exceptions

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from common.models import BaseCatalog, BaseAbstractCatalog, BaseModel, MetadataAbstractModel, BaseAbstractModel
from common import fields as common_fields

from bpms.favorites.fields import InFavoritesFilterField
from bpms.favorites.models import FavoriteModel


class CalendarGroupModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        max_length=100,
        null=False,
        blank=True,
        default='',
        verbose_name='Цвет'
    )

    class Meta:
        verbose_name = 'Группа календарей'
        verbose_name_plural = 'Группы календарей'


class ExternalCalendarModel(BaseCatalog, BaseAbstractCatalog):
    GOOGLE = 'GOOGLE_CALENDAR'

    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = 'Внешний календарь'
        verbose_name_plural = 'Внешние календари'


class CalendarModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        max_length=100,
        null=False,
        blank=True,
        default='',
        verbose_name='Цвет'
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=True,
        verbose_name='Связанный объект',
        on_delete=CUSTOM_CASCADE,
        related_name='event_calendars'
    )
    calendar_group = common_fields.CustomForeignKey(
        to='event_calendar.CalendarGroupModel',
        to_field='code',
        null=True,
        blank=True,
        verbose_name='Группа календарей',
        on_delete=CUSTOM_PROTECT,
        related_name='calendars',
    )

    external_calendar_type = common_fields.CustomForeignKey(
        to='event_calendar.ExternalCalendarModel',
        to_field='code',
        null=True,
        blank=True,
        verbose_name='Тип внешнего календаря',
        on_delete=CUSTOM_PROTECT,
        related_name='external_calendars',
    )
    synchronize = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Синхронизировать'
    )
    external_calendar_id = common_fields.CustomCharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name="ID внешнего календаря",
    )
    # https://developers.google.com/calendar/api/guides/sync
    external_calendar_next_sync_token = models.TextField(
        blank=True,
        default='',
        verbose_name='Токен синхронизации',
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import CalendarModelCreateSerializer, CalendarModelListSerializer, \
            CalendarModelUpdateSerializer
        if action:
            if action == 'list':
                return CalendarModelListSerializer
            elif action == 'create':
                return CalendarModelCreateSerializer
            elif action in ('update', 'partial_update'):
                return CalendarModelUpdateSerializer
            elif action == 'retrieve':
                return CalendarModelListSerializer
            else:
                return CalendarModelListSerializer
        return CalendarModelListSerializer

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if not user:
            return False
        if self.author == user:
            return True
        related_object = self.related_object
        if related_object:
            original_related_object = related_object.original_object  # noqa
            if original_related_object.get_update_permission(request):
                return True
        return False

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        if not user:
            return False
        if self.author == user:
            return True
        related_object = self.related_object
        if related_object:
            original_related_object = related_object.original_object  # noqa
            if original_related_object.get_detail_permission(request):
                return True
        return False

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        return qs

    @classmethod
    def get_select_queryset(cls, request=None):
        if not request:
            return cls.objects.none()
        qs = cls.objects.filter(is_active=True)
        user = request.user.profile

        qs = qs.filter(
            Q(author=user, related_object__isnull=True) |
            Q(
                related_object__is_active=True,
                related_object__workgroupmodel__is_finished=False,
                related_object__workgroupmodel__is_project=True,
                related_object__workgroupmodel__isnull=False,
                related_object__workgroupmodel__workgroupmembersmodel__member=user,
                related_object__workgroupmodel__workgroupmembersmodel__membership_request_status__code='APPROVED',
                related_object__workgroupmodel__workgroupmembersmodel__membership_role__code__in=('MODERATOR', 'FOUNDER')
            )
        ).select_related("related_object__workgroupmodel").annotate(
            private_order=models.Case(
                models.When(
                    related_object__isnull=True,
                    then=models.Value(0)
                ),
                default=models.Value(1),
                output_field=models.IntegerField(),
            )
        ).order_by('private_order', 'name',)
        return qs

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        qs = cls.get_select_queryset(request).filter(
            Q(name__icontains=text) | Q(related_object__workgroupmodel__name__icontains=text)
        )
        return qs

    def __str__(self):
        result = super().__str__()
        if self.calendar_group_id == 'groups_projects':
            try:
                result = f"Проект \"{self.related_object.workgroupmodel.name}\""
            except models.ObjectDoesNotExist:
                pass
        return result


    class Meta:
        verbose_name = 'Календарь событий'
        verbose_name_plural = 'Календари событий'

    def set_is_active(self, value: bool, request):
        if self.related_object:
            raise drf_exceptions.PermissionDenied()
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value:
            self.deleted_at = None
        else:
            self.deleted_at = timezone.now()
        self.is_active = value
        self.save(update_fields=('is_active', 'deleted_at',))


class EventCalendarTypeModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = 'Тип события'
        verbose_name_plural = 'Типы событий'


class EventCalendarPrivacyModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = 'Приватность события'
        verbose_name_plural = 'Приватности события'


class EventCalendarModel(BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel):
    calendar = common_fields.CustomForeignKey(
        to='event_calendar.CalendarModel',
        null=True,
        blank=False,
        verbose_name='Календарь событий',
        related_name='events',
        on_delete=CUSTOM_PROTECT,
    )
    event_type = common_fields.CustomForeignKey(
        to='event_calendar.EventCalendarTypeModel',
        to_field='code',
        default='other',
        null=True,
        blank=False,
        verbose_name='Тип события',
        related_name='events',

        on_delete=CUSTOM_PROTECT
    )

    privacy = common_fields.CustomForeignKey(
        to='event_calendar.EventCalendarPrivacyModel',
        to_field='code',
        blank=True,
        null=False,
        default='private',
        verbose_name='Тип приватности',
        on_delete=CUSTOM_PROTECT
    )

    members = models.ManyToManyField(
        'users.ProfileModel',
        through='event_calendar.EventCalendarMemberModel',
        verbose_name='Участники',
        through_fields=('event', 'user')
    )
    color = common_fields.CustomCharField(
        max_length=100,
        null=False,
        blank=True,
        default='',
        verbose_name='Цвет'
    )
    start_at = common_fields.CustomDateTimeField(
        null=False,
        blank=False,
        default=timezone.now,
        verbose_name='Дата начала',
    )
    end_at = common_fields.CustomDateTimeField(
        null=False,
        blank=False,
        default=timezone.now,
        verbose_name='Дата окончания',
    )
    notify_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата уведомления'
    )
    address = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name='Адрес',
    )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Описание'
    )

    meeting_url = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name='Ссылка на встречу',
    )
    all_day = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Весь день',
    )
    is_finished = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Закончено',
    )
    is_notified = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Автор уведомлён',
    )
    external_calendar_event_id = common_fields.CustomCharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name="ID события внешнего календаря",
    )
    synchronized = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Синхронизировано с событием внешнего календаря',
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')
    in_favorites_filter = InFavoritesFilterField()

    meeting = common_fields.CustomForeignKey(
        'meetings.PlannedMeetingModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='calendar_events',
        verbose_name='Собрание',
    )

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value:
            self.deleted_at = None
        else:
            self.deleted_at = timezone.now()
        self.is_active = value
        if not value and self.meeting_id:
            meeting = self.meeting
            has_other_active_events = EventCalendarModel.objects.filter(
                is_active=True,
                meeting_id=self.meeting_id,
            ).exclude(pk=self.pk).exists()
            if not has_other_active_events and meeting and meeting.is_active:
                meeting.is_active = False
                meeting.deleted_at = timezone.now()
                meeting.save(update_fields=('is_active', 'deleted_at'))
        # сохранение self делает вызывающий код (например BaseModelActionsViewSet.update_is_active)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EventCalendarModelCreateSerializer, EventCalendarModelListSerializer, \
            EventCalendarModelUpdateSerializer, EventCalendarModelDetailSerializer, EventCalendarModelNotifySerializer
        if action:
            if action == 'create':
                return EventCalendarModelCreateSerializer
            elif action in ('update', 'partial_update',):
                return EventCalendarModelUpdateSerializer
            elif action == 'retrieve':
                return EventCalendarModelDetailSerializer
            elif action == 'notify':
                return EventCalendarModelNotifySerializer
            else:
                return EventCalendarModelListSerializer
        else:
            return EventCalendarModelListSerializer

    def get_detail_permission(self, request) -> bool:
        if self.calendar.get_detail_permission(request):
            return True
        user = request.user.profile
        if self.author == user or self.members.filter(pk=user.pk).exists():
            return True
        return False

    def get_update_permission(self, request) -> bool:
        # События календаря, привязанного к задаче, не редактируются через API (логика в задаче).
        if self.calendar.related_object_id:
            ct = ContentType.objects.get_for_model(self.calendar.related_object.original_object)
            if ct.app_label == 'tasks' and ct.model == 'taskmodel':
                return False
        if self.calendar.get_update_permission(request):
            return True
        return self.author_id == request.user.profile.pk

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True, calendar__is_active=True)
        if not request:
            return qs.none()
        user = request.user.profile
        qs = qs.filter(Q(calendar__author=user) | Q(members=user) | Q(author=user)).distinct()
        qs = FavoriteModel.annotate_favorites(qs)
        return qs

    @classmethod
    def get_table_columns(cls):
        return ['in_favorites_filter', ]


class EventCalendarMemberModel(BaseAbstractModel):

    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Пользователь', related_name='event_members'  # related_name='tmp1111',

    )
    event = common_fields.CustomForeignKey(
        to='event_calendar.EventCalendarModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE, related_name='event_members',  # related_name='tmp11112',
        verbose_name='Событие',

    )

    is_notified = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Уведомлен',
    )

    is_attending = common_fields.CustomBooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_('Иду'),
    )
    MEMBERSHIP_ROLE_CHOICES = [
        ('author', _('Организатор')),
        ('member', _('Участник')),
    ]
    membership_role = common_fields.CustomCharField(
        max_length=20,
        blank=True,
        null=True,
        choices=MEMBERSHIP_ROLE_CHOICES,
        default='member',
        verbose_name=_("Роль участника рабочей группы"),
    )

    class Meta:
        verbose_name = 'Участник события'
        verbose_name_plural = 'Участники события'
        unique_together = (('user', 'event',),)


class CalendarCustomSetModel(BaseModel):
    personal_calendars = models.JSONField(
        null=False,
        blank=True,
        default=list,
    )
    group_calendars = models.JSONField(
        null=False,
        blank=True,
        default=list,
    )
    page_name = models.CharField(default='',
                                 max_length=255,
                                 verbose_name='Страница, для которой указываем список календарей')

    class Meta:
        verbose_name = 'Кастомный набор календарей'
        verbose_name_plural = 'Кастомные наборы календарей'


class EventCalendarAccessOrganizationModel(BaseAbstractModel):
    owner = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='event_calendar_access_org',
        verbose_name=_('Профиль хозяина'),
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='event_calendar_access_org',
        verbose_name=_('Организация'),
        help_text='Контрагент'
    )

    class Meta:
        verbose_name = _('Доступ организации к календарю')
        verbose_name_plural = _('Доступы организаций к календарю')
        ordering = ('-created_at',)
        unique_together = (('owner', 'organization'),)


class EventCalendarAccessProfileModel(BaseAbstractModel):
    owner = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='event_calendar_access_profiles',
        verbose_name=_('Профиль пользователя'),
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='event_calendar_access_owners',
        verbose_name=_('Пользователь, которому открывается доступ'),
    )

    class Meta:
        verbose_name = _('Доступ профиля к календарю')
        verbose_name_plural = _('Доступы профилей к календарю')
        ordering = ('-created_at',)
        unique_together = (('owner', 'user'),)


class EventCalendarAccessProfileMetadataModel(MetadataAbstractModel):
    user = models.OneToOneField(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='event_calendar_access_metadata'
    )

    class Meta:
        verbose_name = 'Метадата для доступа профиля'
        verbose_name_plural = 'Метадаты для доступа профиля'

    def __str__(self):
        return f"{self.user.user.last_name} {self.user.user.first_name} {self.user.user.email}"

