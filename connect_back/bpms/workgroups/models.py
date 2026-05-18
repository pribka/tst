import json
import datetime
from django.utils import timezone
import decimal

# from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest, ValidationError
from django.db import models, transaction
from django.db.models import Count, Q, Max, Value, Subquery, OuterRef, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from mptt.models import MPTTModel, TreeForeignKey

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions as drf_exceptions
from rest_framework.serializers import DateTimeField

from bkz3.settings import (
    CUSTOM_CASCADE,
    CUSTOM_DO_NOTHING,
    CUSTOM_PROTECT,
    CUSTOM_SET_NULL,
    FILTER_BY_ORGANIZATIONS,
    SOCKETIO_SYSTEM_CHANNEL,
    TASK_DATES_CONTROL,
)
from model_utils import FieldTracker
from bpms.bpms_common.models import SocialURLs
from bpms.chat.models import ChatModel

from common import fields as common_fields
from common import page_config
from common.current_profile.middleware import get_current_authenticated_profile
from common.models import (
    BaseAbstractCatalog,
    BaseAbstractModel,
    BaseCatalog,
    BaseModel,
    File,
    MetadataAbstractModel,
)
from common.redis import socketio_redis
from common.accounting_catalogs.fields import LocationFilterFakeField
from common.catalogs.models import get_default_currency

from bpms.favorites.fields import InFavoritesFilterField
from change_history import utils as change_history_utils

# from users.models import CustomUser, ProfileModel  # noqa: F401


class WorkgroupTypes(BaseCatalog):
    code = models.CharField(
        max_length=100,
        blank=True,
        default='default'
    )
    class Meta:
        verbose_name = _("Тип рабочей группы")
        verbose_name_plural = _("Типы рабочей группы")


class WorkgroupStatus(BaseCatalog):
    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Статус рабочей группы")
        verbose_name_plural = _("Статусы рабочей группы")


class WorkgroupMembershipStatus(BaseCatalog):
    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Статус участника рабочей группы")
        verbose_name_plural = _("Статусы участника рабочей группы")


class WorkgroupMembershipRole(BaseCatalog):
    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Роль участника рабочей группы")
        verbose_name_plural = _("Роли участника рабочей группы")

    def __str__(self):
        return str(self.code)


class IsMyWorkgroupField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'my_workgroup_filter'
    verbose_name = _('Мои команды')
    default = None
    blank = True

    def get_my_workgroups(self):
        user = get_current_authenticated_profile()
        return WorkgroupMembersModel.objects.filter(
            member=user,
            is_active=True,
            membership_request_status__code='APPROVED',
            membership_role__code='FOUNDER',
        ).values_list('work_group_id', flat=True)

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(pk__in=self.get_my_workgroups())
        else:
            return queryset.exclude(pk__in=self.get_my_workgroups())

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(pk__in=self.get_my_workgroups())
        else:
            return queryset.filter(pk__in=self.get_my_workgroups())


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

    def get_workgroups(self, value):
        return WorkgroupMembersModel.objects.filter(
            member__in=value.get('value'),
            is_active=True,
            membership_request_status__code='APPROVED',
        ).values_list('work_group_id', flat=True)

    def to_filter(self, queryset, value):
        queryset = queryset.filter(pk__in=self.get_workgroups(value))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(pk__in=self.get_workgroups(value))
        return queryset


class WorkgroupModel(BaseModel, MetadataAbstractModel):
    meta_exclude_fields = [
        'author', 'workgroup_logo', 'workgroup_type', 'program', 'counterparty', 'costing_object', 'location',
        'funds', 'funds_currency', 'social_links', 'gallery_files', 'control_dates',
        'is_helpdesk', 'with_chat', 'linked_chat', 'is_overdue', 'is_demo', 'created_at', 'mentions', 'ct',
        'external_id', 'work_directions', ]

    class Meta:
        verbose_name = _("Рабочая группа")
        verbose_name_plural = _("Рабочие группы")

    external_id = common_fields.CustomCharField(
        max_length=36,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Внешний ID'),
    )

    name = common_fields.CustomCharField(
        default="",
        verbose_name=_("Название"),
        max_length=255,
    )
    workgroup_logo = models.ForeignKey(
        File,
        blank=True,
        null=True,
        on_delete=CUSTOM_DO_NOTHING,
        verbose_name=_("Логотип")
    )
    description = models.TextField(
        null=False,
        default="",
        blank=True,
        verbose_name=_("Описание")
    )
    workgroup_type = models.ForeignKey(
        WorkgroupTypes,
        blank=True,
        null=True,
        on_delete=CUSTOM_DO_NOTHING,
        verbose_name=_("Тип")
    )
    program = models.ForeignKey('bpms_common.ProgramModel',
                                null=True,
                                blank=True,
                                verbose_name=_('Программа'),
                                on_delete=CUSTOM_PROTECT)
    counterparty = models.ForeignKey('bpms_common.CounterpartyModel',
                                     null=True,
                                     blank=True,
                                     verbose_name=_('Контрагент'),
                                     on_delete=CUSTOM_PROTECT)
    costing_object = models.ForeignKey('bpms_common.CostingObjectModel',
                                       null=True,
                                       blank=True,
                                       verbose_name=_('Объект калькуляции'),
                                       on_delete=CUSTOM_PROTECT)
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        verbose_name=_('Организация'),
        on_delete=CUSTOM_PROTECT,
        related_name='workgroups',
    )
    location = common_fields.CustomForeignKey(
        to='accounting_catalogs.KATOCodesModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Местоположение'),
        related_name='workgroups'
    )
    funds = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Стоимость проекта, всего'),
        help_text='млн. тенге',
    )
    funds_currency = common_fields.CustomForeignKey(
        to='catalogs.CurrencyModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=True,
        default=get_default_currency,
        related_name='work_groups',
        verbose_name=_('Валюта'),
    )
    social_links = models.ManyToManyField(
        SocialURLs,
        blank=True,
        verbose_name=_("Ссылки на социальные сети")
    )
    public_or_private = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_("Закрытая")
    )
    gallery_files = models.ManyToManyField(
        File,
        blank=True,
        verbose_name=_("Файлы галереи"),
        related_name="workgroup_gallery_files"
    )
    is_project = models.BooleanField(
        default=False,
        verbose_name=_("Проект")
    )
    control_dates = models.BooleanField(
        default=False, blank=True,
        verbose_name=_("Вести контроль дат задач")
    )
    date_start_plan = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Планируемая дата начала")
    )
    dead_line = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Крайний срок"),
    )
    finished_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Дата выполнения"),
    )
    is_finished = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Завершен'),
    )
    is_helpdesk = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Это группа техподдержки'),
    )
    with_chat = models.BooleanField(default=False, verbose_name=_('Группа с чатом'))
    linked_chat = models.ForeignKey('chat.ChatModel',
                                    verbose_name=_('Чат группы'),
                                    null=True,
                                    blank=True,
                                    to_field='chat_uid',
                                    on_delete=CUSTOM_PROTECT)
    work_directions = models.ManyToManyField(
        'catalogs.WorkDirectionModel',
        through='workgroups.WorkgroupWorkDirectionModel',
        through_fields=('work_group', 'work_direction',),
        verbose_name=_('Направления работы'),
        related_name='work_groups',
    )
    members = models.ManyToManyField(
        'users.ProfileModel',
        through='WorkgroupMembersModel',
        through_fields=('work_group', 'member'),
        verbose_name=_('Участники'),
        related_name='workgroup_memberships',
        blank=True,
    )
    is_overdue = models.BooleanField(default=False, verbose_name=_('Просрочен'))

    progress = models.PositiveSmallIntegerField(
        default=0,
        null=False,
        blank=False,
        verbose_name=_('Прогресс'),
        help_text=_('Процент выполнения задач, от 0 до 100'),
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')

    my_workgroup_filter = IsMyWorkgroupField()
    member_filter = MemberFakeField()
    location_filter = LocationFilterFakeField()
    in_favorites_filter = InFavoritesFilterField()

    @classmethod
    def get_snapshot(cls, id):
        """Короткое стандартизированное описание объекта: id, текстовое представление, изображение."""
        from .serializers import WorkgroupNameLogoSerializer
        workgroup = cls.objects.get(id=id)
        serializer_data = WorkgroupNameLogoSerializer().to_representation(workgroup)
        snapshot = {
            "id": str(id),
            "repr": serializer_data.get("name", ""),
            "image": serializer_data.get("workgroup_logo")
        }
        return snapshot

    @property
    def frontend_route(self):
        if self.is_project:
            return '/projects?viewProject=' + str(self.id)  # переопределяем в целевой модели
        else:
            return '/groups?viewGroup=' + str(self.id)  # переопределяем в целевой модели

    @property
    def duration_days(self):
        """Продолжительность проекта в днях. Количество суток с округлением в бОльшую сторону."""
        if self.dead_line and self.date_start_plan:
            duration = self.dead_line - self.date_start_plan
            if duration.seconds > 0: # округляем в бОльшую сторону.
                duration_days = duration.days + 1
            else:
                duration_days = duration.days
        else:
            duration_days = None
        return duration_days

    @property
    def duration_minutes(self):
        """Продолжительность проекта в минутах. Для диаграммы Ганта."""
        if self.date_start_plan and self.dead_line and self.date_start_plan < self.dead_line:
            duration = self.dead_line - self.date_start_plan
            duration_minutes = duration.total_seconds() / 60
        else:
            duration_minutes = None
        return duration_minutes
    
    def check_dates(self):
        if self.is_project and self.dead_line and self.date_start_plan and self.date_start_plan > self.dead_line:
            raise drf_exceptions.ValidationError('Дата начала не может быть позже срока выполнения.')
        # if self.pk and self.is_project:
        #     if self.dead_line and self.project_tasks.filter(is_active=True, dead_line__gt=self.dead_line).exists(): # noqa
        #         raise drf_exceptions.ValidationError('Крайний срок не может быть раньше крайнего срока задач проекта.')
        #     if self.date_start_plan and self.project_tasks.filter( # noqa
        #             is_active=True,
        #             date_start_plan__lt=self.date_start_plan,
        #             date_start_plan__isnull=False
        #     ).exists():
        #         raise drf_exceptions.ValidationError('Дата начала не может быть позже даты начала задач проекта.')

    def save(self, *args, **kwargs):
        old_name = None
        if self.pk:
            old_name = WorkgroupModel.objects.only("name").get(pk=self.pk).name
            cache.set('WorkgroupNameLogoSerializer_' + str(self.pk), None)
        else:
            if self.external_id:
                self.is_project = True
        if not self.is_project:  # Вот хз....
            self.control_dates = False  # Может и не надо такое делать. Вдруг, для групп тоже захотят
        if self.is_finished and not self.finished_date:
            self.finished_date = timezone.now()
        if not self.is_finished and self.finished_date:
            self.finished_date = None
        if TASK_DATES_CONTROL and self.control_dates:
            self.check_dates()
        with transaction.atomic():
            if self.with_chat:
                if not self.linked_chat:
                    workgroup_founder_member = self.workgroupmembersmodel_set.filter(
                        is_active=True,
                        membership_role__code='FOUNDER',
                        membership_request_status__code='APPROVED',
                    ).first()
                    if workgroup_founder_member:
                        workgroup_founder = workgroup_founder_member.member
                    else:
                        workgroup_founder = self.author
                    chat = ChatModel.objects.create(chat_author=workgroup_founder,
                                                    name=self.name,
                                                    is_public=True,
                                                    last_sent=timezone.now(),
                                                    )
                    self.linked_chat = chat
                    chat_members_to_redis = []
                    author_member = chat.members.create(user=workgroup_founder, is_moderator=True)
                    chat_members_to_redis.append(author_member)
                    wg_members = self.workgroupmembersmodel_set.filter(is_active=True).exclude(member=workgroup_founder)

                    for wg_member in wg_members:
                        new_member = chat.members.create(user=wg_member.member)
                        chat_members_to_redis.append(new_member)
                    data = json.dumps(
                        {'event': 'chat_create_chat',
                         'data': {
                             "chat_uid": str(chat.chat_uid),
                             "is_public": True,
                             "members": [{"user": str(each.user.id), "is_moderator": str(each.is_moderator)} for each in
                                         chat_members_to_redis],
                             "name": chat.name,
                             "chat_author": str(chat.chat_author.pk),
                             "last_sent": DateTimeField().to_representation(chat.last_sent),
                             "new_message_count": 0,
                             "is_active": True,
                             "member_count": len(chat_members_to_redis)
                         }
                         }
                    )
                    transaction.on_commit(lambda: socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data))
                else:
                    chat = self.linked_chat
                    if not chat.is_public:
                        raise BadRequest([{'type': 'badData',
                                           'message': 'Невозможно прикрепить личный чат к Рабочей группе/проекту '}])
                    chat.name = self.name
                    chat.save()
            super().save(*args, **kwargs)
            if old_name is not None and old_name != self.name:
                from bpms.event_calendar.utils import sync_related_calendar_name
                sync_related_calendar_name(related_object_id=self.pk)
        workgroup_logo = self.workgroup_logo
        if workgroup_logo:
            transaction.on_commit(lambda: workgroup_logo.copy_to_avatar_path())

    def get_update_permission(self, request) -> bool:
        member = request.user.profile
        if member.can_create_workgroups:
            return True
        return self.workgroupmembersmodel_set.filter(
            models.Q(
                member=member,
                membership_role=WorkgroupMembershipRole.objects.get(code="MODERATOR")
            ) |
            models.Q(
                member=member,
                membership_role=WorkgroupMembershipRole.objects.get(code="FOUNDER")
            )
        ).exists()

    def get_assign_founder_permission(self, request) -> bool:
        member = request.user.profile
        if member.can_create_workgroups:
            return True
        if self.workgroupmembersmodel_set.filter(
            models.Q(
                member=member,
                membership_role=WorkgroupMembershipRole.objects.get(code="FOUNDER")
            )
        ).exists():
            return True

        return False

    def get_detail_permission(self, request) -> bool:
        if request:
            profile = request.user.profile
            if profile.is_support:
                return True
        return WorkgroupMembersModel.objects.filter(
                is_active=True,
                member=request.user.profile,
                work_group=self,
                work_group__is_active=True,
                membership_request_status=WorkgroupMembershipStatus.objects.get(code="APPROVED")
        ).exists()

    def __str__(self):
        return f"{self.name}"

    def get_select_list_logo_url(self):
        if self.workgroup_logo and getattr(self.workgroup_logo, 'is_active', True):
            return self.workgroup_logo.avatar_url
        return ''

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_queryset(request).filter(name__icontains=text).select_related('workgroup_logo')

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import get_workgroup_queryset
        qs = get_workgroup_queryset(request)
        return qs

    @classmethod
    def prepare_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        user = get_current_authenticated_profile()
        workgroup_member = WorkgroupMembersModel.objects.filter(
            is_active=True,
            membership_request_status=WorkgroupMembershipStatus.objects.get(code="APPROVED")
        ).values_list("work_group", flat=True).distinct("work_group")
        qs = qs.filter(is_active=True, pk__in=workgroup_member).annotate(
            is_user=Count('workgroupmembersmodel__member',
                          filter=Q(workgroupmembersmodel__member=user,
                                   workgroupmembersmodel__is_active=True)))
        return qs

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.get_queryset(request).select_related('workgroup_logo')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import WorkgroupNotifySerializer, WorkgroupCreateSerializer, WorkgroupUpdateSerializer, \
            WorkgroupListSerializer, WorkgroupDetailSerializer, WorkgroupSearchSerializer,WorkgroupMembershipUpdateDefaultVisorSerializer

        if action == 'list':
            return WorkgroupListSerializer
        elif action == 'retrieve':
            return WorkgroupDetailSerializer
        elif action == 'create':
            return WorkgroupCreateSerializer
        elif action in ('update', 'partial_update',):
            return WorkgroupUpdateSerializer
        elif action == 'notify':
            return WorkgroupNotifySerializer
        elif action == 'search':
            return WorkgroupSearchSerializer
        elif action == 'change_default_visor':
            return WorkgroupMembershipUpdateDefaultVisorSerializer
        else:
            return WorkgroupDetailSerializer

    @classmethod
    def get_table_columns(cls):
        return 'name', 'author', 'public_or_private', 'dead_line', 'is_finished', 'member_filter', \
               'my_workgroup_filter', 'organization', 'in_favorites_filter'

    @classmethod
    def get_order_param(cls):
        return ['name', ]

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_filter_fields(cls, exclude=None, request=None):
        data = super().get_filter_fields(exclude, request)
        page_name = request.query_params.get('page_name', '')
        if page_name.startswith('page_list_project'):
            result = filter(
                lambda x: (x.get('name', '') not in ['public_or_private', 'public_or_private__exclude']),
                data
            )
            return result
        if page_name.startswith('page_list_workgroup'):
            result = filter(
                lambda x: (x.get('name', '') not in [
                    'dead_line', 'dead_line__exclude', 'is_finished', 'is_finished__exclude'
                ]),
                data
            )
            return result
        return data

    @property
    def label(self):
        label = super().label
        if self.is_project:
            return label + '_project'
        return label
    
    @property
    def location_point(self):
        point_list = list(self.location_points.all())
        if point_list:
            return point_list[0]
        else:
            return None

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        """Аннотации для отчётов (головная организация по связи structural_division)."""
        annotations = {}
        names = set(requested_computed or [])
        outer_ref_column = kwargs.get('outer_ref_column')

        if 'root_organization' in names:
            from common.catalogs.models import ContractorRelationModel

            organization_pk_field = cls._meta.get_field('organization').target_field
            if outer_ref_column:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                wg_root_subquery = cls.objects.filter(
                    pk=OuterRef(outer_ref_column),
                ).annotate(
                    resolved_root_organization=Coalesce(
                        Subquery(root_organization_subquery),
                        F('organization_id'),
                        output_field=organization_pk_field,
                    )
                ).values('resolved_root_organization')[:1]
                annotations['root_organization'] = Subquery(
                    wg_root_subquery,
                    output_field=organization_pk_field,
                )
            else:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                annotations['root_organization'] = Coalesce(
                    Subquery(root_organization_subquery),
                    F('organization_id'),
                    output_field=organization_pk_field,
                )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                'name': 'root_organization',
                'type': 'ForeignKey',
                'related_model': 'catalogs.ContractorModel',
                'verbose_name': _('Головная организация'),
            },
        ]


class WorkgroupWorkDirectionModel(BaseAbstractModel):
    work_group = models.ForeignKey(
        WorkgroupModel,
        blank=False,
        null=True,
        verbose_name=_("Рабочая группа"),
        on_delete=CUSTOM_CASCADE,
        related_name='workgroup_work_directions',
    )
    work_direction = models.ForeignKey(
        'catalogs.WorkDirectionModel',
        blank=False,
        null=True,
        verbose_name=_('Направление работы'),
        on_delete=CUSTOM_CASCADE,
        related_name='workgroup_work_directions',
    )

    class Meta:
        verbose_name = _('Направление работы')
        verbose_name_plural = _('направления работы')
        unique_together = (('work_group', 'work_direction',),)
        ordering = ('work_direction__name',)


class WorkgroupMembersModel(BaseModel):
    member = models.ForeignKey(
        'users.ProfileModel',
        blank=True,
        null=True,
        verbose_name=_("Участник"),
        on_delete=CUSTOM_CASCADE
    )
    work_group = models.ForeignKey(
        WorkgroupModel,
        blank=True,
        null=True,
        verbose_name=_("Рабочая группа"),
        on_delete=CUSTOM_CASCADE
    )
    membership_request_status = models.ForeignKey(
        WorkgroupMembershipStatus,
        blank=True,
        null=True,
        verbose_name=_("Статус участника рабочей группы"),
        on_delete=CUSTOM_DO_NOTHING
    )
    membership_role = models.ForeignKey(
        WorkgroupMembershipRole,
        blank=True,
        null=True,
        verbose_name=_("Роль участника рабочей группы"),
        on_delete=CUSTOM_DO_NOTHING
    )
    member_visible = models.BooleanField(
        default=False,
        verbose_name=_("Видимость участника рабочей группы")
    )
    member_organization = common_fields.CustomForeignKey(
        to='WorkgroupMemberOrganizationModel',
        null=True,
        blank=True,
        verbose_name='Организация-участник',
        on_delete=CUSTOM_SET_NULL,
        related_name='project_members',
    )
    default_visor = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Наблюдатель по умолчанию')
    )

    class Meta:
        verbose_name = _("Состав рабочей группы")
        verbose_name_plural = _("Составы рабочей группы")

    def clean(self):
        if WorkgroupMembersModel.objects.filter(member=self.member, work_group=self.work_group,
                                                is_active=True).exclude(id=self.id).exists():
            raise ValidationError('Member already exists')


class ProjectTemplateModel(BaseAbstractModel):
    """Шаблон проекта."""
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        verbose_name='Название')
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        verbose_name='Организация',
        on_delete=CUSTOM_PROTECT,
        related_name='project_templates',
    )
    is_public = common_fields.CustomBooleanField(
        default=True,
        verbose_name='Публичный')
    is_draft = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Черновик')

    class Meta:
        verbose_name = 'Шаблон проекта'
        verbose_name_plural = 'Шаблоны проектов'

    def __str__(self):
        return getattr(self, 'name')

    def get_detail_permission(self, request) -> bool:
        """Право просматривать шаблоны.
        Для публичных шаблонов: пользователи с правами создавать проекты + директора организаций.
        Для приватных шаблонов: пользовали с правами создавать проекты  + директор в ДАННОЙ организации."""
        user = request.user.profile
        # Для публичных шаблонов
        if self.is_public:
            im_director = user.contractor_profile.filter(
                director=True,
                ).exists()
            from contractor_permissions.utils import contractors_where_user_has_permission
            if contractors_where_user_has_permission(user.pk, 'create_workgroup', None):
                contractor_permission = True
            else:
                contractor_permission = False
        # Для приватных шаблонов
        else:
            contractor_id = self.organization
            im_director = user.contractor_profile.filter(
                director=True,
                contractor_id=contractor_id,
                ).exists()
            try:
                from contractor_permissions.utils import check_contractor_permission
                check_contractor_permission(user.pk, contractor_id, 'create_workgroup', None)
            except drf_exceptions.PermissionDenied:
                contractor_permission = False
            else:
                contractor_permission = True
        if im_director or contractor_permission:
            return True
        else:
            return False
    
    def get_update_permission(self, request) -> bool:
        """Для публичных шаблонов: только суперпользователи.
        Для приватных шаблонов: пользовали с правами создавать проекты в ДАННОЙ организации + директор."""
        if self.is_public:
            return request.user.is_superuser
        else:
            user = request.user.profile
            contractor_id = self.organization
            im_director = user.contractor_profile.filter(
                director=True,
                contractor_id=contractor_id
                ).exists()
            try:
                from contractor_permissions.utils import check_contractor_permission
                check_contractor_permission(user.pk, contractor_id, 'create_workgroup', None)
            except drf_exceptions.PermissionDenied:
                contractor_permission = False
            else:
                contractor_permission = True
            
            if im_director or contractor_permission:
                return True
            else:
                return False

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ProjectTemplateCreateSerializer, ProjectTemplateListSerializer, ProjectTemplateDetailSerializer
        if action:
            if action == 'list':
                return ProjectTemplateListSerializer
            elif action == 'create':
                return ProjectTemplateCreateSerializer
            elif action in ('update', 'partial_update'):
                return ProjectTemplateCreateSerializer
            elif action == 'retrieve':
                return ProjectTemplateDetailSerializer
            else:
                return ProjectTemplateListSerializer
        return ProjectTemplateListSerializer
    
    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_queryset(request).filter(name__icontains=text)

    @classmethod
    def get_queryset(cls, request=None):
        """Показывать все публичные шаблоны и шаблоны организаций, где пользователь может создавать проекты.
        Черновики смотреть может только автор."""
        qs = cls.objects.filter(is_active=True)
        if request:
            user = request.user.profile
            from contractor_permissions.utils import contractors_where_user_has_permission, contractors_where_im_director
            create_workgroup_organizations = contractors_where_user_has_permission(user.pk, 'create_workgroup', None)
            director_organizations = contractors_where_im_director(user)
            lookup = Q()
            lookup |= Q(is_public=True)
            lookup |= Q(organization_id__in=create_workgroup_organizations)
            lookup |= Q(organization_id__in=director_organizations)
            qs = qs.filter(lookup)
            qs = qs.exclude(~Q(author=user), is_draft=True)
        return qs.order_by('is_public', 'name',)
    

class TaskTemplateModel(MPTTModel, BaseModel):
    """Шаблон проекта. Состоит из связанных задач."""
    template = common_fields.CustomForeignKey(
        ProjectTemplateModel,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name='tasks',
        verbose_name=_('Шаблон')
    )
    parent = TreeForeignKey(
        'self',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        related_name='children'
        )
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Название')
        )
    result = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Результат')
        )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )
    order = common_fields.CustomPositiveIntegerField(
        blank=True,
        null=False,
        default=0,
        verbose_name=_('Порядковый номер'),
    )
    duration = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_('Продолжительность')
    )
    TASK_TYPE_CHOICES = [
        ('task', _('Задача')),
        ('stage', _('Этап')),
        ('milestone', _('Веха')),
    ]
    task_type = common_fields.CustomCharField(
        choices=TASK_TYPE_CHOICES,
        max_length=10,
        null=False,
        default='task',
        verbose_name=_('Тип задачи')
    )

    @property
    def duration_days(self):
        return self.duration.days

    class Meta:
        verbose_name = _('Шаблон задачи')
        verbose_name_plural = _('Шаблоны задач')

    def __str__(self):
        return getattr(self, 'name')

    def save(self, *args, **kwargs):
        is_created = True if self.pk is None else False
        if is_created:
            # При создании помещаем задачу с самый низ (присваиваем макс номер order).
            # Если задача является подзадачей, то назначаем макс номер относительно ее "сестёр".
            if self.parent:
                super().save(*args, **kwargs) # сначала надо сохранить, чтобы обращаться к get_siblings
                max_order = self.get_siblings(include_self=False).aggregate(max_order=Coalesce(Max('order'), Value(0)))['max_order']
                self.order = max_order + 1
                self.save()
            # Если задача не имеет родителя (т.е. не является подзадачей), то назначаем макс номер относительно шаблона.
            else:
                max_order = self.template.tasks.filter(level=0).aggregate(max_order=Coalesce(Max('order'), Value(0)))['max_order']
                self.order = max_order + 1
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TaskTemplateCreateSerializer, TaskTemplateListSerializer, TaskTemplateDetailSerializer, TaskTemplateUpdateSerializer
        if action:
            if action == 'list':
                return TaskTemplateListSerializer
            elif action == 'create':
                return TaskTemplateCreateSerializer
            elif action in ('update', 'partial_update'):
                return TaskTemplateUpdateSerializer
            elif action == 'retrieve':
                return TaskTemplateDetailSerializer
            else:
                return TaskTemplateListSerializer
        return TaskTemplateListSerializer


class WorkgroupMemberOrganizationStatusModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name='Цвет',
    )

    class Meta:
        verbose_name = _("Статус организации-участника проекта")
        verbose_name_plural = _("Статусы организации-участника проекта")


class WorkgroupMemberOrganizationModel(BaseModel):
    """Организация-участник рабочей группы"""
    work_group = common_fields.CustomForeignKey(
        WorkgroupModel,
        blank=False,
        null=False,
        verbose_name=_("Рабочая группа"),
        on_delete=CUSTOM_CASCADE,
        related_name='participating_organizations'
    )
    status = common_fields.CustomForeignKey(
        to=WorkgroupMemberOrganizationStatusModel,
        to_field='code',
        null=True,
        blank=True,
        verbose_name=_('Статус организации-участника проекта'),
        on_delete=CUSTOM_PROTECT,
        related_name='members',
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=False,
        blank=False,
        verbose_name=_('Организация'),
        on_delete=CUSTOM_CASCADE,
        related_name='participated_workgroups',
    )
    role = common_fields.CustomForeignKey(
        to='catalogs.ContractorRelationTypeModel',
        to_field='code',
        null=False,
        blank=False,
        verbose_name=_('Роль организации в проекте'),
        on_delete=CUSTOM_CASCADE
    )

    class Meta:
        verbose_name = _('Участвующая организация')
        verbose_name_plural = _('Участвующие организации')

    def get_update_permission(self, request=None) -> bool:
        """
        Редактировать организацию-участник рабочей группы
        имеют право пользователи с ролями 'FOUNDER', 'MODERATOR'
        и связанный с объектом 'ORG-COORDINATOR'.
        """
        if request is None:
            return False

        isMember = Q(is_active=True, member=request.user.profile)
        isManagers = Q(membership_role__code__in=['FOUNDER', 'MODERATOR'])
        isCoordinator = Q(
            membership_role__code='ORG-COORDINATOR',
            member_organization=self
        )

        lookup = isMember & (isManagers | isCoordinator)

        return self.work_group.workgroupmembersmodel_set.filter(
            lookup
        ).exists()

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MemberOrganizationsSerializer, WorkgroupMemberOrganizationModelCreateSerializer

        if action == 'create':
            return WorkgroupMemberOrganizationModelCreateSerializer
        return MemberOrganizationsSerializer
        
    def __str__(self):
        return f"{self.organization} в {self.work_group} ({self.role})"
