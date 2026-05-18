from uuid import uuid4

from django.db import models, transaction
from django.db.models import Q, F, Value, CharField, OuterRef, Subquery
from django.db.models.functions import Cast, Concat, Coalesce
from django.db.models.expressions import Func
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import datetime
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT, URLS

from common import fields as common_fields
from common.models import BaseAbstractModel, BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel, BaseModel
from common import page_config
from common.page_config.filter_fields import ChoiceFilterField
from common.current_profile.middleware import get_current_authenticated_profile


class MeetingServerModel(BaseCatalog, BaseAbstractCatalog):
    url = common_fields.CustomCharField(max_length=255)
    secret = common_fields.CustomCharField(max_length=255)

    class Meta:
        verbose_name = _("Сервер конференций")
        verbose_name_plural = _("Серверы конференций")


def _get_default_server():
    server, created = MeetingServerModel.objects.get_or_create(code='default', defaults={'name': 'Сервер по умолчанию'})
    return server.code


class IsMyMeetingField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'my_meeting_filter'
    verbose_name = _('Мои собрания')
    default = None
    blank = True

    def get_my_meetings(self):
        user = get_current_authenticated_profile()
        return MeetingMemberModel.objects.filter(
            is_active=True,
            user=user,
        ).values_list('meeting_id', flat=True)

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(pk__in=self.get_my_meetings())
        else:
            return queryset.exclude(pk__in=self.get_my_meetings())

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(pk__in=self.get_my_meetings())
        else:
            return queryset.filter(pk__in=self.get_my_meetings())


class MemberFakeField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Участник")
    name = 'member_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def get_meetings(self, value):
        return MeetingMemberModel.objects.filter(
            user__in=value.get('value'),
            is_active=True,
        ).values_list('meeting_id', flat=True)

    def to_filter(self, queryset, value):
        queryset = queryset.filter(pk__in=self.get_meetings(value))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(pk__in=self.get_meetings(value))
        return queryset


class PlannedMeetingModel(BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel):
    meta_exclude_fields = ['code', 'mentions', 'ct', 
                            'members', 'attendeePW', 'moderatorPW', 'server', 'is_external', 'is_fast',
                            'invite_link',
                            ]

    STATUS_CHOICES = (
        ('new', _('Новый')),
        ('online', _('Онлайн')),
        ('ended', _('Завершен')),
        )
    members = models.ManyToManyField('users.ProfileModel',
                                     through='MeetingMemberModel',
                                     verbose_name=_('Участники'),
                                     through_fields=('meeting', 'user')
                                     )
    description = models.TextField(
        null=False,
        blank=True,
        default="",
        verbose_name=_("Описание"),
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=True,
        verbose_name='Связанный объект',
        on_delete=CUSTOM_CASCADE,
        related_name='meetings'
    )
    project = common_fields.CustomForeignKey(
        to='workgroups.WorkgroupModel',
        null=True,
        blank=True,
        verbose_name=_('Проект'),
        on_delete=CUSTOM_SET_NULL,
        related_name='planned_meetings',
    )
    status = common_fields.CustomCharField(
        choices=STATUS_CHOICES,
        max_length=10,
        null=False,
        default='new',
        verbose_name=_("Статус"),
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'}
    )
    attendeePW = models.UUIDField(default=uuid4,
                                  verbose_name=_('attendeer_PW'),
                                  editable=False)
    moderatorPW = models.UUIDField(default=uuid4,
                                   verbose_name=_('moderatorPW'),
                                   editable=False)
    date_begin = common_fields.CustomDateTimeField(null=True,
                                                   blank=False,
                                                   verbose_name=_('Время начала'))
    duration = common_fields.CustomPositiveIntegerField(null=False,
                                                        blank=True,
                                                        default=0,
                                                        verbose_name=_('Продолжительность (мин)'))
    server = common_fields.CustomForeignKey(
        to='meetings.MeetingServerModel',
        to_field='code',
        default=_get_default_server,
        null=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Сервер'))
    invite_link = models.UUIDField(default=uuid4,
                                   verbose_name=_('Ссылка для приглашения'),
                                   editable=False)

    has_record = common_fields.CustomBooleanField(default=False,
                                                  verbose_name=_('Есть запись'))
    is_external = common_fields.CustomBooleanField(
        default=False,
        verbose_name='External meeting'
    )
    is_fast = common_fields.CustomBooleanField(
        default=False,
        help_text='Создано бабкой') # имеется ввиду телеграм бот @babka_bdit_bot, созданный @pribka

    member_filter = MemberFakeField()
    my_meeting_filter = IsMyMeetingField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Запланированная конференция")
        verbose_name_plural = _("Запланированные конференции")

    @classmethod
    def get_table_columns(cls):
        return ['name', 'author', 'status', 'date_begin', 'has_record', 'member_filter',
                'my_meeting_filter', 'project',]

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            PlannedMeetingListSerializer,
            PlannedMeetingCreateSerializer,
            PlannedMeetingDetailSerializer,
            PlannedMeetingUpdateSerializer,
        )
        if action == 'create':
            return PlannedMeetingCreateSerializer
        if action == 'retrieve':
            return PlannedMeetingDetailSerializer
        if action in ('update', 'partial_update'):
            return PlannedMeetingUpdateSerializer
        return PlannedMeetingListSerializer

    @classmethod
    def search_input(cls):
        return True

    def get_connect_info(self):
        """Возвращает словарь с URL-ами подключения и статусом встречи."""
        from .utils import get_connect_meeting_url, get_invite_link
        return {
            "id": str(self.id),
            "url_external": get_invite_link(self.invite_link),
            "url": get_connect_meeting_url(self.id),
            "status": self.status
        }

    def get_detail_permission(self, request) -> bool:
        return self.members.filter(pk=request.user.profile.pk).exists()

    def get_update_permission(self, request) -> bool:
        return self.author == request.user.profile

    def set_is_active(self, value: bool, request):
        from rest_framework import exceptions as drf_exceptions
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False:
                self.deleted_at = timezone.now()
                self.calendar_events.update(meeting=None)
            else:
                self.deleted_at = None
            self.is_active = value
            # сохранение self делает вызывающий код (например BaseModelActionsViewSet.update_is_active)

    @classmethod
    def get_queryset(cls, request=None):
        queryset = cls.objects.filter(
            is_active=True,
            calls__isnull=True,
        )
        if not request:
            return queryset
        user = request.user.profile
        return queryset.filter(
            Q(members=user) | Q(author=user),
        ).distinct()

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        """Возвращает SQL-аннотации вычисляемых полей для отчетов по встречам."""
        annotations = {}
        names = set(requested_computed or [])
        outer_ref_column = kwargs.get('outer_ref_column')

        if {'organization', 'root_organization'} & names:
            from common.catalogs.models import ContractorRelationModel
            organization_pk_field = cls._meta.get_field('project').related_model._meta.get_field('organization').target_field

            if 'organization' in names:
                if outer_ref_column:
                    meeting_organization_subquery = cls.objects.filter(
                        pk=OuterRef(outer_ref_column),
                    ).values('project__organization_id')[:1]
                    annotations['organization'] = Subquery(
                        meeting_organization_subquery,
                        output_field=organization_pk_field,
                    )
                else:
                    annotations['organization'] = F('project__organization_id')

            if 'root_organization' in names:
                if outer_ref_column:
                    root_organization_subquery = ContractorRelationModel.objects.filter(
                        contractor_id=OuterRef('project__organization_id'),
                        relation_type_id='structural_division',
                        is_active=True,
                    ).values('contractor_root_id')[:1]
                    meeting_root_subquery = cls.objects.filter(
                        pk=OuterRef(outer_ref_column),
                    ).annotate(
                        resolved_root_organization=Coalesce(
                            Subquery(root_organization_subquery),
                            F('project__organization_id'),
                            output_field=organization_pk_field,
                        )
                    ).values('resolved_root_organization')[:1]
                    annotations['root_organization'] = Subquery(
                        meeting_root_subquery,
                        output_field=organization_pk_field,
                    )
                else:
                    root_organization_subquery = ContractorRelationModel.objects.filter(
                        contractor_id=OuterRef('project__organization_id'),
                        relation_type_id='structural_division',
                        is_active=True,
                    ).values('contractor_root_id')[:1]
                    annotations['root_organization'] = Coalesce(
                        Subquery(root_organization_subquery),
                        F('project__organization_id'),
                        output_field=organization_pk_field,
                    )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        """Метаданные вычисляемых полей для отчетов по встречам."""
        return [
            {
                "name": "organization",
                "type": "ForeignKey",
                "related_model": "catalogs.ContractorModel",
                "verbose_name": _("Организация"),
            },
            {
                "name": "root_organization",
                "type": "ForeignKey",
                "related_model": "catalogs.ContractorModel",
                "verbose_name": _("Головная организация"),
            },
        ]


class CallModel(BaseModel):
    ACTIVE_STATUSES = ('connecting', 'ringing', 'in_call')

    ticket = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='calls',
        verbose_name=_('Обращение'),
    )
    chat = common_fields.CustomForeignKey(
        to='chat.ChatModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='calls',
        verbose_name=_('Чат'),
    )
    meeting = common_fields.CustomForeignKey(
        to='meetings.PlannedMeetingModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='calls',
        verbose_name=_('Встреча'),
    )
    status = common_fields.CustomForeignKey(
        to='meetings.CallStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='connecting',
        on_delete=CUSTOM_PROTECT,
        related_name='calls',
        verbose_name=_('Статус звонка'),
    )
    initiator = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=False,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='initiated_calls',
        verbose_name=_('Инициатор'),
    )
    accepted_by = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='accepted_calls',
        verbose_name=_('Принял звонок'),
    )
    current_target = models.ManyToManyField(
        to='users.ProfileModel',
        blank=True,
        related_name='targeted_calls',
        verbose_name=_('Текущие целевые участники'),
    )
    ring_attempt = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Попытка дозвона'),
    )
    ring_started_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Начало текущего дозвона'),
    )
    started_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время начала'),
    )
    answered_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время ответа'),
    )
    ended_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время завершения'),
    )

    class Meta:
        verbose_name = _('Звонок')
        verbose_name_plural = _('Звонки')
        ordering = ('-created_at',)

    @property
    def chat_uid(self):
        if self.chat_id and self.chat:
            return self.chat.chat_uid
        return None

    def get_detail_permission(self, request) -> bool:
        ticket = self.ticket
        if ticket is not None and hasattr(ticket, 'get_detail_permission'):
            return ticket.get_detail_permission(request)
        if self.initiator_id == request.user.profile.pk:
            return True
        if self.accepted_by_id == request.user.profile.pk:
            return True
        if self.current_target.filter(pk=request.user.profile.pk).exists():
            return True
        if self.chat and self.chat.members.filter(is_active=True, user=request.user.profile).exists():
            return True
        return False

    def get_update_permission(self, request) -> bool:
        return self.get_detail_permission(request)

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return cls.objects.filter(is_active=True)
        profile = request.user.profile
        return cls.objects.filter(
            is_active=True,
        ).filter(
            Q(initiator_id=profile.pk) |
            Q(accepted_by_id=profile.pk) |
            Q(current_target=profile.pk)
        ).distinct().order_by('-created_at')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            CallListSerializer,
            CallNotifySerializer,
        )
        if action == 'notify':
            return CallNotifySerializer
        return CallListSerializer


class CallStatusModel(BaseCatalog, BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'created_at', 'mentions', 'ct']

    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )


    class Meta:
        verbose_name = _('Статус звонка')
        verbose_name_plural = _('Статусы звонков')


class MeetingRecordsModel(BaseCatalog, BaseAbstractCatalog):
    """Модель для хранения видеозаписи собраний."""
    STATUS_CHOICES = (
        ('new', _('Новая')),
        ('processing', _('В процессе')),
        ('done', _('Готова')),
        ('error', _('Ошибка')),
        )
    STORAGE_PROVIDER_CHOICES = (
        ('google_drive', 'Google Drive'),
        ('nextcloud', 'Nextcloud'),
    )
    meeting = models.ForeignKey(PlannedMeetingModel,
                                related_name='records',
                                on_delete=CUSTOM_CASCADE)
    section = models.ForeignKey(
        to='meetings.MeetingSectionModel',
        on_delete=CUSTOM_CASCADE,
        related_name='records',
        null=True,
        blank=True,
        )
    is_external = common_fields.CustomBooleanField(
        default=False,
        verbose_name='External record',
    )
    storage_provider = common_fields.CustomCharField(
        max_length=32,
        null=False,
        blank=True,
        default='',
        choices=STORAGE_PROVIDER_CHOICES,
        verbose_name='Storage provider',
    )
    url = models.CharField(max_length=255,
                           default='',
                           unique=True)
    initial_data = models.JSONField()

    record_file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_SET_NULL,
        verbose_name='Файл записи',
        null=True,
        blank=True,
    )
    own_file = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Использовать загруженный файл',
    )
    status = common_fields.CustomCharField(
        choices=STATUS_CHOICES,
        max_length=10,
        null=False,
        default='new',
        verbose_name='Статус транскрибации',
    )
    transcribe = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Транскрибация',
    )
    transcribe_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Транскрибация в виде json',
        )
    summary = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Краткое содержание',
    )
    summary_old = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Старое краткое содержание (для сравнения до/после)',
    )
    efficiency = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Эффективность использования времени',
    )
    is_summary_notified = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Уведомление о готовности краткого содержания отправлено',
    )
    is_summary_ready = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Краткое содержание готово'
        )
    is_intents_ready = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Извлечение намерений проведено'
        )
    is_efficiency_ready = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Анализ эффективности проведен'
        )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            MeetingRecordSerializer,
            MeetingRecordUntranscribedSerializer,
            MeetingRecordDetailSerializer
        )
        if action == 'untranscribed':
            return MeetingRecordUntranscribedSerializer
        elif action == 'list':
            return MeetingRecordSerializer
        elif action == 'retrieve':
            return MeetingRecordDetailSerializer
        return MeetingRecordSerializer

    def get_detail_permission(self, request) -> bool:
        if self.section_id and self.section and self.section.get_detail_permission(request):
            return True
        if self.meeting_id and self.meeting and self.meeting.get_detail_permission(request):
            return True
        return False


class MeetingMemberModel(BaseAbstractModel):
    meeting = models.ForeignKey(PlannedMeetingModel,
                                on_delete=CUSTOM_CASCADE)
    user = models.ForeignKey('users.ProfileModel',
                             on_delete=CUSTOM_CASCADE, related_name='meeting_member')
    is_moderator = models.BooleanField(verbose_name=_('Модератор конференции'),
                                       default=False,
                                       )

    # def save(self, *args, **kwargs):
    #     from .tasks import send_notify_about_meeting_invite
    #     if not self.pk and not self.user.id == self.meeting.author.id:
    #         send_notify_about_meeting_invite(self.meeting.id, self.meeting.author.id, self.user)
    #     super().save(*args, *kwargs) #TODO

    class Meta:
        unique_together = (('meeting', 'user'),)
        verbose_name = _("Участник конференции")
        verbose_name_plural = _("Участники конференции")


class MeetingSectionModel(BaseAbstractModel):
    """Модель секции собрания. Секция - временной отрезок от начала до завершения."""
    meta_exclude_fields = ['author', 'created_at', 'last_check_member_time', 'visors',
                            'execution_time_project']

    # Переопределение verbose_name чтобы не делать миграцию
    field_verbose_names = {'meeting': _('Встреча'), }

    STATUS_CHOICES = (
        ('online', _('Онлайн')),
        ('ended', _('Завершен')),
    )
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Название')
    )
    meeting = models.ForeignKey(PlannedMeetingModel,
                                related_name='meeting_sections',
                                on_delete=CUSTOM_CASCADE)
    status = common_fields.CustomCharField(
        choices=STATUS_CHOICES,
        max_length=10,
        null=False,
        default='online',
        verbose_name=_("Статус"),
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'}
    )
    date_start = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала'),
    )
    date_end = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания'),
    )
    duration = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_('Продолжительность')
    )
    members = models.ManyToManyField(
        'users.ProfileModel',
        through='MeetingSectionMemberModel',
        verbose_name=_('Участники'),
        through_fields=('section', 'user'),
        related_name='meeting_sections',
        )
    last_check_member_time = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время последней проверки состава участников'),
    )
    visors = models.ManyToManyField(
        to='users.ProfileModel',
        through='meetings.MeetingSectionVisorsModel',
        through_fields=('section', 'user'),
        related_name='visor_sections',
        verbose_name=_('Наблюдатели'),
    )
    execution_time_project = common_fields.CustomForeignKey(
        to='workgroups.WorkgroupModel',
        null=True,
        blank=True,
        verbose_name=_('Проект трудозатрат'),
        on_delete=CUSTOM_SET_NULL,
        related_name='meeting_sections',
    )

    class Meta:
        verbose_name = _("Секция конференции")
        verbose_name_plural = _("Секции конференций")

    @classmethod
    def get_queryset(cls, request=None):
        queryset = cls.objects.filter(is_active=True)
        if request:
            user = request.user.profile
            lookup = Q(members=user)
            lookup = lookup | Q(meeting__members=user)
            lookup = lookup | Q(visors=user)
            from contractor_permissions.utils import contractors_where_user_has_permission
            supervisor_orgs = contractors_where_user_has_permission(user.pk, 'tasks_supervisor', None)
            if supervisor_orgs:
                lookup = lookup | Q(meeting__author__current_contractor_id__in=supervisor_orgs)
            
            queryset = queryset.filter(lookup).distinct()
        return queryset

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MeetingSectionListSerializer, MeetingSectionDetailSerializer
        if action == 'retrieve':
            return MeetingSectionDetailSerializer
        return MeetingSectionListSerializer

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        
        if self.members.filter(pk=user.pk).exists():
            return True
        
        if self.meeting.members.filter(pk=user.pk).exists():
            return True
        
        if self.visors.filter(pk=user.pk).exists():
            return True
        
        if self.meeting.author.current_contractor_id:
            from contractor_permissions.utils import check_contractor_permission
            from rest_framework import exceptions as drf_exceptions
            try:
                check_contractor_permission(user.pk, self.meeting.author.current_contractor_id, 'tasks_supervisor', None)
                return True
            except drf_exceptions.PermissionDenied:
                pass
        
        return False

    def get_update_permission(self, request) -> bool:
        return self.meeting.get_update_permission(request)

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        """Возвращает SQL-аннотации вычисляемых полей для отчетов по сессиям встреч."""
        annotations = {}
        names = set(requested_computed or [])

        if 'meeting_link' in names:
            meeting_base_url = URLS['frontend_url']
            meeting_url_expr = Concat(
                Value(meeting_base_url),
                Value('?meeting='),
                Cast(F('meeting_id'), CharField()),
            )
            annotations['meeting_link'] = Func(
                Value('repr'),
                Coalesce(F('meeting__name'), Value('')),
                Value('url'),
                meeting_url_expr,
                function='jsonb_build_object',
                output_field=models.JSONField(),
            )

        if 'session_link' in names:
            session_base_url = URLS['meetings']
            session_url_expr = Concat(
                Value(session_base_url),
                Value('?meeting='),
                Cast(F('meeting_id'), CharField()),
                Value('&meettab=session'),
            )
            annotations['session_link'] = Func(
                Value('repr'),
                Coalesce(F('name'), Value('')),
                Value('url'),
                session_url_expr,
                function='jsonb_build_object',
                output_field=models.JSONField(),
            )

        if 'participants' in names:
            participants_subquery = MeetingSectionMemberModel.objects.filter(
                is_active=True,
                section_id=OuterRef('pk'),
            ).values('section_id').annotate(
                participants_value=StringAgg(
                    Func(
                        Concat(
                            Coalesce(F('user__user__last_name'), Value('')),
                            Value(' '),
                            Coalesce(F('user__user__first_name'), Value('')),
                            Value(' '),
                            Coalesce(F('user__user__middle_name'), Value('')),
                        ),
                        function='BTRIM',
                        output_field=CharField(),
                    ),
                    delimiter=', ',
                    distinct=True,
                )
            ).values('participants_value')[:1]
            annotations['participants'] = Coalesce(
                Subquery(participants_subquery, output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        """Метаданные вычисляемых полей для отчетов по сессиям встреч."""
        return [
            {
                "name": "meeting_link",
                "type": "JSONField",
                "verbose_name": _("Ссылка на встречу"),
                "order_by_field": "meeting__name",
            },
            {
                "name": "session_link",
                "type": "JSONField",
                "verbose_name": _("Ссылка на сессию"),
                "order_by_field": "name",
            },
            {
                "name": "participants",
                "type": "CharField",
                "verbose_name": _("Список участников"),
            },
        ]


class MeetingSectionMemberModel(BaseAbstractModel):
    """Модель, которая хранит продолжительность присутствия пользователей на секциях конференции."""
    section = models.ForeignKey(
        MeetingSectionModel,
        on_delete=CUSTOM_CASCADE,
        related_name='meeting_section_members',
        )
    user = models.ForeignKey('users.ProfileModel',
                             on_delete=CUSTOM_CASCADE,
                             related_name='meeting_section_members',)
    duration = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_('Продолжительность')
    )
    is_execution_time_created = models.BooleanField(
        default=False,
        verbose_name=_('Трудозатраты созданы'),
    )
    last_check_member_time = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время последней проверки состава участников'),
    )

    class Meta:
        unique_together = (('section', 'user'),)
        verbose_name = _("Участник секции конференции")
        verbose_name_plural = _("Участники секций конференции")


class MeetingSectionVisorsModel(BaseAbstractModel):
    section = common_fields.CustomForeignKey(
        to='meetings.MeetingSectionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='section_visors_through',
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='section_visors_through',
    )

    class Meta:
        verbose_name = _('Наблюдатель секции собрания')
        verbose_name_plural = _('Наблюдатели секций собрания')
        unique_together = (('section', 'user'),)
