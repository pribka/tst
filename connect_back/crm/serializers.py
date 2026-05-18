from decimal import Decimal
from django.db.models import Sum
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import serializers
from rest_framework import exceptions

from drf_haystack.serializers import HaystackSerializer
from django_q.tasks import async_task

from bkz3.settings import LOCAL_REMNANT_CONTROL
from users.serializers import AppUserSerializer
from common.models import BaseModel, File
from common.utils import get_serialized_attachments
from common.serializers import BaseCatalogRetrieveSerializer
from common.serializers import CachedBaseCatalogSerializer, CachedBaseModelSerializer
from common.current_profile.middleware import get_current_authenticated_profile
from common.catalogs.models import GoodsModel, ContractModel, ContractorModel, DeliveryAddress, WarehouseModel, \
    CurrencyModel, ContractorMemberModel, DeliveryPointModel, PaymentFormModel, CashUnitModel, MeasureUnitModel, \
    DeliveryPurposeModel
from common.catalogs.utils import get_current_price_type
from common.catalogs.serializers import AppWarehouseSerializer, GoodsCategoryShortSerializer, \
    AppDeliveryAddressSerializer, GoodsTypeAppSerializer, DeliveryPointSerializer, PaymentFormListSerializer, \
    MeasureUnitListSerializer, DeliveryPurposeSerializer, GoodsModelForPrintSerializer

from users.serializers import AppUserSerializer

from app_info.models import AppInfo

from . import models
from . import search_indexes
from . import validators
from .enums import OperationTypeEnum
from bkz3.settings import SHOW_CONTRACT_IN_GOODS_ORDER
from bkz3.settings import SHOW_PAY_TYPE_IN_GOODS_ORDER, ORDER_DELIVERY
from common.catalogs.utils import get_price_by_catalog_for_serializer
from users.models import ProfileModel
from bkz3.settings import DEFAULT_PRICE_CURRENCY
from users.serializers import CachedAppUserSerializer


def get_order_reason_data(instance):
    reason_id = getattr(instance, 'reason_id', None)
    if not reason_id:
        return None
    reason = BaseModel.objects.super_get(reason_id)
    if not reason:
        return {
            'id': str(reason_id)
        }
    return {
        'id': str(reason.pk),
        'type': reason.get_label(),
        'name': getattr(reason, 'name', '') or getattr(reason, 'counter', '') or str(reason),
    }


def get_order_customer_contract_data(instance):
    """Короткие данные CRM-договора для списка/карточки заказа.

    Важно: здесь намеренно не выбираем customer_card за заказ. Получатель
    отгрузки хранится в GoodsOrderModel.customer_card и сериализуется отдельно.
    """
    customer_contract = getattr(instance, 'customer_contract', None)
    if not customer_contract:
        return None
    from customer_contracts.serializers import CustomerContractShortSerializer
    data = CustomerContractShortSerializer(customer_contract).data
    serviced_relations = getattr(customer_contract, '_prefetched_objects_cache', {}).get('serviced_cards_relations')
    serviced_cards = []
    if serviced_relations is not None:
        serviced_cards = [
            relation.customer_card
            for relation in serviced_relations
            if getattr(relation, 'customer_card', None)
        ]
    elif customer_contract.pk:
        serviced_cards = [
            relation.customer_card
            for relation in customer_contract.serviced_cards_relations.filter(
                is_active=True,
                customer_card__is_active=True,
            ).select_related('customer_card')[:5]
            if relation.customer_card
        ]
    source_items = getattr(customer_contract, '_prefetched_objects_cache', {}).get('subject_items')
    source_subject = None
    if source_items is not None:
        source_subject = next((item for item in source_items if item.source_interest_id), None)
    if source_subject is None:
        source_subject = customer_contract.subject_items.filter(
            is_active=True,
            source_interest__isnull=False,
        ).select_related('source_interest').order_by('created_at').first()
    source_interest = getattr(source_subject, 'source_interest', None)
    data.update({
        'number': customer_contract.number,
        'amount': serializers.DecimalField(
            max_digits=14,
            decimal_places=2,
        ).to_representation(customer_contract.amount or Decimal('0')),
    })
    if serviced_cards:
        data['customer_cards'] = [
            {
                'id': str(card.pk),
                'name': getattr(card, 'name', '') or str(card),
            }
            for card in serviced_cards
        ]
    if source_interest:
        data['source_interest'] = {
            'id': str(source_interest.pk),
            'counter': getattr(source_interest, 'counter', None),
            'name': getattr(source_interest, 'name', '') or str(source_interest),
        }
    return data


def get_order_customer_card_data(instance):
    """Явно выбранный CRM-клиент заказа, которому оформляется отгрузка."""
    customer_card = getattr(instance, 'customer_card', None)
    if not customer_card:
        return None
    return {
        'id': str(customer_card.pk),
        'name': getattr(customer_card, 'name', '') or str(customer_card),
    }


def get_order_customer_contract_progress(instance):
    """Сводка по договору: сумма предмета, заказано и отгружено по заказам."""
    customer_contract = getattr(instance, 'customer_contract', None)
    if not customer_contract:
        return None
    contract_orders = models.GoodsOrderModel.objects.filter(
        is_active=True,
        customer_contract=customer_contract,
    )
    contract_order_rows = models.TPGoodsOrderModel.objects.filter(
        is_active=True,
        owner__in=contract_orders,
    )
    subject_amount = customer_contract.subject_items.filter(is_active=True).aggregate(Sum('amount'))['amount__sum']
    ordered_amount = contract_order_rows.aggregate(Sum('amount'))['amount__sum']
    delivered_quantity = contract_order_rows.aggregate(Sum('quantity_success'))['quantity_success__sum']
    formatter = serializers.DecimalField(max_digits=15, decimal_places=2)
    quantity_formatter = serializers.DecimalField(max_digits=15, decimal_places=3)
    return {
        'contract_amount': formatter.to_representation(customer_contract.amount or Decimal('0')),
        'subject_amount': formatter.to_representation(subject_amount or Decimal('0')),
        'ordered_amount': formatter.to_representation(ordered_amount or Decimal('0')),
        'delivered_quantity': quantity_formatter.to_representation(delivered_quantity or Decimal('0')),
        'order_count': contract_orders.count(),
    }


class GoodsShoppingCartSerializer(serializers.ModelSerializer):
    price_by_catalog = serializers.SerializerMethodField()
    base_measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = GoodsModel
        fields = (
            'id',
            'name',
            'code',
            'article_number',
            'price_by_catalog', 'base_measure_unit'
        )

    def get_price_by_catalog(self, instance):
        return get_price_by_catalog_for_serializer(instance)


class OrderOperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderOperationTypeModel
        fields = (
            'id',
            'name',
            'code',
        )


class GoodsOrderExecuteStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsOrderExecuteStatusModel
        fields = (
            'id',
            'name',
            'code',
            'created_at',
            'color',
            'icon',
        )


class GoodsOrderPaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PaymentStatusModel
        fields = (
            'id',
            'name',
            'code',
            'created_at',
            'color',
            'icon',
        )

    def to_representation(self, instance):
        if not isinstance(instance, models.PaymentStatusModel):
            instance = models.PaymentStatusModel.objects.get(code=instance)
        return super().to_representation(instance)


class GoodsOrderDeliveryStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.DeliveryStatusModel
        fields = (
            'id',
            'name',
            'code',
            'created_at',
            'color',
            'icon',
        )

    def to_representation(self, instance):
        if not isinstance(instance, models.DeliveryStatusModel):
            instance = models.DeliveryStatusModel.objects.get(code=instance)
        return super().to_representation(instance)


class ShoppingCartModelDetailSerializer(serializers.ModelSerializer):
    goods = serializers.SerializerMethodField()
    goods_for_print = GoodsModelForPrintSerializer()
    warehouse = AppWarehouseSerializer()
    measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = models.ShoppingCartModel
        fields = (
            'id',
            'goods',
            'goods_for_print',
            'quantity',
            'warehouse',
            'measure_unit',
            'coefficient',
            'custom_price',
        )

    def get_goods(self, instance):
        data = GoodsShoppingCartSerializer(instance.goods).data
        price_type = get_current_price_type()
        price_type_id = price_type.code
        price = instance.goods.prices.filter(is_active=True, price_type_id=price_type_id).first()
        data['price'] = serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(
            getattr(price, 'price', None))
        data['currency'] = {'name': getattr(getattr(price_type, 'currency', None), 'name', ''),
                            'icon': getattr(getattr(price_type, 'currency', None), 'icon', ''), }
        data['image'] = getattr(instance.goods.gallery.filter(is_main=True, is_active=True).first(), 'path', '')
        data['available_count'] = instance.goods.remnants.all().aggregate(Sum('quantity'))['quantity__sum']
        data['is_availability'] = bool(data['available_count'])
        data['price_by_catalog'] = get_price_by_catalog_for_serializer(instance.goods)
        data['number'] = None
        data['nds'] = 'Не расчитано'
        data['price_no_discount'] = None
        data['amount_no_discount'] = None
        data['nds_amount'] = None
        data['amount'] = None
        return data


class ShoppingCartModelListSerializer(serializers.ModelSerializer):
    goods = serializers.SerializerMethodField()
    goods_for_print = GoodsModelForPrintSerializer()
    warehouse = AppWarehouseSerializer()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = models.ShoppingCartModel
        fields = (
            'id',
            'goods',
            'goods_for_print',
            'quantity',
            'amount',
            'warehouse',
            'measure_unit',
            'coefficient',
            'custom_price',
        )

    def get_image(self, instance):
        images = list(instance.goods.gallery.all())
        if images:
            return images[0].path
        else:
            return ''

    def get_goods(self, instance):
        data = GoodsShoppingCartSerializer(instance.goods).data
        data['currency'] = {'name': getattr(instance, 'currency_name', ''),
                            'icon': getattr(instance, 'currency_icon', ''), }
        data['image'] = self.get_image(instance)
        data['price'] = serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(
            getattr(instance, 'price', None))
        quantity = getattr(instance, 'remnant_sum', 0)
        if quantity is None:
            quantity = 0
        data['available_count'] = quantity
        data['number'] = None
        data['is_availability'] = bool(quantity)
        data['price_by_catalog'] = get_price_by_catalog_for_serializer(instance.goods)
        data['default_price_currency'] = DEFAULT_PRICE_CURRENCY  # TODO завязать на выборку

        return data


class ShoppingCartModelListTo1CSerializer(serializers.ModelSerializer):
    # amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        model = models.ShoppingCartModel
        fields = (
            # 'id',
            'goods',
            'goods_for_print',
            'quantity',
            # 'amount',
            'warehouse',
            'measure_unit',
            'coefficient',
            'custom_price',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['goods'] = str(instance.goods.id)
        data['goods_for_print'] = str(instance.goods_for_print.id) if instance.goods_for_print else str(
            instance.goods.id)
        if instance.warehouse:
            data['warehouse'] = str(instance.warehouse.id)
        else:
            data['warehouse'] = None
        measure_unit = data['measure_unit']
        if measure_unit:
            data['measure_unit'] = str(measure_unit)
        return data


class TPGoodsOrderModelListTo1CSerializer(ShoppingCartModelListTo1CSerializer):
    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            # 'id',
            'goods',
            'quantity',
            # 'amount',
            'warehouse',
            'measure_unit',
            'coefficient',
        )


class ShoppingCartModelCreateSerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(max_digits=15,
                                        decimal_places=3,
                                        validators=[validators.validate_quantity, ])
    is_draft = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = models.ShoppingCartModel
        fields = (
            'id',
            'goods',
            'warehouse',
            'quantity',
            'measure_unit',
            'coefficient',
            'custom_price',
            'is_draft',
        )

    def create(self, validated_data):
        quantity = validated_data.get('quantity', 0)
        if quantity == 0:
            quantity = 1
        is_draft = validated_data.pop('is_draft', False)
        cart_type = self.context.get('view').cart_type
        measure_unit = validated_data.get('measure_unit', None)
        coefficient = validated_data.get('coefficient', 1)
        custom_price = validated_data.get('custom_price', None)
        if not is_draft:
            instance, created = models.ShoppingCartModel.objects.get_or_create(
                user=get_current_authenticated_profile(),
                goods=validated_data.get('goods'),
                warehouse=validated_data.get('warehouse'),
                cart_type_id=cart_type,
                defaults={
                    'quantity': quantity,
                    'measure_unit': measure_unit,
                    'coefficient': coefficient,
                    'custom_price': custom_price,
                }
            )

            if not created:
                if LOCAL_REMNANT_CONTROL:
                    count_in_warehouse = instance.goods.remnants.filter(
                        warehouse=instance.warehouse
                    ).aggregate(count_sum=Sum('quantity'))['count_sum']
                    if count_in_warehouse is None:
                        count_in_warehouse = 0
                    if not count_in_warehouse >= instance.quantity + quantity:
                        raise exceptions.ValidationError('No remnants.')
                instance.quantity += quantity
                instance.measure_unit = measure_unit
                instance.coefficient = coefficient
                instance.custom_price = custom_price
                instance.save()
        else:
            instance = models.ShoppingCartModel()
            instance.goods = validated_data.get("goods")
            instance.warehouse = validated_data.get("warehouse")
            instance.quantity = quantity
            instance.measure_unit = measure_unit
            instance.coefficient = coefficient
            instance.custom_price = custom_price if custom_price is not None else instance.goods.price_by_catalog
        return instance

    def validate(self, data):
        warehouse = data.get('warehouse')
        goods = data.get('goods')
        storage_type = data.get('storage_type', 'default')
        if not goods:
            raise exceptions.ValidationError('Goods cannot be null')
        quantity = data.get('quantity')
        if quantity == 0:
            quantity = 1
        if not warehouse:
            remnant = goods.remnants.filter(is_active=True, storage_type=storage_type).order_by('-quantity', ).first()
            if not remnant:
                if LOCAL_REMNANT_CONTROL:
                    raise exceptions.ValidationError('No remnants.')
                else:
                    pass
            else:
                warehouse = remnant.warehouse
                data['warehouse'] = remnant.warehouse
        try:
            remnant = goods.remnants.get(warehouse=warehouse, storage_type=storage_type, is_active=True)
        except ObjectDoesNotExist:
            if LOCAL_REMNANT_CONTROL:
                raise exceptions.ValidationError('No remnants.')
            else:
                remnant = None

        if LOCAL_REMNANT_CONTROL and quantity > remnant.quantity:
            raise exceptions.ValidationError('Too much quantity.')
        custom_price = data.get('custom_price')
        if custom_price is not None:
            user = get_current_authenticated_profile()
            if not user.has_full_access_to_order_editing:
                raise exceptions.PermissionDenied('You cannot change custom_price.')
            if custom_price < goods.price_by_catalog:
                raise exceptions.ValidationError('Incorrect custom_price.')
        return data

    def to_representation(self, instance):
        return ShoppingCartModelDetailSerializer(instance, context=self.context).data


class ShoppingCartModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShoppingCartModel
        fields = (
            'id',
            'quantity',
            'measure_unit',
            'coefficient',
            'custom_price',
            'warehouse',
            'goods_for_print',
        )

    def validate(self, data):
        instance = self.instance
        if instance:
            goods = instance.goods
            if goods:
                custom_price = data.get('custom_price')
                if custom_price is not None:
                    user = get_current_authenticated_profile()
                    if not user.has_full_access_to_order_editing:
                        raise exceptions.PermissionDenied('You cannot change custom_price.')
                    if custom_price < goods.price_by_catalog:
                        raise exceptions.ValidationError('Incorrect custom_price.')
        return data

    def validate_quantity(self, data):
        if LOCAL_REMNANT_CONTROL:
            instance = self.instance
            try:
                remnant = instance.goods.remnants.get(warehouse=instance.warehouse, is_active=True)
            except ObjectDoesNotExist:
                raise exceptions.ValidationError('No remnants.')
            if data > remnant.quantity:
                raise exceptions.ValidationError('Too much quantity.')
        return data

    def to_representation(self, instance):
        return ShoppingCartModelDetailSerializer(instance, context=self.context).data


class DeliveryDatePlanMixin:
    def get_delivery_date_plan(self, instance):
        s_field = serializers.DateTimeField()
        return {
            "delivery_date_plan_gte": s_field.to_representation(instance.delivery_date_plan_gte),
            "delivery_date_plan_lte": s_field.to_representation(instance.delivery_date_plan_lte),
        }


class GoodsOrderModelListSerializer(serializers.ModelSerializer, DeliveryDatePlanMixin):
    quantity = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    warehouse = AppWarehouseSerializer()
    contractor = CachedBaseModelSerializer(
        serializer_class=BaseCatalogRetrieveSerializer,
        source='contractor_id'
    )
    contractor_phone = serializers.SerializerMethodField()
    contractor_member = CachedBaseModelSerializer(
        serializer_class=BaseCatalogRetrieveSerializer,
        source='contractor_member_id'
    )
    contract = CachedBaseCatalogSerializer(
        serializer_class=BaseCatalogRetrieveSerializer,
        model=ContractModel,
        source='contract_id'
    )
    execute_status = GoodsOrderExecuteStatusSerializer()
    currency = serializers.SerializerMethodField()
    operation_type = OrderOperationTypeSerializer()
    counter = serializers.SerializerMethodField()
    delivery_point = DeliveryPointSerializer()
    delivery_purpose = DeliveryPurposeSerializer()
    start_delivery_point = serializers.SerializerMethodField()
    operator = CachedAppUserSerializer(source='operator_id')  # AppUserSerializer()
    logistic_manager = CachedAppUserSerializer(source='logistic_manager_id')  # AppUserSerializer()
    delivery_status = CachedBaseCatalogSerializer(
        serializer_class=GoodsOrderDeliveryStatusSerializer,
        model=models.DeliveryStatusModel,
        source='delivery_status_id'
    )
    payment_status = CachedBaseCatalogSerializer(
        serializer_class=GoodsOrderPaymentStatusSerializer,
        model=models.PaymentStatusModel,
        source='payment_status_id')
    user = CachedAppUserSerializer(source='user_id')  # AppUserSerializer()
    logistic_task = serializers.SerializerMethodField()
    pay_type = PaymentFormListSerializer()
    delivery_date_plan = serializers.SerializerMethodField()
    customer_contract = serializers.SerializerMethodField()
    customer_card = serializers.SerializerMethodField()
    customer_contract_progress = serializers.SerializerMethodField()

    def get_counter(self, instance):
        if instance.number_1c:
            return instance.number_1c
        return instance.counter.pk

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'counter',
            'warehouse',
            'contractor',
            'contractor_phone',
            'user',
            'contractor_member',
            'contract',
            'customer_contract',
            'customer_card',
            'customer_contract_progress',
            'execute_status',
            'pickup',
            'quantity',
            'amount',
            'must_paid',
            'nds_amount',
            'operation_type',
            'currency',
            'created_at',
            'updated_at',
            'deleted_at',
            'delivery_date_fact',
            'delivery_point',
            'delivery_purpose',
            'start_delivery_point',
            'operator',
            'logistic_manager',
            'logistic_task',
            'delivery_status',
            'payment_status',
            'pay_date_plan',
            'delivery_date_plan',
            'start_delivery_point',
            'pay_type',
            'goods_content',
        )

    #
    # def to_representation(self, instance):
    #     model_serialized_fields = []
    #     fields = self.fields.items()
    #     for key, value in fields:
    #         if isinstance(value, serializers.ModelSerializer):
    #             model_serialized_fields.append(key)
    #     return super().to_representation(instance)

    def get_quantity(self, instance):
        # quantity = instance.quantity_calculated
        # if instance.quantity == 0:
        #     quantity = instance.tp_goodsorders.all().aggregate(Sum('quantity'))['quantity__sum']
        # else:
        #     quantity = instance.quantity
        try:
            quantity = instance.quantity_calculated
        except AttributeError:
            quantity = instance.tp_goodsorders.all().aggregate(Sum('quantity'))['quantity__sum']
        if quantity is None:
            quantity = 0
        return serializers.DecimalField(max_digits=15, decimal_places=3).to_representation(quantity)
    
    def get_contractor_phone(self, instance):
        return instance.contractor.phone if instance.contractor else ''

    def get_amount(self, instance):
        # amount = instance.amount_calculated
        if instance.amount == 0:
            amount = instance.tp_goodsorders.all().aggregate(Sum('amount'))['amount__sum']
        else:
            amount = instance.amount
        return serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(amount)

    def get_currency(self, instance):
        currency = instance.contract.price_type.currency
        return {'name': currency.name, 'icon': currency.icon}

    def get_logistic_task(self, instance):
        task_delivery_point = instance.task_delivery_point
        if task_delivery_point:
            task = task_delivery_point.task
            if task:
                from bpms.tasks.serializers import ShortTaskSerializer
                return ShortTaskSerializer(task).data
            else:
                return None
        else:
            return None

    def get_start_delivery_point(self, instance):
        warehouse = instance.warehouse
        if warehouse:
            start_delivery_point = warehouse.delivery_point
            if start_delivery_point:
                return DeliveryPointSerializer(start_delivery_point).data
            else:
                return None
        else:
            return None

    def get_customer_contract(self, instance):
        return get_order_customer_contract_data(instance)

    def get_customer_card(self, instance):
        return get_order_customer_card_data(instance)

    def get_customer_contract_progress(self, instance):
        return get_order_customer_contract_progress(instance)


class GoodsOrderModelNotifySerializer(serializers.ModelSerializer):
    user = CachedAppUserSerializer(source='user_id')
    contractor = BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'counter',
            'user',
            'contractor',
            'contract',
            'execute_status',
            'number_1c',
            'amount',
        )


class ContractorShortModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name'
        )


class GoodsOrderModelDetailSerializer(serializers.ModelSerializer, DeliveryDatePlanMixin):
    amount = serializers.SerializerMethodField()
    amount_no_discount = serializers.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    attachments = serializers.SerializerMethodField()
    button_name = serializers.SerializerMethodField()
    cash_pay_recipient = AppUserSerializer()
    cash_pay_type = BaseCatalogRetrieveSerializer()
    co_executors = AppUserSerializer(many=True)
    contract = BaseCatalogRetrieveSerializer()
    contractor = BaseCatalogRetrieveSerializer()
    contractor_member = BaseCatalogRetrieveSerializer()
    currency = serializers.SerializerMethodField()
    counter = serializers.SerializerMethodField()
    delivery_company = ContractorShortModelSerializer()
    delivery_date_plan = serializers.SerializerMethodField()
    delivery_point = DeliveryPointSerializer()
    delivery_purpose = DeliveryPurposeSerializer()
    delivery_status = GoodsOrderDeliveryStatusSerializer()
    delivery_warehouses = serializers.SerializerMethodField()
    execute_status = GoodsOrderExecuteStatusSerializer()
    has_print = serializers.SerializerMethodField()
    has_pay_file = serializers.SerializerMethodField()
    logistic_manager = AppUserSerializer()
    logistic_task = serializers.SerializerMethodField()
    operator = AppUserSerializer()
    operation_type = OrderOperationTypeSerializer()
    pay_type = PaymentFormListSerializer()
    payment_status = GoodsOrderPaymentStatusSerializer()
    quantity = serializers.SerializerMethodField()
    show_pay_type = serializers.SerializerMethodField()
    show_nds = serializers.SerializerMethodField()
    user = AppUserSerializer()
    last_editor = AppUserSerializer()
    user_phone = serializers.SerializerMethodField()
    warehouse = AppWarehouseSerializer()
    reason = serializers.SerializerMethodField()
    customer_contract = serializers.SerializerMethodField()
    customer_card = serializers.SerializerMethodField()
    customer_contract_progress = serializers.SerializerMethodField()
    # delivery_address = AppDeliveryAddressSerializer()

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'amount',
            'amount_no_discount',
            'amount_paid',
            'attachments',
            'button_name',
            'car',
            'cash_pay_recipient',
            'cash_pay_type',
            'co_executors',
            'comment',
            'contract',
            'customer_contract',
            'customer_card',
            'customer_contract_progress',
            'contractor',
            'contractor_member',
            'counter',
            'created_at',
            'currency',
            'deleted_at',
            'delivery_address',
            'delivery_company',
            'delivery_date_fact',
            'delivery_date_plan',
            'delivery_point',
            'delivery_purpose',
            'delivery_status',
            'delivery_warehouses',
            'execute_status',
            'has_pay_file',
            'has_print',
            'logistic_manager',
            'logistic_task',
            'must_paid',
            'must_paid_touched',
            'nds_amount',
            'operation_type',
            'operator',
            'pay_date_plan',
            'pay_type',
            'payment_status',
            'pickup',
            'quantity',
            'show_nds',
            'show_pay_type',
            'updated_at',
            'user',
            'user_phone',
            'warehouse',
            'last_editor',
            'reason',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not SHOW_CONTRACT_IN_GOODS_ORDER:
            data.pop('contract')
        # if 1 == 1:
        #     data.pop('operation_type')
        data['show_operation_type'] = False
        return data

    def get_has_pay_file(self, instance):
        result = False
        if instance.pay_file:
            result = True
        return result

    def get_has_print(self, instance):
        result = False
        # if instance.order_form:
        #     result = True
        return result

    def get_show_pay_type(self, instance):
        return SHOW_PAY_TYPE_IN_GOODS_ORDER

    def get_counter(self, instance):
        if instance.number_1c:
            return instance.number_1c
        return instance.counter.pk

    def get_button_name(self, instance):
        operation_type_code = instance.operation_type.code
        result = None
        if operation_type_code == OperationTypeEnum.offer.value:
            result = 'Получить цены'
        return result

    def get_quantity(self, instance):
        # if instance.quantity == 0:
        #     quantity = instance.tp_goodsorders.all().aggregate(Sum('quantity'))['quantity__sum']
        # else:
        #     quantity = instance.quantity
        try:
            quantity = instance.quantity_calculated
        except AttributeError:
            quantity = instance.tp_goodsorders.all().aggregate(Sum('quantity'))['quantity__sum']
        if quantity is None:
            quantity = 0
        return serializers.DecimalField(max_digits=15, decimal_places=3).to_representation(quantity)

    def get_amount(self, instance):
        if instance.amount == 0:
            amount = instance.tp_goodsorders.all().aggregate(Sum('amount'))['amount__sum']
        else:
            amount = instance.amount
        return serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(amount)

    def get_currency(self, instance):
        currency = instance.contract.price_type.currency
        return {'name': currency.name, 'icon': currency.icon}

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def get_delivery_warehouses(self, instance):
        qs = WarehouseModel.objects.select_related('manager__user').filter(
            tp_goodsorders__owner=instance,
            is_active=True
        ).distinct()
        return AppWarehouseSerializer(qs, many=True).data

    def get_logistic_task(self, instance):
        task_delivery_point = instance.task_delivery_point
        if task_delivery_point:
            task = task_delivery_point.task
            if task:
                from bpms.tasks.serializers import ShortTaskSerializer
                return ShortTaskSerializer(task).data
            else:
                return None
        else:
            return None

    def get_show_nds(self, instance):
        try:
            metadata = AppInfo.objects.get(is_active=True, code='orders_form_info').metadata
        except AppInfo.DoesNotExist:
            return True
        return metadata.get('aside', dict()).get('show_nds', True)

    def get_user_phone(self, instance):
        return getattr(instance.user, 'phone', '')

    def get_reason(self, instance):
        return get_order_reason_data(instance)

    def get_customer_contract(self, instance):
        return get_order_customer_contract_data(instance)

    def get_customer_card(self, instance):
        return get_order_customer_card_data(instance)

    def get_customer_contract_progress(self, instance):
        return get_order_customer_contract_progress(instance)


class CrmGoodsModelSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    category = GoodsCategoryShortSerializer()
    goods_type = GoodsTypeAppSerializer()

    class Meta:
        model = GoodsModel
        fields = (
            'id',
            'code',
            'name',
            'goods_type',
            'article_number',
            'image',
            'category'
        )

    def get_image(self, instance):
        images = list(instance.gallery.filter(is_main=True))
        if images:
            return images[0].path
        else:
            return ''


class TPGoodsOrderModelListSerializer(serializers.ModelSerializer):
    goods = CrmGoodsModelSerializer()
    goods_for_print = GoodsModelForPrintSerializer()
    warehouse = AppWarehouseSerializer()
    price = serializers.SerializerMethodField()
    measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'id',
            'goods',
            'goods_for_print',
            'warehouse',
            'amount',
            'price',
            'price_no_discount',
            'nds',
            'nds_amount',
            'amount_no_discount',
            'discount',
            'number',
            'discount',
            'quantity',
            'created_at',
            'updated_at',
            'deleted_at',
            # Информация о доставке:
            'quantity_success',
            'success_date',
            'delivery_comment',
            'measure_unit',
            'coefficient',
        )

    def get_price(self, instance):
        if instance.price:
            price = instance.price
        else:
            price = instance.calculated_price
        return serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(
            price
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        goods = data.get('goods')
        if goods:
            data['goods']['available_count'] = getattr(instance, 'remnant_sum', 0)
        return data


class TPGoodsOrderModelDeliveryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'id',
            'quantity_success',
            'delivery_comment',
            'attachments',
        )

    # def validate_quantity_success(self, attr):
    #     if attr > self.instance.quantity:
    #         raise exceptions.ValidationError('invalid quantity_success')
    #     return attr

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.quantity_success = validated_data.get('quantity_success', 0)
            instance.delivery_comment = validated_data.get('delivery_comment', '')
            instance.success_date = timezone.now()
            instance.quantity_success_touched = True
            instance.save(
                update_fields=('quantity_success', 'delivery_comment', 'success_date', 'quantity_success_touched')
            )
            instance.attachments.set(validated_data.get('attachments', []))
        return instance

    def to_representation(self, instance):
        return TPGoodsOrderModelListSerializer(instance).data


class CreateGoodsOrderFromCartSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True),
    )

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'contractor',
            'contract',
            'customer_contract',
            'customer_card',
            'delivery_address',
            'pickup',
            'comment',
            'attachments',
            'operation_type',
        )

    def validate(self, data):
        user = get_current_authenticated_profile()
        if not models.ShoppingCartModel.objects.filter(user=user, cart_type_id='shopping_cart', ).exists():
            raise exceptions.ValidationError('Shopping cart cannot be empty.')
        contractor = data.get('contractor', None)
        if not contractor:
            contractor = user.contractors.first()
            if not contractor:
                raise exceptions.ValidationError('Contractor does not exist.')
        else:
            if not user.contractors.filter(pk=contractor.pk).exists():
                raise exceptions.ValidationError('Invalid contractor.')
        contract = data.get('contract', None)
        if not contract:
            contract = ContractModel.objects.get(code='default')
        else:
            if not contractor.contracts.filter(contract=contract).exists():
                raise exceptions.ValidationError('Invalid contract.')

        if data.get('pickup', False):
            data['delivery_address'] = None
        else:
            is_delivery_address_srt = data.get('is_delivery_address_str')
            if is_delivery_address_srt:
                delivery_address_srt = data.get('delivery_address_str')
                if delivery_address_srt == "" or is_delivery_address_srt == None:
                    raise exceptions.ValidationError('Не указан адресс доставки"')
                delivery_address = delivery_address_srt
            else:
                delivery_address_id = data.get('delivery_address')
                try:
                    delivery_address_obj = DeliveryAddress.objects.filter(id=delivery_address_id)
                except:
                    raise exceptions.ValidationError('Не указан адресс доставки"')
                delivery_address = delivery_address_obj.address

        data['delivery_address'] = delivery_address
        data['contractor'] = contractor
        data['contract'] = contract
        return data

    def create(self, validated_data):
        operation_type = validated_data.pop('oper_type')
        # is_delivery_address_srt = validated_data.pop('is_delivery_address_srt', False)
        delivery_address_str = validated_data.pop('delivery_address', "")
        pickup = validated_data.get('pickup')

        with transaction.atomic():
            user = get_current_authenticated_profile()
            attachments = validated_data.pop('attachments', [])
            if not pickup:
                validated_data['delivery_address'] = delivery_address_str

            instance = self.Meta.model.objects.create(
                user=user,
                **validated_data,
            )
            if attachments:
                instance.attachments.set(attachments)
            shopping_cart = models.ShoppingCartModel.objects.filter(user=user, cart_type_id='shopping_cart', )
            price_type = validated_data.get('contract').price_type
            for each in shopping_cart:
                try:
                    price = each.goods.prices.get(price_type=price_type).price
                except ObjectDoesNotExist:
                    raise exceptions.ValidationError(
                        f'Товар {each.goods.article_number} {each.goods.name} не имеет цены для данного соглашения.')
                instance.tp_goodsorders.create(
                    goods=each.goods,
                    warehouse=each.warehouse,
                    quantity=each.quantity,
                    amount=price * each.quantity,
                )
            shopping_cart.delete()
        return instance


class CreateFrom1CGoodsOrderSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()

    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    co_executors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'amount',
            'amount_paid',
            'amount_to_cash',
            'amount_to_cash_secondary',
            'attachments',
            'car',
            'cash_pay_recipient',
            'cash_pay_type',
            'cash_unit',
            'cash_unit_secondary',
            'comment',
            'contractor',
            'contractor_member',
            'contract',
            'customer_contract',
            'customer_card',
            'delivery_address',
            'delivery_company',
            'delivery_date_plan_gte',
            'delivery_date_plan_lte',
            'delivery_point',
            'delivery_purpose',
            'logistic_manager',
            'must_paid',
            'nds_amount',
            'number_1c',
            'operation_type',
            'operator',
            'quantity',
            'pay_date_plan',
            'pay_type',
            'pickup',
            'reason',
            'user',
            'warehouse',
            'co_executors'
        )

    def to_internal_value(self, data):
        delivery_point = data.get('delivery_point')
        delivery_purpose = data.get('delivery_purpose')
        if delivery_point:
            data['delivery_point'] = delivery_point.get('id')
        if delivery_purpose:
            data['delivery_purpose'] = delivery_purpose.get('id')
        return super().to_internal_value(data)

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.create_table_part(instance, validated_data)
        return instance

    def update(self, instance, validated_data):
        validated_data.pop('id', None)
        validated_data.pop('operation_type', None)
        if instance.user:
            validated_data.pop('user', )
        instance = super().update(instance, validated_data)
        instance.tp_goodsorders.clear(bulk=False)
        self.create_table_part(instance, validated_data)
        return instance

    def create_table_part(self, instance, validated_data):
        tp_goods = self.initial_data['tp_goods']
        for tp_goods_elem in tp_goods:
            tp_goods_elem['owner'] = instance
            tp_goods_elem['goods_id'] = tp_goods_elem.pop('goods')
            tp_goods_elem['goods_for_print_id'] = tp_goods_elem.pop('goods_for_print', tp_goods_elem['goods_id'])
            tp_goods_elem['amount_no_discount'] = tp_goods_elem.pop('amounnodiscount')
            # tp_goods_elem['warehouse_id'] = tp_goods_elem.pop('warehouse')
            tp_goods_elem.pop('warehouse')
            if validated_data.get('warehouse'):
                tp_goods_elem['warehouse_id'] = str(validated_data['warehouse'].id)
            else:
                tp_goods_elem['warehouse'] = None
            tp_goods_elem['nds_amount'] = tp_goods_elem.pop('amountnds')
            tp_goods_elem['number'] = tp_goods_elem.pop('num')
            tp_goods_elem['measure_unit_id'] = tp_goods_elem.pop('measure_unit', None)
            tp_goods_elem['coefficient'] = tp_goods_elem.pop('coefficient', 1)
            tp_goods_elem.pop('custom_price', None)
        ready_to_create = [models.TPGoodsOrderModel(**vals) for vals in tp_goods]
        # GoodsRemnantModel.objects.bulk_create(ready_to_create)
        for item in ready_to_create:
            item.save()


class CreateFrom1CGoodsOrderTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'id',
            'owner',
            'warehouse',
            'quantity',
            'price',
            'nds',
            'nds_amount',
            'discount',
            'amount',
        )


class GoodsOrderTPTo1CSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'goods',
            'quantity',
        )


class CreateOrderOfferTo1CSerializer(serializers.ModelSerializer):
    operation_type = serializers.SerializerMethodField()
    tp_goodsorders = GoodsOrderTPTo1CSerializer(many=True)

    def get_operation_type(self, instance):
        return instance.operation_type.code

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'counter',
            'contractor',
            'contract',
            'delivery_address',
            'pickup',
            'comment',
            'nds_amount',
            'operation_type',
            'tp_goodsorders',

        )


class CreateOfferFromCartSerializer(serializers.ModelSerializer):
    class Meta:
        models = models.GoodsOrderModel
        fields = (
            'id',
            'contractor',
            'contact',
            'execute_status',
            'delivery_address',
            'pickup',
            'comment',
            'amount',
            'quantity',
            'nds_amount',
            'operation_type'
        )


class SendOfferFromCartSerializer(serializers.Serializer):
    contractor = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True), required=False, allow_null=True)
    contractor_member = serializers.PrimaryKeyRelatedField(
        queryset=ContractorMemberModel.objects.filter(is_active=True), required=False, allow_null=True
    )
    logistic_manager = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True), required=False, allow_null=True
    )
    contract = serializers.PrimaryKeyRelatedField(
        queryset=ContractModel.objects.filter(is_active=True), required=False, )
    # slug_field='code'),
    # contractor_obj = ContractorModelDetailSerializer()
    # contractor_member_obj = BaseCatalogListSerializer()
    # contract_obj = BaseCatalogListSerializer()

    warehouse = serializers.PrimaryKeyRelatedField(queryset=WarehouseModel.objects.filter(is_active=True),
                                                   required=False, allow_null=True)
    delivery_address = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryAddress.objects.filter(is_active=True), required=False, allow_null=True)
    delivery_point = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryPointModel.objects.filter(is_active=True), required=False, allow_null=True)
    delivery_purpose = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryPurposeModel.objects.filter(is_active=True), required=False, allow_null=True)
    delivery_date_plan_gte = serializers.DateTimeField(allow_null=True, required=False)
    delivery_date_plan_lte = serializers.DateTimeField(allow_null=True, required=False)
    pay_type = serializers.PrimaryKeyRelatedField(
        queryset=PaymentFormModel.objects.filter(is_active=True), required=False, allow_null=True)
    pay_date_plan = serializers.DateField(required=False, allow_null=True)

    pickup = serializers.BooleanField(required=False, default=False)
    operation_type = serializers.CharField()
    cash_pay_recipient = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True),
        required=False, allow_null=True
    )
    cash_pay_type = serializers.PrimaryKeyRelatedField(
        queryset=models.CashPayTypeModel.objects.filter(is_active=True),
        required=False, allow_null=True
    )
    comment = serializers.CharField(allow_blank=True, required=False, allow_null=True, default="")
    attachments = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.filter(is_active=True), required=False, allow_null=True, many=True)

    car = serializers.CharField(allow_blank=True, required=False, allow_null=True, default="")
    operator = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True), required=False, allow_null=True
    )
    amount_paid = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True, default=0,
                                           required=False, )
    # Temporary unit
    cash_unit = serializers.PrimaryKeyRelatedField(
        queryset=CashUnitModel.objects.filter(is_active=True), required=False, allow_null=True)
    cash_unit_secondary = serializers.PrimaryKeyRelatedField(
        queryset=CashUnitModel.objects.filter(is_active=True), required=False, allow_null=True)
    amount_to_cash = serializers.DecimalField(max_digits=15, allow_null=True, default=0, required=False,
                                              decimal_places=2, )
    amount_to_cash_secondary = serializers.DecimalField(max_digits=15, allow_null=True, default=0, required=False,
                                                        decimal_places=2, )
    co_executors = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True), required=False, allow_null=True, many=True
    )
    # End of Temporary unit

    def validate(self, data):
        user = get_current_authenticated_profile()
        operation_type = data['operation_type']
        data.setdefault('co_executors', [])
        # if not models.ShoppingCartModel.objects.filter(user=user, cart_type_id='shopping_cart').exists() and 'tp_goods' not in data:
        #     raise exceptions.ValidationError('Shopping cart cannot be empty.')
        customer_contract_id = self.initial_data.get('customer_contract') if hasattr(self, 'initial_data') else None
        is_crm_contract_order = bool(customer_contract_id)
        contractor = data.get('contractor', None)
        if is_crm_contract_order:
            contractor = None
        elif not contractor:
            contractor = user.contractors.first()
            if not contractor:
                raise exceptions.ValidationError('Contractor does not exist.')
        else:
            if not user.has_full_access_to_order_editing and not user.contractors.filter(pk=contractor.pk).exists():
                raise exceptions.ValidationError('Invalid contractor.')
        contract = data.get('contract', None)

        if not contract:
            contract = ContractModel.objects.get(code='default')
        else:
            if not is_crm_contract_order and not contractor.contracts.filter(contract=contract).exists():
                raise exceptions.ValidationError('Invalid contract.')
        contractor_member = data.get('contractor_member', None)
        if is_crm_contract_order:
            contractor_member = None
        elif not contractor_member:
            raise exceptions.ValidationError('Invalid contractor member.')
        else:
            if not contractor_member.contractor == contractor:
                raise exceptions.ValidationError('Invalid contractor member.')
        if data.get('pickup', False):
            data['delivery_address'] = None
            data['delivery_point'] = None
        else:
            if ORDER_DELIVERY == 'address' and not is_crm_contract_order:
                delivery_address = data.get('delivery_address')
                if delivery_address and not contractor.delivery_addresses.filter(pk=delivery_address.pk).exists():
                    raise exceptions.ValidationError('Invalid delivery address')
                data['delivery_point'] = None
            if ORDER_DELIVERY == 'point' and not is_crm_contract_order:
                delivery_point = data.get('delivery_point')
                if not delivery_point or not contractor.delivery_points.filter(pk=delivery_point.pk).exists():
                    raise exceptions.ValidationError('Invalid delivery point')
        data['operation_type'] = operation_type
        data['contractor'] = contractor
        data['contractor_member'] = contractor_member

        data['contract'] = contract
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['user'] = str(instance['user'])
        data['contract'] = str(instance['contract'].id)
        contractor_member = instance.get('contractor_member')
        data['contractor_member'] = str(contractor_member.id) if contractor_member else None
        warehouse = instance.get('warehouse', '')
        if warehouse:
            data['warehouse'] = str(warehouse.id)
        else:
            data['warehouse'] = None

        cash_unit = instance.get('cash_unit', '')
        if cash_unit:
            data['cash_unit'] = str(cash_unit.id)
        else:
            data['cash_unit'] = None

        cash_unit_secondary = instance.get('cash_unit_secondary', '')
        if cash_unit_secondary:
            data['cash_unit_secondary'] = str(cash_unit_secondary.id)
        else:
            data['cash_unit_secondary'] = None

        logistic_manager = instance.get('logistic_manager', '')
        if logistic_manager:
            data['logistic_manager'] = str(logistic_manager.id)
        else:
            data['logistic_manager'] = None
        cash_pay_type = instance.get('cash_pay_type', None)
        if cash_pay_type:
            data['cash_pay_type'] = str(cash_pay_type.pk)
        cash_pay_recipient = instance.get('cash_pay_recipient', None)
        if cash_pay_recipient:
            data['cash_pay_recipient'] = str(cash_pay_recipient.pk)
        data['delivery_address'] = None
        delivery_address = instance.get('delivery_address', None)
        if delivery_address:
            data['delivery_address'] = instance['delivery_address'].address
        delivery_point = instance.get('delivery_point', None)
        if delivery_point:
            data['delivery_point'] = DeliveryPointSerializer(delivery_point).data
        delivery_purpose = instance.get('delivery_purpose', None)
        if delivery_purpose:
            data['delivery_purpose'] = DeliveryPurposeSerializer(delivery_purpose).data
        contractor = instance.get('contractor')
        data['contractor'] = str(contractor.id) if contractor else None
        data['delivery_method'] = ORDER_DELIVERY
        pay_type = data.get('pay_type')
        if pay_type:
            data['pay_type'] = str(pay_type)
        attachments = data.get('attachments', [])
        if attachments is not None:
            data['attachments'] = [str(each) for each in attachments]
        else:
            data['attachments'] = []
        operator = instance.get('operator', None)
        if operator:
            data['operator'] = str(operator.pk)
        data['delivery_date_plan_gte'] = serializers.DateTimeField().to_representation(
            instance.get('delivery_date_plan_gte', None))
        data['delivery_date_plan_lte'] = serializers.DateTimeField().to_representation(
            instance.get('delivery_date_plan_lte', None))
        co_executors = instance.get('co_executors')
        if co_executors:
            data['co_executors'] = [str(each.pk) for each in co_executors]
        else:
            data['co_executors'] = []
        return data


class Send1COrderSerializer(serializers.ModelSerializer):
    operation_type = serializers.SerializerMethodField()

    def get_operation_type(self, instance):
        return instance.operation_type.code

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'operation_type',
            'contract',
            'contractor',
        )


class Send1COrderGoodsTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'goods',
            'quantity',
        )


class TpGoodsEmptyOrderSerializer(serializers.Serializer):
    # id = serializers.UUIDField()
    goods = serializers.SerializerMethodField()
    goods_for_print = serializers.SerializerMethodField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    price = serializers.DecimalField(max_digits=15, decimal_places=2)
    number = serializers.IntegerField(source='num')
    nds = serializers.CharField()
    amount_nds = serializers.DecimalField(max_digits=15, decimal_places=2, source='amountnds')
    amount_no_discount = serializers.DecimalField(max_digits=15, decimal_places=2, source='amounnodiscount')
    discount = serializers.DecimalField(max_digits=15, decimal_places=2)
    warehouse = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    coefficient = serializers.DecimalField(max_digits=15, decimal_places=3)
    custom_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    measure_unit = serializers.SerializerMethodField()

    def get_measure_unit(self, instance):
        measure_unit_id = instance.get('measure_unit')
        if measure_unit_id:
            try:
                measure_unit_obj = MeasureUnitModel.objects.get(pk=measure_unit_id)
            except MeasureUnitModel.DoesNotExist:
                return None
            return MeasureUnitListSerializer(measure_unit_obj).data
        return None

    def get_currency(self, instance):
        # currency = instance.contract.price_type.currency
        data = None
        currency_id = instance.get('currency', None)
        if currency_id:
            currency = CurrencyModel.objects.get(code=currency_id)
            data = {'name': currency.name, 'icon': currency.icon}
        return data

    def get_goods(self, instance):
        goods_obj = GoodsModel.objects.get(id=instance['goods'])
        return GoodsShoppingCartSerializer(goods_obj).data

    def get_goods_for_print(self, instance):
        try:
            goods_for_print_obj = GoodsModel.objects.get(id=instance.get('goods_for_print'))
        except GoodsModel.DoesNotExist:
            return None
        return GoodsModelForPrintSerializer(goods_for_print_obj).data

    def get_warehouse(self, instance):
        warehouse = instance.get('warehouse', None)
        if warehouse:
            warehouse_obj = WarehouseModel.objects.get(id=instance['warehouse'])
            return AppWarehouseSerializer(warehouse_obj).data
        else:
            return 'Нет в наличии'
        # TODO


class EmptyOrderSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    amount_nds = serializers.DecimalField(max_digits=15, decimal_places=2, source='amountnds')
    must_paid = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0)
    prepayment = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0)
    contractor = serializers.UUIDField()
    # number_1c = serializers.CharField()
    contract = serializers.UUIDField()
    delivery_address = serializers.CharField()

    if not ORDER_DELIVERY == 'address':
        delivery_point = serializers.JSONField(required=False)
    pickup = serializers.BooleanField()
    operation_type = serializers.CharField()
    user = serializers.UUIDField()

    limitcontract = serializers.DecimalField(max_digits=15, decimal_places=2, required=False,
                                             allow_null=True)
    remcontract = serializers.DecimalField(max_digits=15, decimal_places=2, required=False,
                                           allow_null=True)

    tp_goods = TpGoodsEmptyOrderSerializer(many=True)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    pay_type = serializers.UUIDField(required=False, allow_null=True)
    # def get_delivery_address(self, instance):
    #     if instance.get('delivery_address'):
    #         deliv_obj = DeliveryAddress.objects.get(id=instance['delivery_address'])
    #         return AppDeliveryAddressSerializer(deliv_obj).data
    #     else:
    #         return None


class GoodsOrderModelSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = (search_indexes.GoodsOrderModelIndex,)
        fields = ('content',)

    def to_representation(self, instance):
        obj = instance.object
        data = obj.get_serializer_class(action='list')(instance=obj, context=self.context).data
        data['type'] = obj.get_label()
        return data


class TPGoodsOrderWithout1CSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    goods = serializers.SerializerMethodField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=3)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    price = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    nds = serializers.CharField(allow_null=True, allow_blank=True, default='20%')
    amount_nds = serializers.SerializerMethodField()
    amount_no_discount = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    coefficient = serializers.DecimalField(max_digits=15, decimal_places=3)
    warehouse = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    num = 0
    # measure_unit = serializers.PrimaryKeyRelatedField(queryset=MeasureUnitModel.objects.filter(is_active=True))
    measure_unit = MeasureUnitListSerializer()

    def get_goods(self, instance):
        return GoodsShoppingCartSerializer(instance.goods).data

    def get_price(self, instance):
        if instance.custom_price:
            result = instance.custom_price
        else:
            result = instance.goods.price_by_catalog
        return serializers.DecimalField(max_digits=15, decimal_places=3).to_representation(result)

    def get_number(self, instance):
        number = self.num + 1
        self.num = number
        return number

    def get_amount_nds(self, instance):
        return serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(
            instance.goods.price_by_catalog * Decimal('0.20'))

    def get_amount_no_discount(self, instance):
        return serializers.DecimalField(max_digits=15, decimal_places=2).to_representation(
            instance.goods.price_by_catalog)

    def get_discount(self, instance):
        return "0.00"

    def get_warehouse(self, instance):
        warehouse = instance.warehouse
        if warehouse:
            return AppWarehouseSerializer(warehouse).data
        else:
            return 'Нет в наличии'

    def get_currency(self, instance):
        return {"name": "RUB", "icon": "₽"}


class EmptyOrderWithout1CSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    amount_nds = serializers.DecimalField(max_digits=15, decimal_places=2)
    contractor = serializers.UUIDField()
    # number_1c = serializers.CharField()
    contract = serializers.UUIDField()
    delivery_address = serializers.CharField()
    delivery_date_plan_gte = serializers.DateTimeField(allow_null=True, required=False)
    delivery_date_plan_lte = serializers.DateTimeField(allow_null=True, required=False)
    amount_no_discount = serializers.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        allow_null=False,
        required=False,
        default='0.00',
    )
    pay_date_plan = serializers.DateField(allow_null=True, required=False)
    cash_pay_recipient = serializers.UUIDField(allow_null=True, required=False)
    cash_pay_type = serializers.UUIDField(allow_null=True, required=False)
    if not ORDER_DELIVERY == 'address':
        delivery_point = serializers.JSONField()
    pickup = serializers.BooleanField()
    operation_type = serializers.CharField()
    user = serializers.UUIDField()
    tp_goods = TPGoodsOrderWithout1CSerializer(many=True)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    pay_type = serializers.UUIDField(required=False, allow_null=True)


class CreateWithout1CGoodsOrderSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    nds_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'id',
            'amount',
            'nds_amount',
            'contractor',
            'contract',
            'delivery_address',
            'delivery_point',
            'pickup',
            'operation_type',
            'user',
            'comment',
            'pay_type',
            'amount_paid',
            'pay_date_plan',
            'cash_pay_recipient',
            'cash_pay_type',

            'attachments',
            'contractor_member',
            'contract',

            'delivery_address',
            'delivery_company',
            'delivery_date_plan_gte',
            'delivery_date_plan_lte',
            'warehouse',
            'quantity',
            'number_1c',
            'cash_unit',
            'cash_unit_secondary',
            'logistic_manager',
            'amount_to_cash',
            'amount_to_cash_secondary',
            'car',
            'operator',
        )

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            self.create_table_part(instance, validated_data)
            operator = instance.operator
            delivery_point = instance.delivery_point
            warehouse = instance.warehouse
            if operator and delivery_point and warehouse:
                start_delivery_point = warehouse.delivery_point
                if start_delivery_point:
                    from bpms.tasks.models import TaskModel, TaskDeliveryPointModel
                    logistic_task = TaskModel()
                    logistic_task.task_type_id = 'logistic'
                    logistic_task.owner = get_current_authenticated_profile()
                    logistic_task.operator = operator
                    logistic_task.name = f'Задание на доставку заказа {instance.number_1c}'
                    logistic_task.description = instance.comment
                    logistic_task.save()
                    start_task_delivery_point = TaskDeliveryPointModel()
                    start_task_delivery_point.task = logistic_task
                    start_task_delivery_point.is_start = True
                    start_task_delivery_point.delivery_point = start_delivery_point
                    start_task_delivery_point.save()
                    task_delivery_point = TaskDeliveryPointModel()
                    task_delivery_point.task = logistic_task
                    task_delivery_point.delivery_point = delivery_point
                    task_delivery_point.save()
                    instance.task_delivery_point = task_delivery_point
                    instance.save(update_fields=('task_delivery_point',))
                    from bpms.tasks.notifications import notify_driver_about_start_order, \
                        notify_order_user_about_start_order
                    transaction.on_commit(
                        lambda: async_task(
                            notify_driver_about_start_order,
                            logistic_task,
                            instance,
                            logistic_task.owner
                        )
                    )
                    transaction.on_commit(
                        lambda: async_task(
                            notify_order_user_about_start_order,
                            logistic_task,
                            instance,
                            logistic_task.owner
                        )
                    )
        return instance

    # def update(self, instance, validated_data):
    #     validated_data.pop('id', None)
    #     instance = super().update(instance, validated_data)
    #     instance.tp_goodsorders.remove(bulk=False)
    #     self.create_table_part(instance, validated_data)
    #     return instance

    def create_table_part(self, instance, validated_data):
        tp_goods = self.initial_data['tp_goods']
        for tp_goods_elem in tp_goods:
            tp_goods_elem.pop('id', None)
            tp_goods_elem['owner'] = instance
            goods = tp_goods_elem.pop('goods')
            tp_goods_elem['goods_id'] = goods['id']
            tp_goods_elem['amount_no_discount'] = tp_goods_elem.pop('amount_no_discount')
            # tp_goods_elem['warehouse_id'] = tp_goods_elem.pop('warehouse')
            tp_goods_elem.pop('warehouse')
            if validated_data.get('warehouse'):
                tp_goods_elem['warehouse_id'] = str(validated_data['warehouse'].id)
            else:
                tp_goods_elem['warehouse'] = None
            tp_goods_elem['nds_amount'] = tp_goods_elem.pop('amount_nds')
            tp_goods_elem['number'] = tp_goods_elem.pop('number')
            measure_unit = tp_goods_elem.pop('measure_unit', None)
            if measure_unit:
                measure_unit_id = measure_unit.get('id')
            else:
                measure_unit_id = None
            tp_goods_elem['measure_unit_id'] = measure_unit_id
            tp_goods_elem['coefficient'] = tp_goods_elem.pop('coefficient', 1)
            tp_goods_elem.pop('currency', None)
        ready_to_create = [models.TPGoodsOrderModel(**vals) for vals in tp_goods]
        # GoodsRemnantModel.objects.bulk_create(ready_to_create)
        for item in ready_to_create:
            item.save()


class MustPaidUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsOrderModel
        fields = (
            'must_paid',
        )


class CashPaymentOrderModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CashPaymentOrderModel
        fields = (
            'amount',
            'cash_pay_type',
        )

    def validate_cash_pay_type(self, data):
        if data.is_group:
            raise exceptions.ValidationError(f'cash_pay_type {data.name} is group.')
        return data

    def create(self, validated_data):
        owner = self.context.get('owner')
        instance = models.CashPaymentOrderModel.objects.create(owner=owner, **validated_data)
        return instance


class CashPayTypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CashPayTypeModel
        fields = (
            'id',
            'name',
            'is_group',
        )


class DeliveryPointWithOrdersSerializer(serializers.ModelSerializer):
    orders = GoodsOrderModelListSerializer(many=True)

    class Meta:
        model = DeliveryPointModel
        fields = (
            'id',
            'lat',
            'lon',
            'name',
            'address',
            'orders',
        )


class SetPurchasePricesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'id',
            'purchase_price',
        )


class GetPurchasePricesSerializer(serializers.ModelSerializer):
    name_short = serializers.CharField(read_only=True, source='goods.name_short')

    class Meta:
        model = models.TPGoodsOrderModel
        fields = (
            'id',
            'purchase_price',
            'quantity',
            'name_short'
        )
