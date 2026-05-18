from django.db import models
from rest_framework import exceptions as drf_exceptions

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT
from common import fields as common_fields
from common.models import BaseAbstractCatalog, BaseCatalog, BaseModel
from common.validators import validate_text_to_json
from contractor_permissions.utils import check_contractor_permission

from .report_types.classes import get_report_type_instance


class AccountingReportStatusModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Статус отчёта'
        verbose_name_plural = 'Статусы отчётов'

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='',
        verbose_name='Цвет',
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(
            is_active=True
        ).order_by(
            'sort',
            'name',
            'created_at',
        )


class AccountingReportTypeModel(BaseCatalog, BaseAbstractCatalog):
    widget = common_fields.CustomCharField(
        verbose_name='Виджет',
        null=False,
        default='FinancePlanChange',
        max_length=100,
        blank=True
    )
    model_label = common_fields.CustomCharField(
        verbose_name='Имя модели',
        null=False,
        default='FPCReportModel',
        max_length=200,
        blank=True
    )
    info = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )

    class Meta:
        verbose_name = 'Тип отчёта'
        verbose_name_plural = 'Типы отчётов'

    @classmethod
    def get_queryset(cls, *args, **kwargs):
        return cls.objects.filter(
                is_active=True
            )

    def get_report_type_instance(self):
        return get_report_type_instance(self.code)


class AccountingReportSubtypeModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = 'Вид заявки'
        verbose_name_plural = 'Виды заявок'


class AccountingReportBaseModel(BaseModel):
    type = common_fields.CustomForeignKey(
        to='accounting_reports.AccountingReportTypeModel',
        to_field='code',
        null=False,
        blank=False,
        default='finance_plan_change',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Тип отчёта',
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        verbose_name='Организация',
        related_name='accounting_reports',
        on_delete=CUSTOM_PROTECT,
    )
    status = common_fields.CustomForeignKey(
        to='accounting_reports.AccountingReportStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='new',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Статус',
    )

    class Meta:
        verbose_name = 'Базовая модель отчёта'
        verbose_name_plural = 'Базовая модель отчётов'

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return
        user = request.user.profile
        my_organizations = user.my_organizations
        return cls.objects.filter(
            is_active=True,
            organization_id__in=my_organizations
        ).select_related(
            'organization',
            'status',
            'type',
        ).order_by(
            '-created_at',
        )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import AccountingReportBaseModelListSerializer

        return AccountingReportBaseModelListSerializer

    def get_update_permission(self, request) -> bool:
        if not request:
            return False
        if self.status_id in ['processed',]:
            return False
        user = request.user.profile

        try:
            check_contractor_permission(
                user.pk,
                self.organization_id,
                'add_accounting_report',
                self.type.id
            )
        except drf_exceptions.PermissionDenied:
            return False
        return True

    def get_detail_permission(self, request) -> bool:
        if not request:
            return False
        user = request.user.profile
        organizations = user.my_organizations
        if self.organization_id in organizations:
            return True
        return False

    @classmethod
    def get_table_columns(cls):
        return ['author', 'organization', 'status', 'type']

    @classmethod
    def get_report_type_instance(self):
        return get_report_type_instance(self.type_id)


class FPCReportModel(AccountingReportBaseModel):
    subtype = common_fields.CustomForeignKey(
        to='accounting_reports.AccountingReportSubtypeModel',
        to_field='code',
        null=False,
        blank=False,
        default='current',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Вид заявки',
    )
    number = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='Не указан',
        blank=False,
        verbose_name='Номер документа в учетной системе',
    )
    responsible_position = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='Не указана',
        blank=False,
        verbose_name='Должность ответственного',
    )
    responsible_name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='Не указано',
        blank=False,
        verbose_name='ФИО ответственного',
    )
    date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name='Дата формирования отчета',
    )
    consolidation_reports = models.ManyToManyField(
        to='consolidation.ReportModel',
        blank=True,
        related_name='ipf_proposal_reports',
        verbose_name='Отчеты консолидации'
    )

    class Meta:
        verbose_name = 'Отчёт по форме Заявка на ИПФ'
        verbose_name_plural = 'Отчёты по форме Заявка на ИПФ'

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return
        user = request.user.profile
        my_organizations = user.my_organizations
        return cls.objects.filter(
            is_active=True,
            organization_id__in=my_organizations
        ).select_related(
            'organization',
            'status',
            'subtype',
            'type',
        ).order_by(
            '-created_at',
        )

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.FPCReportModelDetailSerializer
        elif action == 'create':
            return serializers.FPCReportModelCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.FPCReportModelUpdateSerializer
        else:
            return serializers.FPCReportModelListSerializer

    # def get_update_permission(self, request):
    #     super().get_update_permission(request)
    #     if self.consolidation_reports.filter(
    #         is_active=True,
    #         ipf_proposal_reports=self,
    #         status_id__in=['approved', 'consolidated']
    #     ).exists():
    #         return False
    #     return True


class SpecificityStructureModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        unique=True,
        null=False,
        max_length=10,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name='Наименование',
        max_length=1023,
        null=False,
        default='',
        blank=True
    )

    class Meta:
        verbose_name = 'Структура специфики'
        verbose_name_plural = 'Структура специфики'

    def __str__(self):
        return f'Структура специфики. Код: {self.code}'


class ProposalItemModel(BaseModel):
    report = common_fields.CustomForeignKey(
        to=FPCReportModel,
        null=False,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Отчёт',
        related_name='proposal_items'
    )
    functional_group = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetFunctionalGroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Функциональная группа',
        related_name='proposal_items',
        null=True,
        blank=False,
    )
    functional_subgroup = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetFunctionalSubgroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Функциональная подгруппа',
        related_name='proposal_items',
        null=True,
        blank=False,
    )
    budget_program_administrator = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramAdministratorModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Администратор бюджетных программ',
        related_name='proposal_items',
        null=True,
        blank=False,
    )
    program = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Программа',
        related_name='proposal_items',
        null=True,
        blank=False,
    )
    subprogram = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetSubprogramModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Подпрограмма',
        related_name='proposal_items',
        null=True,
        blank=True,
    )
    specificity = common_fields.CustomForeignKey(
        to=SpecificityStructureModel,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Специфика',
        related_name='proposal_items',
        null=False,
        blank=False,
    )
    rationale = common_fields.CustomForeignKey(
        to='accounting_reports.RationaleModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Обоснование',
        related_name='proposal_items',
        null=False,
        blank=False,
    )
    january = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Январь',
    )
    february = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Февраль',
    )
    march = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Март',
    )
    april = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Апрель',
    )
    may = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Май',
    )
    june = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Июнь',
    )
    july = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Июль',
    )
    august = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Август',
    )
    september = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Сентябрь',
    )
    october = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Октябрь',
    )
    november = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Ноябрь',
    )
    december = common_fields.CustomDecimalField(
        default=0,
        max_digits=10,
        decimal_places=1,
        verbose_name='Декабрь',
    )

    class Meta:
        verbose_name = 'Заявка на ИПФ'
        verbose_name_plural = 'Заявки на ИПФ'

    def get_sum(self):
        return (
            self.january +
            self.february +
            self.march +
            self.april +
            self.may +
            self.june +
            self.july +
            self.august +
            self.september +
            self.october +
            self.november +
            self.december
        )


class RationaleModel(BaseModel):
    rationale = common_fields.CustomCharField(
        verbose_name='Обоснование',
        max_length=255,
        null=False,
        blank=False,
        unique=True
    )

    class Meta:
        verbose_name = 'Обоснование'
        verbose_name_plural = 'Обоснования'

    def __str__(self):
        return self.rationale


class IpfProposalConsolidationExtraModel(BaseModel):
    consolidation = common_fields.CustomOneToOneField(
        to='consolidation.ConsolidationModel',
        on_delete=CUSTOM_CASCADE,
        null=False,
        related_name='ipf_proposal_extra',
        verbose_name='Консолидация'
    )
    subtype = common_fields.CustomForeignKey(
        to='accounting_reports.AccountingReportSubtypeModel',
        to_field='code',
        null=False,
        blank=False,
        default='current',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Вид заявки',
    )
    date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name='Дата формирования отчета',
    )
    number = common_fields.CustomCharField(
        max_length=31,
        null=True,
        blank=True,
        verbose_name='Номер документа в учетной системе',
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            IpfProposalConsolidationExtraModelCreateSerializer,
            IpfProposalConsolidationExtraModelDetailSerializer)

        if action == 'retrieve':
            return IpfProposalConsolidationExtraModelDetailSerializer
        elif action == 'create':
            return IpfProposalConsolidationExtraModelCreateSerializer
        else:
            return IpfProposalConsolidationExtraModelDetailSerializer

    class Meta:
        verbose_name = 'Доп. поля консолидации для заявок на ИПФ'
        verbose_name_plural = 'Доп. поля консолидации для заявок на ИПФ'


class ChangeCalculationReportModel(AccountingReportBaseModel):
    start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name='Начало периода',
    )
    end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name='Конец периода',
    )
    responsible_position = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='Не указана',
        blank=False,
        verbose_name='Должность ответственного',
    )
    responsible_name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='Не указано',
        blank=False,
        verbose_name='ФИО ответственного',
    )
    consolidation_reports = models.ManyToManyField(
        to='consolidation.ReportModel',
        blank=True,
        related_name='change_calculation_reports',
        verbose_name='Отчеты консолидации'
    )
    is_accumulated = common_fields.CustomBooleanField(
        null=False,
        default=False,
    )

    class Meta:
        verbose_name = 'Отчёт по форме Расчет на ВИ в ИПФпП'
        verbose_name_plural = 'Отчёты по форме Расчет на ВИ в ИПФпП'

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return
        user = request.user.profile
        my_organizations = user.my_organizations
        return cls.objects.filter(
            is_active=True,
            organization_id__in=my_organizations
        ).order_by(
            '-created_at',
        )

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.ChangeCalculationModelDetailSerializer
        elif action == 'create':
            return serializers.ChangeCalculationModelCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.ChangeCalculationModelUpdateSerializer
        else:
            return serializers.ChangeCalculationModelListSerializer

    # def get_update_permission(self, request):
    #     super().get_update_permission(request)
    #     if self.consolidation_reports.filter(
    #         is_active=True,
    #         change_calculation_reports=self,
    #         status_id__in=['approved', 'consolidated']
    #     ).exists():
    #         return False
    #     return True


class ChangeCalculationItemModel(BaseModel):
    report = common_fields.CustomForeignKey(
        to=ChangeCalculationReportModel,
        null=False,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Отчёт',
        related_name='change_calculation_items'
    )
    functional_group = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetFunctionalGroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Функциональная группа',
        related_name='change_calculation_items',
        null=False,
        blank=False,
    )
    functional_subgroup = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetFunctionalSubgroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Функциональная подгруппа',
        related_name='change_calculation_items',
        null=False,
        blank=False,
    )
    budget_program_administrator = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramAdministratorModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Администратор бюджетных программ',
        related_name='change_calculation_items',
        null=False,
        blank=False,
    )
    program = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Программа',
        related_name='change_calculation_items',
        null=False,
        blank=False,
    )
    subprogram = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetSubprogramModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Подпрограмма',
        related_name='change_calculation_items',
        null=True,
        blank=True,
    )
    specificity = common_fields.CustomForeignKey(
        to=SpecificityStructureModel,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Специфика',
        related_name='change_calculation_items',
        null=False,
        blank=False,
    )
    rationale = common_fields.CustomForeignKey(
        to='accounting_reports.RationaleModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Обоснование',
        related_name='change_calculation_items',
        null=False,
        blank=False,
    )
    plan_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=0,
        verbose_name='План, количество'
    )
    plan_amount = common_fields.CustomDecimalField(
        default=0,
        max_digits=14,
        decimal_places=2,
        verbose_name='План, сумма',
    )
    actual_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=0,
        verbose_name='Факт, количество'
    )
    actual_amount = common_fields.CustomDecimalField(
        default=0,
        max_digits=14,
        decimal_places=2,
        verbose_name='Факт, сумма',
    )

    class Meta:
        verbose_name = 'Расчет на ВИ в ИПФпП'
        verbose_name_plural = 'Расчет на ВИ в ИПФпП'
