from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.core.validators import MinValueValidator, DecimalValidator
from django.db import models, transaction
from django.db.models import OuterRef, Sum, Count, Q, Subquery, Prefetch, F, Case, When

from django_q.tasks import async_task

from rest_framework import exceptions as rest_exceptions

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE, DEFAULT_PRICE_TYPE_CODE, GOODS_PRICE_BY_CATALOG

from common import fields as common_fields
from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from common.catalogs.models import GoodsPriceModel, ContractModel
from common.catalogs.utils import get_user_price_type
from common.current_profile.middleware import get_current_authenticated_profile

from gallery.models import GalleryModel

from . import fields


class CartTypeModel(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = _('Cart type')
        verbose_name_plural = _('Cart types')


class ShoppingCartModel(BaseModel):
    cart_type = common_fields.CustomForeignKey(
        to='crm.CartTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=True,
        default='shopping_cart',
        verbose_name=_('Cart type')
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('User')
    )
    goods = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=pgettext_lazy('singular', 'Goods'),
        related_name='shopping_carts',
    )
    goods_for_print = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name='Товар для печати',
        related_name='shopping_carts_for_print',
    )
    warehouse = common_fields.CustomForeignKey(
        to='catalogs.WarehouseModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('warehouse'),
        related_name='shopping_carts',

    )
    quantity = common_fields.CustomDecimalField(
        null=False,
        default=1, max_digits=15, decimal_places=3,
        blank=True,
        verbose_name=_('Quantity'),
        validators=(MinValueValidator(1),)
    )
    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        # related_name='tp_goodsorders',
    )
    coefficient = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        default=1,
        verbose_name=_('Coefficient')
    )
    custom_price = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        verbose_name='Кастомная цена',
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.goods_for_print = self.goods
        if not self.custom_price:
            self.custom_price = self.goods.price_by_catalog
        return super().save(*args, **kwargs)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ShoppingCartModelListSerializer, ShoppingCartModelCreateSerializer, \
            ShoppingCartModelUpdateSerializer, ShoppingCartModelDetailSerializer
        if action == 'create':
            return ShoppingCartModelCreateSerializer
        elif action in ['update', 'partial_update']:
            return ShoppingCartModelUpdateSerializer
        elif action == 'retrieve':
            return ShoppingCartModelDetailSerializer
        else:
            return ShoppingCartModelListSerializer

    @classmethod
    def get_queryset(cls, request=None, price_type_code=None):
        user = get_current_authenticated_profile()
        if not price_type_code:
            if request:
                contract_id = request.query_params.get('contract')
            else:
                contract_id = None
            if not contract_id:
                price_type = get_user_price_type(user)
            else:
                try:
                    contract = ContractModel.objects.get(pk=contract_id)
                except ContractModel.DoesNotExist:
                    raise rest_exceptions.NotFound('Contract not found.')
                price_type = contract.price_type
            price_type_id = price_type.code
        else:
            price_type_id = price_type_code

        prices = GoodsPriceModel.objects.filter(is_active=True, goods__shopping_carts=OuterRef('pk'),
                                                price_type_id=price_type_id)
        if GOODS_PRICE_BY_CATALOG:
            price__lookup = F('goods__price_by_catalog')
        else:
            price__lookup = Subquery(prices.values('price'),
                                     output_field=models.DecimalField(max_digits=15, decimal_places=2))
        queryset = cls.objects.prefetch_related(
            Prefetch('goods__gallery', queryset=GalleryModel.objects.filter(is_active=True, is_main=True))
        ).select_related('goods', 'warehouse__manager__user').filter(user=user).annotate(
            # price=Subquery(prices.values('price'), output_field=models.DecimalField(max_digits=15, decimal_places=2)),
            price=price__lookup,
            currency_name=Subquery(prices.values('price_type__currency__name')),
            currency_icon=Subquery(prices.values('price_type__currency__icon')),
            remnant_sum=Sum('goods__remnants__quantity'),
            amount=Case(
                When(custom_price__isnull=False, then=F('custom_price') * F('quantity')),
                default=F('price') * F('quantity'),
                output_field=models.DecimalField(max_digits=15, decimal_places=2)),
        )
        return queryset

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Корзина товаров'
        unique_together = (('user', 'goods', 'warehouse', 'cart_type',),)
        # ordering = ['created_at']


class GoodsOrderExecuteStatusModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name='Цвет',
    )
    icon = common_fields.CustomCharField(
        null=False,
        default='info',
        blank=True,
        max_length=127,
        verbose_name='Иконка',
    )

    class Meta:
        verbose_name = 'Состояние заказа'
        verbose_name_plural = 'Состояние заказов'

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsOrderExecuteStatusSerializer
        return GoodsOrderExecuteStatusSerializer


class OrderCounterModel(models.Model):
    def __str__(self):
        return f"{self.pk}"

    @classmethod
    def get_label(cls):
        return cls._meta.label


def get_order_counter():
    counter = OrderCounterModel.objects.create()
    return counter.pk


class OrderOperationTypeModel(BaseCatalog, BaseAbstractCatalog):
    """Тип операции заказа. Коды операций заказа берем из crm.enums.OperationTypeEnum."""

    class Meta:
        verbose_name = "Тип операции заказа"
        verbose_name_plural = "Типы операции заказа"


class OrderManagerModel(BaseModel):
    """
    Модель для списка ответственных за заказы
    """
    profile = models.OneToOneField(
        'users.ProfileModel',
        verbose_name='Профиль пользователя',
        on_delete=models.PROTECT,
    )


# TODO Устарело!
class PayTypeModel(BaseCatalog, BaseAbstractCatalog):
    """
    Вид оплаты заказа.
    """
    required = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name='Требует оплату',
    )

    class Meta:
        verbose_name = "Вид оплаты заказа"
        verbose_name_plural = "Виды оплаты заказа"


class CashPayTypeModel(BaseCatalog, BaseAbstractCatalog):
    """Вид наличной оплаты заказа."""

    parent = common_fields.CustomForeignKey(
        to='self',
        on_delete=CUSTOM_PROTECT,
        verbose_name="Группа",
        blank=True,
        null=True,
    )

    is_group = common_fields.CustomBooleanField(
        verbose_name="Группа",
        null=False,
        default=False,
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import CashPayTypeModelSerializer
        return CashPayTypeModelSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return super().get_queryset(request).order_by('sort', 'name')

    class Meta:
        verbose_name = 'Вид наличной оплаты заказа'
        verbose_name_plural = 'Виды наличной оплаты заказа'


class DeliveryStatusModel(BaseCatalog, BaseAbstractCatalog):
    """Статус доставки заказа"""
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name='Цвет',
    )
    icon = common_fields.CustomCharField(
        null=False,
        default='info',
        blank=True,
        max_length=127,
        verbose_name='Иконка',
    )
    edit_order_is_possible = common_fields.CustomBooleanField(
        verbose_name="Корректировка заказа разрешена",
        null=False,
        default=True,
    )

    class Meta:
        verbose_name = 'Статус доставки заказа'
        verbose_name_plural = 'Статусы доставки заказа'

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsOrderDeliveryStatusSerializer
        return GoodsOrderDeliveryStatusSerializer


class PaymentStatusModel(BaseCatalog, BaseAbstractCatalog):
    """Статус оплаты заказа"""
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name='Цвет',
    )
    icon = common_fields.CustomCharField(
        null=False,
        default='info',
        blank=True,
        max_length=127,
        verbose_name='Иконка',
    )

    class Meta:
        verbose_name = 'Статус оплаты заказа'
        verbose_name_plural = 'Статусы оплаты заказа'

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsOrderPaymentStatusSerializer
        return GoodsOrderPaymentStatusSerializer


class GoodsOrderModel(BaseModel):
    """Заказ товаров."""
    pay_type = common_fields.CustomForeignKey(
        to='catalogs.PaymentFormModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='goods_orders',
        verbose_name='Форма оплаты',
    )
    pay_date_plan = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name="Дата оплаты план."
    )
    pay_date_fact = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name="Дата оплаты факт."
    )
    # Поля для наличной оплаты:
    cash_pay_recipient = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='pay_recipient_order',
        verbose_name='Получатель наличной оплаты',
    )
    cash_pay_type = common_fields.CustomForeignKey(
        to='crm.CashPayTypeModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name="Вид наличной оплаты",
    )
    cash_unit = common_fields.CustomForeignKey(
        to='catalogs.CashUnitModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='goods_orders',
        verbose_name='Кошелёк1',
    )
    cash_unit_secondary = common_fields.CustomForeignKey(
        to='catalogs.CashUnitModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        # related_name='goods_orders',
        verbose_name='Кошелёк2',
    )
    reason = common_fields.CustomForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='related_orders',
        verbose_name=_('Basis')
    )
    # CRM: заказ может быть оформлен на основании CRM-договора.
    # В этом сценарии ContractorModel не является клиентом заказа.
    customer_contract = common_fields.CustomForeignKey(
        to='customer_contracts.CustomerContractModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='goods_orders',
        verbose_name=_('CRM contract')
    )
    # CRM: это явно выбранный получатель отгрузки из CustomerCardModel.
    # Не вычислять его как "первую карточку договора": если карточек несколько,
    # пользователь должен выбрать нужную, и выбранное значение сохраняется здесь.
    customer_card = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='goods_orders',
        verbose_name=_('CRM customer')
    )
    start_task_delivery_point = common_fields.CustomForeignKey(
        to='tasks.TaskDeliveryPointModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='start_goods_orders',
        verbose_name='Стартовая точка доставки в задаче'
    )
    task_delivery_point = common_fields.CustomForeignKey(
        to='tasks.TaskDeliveryPointModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='goods_orders',
        verbose_name="Конечная точка доставки в задаче",
    )
    counter = common_fields.CustomOneToOneField(
        to='crm.OrderCounterModel',
        on_delete=CUSTOM_PROTECT,
        null=False,
        default=get_order_counter,
        verbose_name=_('Order number')
    )
    number_1c = common_fields.CustomCharField(
        default="",
        blank=True,
        verbose_name=_('Order number'),
        help_text="Номер заказа в 1С",
        max_length=255,
    )
    warehouse = common_fields.CustomForeignKey(
        to='catalogs.WarehouseModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Warehouse'),
        related_name='orders'
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Author'),
        null=True,
        blank=False,
        help_text='Поле user',
        related_name='orders',
    )
    last_editor = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Last editor'),
        null=True,
        blank=True,
        help_text='Исправил заказ',
        related_name='edited_orders',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Клиент',
        null=True,
        blank=False,
        related_name='orders',
    )
    contractor_member = common_fields.CustomForeignKey(
        to='catalogs.ContractorMemberModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Contractor'),
        null=True,
        blank=False,
        related_name='orders',
    )
    contract = common_fields.CustomForeignKey(
        to='catalogs.ContractModel',
        on_delete=CUSTOM_PROTECT,
        to_field='code',
        null=False,
        default='default',
        blank=False,
        related_name='orders',
        verbose_name=_('Contract')
    )

    execute_status = common_fields.CustomForeignKey(
        to='crm.GoodsOrderExecuteStatusModel',
        to_field='code',
        related_name='orders',
        verbose_name='Текущее состояние заказа',
        null=False,
        default='default',
        blank=False,
        on_delete=CUSTOM_PROTECT,
    )
    payment_status = common_fields.CustomForeignKey(
        to='crm.PaymentStatusModel',
        to_field='code',
        related_name='orders',
        verbose_name='Статус оплаты',
        null=False,
        default='expect_payment',
        blank=False,
        on_delete=CUSTOM_PROTECT,
    )
    delivery_status = common_fields.CustomForeignKey(
        to='crm.DeliveryStatusModel',
        to_field='code',
        related_name='orders',
        verbose_name='Статус доставки',
        null=False,
        default='new',
        blank=False,
        on_delete=CUSTOM_PROTECT,
    )
    delivery_address = common_fields.CustomCharField(
        max_length=1023,
        null=True,
        default="Не указан",
        blank=True,
        verbose_name=_('Delivery address')
    )
    delivery_date_plan_gte = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата доставки план. нач.',
    )
    delivery_date_plan_lte = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата доставки план. кон.'
    )
    delivery_date_fact = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата доставки факт.',
    )
    logistic_manager = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        related_name='logist_orders',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Менеджер транспортной компании',
        help_text='Для логистической задачи',
    )
    operator = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Водитель'),
        related_name='operator_orders',

    )
    car = common_fields.CustomCharField(
        max_length=1023,
        null=True,
        default="",
        blank=True,
        verbose_name=_('Автомобиль')
    )
    delivery_point = common_fields.CustomForeignKey(
        to='catalogs.DeliveryPointModel',
        related_name='orders',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Точка доставки',
        help_text='Для логистической задачи',
    )
    delivery_purpose = common_fields.CustomForeignKey(
        to='catalogs.DeliveryPurposeModel',
        related_name='orders',
        null=True,
        blank=True,
        default = '',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Назначение доставки'
    )
    delivery_company = common_fields.CustomForeignKey(
        'catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Транспортная компания',
    )
    pickup = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name="Самовывоз"
    )
    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default="",
        blank=True,
        verbose_name=_("Comment")
    )
    cash_payment_comment = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default="",
        blank=True,
        verbose_name="Комментарий к оплате")
    amount_no_discount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Сумма заказа(без скидки)'
    )
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Сумма заказа'
    )
    amount_paid = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Оплачено сумма',
    )
    amount_to_cash = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False, blank=True,
        default=0,
        verbose_name='Оплатить в кассу',
    )
    amount_to_cash_secondary = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False, blank=True,
        default=0,
        verbose_name='Оплатить в кассу по второму кошельку',
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Количество товаров'
    )
    must_paid = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=True,
        default=0,
        verbose_name='Сумма к оплате'
    )
    nds_amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Сумма НДС'
    )
    # Коды операций заказа необходимо получать из crm.enums.OperationTypeEnum.
    operation_type = common_fields.CustomForeignKey(
        'crm.OrderOperationTypeModel',
        verbose_name='Тип операции',
        related_name='orders',
        on_delete=CUSTOM_PROTECT,
        to_field='code',
        default='20'
    )
    pay_file = common_fields.CustomForeignKey(
        'common.File',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Файл счета на оплату',
        related_name='order_pay_file'
    )
    find_pay_file = models.BooleanField(default=False)
    order_form = common_fields.CustomForeignKey(
        'common.File',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Файл печатной формы',
        related_name='order_form_file'
    )
    find_order_form = models.BooleanField(default=False)

    goods = fields.GoodsFakeField()
    is_daily_created_filter = fields.IsDailyCreatedField()
    is_daily_delivery_filter = fields.IsDailyDeliveryField()
    without_logistic_task_filter = fields.WithoutLogisticTaskFilterField()

    co_executors = models.ManyToManyField(
        to='users.ProfileModel',
        blank=True,
        verbose_name="Соисполнители",
        through='crm.OrderCoExecutorModel'
    )

    @property
    def goods_content(self):
        return ', '.join(each.goods.name_short for each in self.tp_goodsorders.all())

    @property
    def must_paid_touched(self):
        return self.tp_goodsorders.filter(quantity_success_touched=True).exists()

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import GoodsOrderModelListSerializer, GoodsOrderModelDetailSerializer, \
            GoodsOrderModelNotifySerializer, GoodsOrderModelSearchSerializer
        if action == 'retrieve':
            return GoodsOrderModelDetailSerializer
        elif action == 'notify':
            return GoodsOrderModelNotifySerializer
        elif action == 'search':
            return GoodsOrderModelSearchSerializer
        return GoodsOrderModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        user = get_current_authenticated_profile()
        queryset = cls.objects.prefetch_related(
            # 'user__c1_roles',
            # 'operator__c1_roles',
            # 'logistic_manager__c1_roles',
            # 'warehouse__manager__c1_roles',
            'tp_goodsorders__goods',
            ).select_related(
                # 'user__user',
                # 'user__avatar',
            #     'warehouse__manager__user',
            #    'warehouse__manager__avatar',
                # 'operator__avatar',
                # 'operator__user',
                # 'logistic_manager__avatar',
                # 'logistic_manager__user',
            'warehouse__delivery_point',  # Кешируй весь склад
            'warehouse',
            'execute_status',
            #  'delivery_status',
            #  'payment_status',  # Кешируй
            'contract__price_type__currency',  # Кешируй весь контракт
            'contractor',
            'contractor_member',
            'delivery_point',
            'operation_type',
            # 'counter',
            'task_delivery_point',
            'task_delivery_point__task',
            'pay_type',  # кешируй
            ).filter(is_active=True)
        if user.check_profile_types({'superuser', 'admin', 'employee'}) or user.has_full_access_to_order_list:
            return queryset.annotate(
                amount_calculated=Sum('tp_goodsorders__amount'),
                quantity_calculated=Sum('tp_goodsorders__quantity'),
            ).order_by('-created_at')
        if user.is_storekeeper:
            warehouses = user.warehousemodel_set.filter(is_active=True).values_list('pk', flat=True)
            return queryset.filter(warehouse_id__in=warehouses).annotate(
                amount_calculated=Sum('tp_goodsorders__amount'),
                quantity_calculated=Sum('tp_goodsorders__quantity'),
            ).order_by('-created_at')
        return queryset.filter(Q(user=user) | Q(logistic_manager=user) | Q(operator=user)).distinct().annotate(
            amount_calculated=Sum('tp_goodsorders__amount'),
            quantity_calculated=Sum('tp_goodsorders__quantity'),
        ).order_by('-created_at')

    @classmethod
    def get_table_columns(cls):
        return (
            'number_1c',
            'user',
            'contractor',
            'amount',
            'created_at',
            'execute_status',
            'delivery_status',
            'payment_status',
            # 'delivery_address',
            'pay_type',
            'pay_date_plan',
            'must_paid',
            'delivery_date_plan_gte',
            'delivery_date_plan_lte',
            'goods',
            'warehouse',
            'is_daily_created_filter',
            'is_daily_delivery_filter',
            'without_logistic_task_filter',
        )

    def get_detail_permission(self, request):
        user = request.user.profile
        if user in (self.user, self.logistic_manager, self.operator, getattr(self.warehouse, 'manager', None)):
            return True
        if user.check_profile_types({'employee', 'superuser', 'admin'}) or user.has_full_access_to_order_list:
            return True
        task_delivery_point = self.task_delivery_point
        if task_delivery_point:
            task = task_delivery_point.task
            if task:
                return task.get_detail_permission(request)
        return False

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def has_characteristics_plan(cls):
        return True

    def save(self, *args, **kwargs):
        #Присвоение заказу статуса "Завершен" после доставки и оплаты
        if ((self.execute_status.code not in ['completed',]) and
            (self.delivery_status.code in ['partially_delivered', 'delivered']) and
            (self.payment_status.code in ['partially_paid', 'paid'])):
            self.execute_status_id = 'completed'
            # TODO Стоит пересмотреть логику!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.save(update_fields=('execute_status_id',),)
        super().save(*args, **kwargs)
        start_task_delivery_point = self.start_task_delivery_point
        warehouse = self.warehouse
        if start_task_delivery_point and warehouse and not (start_task_delivery_point.delivery_point == warehouse.delivery_point):
            start_task_delivery_point.delivery_point = warehouse.delivery_point
            start_task_delivery_point.save(update_fields=('delivery_point',))
            task = start_task_delivery_point.task
            from bpms.tasks.utils import send_socketio_about_update_task
            transaction.on_commit(lambda: async_task(send_socketio_about_update_task, task))
            initiator = get_current_authenticated_profile()
            if initiator:
                from bpms.tasks.notifications import notify_about_update_delivery_points
                transaction.on_commit(
                    lambda: async_task(notify_about_update_delivery_points, start_task_delivery_point.task, initiator)
                )

    class Meta:
        verbose_name = _('Заказ товаров')
        verbose_name_plural = _('Заказы товаров')


class TPGoodsOrderModel(BaseModel):
    owner = common_fields.CustomForeignKey(
        to='crm.GoodsOrderModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='tp_goodsorders',
        verbose_name=_('Order')
    )
    number = common_fields.CustomPositiveIntegerField(
        null=True,
        default=1,
        blank=True,
        verbose_name='Порядковый номер',
        validators=(MinValueValidator(1),)
    )
    goods = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        related_name='tp_goodsorders',
        verbose_name=_('goods'),
    )
    goods_for_print = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='tp_goodsorders_for_print',
        verbose_name="Товар для печати"
    )
    warehouse = common_fields.CustomForeignKey(
        to='catalogs.WarehouseModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        related_name='tp_goodsorders',
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        default=0,
        verbose_name=_('Quantity')
    )
    quantity_base = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        default=0,
        verbose_name=_('Quantity base')
    )
    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        # related_name='tp_goodsorders',
    )
    coefficient = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        default=1,
        verbose_name=_('Coefficient')
    )
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Amount')
    )
    amount_no_discount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Сумма без скидок'
    )
    price = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Price')
    )
    price_no_discount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name="Цена без скидки"
    )
    purchase_price = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Закупочная цена",
    )
    nds = common_fields.CustomCharField(
        max_length=255,
        default="",
        blank=True,
        verbose_name="Ставка НДС"
    )
    discount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Сумма скидки'
    )
    nds_amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name='Сумма НДС'
    )
    # Информация о доставке
    quantity_success = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        default=0,
        verbose_name="Количество принятых товаров",
    )
    quantity_success_touched = common_fields.CustomBooleanField(
        default=False,
        null=False,
        verbose_name="Изменено количество принятых товаров"
    )
    success_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата отгрузки")
    delivery_comment = models.CharField(max_length=500, default='', blank=True, verbose_name="Комментарий по доставке")


    def __str__(self):
        return f"{self.goods.article_number}"

    @property
    def calculated_price(self):
        return self.amount / self.quantity

    def get_detail_permission(self, request) -> bool:
        return self.owner.get_detail_permission(request)

    class Meta:
        verbose_name = _('Goods for order')
        verbose_name_plural = _('Goods for orders')
        unique_together = (('owner', 'goods', 'warehouse',),)


class CashPaymentOrderModel(BaseModel):
    owner = common_fields.CustomForeignKey(
        to='crm.GoodsOrderModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='cash_payment',
        verbose_name=_('Order')
    )
    cash_pay_type = common_fields.CustomForeignKey(
        to='crm.CashPayTypeModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name="Вид наличной оплаты",
    )
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Amount')
    )

    def get_detail_permission(self, request) -> bool:
        return self.owner.get_detail_permission(request)

    class Meta:
        verbose_name = "Наличная оплата заказа"
        verbose_name_plural = "Наличная оплата заказов"


class OrderCoExecutorModel(models.Model):
    order = models.ForeignKey(
        'crm.GoodsOrderModel',
        null=True,
        blank=False,
        verbose_name="Заказ",
        on_delete=CUSTOM_CASCADE
    )
    user = models.ForeignKey(
        'users.ProfileModel',
        null=True,
        blank=False,
        verbose_name="Пользователь",
        on_delete=CUSTOM_CASCADE
    )

    class Meta:
        unique_together = ('order', 'user',)
        verbose_name = 'Соисполнитель заказа'
        verbose_name_plural = 'Соисполнители заказа'


# class DeprecatedTPGoodsOrderModel(BaseAbstractModel):
#     owner = common_fields.CustomForeignKey(
#         to='crm.GoodsOrderModel',
#         on_delete=CUSTOM_CASCADE,
#         null=True,
#         blank=False,
#         related_name='tp_goodsorders',
#         verbose_name=_('Order')
#     )
#     number = common_fields.CustomPositiveIntegerField(
#         null=True,
#         default=1,
#         blank=True,
#         verbose_name='Порядковый номер',
#         validators=(MinValueValidator(1),)
#     )
#     goods = common_fields.CustomForeignKey(
#         to='catalogs.GoodsModel',
#         on_delete=CUSTOM_PROTECT,
#         null=True,
#         blank=False,
#         related_name='tp_goodsorders',
#         verbose_name=_('goods'),
#     )
#     warehouse = common_fields.CustomForeignKey(
#         to='catalogs.WarehouseModel',
#         on_delete=CUSTOM_PROTECT,
#         null=True,
#         blank=False,
#         related_name='tp_goodsorders',
#     )
#     quantity = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=3,
#         null=False,
#         default=0,
#         verbose_name=_('Quantity')
#     )
#     amount = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=False,
#         default=0,
#         verbose_name=_('Amount')
#     )
#     amount_no_discount = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=False,
#         default=0,
#         verbose_name='Сумма без скидок'
#     )
#     price = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=False,
#         default=0,
#         verbose_name=_('Price')
#     )
#     price_no_discount = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=False,
#         default=0,
#         verbose_name="Цена без скидки"
#     )
#     nds = common_fields.CustomCharField(
#         max_length=255,
#         default="",
#         blank=True,
#         verbose_name="Ставка НДС"
#     )
#     discount = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=False,
#         default=0,
#         verbose_name='Сумма скидки'
#     )
#     nds_amount = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=False,
#         default=0,
#         verbose_name='Сумма НДС'
#     )
#     # Информация о доставке
#     quantity_success = common_fields.CustomDecimalField(
#         max_digits=15,
#         decimal_places=3,
#         null=False,
#         default=0,
#         verbose_name="Количество принятых товаров",
#     )
#     success_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата отгрузки")
#     delivery_comment = models.CharField(max_length=500, default='', blank=True, verbose_name="Комментарий по доставке")
#
#     def __str__(self):
#         return f"{self.goods.article_number}"
#
#     @property
#     def calculated_price(self):
#         return self.amount / self.quantity
#
#     class Meta:
#         verbose_name = _('Goods for order')
#         verbose_name_plural = _('Goods for orders')
#         unique_together = (('owner', 'goods', 'warehouse',),)


# Deals are split into a dedicated module to keep this file manageable.
from .deals_models import DealModel, DealStageModel  # noqa: E402,F401
