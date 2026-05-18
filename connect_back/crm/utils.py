from decimal import Decimal
from urllib.parse import quote

from django.db import models
from django.db.models import Case, F, Sum, When
from django_q.tasks import async_task
from rest_framework import exceptions as drf_exceptions

from bkz3.settings import (BACKEND_URL, DOWNLOADER_PATH, FRONTEND_URL,
                           GLOBAL_FRONT_SETTINGS)
from bpms.event_calendar.models import (CalendarModel, EventCalendarModel,
                                        EventCalendarTypeModel)
from crm.models import OrderManagerModel
from notifications.models import (EmailNotificationAttachmentModel,
                                  EmailNotificationModel,
                                  EmailNotificationRecipientModel)
from notifications.utils import send_email

from . import search_indexes


def collect_and_send_order_email(order):
    context = dict()
    order_records = order.tp_goodsorders.all()
    order_records_aggregation = order_records.aggregate(total_sum=Sum('amount'), total_count=Sum('quantity'))
    context['order_counter'] = order.number_1c
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    # CRM: в заказах из CRM клиент хранится как CustomerCardModel на самом
    # заказе. Старый contractor используем только для не-CRM заказов.
    crm_customer = getattr(order, 'customer_card', None)
    if crm_customer:
        context['contractor_name'] = crm_customer.name
    elif order.contractor:
        context['contractor_name'] = order.contractor.name
    else:
        context['contractor_name'] = ''
    context['frontend_url'] = FRONTEND_URL
    total_count = order_records_aggregation.get('total_count', 0)
    if not total_count:
        total_count = 0
    total_summ = order_records_aggregation.get('total_sum', 0)
    if not total_summ:
        total_summ = 0
    context['total_count'] = float(order.quantity)  # TODO
    context['total_summ'] = float(order.amount)
    context['order_user_name'] = order.user.user.full_name
    # context['total_summ'] = float(order.amount)
    goods_in_order = order_records.values('goods__name', 'quantity', 'amount', 'goods__article_number',
                                          'discount', 'price', 'nds', 'nds_amount', 'amount_no_discount',
                                          'number').order_by('number')

    goods_in_order_list = list(goods_in_order)
    for goods in goods_in_order_list:
        goods['quantity'] = float(goods['quantity'])
        goods['amount'] = float(goods['amount'])
        goods['price'] = float(goods['price'])
        goods['discount'] = float(goods['discount'])
        goods['amount_no_discount'] = float(goods['amount_no_discount'])
        goods['nds_amount'] = float(goods['nds_amount'])
        # goods['total_count'] = float(goods['total_count'])
    context['goods_in_order'] = goods_in_order_list
    notification = EmailNotificationModel.objects.create(template='order_to_recipient',
                                                         subject=F'Заказ {order.number_1c} оформлен!',
                                                         context=context)
    recepient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                               recipient=order.user.user.email)
    send_email(notification.id)
    # send_email.delay(notification.id)
    # async_task(send_email, notification.id)


def notify_managers_about_new_order(order):
    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    context['order_number'] = order.number_1c
    notification = EmailNotificationModel.objects.create(template='order_to_manager',
                                                         subject='Создан новый заказ!',
                                                         context=context)
    order_manager_list = OrderManagerModel.objects.filter(is_active=True)
    for each in order_manager_list:
        recepient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                                   recipient=each.profile.user.email)

    send_email(notification.id)
    # async_task(send_email,notification.id)
    # async_task(send_email, notification.id)


def to_email_offer(email: str, offer_number: str, file_path: str):
    context = {
        'offer_number': offer_number
    }
    notification = EmailNotificationModel.objects.create(
        template='to_email_offer',
        subject='Коммерческое предложение',
        context=context,
    )
    EmailNotificationAttachmentModel.objects.create(email_notification=notification, path=file_path)
    EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                   recipient=email)
    # send_email.delay(notification.id)
    async_task(send_email, notification.id)


def update_order_index(instance):
    search_indexes.GoodsOrderModelIndex().update_object(instance)


def get_pay_file_url(instance):
    if DOWNLOADER_PATH is not None:
        parent_path = quote(f"?obj={instance.pk}&id={instance.pay_file_id}&target=pay_file")
        return f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'
    else:
        return instance.pay_file.absolute_url


def calculate_order(data, shopping_cart_list):
    shopping_cart_list = shopping_cart_list.annotate(amount=Case(
                When(custom_price__isnull=False, then=F('custom_price') * F('quantity')),
                default=F('goods__price_by_catalog') * F('quantity'),
                output_field=models.DecimalField(max_digits=15, decimal_places=2)),
        )
    amount = shopping_cart_list.aggregate(Sum('amount'))['amount__sum']
    amount_nds = amount * Decimal("0.20")
    data['amount'] = amount
    data['amount_nds'] = amount_nds
    data['amount_no_discount'] = amount
    data['tp_goods'] = shopping_cart_list
    data['delivery_address'] = ''
    from .serializers import EmptyOrderWithout1CSerializer
    result = EmptyOrderWithout1CSerializer(data).data
    result['calculated'] = True
    amount_no_discount = Decimal('0.00').quantize(Decimal('0.01'))
    for item in result['tp_goods']:
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
    result['amount_no_discount'] = amount_no_discount.__str__()
    return result


def get_event_description(order):
    goods = order.tp_goodsorders.filter(is_active=True).select_related(
        'goods',
        'measure_unit'
    ).values(
        'goods__name',
        'quantity',
        'amount',
        'price',
        'number',
        'measure_unit__name_short'
    ).order_by('number')
    html = '<table border="1"><tr><th>№</th><th>Наименование</th><th>Количество</th><th>Ед.изм.</th><th>Цена</th><th>Сумма</th></tr>'
    total_amount = 0
    for item in goods:
        unit = item['measure_unit__name_short'] or 'Не указано'
        name = item['goods__name'] or 'Не указано'
        amount = item['amount'] or 0
        total_amount += amount
        html += f'<tr><td>{item["number"]}</td><td>{name}</td><td>{item["quantity"]}</td><td>{unit}</td><td>{item["price"]}</td><td>{amount}</td></tr>'
    html += f'<tr><td colspan="5"><strong>Итого:</strong></td><td><strong>{total_amount}</strong></td></tr>'
    html += '</table>'
    return html


def get_event_name(order):
    return f'Отгрузка заказа {order.number_1c}'


def createShipmentEvent(order):
    calendar = CalendarModel.objects.filter(
        is_active=True,
        calendar_group_id='resources',
        code='not_distributed'
    ).first()
    event_type = EventCalendarTypeModel.objects.filter(
        is_active=True,
        code='shipment'
    ).first()
    if not calendar or not event_type:
        raise drf_exceptions.ValidationError(
            'Убедитесь что создан календарь с кодом not_distributed и тип события с кодом shipment'
        )
    EventCalendarModel.objects.create(
        calendar=calendar,
        event_type=event_type,
        privacy_id='public',
        color=calendar.color,
        start_at=order.delivery_date_plan_gte,
        end_at=order.delivery_date_plan_lte,
        address=order.delivery_address,
        description=get_event_description(order),
        name=get_event_name(order)
    )
    return
