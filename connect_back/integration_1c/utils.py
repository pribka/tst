from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
import random
import requests
import json
from notifications.models import EmailNotificationModel, EmailNotificationRecipientModel, \
    EmailNotificationAttachmentModel
from base64 import b64decode
from bkz3.settings import EXPORT_1C_DATA_URL, EXPORT_1C_DATA_TOKEN
from bkz3.settings import SUPPORT_EMAIL
from bkz3.settings import COMPANY_NAME
from django_q.tasks import async_task

from django.db import transaction
from django.utils import timezone
import base64
import io
from datetime import timedelta

from django.core.files import File as DjangoFile
from common.models import File
from notifications.utils import send_email
from crm.models import GoodsOrderModel
from common.models import TechnicalIsolatedCallsControlModel
from bkz3.settings import MEDIA_URL

FIELD_TYPE_MAPPER = {
    "ForeignKey": "ForeignKey",
    "CustomForeignKey": "ForeignKey",
    "CustomCurrentProfileField": "ForeignKey",
    "TreeForeignKey": "ForeignKey",
    "BooleanField": "BooleanField",
    "CustomBooleanField": "BooleanField",
    "CustomDateTimeField": "DateTimeField",
    "DateTimeField": "DateTimeField",
    "DateField": "DateField",
    "CustomDateField": "DateField",
    "IntegerField": "IntegerField",
    "CustomIntegerField": "IntegerField",
    "ManyToManyField": "ManyToManyField",
    "UUIDField": "UUIDField",
    "OneToOneField": "OneToOneField",
    "CustomOneToOneField": "OneToOneField",
    "CharField": "CharField",
    "CustomCharField": "CharField",
    "CustomFileField": "FileField",
    "FileField": "FileField",
    "CustomPositiveIntegerField": "PositiveIntegerField",
    "DecimalField": "DecimalField",
    "CustomDecimalField": "DecimalField",
    "TextField": "TextField",
    "FloatField": "FloatField",
}


EMPTY_1C_GUID = '00000000-0000-0000-0000-000000000000'


def load_1c_payload(request):
    request_data = getattr(request, 'data', None)
    if hasattr(request_data, 'get'):
        data_payload = request_data.get('data')
        if isinstance(data_payload, str):
            return deserialize_1c_json(data_payload)
        return request_data

    if isinstance(request_data, list):
        return request_data

    return deserialize_1c_json(request.body.decode('utf-8-sig'))


def deserialize_1c_json(raw_value):
    if isinstance(raw_value, (dict, list)):
        return raw_value

    if raw_value is None:
        return {}

    raw_value = raw_value.strip()
    if not raw_value:
        return {}

    start_positions = [pos for pos in (raw_value.find('{'), raw_value.find('[')) if pos != -1]
    if start_positions:
        raw_value = raw_value[min(start_positions):]

    raw_value = raw_value.replace('muachuille', ';')
    raw_value = raw_value.replace('huyachuille', '&')
    return json.loads(raw_value)


def normalize_1c_value(value):
    if value == EMPTY_1C_GUID:
        return None

    if isinstance(value, list):
        return [normalize_1c_value(item) for item in value]

    if isinstance(value, dict):
        return {key: normalize_1c_value(item) for key, item in value.items()}

    return value


def get_model_field(model_cls, field_name):
    try:
        return model_cls._meta.get_field(field_name)
    except FieldDoesNotExist:
        if field_name.endswith('_id'):
            return model_cls._meta.get_field(field_name[:-3])
        raise


def extract_many_to_many_ids(value):
    value = normalize_1c_value(value)
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError('Для many-to-many ожидается список значений.')

    result = []
    for item in value:
        if isinstance(item, dict):
            if 'id' in item:
                result.append(item['id'])
            elif 'uid' in item:
                result.append(item['uid'])
            else:
                raise ValueError('Не найден ключ id или uid в элементе many-to-many.')
        else:
            result.append(item)

    return [normalize_1c_value(item) for item in result]


def get_model_structure_to_integration(model):
    """Функция парсинга класса структуры модели"""
    full_structure = dict()
    main_model = model
    model_has_parents = True
    models_structure_list = list()
    while model_has_parents:
        model_fields = model._meta.fields + model._meta.many_to_many
        structure = dict()
        model_ct = ContentType.objects.get_for_model(model)
        structure['model'] = f'{model_ct.app_label}.{model_ct.model}'
        structure['fields'] = dict()

        for field in model_fields:
            if field.model == model:
                field_structure = dict()
                fields_data_type = FIELD_TYPE_MAPPER[field.__class__.__name__]
                field_structure['type'] = fields_data_type
                field_structure['blank'] = field.blank
                field_structure['null'] = field.null
                if field.is_relation:
                    field_structure['related_model'] = field.related_model._meta.label_lower
                if field.attname == 'ct_id':
                    field_structure['default_value'] = ContentType.objects.get_for_model(main_model).id

                if field.attname == 'id':
                    structure['pk'] = field_structure
                else:
                    structure['fields'][field.attname] = field_structure
        models_structure_list.append(structure)
        try:
            model = list(model._meta.parents.keys())[0]
        except:
            model_has_parents = False
    full_structure['1c_model_name'] = main_model.get_1c_model_name()
    full_structure['models_structure'] = models_structure_list
    full_structure['models_structure'].reverse()
    return full_structure


def generate_password():
    chars = "ABCDEFGHIJKLMNPQRSTUVWXYZ1234567890"
    value = "".join(random.choice(chars) for _ in range(8))
    return value


from bkz3.settings import GLOBAL_FRONT_SETTINGS
from bkz3.settings import FRONTEND_URL


def set_random_password_and_send_email(user):
    rand_pass = generate_password()
    user.set_password(rand_pass)
    user.password_generated = True
    user.save()
    context = dict()
    context['password'] = rand_pass
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    context['company_name'] = COMPANY_NAME
    context['email'] = user.email
    context['fio'] = f"{user.last_name} {user.first_name}"
    context['frontend_url'] = FRONTEND_URL
    context['contractor'] = user.profile.contractormodel_set.filter(is_active=True).last().name
    context['support_email'] = SUPPORT_EMAIL
    notification = EmailNotificationModel.objects.create(template='send_new_random_password',
                                                         subject='Ваш новый пароль',
                                                         context=context)
    recepient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                               recipient=user.email)
    send_email(notification.id)
    # async_task(send_email, notification.id)
    return user


def send_pay_file_email(order_id):
    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    order = GoodsOrderModel.objects.get(id=order_id)
    context['frontend_url'] = FRONTEND_URL
    if order.number_1c:
        context['order_number'] = order.number_1c
    else:
        context['order_number'] = '000000'
    notification = EmailNotificationModel.objects.create(template='send_order_pay_file',
                                                         subject=F'Счет на оплату готов! Заказ {order.number_1c}',
                                                         context=context)
    recepient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                               recipient=order.author.user.email)
    attachemnts = EmailNotificationAttachmentModel.objects.create(email_notification=notification,
                                                                  path=F'{MEDIA_URL}{order.pay_file.upload.name}')
    # send_email.delay(notification.id)
    send_email(notification.id)
    # async_task(send_email, notification.id)


def changed_pay_file_email(order_id):
    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    order = GoodsOrderModel.objects.get(id=order_id)
    context['frontend_url'] = FRONTEND_URL
    if order.number_1c:
        context['order_number'] = order.number_1c
    else:
        context['order_number'] = '000000'
    notification = EmailNotificationModel.objects.create(template='pay_file_changed',
                                                         subject=F'Счет на оплату был изменен! Заказ {order.number_1c}',
                                                         context=context)
    recepient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                               recipient=order.author.user.email)
    attachemnts = EmailNotificationAttachmentModel.objects.create(email_notification=notification,
                                                                  path=order.pay_file.upload.url)
    # send_email.delay(notification.id)
    send_email(notification.id)


def send_order_from_1c_file_email(order_id):
    context = dict()
    context['logo'] = GLOBAL_FRONT_SETTINGS['header_setting']['logo']
    order = GoodsOrderModel.objects.get(id=order_id)
    context['frontend_url'] = FRONTEND_URL
    if order.number_1c:
        context['order_number'] = order.number_1c
    else:
        context['order_number'] = '000000'
    notification = EmailNotificationModel.objects.create(template='send_order_form_file',
                                                         subject='Печатная форма заказа готова!',
                                                         context=context)
    recepient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                               recipient=order.author.user.email)
    attachemnts = EmailNotificationAttachmentModel.objects.create(email_notification=notification,
                                                                  path=order.order_form.upload.url)
    # send_email.delay(notification.id)
    send_email(notification.id)
    # async_task(send_email, notification.id)


def get_file_from_base64(base64_str):
    ready_bytes = b64decode(base64_str)
    file = io.BytesIO(ready_bytes)
    return file


def set_isolated_funk_is_start(control_obj):
    control_obj.is_started = True
    control_obj.date_started = timezone.now()
    control_obj.save()


def set_isolated_funk_is_end(control_obj):
    control_obj.is_started = False
    control_obj.date_started = None
    control_obj.save()


def get_remnants_from_1c():
    from common.catalogs.models import GoodsRemnantModel, GoodsModel, WarehouseModel
    # Делаем запись в техническую модель о начале выполнения вызываемой извне функции
    funk_name = "get_remnants"
    control_obj, created = TechnicalIsolatedCallsControlModel.objects.get_or_create(name=funk_name)
    set_isolated_funk_is_start(control_obj)

    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/remnants'
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    auth = {"Authorization": 'Basic ' + token}
    r = requests
    resp = r.get(url=url,
                 headers=auth)
    if resp.status_code == 200:
        data = json.loads(resp.text)
        # with transaction.atomic():
        #     GoodsRemnantModel.objects.all().delete()
        with transaction.atomic():
            GoodsRemnantModel.objects.all().delete()
            for remnant in data:
                if GoodsModel.objects.filter(id=remnant['goods_id']).exists() and \
                        WarehouseModel.objects.filter(id=remnant['warehouse_id']).exists():
                    GoodsRemnantModel.objects.create(**remnant)

            # ready_to_create = [GoodsRemnantModel(**vals) for vals in data]
            # GoodsRemnantModel.objects.bulk_create(ready_to_create)
    set_isolated_funk_is_end(control_obj)
    return 'ok'


def send_offer_to_1c(serialized_data, operation_type):
    """operation_type
    0 = Расчитать цены
    20 = Сформировать КП
    40 = Сформировать заказ
    """
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/order'
    url = F"{EXPORT_1C_DATA_URL}{address_path}?type={operation_type}"
    r = requests
    resp = r.post(url=url,
                  json=serialized_data, headers={"Authorization": 'Basic ' + token})
    data = None
    status = resp.status_code
    data = resp.text
    if resp.status_code == 200:
        data = resp.text

        if 'data' in data:
            data = data
    return data, status


def send_contractor_to_1c(serialized_data):
    """
    Отправка данных нового клиента в 1С
    """
    if EXPORT_1C_DATA_TOKEN and EXPORT_1C_DATA_URL:
        token = EXPORT_1C_DATA_TOKEN
        address_path = 'hs/order/client'
        url = f"{EXPORT_1C_DATA_URL}{address_path}"
        r = requests
        resp = r.post(url=url,
                      json=serialized_data,
                      headers={"Authorization": 'Basic ' + token})
        data = resp.text
        status = resp.status_code
    else:
        data = 'Ошыбка отправки данных'
        status = 400

    return data, status


def send_update_order_to_1c(serialized_data, operation_type):
    """Отправка запроса на изменение заказа."""
    token = EXPORT_1C_DATA_TOKEN
    address_path = f'hs/order/change_order/{serialized_data.get("id")}'
    url = f"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.put(url=url, json=serialized_data, headers={"Authorization": 'Basic ' + token})
    status = resp.status_code
    data = resp.text
    return data, status


def send_split_order_by_warehouses(serialized_data):
    token = EXPORT_1C_DATA_TOKEN
    address_path = f'hs/order/split_by_warehouses/'
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.post(url=url,
                  json=serialized_data, headers={"Authorization": 'Basic ' + token})
    data = None
    status = resp.status_code
    data = resp.text
    if resp.status_code == 200:
        data = resp.text

        if 'data' in data:
            data = data
    return data, status


def send_cash_payment_to_1c(order_id, data, user):
    """Отправка запроса на оплату заказа наличными."""
    token = EXPORT_1C_DATA_TOKEN
    address_path = f"hs/order/cash_payment/{order_id}"
    url = f"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    data['author'] = str(user.pk)
    resp = r.post(url=url, json=data, headers={"Authorization": 'Basic ' + token})
    resp_status = resp.status_code
    resp_data = resp.text
    return resp_data, resp_status


def send_calculate_must_paid_to_1c(order_id, data):
    """Отправка запроса на рассчет суммы к оплате заказа"""
    token = EXPORT_1C_DATA_TOKEN
    address_path = f'hs/order/calculate_must_paid/{order_id}'
    url = f"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.post(url=url, json=data, headers={"Authorization": 'Basic ' + token})
    status = resp.status_code
    data = resp.text
    return data, status


def send_purchase_prices_to_1c(order_id, data):
    """Отправка запроса на установку закупочной цены товара в табчасти заказа."""
    token = EXPORT_1C_DATA_TOKEN
    address_path = f'hs/order/set_purchase_prices/{order_id}'
    url = f"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.post(url=url, json=data, headers={"Authorization": 'basic' + token})
    status = resp.status_code
    data = resp.text
    return data, status

def get_commercial_offer_file_from_1c(order_id):
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/get_kp_file'
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})

    data = None
    status = resp.status_code
    if resp.status_code == 200:
        data = resp.content

    return data, status


def get_invoice_file_from_1c(order_id):
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/get_kp_file?id=' + str(order_id)
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})

    data = None
    status = resp.status_code
    if resp.status_code == 200:
        data = resp.content

    return data, status


def get_pay_file_from_1c(order_id):
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/get_pay_file?id=' + str(order_id)
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})

    data = None
    status = resp.status_code
    status_1c_code = ""
    back_1c_status_str = ""
    file_base64 = b""
    file_extension = 'zip'

    if resp.status_code == 200:
        file_base64 = resp.content
        # loaded_data = json.loads(resp.content)
        # # status_code = 0 Заказ еще не готов
        # # status_code = 1 Заказ готов (веренм файл)
        status_1c_code = resp.headers['status_code']

        back_1c_status_str = "Документ обрабатывается"
        if 'file_extension' in resp.headers and not resp.headers['file_extension'] == '':
            file_extension = resp.headers['file_extension']
        if status_1c_code == "1":
            file_base64 = resp.content

    return file_base64, status, status_1c_code, back_1c_status_str, file_extension


def get_sale_file_from_1c(order_id):
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/doc_sale/' + str(order_id)
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})

    data = None
    status = resp.status_code
    status_1c_code = ""
    back_1c_status_str = ""
    file_base64 = b""
    file_extension = 'zip'

    if resp.status_code == 200:
        file_base64 = resp.content
        # loaded_data = json.loads(resp.content)
        # # status_code = 0 Заказ еще не готов
        # # status_code = 1 Заказ готов (веренм файл)
        status_1c_code = resp.headers['status_code']

        back_1c_status_str = "Документ обрабатывается"
        if 'file_extension' in resp.headers and not resp.headers['file_extension'] == '':
            file_extension = resp.headers['file_extension']
        if status_1c_code == "1":
            file_base64 = resp.content

    return file_base64, status, status_1c_code, back_1c_status_str, file_extension


def update_file_from_1c(file_code):
    file_base64, file_format, status, status_1c_code = get_file_for_update_from_1c(file_code)
    if status_1c_code == '1':
        ready_bytes = io.BytesIO(file_base64)
        file_obj = File.objects.get(code=file_code)
        ready_file_2 = DjangoFile(ready_bytes, name=file_obj.name.split('.')[0] + file_format)
        file_obj.upload = ready_file_2
        file_obj.save()


def get_file_for_update_from_1c(file_code: str):
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/get_new_file?' + file_code
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})
    status = resp.status_code
    status_1c_code = ""
    file_format = ""

    file_base64 = b""
    if resp.status_code == 200:
        file_base64 = resp.content
        status_1c_code = resp.headers['status_code']
        if status_1c_code == "1":
            file_base64 = resp.content
            file_format = resp.headers['format']

    return file_base64, file_format, status, status_1c_code


def get_order_form_from_1c(order_id):
    token = EXPORT_1C_DATA_TOKEN
    address_path = 'hs/order/get_order_file?id=' + str(order_id)
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})

    data = None
    status = resp.status_code
    status_1c_code = ""
    back_1c_status_str = ""
    file_base64 = b""
    if resp.status_code == 200:
        file_base64 = resp.content
        # loaded_data = json.loads(resp.content)
        # # status_code = 0 Заказ еще не готов
        # # status_code = 1 Заказ готов (веренм файл)
        status_1c_code = resp.headers['status_code']
        back_1c_status_str = "Документ обрабатывается"
        if status_1c_code == "1":
            file_base64 = resp.content

    return file_base64, status, status_1c_code, back_1c_status_str


def get_zip_file_and_save(file_base64, order_id, file_name=None, file_extension='zip'):
    ready_file_2 = io.BytesIO(file_base64)
    if not file_name:
        file_name = str(order_id)
    ready_file = DjangoFile(ready_file_2, name=F'{file_name}.{file_extension}')
    file_obj = File.objects.create(upload=ready_file)
    return file_obj


def get_personal_file_from_1c(code, file_name, profile_id, date_begin, date_end, contractor, member, contract):
    token = EXPORT_1C_DATA_TOKEN
    address_path = F'hs/order/get_personal_file?code={code}&profile={profile_id}&date_begin={date_begin}&date_end={date_end}&contractor={contractor}&member={member}&contract={contract}'
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})
    if resp.status_code == 200:
        status_1c_code = resp.headers['status_code']
        if status_1c_code == "1":
            file_base64 = resp.content
            file_format = resp.headers['format']
            ready_bytes = io.BytesIO(file_base64)
            ready_file_2 = DjangoFile(ready_bytes, name=file_name + file_format)
            return ready_file_2, True, file_format
    return '', False, ''


def check_start_isolated_funk(funk_name):
    control_obj, created = TechnicalIsolatedCallsControlModel.objects.get_or_create(name=funk_name)
    now = timezone.now()
    if control_obj.date_started:
        time_check = now > control_obj.date_started + timedelta(minutes=5)
    else:
        time_check = False
    can_start = False
    if not control_obj.is_started or time_check:
        can_start = True
    return can_start


def get_contract_file_from_1c(contact_id, contract_name):
    token = EXPORT_1C_DATA_TOKEN
    address_path = F'hs/order/get_contract_act?id={contact_id}'
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    r = requests
    resp = r.get(url=url,
                 headers={"Authorization": 'Basic ' + token})
    if resp.status_code == 200:
        status_1c_code = resp.headers['status_code']
        if status_1c_code == "1":
            file_base64 = resp.content
            file_format = resp.headers['format']
            ready_bytes = io.BytesIO(file_base64)
            file_name = f'Акт сверки {contract_name}'
            ready_file_2 = DjangoFile(ready_bytes, name=file_name + file_format)
            return ready_file_2, True

    return '', False


def send_order_files_to_1c(order_id, attachments):
    token = EXPORT_1C_DATA_TOKEN
    address_path = F'hs/order/files?order={order_id}'
    url = F"{EXPORT_1C_DATA_URL}{address_path}"
    files = File.objects.filter(id__in=attachments)
    files_dict = {}
    for file in files:
        upload = file.upload
        name = file.name
        with upload.open():
            files_dict[name] = base64.b64encode(upload.read())
    r = requests
    resp = r.post(url=url,
                  headers={"Authorization": 'Basic ' + token},
                  files=files_dict
                  )


def send_update_goods_price_to_1c(serialized_data):
    # TODO пока заглушка
    # token = EXPORT_1C_DATA_TOKEN
    # address_path = f'hs/goods/update_price/'
    # url = f"{EXPORT_1C_DATA_URL}{address_path}"
    # r = requests
    # resp = r.post(url=url,
    #               headers={"authorization": 'Basic ' + token},
    #               json=serialized_data,
    #               )
    # status = resp.status_code
    # data = resp.text
    # if resp.status_code == 200:
    #     data = resp.text
    #
    #     if 'data' in data:
    #         data = data
    data = serialized_data
    status = 200
    return data, status
