import datetime
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from rest_framework import exceptions as drf_exceptions

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT
from change_history import utils as change_history_utils
from common import fields as common_fields
from common.models import BaseAbstractCatalog, BaseCatalog, BaseModel, BaseAbstractModel
from common.accounting_catalogs.fields import LocationFilterFakeField


class InvestProjectStageModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Стадия проекта')
        verbose_name_plural = _('Стадии проекта')
        ordering = ('sort', 'name',)


class InvestProjectCategoryModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ('name',)


class InvestProjectSubcategoryModel(BaseCatalog, BaseAbstractCatalog):
    category = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectCategoryModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('Категория'),
        related_name='subcategories'
    )
    dative_case = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        verbose_name=_('Дательный падеж'),
        help_text='(по) птицеводству, (по) орошению...',
    )

    class Meta:
        verbose_name = _('Подкатегория')
        verbose_name_plural = _('Подкатегории')
        ordering = ('name',)


class InvestProjectFundingSourceModel(BaseCatalog, BaseAbstractCatalog):
    short_name = common_fields.CustomCharField(
        verbose_name=_("Сокращенное наименование"),
        max_length=255,
        null=False,
        default='',
        blank=True
    )

    class Meta:
        verbose_name = _('Источник финансирования')
        verbose_name_plural = _('Источники финансирования')


class FundingSourceAndAmountModel(BaseModel):
    invest_project_info = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectInfoModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='funding_sources',
        verbose_name=_('Инвест. проект'),
    )
    funding_source = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectFundingSourceModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='funding_sources',
        verbose_name=_('Источник финансирования'),
    )
    amount = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Объем финансирования'),
        help_text='млн. тенге',
    )
    comment = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Комментарий'),
    )

    class Meta:
        verbose_name = _('Источник и объем финансирования')
        verbose_name_plural = _('Источники и объем финансирования')
        ordering = ('created_at',)


class InvestProjectMeasureUnitModel(BaseCatalog, BaseAbstractCatalog):
    name_short = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='',
        verbose_name=_("Краткое название"),
        help_text="кг, м, шт. и т. д.",
    )
    name_plural = common_fields.CustomCharField(
        max_length=127,
        null=False,
        default='',
        verbose_name=_("Множественное число"),
        help_text="килограммы, метры, штуки, и т. д.",
    )

    class Meta:
        verbose_name = _('Единица измерения')
        verbose_name_plural = _('Единицы измерения')
        ordering = ('name',)


class InvestProjectInfoModel(BaseModel):
    tracker = FieldTracker(
        fields=(
            'funds',
            'own_funds',
            'borrowed_funds',
            'bank_funds',
            'installation_stage',
            'jobs_permanent',
            'jobs_temporary',
            'project_capacity',
            'questions',
        )
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('Организация'),
        related_name='invest_projects_info',
    )
    location = common_fields.CustomForeignKey(
        to='accounting_catalogs.KATOCodesModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Местоположение'),
        related_name='invest_projects_info'
    )

    # Предприятие
    company_name = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Наименование предприятия'),
    )
    company_director_name = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('ФИО руководителя предприятия'),
    )
    company_phone = common_fields.CustomCharField(
        max_length=15,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Контактный номер телефона предприятия')
    )
    company_bin = common_fields.CustomCharField(
        max_length=12,
        null=False,
        blank=True,
        default='',
        verbose_name=_('БИН предприятия'),
    )

    project_name = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        default='',
        blank=False,
        verbose_name=_('Наименование проекта'),
    )
    stage = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectStageModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Стадия проекта'),
        related_name='invest_projects_info'
    )
    category = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectCategoryModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('Категория'),
        related_name='invest_projects_info'
    )
    subcategory = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectSubcategoryModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Подкатегория'),
        related_name='invest_projects_info'
    )
    project = common_fields.CustomForeignKey(
        to='workgroups.WorkgroupModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Проект'),
        related_name='invest_projects_info'
    )
    land_plot_is_allocated = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Земельный участок выделен')
    )
    types_of_products = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Виды продукции'),
    )
    comment = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Комментарий'),
    )
    foreign_investor_info = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Иностранный инвестор'),
    )
    fin_institute = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Финансовый институт'),
    )
    work_experience = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Опыт работы'),
    )
    funds = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Стоимость проекта, всего'),
        help_text='млн. тенге',
    )
    own_funds = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Собственные средства'),
        help_text='млн. тенге'
    )
    borrowed_funds = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Заемные средства'),
        help_text='млн. тенге'
    )
    bank_funds = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Средства банков второго уровня'),
        help_text='млн. тенге'
    )
    has_documentation = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('ПСД разработана'),
    )
    installation_stage = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Стадия СМР'),
        help_text='В процентах, до 100',
        validators=(MaxValueValidator(limit_value=100),)
    )
    infrastructure_info = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Проведенные инфраструктуры'),
    )
    cadaster = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Кадастровый номер ЗУ'),
    )
    jobs_permanent = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Постоянные рабочие места'),
    )
    jobs_temporary = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Временные рабочие места'),
    )
    project_capacity = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Мощность проекта'),
    )
    measure_unit = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectMeasureUnitModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('Единица измерения'),
        related_name='invest_projects_info',
    )
    plowed_field_quantity = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Пашни'),
        help_text='тыс. га',
    )
    pasture_quantity = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Пастбища'),
        help_text='тыс. га',
    )
    land_plot = common_fields.CustomDecimalField(
        null=False,
        default=0,
        decimal_places=2,
        max_digits=10,
        verbose_name=_('Земельный участок (гектар)')
    )
    questions = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Проблемные вопросы'),
    )
    date_start = common_fields.CustomDateField(
        null=True,
        blank=False,
        verbose_name=_('Дата начала'),
    )
    dead_line = common_fields.CustomDateField(
        null=True,
        blank=False,
        verbose_name=_('Планируемый срок ввода в эксплуатацию')
    )
    status = common_fields.CustomForeignKey(
        'invest_projects_info.InvestProjectStatusModel',
        to_field='code',
        null=False,
        default='draft',
        verbose_name=_('Статус'),
        on_delete=CUSTOM_PROTECT,
        related_name='invest_projects',
    )
    location_filter = LocationFilterFakeField()

    class Meta:
        verbose_name = _('Информация по инвест. проекту')
        verbose_name_plural = _('Информация по инвест. проектам')
        ordering = ('-created_at',)

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        if 'funds' in changed_fields:
            before = changed_fields['funds']
            after = self.funds
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__funds',
                before,
                after,
            )
        if 'own_funds' in changed_fields:
            before = changed_fields['own_funds']
            after = self.own_funds
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__own_funds',
                before,
                after,
            )
        if 'borrowed_funds' in changed_fields:
            before = changed_fields['borrowed_funds']
            after = self.borrowed_funds
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__borrowed_funds',
                before,
                after,
            )
        if 'bank_funds' in changed_fields:
            before = changed_fields['bank_funds']
            after = self.bank_funds
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__bank_funds',
                before,
                after,
            )
        if 'installation_stage' in changed_fields:
            before = changed_fields['installation_stage']
            after = self.installation_stage
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__installation_stage',
                before,
                after,
            )
        if 'jobs_permanent' in changed_fields:
            before = changed_fields['jobs_permanent']
            after = self.jobs_permanent
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__jobs_permanent',
                before,
                after,
            )
        if 'jobs_temporary' in changed_fields:
            before = changed_fields['jobs_temporary']
            after = self.jobs_temporary
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__jobs_temporary',
                before,
                after,
            )
        if 'project_capacity' in changed_fields:
            before = changed_fields['project_capacity']
            after = self.project_capacity
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__project_capacity',
                before,
                after,
            )
        if 'questions' in changed_fields:
            before = changed_fields['questions']
            after = self.questions
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'invest_projects_info__questions',
                before,
                after,
            )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (InvestProjectInfoModelCreateSerializer,
                                  InvestProjectInfoModelDetailSerializer,
                                  InvestProjectInfoModelListSerializer,
                                  InvestProjectInfoModelUpdateSerializer)
        if not action:
            return InvestProjectInfoModelListSerializer
        if action == 'create':
            return InvestProjectInfoModelCreateSerializer
        if action in ('update', 'partial_update',):
            return InvestProjectInfoModelUpdateSerializer
        if action == 'retrieve':
            return InvestProjectInfoModelDetailSerializer
        return InvestProjectInfoModelListSerializer

    @classmethod
    def get_table_columns(cls):
        return 'project_name', 'organization', 'category', 'subcategory', 'dead_line', 'company_name', 'location_filter'

    # @property
    # def statuses_visible_for_approve_permission(self):
    #     return ['on_check', 'on_rework', 'approved', 'change_requested', 'completed', 'archive']

    # def get_creator_organizations(self, request) -> set:
    #     """Возвращает множество организаций, где пользователь может создавать инвестпроекты.
    #     Включает только те организации, где явно назначена эта роль"""
    #     from contractor_permissions.utils import contractors_where_user_has_permission
    #     user = request.user.profile
    #     create_permission_id = InvestProjectPermissionTypeModel.objects.get(code='create')
    #     creator_organizations = contractors_where_user_has_permission(
    #         user.pk,
    #         'create_invest_projects_info',
    #         create_permission_id
    #         )
    #     return creator_organizations

    # def get_approver_organizations(self, request) -> set:
    #     """Возвращает множество организаций, где пользователь может одобрять инвестпроекты.
    #     Это организации, где у него есть роль одобрения инвестпроектов, а также НИЖЕСТОЯЩИЕ."""
    #     from contractor_permissions.utils import contractors_where_user_has_permission
    #     from users.utils import get_descendants_departments_related_organizations
    #     user = request.user.profile
    #     approve_permission_id = InvestProjectPermissionTypeModel.objects.get(code='approve')
    #     approver_organizations = contractors_where_user_has_permission(
    #         user.pk,
    #         'create_invest_projects_info',
    #         approve_permission_id
    #         )
    #     approver_organizations = get_descendants_departments_related_organizations(approver_organizations)
    #     return approver_organizations

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).select_related('location')
        if request:
            from users.utils import get_tree_departments_related_organizations
            from .utils import (get_invest_project_creator_organizations,
                                get_invest_project_approver_organizations)
            user = request.user.profile
            creator_organizations = get_invest_project_creator_organizations(request)
            approver_organizations = get_invest_project_approver_organizations(request)
            organizations = get_tree_departments_related_organizations(user.my_organizations)
            statuses_visible_for_approve_permission = ['on_check', 'on_rework', 'approved', 'change_requested', 'completed', 'archive']
            statuses_visible_for_organization_members = ['approved', 'change_requested', 'completed',]
            lookup = Q()
            lookup |= Q(organization_id__in=creator_organizations)
            lookup |= Q(organization_id__in=approver_organizations, status_id__in=statuses_visible_for_approve_permission)
            lookup |= Q(organization_id__in=organizations, status_id__in=statuses_visible_for_organization_members)
            qs = qs.filter(lookup)
        return qs.order_by('-created_at',)

    def get_update_status_permission(self, request) -> bool:
        """Разрешение на изменение статуса инвестпроекта"""
        from .utils import get_invest_project_approver_organizations
        user = request.user.profile
        new_status = request.data.get('status', '')
        approver_organizations = get_invest_project_approver_organizations(request)

        create_permission_id = InvestProjectPermissionTypeModel.objects.get(code='create')
        from contractor_permissions.utils import check_contractor_permission
        try:
            check_contractor_permission(user.pk, self.organization.pk, 'create_invest_projects_info', create_permission_id)
        except drf_exceptions.PermissionDenied:
            create_permission = False
        else:
            create_permission = True

        creator_permitted_from_statuses = ['draft', 'on_rework', 'approved']
        creator_permitted_to_statuses = ['on_check', 'change_requested', '']
        approver_permitted_from_statuses = ['on_check', 'approved', 'change_requested', 'completed', 'archive']
        approver_permitted_to_statuses = ['on_rework', 'approved', 'completed', 'archive', '']

        if (create_permission
            and self.status_id in creator_permitted_from_statuses
            and new_status in creator_permitted_to_statuses):
            return True
        elif (self.organization_id in approver_organizations
              and self.status_id in approver_permitted_from_statuses
              and new_status in approver_permitted_to_statuses):
            return True
        else:
            return False


    def get_delete_permission(self, request) -> bool:
        """Разрешение на удаление статуса инвестпроекта.
        Удалять могуть только пользователи с ролью создатель и только пока инвестпроект в статусе Черновик."""
        user = request.user.profile
        creator_can_delete_statuses = ['draft',]

        create_permission_id = InvestProjectPermissionTypeModel.objects.get(code='create')
        from contractor_permissions.utils import check_contractor_permission
        try:
            check_contractor_permission(user.pk, self.organization.pk, 'create_invest_projects_info', create_permission_id)
        except drf_exceptions.PermissionDenied:
            create_permission = False
        else:
            create_permission = True

        if create_permission and (self.status_id in creator_can_delete_statuses):
            return True
        else:
            return False

    def get_update_permission(self, request, is_add_project=False) -> bool:
        """Разрешение на редактирование инвестпроекта. Редактировать могут только пользователи
        с ролью создатель и только когда инвестпроект в статусах Черновик или На доработке."""
        user = request.user.profile
        creator_can_edit_statuses = ['draft', 'on_rework']

        create_permission_id = InvestProjectPermissionTypeModel.objects.get(code='create')
        from contractor_permissions.utils import check_contractor_permission
        try:
            check_contractor_permission(user.pk, self.organization.pk, 'create_invest_projects_info', create_permission_id)
        except drf_exceptions.PermissionDenied:
            create_permission = False
        else:
            create_permission = True

        if (create_permission and (self.status_id in creator_can_edit_statuses) or
           (create_permission and self.status_id == 'approved' and is_add_project)):
            return True
        else:
            return False

    def get_detail_permission(self, request) -> bool:
        from users.utils import get_descendants_departments_related_organizations
        from .utils import get_invest_project_approver_organizations
        user = request.user.profile
        create_permission_id = InvestProjectPermissionTypeModel.objects.get(code='create')

        from contractor_permissions.utils import check_contractor_permission
        try:
            check_contractor_permission(user.pk, self.organization.pk, 'create_invest_projects_info', create_permission_id)
        except drf_exceptions.PermissionDenied:
            create_permission = False
        else:
            create_permission = True

        approver_organizations = get_invest_project_approver_organizations(request)
        organizations = get_descendants_departments_related_organizations(user.my_organizations)
        statuses_visible_for_approve_permission = ['on_check', 'on_rework', 'approved', 'change_requested', 'completed', 'archive']
        statuses_visible_for_organization_members = ['approved', 'change_requested', 'completed',]

        if create_permission:
            return True
        elif (self.organization_id in approver_organizations
              and self.status_id in statuses_visible_for_approve_permission):
            return True
        elif (self.organization_id in organizations
              and self.status_id in statuses_visible_for_organization_members):
            return True
        else:
            return False


class InvestProjectPermissionTypeModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = _('Тип разрешения в инвест-проектах')
        verbose_name_plural = _('Типы разрешений в инвест-проектах')


class InvestProjectStatusModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )
    btn_title = common_fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=31,
        verbose_name=_('Название кнопки'),
    )

    class Meta:
        verbose_name = _("Статус инвестпроекта")
        verbose_name_plural = _("Статусы инвестпроектов")
    
    @classmethod
    def get_select_queryset(cls, request=None):
        """В зависимости от роли пользователя выдает разный список статусов
        инвестпроектов, которые доступны для просмотра."""
        queryset =  cls.objects.filter(is_active=True).order_by('sort', 'name', 'created_at')
        if request:
            from .utils import (get_invest_project_creator_organizations,
                                get_invest_project_approver_organizations)
            creator_organizations = get_invest_project_creator_organizations(request)
            approver_organizations = get_invest_project_approver_organizations(request)

            statuses_visible_for_approve_permission = ['on_check', 'on_rework', 'approved', 'change_requested', 'completed', 'archive']
            statuses_visible_for_organization_members = ['approved', 'change_requested', 'completed',]
            if creator_organizations:
                queryset = queryset # do nothing
            elif approver_organizations:
                queryset = queryset.filter(code__in=statuses_visible_for_approve_permission)
            else:
                queryset = queryset.filter(code__in=statuses_visible_for_organization_members)
        return queryset

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_order_param(cls):
        return ['sort', 'name',]

    @property
    def hex_color(self):
        colors = {
            'geekblue': '#597ef7',
            'purple': '#9254de',
            'orange': '#ffa940',
            'red': '#ff4d4f',
            'green': '#73d13d',
            'pink': '#FFC0CB',
            'cyan': '#36cfc9',
            'gray': '#808080',
        }
        return colors.get(self.color, '#f5f5f5')

    @property
    def depends(self):
        return list(self.depends_statuses.all().values_list('status_id', flat=True,))


class InvestProjectStatusDependsModel(BaseAbstractModel):
    status = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectStatusModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Статус инвестпроекта'),
    )
    next_status = common_fields.CustomForeignKey(
        to='invest_projects_info.InvestProjectStatusModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Статус инвестпроекта'),
        related_name='depends_statuses'
    )

    class Meta:
        verbose_name = _('Зависимость статуса')
        verbose_name_plural = _('Зависимости статусов')
        unique_together = (('status', 'next_status',),)