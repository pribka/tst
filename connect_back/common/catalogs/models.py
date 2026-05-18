import uuid
import re
import datetime
import secrets
import hashlib

from functools import lru_cache
from django.db import models, transaction, IntegrityError
from django.db.models import F, Subquery, OuterRef, Prefetch, Count, Sum, Value, Q
from django.db.models.functions import Coalesce
from django.core.validators import DecimalValidator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.utils import timezone
from django.contrib.gis.db import models as gis_models
from django.core.cache import cache


from rest_framework import exceptions as drf_exceptions

from django_q.tasks import async_task

from model_utils import FieldTracker

from rest_framework import exceptions as rest_exceptions

from mptt.models import MPTTModel, TreeForeignKey

from change_history import utils as change_history_utils

from bkz3.settings import (CUSTOM_CASCADE,
                           CUSTOM_DO_NOTHING,
                           CUSTOM_SET_NULL,
                           CUSTOM_PROTECT,
                           DEFAULT_CURRENCY_CODE,
                           DEFAULT_OFFER_TEXT,
                           FILTER_BY_ORGANIZATIONS)

from common.models import BaseCatalog, BaseAbstractCatalog, BaseAbstractModel, BaseModel, MetadataAbstractModel
from common import page_config
from common import fields as common_fields
from common.current_profile.middleware import get_current_authenticated_profile
from gallery.models import GalleryModel

from . import utils
from . import fields
from . import validators
from ..catalogs.utils import get_price_by_catalog_for_serializer


class CurrencyModel(BaseCatalog, BaseAbstractCatalog):
    icon = common_fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=7,
        verbose_name=_('Icon')
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def has_characteristics_plan(cls):
        return False

    @classmethod
    def get_queryset(cls, request=None):
        return super().get_queryset(request).order_by('sort', 'name',)

    class Meta:
        verbose_name = _('Currency')
        verbose_name_plural = _('Currencies')


def get_default_currency():
    return DEFAULT_CURRENCY_CODE


@lru_cache(maxsize=1)
def get_default_currency_object():
    return CurrencyModel.objects.get(code=DEFAULT_CURRENCY_CODE)


class PriceTypeModel(BaseCatalog, BaseAbstractCatalog):
    """Типы цен"""
    currency = common_fields.CustomForeignKey(
        to='catalogs.CurrencyModel',
        to_field='code',
        null=False,
        blank=False,
        default=get_default_currency,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Currency'),
        related_name='price_types',
    )
    default = models.BooleanField(verbose_name=_('Default'), default=False)

    @classmethod
    def get_data_path(cls):
        return '/catalogs/price_types/'

    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = _('Price type')
        verbose_name_plural = _('Price types')


class WarehouseModel(BaseCatalog, BaseAbstractCatalog):
    """Склады"""
    manager = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Warehouseman'),
    )
    address = common_fields.CustomCharField(
        max_length=5000,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Address'),
    )
    phone = common_fields.CustomCharField(
        max_length=127,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Phone')
    )
    delivery_point = common_fields.CustomForeignKey(
        to='catalogs.DeliveryPointModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Delivery point'),
        related_name='warehouses',
    )
    default_warehouse = common_fields.CustomBooleanField(default=False,
                                                         blank=False,
                                                         verbose_name='Склад по умолчанию')


    def save(self, *args, **kwargs):
        '''
        Если склад указан как склад по умолчанию сбрасываем default_warehouse
        в False у всех объектов, у которых оно установлено в True
        '''
        if self.default_warehouse:
            WarehouseModel.objects.filter(
                is_active=True,
                default_warehouse=True).update(default_warehouse=False)

        super(WarehouseModel, self).save(*args, **kwargs)

    @property
    def manager_phone(self):
        return getattr(self.manager, 'phone', '')

    @classmethod
    def get_data_path(cls):
        return '/catalogs/warehouses/'

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import AppWarehouseSerializer
        return AppWarehouseSerializer

    class Meta:
        verbose_name = _('Warehouse')
        verbose_name_plural = _('Warehouses')


class IsAvailableFakeField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'is_available'
    verbose_name = 'Есть в наличии'
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(remnant_sum__gt=0)
        else:
            return queryset.filter(Q(remnant_sum=0) | Q(remnant_sum__isnull=True))

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(Q(remnant_sum__gt=0) & Q(remnant_sum__isnull=False))
        else:
            return queryset.exclude(Q(remnant_sum=0) | Q(remnant_sum__isnull=True))


class PriceFakeField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.DecimalFormField()
    filter_info = page_config.DecimalFilterField()
    tp_info = page_config.TPDecimalColumn()
    filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}
    internal_type = "DecimalField"
    name = 'price'
    verbose_name = 'Цена'
    default = None
    blank = True
    validators = (DecimalValidator(max_digits=15, decimal_places=2),)
    decimal_places = 2
    max_digits = 15

    def to_filter(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.filter(price__gte=start)
        if end is not None:
            queryset = queryset.filter(price__lte=end)
        return queryset

    def to_exclude(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.exclude(price__gte=start)
        if end is not None:
            queryset = queryset.exclude(price__lte=end)
        return queryset


class WarehouseFakeField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = "В наличии на складе"
    name = 'warehouse'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'catalogs.WarehouseModel'
    model = 'catalogs.WarehouseModel'
    data_path = '/app_info/select_list/?model=catalogs.WarehouseModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(
            remnants__warehouse__in=value.get('value'), remnants__quantity__isnull=False, remnants__quantity__gt=0)
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(
            remnants__warehouse__in=value.get('value'), remnants__quantity__isnull=False, remnants__quantity__gt=0)
        return queryset


class GoodsTypeModel(BaseCatalog, BaseAbstractCatalog):
    """Типы товаров"""
    code = common_fields.CustomCharField(
        verbose_name=_('search code'),
        unique=True,
        null=False,
        default="0",
        max_length=8,
        blank=True,
        table_info=page_config.DefaultTableColumn(width=300)
    )
    color = common_fields.CustomCharField(
        max_length=100,
        default='geekblue',
        verbose_name='Цвет отображения'
    )

    class Meta:
        verbose_name = "Тип товара"
        verbose_name_plural = "Типы товара"


class MeasureUnitModel(BaseCatalog, BaseAbstractCatalog):
    name_short = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='',
        verbose_name="Краткое название",
        help_text="кг, м, шт. и т. д.",
    )
    name_plural = common_fields.CustomCharField(
        max_length=127,
        null=False,
        default='',
        verbose_name="Множественное число",
        help_text="килограммы, метры, штуки, и т. д.",
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MeasureUnitListSerializer
        return MeasureUnitListSerializer

    def __str__(self):
        return self.name_plural

    class Meta:
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"


class GoodsModel(BaseCatalog, BaseAbstractCatalog):
    """Товары"""
    name_short = common_fields.CustomCharField(
        max_length=127,
        null=False,
        blank=True,
        default='',
        verbose_name='Краткое наименование',
    )
    article_number = common_fields.CustomCharField(
        max_length=255,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Article number')
    )
    description = common_fields.CustomCharField(
        max_length=1023,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Description'),
    )
    price_by_catalog = common_fields.CustomDecimalField(  # Дефолтная цена для отображения на экране
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Price by catalog')
    )
    popularity = models.FloatField(
        verbose_name=_("popularity"),
        null=False,
        blank=True,
        default=0,
    )
    goods_type = common_fields.CustomForeignKey('catalogs.GoodsTypeModel',
                                                default='0',
                                                verbose_name="Тип номенклатуры",
                                                to_field="code",
                                                related_name="goods",
                                                on_delete=CUSTOM_PROTECT)

    base_measure_unit = common_fields.CustomForeignKey('catalogs.MeasureUnitModel',
                                                       null=True, blank=True,
                                                       verbose_name="Базовая ед. изм.",
                                                       # to_field="code",
                                                       # related_name="goods",
                                                       on_delete=CUSTOM_PROTECT)

    show_in_catalog = common_fields.CustomBooleanField(default=True,
                                                       verbose_name='Отображать в каталоге')
    is_available = IsAvailableFakeField()
    price = PriceFakeField()
    warehouse = WarehouseFakeField()

    def __str__(self):
        return f"{self.article_number} {self.name}"

    def get_price(self, price_type='default'):
        try:
            goods_price = GoodsPriceModel.objects.get(is_active=True, goods=self,
                                                      price_type_id=price_type).price
        except:
            goods_price = None
        return goods_price

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_select_queryset(request).filter(
            Q(name__icontains=text) | Q(article_number__icontains=text), is_active=True)

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.objects.filter(is_active=True)

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/catalogs/goods/'

    @classmethod
    def get_table_columns(cls):
        return 'status', 'name', 'article_number', 'is_available', 'price_by_catalog', 'warehouse', 'goods_type'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsModelCUDSerializer, GoodsModelListSerializer, GoodsModelRetrieveSerializer
        if action == 'list':
            return GoodsModelListSerializer
        elif action == 'retrieve':
            return GoodsModelRetrieveSerializer
        # elif action in ['create', 'update', 'partial_update']:
        #     return GoodsModelCUDSerializer
        else:
            return GoodsModelListSerializer

    @classmethod
    def get_queryset(cls, request=None, price_type_code=None):
        user = get_current_authenticated_profile()
        if not price_type_code:
            if request:
                contract_id = request.query_params.get('contract')
            else:
                contract_id = None
            if not contract_id:
                price_type = utils.get_user_price_type(user)
            else:
                try:
                    contract = ContractModel.objects.get(pk=contract_id)
                except ContractModel.DoesNotExist:
                    raise rest_exceptions.NotFound('Contract not found.')
                price_type = contract.price_type
            price_type_id = price_type.code
        else:
            price_type_id = price_type_code
        prices = GoodsPriceModel.objects.filter(is_active=True, goods=OuterRef('pk'), price_type_id=price_type_id)
        queryset = cls.objects.select_related('base_measure_unit',).prefetch_related(
            Prefetch('gallery', queryset=GalleryModel.objects.filter(is_active=True, is_main=True)),
        ).filter(is_active=True).annotate(
            price=Subquery(prices.values('price')),
            currency_name=Subquery(prices.values('price_type__currency__name')),
            currency_icon=Subquery(prices.values('price_type__currency__icon')),
            remnant_sum=Sum('remnants__quantity'),
            in_cart=Count('shopping_carts', Q(shopping_carts__user=user))
        )
        return queryset

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        data = super().get_filter_fields(exclude, request)
        for each in data:
            if each.get('name') == 'name':
                each['verbose_name'] = 'Наименование продукции'
        return data

    def get_detail_permission(self, request) -> bool:
        return not request.user.is_anonymous

    class Meta:
        verbose_name = pgettext_lazy('singular', 'Goods')
        verbose_name_plural = pgettext_lazy('plural', 'Goods')


class NomenclatureModel(GoodsModel):
    """Номенклатура материалов (товаров) и услуг организации."""
    contractor = common_fields.CustomForeignKey(
        to='ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='nomenclatures',
        verbose_name=_('Организация')
    )

    class Meta:
        verbose_name = _('Номенклатура')
        verbose_name_plural = _('Номенклатура')

    def __str__(self):
        base_measure_unit_name_plural = getattr(self.base_measure_unit, 'name_plural', '')
        article_number = f" - {self.article_number}" if self.article_number else ''
        return f"{self.name}, {base_measure_unit_name_plural}{article_number}"

    @classmethod
    def get_queryset(cls, request=None, price_type_code=None):
        qs = cls.objects.filter(is_active=True)
        if request:
            try:
                query_params = request.query_params
            except AttributeError:
                query_params = request.GET
            user = request.user.profile
            my_organizations = user.my_organizations
            qs = qs.filter(contractor_id__in=my_organizations)
            contractor_id = query_params.get('contractor')
            if contractor_id:
                qs = qs.filter(contractor_id=contractor_id)
        else:
            qs = qs.none()
        return qs

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import AppNomenclatureSerializer
        return AppNomenclatureSerializer


class GoodsBarcodeModel(BaseAbstractModel):
    goods = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=pgettext_lazy('singular', 'Goods'),
        null=True,
        blank=False,
        related_name='barcodes',
    )
    barcode = common_fields.CustomCharField(
        max_length=127,
        default='',
        null=False,
        unique=True,
    )

    class Meta:
        verbose_name = _('Barcode')
        verbose_name_plural = _('Barcodes')


class GoodsCategoryModel(BaseCatalog, MPTTModel, BaseAbstractCatalog):
    parent = TreeForeignKey('self', on_delete=CUSTOM_PROTECT, null=True, blank=True, related_name='children')
    level = models.IntegerField(default=0)
    lft = models.IntegerField(default=0)
    rght = models.IntegerField(default=0)
    tree_id = models.IntegerField(default=0)
    goods = models.ManyToManyField('catalogs.GoodsModel',
                                   related_name='category',
                                   verbose_name='Товары',
                                   blank=True)

    class Meta:
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товаров'

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/catalogs/goods_category/'

    @classmethod
    def get_table_columns(cls):
        return 'name', 'code'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsCategoryListSerializer, GoodsCategoryShortSerializer
        if action == 'list':
            return GoodsCategoryListSerializer
        elif action == 'retrieve':
            return GoodsCategoryShortSerializer
        # elif action in ['create', 'update', 'partial_update']:
        #     return GoodsCategoryCUDSerializer
        else:
            return GoodsCategoryShortSerializer


class ContractModel(BaseCatalog, BaseAbstractCatalog):
    """Соглашение"""
    price_type = common_fields.CustomForeignKey(
        to='catalogs.PriceTypeModel',
        to_field='code',
        verbose_name=_('Price type'),
        on_delete=CUSTOM_PROTECT,
        null=False,
        default='default',
        related_name='contracts',
    )
    payment = common_fields.CustomForeignKey(
        to='catalogs.TypeOrderPaymentModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_SET_NULL,
        related_name='contracts',
        verbose_name=_('Type order payment')
    )
    is_individual = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Индивидуальное соглашение',
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractModelListSerializer
        return ContractModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        user = get_current_authenticated_profile()
        contractors = user.contractors.all()
        return cls.objects.select_related('price_type__currency').filter(
            Q(Q(contractors__contractor__in=contractors) | Q(is_individual=False)),
            is_active=True

        ).order_by(
            '-contractors__default', 'name'
        ).distinct()

    @classmethod
    def get_filtered_select_queryset(cls, contractor_id, request=None):
        return cls.get_queryset(request).filter(
            is_active=True, contractors__contractor_id=contractor_id).exclude(code='default')

    @classmethod
    def is_enum(cls):
        return True


class TypeOrderPaymentModel(BaseModel):
    payment_form = common_fields.CustomForeignKey(
        to='catalogs.PaymentFormModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_("Payment form"),
        null=False,
        default='any',
        blank=False,
    )

    class Meta:
        verbose_name = _("Type order payment")
        verbose_name_plural = _("Types order payment")

    def __str__(self):
        return f'{self.pk} {self.payment_form}'


class PaymentStageModel(BaseModel):
    owner = common_fields.CustomForeignKey(
        to='catalogs.TypeOrderPaymentModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_("Type order payment"),
        related_name='stages',
    )
    payment_option = common_fields.CustomForeignKey(
        to='catalogs.PaymentOptionModel',
        to_field='code',
        null=False,
        blank=False,
        default='advance_before_collateral',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Payment option'),
    )
    payment_percent = common_fields.CustomDecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
        default=100,
        blank=False,
        verbose_name=_('Payment percent')
    )
    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=False,
        default=1,
        verbose_name=_('Days duration'),
        help_text="Дней",
    )

    class Meta:
        verbose_name = _('Payment stage')
        verbose_name_plural = _('Payment stages')
        ordering = ('sort',)


class ContractorModel(BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel):
    """Контрагенты (Клиент)"""
    meta_exclude_fields = ['author', 'code',
        'profiles', 'tariffs', 'curator', 'contact_person', 'budget_program_administrator', 'code_gu', 'is_carrier',
        'phone', 'email', 'warehouses', 'delivery_points', 'logo', 'is_archived', 'doc_prefix',
        'is_demo', 'has_demo_data', 'name', 'full_name', 'created_at', 'mentions', 'ct', 'external_id',]

    external_id = common_fields.CustomCharField(
        max_length=36,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Внешний ID'),
    )

    profiles = models.ManyToManyField(
        to='users.ProfileModel',
        through='catalogs.ContractorProfileModel',
        through_fields=('contractor', 'user'),
        verbose_name=_('Individuals')
    )
    tariffs = models.ManyToManyField(
        to='billing.TariffModel',
        through='billing.ContractorTariffModel',
        through_fields=('contractor', 'tariff'),
        verbose_name=_('Тарифы'),
    )
    curator = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Ответственный сотрудник"),
        related_name="curator_contractors",
    )
    contact_person = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Контактное лицо"),
        related_name="contractor_contact",
    )
    budget_program_administrator = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramAdministratorModel',
        on_delete=CUSTOM_SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Администратор бюджетных программ'),
        related_name='budget_admin_contractors',
    )
    code_gu = common_fields.CustomCharField(
        max_length=10,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Код ГУ')
    )
    full_name = common_fields.CustomCharField(
        max_length=511,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Полное наименование')
    )
    is_carrier = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Компания перевозчик')
    )
    phone = models.CharField(max_length=20, default='', blank=True)
    email = models.CharField(max_length=255, default='', blank=True)
    warehouses = models.ManyToManyField(
        to='catalogs.WarehouseModel',
        through='catalogs.WarehouseContractorModel',
        verbose_name=_('Склады'),
    )

    delivery_points = models.ManyToManyField(
        'catalogs.DeliveryPointModel',
        through='catalogs.ContractorDeliveryPointModel',
        blank=True,
        verbose_name=_('Точки доставки')
    )
    logo = common_fields.CustomCharField(
        max_length=63,
        null=False,
        blank=True,
        default='',
        verbose_name="Логотип"
    )
    is_archived = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Архивный'
    )
    doc_prefix = models.CharField(default='', max_length=4, blank=True)
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')
    has_demo_data = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Установлены демо-данные')

    orders_in_progress_filter = fields.OrdersInProgressField()
    last_order_date_filter = fields.LastOrderDateField()
    contractor_status_filter = fields.ContractorSatusField()

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_data_path(cls):
        return '/catalogs/contractors/'

    @classmethod
    def get_table_columns(cls):
        return 'name', 'contractor_status_filter'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorModelSerializer, ContractorModelUpdateSerializer
        from .serializers import ContractorModelDetailSerializer
        if action in ['update', 'partial_update']:
            return ContractorModelUpdateSerializer
        if action == 'retrieve':
            return ContractorModelDetailSerializer
        return ContractorModelSerializer

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['table_columns'].append({'cellRenderer': 'DefaultRow',
                                      'field': 'profiles',
                                      'headerName': 'Физлица',
                                      'sortable': False,
                                      'width': 300})
        return data

    @classmethod
    def get_queryset(cls, request=None):
        user = get_current_authenticated_profile()
        if user.has_full_access_to_order_editing or user.is_support:
            return cls.objects.filter(is_active=True).prefetch_related(
                'my_tasks',
                'my_tasks__event_calendars',
                'my_tasks__event_calendars__events',
            )
        else:
            return (
                user.contractors.filter(is_active=True).prefetch_related(
                    'my_tasks',
                    'my_tasks__event_calendars',
                    'my_tasks__event_calendars__events',
                ) | cls.objects.filter(
                    is_carrier=True,
                    is_active=True
                    ).prefetch_related(
                        'my_tasks',
                        'my_tasks__event_calendars',
                        'my_tasks__event_calendars__events',
                    )
                ).distinct()

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_select_queryset(request).filter(
            Q(name__icontains=text) | Q(full_name__icontains=text)
        ).order_by('name', 'created_at')

    @classmethod
    def get_request_approval_select_queryset(cls, profile):
        permission_type_ids = ("request_approvals_manager", "request_approvals_admin")

        from common.utils import get_my_access_groups, use_access_groups
        from contractor_permissions import models as contractor_permission_models
        from users.utils import get_descendants_departments_related_organizations

        if use_access_groups(profile.pk):
            my_access_groups_id = get_my_access_groups(profile)
            permission_access_groups_id = contractor_permission_models.AccessGroupAppSectionRoleThrough.objects.filter(
                access_group__in=my_access_groups_id,
                app_section_role__permission_type_id__in=permission_type_ids,
            ).values_list('access_group', flat=True)
            permission_contractor_ids = contractor_permission_models.AccessGroupMemberThroughModel.objects.filter(
                access_group__in=permission_access_groups_id,
                member__user=profile,
            ).values_list('member__contractor', flat=True)
        else:
            permission_contractor_ids = contractor_permission_models.ContractorPermissionModel.objects.filter(
                contractor_permission_role__contractor__in=profile.my_organizations,
                contractor_permission_role__is_active=True,
                contractor_permission_role__contractor_profiles__user=profile,
                permission_type_id__in=permission_type_ids,
            ).values_list('contractor_permission_role__contractor', flat=True)

        permission_contractor_ids = get_descendants_departments_related_organizations(
            permission_contractor_ids,
            include_self=True,
        )
        return cls.objects.filter(is_active=True, pk__in=permission_contractor_ids)

    @classmethod
    def get_snapshot(cls, id):
        instance = cls.objects.filter(pk=id).first()
        if not instance:
            return {}
        return {
            "id": str(instance.pk),
            "repr": instance.name or instance.full_name or str(instance.pk),
            "name": instance.name,
            "full_name": instance.full_name,
        }

    @classmethod
    def get_select_queryset(cls, request=None):
        queryset = cls.get_queryset(request)

        if request:
            field_name = request.query_params.get('field', '')
            user = request.user.profile

            # Для выпадающего списка организаций техподдержки в фильтрах хелпдеска
            if field_name in ('help_desk_ticket_org_admin_filter', 'org_admin_filter',):
                from contractor_permissions.utils import contractors_where_user_has_permission
                permission_type_ids = ('help_desk_manager', 'help_desk_admin', 'help_desk_supervisor')
                permission_contractor_ids = contractors_where_user_has_permission(user.pk, permission_type_ids, None)
                queryset = queryset.filter(pk__in=permission_contractor_ids)

            if field_name in ('request_approval_organization', 'workflow_request_organization'):
                queryset = cls.get_request_approval_select_queryset(user)

            is_support = user.is_support
            if field_name in ('organization', 'user_organization_filter') and FILTER_BY_ORGANIZATIONS and not is_support:
                from users.utils import get_tree_departments_related_organizations
                queryset = cls.objects.filter(
                    is_active=True, pk__in=get_tree_departments_related_organizations(
                        user.my_organizations
                    )
                )
            page_name = request.query_params.get('page_name')
            if page_name and page_name.endswith('customer_contracts.CustomerContractModel'):
                # Для фильтра списка контрактов
                from customer_contracts.models import CustomerContractModel
                customer_contracts_contractors = CustomerContractModel.get_queryset(
                    request
                ).order_by('organization').values_list('organization', flat=True).distinct('organization')
                queryset = queryset.filter(pk__in=customer_contracts_contractors)

        return queryset.order_by('name', 'created_at',)

    def get_select_list_logo_url(self):
        from common.utils import get_logo_url
        return get_logo_url(self.logo) if self.logo else ''

    @property
    def delivery_addresses_str(self) -> str:
        """Возвращает строку с адресами доставки. Используется поисковой системой."""
        return " ".join(list(self.delivery_points.filter(
            is_active=True
        ).order_by('-created_at').values_list('name', flat=True))).strip()

    @property
    def member_inn(self) -> str:
        """Используется поисковой системой."""

        contractor_member = self.contractor_members.filter(
            is_active=True
        ).order_by(
            '-created_at'
        ).first()
        if contractor_member:
            return contractor_member.inn
        return ''

    @property
    def last_delivery_address(self) -> str:
        last_delivery_point = self.delivery_points.filter(
            is_active=True).order_by('-created_at').first()
        if last_delivery_point:
            return last_delivery_point.name
        else:
            return ''

    @property
    def only_digits_phone(self) -> str:
        if self.phone:
            return re.sub(r'\D', '', self.phone)
        else:
            return ''

    @property
    def last_delivery_point(self) -> str:
        last_delivery_point = self.delivery_points.filter(
            is_active=True).order_by('-created_at').first()
        if last_delivery_point:
            return last_delivery_point.id
        else:
            return ''

    @property
    def contact_person_name(self) -> str:
        if self.contact_person:
            return self.contact_person.user.full_name
        else:
            contact_person = self.contractor_profile.filter( # noqa
                is_active=True,
                director=True).first()
            if contact_person:
                contact_person_user = contact_person.user
                if contact_person_user:
                    return contact_person_user.full_name
                else:
                    return ''
            else:
                return ''

    def get_detail_permission(self, request) -> bool:
        if self.is_carrier:
            return True
        user = request.user.profile
        if user.has_full_access_to_order_editing:
            return True
        if user.contractors.filter(is_active=True, pk=self.pk).exists():
            return True
        return False

    def get_update_permission(self, request) -> bool:
        if FILTER_BY_ORGANIZATIONS:
            user = request.user.profile
            try:
                contractor_profile = user.contractor_profile.get(contractor=self)
            except ObjectDoesNotExist:
                return False
            if contractor_profile.director:
                return True
            from contractor_permissions.utils import check_contractor_permission
            try:
                check_contractor_permission(user.pk, self.pk, 'admin', None)
            except drf_exceptions.PermissionDenied:
                return False
            else:
                return True
        return request.user.profile.has_full_access_to_order_editing

    def save(self, *args, **kwargs):
        if self.pk:
            cache.set('ContractorModelShortSerializer_' + str(self.pk), None)
        super().save(*args, **kwargs)

    @property
    def contractor_parent(self):
        relation = self.contractor_relations.filter(
            relation_type_id='structural_division',
        ).order_by('-created_at').first()
        return relation.contractor_parent if relation else None

    @property
    def director(self):
        contractor_profile = self.contractor_profile.filter(director=True).first()
        if contractor_profile:
            return contractor_profile.user
        else:
            return None


class ContractorRelationModel(BaseModel):
    contractor_root = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Корневой контрагент',
        null=True,
        blank=True,
        editable=False,
        related_name='contractor_relations_root',
    )
    contractor_parent = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Родительский контрагент',
        null=True,
        blank=False,
        related_name='contractor_relations_parent',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Контрагент',
        null=True,
        blank=False,
        related_name='contractor_relations',
    )
    relation_type = common_fields.CustomForeignKey(
        to='catalogs.ContractorRelationTypeModel',
        to_field='code',
        null=False,
        default='structural_division',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Тип отношения',
        related_name='contractor_relations'
    )

    def get_root(self):
        relation_type = self.relation_type
        contractor = self.contractor_parent

        try:
            relation_contractor_parent = ContractorRelationModel.objects.get(
                contractor=contractor,
                relation_type=relation_type,
                is_active=True,
            )
        except ContractorRelationModel.DoesNotExist:
            return contractor
        else:
            return relation_contractor_parent.contractor_root

    def get_descendants(self):
        relation_type = self.relation_type
        contractor_id = self.contractor.pk
        contractors_seed = {contractor_id, }
        result = [contractor_id]
        while True:
            contractors = set(ContractorRelationModel.objects.filter(
                contractor_parent_id__in=contractors_seed,
                relation_type=relation_type,
            ).values_list('contractor', flat=True))
            result = result + list(contractors)
            if len(contractors) == 0:
                result = set(result)
                return result
            contractors_seed = contractors

    def get_children(self):
        relation_type = self.relation_type
        children = ContractorRelationModel.objects.filter(
            contractor_parent=self.contractor,
            relation_type=relation_type,
        )
        return children

    def set_root(self):
        new_root = self.get_root()
        descendants_id = self.get_descendants()
        ContractorRelationModel.objects.filter(contractor__in=descendants_id).update(contractor_root=new_root)

    def check_ring(self):
        descendants = self.get_descendants()
        if self.contractor_parent.pk in descendants:
            raise ValidationError({"message": "Невозможное действие: образуется кольцо."})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.relation_type.code == 'structural_division':
                self.check_ring()
            super().save(*args, **kwargs)
            if self.relation_type.code == 'structural_division':
                self.set_root()

    def delete(self, using=None, keep_parents=False):
        if self.relation_type.code == 'structural_division':
            with transaction.atomic():
                children = self.get_children()
                result = super().delete(using, keep_parents)
                for each in children:
                    each.set_root()
            return result
        else:
            return super().delete(using, keep_parents)

    class Meta:
        verbose_name = 'Связь контрагентов'
        verbose_name_plural = 'Связи контрагентов'
        unique_together = (('contractor_parent', 'contractor', 'relation_type'),)


class ContractorRelationTypeModel(BaseCatalog, BaseAbstractCatalog):
    name_parent = common_fields.CustomCharField(
        verbose_name="Название родителя",
        max_length=255,
        null=False,
        default='',
        blank=True,
        table_info=page_config.DefaultTableColumn(width=300)
    )
    notify_name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    notify_name_parent = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorRelationTypeModelListSerializer
        return ContractorRelationTypeModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort', 'name', '-created_at',)

    def __str__(self):
        return f"{self.name} - {self.name_parent}"

    class Meta:
        verbose_name = 'Тип отношения контрагентов'
        verbose_name_plural = 'Типы отношения контрагентов'


class ContractorDepartmentModel(BaseCatalog, BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'code', 'contractor_profiles', 'phone', 'email', 'created_at', 'mentions', 'ct']

    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        related_name='departments',
        verbose_name='Организация',
        help_text='ContractorModel',
    )
    contractor_profiles = models.ManyToManyField(
        to='catalogs.ContractorProfileModel',
        verbose_name='Участники организации',
        blank=True,
        help_text='ContractorProfileModel, должны быть участниками contractor',
        related_name='departments',
        through='catalogs.ContractorDepartmentProfileModel'
    )
    full_name = common_fields.CustomCharField(
        max_length=511,
        null=True,
        blank=True,
        default='',
        verbose_name='Полное наименование'
    )
    phone = models.CharField(max_length=20, default='', blank=True)
    email = models.CharField(max_length=255, default='', blank=True)

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('name',)


class ContractorDepartmentProfileModel(BaseAbstractModel):
    contractor_profile = common_fields.CustomForeignKey(
        to='catalogs.ContractorProfileModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Участник организации',
        null=True,
        blank=False,
        related_name='department_profiles'
    )
    department = common_fields.CustomForeignKey(
        to='catalogs.ContractorDepartmentModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Отдел',
        null=True,
        blank=False,
        related_name='department_profiles'
    )
    director = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Руководитель'
    )

    class Meta:
        verbose_name = 'Участник отдела'
        verbose_name_plural = 'Участники отдела'
        unique_together = (('department', 'contractor_profile',),)


class ContractorMemberModel(BaseCatalog, BaseAbstractCatalog):
    """Контрагент"""
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        related_name='contractor_members',
    )
    inn = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name='Идентификационный номер налогоплательщика, ИНН',
        # help_text='ИНН юридического лица должен быть последовательностью '
        #           'из 10 арабских цифр',
        # validators=(validators.inn_validator, )
    )
    full_name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное наименование',
    )
    kpp = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Код причины постановки, КПП',
        # help_text='КПП юридического лица должен быть последовательностью '
        #           'из 9 арабских цифр',
        # validators=(validators.kpp_validator, )
    )
    ogrn = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Основной государственный регистрационный номер, ОГРН',
        # help_text='ОГРН юридического лица должен быть последовательностью '
        #           'из 13 арабских цифр, первая цифра 1 или 5',
        # validators=(validators.ogrn_validator, )
    )
    ogrnip = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Основной государственный регистрационный номер '
                     'индивидуального предпринимателя, ОГРНИП',
        # help_text='ОГРН индивидуального предпринимателя должен быть '
        #           'последовательностью из 15 арабских цифр, '
        #           'первая цифра 3',
        # validators=(validators.ogrnip_validator, )
    )
    okpo = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Общероссийский классификатор предприятий '
                     'и организаций, ОКПО',
        # help_text='ОКПО должен быть последовательностью из 8 арабских цифр '
        #           'для организаций и из 10 арабских цифр для индивидуальных '
        #           'предпринимателей',
        # validators=(validators.okpo_validator, )
    )
    legal_address = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Юридический адрес',
    )
    postal_address = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Почтовый адрес',
    )
    phone = common_fields.CustomCharField(
        max_length=20,
        null=False,
        default='',
        blank=True,
        verbose_name='Телефон',
    )
    email = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name='Электронная почта',
    )
    director_position = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name='Должность руководителя',
    )
    director_position_genitive = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name='Должность руководителя в родительном падеже',
    )
    director_full_name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное ФИО руководителя',
    )
    director_full_name_genitive = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное ФИО руководителя в родительном падеже',
    )

    @property
    def bank_requisites(self):
        return self.requisites.filter(is_active=True).order_by('-created_at').first()

    @property
    def director_short_name(self):
        full_name = self.director_full_name
        split_full_name = full_name.split(' ')
        try:
            last_name = split_full_name[0]
        except IndexError:
            return ''
        try:
            first_name = split_full_name[1]
        except IndexError:
            return last_name
        try:
            patronimic_name = split_full_name[2]
        except IndexError:
            return f"{last_name} {first_name[0]}."
        return f"{last_name} {first_name[0]}. {patronimic_name[0]}."

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_select_queryset(cls, request=None):
        user = get_current_authenticated_profile()
        if user.has_full_access_to_order_editing:
            return cls.get_queryset(request)
        else:
            contrs = (user.contractors.filter(is_active=True) | ContractorModel.objects.filter(is_carrier=True,
                                                                                               is_active=True)).distinct()
            return cls.get_queryset(request).filter(contractor__in=contrs)

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        user = get_current_authenticated_profile()
        if user.has_full_access_to_order_editing:
            qs = cls.get_queryset(request)
        else:
            contrs = (user.contractors.filter(is_active=True) | ContractorModel.objects.filter(is_carrier=True,
                                                                                               is_active=True)).distinct()
            qs = cls.get_queryset(request).filter(contractor__in=contrs)

        if text:
            qs = qs.filter(contractor=text)

        return qs

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorMemberModelSerializer
        return ContractorMemberModelSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('name')

    class Meta:
        verbose_name = _('Contractor')
        verbose_name_plural = _('Contractors')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        contractor = self.contractor
        if contractor:
            contractor.save()

class PotentialContractorModel(BaseCatalog, BaseAbstractCatalog):
    """Потенциальные Контрагенты"""
    # profiles = models.ManyToManyField(
    #     to='users.ProfileModel',
    #     through='catalogs.ContractorProfileModel',
    #     through_fields=('contractor', 'user'),
    #     verbose_name=_('Individuals')
    # )
    company_name = common_fields.CustomCharField(default='',
                                                 blank=True,
                                                 verbose_name='Название компании',
                                                 max_length=255
                                                 )
    business_region_name = common_fields.CustomCharField(default='',
                                                         blank=True,
                                                         verbose_name='Бизнес регион',
                                                         max_length=255
                                                         )
    phone = common_fields.CustomCharField(default='',
                                          blank=True,
                                          verbose_name='Номер телефона',
                                          max_length=100)
    email = common_fields.CustomCharField(default='',
                                          blank=True,
                                          verbose_name='email',
                                          max_length=255)
    is_archived = common_fields.CustomBooleanField(default=False,
                                                   verbose_name='Архивный')
    contractor = common_fields.CustomForeignKey(to=ContractorModel,
                                                on_delete=CUSTOM_SET_NULL,
                                                null=True,
                                                blank=True,
                                                default=None,
                                                verbose_name="Клиент",
                                                related_name="source_lead")
    lead_status_filter = fields.LeadSatusField()

    class Meta:
        verbose_name = _('Potential Contractor')
        verbose_name_plural = _('Potential Contractors')

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/catalogs/contractors/'

    @property
    def only_digits_phone(self) -> str:
        if self.phone:
            return re.sub(r'\D', '', self.phone)
        else:
            return ''

    @classmethod
    def get_table_columns(cls):
        # return 'status', 'code', 'name', 'profiles'
        return 'name', 'company_name', 'lead_status_filter'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (ContractorModelSerializer,
                                  PotentialContractorModelUpdateSerializer,
                                  PotentialContractorModelShortSerializer)
        if action in ['update', 'partial_update']:
            return PotentialContractorModelUpdateSerializer
        # return ContractorModelSerializer
        return PotentialContractorModelShortSerializer

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['table_columns'].append({'cellRenderer': 'DefaultRow',
                                      'field': 'profiles',
                                      'headerName': 'Физлица',
                                      'sortable': False,
                                      'width': 300})
        return data

    @classmethod
    def get_queryset(cls, request=None):
        user = get_current_authenticated_profile()
        return user.contractors.filter(is_active=True)


class ContractContractorModel(BaseAbstractModel):
    contract = common_fields.CustomForeignKey(
        to='catalogs.ContractModel',
        to_field='code',
        null=False,
        default='default',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        verbose_name='Соглашение',
        related_name='contractors'
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        verbose_name=_('Contractor'),
        on_delete=CUSTOM_PROTECT,
        related_name='contracts',
    )
    default = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name='Соглашение по умолчанию'
    )

    class Meta:
        verbose_name = 'М2М Контрагент Соглашение'
        verbose_name_plural = 'M2M Контрагент Соглашение'
        unique_together = (('contract', 'contractor'),)

    def save(self, *args, **kwargs):
        if self.default:
            # Убираем default у остальных записей, если эта запись default:
            ContractContractorModel.objects.filter(contractor=self.contractor).update(default=False)
        else:
            if not ContractContractorModel.objects.filter(contractor=self.contractor).exists():
                # Первая запись связанного объекта всегда is_main:
                self.default = True
        super().save(*args, **kwargs)


class ContractorProfileModel(BaseAbstractModel):
    """M2M-связь контрагента с физлицом (профилем)"""

    meta_exclude_fields = ['author', 'created_at', 'director', 'default_ticket_visor', ]
    field_verbose_names = {'user': _('Сотрудник'), 'contractor': _('Организация'),}

    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Individual'),
        blank=False,
        related_name='contractor_profile',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Contractor'),
        blank=False,
        related_name='contractor_profile',
    )
    director = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Главное физ. лицо'
    )
    default_ticket_visor = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Наблюдатель обращений по умолчанию'
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorProfileNotifySerializer
        # Для уведомлений:
        return ContractorProfileNotifySerializer

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        annotations = {}
        names = set(requested_computed or [])
        outer_ref_column = kwargs.get('outer_ref_column')

        if 'root_contractor' in names:
            root_subquery = ContractorRelationModel.objects.filter(
                contractor_id=OuterRef('contractor_id'),
                relation_type_id='structural_division',
                is_active=True,
            ).values('contractor_root_id')[:1]
            contractor_pk_field = cls._meta.get_field('contractor').target_field
            if outer_ref_column:
                profile_root_subquery = cls.objects.filter(
                    pk=OuterRef(outer_ref_column),
                ).annotate(
                    resolved_root_contractor=Coalesce(
                        Subquery(root_subquery),
                        F('contractor_id'),
                        output_field=contractor_pk_field,
                    )
                ).values('resolved_root_contractor')[:1]
                annotations['root_contractor'] = Subquery(
                    profile_root_subquery,
                    output_field=contractor_pk_field,
                )
            else:
                annotations['root_contractor'] = Coalesce(
                    Subquery(root_subquery),
                    F('contractor_id'),
                    output_field=contractor_pk_field,
                )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                'name': 'root_contractor',
                'type': 'ForeignKey',
                'related_model': 'catalogs.ContractorModel',
                'verbose_name': _('Головная организация'),
            },
        ]

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if request is None:
            return qs
        user = request.user.profile
        allowed_contractor_ids = user.contractors.filter(is_active=True).values_list('pk', flat=True)
        return qs.filter(contractor_id__in=allowed_contractor_ids)

    def __str__(self):
        return f"{self.contractor.name} | {self.user}"

    class Meta:
        verbose_name = 'Контрагент физлиц'
        verbose_name_plural = 'Контрагенты физлиц'
        unique_together = (('user', 'contractor',),)


def generate_1c_access_token():
    """Генерирует случайную строку для токена."""
    return secrets.token_urlsafe(48)


class Contractor1CAccessTokenModel(BaseAbstractModel):
    contractor = common_fields.CustomForeignKey(
        to='ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='contractor_1c_access_tokens',
        verbose_name=_('Организация')
    )
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        verbose_name=_('Название'),
    )
    token_hash = common_fields.CustomCharField(
        max_length=128,
        unique=True,
        db_index=True,
        verbose_name=_('Хэш токена')
    )
    expires_at = common_fields.CustomDateTimeField(
        verbose_name=_('Срок действия до'),
        null=True,
        blank=True,
    )
    last_used_at = common_fields.CustomDateTimeField(
        verbose_name=_('Дата последнего использования'),
        null=True,
        blank=True,
    )
    _raw_token = None

    class Meta:
        verbose_name = _('Токен доступа для 1С')
        verbose_name_plural = _('Токены доступа для 1С')
        ordering = ('-created_at',)

    @classmethod
    def create_for_service(cls, name, contractor, expires_at):
        """Фабричный метод для создания токена."""
        raw_token = generate_1c_access_token()
        hashed_token = cls.hash_token(raw_token)

        instance = cls.objects.create(
            name=name,
            contractor=contractor,
            token_hash=hashed_token,
            expires_at=expires_at,
        )
        # Сохраняем чистый токен в атрибут объекта, чтобы вернуть его вызвавшему коду
        instance._raw_token = raw_token
        return instance

    @staticmethod
    def hash_token(token):
        """Метод для хэширования строки."""
        return hashlib.sha256(token.encode()).hexdigest()

    @property
    def is_expired(self):
        """Проверка, истек ли срок действия."""
        if self.expires_at is not None:
            return timezone.localdate() > self.expires_at
        else:
            return False

    @property
    def is_valid(self):
        """Общая проверка валидности."""
        return self.is_active and not self.is_expired

    def check_token(self, raw_token):
        """Проверяет соответствие переданного токена хэшу в базе."""
        return self.token_hash == self.hash_token(raw_token)

    def __str__(self):
        status = "Active" if self.is_valid else "Inactive/Expired"
        return f"Token {self.name} ({status})"


class WarehouseContractorModel(BaseAbstractModel):
    """M2M-связь контрагента со складом (склады клиента)"""
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Contractor'),
        blank=False,
    )
    warehouse = common_fields.CustomForeignKey(
        to='catalogs.WarehouseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Warehouse'),
    )

    class Meta:
        verbose_name = "Склад клиента"
        verbose_name_plural = "Склады клиентов"
        unique_together = (('contractor', 'warehouse',),)


class DeliveryAddress(BaseAbstractModel):
    """Адреса доставки"""
    code = common_fields.CustomCharField(
        verbose_name=_('search code'),
        unique=True,
        null=False,
        default=uuid.uuid1,
        max_length=100,
        blank=True,
        table_info=page_config.DefaultTableColumn(width=300)
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Contractor'),
        related_name='delivery_addresses',
    )
    address = common_fields.CustomCharField(
        null=False,
        default='',
        blank=False,
        max_length=500,
        verbose_name=_('Address'),
    )

    class Meta:
        verbose_name = _('Delivery address')
        verbose_name_plural = _('Delivery addresses')

    @classmethod
    def get_data_path(cls):
        return '/catalogs/delivery_addresses/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import DeliveryAddressModelSerializer
        return DeliveryAddressModelSerializer

    @classmethod
    def get_table_columns(cls):
        return 'status', 'code', 'contractor', 'address'

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def has_characteristics_plan(cls):
        return False

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['update_condition'] = {'is_active': True, 'is_predefined': False}
        if cls.is_enum():
            data.pop('edit_form', None)
            data.pop('update_condition', None)
        return data

    @classmethod
    def get_page_config(cls):
        if cls.is_enum():
            return {
                "showFilter": True
            }
        else:
            return super().get_page_config()

    @classmethod
    def get_context_menu(cls):
        if cls.is_enum():
            return None
        else:
            return super().get_context_menu()

    @classmethod
    def get_queryset(cls, request=None):
        user = get_current_authenticated_profile()
        contractors = user.contractors.all()
        return cls.objects.filter(is_active=True, contractor__in=contractors)

    def __str__(self):
        return f"{self.address}"


class GoodsRemnantModel(BaseAbstractModel):
    """Остатки товара"""
    STORAGE_TYPE_CHOICES = (('default', 'В наличии '),
                            ('ready_to_assemble', 'Готов к сборке'),)
    goods = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Goods'),
        related_name='remnants',
    )
    warehouse = common_fields.CustomForeignKey(
        to='catalogs.WarehouseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Warehouse'),
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        blank=False,
        default=0,
        verbose_name=_('Quantity'),
    )
    storage_type = common_fields.CustomCharField(default='default',
                                                 choices=STORAGE_TYPE_CHOICES,
                                                 max_length=25,
                                                 verbose_name='Тип храненияя')

    class Meta:
        verbose_name = _('Goods remnant')
        verbose_name_plural = _('Goods remnants')
        unique_together = (('goods', 'warehouse', 'storage_type'),)

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/catalogs/goods_remnants/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsRemnantModelListSerializer
        return GoodsRemnantModelListSerializer

    @classmethod
    def get_table_columns(cls):
        return 'status', 'goods', 'warehouse', 'quantity', 'created_at'

    @classmethod
    def has_characteristics_plan(cls):
        return False

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['update_condition'] = {'is_active': True, 'is_predefined': False}
        if cls.is_enum():
            data.pop('edit_form', None)
            data.pop('update_condition', None)
        return data

    @classmethod
    def get_page_config(cls):
        if cls.is_enum():
            return {
                "showFilter": True
            }
        else:
            return super().get_page_config()

    @classmethod
    def get_context_menu(cls):
        if cls.is_enum():
            return None
        else:
            return super().get_context_menu()


class GoodsPriceModel(BaseAbstractModel):
    """Цены на товары"""
    goods = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('Goods'),
        related_name='prices',
    )
    price_type = common_fields.CustomForeignKey(
        to='catalogs.PriceTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=False,
        default='default',
        verbose_name=_('Price type'),
    )
    price = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        blank=False,
        verbose_name=_('Price')
    )

    class Meta:
        verbose_name = _('Goods price')
        verbose_name_plural = _('Goods prices')
        unique_together = (('goods', 'price_type',),)

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/catalogs/goods_prices/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsPriceModelListSerializer
        return GoodsPriceModelListSerializer

    @classmethod
    def get_table_columns(cls):
        return 'status', 'goods', 'price_type', 'price', 'created_at'

    @classmethod
    def has_characteristics_plan(cls):
        return False

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['update_condition'] = {'is_active': True, 'is_predefined': False}
        if cls.is_enum():
            data.pop('edit_form', None)
            data.pop('update_condition', None)
        return data

    @classmethod
    def get_page_config(cls):
        if cls.is_enum():
            return {
                "showFilter": True
            }
        else:
            return super().get_page_config()

    @classmethod
    def get_context_menu(cls):
        if cls.is_enum():
            return None
        else:
            return super().get_context_menu()


class CashUnitModel(BaseCatalog):
    pass


class PaymentFormModel(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    required = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name='Требует оплату',
    )
    is_cash = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name='Является наличной оплатой',
    )
    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import PaymentFormListSerializer
        return PaymentFormListSerializer

    class Meta:
        verbose_name = _("Payment form")
        verbose_name_plural = _("Payment forms")


class PaymentOptionModel(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = _("Payment option")
        verbose_name_plural = _("Payment options")


class DeliveryPointModel(BaseCatalog):
    lat = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=13,
        null=False,
        default=0,
        verbose_name='Широта'
    )
    lon = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=13,
        null=False,
        default=0,
        verbose_name='Долгота'
    )
    address = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Адрес'
    )
    contractors = models.ManyToManyField(
        'catalogs.ContractorModel',
        through='catalogs.ContractorDeliveryPointModel',
        blank=True,
        verbose_name='Клиенты',
    )

    class Meta:
        verbose_name = 'Точка доставки'
        verbose_name_plural = 'Точки доставки'
        ordering = ('-created_at',)

    @classmethod
    def is_enum(cls):
        return True


class ContractorDeliveryPointModel(BaseModel):
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Клиент',
    )
    delivery_point = common_fields.CustomForeignKey(
        to='catalogs.DeliveryPointModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Точка доставки',
    )

    class Meta:
        verbose_name = 'Точка доставки клиента'
        verbose_name_plural = 'Точки доставки клиента'
        unique_together = (('contractor', 'delivery_point',),)


class OfferModel(BaseCatalog):
    """
    Модель для оферты
    """
    offer_text = models.TextField(
        verbose_name='Текст договора-оферты',
        null=True,
        blank=False,
        default=DEFAULT_OFFER_TEXT
    )
    user = models.ManyToManyField(
        'users.ProfileModel',
        # through='catalogs.UserOfferModel',
        # through_fields=('offer', 'user'),
        related_name='user_profile',
        blank=True,
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Договор - оферта'
        verbose_name_plural = 'Договоры - оферты'


# class UserOfferModel(BaseModel):
#     """
#     Промежуточная модель для связи договора-оферты с клиентом
#     """
#     user = common_fields.CustomForeignKey(
#         to='users.ProfileModel',
#         null=True,
#         blank=False,
#         on_delete=CUSTOM_PROTECT,
#         related_name='profile',
#         verbose_name='Пользователь',
#     )
#     offer = common_fields.CustomForeignKey(
#         to='catalogs.OfferModel',
#         null=True,
#         blank=False,
#         on_delete=CUSTOM_PROTECT,
#         related_name='offer',
#         verbose_name='Договор - оферта',
#     )

#     class Meta:
#         verbose_name = 'Договор - оферта клиента'
#         verbose_name_plural = 'Договоры - оферты клиента'
#         unique_together = (('user', 'offer',),)


class UserURLsModel(BaseCatalog):

    url = models.URLField(
        verbose_name='URL',
        max_length=200,
        default='',
        blank=False,
        help_text='Адрес ссылки')
    favicon = models.ImageField(
        verbose_name='Иконка',
        upload_to='icons/',
        blank=True,
        help_text='Иконка')
    method = models.CharField(
        verbose_name='Метод GET или POST',
        max_length=10,
        default='GET',
        blank=False,
        help_text='Метод')

    params = models.CharField(
        verbose_name='Объект с параметрами',
        max_length=1000,
        default='',
        blank=False,
        help_text='Объект с параметрами'
    )

    class Meta:
        verbose_name = 'Ссылка пользователя'
        verbose_name_plural = 'Ссылки пользователя'


class RegisterHelpModel(BaseCatalog):
    """
    Текст помощи при регистрации
    """
    help_text = models.TextField(
        verbose_name='Текст справки',
        blank=False,
        default=''
    )

    class Meta:
        verbose_name = 'Помощь при регистрации'


class DeliveryPurposeModel(BaseCatalog):
    purpose = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        verbose_name='Назначение доставки'
    )

    def __str__(self):
        return self.purpose

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import DeliveryPurposeSerializer
        return DeliveryPurposeSerializer

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise rest_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise rest_exceptions.ValidationError()
        else:
            pass

    def get_update_permission(self, request):
        if request.user.profile.can_edit_goods_price:
            return True

    def get_detail_permission(self, request):
        if not request.user.is_anonymous:
            return True

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('purpose', 'created_at')

    class Meta:
        verbose_name = 'Назначение доставки'
        verbose_name_plural = 'Назначения доставки'


class BankRequisitesModel(BaseCatalog, BaseAbstractCatalog):
    contractor_member = common_fields.CustomForeignKey(
        to='catalogs.ContractorMemberModel',
        on_delete=CUSTOM_PROTECT,
        related_name='requisites',
    )
    bank_name = common_fields.CustomCharField(
        max_length=100,
        null=False,
        default='',
        blank=True,
        verbose_name='Наименование банка',
    )
    bank_account = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Расчетный счет, РС',
        # help_text='Расчетный счет юридического лица должен быть '
        #           'последовательностью из 20 арабских цифр, '
        #           'первая цифра 405, 406 или 407',
        # validators=(validators.bank_account_validator, )
    )
    correspondent_account = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Корреспондентский счет, КС',
        # help_text='Корреспондентский счет юридического лица должен быть '
        #           'последовательностью из 20 арабских цифр, первая цифра 301, '
        #           'последние три цифры номера совпадают с последними '
        #           'тремя цифрами БИК',
        # validators=(validators.correspondent_account_validator, )
    )
    bik = common_fields.CustomCharField(
        max_length=50,
        null=False,
        default='',
        blank=True,
        verbose_name='Банковский идентификационный код, БИК',
        # help_text='Банковский идентификационный код должен быть '
        #           'последовательностью из 9 арабских цифр, '
        #           'первые цифры 04',
        # validators=(validators.bik_validator, )
    )
    is_default = common_fields.CustomBooleanField(
        default=False,
        blank=False,
        verbose_name='Основные реквизиты'
    )

    def save(self, *args, **kwargs):
        '''
        Если реквизиты указаны как основные сбрасываем is_default
        в False для всех остальных реквизитов контрагента
        '''
        if self.is_default:
            BankRequisitesModel.objects.filter(
                is_active=True,
                contractor_member=self.contractor_member,
                is_default=True
            ).update(is_default=False)

        super(BankRequisitesModel, self).save(*args, **kwargs)

    def __str__(self):
        return self.bank_name

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True)

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import RequisitesModelSerializer
        return RequisitesModelSerializer


class CostItemModel(BaseCatalog, BaseAbstractCatalog):
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='cost_items',
        verbose_name=_('Организация')
    )

    class Meta:
        verbose_name = _('Статья затрат')
        verbose_name_plural = _('Статьи затрат')
    #
    # @classmethod
    # def search_input(cls):
    #     return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import CostItemModelListSerializer
        return CostItemModelListSerializer

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        from users.utils import get_tree_departments_related_organizations
        qs = cls.objects.filter(is_active=True)
        if request:
            # TODO пока что просто чтобы был в организации
            permission_contractors_id = set(request.user.profile.my_organizations)
            if permission_contractors_id:
                tree_permission_contractors_id = get_tree_departments_related_organizations(permission_contractors_id)
                contractor_id = request.query_params.get('contractor')
                if contractor_id:
                    if uuid.UUID(contractor_id) in tree_permission_contractors_id:
                        contractors_id = get_tree_departments_related_organizations((contractor_id,))
                        qs = qs.filter(
                            Q(contractor__isnull=True) | Q(contractor_id__in=contractors_id)).annotate(
                            contractor_order=models.Case(
                                models.When(contractor_id=contractor_id, then=Value(0)),
                                default=Value(1),
                                output_field=models.IntegerField(),
                            )
                        ).order_by('contractor_order', 'sort', 'name')
                    else:
                        return qs.none()
                else:
                    qs = qs.filter(
                        Q(contractor__isnull=True) | Q(contractor_id__in=tree_permission_contractors_id)
                    ).order_by('sort', 'name')
            else:
                return qs.none()
        return qs

    def get_update_permission(self, request) -> bool:
        contractor = self.contractor
        if not contractor:
            return False
        from users.utils import get_ancestor_departments_related_organizations
        from contractor_permissions.utils import contractors_where_user_has_permission
        contractors_id = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        permission_contractors_id = set(
            contractors_where_user_has_permission(request.user.profile.pk, 'admin', None)
        )
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        contractor = self.contractor
        if not contractor:
            return True
        from users.utils import get_tree_departments_related_organizations
        contractors_id = get_tree_departments_related_organizations((contractor.pk,))
        # TODO пока что просто чтобы был в организации
        my_organizations = set(user.my_organizations)
        if my_organizations.isdisjoint(contractors_id):
            return False
        else:
            return True


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


class ContractorProfileRequestModel(BaseAbstractModel):
    tracker = FieldTracker(
        fields=('is_touched',)
    )

    is_approved = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Одобрено',
    )
    is_touched = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Проверено',
        editable=False,
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Профиль пользователя',
        related_name='contractor_profile_requests'
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Организация',
    )

    access_groups = models.ManyToManyField(
        to='contractor_permissions.AccessGroupModel',
        blank=True,
        related_name='profile_requests',
        verbose_name='Группы доступа'
    )

    class Meta:
        verbose_name = 'Заявка на директора организации'
        verbose_name_plural = 'Заявки на директора организации'

    @property
    def organization_bin(self):
        """Бин организации, для поисковой индексации."""
        contractor_member = self.organization.contractor_members.first()
        if contractor_member:
            return contractor_member.inn
        else:
            return ''

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (ContractorProfileRequestModelNotify,
                                  ContractorProfileRequestListSerializer,
                                  ContractorProfileRequestUpdateSerializer)
        if action in ('update', 'partial_update'):
            return ContractorProfileRequestUpdateSerializer
        if action == 'notify':
            return ContractorProfileRequestModelNotify
        return ContractorProfileRequestListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        user = request.user.profile
        if not user.is_support:
            return cls.objects.none()
        return cls.objects.filter(is_active=True).order_by('-created_at')

    @classmethod
    def get_table_columns(cls):
        return 'user', 'organization', 'is_touched', 'is_approved'

    def __str__(self):
        return f"{self.created_at} {self.user} {self.organization}"

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.pk)
        except ObjectDoesNotExist:
            super().save(*args, **kwargs)
        else:
            if self.is_touched and not self.tracker.has_changed('is_touched'):
                raise ValidationError('Заявка уже была рассмотрена')
            if not self.is_touched and self.tracker.has_changed('is_touched'):
                raise ValidationError('Заявка уже была рассмотрена')
            with transaction.atomic():
                if self.is_approved:
                    user = self.user
                    organization = self.organization
                    contractor_profile = ContractorProfileModel()
                    contractor_profile.user = user
                    contractor_profile.director = False
                    contractor_profile.contractor = organization
                    try:
                        contractor_profile.save()
                    except IntegrityError:
                        raise ValidationError(
                            'Пользователь уже является участником этой организации.',
                            code='invalid',
                            params={'value': True}
                        )
                    from common.utils import use_access_groups
                    if use_access_groups(None):
                        pass
                    else:
                        from contractor_permissions.models import (ContractorPermissionRoleModel,
                                                                   ContractorPermissionModel,
                                                                   ContractorPermissionRoleProfileModel)
                        contractor_permission = ContractorPermissionModel.objects.filter(
                            is_active=True,
                            contractor_permission_role__contractor=organization,
                            contractor_permission_role__is_active=True,
                            permission_type_id='send_report',
                            aux_conditions__isnull=True,
                        ).order_by('-created_at').first()
                        if contractor_permission:
                            permission_role = contractor_permission.contractor_permission_role
                        else:
                            permission_role = ContractorPermissionRoleModel.objects.create(
                                name='Может отправлять отчеты',
                                contractor=organization,
                            )
                            ContractorPermissionModel.objects.create(
                                permission_type_id='send_report',
                                contractor_permission_role=permission_role,
                            )
                        ContractorPermissionRoleProfileModel.objects.create(
                            contractor_permission_role=permission_role,
                            contractor_profile=contractor_profile
                        )

                        contractor_permission = ContractorPermissionModel.objects.filter(
                            is_active=True,
                            contractor_permission_role__contractor=organization,
                            contractor_permission_role__is_active=True,
                            permission_type_id='',
                            aux_conditions__isnull=True,
                        ).order_by('-created_at').first()
                        if contractor_permission:
                            permission_role = contractor_permission.contractor_permission_role
                        else:
                            permission_role = ContractorPermissionRoleModel.objects.create(
                                name='Может создавать оценки рисков',
                                contractor=organization,
                            )
                            ContractorPermissionModel.objects.create(
                                permission_type_id='create_risk_assessment',
                                contractor_permission_role=permission_role,
                            )
                        ContractorPermissionRoleProfileModel.objects.create(
                            contractor_permission_role=permission_role,
                            contractor_profile=contractor_profile
                        )

                    user.temporary_blocked = False
                    user.save(update_fields=('temporary_blocked',))
                    from .utils import send_email_about_register_request_approved
                    transaction.on_commit(lambda: async_task(send_email_about_register_request_approved, user))
                self.is_touched = True
                super().save(*args, **kwargs)


class LocationPointModel(BaseAbstractModel):
    """Модель геометки объекта."""
    tracker = FieldTracker(
        fields=(
            'name',
            'address',
        )
    )
    name = common_fields.CustomCharField(
        verbose_name=_('Наименование'),
        max_length=255,
        null=False,
        default='',
        blank=True,
        table_info=page_config.DefaultTableColumn(width=300)
    )
    lat = common_fields.CustomDecimalField(
        max_digits=9,
        decimal_places=6,
        db_index=True,
        default=0,
        verbose_name=_('Широта')
    )
    lon = common_fields.CustomDecimalField(
        max_digits=9,
        decimal_places=6,
        db_index=True,
        default=0,
        verbose_name=_('Долгота')
    )
    address = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Адрес')
    )
    related_object = models.ForeignKey(
        'common.BaseModel',
        on_delete=CUSTOM_CASCADE,
        related_name='location_points',
        verbose_name=_('Related object'),
        null=True
        )

    admin_area = common_fields.CustomForeignKey(
        to='LocationAdminAreaModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Административная единица'),
    )

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        try:
            related_object = self.related_object.original_object
        except ObjectDoesNotExist:
            return
        if 'location_points' in getattr(related_object, 'm2m_track_fields', tuple()):
            object_property_id = f"{related_object.track_prefix}__location_point"
            str_view = self.address
            pk_set = {self.pk, }
            related_object_id = related_object.pk
            if created:
                change_history_utils.create_add_m2m(
                    related_object_id,
                    action_date,
                    object_property_id,
                    str_view=str_view,
                    pk_set=pk_set
                )
                return
            if deleted:
                change_history_utils.create_remove_m2m(
                    related_object_id,
                    action_date,
                    object_property_id,
                    str_view,
                    pk_set
                )
            if not changed_fields:
                return
            if 'name' in changed_fields:
                change_history_utils.create_update_str(
                    related_object_id,
                    action_date,
                    f"{object_property_id}__name",
                    f"{str_view} - \"{changed_fields['name']}\"",
                    f"{str_view} - \"{changed_fields['name']}\"",
                )

    def __str__(self):
        return f"{self.address}"

    @property
    def wkt(self):
        return f"POINT({self.lon} {self.lat})"


class KlassificationDimensionModel(BaseCatalog, BaseAbstractCatalog):
    description = common_fields.CustomCharField(
        max_length=1023,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Description'),
    )
    pass


class KlassificationCategoryModel(BaseCatalog, BaseAbstractCatalog):
    dimension = models.ForeignKey(KlassificationDimensionModel, on_delete=CUSTOM_PROTECT)
    description = common_fields.CustomCharField(
        max_length=1023,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Description'),
    )



class KlassificationModel(BaseAbstractModel):
    related_object = models.ForeignKey(BaseModel,
    related_name='klassification',

                                       on_delete=CUSTOM_CASCADE)
    dimension = models.ForeignKey(KlassificationDimensionModel, on_delete=CUSTOM_PROTECT)
    category = models.ManyToManyField(KlassificationCategoryModel)
    description = common_fields.CustomCharField(
        max_length=1023,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Description'),
    )



class LocationAdminAreaModel(gis_models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    kato = gis_models.OneToOneField(
        'accounting_catalogs.KATOCodesModel',
        to_field='code',
        null=True,
        blank=True,
        related_name='admin_area',
        on_delete=CUSTOM_PROTECT,
    )
    is_active = gis_models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = gis_models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = gis_models.DateTimeField(
        auto_now=True,
    )

    deleted_at = gis_models.DateTimeField(
        null=True,
        blank=True,
    )

    sort = gis_models.IntegerField(default=500, verbose_name=_('List order'))

    osm_id = gis_models.PositiveIntegerField(unique=True)
    parent = gis_models.ForeignKey(
        'self',
        on_delete=gis_models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
    )
    parent_osm_id = gis_models.PositiveIntegerField(null=True)

    name_ru = gis_models.CharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
    )
    name_kk = gis_models.CharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
    )
    name_en = gis_models.CharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
    )
    admin_level = gis_models.PositiveIntegerField(
        null=False,
        default=6,
    )

    geom = gis_models.MultiPolygonField(srid=4326)

    show_stats = common_fields.CustomBooleanField(
        default=True
    )

    class Meta:
        verbose_name = _('Область')
        verbose_name_plural = _('Области')
        ordering = ('sort', 'name_ru', )

    def __str__(self):
        return f"{self.name_ru} {self.parent if self.parent else ''}"

locationadminareamodel_mapping = {
    'osm_id': 'osm_id',
    'name_kk': 'name_kk',
    'name_ru': 'name_ru',
    'name_en': 'name_en',
    'admin_level': 'admin_level',
    'parent_osm_id': 'parent',
    'kato': {'code': 'kato_code'},
    'geom': 'MULTIPOLYGON',
}


class LegalEntityModel(BaseCatalog, BaseAbstractCatalog):
    full_name = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Полное наименование',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        related_name='legal_entities',
        on_delete=CUSTOM_PROTECT,

    )

    inn = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name='ИИН/БИн',
    )

    external_id = common_fields.CustomCharField(
        max_length=36,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Внешний ID'),
    )

    class Meta:
        verbose_name = _('Юридическое лицо')
        verbose_name_plural = _('Юридические лица')


class WorkDirectionModel(BaseCatalog, BaseAbstractCatalog):
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        related_name='work_directions',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация')
    )
    is_archive = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('В архиве')
    )

    class Meta:
        verbose_name = _('Направление работы')
        verbose_name_plural = _('Направления работы')
        ordering = ('name', '-created_at',)

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            WorkDirectionCreateSerializer,
            WorkDirectionUpdateSerializer,
            WorkDirectionListSerializer,
            WorkDirectionDetailSerializer
        )
        if action == 'create':
            return WorkDirectionCreateSerializer
        elif action in ('update', 'partial_update'):
            return WorkDirectionUpdateSerializer
        elif action == 'retrieve':
            return WorkDirectionDetailSerializer
        else:
            return WorkDirectionListSerializer

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_queryset(cls, request=None):
        from users.utils import get_tree_departments_related_organizations
        qs = cls.objects.filter(is_active=True)
        if request:
            user = request.user.profile
            contractors_id = set(user.my_organizations)
            if contractors_id:
                contractors_id = get_tree_departments_related_organizations(contractors_id)
            else:
                return qs.none()
        else:
            return qs.none()
        return qs.filter(contractor__in=contractors_id).order_by('name',)

    def get_update_permission(self, request) -> bool:
        from contractor_permissions.utils import contractors_where_user_has_permission
        contractor = self.contractor
        if not contractor:
            return False
        from users.utils import get_ancestor_departments_related_organizations
        contractors_id = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        permission_contractors_id = set(
            contractors_where_user_has_permission(request.user.profile.pk, 'admin', None)
        )
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        contractor = self.contractor
        if not contractor:
            return True
        from users.utils import get_tree_departments_related_organizations
        contractors_id = get_tree_departments_related_organizations((contractor.pk,))
        permission_contractors_id = set(user.my_organizations)
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

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


class ExternalCustomerModel(BaseModel):
    external_id = common_fields.CustomCharField(
        max_length=36,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Внешний ID'),
    )

    source = common_fields.CustomForeignKey(
        to='catalogs.Contractor1CAccessTokenModel',
        null=True,
        blank=True,
        related_name='external_customers',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Источник')
    )

    org_admin = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Организация',
        related_name='external_customers',
    )

    name = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Наименование')
    )

    full_name = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Полное наименование')
    )
    inn = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name='БИН',
    )

    class Meta:
        verbose_name = _('Клиент от внешнего сервиса')
        verbose_name_plural = _('Клиенты от внешнего сервиса')

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()
        user = request.user.profile
        from contractor_permissions.utils import contractors_where_user_has_permission
        from users.utils import get_descendants_departments_related_organizations
        contractors = contractors_where_user_has_permission(
            user.pk,
            ('admin', 'create_workgroup', 'help_desk_admin'),
            None
        )
        if not contractors:
            return qs.none()
        descendants = get_descendants_departments_related_organizations(contractors, include_self=True)
        qs = qs.filter(org_admin__in=descendants)
        qs = qs.order_by('name')
        return qs

    def __str__(self):
        return f"{self.inn} | {self.name}"

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        qs = cls.get_select_queryset(request)
        return qs.filter(
            Q(name__icontains=text) | Q(full_name__icontains=text) |
            Q(inn__exact=text))

