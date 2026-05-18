from django.utils import timezone
from crm.models import GoodsOrderModel
from common.models import TechnicalIsolatedCallsControlModel
from django_q.tasks import async_task
from bkz3.settings import SHORT_COMPANY_NAME
from .utils import get_remnants_from_1c
from .utils import get_pay_file_from_1c
from .utils import get_order_form_from_1c
from .utils import get_zip_file_and_save
from .utils import send_pay_file_email
from .utils import changed_pay_file_email
from .utils import send_order_from_1c_file_email
from .utils import set_isolated_funk_is_start
from .utils import set_isolated_funk_is_end


def get_pay_file_for_order(order_id):
    order = GoodsOrderModel.objects.get(id=order_id)
    file_base64, status, status_1c_code, back_1c_status_str, file_extension = get_pay_file_from_1c(order_id=order_id)
    date_created = order.created_at.date()
    file_name = F"Счет {order.number_1c} от {date_created} от {SHORT_COMPANY_NAME}"
    if not order.pay_file and status_1c_code == "1":
        order.pay_file = get_zip_file_and_save(file_base64, order.id, file_name, file_extension)
        order.find_pay_file = False
        order.save()
        async_task(send_pay_file_email, order.id)
    if order.pay_file and status_1c_code == "2":
        order.pay_file = get_zip_file_and_save(file_base64, order.id, file_name, file_extension)
        order.find_pay_file = False
        order.save()
        async_task(changed_pay_file_email, order.id)


def get_order_form_for_order(order_id):
    order = GoodsOrderModel.objects.get(id=order_id)
    if not order.order_form:
        file_base64, status, status_1c_code, back_1c_status_str = get_order_form_from_1c(order_id=order_id)

        if status_1c_code == "1":
            order.order_form = get_zip_file_and_save(file_base64, order.id)
            order.find_order_form = False
            order.save()
            async_task(send_order_from_1c_file_email, order.id)


def check_order_find_pay_file():
    # Делаем запись в техническую модель о начале выполнения вызываемой извне функции
    funk_name = "check_order_pay_file"
    control_obj, created = TechnicalIsolatedCallsControlModel.objects.get_or_create(name=funk_name)
    set_isolated_funk_is_start(control_obj)

    orders = GoodsOrderModel.objects.filter(find_pay_file=True,
                                            is_active=True)[:20]
    for order in orders:
        file_base64, status, status_1c_code, back_1c_status_str, file_extension = get_pay_file_from_1c(order_id=order.id)
        if status_1c_code == "1":
            order.pay_file = get_zip_file_and_save(file_base64, order.id, file_extension)
            order.find_pay_file = False
            order.save()
            async_task(send_pay_file_email, order.id)
            # send_pay_file_email(order.id)

    # Делаем запись о завершении функции
    set_isolated_funk_is_end(control_obj)


def check_order_find_order_form():
    # Делаем запись в техническую модель о начале выполнения вызываемой извне функции
    funk_name = "check_order_form"
    control_obj, created = TechnicalIsolatedCallsControlModel.objects.get_or_create(name=funk_name)
    set_isolated_funk_is_start(control_obj)

    orders = GoodsOrderModel.objects.filter(find_order_form=True,
                                            is_active=True)[:20]
    for order in orders:
        file_base64, status, status_1c_code, back_1c_status_str = get_order_form_from_1c(order_id=order.id)
        if status_1c_code == "1":
            order.order_form = get_zip_file_and_save(file_base64, order.id)
            order.find_order_form = False
            order.save()
            async_task(send_order_from_1c_file_email, order.id)
            send_order_from_1c_file_email(order.id)

    # Делаем запись о завершении функции
    set_isolated_funk_is_end(control_obj)


def get_remnants_from_1c_cron():
    get_remnants_from_1c()
