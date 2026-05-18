import datetime
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q, Prefetch

from rest_framework import exceptions as drf_exceptions

from model_utils import FieldTracker

from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel
from common import fields as common_fields
from common.page_config.filter_fields import ChoiceFilterField, ForeignKeyFilterField, ProfileFilterField, \
    CharFilterField
from common.utils import get_available_section_codes, use_access_groups
from change_history import utils as change_history_utils
from contractor_permissions.utils import check_contractor_permission, contractors_where_user_has_permission
from users.utils import get_tree_departments_related_organizations
from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE, CUSTOM_SET_NULL

from .utils import calculate_key_result_progress, get_quarter
from . import fields


QUARTER_CHOICES = (
    (1, _('I')),
    (2, _('II')),
    (3, _('III')),
    (4, _('IV')),
)


class ValueEffortsModel(BaseCatalog, BaseAbstractCatalog):
    """Модель приоритетов целей по матрице усилий и результатов (Value/Efforts)."""
    meta_exclude_fields = ['author', 'code', 'color', 'hex_color', 'created_at', 'mentions', 'ct',]
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )
    hex_color = common_fields.CustomCharField(
        null=False,
        default='#ffffff',
        blank=True,
        max_length=7,
        verbose_name=_('Код цвета'),
        help_text='начинается с #: #ff00ff',
    )

    class Meta:
        verbose_name = _('Матрица усилий и результатов')
        verbose_name_plural = _('Матрица усилий и результатов')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ValueEffortSerializer
        return ValueEffortSerializer


class ObjectiveStatusModel(BaseCatalog, BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'code', 'color', 'hex_color', 'created_at', 'mentions', 'ct',]
    """Модель статусов целей OKR."""
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )
    hex_color = common_fields.CustomCharField(
        null=False,
        default='#ffffff',
        blank=True,
        max_length=7,
        verbose_name=_('Код цвета'),
        help_text='начинается с #: #ff00ff',
    )
    is_closed = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Цель закрыта'),
    )

    class Meta:
        verbose_name = _('Статус цели')
        verbose_name_plural = _('Статусы целей')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ObjectiveStatusSerializer
        return ObjectiveStatusSerializer
    

class NotificationFrequencyModel(BaseCatalog, BaseAbstractCatalog):
    """Модель частоты напоминаний о необходимости обновить цели и ключевые результаты."""
    meta_exclude_fields = ['author', 'code', 'cron', 'created_at', 'mentions', 'ct',]
    description = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание')
    )
    cron = common_fields.CustomCharField(
        max_length=50,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Cron-выражение')
    )

    class Meta:
        verbose_name = _('Частота напоминания')
        verbose_name_plural = _('Частота напоминаний')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import NotificationFrequencySerializer
        return NotificationFrequencySerializer
    

class InitiativesRelatedObjectType(BaseCatalog, BaseAbstractCatalog):
    """Модель типа объекта, который является источником инициативы (задача, спринт и т.д.)."""
    model_label = common_fields.CustomCharField(
        max_length=63,
        null=False,
        default='',
        blank=True,
        verbose_name='Имя модели',
        help_text='имя_модуля.ИмяМодели: tasks.TaskModel'
    )

    class Meta:
        verbose_name = _('Источник инициативы')
        verbose_name_plural = _('Источники инициатив')


class KeyResultMetricsModel(BaseCatalog, BaseAbstractCatalog):
    """Модель метрик ключевых результатов."""
    meta_exclude_fields = ['author', 'code', 'contractor', 'is_demo', 'created_at', 'mentions', 'ct',]
    description = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание')
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')

    class Meta:
        verbose_name = _('Метрика ключевого результата')
        verbose_name_plural = _('Метрики ключевых результатов')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import KeyResultMetricsSerializer
        return KeyResultMetricsSerializer


    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()
        user_id = request.user.profile.pk
        okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)

        if okr_organizations:
            lookup = Q(contractor_id__in=okr_organizations)

        contractor_id = request.query_params.get('contractor')
        search = request.query_params.get('search')
        if contractor_id:
            if uuid.UUID(contractor_id) in okr_organizations:
                lookup = Q(contractor_id__in=okr_organizations)
            else:
                qs = qs.none()
        lookup |= Q(contractor__isnull=True)
        if search and len(search) > 2:
            lookup &= Q(name__icontains=search)
        qs = qs.filter(lookup)
        return qs.order_by('contractor_id', 'name',)

    def get_update_permission(self, request) -> bool:
        user_id = request.user.profile.pk
        contractor_id = self.contractor.pk
        try:
            check_contractor_permission(user_id, contractor_id, ('create_okr', 'operator_okr'), None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        """Просматривать миссию организации могут все сотрудники дерева организаций.
        У сотрудника должны быть права на просмотр целей ОКР."""
        user_id = request.user.profile.pk
        okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)
        okr_organizations_tree = get_tree_departments_related_organizations(okr_organizations)
        if self.contractor_id in okr_organizations_tree:
            return True
        else:
            return False

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass


class MissionModel(BaseModel):
    """Миссия компании."""
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация'),
        related_name='okr_info',
        null=False,
        blank=False,
    )
    mission = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Миссия компании'),
    )

    class Meta:
        verbose_name = _('Миссия компании')
        verbose_name_plural = _('Миссии компаний')

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        return serializers.MissionSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        user_id = request.user.profile.pk
        okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)
        okr_organizations_tree = get_tree_departments_related_organizations(okr_organizations)
        qs = qs.filter(organization__in=okr_organizations_tree)

        organization_id = request.query_params.get('organization')
        if organization_id:
            if uuid.UUID(organization_id) in okr_organizations_tree:
                qs = qs.filter(organization_id=organization_id)
            else:
                qs = qs.none()
        return qs.order_by('-created_at')

    def get_update_permission(self, request) -> bool:
        user_id = request.user.profile.pk
        organization_id = self.organization.pk
        try:
            check_contractor_permission(user_id, organization_id, 'create_okr', None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        """Просматривать миссию организации могут все сотрудники дерева организаций.
        У сотрудника должны быть права на просмотр целей ОКР."""
        user_id = request.user.profile.pk
        okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)
        okr_organizations_tree = get_tree_departments_related_organizations(okr_organizations)
        if self.organization_id in okr_organizations_tree:
            return True
        else:
            return False

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass


class ObjectivesModel(BaseModel, MetadataAbstractModel):
    """Модель целей OKR"""
    tps = []
    meta_exclude_fields = ['parent', 'is_demo', 'created_at', 'mentions', 'ct',]

    tracker = FieldTracker(
        fields=(
            'parent',
            'department',
            'owner',
            'operator',
            'objective',
            'date_start',
            'date_end',
            'is_public',
            'value_efforts',
            'status',
            'notification',
        )
    )
    track_prefix = 'objective'

    parent = models.ForeignKey(
        to='self',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Родительская цель'),
        )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация'),
        related_name='objectives',
        null=True,
        blank=False,
    )
    department = common_fields.CustomForeignKey(
        to='catalogs.ContractorDepartmentModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Отдел'),
        related_name='objectives',
        null=True,
        blank=True,
    )
    owner = common_fields.CustomForeignKey(
        'users.ProfileModel',
        null=True,
        on_delete=CUSTOM_PROTECT,
        related_name='owner_objectives',
        verbose_name=_('Постановщик'),
        filter_info=ProfileFilterField(),
    )
    operator = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Ответственный за цель'),
        related_name='operator_objectives',
        filter_info=ProfileFilterField(),
    )
    objective = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание цели'),
    )
    date_start = common_fields.CustomDateField(
        null=False,
        blank=False,
        verbose_name=_('Дата начала')
    )
    date_end = common_fields.CustomDateField(
        null=False,
        blank=False,
        verbose_name=_('Дата окончания')
    )
    date_end_quarter = common_fields.CustomPositiveIntegerField(
        choices=QUARTER_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Квартал окончания'),
    )
    is_public = common_fields.CustomBooleanField(
        default=True,
        verbose_name='Общедоступная цель')
    visors = models.ManyToManyField(
        'users.ProfileModel',
        through='ObjectiveVisor',
        verbose_name=_('Наблюдатели'),
        related_name='visor_objectives',
    )
    value_efforts = common_fields.CustomForeignKey(
        to='okr.ValueEffortsModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        verbose_name=_('Усилия и результаты')
    )
    status = common_fields.CustomForeignKey(
        'okr.ObjectiveStatusModel',
        to_field='code',
        null=False,
        default='as_planned',
        verbose_name=_('Status'),
        on_delete=CUSTOM_PROTECT,
        related_name='objectives',
    )
    notification = common_fields.CustomForeignKey(
        'okr.NotificationFrequencyModel',
        to_field='code',
        null=False,
        default='quarterly',
        verbose_name=_('Частота напоминаний'),
        on_delete=CUSTOM_PROTECT,
        related_name='objectives',
    )
    notify_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата следующего напоминания')
    )

    progress = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        verbose_name=_("Прогресс"),
        validators=(MaxValueValidator(limit_value=100),)
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')

    departments_filter = fields.DepartmentsFilterField()
    user_current_contractor_departments_filter = fields.UserCurrentContractorDepartmentsFilterField()
    objective_period_filter = fields.ObjectivePeriodFilterField()

    class Meta:
        verbose_name = _('Цель организации')
        verbose_name_plural = _('Цели организаций')

    @classmethod
    def get_table_columns(cls):
        return [
            'objective_period_filter',
            'user_current_contractor_departments_filter',
            'status'
        ]
    def __str__(self):
        return self.objective

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.ObjectivesModelCreateSerializer
        elif action == 'retrieve':
            return serializers.ObjectivesModelDetailSerializer
        elif action in ('update', 'partial_update',):
            return serializers.ObjectivesModelUpdateSerializer
        elif action == 'notify':
            return serializers.ObjectivesModelNotifySerializer
        else:
            return serializers.ObjectivesModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()
        user_id = request.user.profile.pk
        okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)
        qs = qs.filter(organization__in=okr_organizations)

        organization_id = request.query_params.get('organization')
        if organization_id:
            if uuid.UUID(organization_id) in okr_organizations:
                qs = qs.filter(organization_id=organization_id)
            else:
                qs = qs.none()

        department_id = request.query_params.get('department')
        if department_id:
            qs = qs.filter(department_id=department_id)

        parent = request.query_params.get('parent', None)
        if parent:
            if parent == 'root':
                qs = qs.filter(parent__isnull=True)
            else:
                qs = qs.filter(parent=parent)

        date_start = request.query_params.get('date_start')
        if date_start:
            qs = qs.filter(date_start__gte=date_start)

        date_end = request.query_params.get('date_end')
        if date_end:
            qs = qs.filter(date_end__lte=date_end)

        quarter = request.query_params.get('quarter')
        if quarter:
            qs = qs.filter(date_end_quarter=quarter)

        text = request.query_params.get('text')
        if text:
            qs = qs.filter(objective__icontains=text)

        qs = qs.exclude(Q(is_public=False) & ~Q(author_id=user_id) & ~Q(visors__id=user_id)).distinct()
        qs = qs.select_related('organization', 'department', 'value_efforts', 'status', 'notification',)
        qs = qs.prefetch_related('children')
        return qs.order_by('date_start', 'date_end', '-created_at')


    @classmethod
    def get_select_queryset(cls, request=None):
        qs = cls.get_queryset(request)
        qs = qs.filter(status__is_closed=False,
                       department__isnull=True,
                       ).select_related(None).prefetch_related(None)
        return qs

    def get_update_permission(self, request) -> bool:
        user_id = request.user.profile.pk
        try:
            check_contractor_permission(user_id, self.organization_id, 'create_okr', None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return self.is_public or self.author_id==user_id

    def get_detail_permission(self, request) -> bool:
        """Просматривать цели организации могут администраторы и сотрудники управления проектами."""
        user_id = request.user.profile.pk
        try:
            check_contractor_permission(user_id, self.organization_id, ('create_okr', 'operator_okr'), None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return self.is_public or self.author_id == user_id or self.visors.filter(id=user_id).exists()

    def get_update_key_results_permission(self, request) -> bool:
        """Может ли пользователь создавать ключевые результаты у цели."""
        user_id = request.user.profile.pk
        update_permission = self.get_update_permission(request)
        return (update_permission or
                (self.is_public and self.owner_id==user_id) or
                (self.is_public and self.operator_id==user_id))

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    def recalculate_progress(self):
        """Пересчитывает прогресс цели на основе прогресса ключевых результатов."""
        key_results = list(KeyResultsModel.objects.filter(
            is_active=True, 
            objective_id=self.id
        ).values('progress'))
        
        progress_list = [item['progress'] for item in key_results if item['progress'] is not None]
        
        try:
            average = round(sum(progress_list) / len(progress_list), 0)
            self.progress = int(average)
        except (ZeroDivisionError, TypeError):
            self.progress = 0

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического обновления квартала."""
        if self.date_end:
            quarter_num = get_quarter(self.date_end)
            self.date_end_quarter = quarter_num
        else:
            self.date_end_quarter = None
        
        # Пересчитываем прогресс
        self.recalculate_progress()
        
        # Сохраняем объект
        super().save(*args, **kwargs)

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        # if 'parent' in changed_fields:
        #     parent_after = self.parent
        #     if parent_after:
        #         parent_id_after = parent_after.pk
        #     else:
        #         parent_id_after = None
        #     change_history_utils.create_update_catalog_fk(
        #         self.pk,
        #         action_date,
        #         'objective__parent',
        #         changed_fields['parent'],
        #         parent_id_after,
        #     )
        if 'parent' in changed_fields:
            parent_after = self.parent
            if parent_after:
                parent_objective_after = parent_after.objective
            else:
                parent_objective_after = ''
            if changed_fields['parent']:
                parent_before = ObjectivesModel.objects.get(pk=changed_fields['parent'])
                parent_objective_before = parent_before.objective
            else:
                parent_objective_before = ''
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'objective__parent',
                parent_objective_before,
                parent_objective_after,
            )
        if 'department' in changed_fields:
            department_after = self.department
            if department_after:
                department_id_after = department_after.pk
            else:
                department_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'objective__department',
                changed_fields['department'],
                department_id_after,
            )
        if 'owner' in changed_fields:
            owner_after = self.owner
            if owner_after:
                owner_id_after = self.owner.pk
            else:
                owner_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'objective__owner',
                changed_fields['owner'],
                owner_id_after,
            )
        if 'operator' in changed_fields:
            operator_after = self.operator
            if operator_after:
                operator_id_after = self.operator.pk
            else:
                operator_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'objective__operator',
                changed_fields['operator'],
                operator_id_after,
            )
        if 'objective' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'objective__objective',
                changed_fields['objective'],
                self.objective,
            )
        if 'date_start' in changed_fields:
            date_start_before = changed_fields['date_start']
            date_start_after = self.date_start
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'objective__date_start',
                date_start_before,
                date_start_after,
            )
        if 'date_end' in changed_fields:
            date_end_before = changed_fields['date_end']
            date_end_after = self.date_end
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'objective__date_end',
                date_end_before,
                date_end_after,
            )
        if 'is_public' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'objective__is_public',
                self.is_public,
            )
        if 'value_efforts' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['value_efforts'],
                ValueEffortsModel,
                'value_efforts',
                'objective',
                action_date,
            )
        if 'status' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['status'],
                ObjectiveStatusModel,
                'status',
                'objective',
                action_date,
            )
        if 'notification' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['notification'],
                NotificationFrequencyModel,
                'notification',
                'objective',
                action_date,
            )


class KeyResultsModel(BaseModel):
    """Модель ключевых результатов OKR"""
    tps = []
    meta_exclude_fields = ['is_demo', 'created_at', 'mentions', 'ct',]
    tracker = FieldTracker(
        fields=(
            'description',
            'operator',
            'metrics',
            'base',
            'plan',
            'fact',
            'date_start',
            'date_end',
        )
    )
    track_prefix = 'key_result'

    objective = common_fields.CustomForeignKey(
        to='okr.ObjectivesModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Цель организации'),
        related_name='key_results',
        null=False,
        blank=False,
    )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание КР'),
    )
    operator = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Ответственный за КР'),
        related_name='operator_key_results',
        filter_info=ProfileFilterField(),
    )
    metrics = common_fields.CustomForeignKey(
        'okr.KeyResultMetricsModel',
        null=True,
        verbose_name=_('Метрика КР'),
        on_delete=CUSTOM_SET_NULL,
        related_name='key_results',
    )
    base = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Базовое значение'),
    )
    plan = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Планируемое значение'),
    )
    fact = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Фактическое значение'),
    )
    date_start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала')
    )
    date_end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )

    date_end_quarter = common_fields.CustomPositiveIntegerField(
        choices=QUARTER_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Квартал окончания'),
    )

    progress = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        verbose_name=_("Прогресс"),
        validators=(MaxValueValidator(limit_value=100),)
    )

    tasks = models.ManyToManyField(
        'tasks.TaskModel',
        through='KeyResultTasks',
        verbose_name=_('Задачи')
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')

    class Meta:
        verbose_name = _('Ключевой результат')
        verbose_name_plural = _('Ключевые результаты')

    def __str__(self):
        key_result_part = (
            f"{self.description[:27]}..." 
            if len(self.description) > 30 
            else self.description
        ) if self.description else "Без названия"

        date_end = (
            self.date_end.strftime("%Y-%m-%d") 
            if self.date_end 
            else "без даты"
        )
        return f"{key_result_part} (до {date_end})"

    def recalculate_progress(self):
        """Пересчитывает прогресс ключевого результата на основе base, plan и fact."""
        progress = calculate_key_result_progress(self.base, self.plan, self.fact)
        self.progress = int(progress)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.KeyResultsModelCreateSerializer
        elif action == 'retrieve':
            return serializers.KeyResultsModelDetailSerializer
        elif action in ('update', 'partial_update',):
            return serializers.KeyResultsModelUpdateSerializer
        else:
            return serializers.KeyResultsModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).prefetch_related('tasks')
        user_id = request.user.profile.pk
        objective_id = request.query_params.get('objective')
        if objective_id:
            try:
                objective = ObjectivesModel.objects.get(pk=objective_id)
            except ObjectivesModel.DoesNotExist:
                return qs.none()
            try:
                check_contractor_permission(user_id, objective.organization_id, ('create_okr', 'operator_okr'), None)
            except drf_exceptions.PermissionDenied:
                return qs.none()
            qs = qs.filter(objective_id=objective_id).order_by('date_start', 'date_end', '-created_at')
        else:
            okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)
            okr_organizations_tree = get_tree_departments_related_organizations(okr_organizations)
            qs = qs.filter(objective__organization__in=okr_organizations_tree)
        return qs

    def get_update_permission(self, request) -> bool:
        return self.objective.get_update_key_results_permission(request)

    def get_detail_permission(self, request) -> bool:
        return self.objective.get_detail_permission(request)

    def get_update_initiatives_permission(self, request) -> bool:
        """Может ли пользователь менять инициативы у ключевого результата."""
        user_id = request.user.profile.pk
        update_permission = self.get_update_permission(request)
        return update_permission or self.operator_id==user_id
    
    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
                # Пересчитываем прогресс связанной цели при деактивации
                if self.objective:
                    self.objective.recalculate_progress()
            elif value is True and self.is_active is False:
                self.deleted_at = None
                # Пересчитываем прогресс связанной цели при активации
                if self.objective:
                    self.objective.recalculate_progress()
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического пересчета прогресса."""
        if self.date_end:
            quarter_num = get_quarter(self.date_end)
            self.date_end_quarter = quarter_num
        else:
            self.date_end_quarter = None
        
        # Пересчитываем свой прогресс
        self.recalculate_progress()
        
        # Сохраняем ключевой результат
        super().save(*args, **kwargs)
        
        # Пересчитываем прогресс связанной цели
        if self.objective:
            self.objective.recalculate_progress()
            self.objective.save(update_fields=['progress'])

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
                'Создан ключевой результат',
            )
            return
        if not changed_fields:
            return
        if 'description' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'key_result__description',
                changed_fields['description'],
                self.description,
            )
        if 'operator' in changed_fields:
            operator_after = self.operator
            if operator_after:
                operator_id_after = self.operator.pk
            else:
                operator_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'key_result__operator',
                changed_fields['operator'],
                operator_id_after,
                self.description,
            )
        if 'metrics' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'key_result__metrics',
                changed_fields['metrics'],
                self.metrics,
                self.description,
            )
        if 'base' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'key_result__base',
                changed_fields['base'],
                self.base,
                self.description,
            )
        if 'plan' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'key_result__plan',
                changed_fields['plan'],
                self.plan,
                self.description,
            )
        if 'fact' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'key_result__fact',
                changed_fields['fact'],
                self.fact,
                self.description,
            )
        if 'date_start' in changed_fields:
            date_start_before = changed_fields['date_start']
            date_start_after = self.date_start
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'key_result__date_start',
                date_start_before,
                date_start_after,
                self.description,
            )
        if 'date_end' in changed_fields:
            date_end_before = changed_fields['date_end']
            date_end_after = self.date_end
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'key_result__date_end',
                date_end_before,
                date_end_after,
                self.description,
            )


class InitiativesModel(BaseModel):
    """Модель инициатив OKR"""
    tracker = FieldTracker(
        fields=(
            'related_object_type',
            'related_object',
            'title',
            'description',
            'operator',
            'date_start',
            'date_end',
            'is_completed',
        )
    )
    track_prefix = 'initiative'

    key_result = common_fields.CustomForeignKey(
        to='okr.KeyResultsModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Ключевой результат'),
        related_name='initiatives',
        null=False,
        blank=False,
    )
    related_object_type = common_fields.CustomForeignKey(
        to='okr.InitiativesRelatedObjectType',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=False,
        null=False,
        verbose_name=_('Источник')
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Ссылка на объект'),
        related_name='related_initiatives',
        null=True,
        blank=True,
    )
    title = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Название')
    )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )
    operator = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Ответственный'),
        related_name='operator_initiatives',
        filter_info=ProfileFilterField(),
    )
    date_start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала')
    )
    date_end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    is_completed = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Завершена'),
    )

    class Meta:
        verbose_name = _('Инициатива')
        verbose_name_plural = _('Инициативы')


    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.InitiativesModelCreateSerializer
        elif action == 'retrieve':
            return serializers.InitiativesModelDetailSerializer
        elif action in ('update', 'partial_update',):
            return serializers.InitiativesModelUpdateSerializer
        else:
            return serializers.InitiativesModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        user_id = request.user.profile.pk
        okr_organizations = contractors_where_user_has_permission(user_id, ('create_okr', 'operator_okr'), None)
        okr_organizations_tree = get_tree_departments_related_organizations(okr_organizations)
        qs = qs.filter(key_result__objective__organization__in=okr_organizations_tree)

        organization_id = request.query_params.get('organization')
        if organization_id:
            if uuid.UUID(organization_id) in okr_organizations_tree:
                qs = qs.filter(organization_id=organization_id)
            else:
                qs = qs.none()

        objective_id = request.query_params.get('objective')
        if objective_id:
            try:
                objective = ObjectivesModel.objects.get(pk=objective_id)
            except ObjectivesModel.DoesNotExist:
                qs = qs.none()
            else:
                if objective.organization_id in okr_organizations_tree:
                    qs = qs.filter(objective_id=objective_id)
                else:
                    qs = qs.none()

        key_result_id = request.query_params.get('key_result')
        if key_result_id:
            try:
                key_result = KeyResultsModel.objects.get(pk=key_result_id)
            except KeyResultsModel.DoesNotExist:
                qs = qs.none()
            else:
                if key_result.objective.organization_id in okr_organizations_tree:
                    qs = qs.filter(key_result_id=key_result_id)
                else:
                    qs = qs.none()
        return qs.order_by('created_at')

    def get_update_permission(self, request) -> bool:
        return self.key_result.get_update_initiatives_permission(request)

    def get_detail_permission(self, request) -> bool:
        return self.key_result.objective.get_detail_permission(request)

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
                'Создана инициатива',
            )
            return
        if not changed_fields:
            return
        if 'related_object_type' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['related_object_type'],
                InitiativesRelatedObjectType,
                'related_object_type',
                'initiative',
                action_date,
            )
        if 'related_object' in changed_fields:
            related_object_after = self.related_object
            if related_object_after:
                related_object_id_after = related_object_after.pk
            else:
                related_object_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'initiative__related_object',
                changed_fields['related_object'],
                related_object_id_after,
            )
        if 'title' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'initiative__title',
                changed_fields['title'],
                self.title,
            )
        if 'description' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'initiative__description',
                changed_fields['description'],
                self.description,
            )
        if 'operator' in changed_fields:
            operator_after = self.operator
            if operator_after:
                operator_id_after = self.operator.pk
            else:
                operator_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'initiative__operator',
                changed_fields['operator'],
                operator_id_after,
            )
        if 'date_start' in changed_fields:
            date_start_before = changed_fields['date_start']
            date_start_after = self.date_start
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'initiative__date_start',
                date_start_before,
                date_start_after,
            )
        if 'date_end' in changed_fields:
            date_end_before = changed_fields['date_end']
            date_end_after = self.date_end
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'initiative__date_end',
                date_end_before,
                date_end_after,
            )
        if 'is_completed' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'initiative__is_completed',
                self.is_completed,
            )


class ObjectiveVisor(models.Model):
    """Пользователи, которые могут просматривать приватную цель."""
    class Meta:
        unique_together = (('user', 'objective'),)
        verbose_name = _('Наблюдатель цели')
        verbose_name_plural = _('Наблюдатели целей')

    user = models.ForeignKey('users.ProfileModel',
                             null=True,
                             on_delete=CUSTOM_CASCADE, )
    objective = models.ForeignKey(ObjectivesModel,
                             null=True,
                             on_delete=CUSTOM_CASCADE,
                             related_name='objective_visors')

    @classmethod
    def get_label(cls):
        return cls._meta.label

    def __str__(self):
        return f'{self.user.full_name} {self.objective.objective}'


class KeyResultTasks(models.Model):
    """Задачи ключевого результата в качестве инициатив."""

    task = models.ForeignKey(
        'tasks.TaskModel',
        null=True,
        on_delete=CUSTOM_CASCADE,
        related_name='key_results'
    )
    key_result = models.ForeignKey(
        KeyResultsModel,
        null=True,
        on_delete=CUSTOM_CASCADE,
        related_name='key_result_tasks'
    )

    class Meta:
        unique_together = (('task', 'key_result'),)
        verbose_name = _('Задача ключевого результата')
        verbose_name_plural = _('Задачи ключевых результатов')
