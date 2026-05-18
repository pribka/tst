import io
import json
import requests
import copy
import uuid
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File as DjangoFile
from django.http.response import FileResponse
from django.db import transaction
from django.db.models import Sum, Prefetch, F
from django.db.models.manager import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import DecimalField
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions as drf_exceptions
from rest_framework import status

from django_q.tasks import async_task

from bkz3.settings import BASE_DIR
from bkz3.settings import BITRIX_TOKEN
from bkz3.settings import BITRIX_OUTER_TOKEN
from bkz3.settings import ORDER_WITHOUT_1C
from bkz3.settings import SHORT_COMPANY_NAME
from bkz3.settings import DIRECT_ORDER_FILES
from drf_haystack.viewsets import HaystackGenericAPIView

from haystack.query import SearchQuerySet, RelatedSearchQuerySet

from common.views import BaseModelViewSet, BaseCatalogViewSet
from common.catalogs.models import GoodsModel, MeasureUnitModel, WarehouseModel
from common.models import File
from common.catalogs.models import ContractorProfileModel
from common.catalogs.serializers import AppWarehouseSerializer

from app_info.models import AppInfo

from users.models import (ProfileModelOuterLeadID,
                          ProfileModelOuterID)

from bpms.bpms_common.serializers import AppFileSerializer
from gallery.models import GalleryModel

from . import models
from . import paginators
from . import serializers
from . import utils
from . import permissions
from . import notifications
from .enums import OperationTypeEnum

from integration_1c.utils import send_offer_to_1c, send_update_order_to_1c
from integration_1c.utils import get_invoice_file_from_1c
from integration_1c.utils import get_contract_file_from_1c, send_cash_payment_to_1c
from integration_1c.utils import send_order_files_to_1c, send_calculate_must_paid_to_1c
from integration_1c.utils import get_pay_file_from_1c, send_split_order_by_warehouses
from integration_1c.utils import get_sale_file_from_1c, send_purchase_prices_to_1c


class ShoppingCartModelViewSet(BaseModelViewSet):
    model = models.ShoppingCartModel
    pagination_class = paginators.ShoppingCartPagination
    cart_type: str = 'shopping_cart'

    def get_queryset(self):
        return self.model.get_queryset().filter(cart_type_id=self.cart_type).order_by('created_at')

    def create(self, request, *args, **kwargs):
        return super(BaseModelViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super(BaseModelViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super(BaseModelViewSet, self).destroy(request, *args, **kwargs)

    @action(methods=('get',), detail=False, url_path=r'count')
    def get_count(self, request, *args, **kwargs):
        user = request.user.profile
        quantity = self.model.objects.filter(
            user=user,
            cart_type_id=self.cart_type,
        ).aggregate(Sum('quantity'))['quantity__sum']
        if quantity is None:
            quantity = 0
        return Response({'count': quantity})

    @action(methods=('get',), detail=False, url_path=r'amount')
    def get_amount(self, request, *args, **kwargs):
        amount = DecimalField(max_digits=15, decimal_places=2).to_representation(
            self.model.get_queryset().filter(cart_type_id=self.cart_type).aggregate(Sum('amount'))['amount__sum']
        )
        if not amount:
            amount = "0.00"
        return Response({'amount': amount})

    @action(methods=('post',), detail=False, url_path='clear')
    def clear(self, request, *args, **kwargs):
        self.model.objects.filter(user=request.user.profile, cart_type_id=self.cart_type).delete()
        return Response('ok')

    @action(methods=('get',), detail=False, url_path='warehouses')
    def get_warehouses(self, request, *args, **kwargs):
        qs = WarehouseModel.objects.filter(
            is_active=True, shopping_carts__user=request.user.profile, shopping_carts__cart_type_id=self.cart_type,
        ).distinct().order_by('name')
        data = AppWarehouseSerializer(qs, many=True).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='order_warehouses')
    def get_order_warehouses(self, request, *args, **kwargs):
        order_id = request.query_params.get('order', None)
        try:
            order = models.GoodsOrderModel.objects.get(is_active=True,
                                                       pk=order_id)
        except models.GoodsOrderModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Order does not exist')
        qs = WarehouseModel.objects.filter(
            is_active=True,
            tp_goodsorders__owner=order).distinct().order_by('name')
        data = AppWarehouseSerializer(qs, many=True).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='form_info')
    def get_form_info(self, request, *args, **kwargs):
        goods_id = request.query_params.get('goods')
        from common.catalogs.models import GoodsModel
        from common.catalogs.serializers import MeasureUnitListSerializer
        if goods_id:
            try:
                goods = GoodsModel.objects.get(pk=goods_id, is_active=True)
            except GoodsModel.DoesNotExist:
                goods = None
            if goods:
                default_measure_unit = goods.base_measure_unit
            else:
                default_measure_unit = None
            if default_measure_unit:
                default_measure_unit_data = MeasureUnitListSerializer(default_measure_unit).data
            else:
                default_measure_unit_data = None
        else:
            default_measure_unit = None
            default_measure_unit_data = None
        try:
            from bkz3.local_settings import EXTEND_MEASURE_CONFIG

        except ImportError:
            try:
                EXTEND_MEASURE_CONFIG = AppInfo.objects.get(is_active=True, code='shopping_cart_form_info').metadata
            except AppInfo.DoesNotExist:
                EXTEND_MEASURE_CONFIG = {
                    "form": {
                        "measure_unit": getattr(default_measure_unit, 'pk', None),
                        "coefficient": 1
                    },
                    "formInfo": [
                        {
                            "key": 'measure_unit',
                            "name": 'ед. изм.',
                            "widget": 'Select',
                            "default_value": default_measure_unit_data,
                            "apiPath": '/app_info/filtered_select_list/?model=catalogs.MeasureUnitModel',
                            "rulesConfig": [
                                {
                                    "message": "Обязательно для заполнения",
                                    "required": True,
                                    "trigger": "change"
                                }
                            ]
                        },
                        {
                            "key": 'coefficient',
                            "depends_on": ["measure_unit"],
                            "name": 'коэфф.',
                            "widget": 'Number',
                            "min": 0,
                            "max": 1000,
                            "participatesTotal": True,
                            "rulesConfig": [
                                {
                                    "message": "Обязательно для заполнения",
                                    "required": True,
                                    "trigger": "change",
                                    "min": 1,
                                    "type": "number",
                                }
                            ]
                        }
                    ]
                }

        return Response(EXTEND_MEASURE_CONFIG)


class ReturnCartViewSet(ShoppingCartModelViewSet):
    cart_type: str = 'return_cart'


def collect_data_after_1c(serialized_data_to_1c, data_to_serialize_1c, returned_order_data):
    result = copy.deepcopy(returned_order_data)
    # CRM-заказы могут создаваться без ContractorModel: клиентом является
    # CustomerCardModel, а договор хранится в customer_contract.
    result['contractor'] = serialized_data_to_1c.get('contractor')
    result['contractor_member'] = serialized_data_to_1c.get('contractor_member')
    result['user'] = serialized_data_to_1c['user']
    result['operation_type'] = serialized_data_to_1c['operation_type']
    result['contract'] = data_to_serialize_1c['contract'].code
    result['pickup'] = serialized_data_to_1c['pickup']
    result['nds_amount'] = returned_order_data['amountnds']
    result['quantity'] = returned_order_data['num']
    # returned_order_data['number_1c'] = returned_order_data['num'] #TODO получить с 1С
    result['comment'] = serialized_data_to_1c['comment']
    result['delivery_address'] = serialized_data_to_1c.get('delivery_address', '')
    result['delivery_company'] = serialized_data_to_1c.get('delivery_company', None)
    result['logistic_manager'] = serialized_data_to_1c['logistic_manager']
    result['cash_unit'] = serialized_data_to_1c['cash_unit']
    result['cash_unit_secondary'] = serialized_data_to_1c['cash_unit_secondary']
    result['amount_to_cash'] = serialized_data_to_1c['amount_to_cash']
    result['amount_to_cash_secondary'] = serialized_data_to_1c['amount_to_cash_secondary']
    result['amount_paid'] = serialized_data_to_1c.get('amount_paid', 0)
    result['pay_type'] = serialized_data_to_1c['pay_type']
    result['attachments'] = serialized_data_to_1c.get('attachments', [])
    result['car'] = serialized_data_to_1c.get('car', '')
    result['operator'] = serialized_data_to_1c.get('operator', '')
    result['delivery_point'] = serialized_data_to_1c.get('delivery_point', None)
    result['delivery_purpose'] = serialized_data_to_1c.get('delivery_purpose', None)
    result['delivery_date_plan_gte'] = serialized_data_to_1c.get('delivery_date_plan_gte')
    result['delivery_date_plan_lte'] = serialized_data_to_1c.get('delivery_date_plan_lte')
    result['pay_date_plan'] = serialized_data_to_1c.get('pay_date_plan')
    result['cash_pay_type'] = serialized_data_to_1c.get('cash_pay_type')
    result['cash_pay_recipient'] = serialized_data_to_1c.get('cash_pay_recipient')
    result['co_executors'] = serialized_data_to_1c.get('co_executors', [])
    result['reason'] = data_to_serialize_1c.get('reason')
    result['customer_contract'] = data_to_serialize_1c.get('customer_contract')
    result['customer_card'] = data_to_serialize_1c.get('customer_card')

    def tempe(x, y):
        x['measure_unit'] = y['measure_unit']
        x['coefficient'] = y['coefficient']
        x['custom_price'] = y['custom_price']
        return x

    tp_goods = list(map(tempe, returned_order_data['tp_goods'], serialized_data_to_1c['tp_goods']))
    result['tp_goods'] = tp_goods
    return result

def collect_prepared_order_data(data_to_serialize_1c, shopping_card_list, request_user):
    serialized_to_1c = serializers.SendOfferFromCartSerializer(data=data_to_serialize_1c)
    serialized_to_1c.is_valid(raise_exception=True)
    serialized_data_to_1c = serialized_to_1c.data
    serialized_data_to_1c['user'] = str(request_user.id)
    #: Отправляем физ лицо (на стороне 1са ищем по нему Контактное лицо)
    # serialized_data_to_1c['profile'] = str(request_user.profile.id)
    serialized_data_to_1c['delivery_address'] = data_to_serialize_1c.get('delivery_address_str', '')
    serialized_data_to_1c['delivery_company'] = data_to_serialize_1c.get('delivery_company', None)

    from common.catalogs.serializers import ContractorModelDetailSerializer
    from common.serializers import BaseCatalogListSerializer
    from common.catalogs.models import ContractorModel, ContractorMemberModel

    # Для обычных заказов в 1С по-прежнему передаем contractor/contact.
    # Для CRM-заказов эти поля могут быть пустыми, поэтому сериализуем их
    # только при наличии.
    contractor_id = serialized_data_to_1c.get('contractor') or serialized_to_1c.initial_data.get('contractor')
    contractor_member_id = serialized_data_to_1c.get('contractor_member') or serialized_to_1c.initial_data.get('contractor_member')
    contract_id = serialized_data_to_1c.get('contract') or serialized_to_1c.initial_data.get('contract')
    if contractor_id:
        serialized_data_to_1c['contractor_obj'] = ContractorModelDetailSerializer(
            instance=ContractorModel.objects.get(pk=contractor_id)).data
    if contractor_member_id:
        serialized_data_to_1c['contractor_member_obj'] = BaseCatalogListSerializer(
            instance=ContractorMemberModel.objects.get(pk=contractor_member_id)).data
    serialized_data_to_1c['contract_obj'] = BaseCatalogListSerializer(
        instance=models.ContractModel.objects.get(pk=contract_id)).data

    if 'tp_goods' in data_to_serialize_1c:
        serialized_data_to_1c['tp_goods'] = data_to_serialize_1c['tp_goods']
        return serialized_data_to_1c
    if isinstance(shopping_card_list, QuerySet) and shopping_card_list.model == models.ShoppingCartModel:
        serialized_data_to_1c['tp_goods'] = serializers.ShoppingCartModelListTo1CSerializer(shopping_card_list,
                                                                                        many=True).data
    else:
        tp_goods_serializer = serializers.TPGoodsOrderModelListTo1CSerializer(data=shopping_card_list, many=True)
        tp_goods_serializer.is_valid(raise_exception=True)
        serialized_data_to_1c['tp_goods'] = tp_goods_serializer.data
    return serialized_data_to_1c


class GoodsOrderModelViewSet(BaseModelViewSet):
    model = models.GoodsOrderModel
    operation_types = (
        OperationTypeEnum.draft.value,
        OperationTypeEnum.offer.value,
        OperationTypeEnum.price.value,
        OperationTypeEnum.purchase.value,
    )
    shopping_cart_type = 'shopping_cart'

    @staticmethod
    def _decimal(value, default='0'):
        if value in (None, ''):
            return Decimal(default)
        return Decimal(str(value))

    @staticmethod
    def _money(value):
        return DecimalField(max_digits=15, decimal_places=2).to_representation(value)

    @staticmethod
    def _quantity(value):
        return DecimalField(max_digits=15, decimal_places=3).to_representation(value)

    def _resolve_crm_order_customer_card(self, request, customer_contract, raw_customer_card_id):
        """Определить получателя отгрузки для CRM-заказа.

        Правило бизнеса: не брать "первого клиента договора". Если в договоре
        одна обслуживаемая карточка, подставляем ее автоматически. Если карточек
        несколько, пользователь обязан выбрать получателя явно.
        """
        if not customer_contract:
            return None

        from help_desk.models import CustomerCardModel

        customer_cards = list(
            CustomerCardModel.get_queryset(request).filter(
                serviced_contracts_relations__customer_contract=customer_contract,
                serviced_contracts_relations__is_active=True,
                is_active=True,
            ).distinct().order_by('name', '-created_at')
        )
        if raw_customer_card_id not in (None, ''):
            raw_customer_card_id = str(raw_customer_card_id)
            for customer_card in customer_cards:
                if str(customer_card.pk) == raw_customer_card_id:
                    return customer_card
            raise drf_exceptions.ValidationError({
                'customer_card': 'Выбранный CRM-клиент не входит в обслуживаемые карточки договора.'
            })

        if len(customer_cards) == 1:
            return customer_cards[0]
        if not customer_cards:
            raise drf_exceptions.ValidationError({
                'customer_card': 'В договоре нет обслуживаемых CRM-клиентов.'
            })
        raise drf_exceptions.ValidationError({
            'customer_card': 'Выберите CRM-клиента, которому оформляется отгрузка.'
        })

    def _get_local_crm_order_lines(self, raw_lines):
        """Преобразовать строки заказа из CRM-формы в объекты номенклатуры."""
        if not isinstance(raw_lines, (list, tuple)) or not raw_lines:
            raise drf_exceptions.ValidationError({'tp_goods': 'Order lines are required.'})

        goods_ids = [line.get('goods') for line in raw_lines if isinstance(line, dict) and line.get('goods')]
        goods_by_id = {
            str(goods.pk): goods for goods in GoodsModel.objects.filter(is_active=True, pk__in=goods_ids)
        }
        warehouse_ids = [
            line.get('warehouse') for line in raw_lines
            if isinstance(line, dict) and line.get('warehouse')
        ]
        warehouses_by_id = {
            str(warehouse.pk): warehouse
            for warehouse in WarehouseModel.objects.filter(is_active=True, pk__in=warehouse_ids)
        }
        measure_unit_ids = [
            line.get('measure_unit') for line in raw_lines
            if isinstance(line, dict) and line.get('measure_unit')
        ]
        measure_units_by_id = {
            str(unit.pk): unit
            for unit in MeasureUnitModel.objects.filter(is_active=True, pk__in=measure_unit_ids)
        }
        lines = []
        for index, raw_line in enumerate(raw_lines, start=1):
            if not isinstance(raw_line, dict):
                raise drf_exceptions.ValidationError({'tp_goods': 'Invalid order line.'})
            goods_id = raw_line.get('goods')
            goods = goods_by_id.get(str(goods_id))
            if not goods:
                raise drf_exceptions.ValidationError({'tp_goods': f'Goods not found: {goods_id}'})
            goods_for_print_id = raw_line.get('goods_for_print') or goods_id
            goods_for_print = goods_by_id.get(str(goods_for_print_id))
            if not goods_for_print and goods_for_print_id:
                goods_for_print = GoodsModel.objects.filter(is_active=True, pk=goods_for_print_id).first()
            warehouse = warehouses_by_id.get(str(raw_line.get('warehouse')))
            measure_unit = measure_units_by_id.get(str(raw_line.get('measure_unit'))) or goods.base_measure_unit
            quantity = self._decimal(raw_line.get('quantity') or '1')
            if quantity <= 0:
                raise drf_exceptions.ValidationError({'tp_goods': 'Quantity must be greater than zero.'})
            price = self._decimal(
                raw_line.get('custom_price') or raw_line.get('price') or goods.price_by_catalog or '0'
            )
            coefficient = self._decimal(raw_line.get('coefficient') or '1')
            lines.append({
                'id': raw_line.get('id') or str(uuid.uuid4()),
                'number': index,
                'goods': goods,
                'goods_for_print': goods_for_print or goods,
                'warehouse': warehouse,
                'measure_unit': measure_unit,
                'quantity': quantity,
                'custom_price': price,
                'coefficient': coefficient,
            })
        return lines

    def _get_local_line_value(self, line, key, default=None):
        if isinstance(line, dict):
            return line.get(key, default)
        return getattr(line, key, default)

    def _build_local_crm_order_goods(self, shopping_card_list, contract):
        """Собрать табличную часть заказа без обращения к 1С.

        Этот путь нужен для CRM MVP: заказ собирается из потребностей интереса
        или предмета договора прямо в BPMS, при этом сохраняется формат ответа,
        который ожидает существующий фронт заказов.
        """
        currency_data = None
        currency_id = None
        if contract.price_type and contract.price_type.currency:
            currency = contract.price_type.currency
            currency_id = currency.code
            currency_data = {'name': currency.name, 'icon': currency.icon}
        display_currency = currency_data or {'name': currency_id or '', 'icon': ''}

        tp_goods = []
        amount = Decimal('0.00')
        amount_no_discount = Decimal('0.00')
        nds_amount = Decimal('0.00')
        quantity = Decimal('0.000')

        for number, cart_item in enumerate(shopping_card_list, start=1):
            goods = self._get_local_line_value(cart_item, 'goods')
            goods_for_print = self._get_local_line_value(cart_item, 'goods_for_print') or goods
            warehouse_obj = self._get_local_line_value(cart_item, 'warehouse')
            measure_unit_obj = self._get_local_line_value(cart_item, 'measure_unit')
            coefficient = self._get_local_line_value(cart_item, 'coefficient') or Decimal('1.000')
            item_quantity = self._decimal(self._get_local_line_value(cart_item, 'quantity'))
            item_price = self._decimal(
                self._get_local_line_value(cart_item, 'custom_price') or goods.price_by_catalog
            )
            item_amount = (item_price * item_quantity).quantize(Decimal('0.01'))
            item_nds = (item_amount * Decimal('0.20')).quantize(Decimal('0.01'))
            item_amount_no_discount = item_amount
            goods_data = serializers.GoodsShoppingCartSerializer(goods).data
            goods_data['currency'] = display_currency
            goods_data['amount'] = self._money(item_amount)
            goods_data['price'] = self._money(item_price)
            goods_data['number'] = number
            goods_data['amount_no_discount'] = self._money(item_amount_no_discount)
            goods_data['nds'] = '20%'
            goods_data['amount_nds'] = self._money(item_nds)
            goods_data['image'] = getattr(goods.gallery.filter(is_main=True, is_active=True).first(), 'path', '')
            available_count = goods.remnants.filter(is_active=True).aggregate(Sum('quantity'))['quantity__sum']
            goods_data['available_count'] = available_count or 0
            goods_data['is_availability'] = bool(available_count)
            goods_data['default_price_currency'] = display_currency.get('name', '')

            if goods_for_print:
                goods_for_print_data = serializers.GoodsModelForPrintSerializer(goods_for_print).data
            else:
                goods_for_print_data = None
            if warehouse_obj:
                warehouse = AppWarehouseSerializer(warehouse_obj).data
            else:
                warehouse = {
                    'id': None,
                    'name': 'Не выбран',
                }
            if measure_unit_obj:
                measure_unit = serializers.MeasureUnitListSerializer(measure_unit_obj).data
            else:
                measure_unit = None

            tp_goods.append({
                'id': str(self._get_local_line_value(cart_item, 'id') or uuid.uuid4()),
                'goods': goods_data,
                'goods_for_print': goods_for_print_data,
                'warehouse': warehouse,
                'amount': self._money(item_amount),
                'price': self._money(item_price),
                'price_no_discount': self._money(item_price),
                'nds': '20%',
                'amount_nds': self._money(item_nds),
                'amount_no_discount': self._money(item_amount_no_discount),
                'discount': self._money(Decimal('0.00')),
                'number': number,
                'quantity': self._quantity(item_quantity),
                'created_at': self._get_local_line_value(cart_item, 'created_at'),
                'updated_at': self._get_local_line_value(cart_item, 'updated_at'),
                'deleted_at': self._get_local_line_value(cart_item, 'deleted_at'),
                'quantity_success': self._quantity(Decimal('0.000')),
                'success_date': None,
                'delivery_comment': '',
                'measure_unit': measure_unit,
                'coefficient': self._quantity(coefficient),
                'custom_price': self._money(item_price),
                'currency': display_currency,
            })

            amount += item_amount
            amount_no_discount += item_amount_no_discount
            nds_amount += item_nds
            quantity += item_quantity

        return tp_goods, amount, amount_no_discount, nds_amount, quantity

    def _build_local_crm_calculation_response(
            self, data_to_serialize_1c, shopping_card_list, contract, request_user
    ):
        # CRM: расчет суммы выполняем локально, чтобы форма заказа могла показать
        # итог до сохранения даже без доступного endpoint-а 1С.
        tp_goods, amount, amount_no_discount, nds_amount, quantity = self._build_local_crm_order_goods(
            shopping_card_list, contract
        )
        return {
            'amount': self._money(amount),
            'amount_nds': self._money(nds_amount),
            'must_paid': self._money(amount),
            'prepayment': self._money(Decimal('0.00')),
            'contractor': str(data_to_serialize_1c.get('contractor')) if data_to_serialize_1c.get('contractor') else None,
            'customer_contract': str(data_to_serialize_1c.get('customer_contract')) if data_to_serialize_1c.get('customer_contract') else None,
            'customer_card': str(data_to_serialize_1c.get('customer_card')) if data_to_serialize_1c.get('customer_card') else None,
            'contract': str(contract.pk),
            'delivery_address': data_to_serialize_1c.get('delivery_address_str', ''),
            'pickup': data_to_serialize_1c.get('pickup', False),
            'operation_type': data_to_serialize_1c.get('operation_type', '0'),
            'user': str(request_user.pk),
            'limitcontract': None,
            'remcontract': None,
            'tp_goods': tp_goods,
            'comment': data_to_serialize_1c.get('comment', ''),
            'pay_type': data_to_serialize_1c.get('pay_type'),
            'amount_no_discount': self._money(amount_no_discount),
            'quantity': self._quantity(quantity),
            'calculated': True,
        }

    def _create_local_crm_orders(
            self, request, data_to_serialize_1c, serialized_data_to_1c, shopping_card_list,
            contract, customer_contract, attachments
    ):
        """Создать CRM-заказ локально, сохранив связь с договором и интересом."""
        if isinstance(serialized_data_to_1c, dict):
            serialized_orders = [serialized_data_to_1c]
        else:
            serialized_orders = serialized_data_to_1c

        order_instances = []
        with transaction.atomic():
            for order_data in serialized_orders:
                warehouse_id = order_data.get('warehouse')
                order_cart = shopping_card_list
                if warehouse_id and isinstance(order_cart, QuerySet):
                    order_cart = order_cart.filter(warehouse_id=warehouse_id)

                tp_goods, amount, amount_no_discount, nds_amount, quantity = self._build_local_crm_order_goods(
                    order_cart, contract
                )
                first_line_warehouse = None
                for line in order_cart:
                    line_warehouse = self._get_local_line_value(line, 'warehouse')
                    if line_warehouse:
                        first_line_warehouse = line_warehouse.pk
                        break
                order = models.GoodsOrderModel.objects.create(
                    user=request.user.profile,
                    contractor_id=order_data.get('contractor'),
                    contractor_member_id=order_data.get('contractor_member'),
                    contract=contract,
                    customer_contract=customer_contract,
                    # CRM: customer_card уже проверен в _resolve_crm_order_customer_card.
                    # Именно это поле показывает, кому сделана отгрузка.
                    customer_card_id=data_to_serialize_1c.get('customer_card') or order_data.get('customer_card'),
                    reason_id=data_to_serialize_1c.get('reason') or None,
                    operation_type_id=data_to_serialize_1c.get('operation_type') or '40',
                    delivery_address=order_data.get('delivery_address') or data_to_serialize_1c.get(
                        'delivery_address_str', ''
                    ),
                    delivery_company_id=order_data.get('delivery_company') or None,
                    delivery_point_id=order_data.get('delivery_point') or None,
                    delivery_purpose_id=order_data.get('delivery_purpose') or None,
                    delivery_date_plan_gte=order_data.get('delivery_date_plan_gte'),
                    delivery_date_plan_lte=order_data.get('delivery_date_plan_lte'),
                    pay_date_plan=order_data.get('pay_date_plan'),
                    pay_type_id=order_data.get('pay_type') or None,
                    pickup=order_data.get('pickup', False),
                    comment=order_data.get('comment', ''),
                    cash_pay_recipient_id=order_data.get('cash_pay_recipient') or None,
                    cash_pay_type_id=order_data.get('cash_pay_type') or None,
                    cash_unit_id=order_data.get('cash_unit') or None,
                    cash_unit_secondary_id=order_data.get('cash_unit_secondary') or None,
                    logistic_manager_id=order_data.get('logistic_manager') or None,
                    amount=amount,
                    amount_no_discount=amount_no_discount,
                    amount_paid=order_data.get('amount_paid') or Decimal('0.00'),
                    amount_to_cash=order_data.get('amount_to_cash') or Decimal('0.00'),
                    amount_to_cash_secondary=order_data.get('amount_to_cash_secondary') or Decimal('0.00'),
                    must_paid=amount,
                    nds_amount=nds_amount,
                    quantity=quantity,
                    warehouse_id=warehouse_id or first_line_warehouse or None,
                    car=order_data.get('car') or '',
                    operator_id=order_data.get('operator') or None,
                )
                if attachments:
                    order.attachments.set(attachments)
                co_executors = order_data.get('co_executors') or []
                if co_executors:
                    order.co_executors.set(co_executors)

                for item, cart_item in zip(tp_goods, order_cart):
                    goods = self._get_local_line_value(cart_item, 'goods')
                    goods_for_print = self._get_local_line_value(cart_item, 'goods_for_print') or goods
                    warehouse = self._get_local_line_value(cart_item, 'warehouse')
                    measure_unit = self._get_local_line_value(cart_item, 'measure_unit')
                    item_quantity = self._decimal(self._get_local_line_value(cart_item, 'quantity'))
                    coefficient = self._decimal(
                        self._get_local_line_value(cart_item, 'coefficient') or Decimal('1.000')
                    )
                    models.TPGoodsOrderModel.objects.create(
                        owner=order,
                        number=item['number'],
                        goods=goods,
                        goods_for_print=goods_for_print,
                        warehouse=warehouse,
                        quantity=item_quantity,
                        quantity_base=(item_quantity * coefficient),
                        measure_unit=measure_unit,
                        coefficient=coefficient,
                        amount=self._decimal(item['amount']),
                        amount_no_discount=self._decimal(item['amount_no_discount']),
                        price=self._decimal(item['price']),
                        price_no_discount=self._decimal(item['price_no_discount']),
                        nds=item['nds'],
                        discount=self._decimal(item['discount']),
                        nds_amount=self._decimal(item['amount_nds']),
                    )
                order_instances.append(order)
            if isinstance(shopping_card_list, QuerySet):
                shopping_card_list.delete()

        result = [serializers.GoodsOrderModelDetailSerializer(order).data for order in order_instances]
        for order_data in result:
            order_data['calculated'] = False
        return result[0] if len(result) == 1 else result

    @action(methods=('post',), detail=False, url_path='build_order_line')
    def build_order_line(self, request, *args, **kwargs):
        # CRM: фронт добавляет строки из потребностей/договора по одной,
        # а backend нормализует цену, единицы измерения, склад и остатки.
        contract_code = request.data.get('contract') or 'default'
        try:
            contract = models.ContractModel.objects.get(code=contract_code)
        except models.ContractModel.DoesNotExist:
            contract = models.ContractModel.objects.get(code='default')
        lines = self._get_local_crm_order_lines([request.data])
        tp_goods, amount, amount_no_discount, nds_amount, quantity = self._build_local_crm_order_goods(lines, contract)
        return Response(tp_goods[0])

    def get_queryset(self):
        if self.action == 'list':
            queryset = self.model.get_queryset().filter(operation_type_id__in=self.operation_types)
            if str(self.request.query_params.get('crm_only', '')).lower() in ('1', 'true', 'yes'):
                # CRM: отдельный список "Продажи -> Заказы" должен видеть
                # только заказы, связанные с CRM-договором.
                from customer_contracts.models import CustomerContractServicedCardModel, CustomerContractSubjectModel
                queryset = queryset.filter(customer_contract__isnull=False).select_related(
                    'customer_contract',
                    'customer_card',
                ).prefetch_related(
                    Prefetch(
                        'customer_contract__serviced_cards_relations',
                        queryset=CustomerContractServicedCardModel.objects.filter(
                            is_active=True,
                            customer_card__is_active=True,
                        ).select_related('customer_card').order_by('created_at'),
                    ),
                    Prefetch(
                        'customer_contract__subject_items',
                        queryset=CustomerContractSubjectModel.objects.filter(
                            is_active=True,
                            source_interest__isnull=False,
                        ).select_related('source_interest').order_by('created_at'),
                    )
                )
            return queryset
        else:
            return self.model.objects.select_related(
                'warehouse__manager__user',
                'execute_status',
                'delivery_status',
                'payment_status',
                'contract__price_type__currency',
                'contractor',
                'contractor_member',
                'customer_card',
                'delivery_point',
                'operator',
                'logistic_manager',
                'operation_type',
                'counter',
                'delivery_purpose',
            ).filter(is_active=True).annotate(
                amount_calculated=Sum('tp_goodsorders__amount'),
                quantity_calculated=Sum('tp_goodsorders__quantity'),
            ).order_by('-created_at')
        # TODO обход базовых прав (check_custom_permission) из BaseModelViewSet

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.get_detail_permission(request):
            return super().retrieve(request, *args, **kwargs)
        else:
            raise drf_exceptions.PermissionDenied()
    
    @action(
        methods=('put',),
        detail=True,
        url_path=r'set_warehouse',
        permission_classes=(IsAuthenticated, )
    )
    def set_warehouse(self, request, *args, **kwargs):
        """
        Присваевает склад заказу и всем товарным позициям в этом заказе
        """
        obj = self.get_object()
        if(not request.user.profile.has_full_access_to_order_editing):
            return Response({'status': status.HTTP_403_FORBIDDEN, 'data': 'Недостаточно прав для этой операции'})
        with transaction.atomic():
            try:
                warehouse_id = request.data.get('warehouse', None)
                warehouse = WarehouseModel.objects.filter(is_active=True, pk=warehouse_id).first()
                tpgoods = obj.tp_goodsorders.filter(is_active=True)
                obj.warehouse = warehouse
                obj.save()
                tpgoods.update(warehouse=warehouse)
                return Response({'status': status.HTTP_200_OK, 'data': 'Склад изменен'})
            except ObjectDoesNotExist:
                raise drf_exceptions.ValidationError('Неудалось изменить склад')
            except Exception as e:
                raise drf_exceptions.ValidationError(e)

    @action(methods=('get',), detail=True, url_path='get_purchase_prices')
    def get_purchase_prices(self, request, *args, **kwargs):
        user = request.user.profile
        if not user.warehouse_select_is_available:
            raise drf_exceptions.PermissionDenied()
        order = self.get_object()
        tp_goodsorders = order.tp_goodsorders.all().order_by('goods__name_short')
        s_data = serializers.GetPurchasePricesSerializer(tp_goodsorders, many=True).data
        return Response(s_data)

    @action(methods=('post',), detail=True, url_path='set_purchase_prices')
    def set_purchase_prices(self, request, *args, **kwargs):
        user = request.user.profile
        if not user.warehouse_select_is_available:
            raise drf_exceptions.PermissionDenied()
        order = self.get_object()
        request_data = request.data

        # Проверяем, что в запросе указаны все записи табчасти заказа:
        data_id_list = [each.get('id') for each in request_data]
        if None in data_id_list:
            raise drf_exceptions.ValidationError('id not found.')
        data_id_set = set(data_id_list)
        if not len(data_id_list) == len(data_id_set):
            raise drf_exceptions.ValidationError('Повторяющиеся записи в запросе!')
        tp_goods = order.tp_goodsorders.all().order_by('goods__name_short')
        tp_goods_id_set = set(str(each) for each in tp_goods.values_list('pk', flat=True))
        if not data_id_set == tp_goods_id_set:
            raise drf_exceptions.ValidationError('Укажите цены для всех товаров заказа.')

        # Вызываем утилиту, в resp_data_text должны быть данные для сохранения -
        # список словарей с ключами id и purchase_price.
        resp_data_text, resp_status = send_purchase_prices_to_1c(order.pk, request_data)

        # TODO заглушка пока интеграцию не сделаем:
        resp_status = 200
        resp_data_text = json.dumps(request_data)
        # Конец заглушки.

        if resp_status == 200:
            returned_data = json.loads(resp_data_text)
            with transaction.atomic():
                for each in returned_data:
                    serializer = serializers.SetPurchasePricesSerializer(data=each, instance=tp_goods.get(pk=each['id']))
                    serializer.is_valid(raise_exception=True)
                    # TODO Что делать, если данные в 1С сохранились, но в бэкенде при сохранении ошибка?
                    serializer.save()
        else:
            raise drf_exceptions.ValidationError(resp_data_text)

        return Response(serializers.GetPurchasePricesSerializer(tp_goods, many=True).data)

    @action(
        methods=('get',),
        detail=True,
        url_path='goods',
        permission_classes=(IsAuthenticated, permissions.OrderDetailPermission),
        pagination_class=paginators.TPGoodsOrderPagination,
    )
    def get_goods(self, request, *args, **kwargs):
        obj = self.get_object()
        queryset = obj.tp_goodsorders.select_related(
            'warehouse__manager__user',
            'goods',
        ).prefetch_related(
            Prefetch('goods__gallery', queryset=GalleryModel.objects.filter(is_main=True))
        ).filter(is_active=True, ).annotate(remnant_sum=Sum('goods__remnants__quantity')).order_by('number')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, self)
        s_data = serializers.TPGoodsOrderModelListSerializer(page, many=True).data
        return paginator.get_paginated_response(s_data)

    @action(
        methods=('get',),
        detail=False,
        url_path=r'delivery_points',
        permission_classes=(IsAuthenticated,),
    )
    def get_delivery_points(self, request, *args, **kwargs,):
        from common.catalogs.models import DeliveryPointModel
        from common.catalogs.serializers import DeliveryPointWithWarehousesSerializer
        query_params = request.query_params
        lat_gte = query_params.get('lat__gte', 0)
        lat_lte = query_params.get('lat__lte', 0)
        lon_gte = query_params.get('lon__gte', 0)
        lon_lte = query_params.get('lon__lte', 0)
        orders_qs = DeliveryPointModel.objects.prefetch_related(
            Prefetch(
                lookup='orders',
                queryset=models.GoodsOrderModel.objects.filter(
                    is_active=True,
                    pickup=False,
                    task_delivery_point__isnull=True,
                ).annotate(
                    amount_calculated=Sum('tp_goodsorders__amount'),
                    quantity_calculated=Sum('tp_goodsorders__quantity'),
                ).order_by('created_at')
            )
        ).filter(
            is_active=True,
            lat__gte=lat_gte,
            lat__lte=lat_lte,
            lon__gte=lon_gte,
            lon__lte=lon_lte,
            orders__isnull=False,
            orders__pickup=False,
            orders__task_delivery_point__isnull=True,
            orders__is_active=True,
        ).distinct().order_by('created_at')
        orders_data = serializers.DeliveryPointWithOrdersSerializer(
            orders_qs, many=True, context={'request': request}
        ).data
        warehouses_qs = DeliveryPointModel.objects.prefetch_related(
            Prefetch(
                lookup='warehouses',
                queryset=WarehouseModel.objects.filter(
                    is_active=True,
                    default_warehouse=False,
                ).order_by('name')
            )
        ).filter(
            is_active=True,
            lat__gte=lat_gte,
            lat__lte=lat_lte,
            lon__gte=lon_gte,
            lon__lte=lon_lte,
            warehouses__isnull=False,
            warehouses__is_active=True,
            warehouses__default_warehouse=False,
        ).distinct().order_by('created_at')
        warehouses_data = DeliveryPointWithWarehousesSerializer(
            warehouses_qs, many=True, context={"request": request}
        ).data
        return Response({"orders": orders_data, "warehouses": warehouses_data})

    @action(
        methods=('post',),
        detail=True,
        url_path=r'is_paid',
        permission_classes=(IsAuthenticated, permissions.DeliveryPermission)
    )
    def is_paid(self, request, *args, **kwargs):
        obj = self.get_object()
        # if obj.pay_type and not obj.pay_type.required:
        #     raise drf_exceptions.ValidationError('Payment is not required.')
        if obj.must_paid_touched:
            raise drf_exceptions.ValidationError('Must paid is touched.')
        resp_data_text, resp_status = send_cash_payment_to_1c(obj.pk, request.data, request.user.profile)
        if resp_status == 200:
            resp_data = json.loads(resp_data_text)
            must_paid = float(resp_data.get('must_paid'))
            with transaction.atomic():
                serializer = serializers.CashPaymentOrderModelSerializer(
                    data=request.data.get('multifield'), many=True, context={"owner": obj}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if must_paid > 0:
                    obj.payment_status_id = 'partially_paid'
                else:
                    obj.payment_status_id = 'paid'
                # TODO must_paid получать из 1С.
                obj.must_paid = must_paid
                obj.cash_payment_comment = str(request.data.get('comment', ''))[:255]
                obj.save(update_fields=('payment_status_id', 'must_paid', 'cash_payment_comment'),)
            return Response(serializers.GoodsOrderModelDetailSerializer(instance=obj).data)
        else:
            return Response(resp_data_text, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('post',),
        detail=True,
        url_path=r'goods/to_delivery',
        permission_classes=(IsAuthenticated, permissions.DeliveryPermission)
    )
    def to_delivery(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.must_paid_touched:
            raise drf_exceptions.ValidationError('must_paid is not calculated.')
        payment_is_required = not obj.pay_type or obj.pay_type.required
        if payment_is_required and not obj.payment_status_id in ['paid', 'partially_paid']:
            raise drf_exceptions.ValidationError('Payment is required')
        if obj.delivery_status_id in ('delivered', 'partially_delivered'):
            raise drf_exceptions.ValidationError('Already delivered.')
        tp_goods = obj.tp_goodsorders.filter(success_date__isnull=True, is_active=True).order_by('number')
        now = timezone.now()
        with transaction.atomic():
            for each in tp_goods:
                each.quantity_success = each.quantity
                each.success_date = now
                each.save()
        partially_delivery = obj.tp_goodsorders.filter(is_active=True, quantity_success__lt=F('quantity')).exists()
        if partially_delivery:
            obj.delivery_status_id = 'partially_delivered'
        else:
            obj.delivery_status_id = 'delivered'
        obj.delivery_date_fact = now
        obj.save(update_fields=('delivery_status_id', 'delivery_date_fact'),)
        async_task(notifications.notify_about_order_delivered, request.user.profile, obj)
        task = obj.task_delivery_point.task
        task_delivery_points = list(task.task_delivery_points.filter(is_active=True).values_list('pk', flat=True))
        task_delivered = not models.GoodsOrderModel.objects.filter(
            task_delivery_point__in=task_delivery_points,
            is_active=True,
        ).exclude(delivery_status_id__in=('delivered', 'partially_delivered')).exists()
        if task_delivered:
            task.status_id = 'completed'
            task.finished_date = now
            task.save(update_fields=('status_id', 'finished_date'),)
            from bpms.tasks.notifications import notify_about_new_status
            async_task(notify_about_new_status, str(task.pk), 'completed', str(request.user.profile.pk))
        from bpms.tasks.utils import get_status_data
        return Response(
            {
                "success_date": now.isoformat(),
                "delivery_date_fact": now.isoformat(),
                "delivery_status": obj.delivery_status.get_serializer_class()(obj.delivery_status).data,
                "task_status": get_status_data(task),
                "execute_status": obj.execute_status.get_serializer_class()(obj.execute_status).data,
            }
        )

    @action(
        methods=('put',),
        detail=True,
        url_path=r'set_driver',

    )
    def set_driver(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.profile == obj.logistic_manager:
            obj.car = request.data['car']
            obj.operator_id = request.data['operator']
            obj.save()
            return Response('updated')
        return Response(status=403, data='Недостаточно полномочий')

    @action(
        methods=('post',),
        detail=False,
        url_path=r'goods/(?P<tp_goods_id>[^/.]+)/delivery',
        permission_classes=(IsAuthenticated,)
    )
    def update_delivery(self, request, *args, **kwargs):
        tp_goods_id = kwargs.get('tp_goods_id')
        if not tp_goods_id:
            raise drf_exceptions.ValidationError('no tp_goods_id')
        try:
            tp_goods = models.TPGoodsOrderModel.objects.get(pk=tp_goods_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('tp_goods does not exist')
        # if tp_goods.success_date:
        #     raise drf_exceptions.ValidationError('success_date is not None.')
        order = tp_goods.owner
        if not order:
            raise drf_exceptions.ValidationError('order does not exist')
        if order.delivery_status_id in ('delivered', 'partially_delivered'):
            raise drf_exceptions.ValidationError('Order already delivered.')
        if order.execute_status_id == 'completed':
            raise drf_exceptions.ValidationError('Order already completed.')
        task_delivery_point = order.task_delivery_point
        if not task_delivery_point:
            raise drf_exceptions.ValidationError('task_delivery_point is null')
        task = task_delivery_point.task
        if not task:
            raise drf_exceptions.ValidationError('task is null')
        if not task.operator or not request.user.profile == task.operator:
            raise drf_exceptions.ValidationError('user has no operator')

        serializer = serializers.TPGoodsOrderModelDeliveryUpdateSerializer(data=request.data, instance=tp_goods)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        methods=('post',),
        detail=True,
        url_path='calculate_must_paid'
    )
    def calculate_must_paid(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.must_paid_touched:
            return Response({'must_paid': instance.must_paid})
        touched_tp_qs = instance.tp_goodsorders.filter(quantity_success_touched=True)
        data_to_1c = [
            {
                "id": str(each[0]),
                "quantity_success": str(each[1])
            }
            for each in touched_tp_qs.values_list('id', 'quantity_success')
        ]

        data_1c, resp_status = send_calculate_must_paid_to_1c(instance.pk, data_to_1c)
        print(f'******* data from 1c *********\n {data_1c}')
        if resp_status == 200:
            data = json.loads(data_1c)
            with transaction.atomic():
                serializer = serializers.MustPaidUpdateSerializer(instance=instance, data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                touched_tp_qs.update(quantity_success_touched=False)
            return Response(data)
        else:
            return Response({"data": data_1c, "status": resp_status}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('get',),
        detail=True,
        url_path='invoice_file',
        permission_classes=(IsAuthenticated, permissions.OrderDetailPermission)
    )
    def get_invoice_file(self, request, *args, **kwargs):
        order = self.get_object()
        # filename = F"Коммерческое предложение #{obj.counter}"
        file = None
        if not order.invoice_file:
            file_bytes, status = get_invoice_file_from_1c(order_id=order.id)
            if status == 200:
                # ready_file = DjangoFile(file_bytes, name=F'{str(order.id)}.zip')
                ready_file_2 = io.BytesIO(file_bytes)
                ready_file = DjangoFile(ready_file_2, name=F'{str(order.id)}.pdf')
                file_obj = File.objects.create(upload=ready_file)
                order.invoice_file = file_obj
                order.save()
        file = order.invoice_file.upload
        return FileResponse(file)

    @action(
        methods=('get',),
        detail=True,
        url_path='pay_file',
        permission_classes=(IsAuthenticated, permissions.OrderDetailPermission)
    )
    def get_pay_file(self, request, *args, **kwargs):

        order = self.get_object()
        if DIRECT_ORDER_FILES:
            file_base64, resp_status, status_1c_code, back_1c_status_str, file_extension = get_pay_file_from_1c(order.pk)
            file_name = F"Счет {order.number_1c} от {order.created_at.date()} от {SHORT_COMPANY_NAME}"
            ready_file_2 = io.BytesIO(file_base64)
            if not file_name:
                file_name = str(order.pk)
            ready_file = DjangoFile(ready_file_2, name=F'{file_name}.{file_extension}')
            order.has_pay_file = True
            return FileResponse(ready_file, filename=f"{file_name}.{file_extension}")
        else:
            if not order.pay_file:
                error_str = "Документ обрабатывается менеджером, результат будет отправлен на электронную почту"
                return Response({"status": "1c_error", "error_str": error_str}, status=400)
            data = AppFileSerializer(order.pay_file).data
            data['path'] = utils.get_pay_file_url(order)
            return Response(data)

    @action(
        methods=('get',),
        detail=True,
        url_path='doc_sale',
        permission_classes=(IsAuthenticated, permissions.OrderDetailPermission)
    )
    def get_sale_file(self, request, *args, **kwargs):
        order = self.get_object()
        file_base64, resp_status, status_1c_code, back_1c_status_str, file_extension = get_sale_file_from_1c(order.pk)
        file_name = F"Реализация товаров {order.number_1c} от {order.created_at.date()} от {SHORT_COMPANY_NAME}"
        ready_file_2 = io.BytesIO(file_base64)
        if not file_name:
            file_name = str(order.pk)
        ready_file = DjangoFile(ready_file_2, name=F'{file_name}.{file_extension}')
        return FileResponse(ready_file, filename=f"{file_name}.{file_extension}")

    @action(
        methods=('get',),
        detail=True,
        url_path='order_1c_form',
        permission_classes=(IsAuthenticated, permissions.OrderDetailPermission)
    )
    def get_order_1c_form(self, request, *args, **kwargs):
        order = self.get_object()
        if not order.order_form:
            error_str = "Документ обрабатывается менеджером, результат будет отправлен на электронную почту"
            return Response({"status": "1c_error", "error_str": error_str}, status=400)
        order = self.get_object()
        return Response(AppFileSerializer(order.order_form).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        task_delivery_point = instance.task_delivery_point
        if task_delivery_point:
            task = task_delivery_point.task
            if task and task.status == 'in_transit':
                raise drf_exceptions.PermissionDenied('Заказ в пути.')
        old_warehouse_id = instance.warehouse_id
        if not instance.delivery_status.edit_order_is_possible:
            raise drf_exceptions.ValidationError(_('Editing this order is forbidden'))
        request_user = request.user.profile
        instance.last_editor = request_user
        instance.save()
        data_to_serialize_1c = request.data
        data_to_serialize_1c['id'] = kwargs.get('pk')
        contract_code = request.data.get('contract')
        if not contract_code:
            raise drf_exceptions.ValidationError(_('invalid contract'))
        try:
            contract = models.ContractModel.objects.get(code=contract_code)
        except models.ContractModel.DoesNotExist:
            raise drf_exceptions.ValidationError(_('invalid contract'))
        oper_type = str(request.data.get('oper_type', ''))
        data_to_serialize_1c['operation_type'] = oper_type
        data_to_serialize_1c['user'] = str(instance.user_id)
        data_to_serialize_1c['contract'] = contract
        shopping_card_list = request.data.get('tp_goods')
        serialized_data_to_1c = collect_prepared_order_data(data_to_serialize_1c, shopping_card_list, instance.user)
        serialized_data_to_1c['id'] = str(instance.pk)
        create_orders = data_to_serialize_1c.get('create_orders')
        if create_orders and isinstance(create_orders, dict):
            new_orders = dict()
            for key, value in create_orders.items():
                new_order = copy.deepcopy(serialized_data_to_1c)
                new_order.pop('id', None)
                new_order['warehouse'] = value.get('warehouse')
                new_order['tp_goods'] = value.get('tp_goods')
                new_orders[key] = new_order
            serialized_data_to_1c['create_orders'] = new_orders
        else:
            serialized_data_to_1c['create_orders'] = dict()
        # Отправка в 1C
        attachments = request.data.get('attachments', [])
        data_from_1c, status_1c = send_update_order_to_1c(serialized_data_to_1c, operation_type=oper_type)
        if status_1c != 200:
            return Response(status=400, data={"status": status_1c, "data": data_from_1c})
        loaded_data_from_1c = json.loads(data_from_1c)
        returned_order_data = collect_data_after_1c(serialized_data_to_1c, data_to_serialize_1c, loaded_data_from_1c[0])
        returned_order_data['operation_type'] = instance.operation_type_id

        if status_1c == 200:
            with transaction.atomic():
                serialized_from_1c = serializers.CreateFrom1CGoodsOrderSerializer(
                    instance=instance,
                    data=returned_order_data
                )
                serialized_from_1c.is_valid(raise_exception=True)
                instance = serialized_from_1c.save()
                returned_create_orders = returned_order_data.get('create_orders')
                if returned_create_orders:
                    for key, value in returned_create_orders.items():
                        s_data_to_1c = serialized_data_to_1c['create_orders'].get(key)
                        data_to_s_1c = data_to_serialize_1c
                        returned_create_order = collect_data_after_1c(s_data_to_1c, data_to_s_1c, value)
                        returned_create_order['operation_type'] = '40'
                        s_from_1c = serializers.CreateFrom1CGoodsOrderSerializer(
                            data=returned_create_order,
                        )
                        s_from_1c.is_valid(raise_exception=True)
                        s_from_1c.save()
                        # TODO добавить уведомления.
            # async_task(utils.collect_and_send_order_email, instance) TODO добавить уведомления
            # async_task(utils.notify_managers_about_new_order, instance)
            if attachments:
                async_task(send_order_files_to_1c, instance.id, attachments)
        # TODO заглушка
        tp_goods = returned_order_data['tp_goods']
        if tp_goods:
            instance.warehouse_id = tp_goods[0]['warehouse_id']
            instance.save()
        async_task(notifications.notify_about_update_order, request_user, instance, old_warehouse_id)
        result_data = serializers.GoodsOrderModelDetailSerializer(instance).data
        result_data['calculated'] = False
        return Response(result_data)

    @action(methods=('post',), detail=True, url_path='split_by_warehouses')
    def split_by_warehouses(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.delivery_status.edit_order_is_possible:
            raise drf_exceptions.ValidationError(_('Editing this order is forbidden'))
        warehouse_id = request.data.get('warehouse')
        if not warehouse_id:
            raise drf_exceptions.ValidationError('Warehouse is not be empty.')
        try:
            warehouse = WarehouseModel.objects.get(is_active=True, pk=warehouse_id)
        except WarehouseModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Warehouse not found.')
        tp_goods_id = request.data.get('tp_goods', [])
        tp_goods = list(instance.tp_goodsorders.filter(pk__in=tp_goods_id))
        if not tp_goods or not len(tp_goods_id) == len(tp_goods):
            raise drf_exceptions.ValidationError('Invalid tp_goods.')
        tp_goods_data = [
            {
                'goods': str(each.goods_id),
                'goods_for_print': str(each.goods_for_print_id),
                'quantity': str(each.quantity),
                'warehouse': warehouse_id,
                'measure_unit': str(each.measure_unit_id) if each.measure_unit_id else None,
                'coefficient': str(each.coefficient),
                'custom_price': str(each.price),
            } for each in tp_goods
        ]
        data_to_1c = {
            "contractor": instance.contractor_id,
            "contractor_member": instance.contractor_member_id,
            "logistic_manager": instance.logistic_manager_id,
            "contract": instance.contract,
            "warehouse": warehouse.pk,
            "delivery_address_str": instance.delivery_address,
            "delivery_point": instance.delivery_point_id,
            "delivery_purpose": instance.delivery_purpose_id,
            "delivery_date_plan_gte": instance.delivery_date_plan_gte,
            "delivery_date_plan_lte": instance.delivery_date_plan_lte,
            "pay_type": instance.pay_type_id,
            "pay_date_plan": instance.pay_date_plan,
            "pickup": instance.pickup,
            "operation_type": "40",
            "cash_pay_recipient": instance.cash_pay_recipient_id,
            "cash_pay_type": instance.cash_pay_type_id,
            "comment": instance.comment,
            "attachments": list(instance.attachments.all().values_list('pk', flat=True)),
            "car": instance.car,
            "operator": instance.operator_id,
            "amount_paid": instance.amount_paid,
            "cash_unit": instance.cash_unit_id,
            "cash_unit_secondary": instance.cash_unit_secondary_id,
            "amount_to_cash": instance.amount_to_cash,
            "amount_to_cash_secondary": instance.amount_to_cash_secondary,
            "tp_goods": tp_goods_data,
        }
        serialized_data_to_1c = collect_prepared_order_data(data_to_1c, None, request.user.profile)
        serialized_data_to_1c['original_order'] = {
            "id": str(instance.pk),
            "tp_goods": tp_goods_id,
        }
        data_from_1c, status_1c = send_split_order_by_warehouses(serialized_data_to_1c)
        if status_1c != 200:
            return Response(status=status_1c, data=data_from_1c)
        loaded_data_from_1c = json.loads(data_from_1c)
        returned_order_data = collect_data_after_1c(serialized_data_to_1c, data_to_1c, loaded_data_from_1c['new_order'])
        returned_order_data['operation_type'] = instance.operation_type_id
        with transaction.atomic():
            serialized_from_1c = serializers.CreateFrom1CGoodsOrderSerializer(
                data=returned_order_data
            )
            serialized_from_1c.is_valid(raise_exception=True)
            new_order = serialized_from_1c.save()
            returned_original_order_data = loaded_data_from_1c['original_order']
            instance.amount_no_discount = returned_original_order_data['amount_no_discount']
            instance.amount = returned_original_order_data['amount']
            instance.amount_to_cash = returned_original_order_data.get('amount_to_cash', 0)
            instance.amount_to_cash_secondary = returned_original_order_data.get('amount_to_cash_secondary', 0)
            instance.quantity = returned_original_order_data['quantity']
            instance.must_paid = returned_original_order_data['must_paid']
            instance.nds_amount = returned_original_order_data['nds_amount']
            instance.save()
            instance.tp_goodsorders.filter(pk__in=tp_goods_id).delete()
        return Response(serializers.GoodsOrderModelDetailSerializer(new_order).data)

    @action(methods=('post',), detail=False, )
    def create_from_cart(self, request, *args, **kwargs):
        oper_type = str(request.data.get('oper_type', ''))
        request_user = request.user.profile

        data_to_serialize_1c = request.data
        contract_code = request.data.get('contract')
        customer_contract_id = request.data.get('customer_contract')
        customer_contract = None
        customer_card = None
        if not contract_code and customer_contract_id:
            contract_code = 'default'
            request.data['contract'] = contract_code
        try:
            contract = models.ContractModel.objects.get(code=contract_code)
        except models.ContractModel.DoesNotExist:
            raise drf_exceptions.ValidationError(_('invalid contract'))
        data_to_serialize_1c['operation_type'] = oper_type
        data_to_serialize_1c['contract'] = contract
        data_to_serialize_1c['user'] = request_user.id
        if customer_contract_id:
            try:
                from customer_contracts.models import CustomerContractModel
                customer_contract = CustomerContractModel.get_queryset(request).get(pk=customer_contract_id)
            except CustomerContractModel.DoesNotExist:
                raise drf_exceptions.ValidationError(_('invalid CRM contract'))
            data_to_serialize_1c['customer_contract'] = customer_contract.pk
            # CRM: перед созданием заказа фиксируем явного получателя отгрузки.
            customer_card = self._resolve_crm_order_customer_card(
                request,
                customer_contract,
                request.data.get('customer_card')
            )
            data_to_serialize_1c['customer_card'] = customer_card.pk

        if customer_contract:
            # CRM: если заказ создается из договора/интереса, не используем
            # корзину и ContractorModel. Табличная часть приходит из формы.
            order_lines = self._get_local_crm_order_lines(request.data.get('tp_goods'))
            attachments = request.data.get('attachments', [])
            serialized_data_to_1c = {
                'contractor': None,
                'contractor_member': None,
                'warehouse': request.data.get('warehouse'),
                'delivery_address': request.data.get('delivery_address_str') or request.data.get('delivery_address'),
                'delivery_company': request.data.get('delivery_company'),
                'delivery_point': request.data.get('delivery_point'),
                'delivery_purpose': request.data.get('delivery_purpose'),
                'delivery_date_plan_gte': request.data.get('delivery_date_plan_gte'),
                'delivery_date_plan_lte': request.data.get('delivery_date_plan_lte'),
                'pay_date_plan': request.data.get('pay_date_plan'),
                'pay_type': request.data.get('pay_type'),
                'pickup': request.data.get('pickup', False),
                'comment': request.data.get('comment', ''),
                'cash_pay_recipient': request.data.get('cash_pay_recipient'),
                'cash_pay_type': request.data.get('cash_pay_type'),
                'cash_unit': request.data.get('cash_unit'),
                'cash_unit_secondary': request.data.get('cash_unit_secondary'),
                'logistic_manager': request.data.get('logistic_manager'),
                'amount_paid': request.data.get('amount_paid') or Decimal('0.00'),
                'amount_to_cash': request.data.get('amount_to_cash') or Decimal('0.00'),
                'amount_to_cash_secondary': request.data.get('amount_to_cash_secondary') or Decimal('0.00'),
                'car': request.data.get('car') or '',
                'operator': request.data.get('operator'),
                'co_executors': request.data.get('co_executors') or [],
                'customer_card': customer_card.pk if customer_card else None,
            }
            if oper_type == '0':
                return Response(
                    self._build_local_crm_calculation_response(
                        data_to_serialize_1c, order_lines, contract, request_user
                    )
                )
            return Response(
                self._create_local_crm_orders(
                    request,
                    data_to_serialize_1c,
                    serialized_data_to_1c,
                    order_lines,
                    contract,
                    customer_contract,
                    attachments
                )
            )

        shopping_card_list = models.ShoppingCartModel.objects.filter(
            user=request.user.profile,
            cart_type_id=self.shopping_cart_type,
        ).order_by('created_at')
        if oper_type == "0":
            serialized_data_to_1c = collect_prepared_order_data(data_to_serialize_1c, shopping_card_list, request_user)
        else:
            serialized_data_to_1c = []

            warehouses = set(shopping_card_list.values_list('warehouse', flat=True).distinct())

            for warehouse in warehouses:
                # for warehouse in warehouses:
                data_to_serialize_1c['warehouse'] = warehouse

                shopping_card_list_by_warehouse = shopping_card_list.filter(warehouse_id=warehouse)
                serialized_data_to_1c_part_data = collect_prepared_order_data(data_to_serialize_1c,
                                                                              shopping_card_list_by_warehouse,
                                                                              request_user)
                serialized_data_to_1c.append(serialized_data_to_1c_part_data)

        attachments = request.data.get('attachments', [])

        # Отправка в 1C
        try:
            data_from_1c, status_1c = send_offer_to_1c(serialized_data_to_1c, operation_type=oper_type)
        except requests.exceptions.MissingSchema:
            if not customer_contract:
                raise
            if oper_type == '0':
                return Response(
                    self._build_local_crm_calculation_response(
                        data_to_serialize_1c, shopping_card_list, contract, request_user
                    )
                )
            return Response(
                self._create_local_crm_orders(
                    request,
                    data_to_serialize_1c,
                    serialized_data_to_1c,
                    shopping_card_list,
                    contract,
                    customer_contract,
                    attachments
                )
            )
        if status_1c != 200:
            return Response(status=400, data={"status": status_1c, "data": data_from_1c})

        loaded_data_from_1c = json.loads(data_from_1c)
        if oper_type == '0':
            returned_order_data = collect_data_after_1c(
                serialized_data_to_1c, data_to_serialize_1c, loaded_data_from_1c[0]
            )
        else:
            returned_order_data = []
            for order_data in loaded_data_from_1c:
                serialized_data_to_1c_part_data = collect_prepared_order_data(data_to_serialize_1c,
                                                                              shopping_card_list.filter(
                                                                                  warehouse=order_data.get('warehouse',
                                                                                                           None)),
                                                                              request_user)
                order_data = collect_data_after_1c(serialized_data_to_1c_part_data, data_to_serialize_1c, order_data)
                returned_order_data.append(order_data)
        if status_1c == 200:
            try:
                from bkz3.settings import CREATE_SHIPMENT_EVENT
            except ImportError:
                CREATE_SHIPMENT_EVENT = False
            if oper_type != '0':
                with transaction.atomic():
                    orders_instances = []
                    for order in returned_order_data:
                        serialized_from_1c = serializers.CreateFrom1CGoodsOrderSerializer(data=order)
                        if serialized_from_1c.is_valid(raise_exception=True):
                            instance = serialized_from_1c.save()

                            result_data = serializers.GoodsOrderModelDetailSerializer(instance).data
                            orders_instances.append(instance)
                            result_data['calculated'] = False
                        else:
                            instance = None
                    shopping_card_list.delete()
                for order_instance in orders_instances:
                    if CREATE_SHIPMENT_EVENT:
                        utils.createShipmentEvent(order_instance)
                    async_task(utils.collect_and_send_order_email, order_instance)
                    async_task(utils.notify_managers_about_new_order, order_instance)
                    async_task(notifications.notify_about_new_order, order_instance)
                    if order_instance.cash_pay_recipient:
                        async_task(notifications.notify_pay_recipient_about_new_order, order_instance)
                    if order_instance.logistic_manager:
                        async_task(notifications.notify_logistic_manager_about_new_order(request_user, order_instance))
                    if attachments:
                        async_task(send_order_files_to_1c, order_instance.id, attachments)
                        # send_order_files_to_1c(order_instance.id, attachments)
            else:
                currency = contract.price_type.currency_id
                for each in returned_order_data['tp_goods']:
                    each['currency'] = currency

                result_data = serializers.EmptyOrderSerializer(returned_order_data).data
                amount_no_discount = Decimal('0.00').quantize(Decimal('0.01'))
                for item in result_data['tp_goods']:
                    goods = item['goods']
                    goods['currency'] = item['currency']
                    goods['amount'] = item['amount']
                    goods['price'] = item['price']
                    # goods['price_no_discount'] = item['price_no_discount'] #TODO получем в 1С
                    goods['number'] = item['number']
                    goods['amount_no_discount'] = item['amount_no_discount']
                    amount_no_discount += Decimal(item['amount_no_discount']).quantize(Decimal('0.01'))
                    goods['nds'] = item['nds']
                    goods['amount_nds'] = item['amount_nds']
                result_data['amount_no_discount'] = amount_no_discount.__str__()
                result_data['calculated'] = True

        return Response(result_data)

    @action(methods=('post',), detail=False, )
    def create_offer(self, request, *args, **kwargs):
        data = request.data
        to_email = data.pop('to_email', None)
        serializer = serializers.CreateOfferFromCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        data['goods'] = models.ShoppingCartModel.objects.filter(
            user=request.user.profile,
            cart_type_id=self.shopping_cart_type,
        ).values('goods', 'quantity')
        # TODO тут мы отправляем данные в 1С. Пока отправляем пустой pdf.
        offer_number = '000001'
        if to_email and isinstance(to_email, str):
            utils.to_email_offer(to_email, offer_number, file_path='empty_pdf.pdf')
            return Response('ok')
        file = open(f"{BASE_DIR}/empty_pdf.pdf", 'rb')
        return FileResponse(file)

    @action(methods=('post',), detail=False)
    def get_prices(self, request, *args, **kwargs):
        data = request.data
        serializer = serializers.SendOfferFromCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        data['goods'] = models.ShoppingCartModel.objects.filter(
            user=request.user.profile,
            cart_type_id=self.shopping_cart_type,
        ).values('goods', 'quantity')
        returned_1c_data, status = send_offer_to_1c(data, operation_type="0")
        returned_data = json.loads(returned_1c_data)
        return Response(data=returned_data,
                        status=200)

    @action(methods=('get',), detail=False, url_path='form_info')
    def get_form_info(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(is_active=True, code='orders_form_info').metadata
        except AppInfo.DoesNotExist:
            data = dict()
        return Response(data)

    @action(methods=('get',), detail=False, url_path="payments_form_info")
    def get_payments_form_info(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(code='payments_form_info', is_active=True).metadata
        except AppInfo.DoesNotExist:
            data = {
                    "modalLabel": "Подтверждение оплаты",
                    "actionButtons": [
                        {
                            "name": "Подтвердить оплату",
                            "type": "primary",
                            "size": "large",
                            "action": "submit",
                            "disabled": False
                        },
                        {
                            "action": "empty_submit",
                            "disabled": False,
                            "name": "Без оплаты",
                            "size": "large",
                            "type": "default"
                        }
                    ],
                    "form": {
                        "comment": "",
                        "multifield": [
                            {
                                "cash_pay_type": None,
                                "amount": None
                            }
                        ]
                    },
                    "formInfo": [
                        {
                            "widget": "MultiField",
                            "key": "multifield",
                            "multiple": True,
                            "formInfo": [
                                {
                                    "name": "Способ получения",
                                    "key": "cash_pay_type",
                                    "widget": "TreeSelect",
                                    "apiUrl": "/crm/cash_pay_types/",
                                    # "rules": {
                                    #     "message": "Обязательно для заполнения",
                                    #     "required": True
                                    # },
                                },
                                {
                                    "name": "Сумма",
                                    "key": "amount",
                                    "type": "numeric",
                                    "widget": "Input",
                                    "deleteButton": True,
                                    # "rules": {
                                    #     "message": "Обязательно для заполнения",
                                    #     "required": True,
                                    #     "pattern": {
                                    #         "value": "/^(0|[1-9]\d*)(\.\d+)?$/",
                                    #         "message": 'Введите число',
                                    #     }
                                    # },
                                }
                            ]
                        },
                        {
                            "name": "Комментарий",
                            "key": "comment",
                            "widget": "TextArea"
                        }
                    ]
                }
        return Response(data)

    @action(methods=('get',), detail=False, url_path='table_info', )
    def get_table_info(self, request, *args, **kwargs):
        data = AppInfo.objects.get(code='orders_table_info').metadata
        return Response(data)

    @action(
        methods=('get',),
        detail=True,
        url_path='action_info',
        permission_classes=(IsAuthenticated, permissions.OrderDetailPermission)
    )
    def get_action_info(self, request, *args, **kwargs):
        user = request.user.profile
        order = self.get_object()
        try:
            actions = AppInfo.objects.get(code='orders_action_info',).metadata
        except AppInfo.DoesNotExist:
            actions = {
                "edit": {"availability": True},
                "add_task": {"availability": True},
                'blob_file': True,
                "shipment": {"availability": True},
                "share": {"availability": True},
                "document_printing": {"availability": True},
            }
        logistic_manager = order.logistic_manager
        is_logistic_manager = logistic_manager is not None and user == logistic_manager
        if ((not user == order.author and not user.has_full_access_to_order_editing) or
            (not order.delivery_status.edit_order_is_possible)):
            actions.pop('edit', None)
        if not user.can_create_logistic_task and not is_logistic_manager:
            actions.pop('add_task', None)
        if user.is_storekeeper:
            actions.pop('shipment', None)

        if order.delivery_status.code in ('delivered', 'partially_delivered'):
            actions.pop('edit', None)

        task_delivery_point = order.task_delivery_point
        if task_delivery_point:
            if task_delivery_point.task.status_id in ('in_transit', 'completed',):
                actions.pop('edit', None)
        # order = models.GoodsOrderModel()
        # if order.last_editor is not None \
        #         and order.last_editor.can_create_logistic_task:
        #     actions.pop('edit', None)


        operator = order.operator
        is_driver = operator if operator is not None else False
        if not is_logistic_manager and not is_driver:
            actions.pop('document_printing', None)
        data = {"actions": actions}
        return Response(data)


class ReturnOrderViewSet(GoodsOrderModelViewSet):
    operation_types = (OperationTypeEnum.to_return.value,)
    shopping_cart_type = 'return_cart'


class GetReportAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        file = open(f"{BASE_DIR}/empty_xls.xls", 'rb')
        return FileResponse(file, content_type='application/octet-stream')



class BitrixFormAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user

        dealer_record = ContractorProfileModel.objects.filter(user=user.profile).first()

        if dealer_record:
            dealer = dealer_record.contractor.name
        else:
            dealer = request.user.profile.full_name

        if len(request.data['user_phone']) > 0:
            phone = request.data['user_phone']
            request.user.profile.phone = phone
            request.user.profile.save()
        else:
            phone = request.user.profile.phone

        dict = {
            'fields': {
                "TITLE": dealer,
                "SOURCE_ID": 'WEB',
                "LAST_NAME": user.last_name,
                "NAME": user.first_name,
                "SECOND_NAME": user.middle_name,
                "PHONE": [
                    {
                        "VALUE": phone,
                        "VALUE_TYPE": "WORK"
                    }
                ],
                "EMAIL": [
                    {
                        "VALUE": user.email,
                        "VALUE_TYPE": "WORK"
                    }
                ],
                "COMMENTS": request.data['issue_description']
            }, 'params': {
                "REGISTER_SONET_EVENT": "Y"
            }
        }
        external_id_rec = request.user.profile.external_ids.all().order_by('outer_id').last()

        if external_id_rec:
            dict['fields']['CONTACT_ID'] = external_id_rec.outer_id

        lead_gen_res = requests.post('https://promsytex.bitrix24.ru/rest/' + BITRIX_TOKEN + '/crm.lead.add.json',
                                     json=dict).content

        d = json.loads(lead_gen_res)
        outer_id = d['result']

        ProfileModelOuterLeadID.objects.create(profile=user.profile, outer_id=outer_id)

        return Response(data={'status': 'ok'})


class BitrixOuterHookAPIView(APIView):
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        raise drf_exceptions.NotFound() # 17.04.2026

        outer_id = request.data.get('data[FIELDS][ID]')
        token = request.data.get('auth[application_token]')

        if not outer_id or not token:
            return Response(status=200)

        if token != BITRIX_OUTER_TOKEN:
            return Response(status=200)

        lead_record = ProfileModelOuterLeadID.objects.filter(outer_id=outer_id).first()

        if lead_record:
            profile = lead_record.profile
            lead_response = requests.get(
                'https://promsytex.bitrix24.ru/rest/' + BITRIX_TOKEN + '/crm.lead.get.json?ID=' + outer_id,
                timeout=(3.05, 10))

            if lead_response.status_code == 200:
                d = json.loads(lead_response.content)
                if 'CONTACT_ID' in d['result']:
                    ProfileModelOuterID.objects.get_or_create(outer_id=d['result']['CONTACT_ID'], profile=profile)

        return Response(data={'status': 'ok'})


class GoodsOrderSearchView(HaystackGenericAPIView):
    index_models = (models.GoodsOrderModel,)
    serializer_class = serializers.GoodsOrderModelSearchSerializer
    pagination_class = paginators.CustomPagination
    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request, *args, **kwargs):
        text = request.query_params.get('text')
        if not text:
            search_queryset = SearchQuerySet().none()
        else:
            search_queryset = RelatedSearchQuerySet().filter(
                text=text,
            ).models(models.GoodsOrderModel).load_all()
        page = self.paginate_queryset(search_queryset)
        s_data = self.serializer_class(page, many=True, context={'request': request}).data
        return self.get_paginated_response(s_data)


class ContractGetFileFrom1CView(APIView):
    permission_classes = (permissions.ContractGetFilePermission,)

    @staticmethod
    def get_object(pk):
        return models.ContractModel.objects.get(pk=pk)

    def get(self, request, *args, **kwargs):
        pk = kwargs['contact_uid']
        contract = self.get_object(pk)
        self.check_object_permissions(request, obj=contract)
        file, status_1c = get_contract_file_from_1c(pk, contract.name)
        if status_1c:
            return FileResponse(file)
        return Response(status=400)


class LogisticMonitorPageInfo(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(is_active=True, code='logistic_monitor_page_info').metadata
        except AppInfo.DoesNotExist:
            data = dict()
        return Response(data)


class CashPayTypeModelViewSet(BaseCatalogViewSet):
    model = models.CashPayTypeModel
