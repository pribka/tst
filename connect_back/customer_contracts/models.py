from decimal import Decimal

from django.db import models
from django.db.models import Q, OuterRef, Subquery, Value, CharField, F
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from rest_framework import exceptions as drf_exceptions

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE, CUSTOM_SET_NULL

from common import models as common_models
from common import fields as common_fields
from contractor_permissions.utils import contractors_where_user_has_permission


ALLOW_DEAL_LINKED_CONTRACT_DIRECT_EDIT = True


class CustomerContractStatusModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'external_uid', 'created_at', 'mentions', 'ct', ]

    external_uid = common_fields.CustomCharField(
        max_length=36,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Внешний ID'),
    )

    class Meta:
        verbose_name = _('Статус контракта')
        verbose_name_plural = _('Статусы контракта')


class CustomerContractModel(common_models.BaseModel):
    meta_exclude_fields = [
        'mentions', 'ct', 'author', 'created_at',
        'customer_card', 'external_customer', 'deal', 'legal_entity', 'source',
        'external_id', 'is_exists', 'amount', 'is_signed', 'date_start', 'date_end',
    ]
    status = common_fields.CustomForeignKey(
        to='customer_contracts.CustomerContractStatusModel',
        null=True,
        blank=True,
        related_name='customer_contracts',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус'),
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        related_name='customer_contracts',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация')
    )
    # customer_card - не использовать!
    customer_card = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardModel',
        null=True,
        blank=False,
        related_name='customer_contracts',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Карточка клиента')
    )
    customer_cards = models.ManyToManyField(
        'help_desk.CustomerCardModel',
        related_name='serviced_contracts',
        through='customer_contracts.CustomerContractServicedCardModel',
        through_fields=('customer_contract', 'customer_card'),
        verbose_name=_('Клиенты'),
        blank=True,
    )
    external_customer = common_fields.CustomForeignKey(
        to='catalogs.ExternalCustomerModel',
        null=True,
        blank=True,
        related_name='customer_contracts',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Клиент от внешнего сервиса')
    )

    deal = common_fields.CustomForeignKey(
        to='crm.DealModel',
        null=True,
        blank=True,
        related_name='customer_contracts',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Сделка'),
    )
    legal_entity = common_fields.CustomForeignKey(
        to='catalogs.LegalEntityModel',
        null=True,
        blank=True,
        related_name='customer_contracts',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Юридическое лицо'),
    )
    source = common_fields.CustomForeignKey(
        to='catalogs.Contractor1CAccessTokenModel',
        null=True,
        blank=True,
        related_name='customer_contracts',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Источник')
    )
    projects = models.ManyToManyField(
        'workgroups.WorkgroupModel',
        related_name='customer_contracts',
        through='customer_contracts.CustomerContractProjectModel',
        through_fields=('customer_contract', 'project'),
        verbose_name=_('Проекты'),
    )
    number = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Номер')
    )
    external_id = common_fields.CustomCharField(
        max_length=36,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Внешний ID'),
    )
    contract_date = common_fields.CustomDateField(
        null=True,
        verbose_name=_('Дата контракта')
    )
    hours_plan = common_fields.CustomDecimalField(
        default=0,
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Плановые часы'),
        validators=(MinValueValidator(0, message=_('The value can only be positive or 0')),)
    )
    hours_fact = common_fields.CustomDecimalField(
        default=0,
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Фактические часы'),
        validators=(MinValueValidator(0, message=_('The value can only be positive or 0')),)
    )
    is_signed = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Документ подписан')
    )
    is_exists = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('В наличии')
    )

    date_start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name='Дата начала',
    )
    date_end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания'
    )

    amount = common_fields.CustomDecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Сумма'
    )

    class Meta:
        verbose_name = _('Контракт')
        verbose_name_plural = _('Контракты')

    @classmethod
    def get_data_path(cls):
        return '/customer_contracts/'

    @classmethod
    def get_order_param(cls):
        return ['-updated_at', '-created_at']

    @classmethod
    def get_table_columns(cls):
        return [
            'number',
            'external_customer',
            'organization',
            'status',
            'contract_date',
            'date_start',
            'date_end',
            'amount',
            'hours_plan',
            'hours_fact',
            'updated_at',
        ]

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        annotations = {}
        names = set(requested_computed or [])
        outer_ref_column = kwargs.get('outer_ref_column')

        if 'projects_list' in names:
            projects_subquery = CustomerContractProjectModel.objects.filter(
                is_active=True,
                customer_contract_id=OuterRef('pk'),
                project__is_active=True,
            ).values('customer_contract_id').annotate(
                value=StringAgg(
                    'project__name',
                    delimiter=', ',
                    distinct=True,
                )
            ).values('value')[:1]
            annotations['projects_list'] = Coalesce(
                Subquery(projects_subquery, output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )

        if 'customer_cards_list' in names:
            customer_cards_subquery = CustomerContractServicedCardModel.objects.filter(
                is_active=True,
                customer_contract_id=OuterRef('pk'),
                customer_card__is_active=True,
            ).values('customer_contract_id').annotate(
                value=StringAgg(
                    'customer_card__name',
                    delimiter=', ',
                    distinct=True,
                )
            ).values('value')[:1]
            annotations['customer_cards_list'] = Coalesce(
                Subquery(customer_cards_subquery, output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )

        if 'root_organization' in names:
            from common.catalogs.models import ContractorRelationModel

            organization_pk_field = cls._meta.get_field('organization').target_field
            if outer_ref_column:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                contract_root_subquery = cls.objects.filter(
                    pk=OuterRef(outer_ref_column),
                ).annotate(
                    resolved_root_organization=Coalesce(
                        Subquery(root_organization_subquery),
                        F('organization_id'),
                        output_field=organization_pk_field,
                    )
                ).values('resolved_root_organization')[:1]
                annotations['root_organization'] = Subquery(
                    contract_root_subquery,
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
                "name": "projects_list",
                "type": "CharField",
                "verbose_name": _("Список проектов"),
            },
            {
                "name": "customer_cards_list",
                "type": "CharField",
                "verbose_name": _("Список клиентов"),
            },
            {
                "name": "root_organization",
                "type": "ForeignKey",
                "related_model": "catalogs.ContractorModel",
                "verbose_name": _("Головная организация"),
            },
        ]

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        from users.utils import get_descendants_departments_related_organizations
        queryset = cls.objects.filter(
            is_active=True,
        ).select_related(
            'status',
            'organization',
            'customer_card',
            'external_customer',
            'deal',
        ).order_by('-updated_at', '-created_at')
        if request is None:
            return queryset
        profile = request.user.profile
        allowed_by_permission = set(contractors_where_user_has_permission(
            profile.pk,
            ('admin', 'help_desk_admin', 'create_workgroup', 'workgroups_supervisor'),
            None,
        ))
        if not allowed_by_permission:
            return queryset.none()
        descendants = get_descendants_departments_related_organizations(allowed_by_permission, include_self=True)
        return queryset.filter(organization_id__in=descendants).distinct()

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            CustomerContractListSerializer,
            CustomerContractDetailSerializer,
            CustomerContractUpdateSerializer,
            CustomerContractCreateSerializer,
        )
        if action == 'retrieve':
            return CustomerContractDetailSerializer
        elif action in ('update', 'partial_update'):
            return CustomerContractUpdateSerializer
        elif action == 'create':
            return CustomerContractCreateSerializer
        else:
            return CustomerContractListSerializer

    def get_update_permission(self, request) -> bool:
        from users.utils import get_ancestor_departments_related_organizations
        organization_id = self.organization_id
        if not request or not organization_id:
            return False
        profile = request.user.profile
        ancestors = get_ancestor_departments_related_organizations((organization_id,), include_self=True)
        allowed_contractors = set(contractors_where_user_has_permission(
            profile.pk,
            ('admin', 'help_desk_admin', 'create_workgroup',),
            None,
        ))
        return not allowed_contractors.isdisjoint(ancestors)

    def get_detail_permission(self, request) -> bool:
        from users.utils import get_ancestor_departments_related_organizations
        organization_id = self.organization_id
        if not request or not organization_id:
            return False
        profile = request.user.profile
        ancestors = get_ancestor_departments_related_organizations((organization_id,), include_self=True)
        allowed_contractors = set(contractors_where_user_has_permission(
            profile.pk,
            ('admin', 'help_desk_admin', 'create_workgroup', 'workgroups_supervisor'),
            None,
        ))
        return not allowed_contractors.isdisjoint(ancestors)

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request) or self.external_id:
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


    def is_locked_by_deal(self):
        return bool(self.deal_id)

    def get_display_name(self, display=('external_customer', 'number', 'contract_date')):
        external_customer_name = ''
        if 'external_customer' in display:
            if self.external_customer_id and self.external_customer:
                external_customer_name = (
                    getattr(self.external_customer, 'full_name', None)
                    or getattr(self.external_customer, 'name', None)
                    or ''
                ).strip()
            elif self.customer_card_id:
                external_customer_name = (
                        getattr(self.customer_card, 'full_name', None)
                        or getattr(self.customer_card, 'name', None)
                        or ''
                ).strip()
            else:
                external_customer_name = ''
        number = ''
        if 'number' in display:
            number = (self.number or '').strip()
        contract_date_text = ''
        if 'contract_date' in display and self.contract_date:
            contract_date_text = self.contract_date.strftime('%d.%m.%Y') if self.contract_date else ''
        parts = []
        if external_customer_name:
            parts.append(external_customer_name)
        if number:
            parts.append(f'№{number}')
        if contract_date_text:
            parts.append(f'от {contract_date_text}')

        if parts:
            return ' '.join(parts)
        return str(self.pk)

    def __str__(self):
        return self.get_display_name()

    def clean(self):
        super().clean()
        if not self.pk:
            return
        if ALLOW_DEAL_LINKED_CONTRACT_DIRECT_EDIT:
            return

        persisted = type(self).objects.filter(pk=self.pk).values().first()
        if not persisted or not persisted.get('deal_id'):
            return

        for field in self._meta.concrete_fields:
            if field.name in ('updated_at',):
                continue
            if getattr(self, field.attname) != persisted.get(field.attname):
                raise ValidationError(_('Contract linked to a deal can only be edited through the deal.'))

    def recalculate_hours_fact(self):
        from help_desk.models import HelpDeskTicketModel
        from common.estimates.models import AccumulationRegister

        tasks = self.tasks.filter(is_active=True).values_list('pk', flat=True)
        analytics_keys = self.customer_contract_projects.all().values_list('pk', flat=True)
        tickets = HelpDeskTicketModel.objects.filter(
            analytics_key__in=analytics_keys,
            is_active=True
        ).values_list('pk', flat=True)
        tasks_hours = AccumulationRegister.objects.filter(
            registrar__in=tasks,
        ).aggregate(
            quantity_fact_sum=models.Sum('quantity_fact')
        )['quantity_fact_sum']
        if tasks_hours is None:
            tasks_hours = 0
        tickets_hours = AccumulationRegister.objects.filter(
            registrar__in=tickets
        ).aggregate(
            quantity_fact_sum=models.Sum('quantity_fact')
        )['quantity_fact_sum']
        if tickets_hours is None:
            tickets_hours = 0
        self.hours_fact = tasks_hours + tickets_hours
        self.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.clean()
        result = super().save(*args, **kwargs)
        from .utils import ensure_serviced_cards_for_customer_contract
        ensure_serviced_cards_for_customer_contract(self)
        if is_new and not self.deal_id:
            from .utils import ensure_deal_for_customer_contract
            ensure_deal_for_customer_contract(self)
        return result


class CustomerContractProjectModel(common_models.BaseAbstractModel):
    """Ключ аналитики для обращений хелпдеска. Связь с контрактом и проектом."""
    
    meta_exclude_fields = ['author', 'created_at',]

    customer_contract = common_fields.CustomForeignKey(
        to='customer_contracts.CustomerContractModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Контракт'),
        related_name='customer_contract_projects'
    )
    project = common_fields.CustomForeignKey(
        to='workgroups.WorkgroupModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Проект'),
        related_name='customer_contract_projects'
    )

    def __str__(self):
        contract_name = ''
        if self.customer_contract_id and self.customer_contract:
            contract_name = self.customer_contract.get_display_name(display=('number', 'contract_date',))
        project_name = ''
        if self.project_id and self.project:
            project_name = self.project.name or str(self.project.pk)
        if contract_name and project_name:
            return f'{contract_name} / {project_name}'
        return contract_name or project_name or str(self.pk)

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(
            is_active=True,
            customer_contract__is_active=True,
            project__is_active=True,
        ).select_related('customer_contract', 'customer_contract__external_customer', 'project')
        if request:
            contract_qs = CustomerContractModel.get_queryset(request)
            qs = qs.filter(customer_contract_id__in=contract_qs.values_list('pk', flat=True))

            contractor_id = request.query_params.get('contractor')
            if contractor_id:
                qs = qs.filter(customer_contract__organization_id=contractor_id)
        return qs

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.get_queryset(request)

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        qs = cls.get_select_queryset(request)
        if not text:
            return qs
        return qs.filter(
            Q(customer_contract__number__icontains=text) |
            Q(customer_contract__external_customer__name__icontains=text) |
            Q(customer_contract__external_customer__full_name__icontains=text) |
            Q(project__name__icontains=text)
        )

    def get_detail_permission(self, request) -> bool:
        if not self.customer_contract_id:
            return False
        return self.customer_contract.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        return False

    class Meta:
        verbose_name = _('Проект контракта')
        verbose_name_plural = _('Проекты контракта')


class CustomerContractServicedCardModel(common_models.BaseAbstractModel):
    
    meta_exclude_fields = ['author', 'created_at',]

    customer_contract = common_fields.CustomForeignKey(
        to='customer_contracts.CustomerContractModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Contract'),
        related_name='serviced_cards_relations'
    )
    customer_card = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Customer card'),
        related_name='serviced_contracts_relations'
    )

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(
            is_active=True,
            customer_contract__is_active=True,
            customer_card__is_active=True,
        ).select_related('customer_contract', 'customer_card')
        if request:
            contract_qs = CustomerContractModel.get_queryset(request)
            qs = qs.filter(customer_contract_id__in=contract_qs.values_list('pk', flat=True))
        return qs

    def get_detail_permission(self, request) -> bool:
        if not self.customer_contract_id:
            return False
        return self.customer_contract.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        if not self.customer_contract_id:
            return False
        return self.customer_contract.get_update_permission(request)

    class Meta:
        verbose_name = _('Contract serviced card')
        verbose_name_plural = _('Contract serviced cards')
        unique_together = (('customer_contract', 'customer_card',),)


class CustomerContractSubjectModel(common_models.BaseAbstractModel):
    """Строка предмета CRM-договора, согласованная из потребности интереса.

    Модель отделяет коммерчески согласованный предмет договора от исходной
    потребности интереса: в договор может попасть не все или с другой ценой.
    """

    meta_exclude_fields = ['author', 'created_at',]

    customer_contract = common_fields.CustomForeignKey(
        to='customer_contracts.CustomerContractModel',
        null=False,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Договор'),
        related_name='subject_items',
    )
    source_interest = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Интерес'),
        related_name='customer_contract_subject_items',
    )
    # CRM: связь с конкретной потребностью позволяет видеть, что именно из
    # интереса попало в договор, а что осталось только запросом клиента.
    source_need = common_fields.CustomForeignKey(
        to='tasks.TaskInterestNeedModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Потребность интереса'),
        related_name='customer_contract_subject_items',
    )
    goods = common_fields.CustomForeignKey(
        to='catalogs.NomenclatureModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Товар или услуга'),
        related_name='customer_contract_subject_items',
    )
    name = common_fields.CustomCharField(
        verbose_name=_('Наименование'),
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    name_short = common_fields.CustomCharField(
        max_length=127,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Краткое наименование'),
    )
    article_number = common_fields.CustomCharField(
        max_length=255,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Артикул')
    )
    base_measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_('Базовая ед. изм.'),
        on_delete=CUSTOM_PROTECT,
        related_name='customer_contract_subject_base_measure_unit',
    )
    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_('Единица измерения'),
        on_delete=CUSTOM_PROTECT,
        related_name='customer_contract_subject_measure_unit',
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        blank=False,
        default=1,
        verbose_name=_('Количество'),
        validators=(MinValueValidator(0),)
    )
    price = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=False,
        default=0,
        verbose_name=_('Цена договора'),
        validators=(MinValueValidator(0),)
    )
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=False,
        default=0,
        verbose_name=_('Сумма договора'),
        validators=(MinValueValidator(0),)
    )
    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )

    @classmethod
    def get_queryset(cls, request=None):
        # Доступ к предмету договора наследуется от самого договора.
        qs = cls.objects.filter(
            is_active=True,
            customer_contract__is_active=True,
        ).select_related(
            'customer_contract',
            'source_interest',
            'source_need',
            'goods',
            'measure_unit',
            'base_measure_unit',
        ).order_by('created_at')
        if request:
            contract_qs = CustomerContractModel.get_queryset(request)
            qs = qs.filter(customer_contract_id__in=contract_qs.values_list('pk', flat=True))
        return qs

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action in ('create',):
            return serializers.CustomerContractSubjectCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.CustomerContractSubjectUpdateSerializer
        return serializers.CustomerContractSubjectListSerializer

    def get_detail_permission(self, request) -> bool:
        if not self.customer_contract_id:
            return False
        return self.customer_contract.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        if not self.customer_contract_id:
            return False
        return self.customer_contract.get_update_permission(request)

    def save(self, *args, **kwargs):
        # Если строка привязана к номенклатуре, синхронизируем справочные поля,
        # чтобы предмет договора оставался читаемым даже при просмотре списком.
        goods = self.goods
        if goods:
            self.name = goods.name
            self.name_short = goods.name_short
            self.article_number = goods.article_number
            self.base_measure_unit = goods.base_measure_unit
            if not self.measure_unit:
                self.measure_unit = goods.base_measure_unit
        self.amount = (self.quantity or Decimal('0')) * (self.price or Decimal('0'))
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Предмет договора')
        verbose_name_plural = _('Предмет договора')
        ordering = ('created_at',)
