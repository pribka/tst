from django.utils import timezone
from django.core import serializers
from django.core.exceptions import ValidationError, ObjectDoesNotExist, FieldDoesNotExist
from django.core.files import File as DjangoFile
from django.db import transaction, IntegrityError
from django.http import FileResponse
from django.db.models import Q
from django.apps import apps

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, exceptions as drf_exceptions
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.authentication import BasicAuthentication, SessionAuthentication

from django_q.tasks import async_task

from common.paginators import CustomPagination

from contractor_access_tokens.auth_classes import Contractor1CAccessTokenAuthentication
from contractor_access_tokens.permissions import Contractor1CAccessTokenPermission

from . import models, utils
from .permissions import Token1CPermission, URVTokenPermission
from .utils import get_model_structure_to_integration
from .utils import get_file_from_base64
from .utils import send_offer_to_1c
from .utils import check_start_isolated_funk
from .utils import update_file_from_1c
from .utils import get_personal_file_from_1c

from .cron import get_pay_file_for_order
from .cron import get_order_form_for_order
from .serializers import Profile1CDocumentsListSerializer
import json


class WriteObjectsFrom1CViewSet(ViewSet):
    authentication_classes = (Contractor1CAccessTokenAuthentication,)
    permission_classes = (Contractor1CAccessTokenPermission,)

    @staticmethod
    def _get_model_class(object_1c):
        model_cls = None

        if object_1c.model_ct_id:
            model_cls = object_1c.model_ct.model_class()

        if model_cls is None and object_1c.model:
            try:
                app_label, model_name = object_1c.model.split('.', 1)
                model_cls = apps.get_model(app_label, model_name)
            except (LookupError, ValueError):
                model_cls = None

        return model_cls

    @staticmethod
    def _get_exchange_map(object_1c):
        fields = object_1c.fields.all()
        if not fields:
            return {}
        return {item.field_1c: item.field_django for item in fields}

    @staticmethod
    def _prepare_item_list(items):
        if isinstance(items, list):
            return items
        if isinstance(items, dict):
            return [items]
        raise ValueError('Для объекта 1С ожидается список или словарь.')

    def _map_item(self, object_1c, item):
        if not isinstance(item, dict):
            raise ValueError('Элемент входящего обмена должен быть объектом JSON.')

        field_map = self._get_exchange_map(object_1c)
        if not field_map:
            return {key: utils.normalize_1c_value(value) for key, value in item.items()}

        mapped_item = {}
        for source_field, target_field in field_map.items():
            if source_field in item:
                mapped_item[target_field] = utils.normalize_1c_value(item[source_field])
        return mapped_item

    def _get_lookup_kwargs(self, model_cls, lookup_field, lookup_value):
        field = utils.get_model_field(model_cls, lookup_field)
        if field.is_relation and not field.many_to_many:
            return {field.attname: lookup_value}
        if lookup_field.endswith('_id'):
            return {lookup_field: lookup_value}
        return {field.name: lookup_value}

    def _apply_data_to_instance(self, instance, mapped_item, object_1c):
        many_to_many_values = {}

        for target_field, value in mapped_item.items():
            field = utils.get_model_field(instance.__class__, target_field)

            if field.many_to_many:
                many_to_many_values[field.name] = utils.extract_many_to_many_ids(value)
                continue

            if field.is_relation:
                object_1c_field = object_1c.fields.filter(field_django=field.name).first()
                if object_1c_field:
                    field_search = object_1c_field.field_search
                    fk_instance = field.related_model.objects.get(**{field_search: value})
                    setattr(instance, field.name, fk_instance)
                continue

            setattr(instance, field.name, value)

        # instance.exchange = True Признак, что запись пришла из 1С?

        instance.save()

        for field_name, value in many_to_many_values.items():
            getattr(instance, field_name).set(value)

        return instance

    def _save_item(self, object_1c, source, item):
        model_cls = self._get_model_class(object_1c)
        if model_cls is None:
            raise ValueError('Для правила обмена не найдена модель Django.')

        mapped_item = self._map_item(object_1c, item)

        lookup_value = mapped_item.get(object_1c.lookup_field)

        instance = None
        if lookup_value is not None:
            lookup_kwargs = self._get_lookup_kwargs(model_cls, object_1c.lookup_field, lookup_value)
            instance = model_cls.objects.filter(**lookup_kwargs).first()
        if instance and not object_1c.update_if_exist:
            return instance
        if instance is None:
            if lookup_value is not None and object_1c.lookup_field in ('id', 'pk'):
                instance = model_cls(id=lookup_value)
            elif object_1c.create_if_missing:
                instance = model_cls()
            else:
                raise ValueError('Запись для обновления не найдена, создание отключено.')
            organization_field = object_1c.organization_field
            if organization_field:
                setattr(instance, organization_field, source.contractor_id)
            if hasattr(instance, 'source'):
                instance.source = source
        instance = self._apply_data_to_instance(instance, mapped_item, object_1c)

        return instance

    def _set_is_active_item(self, object_1c, source, item):
        model_cls = self._get_model_class(object_1c)
        if model_cls is None:
            raise ValueError('Для правила обмена не найдена модель Django.')

        mapped_item = self._map_item(object_1c, item)
        organization_field = object_1c.organization_field
        if organization_field:
            mapped_item[organization_field] = str(source.contractor_id)
        lookup_value = mapped_item.get(object_1c.lookup_field)

        if lookup_value is None:
            raise ValueError(f'Ожидается ключ {object_1c.lookup_field}.')
        lookup_kwargs = self._get_lookup_kwargs(model_cls, object_1c.lookup_field, lookup_value)
        instance = model_cls.objects.filter(**lookup_kwargs).first()

        if instance is None:
            raise ValueError('Запись для удаления не найдена.')
        is_active = item.get('is_active', False)
        if not isinstance(is_active, bool):
            raise ValueError('is_active: ожидается булеан.')
        instance.is_active = is_active
        instance.save()
        return instance

    @action(methods=('post',), detail=False, url_path='write_objects')
    def post(self, request, *args, **kwargs):
        payload = utils.load_1c_payload(request)
        source = request.auth
        if not isinstance(payload, dict):
            ret = {'detail': 'Ожидался JSON-объект вида {"ИмяОбъекта": [{...}]}'}
            models.WriteLog.objects.create(
                source=source,
                payload=payload,
                ret=ret,
            )
            return Response(
                ret,
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload = {
            key: value for key, value in payload.items()
        }

        exchange_rules = models.Object1C.objects.filter(
            is_active=True,
        ).select_related('model_ct').prefetch_related('fields')
        exchange_by_name = {item.name_object_1c: item for item in exchange_rules}

        response_payload = {}

        for object_name, raw_items in payload.items():
            try:
                items = self._prepare_item_list(raw_items)
            except ValueError as exc:
                response_payload[object_name] = [{
                    'obmen_proizoshel_uspeshno': False,
                    'error': str(exc),
                }]
                continue

            object_1c = exchange_by_name.get(object_name)
            if object_1c is None:
                response_payload[object_name] = []
                for item in items:
                    response_item = item.copy() if isinstance(item, dict) else {'value': item}
                    response_item['obmen_proizoshel_uspeshno'] = False
                    response_item['error'] = 'Для объекта не настроено правило входящего обмена.'
                    response_payload[object_name].append(response_item)
                continue

            response_items = []
            for item in items:
                response_item = item.copy() if isinstance(item, dict) else {'value': item}
                try:
                    with transaction.atomic():
                        instance = self._save_item(object_1c, source, item)
                    response_item['obmen_proizoshel_uspeshno'] = True
                    response_item['id'] = str(instance.pk)
                except (FieldDoesNotExist, ValueError, ValidationError, IntegrityError) as exc:
                    response_item['obmen_proizoshel_uspeshno'] = False
                    response_item['error'] = str(exc)
                except Exception as exc:
                    response_item['obmen_proizoshel_uspeshno'] = False
                    response_item['error'] = str(exc)
                response_items.append(response_item)

            response_payload[object_name] = response_items
        models.WriteLog.objects.create(
            ret=response_payload,
            payload=payload,
            source=request.auth,
        )
        return Response(response_payload, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=False, url_path='set_is_active',)
    def set_is_active(self, request, *args, **kwargs):
        payload = utils.load_1c_payload(request)
        source = request.auth
        if not isinstance(payload, dict):
            ret = {'detail': 'Ожидался JSON-объект вида {"ИмяОбъекта": [{...}]}'}
            models.WriteLog.objects.create(
                source=source,
                payload=payload,
                ret=ret,
                action='set_is_active',
            )
            return Response(
                ret,
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload = {
            key: value for key, value in payload.items()
        }

        exchange_rules = models.Object1C.objects.filter(
            is_active=True,
            organization=source.contractor,
        ).select_related('model_ct').prefetch_related('fields')
        exchange_by_name = {item.name_object_1c: item for item in exchange_rules}

        response_payload = {}

        for object_name, raw_items in payload.items():
            try:
                items = self._prepare_item_list(raw_items)
            except ValueError as exc:
                response_payload[object_name] = [{
                    'obmen_proizoshel_uspeshno': False,
                    'error': str(exc),
                }]
                continue

            object_1c = exchange_by_name.get(object_name)
            if object_1c is None:
                response_payload[object_name] = []
                for item in items:
                    response_item = item.copy() if isinstance(item, dict) else {'value': item}
                    response_item['obmen_proizoshel_uspeshno'] = False
                    response_item['error'] = 'Для объекта не настроено правило входящего обмена.'
                    response_payload[object_name].append(response_item)
                continue

            response_items = []
            for item in items:
                response_item = item.copy() if isinstance(item, dict) else {'value': item}
                try:
                    with transaction.atomic():

                        instance = self._set_is_active_item(object_1c, source, item)
                    response_item['obmen_proizoshel_uspeshno'] = True
                    response_item['id'] = str(instance.pk)
                except (FieldDoesNotExist, ValueError, ValidationError, IntegrityError) as exc:
                    response_item['obmen_proizoshel_uspeshno'] = False
                    response_item['error'] = str(exc)
                except Exception as exc:
                    response_item['obmen_proizoshel_uspeshno'] = False
                    response_item['error'] = str(exc)
                response_items.append(response_item)

            response_payload[object_name] = response_items
        models.WriteLog.objects.create(
            ret=response_payload,
            payload=payload,
            source=request.auth,
            action='set_is_active',
        )
        return Response(response_payload, status=status.HTTP_200_OK)

    @action(
        methods=('post',),
        detail=False,
        url_path='objects_to_json',
        authentication_classes=(BasicAuthentication, SessionAuthentication,),
        permission_classes=(IsAuthenticated,)
    )
    def objects_to_json(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        data = request.data
        model_list = data.get('models')
        organization_id = data.get('organization')
        if not organization_id:
            raise drf_exceptions.ValidationError('organization_id required')

        qs = models.Object1C.objects.filter(
            is_active=True,
            organization_id=organization_id,
        ).order_by('model')
        if model_list:
            qs = qs.filter(model__in=model_list)
        qs = qs.values(
            'id',
            'name',
            'name_object_1c',
            'model',
            'is_related',
            'lookup_field',
            'organization_field',
            'create_if_missing',
        )
        resp = list()
        for each in qs:
            resp_item = each
            object_1c_fields = models.Object1CField.objects.filter(
                object_1c=each['id'],
            ).order_by('name').values(
                'name',
                'field_1c',
                'field_django',
                'field_search',
                'main_field',
                'is_binary_data',
            )
            resp_item['fields'] = object_1c_fields
            resp.append(resp_item)
        return Response(resp)

    @action(
        methods=('post',),
        detail=False,
        url_path='json_to_objects',
        authentication_classes=(BasicAuthentication, SessionAuthentication,),
        permission_classes=(IsAuthenticated,)
    )
    def json_to_objects(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        data = request.data
        organization_id = data.get('organization')
        if not organization_id:
            raise drf_exceptions.ValidationError('organization_id required.')
        objects_1c = data.get('objects_1c')
        with transaction.atomic():
            for object_1c in objects_1c:
                instance = models.Object1C()
                instance.organization_id = organization_id
                instance.name = object_1c['name']
                instance.name_object_1c = object_1c['name_object_1c']
                instance.model = object_1c['model']
                instance.is_related = object_1c['is_related']
                instance.lookup_field = object_1c['lookup_field']
                instance.organization_field = object_1c['organization_field']
                instance.create_if_missing = object_1c['create_if_missing']
                instance.save()
                object_1c_fields = object_1c['fields']
                for object_1c_field in object_1c_fields:
                    field_instance = models.Object1CField()
                    field_instance.object_1c = instance
                    field_instance.name = object_1c_field['name']
                    field_instance.field_1c = object_1c_field['field_1c']
                    field_instance.field_django = object_1c_field['field_django']
                    field_instance.field_search = object_1c_field['field_search']
                    field_instance.main_field = object_1c_field['main_field']
                    field_instance.is_binary_data = object_1c_field['is_binary_data']
                    field_instance.save()
        return Response('ok')


class ExternalImportData(APIView):
    authentication_classes = ()
    permission_classes = (Token1CPermission,)
    """Ендпоинт получения и записи данных из интеграции"""

    @staticmethod
    def check_model_in_whitelist(obj, ct_in_wl):
        """ Проверка перед записью есть ли модель в моделеях для обмена """
        if obj.object.__class__.__name__ == 'BaseModel':
            in_wl = obj.object.ct_id in ct_in_wl
        elif obj.object.__class__.__name__ == 'BaseCatalog':
            in_wl = True
        else:
            ct = models.ContentType.objects.get_for_model(obj.object)
            in_wl = ct.id in ct_in_wl
        return in_wl

    def post(self, request, *args, **kwargs):
        post_copy = request.POST.copy()
        json_string = post_copy.get('data')
        JSONSerializer = serializers.get_deserializer('json')
        objects_to_save = JSONSerializer(json_string)
        content_types_to_import = models.ModelToIntegrationModel.objects.filter(is_active=True).values_list(
            'model_ct_id', flat=True)
        error_list = list()
        with transaction.atomic():
            for obj in objects_to_save:
                if self.check_model_in_whitelist(obj, content_types_to_import):
                    try:
                        obj.object.before_save_by_exchange()
                        obj.save()
                        obj.object.after_save_by_exchange()
                    except Exception as e:
                        transaction.set_rollback(True)
                        error_list.append({"uid": obj.object.id,
                                           "model": obj.object.__class__.__name__,
                                           "exception": e.args})
                else:
                    transaction.set_rollback(True)
                    error_list.append({"uid": obj.object.id,
                                       "model": obj.object.__class__.__name__,
                                       "exception": "Модель не доступна для обмена!"})

        return Response({"error_list": error_list},
                        status=status.HTTP_200_OK)


class DeleteObjects(APIView):
    authentication_classes = ()
    permission_classes = (Token1CPermission,)

    def post(self, request, *args, **kwargs):
        data = request.POST
        delete_objects = json.loads(request.data['delete_objects'])
        wl_integration_models = models.ModelToIntegrationModel.objects.filter(is_active=True).values_list('model_ct',
                                                                                                          flat=True)
        objects_to_delete = models.BaseModel.objects.filter(id__in=delete_objects,
                                                            ct_id__in=wl_integration_models)
        error_list = list()
        for object_to_delete in objects_to_delete:
            try:
                object_to_delete.delete()
            except Exception as e:
                error_list.append({"uid": object_to_delete.id,
                                   "model": object_to_delete.ct.__class__.__name__,
                                   "exception": e.args})
        return Response(error_list,
                        status=status.HTTP_200_OK)


class ModelStructureToImportData(APIView):
    """Ендпоинт получения структуры моделей"""
    authentication_classes = ()
    permission_classes = (Token1CPermission,)

    def get(self, request, *args, **kwargs):
        model_label = request.GET.get('model', None)
        data = list()
        white_list_models = models.ModelToIntegrationModel.objects.filter(is_active=True).order_by('model_ct_id')

        if model_label:
            app_label, model_name = model_label.split('.')
            model_ct = models.ContentType.objects.get(app_label=app_label, model=model_name)
            white_list_models = white_list_models.filter(model_ct=model_ct)

        for model in white_list_models:
            model_cls = model.model_ct.model_class()
            data.append(get_model_structure_to_integration(model_cls))

        return Response(data,
                        status=status.HTTP_200_OK)


class SendWorkTypeView(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from bpms.tasks.models import TaskWorkTypeModel, TaskStatusTypeModel, TaskStatusModel, \
            TaskStatusTypeDependsModel, TaskTypeModel, TaskStatusWorkTypeConnectModel

        data = request.data.get('data')

        for item in data:
            id = item['id']
            name = item['name']
            try:
                type_of_work, created = TaskWorkTypeModel.objects.get_or_create(id=id, defaults={"name": name})
                type_of_work.name = name
                type_of_work.is_active = item['is_active']
                type_of_work.save()

            except Exception as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)

            task_type, created = TaskTypeModel.objects.get_or_create(code='interest',
                                                                     defaults={
                                                                         'name': "Интерес"
                                                                     })
            task_status, created = TaskStatusModel.objects.get_or_create(id=item['status_id'],
                                                                         defaults={
                                                                             'name': item['status_name']
                                                                         })
            task_status.name = item['status_name']
            task_status.save()

            connected = TaskStatusTypeModel.objects.filter(task_type=task_type,
                                                           task_status=task_status).first()
            if not connected:
                connected = TaskStatusTypeModel.objects.create(task_type=task_type,
                                                               task_status=task_status)

            connected.is_complete = item.get('status_is_complete', False)
            connected.is_open = item.get('status_is_open', False)
            connected.show_btn = item.get('status_show_btn', False)
            connected.is_active = item['is_active']
            connected.save()

            depend = TaskStatusTypeDependsModel.objects.filter(task_status_type=connected,
                                                               task_status=task_status).first()
            if not depend:
                depend = TaskStatusTypeDependsModel.objects.create(task_status=task_status,
                                                                   task_status_type=connected)
            work_connect, is_new = TaskStatusWorkTypeConnectModel.objects.get_or_create(status=task_status)
            work_connect.worktype.add(type_of_work)

        return Response(status=status.HTTP_200_OK)


class SendPriceTypes(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import PriceTypeModel
        data = request.data.get('data')
        for item in data:
            id = item['id']
            name = item['name']
            currency = item['currency']
            goods, created = PriceTypeModel.objects.get_or_create(id=id, defaults={"name": name,
                                                                                   "currency_id": currency,
                                                                                   })
            if not created:
                goods.name = name
                goods.currency_id = currency
                goods.save()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGoods(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import GoodsModel, GoodsCategoryModel
        data = request.data.get('data')
        for item in data:
            id = item['id']
            name = item['name']
            name_short = item['name_short']
            description = item['description']
            article_number = item['article_number']
            code = item['code']
            price_by_catalog = item['price_by_catalog']
            category = item['category']
            show_in_catalog = item.get('show_in_catalog', True)
            goods_type = item['goods_type']
            base_measure_unit_id = item.get('base_measure_unit_id', None)

            goods_default = dict()
            goods_default['name'] = name
            goods_default['description'] = description
            goods_default['code'] = code
            goods_default['show_in_catalog'] = show_in_catalog
            goods_default['goods_type_id'] = goods_type
            goods_default['name_short'] = name_short
            goods_default['price_by_catalog'] = price_by_catalog
            goods_default['article_number'] = article_number
            goods_default['base_measure_unit_id'] = base_measure_unit_id
            goods, created = GoodsModel.objects.get_or_create(id=id, defaults=goods_default)
            if not created:
                goods.base_measure_unit_id = base_measure_unit_id
                goods.name = name
                goods.description = description
                goods.code = code
                goods.name_short = name_short
                goods.price_by_catalog = price_by_catalog
                goods.goods_type_id = goods_type
                goods.article_number = article_number
                goods.show_in_catalog = show_in_catalog
                goods.save()
            if category != '00000000-0000-0000-0000-000000000000':
                cat = GoodsCategoryModel.objects.get_or_create(
                    id=category,
                    defaults={
                        'name': 'Category ' + category
                    }
                )
                goods.category.through.objects.get_or_create(goodscategorymodel_id=category, goodsmodel_id=goods.id)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGoodsPrices(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import GoodsPriceModel, PriceTypeModel, GoodsModel
        data = request.data.get('data')
        price_type_map = PriceTypeModel.objects.all().values('id', 'code')
        error_list = list()
        for item in data:
            id = item.get('id')
            goods = item.get('goods')
            price = item.get('price')
            price_type = item.get('price_type', 'default')
            goods_obj, goods_created = GoodsModel.objects.get_or_create(id=goods,
                                                                        defaults={"name": "NOT FOUND! НЕОПОЗНАННЫЙ ОБЪЕКТ",
                                                                                  "show_in_catalog": False})
            # try:
            goods_price, created = GoodsPriceModel.objects.get_or_create(id=id,
                                                                         defaults={
                                                                             "goods": goods_obj,
                                                                             "price_type_id": price_type,
                                                                             "price": price,
                                                                         })
            if price_type == 'default':
                goods_obj.price_by_catalog = price
                goods_obj.save()

            if not created:
                goods_price.goods = goods_obj
                goods_price.price_type_id = price_type
                goods_price.price = price
                goods_price.save()
            # except Exception as e:
            #     error_list.append({"id": item['id']})

        return Response({"status": "ok", "error_list": error_list}, status=status.HTTP_200_OK)


class SendTypeOfPayment(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import PaymentFormModel
        data = request.data.get('data')
        for item in data:
            id = item['id']
            name = item['name']
            required = item.get('required', False)
            type_of_payment, created = PaymentFormModel.objects.get_or_create(id=id, defaults={
                "name": name, "required": required,
            })
            if not created:
                type_of_payment.name = name
                type_of_payment.required = required
                type_of_payment.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendContract(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):

        from common.catalogs.models import ContractModel, ContractContractorModel, PriceTypeModel
        data = request.data.get('data')
        price_type_map = PriceTypeModel.objects.all().values('id', 'code')
        for item in data:
            id = item['id']
            name = item['name']
            # payment = item['payment']
            price_type = item['price_type']
            is_individual = item['is_individual']
            contractor = item.get('contractor', None)
            price_type_mapped = price_type_map.get(id=price_type)['code']
            contract, created = ContractModel.objects.get_or_create(id=id, defaults={"price_type_id": price_type_mapped,
                                                                                     # "payment_id": payment,
                                                                                     "is_individual": is_individual,
                                                                                     "name": name,
                                                                                     })

            if not created:
                contract.name = name
                contract.price_type_id = price_type_mapped
                # contract.payment_id = payment
                contract.is_individual = is_individual
                contract.save()
                # TODO нужна еще дата действия соглашения
            if contractor and is_individual:
                contract_relation, contract_relation_created = ContractContractorModel.objects.get_or_create(
                    contract=contract,
                    contractor_id=contractor
                )
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGoodsCategory(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import GoodsCategoryModel
        data = request.data.get('data')
        for item in data:
            id = item['id']
            name = item['name']
            parent = item['parent']
            if parent == '00000000-0000-0000-0000-000000000000':
                parent = None
            if parent:
                parent, parent_created = GoodsCategoryModel.objects.get_or_create(id=parent,
                                                                                  defaults={
                                                                                      "name": "НЕОПОЗНАНЫЙ ОБЪЕКТ"})
            category, created = GoodsCategoryModel.objects.get_or_create(id=id,
                                                                         defaults={"parent": parent, "name": name})
            if not created:
                category.name = name
                category.parent = parent
                category.save()
            # category.goods.set(goods)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendContractContractorRelation(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import ContractContractorModel
        data = request.data.get('data')
        for item in data:
            contract = item['contract']
            contractor = item['contractor']
            category, created = ContractContractorModel.objects.get_or_create(contract=contract, contractor=contractor)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGoodImages(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.models import File
        from gallery.models import GalleryModel
        from common.catalogs.models import GoodsModel
        data = request.data.get('data')
        for item in data:
            goods_id = item['goods']
            image_json = item['image']
            with transaction.atomic():
                b64 = image_json['base64']
                file_format = image_json['format']
                ready_file = get_file_from_base64(b64)
                file_obj = DjangoFile(ready_file, name=image_json['id'] + '.' + file_format)
                goods_image, image_created = File.objects.get_or_create(id=image_json['id'],
                                                                        defaults={"upload": file_obj})
                if not image_created:
                    goods_image.upload = file_obj
                    goods_image.save()
                goods, created_goods = GoodsModel.objects.get_or_create(id=goods_id,
                                                                        defaults={"name": "НЕОПОЗНАНЫЙ ОБЪЕКТ"})
                if goods_image:
                    gallery_image, created_gallery_obj = GalleryModel.objects.get_or_create(file=goods_image,
                                                                                            related_object=goods,
                                                                                            is_main=True)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendOrderTo1C(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from crm.models import GoodsOrderModel
        from crm.serializers import GoodsOrderModelDetailSerializer
        from crm.enums import OperationTypeEnum
        post_copy = request.data
        order_id = post_copy['order']
        order = GoodsOrderModel.objects.get(id=order_id)
        serialized_data = {"order": str(order.id)}
        # отправка данных в 1с
        request_1c_data, status_1c = send_offer_to_1c(serialized_data, operation_type=order.operation_type)

        # Для тестов пока не получаем данные с 1с
        if order.operation_type_id == OperationTypeEnum.offer.value:
            order.operation_type_id = OperationTypeEnum.purchase.value
            order.save()
        else:
            pass

        data_to_return = GoodsOrderModelDetailSerializer(order).data

        return Response(data=data_to_return, status=status.HTTP_200_OK)


class SendWarehouse(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import WarehouseModel, DeliveryPointModel
        data = request.data.get('data')
        with transaction.atomic():
            for item in data:
                warehouse_id = item['id']
                warehouse_name = item['name']
                warehouse_address = item['address']
                warehouse_sort = item.get('sort', 500)
                warehouse_connected_list = item.get('connected_warehouse', [])
                address_point = item.get('address_point')
                for connected_warehouse_name in warehouse_connected_list:
                    warehouse_name += F" + {connected_warehouse_name}"
                # warehouse_manager = item['manager']
                delivery_point = None
                if address_point:
                    try:
                        delivery_point = DeliveryPointModel.objects.create(**address_point)
                    except IntegrityError:
                        raise drf_exceptions.ValidationError(
                            f'Invalid address_point in warehouse {warehouse_id} {warehouse_name}.'
                        )
                try:
                    warehouse, created = WarehouseModel.objects.update_or_create(id=warehouse_id,
                                                                                 defaults={
                                                                                     "id": warehouse_id,
                                                                                     "name": warehouse_name,
                                                                                     "address": warehouse_address,
                                                                                     "sort": warehouse_sort,
                                                                                     'manager_id': item.get('manager',
                                                                                                            None),
                                                                                     "delivery_point": delivery_point,
                                                                                     # "manager_id": warehouse_manager
                                                                                 }
                                                                                 )
                except IntegrityError:
                    raise drf_exceptions.ValidationError(
                        f'Invalid warehouse {warehouse_id} {warehouse_name}.'
                    )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGoodsRemnant(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import GoodsRemnantModel
        data = request.data.get('data')
        for item in data:
            remnant_id = item['id']
            remnant_warehouse = item['warehouse']
            remnant_quantity = item['quantity']
            storage_type = item.get('storage_type', 'default')

            remnant_goods = item['goods']
            remnant, created = GoodsRemnantModel.objects.get_or_create(id=remnant_id,
                                                                       defaults={"warehouse_id": remnant_warehouse,
                                                                                 "quantity": remnant_quantity,
                                                                                 "goods": remnant_goods,
                                                                                 'storage_type': storage_type
                                                                                 })
            if not created:
                remnant.warehouse_id = remnant_warehouse
                remnant.quantity = remnant_quantity
                remnant.goods_id = remnant_goods
                remnant.storage_type = storage_type
                remnant.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendContractorAddress(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from common.catalogs.models import DeliveryAddress
        data = request.data.get('data')
        for item in data:
            address_id = item['id']
            address_str = item['address']
            contractor_id = item['contractor']
            address, created = DeliveryAddress.objects.get_or_create(id=address_id, defaults={"address": address_str,
                                                                                              "contractor_id": contractor_id})
            if not created:
                address.address = address_str
                address.contractor_id = contractor_id
                address.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendTaskFiles(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from bpms.tasks.models import TaskModel
        from common.models import File
        data = request.data.get('data')
        for item in data:

            task_id = item['task']
            json_file = item['file']
            b64 = json_file['base64']
            file_format = json_file['format']
            file_id = json_file['id']

            task = TaskModel.objects.get(id=task_id)
            ready_bytes = get_file_from_base64(b64)
            ready_file_3 = DjangoFile(ready_bytes, name=file_id + '.' + file_format)
            task_file, image_created = File.objects.get_or_create(id=file_id,
                                                                  defaults={"upload": ready_file_3})
            if not image_created:
                task_file.upload = ready_file_3
                task_file.save()
            task.attachments.add(task_file)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendGoodsOrderExecuteStatuses(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from crm.models import GoodsOrderExecuteStatusModel
        data = request.data.get('data')
        for item in data:
            id = item['id']
            name = item['name']
            exec_status, created = GoodsOrderExecuteStatusModel.objects.get_or_create(id=id, defaults={"name": name})
            if not created:
                exec_status.name = name
                exec_status.save()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SendOrderPaymentStatus(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from crm.models import GoodsOrderModel
        data = request.data.get('data')
        with transaction.atomic():
            for each in data:
                order_id = each.get('id')
                try:
                    order = GoodsOrderModel.objects.get(pk=order_id, is_active=True)
                except GoodsOrderModel.DoesNotExist:
                    raise drf_exceptions.ValidationError(f"Order {order_id} not found.")
                payment_status = each.get('payment_status')
                if not payment_status:
                    raise drf_exceptions.ValidationError(f"Payment status for order {order_id} is empty.")
                order.payment_status_id = payment_status
                try:
                    order.save(update_fields=('payment_status_id',))
                except IntegrityError:
                    raise drf_exceptions.ValidationError(
                        f"Invalid payment status {payment_status} in order {order_id}: payment status not found."
                    )
                must_paid = each.get('must_paid')
                if must_paid is not None:
                    order.must_paid = must_paid
                    try:
                        order.save(update_fields=('must_paid',))
                    except IntegrityError:
                        raise drf_exceptions.ValidationError(f"Invalid must_paid in order {order_id}.")
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class UpdateOrderStatus(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from crm.models import GoodsOrderModel
        data = request.data.get('data')
        for order in data:
            order_id = order['id']
            new_status = order['status']
            order_obj = GoodsOrderModel.objects.get(id=order_id)
            order_obj.execute_status_id = new_status
            order_obj.save()
            # get_pay_file_for_order(order_id)
            # get_order_form_for_order(order_id)
            # async_task(get_order_form_for_order, order_id)
            async_task(get_pay_file_for_order, order_id)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class TestGetRemnants(APIView):
    # authentication_classes = ()
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        from .utils import get_remnants_from_1c
        if request.user.is_superuser:
            get_remnants_from_1c()
            return Response(status=200)
        return Response(status=403)


class IsolatedGetRemnants(APIView):
    # authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def get(self, request, *args, **kwargs):
        from .utils import get_remnants_from_1c
        funk_name = 'get_remnants'
        can_start = check_start_isolated_funk(funk_name)
        if can_start:
            get_remnants_from_1c()
        return Response({"status": "ok"}, status=200)


class IsolatedCheckOrderForm(APIView):
    # authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def get(self, request, *args, **kwargs):
        from .cron import check_order_find_order_form
        funk_name = 'check_order_form'
        can_start = check_start_isolated_funk(funk_name)
        if can_start:
            check_order_find_order_form()
        return Response({"status": "ok"}, status=200)


class IsolatedCheckOrderPayFile(APIView):
    # authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def get(self, request, *args, **kwargs):
        from .cron import check_order_find_pay_file

        funk_name = 'check_order_pay_file'
        can_start = check_start_isolated_funk(funk_name)
        if can_start:
            check_order_find_pay_file()

        return Response({"status": "ok"}, status=200)


class CustomUpdateFile(APIView):
    """
    Динамическое обновление файла
    """
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        data = request.data.get('data')
        for file_fom_1c in data:
            async_task(update_file_from_1c, file_fom_1c['code'])

        return Response({"status": "ok"},
                        status=status.HTTP_200_OK)


def update_file_from_1c_view(request):
    update_file_from_1c('remnants_xls')


class SendFileCodes(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        data = request.data.get('data')
        doc_model = models.Profile1CDocumentsModel
        for i in data:
            profile_id = i.get('profile_id')
            is_active = i.get('is_active', True)
            document_name = i.get('document_name')
            document_code = i.get('document_code')
            doc, created = doc_model.objects.get_or_create(code=document_code, profile_id=profile_id,
                                                           defaults={"name": document_name})
            if not created:
                doc.name = document_name
                doc.is_active = is_active
                doc.save()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


# Create your views here.


class SendTaskScenarion(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from bpms.tasks.models import TaskScenarioModel
        data = request.data.get('data')
        for scenario in data:
            scenario_id = scenario.get('id')
            scenario_name = scenario.get('name')
            scenario_obj, created = TaskScenarioModel.objects.get_or_create(id=scenario_id,
                                                                            defaults={'name': scenario_name})
            if not created:
                scenario_obj.name = scenario_name
                scenario_obj.save()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class GetMyDoc1cList(generics.ListAPIView):
    queryset = models.Profile1CDocumentsModel.objects.filter(is_active=True)
    serializer_class = Profile1CDocumentsListSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(Q(profile=self.request.user.profile) | Q(profile__isnull=True))


from bpms.tasks.models import TaskLoadingGoodsModel
from rest_framework.serializers import ModelSerializer


class C1TaskLoadingGoodsModelSerializer(ModelSerializer):
    class Meta:
        fields = '__all__'
        model = TaskLoadingGoodsModel


class GetLoadingDocs(APIView):
    queryset = TaskLoadingGoodsModel.objects.filter(is_active=True)
    serializer_class = C1TaskLoadingGoodsModelSerializer
    pagination_class = CustomPagination
    permission_classes = (URVTokenPermission,)

    def get(self, request):
        queryset = self.queryset.filter(number__gte=self.request.query_params['number'])
        serializer = C1TaskLoadingGoodsModelSerializer(queryset, many=True)
        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            instance = TaskLoadingGoodsModel.objects.get(pk=pk)
        except TaskLoadingGoodsModel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        # data.pop('id')
        # data.pop('number')
        # data.pop('author')
        # data.pop('ct')
        # data.pop('attachments')
        serializer = C1TaskLoadingGoodsModelSerializer(instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetMyFileFrom1C(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        code = request.query_params.get('code')
        date_begin = request.query_params.get('date_begin')
        date_end = request.query_params.get('date_end')
        contractor = request.query_params.get('contractor')
        member = request.query_params.get('member')
        contract = request.query_params.get('contract')
        profile = request.user.profile
        my_doc = models.Profile1CDocumentsModel.objects.filter(code=code,
                                                               is_active=True)
        my_doc = my_doc.filter(Q(profile=self.request.user.profile) | Q(profile__isnull=True))
        if my_doc.exists():
            my_doc_obj = my_doc.last()
            file_name = my_doc_obj.name
            file, status_1c, file_format = get_personal_file_from_1c(code, file_name,
                                                                     str(profile.id), date_begin, date_end, contractor,
                                                                     member, contract)
            if status_1c:
                resp = FileResponse(file)
                resp.headers['File-format'] = file_format
                return resp

        return Response(status=status.HTTP_403_FORBIDDEN)


class SendCashPayment(APIView):
    authentication_classes = ()
    permission_classes = (URVTokenPermission,)

    def post(self, request, *args, **kwargs):
        from crm.models import CashPayTypeModel
        from rest_framework import exceptions as drf_exceptions
        data = request.data.get('data')
        if not isinstance(data, list):
            raise drf_exceptions.ValidationError('Data must be a list.')
        with transaction.atomic():
            for each in data:
                instance, created = CashPayTypeModel.objects.update_or_create(
                    pk=each['id'], defaults={
                        "name": each['name'],
                        "id": each["id"],
                        "is_group": each.get("is_group", False),
                        "parent_id": each.get("parent", None),
                    }
                )
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class GetPayFileFrom1C(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        pk = request.query_params.get('id')
        from . import cron
        cron.get_pay_file_for_order(pk)
        return Response('ok')


class SetIsActive(APIView):
    permission_classes = (
        URVTokenPermission,
    )

    def post(self, request, *args, **kwargs):
        data = request.data.get('data')
        if not isinstance(data, list):
            raise drf_exceptions.ValidationError('Data is not a list.')
        with transaction.atomic():
            for each in data:
                if not isinstance(each, dict):
                    raise drf_exceptions.ValidationError(f'invalid data {each}: data must be dict.')
                if 'id' not in each or 'is_active' not in each:
                    raise drf_exceptions.ValidationError(f'Invalid data {each}.')
                instance_id = each.get('id')
                instance_is_active = each.get('is_active')
                try:
                    instance = models.BaseModel.objects.super_get(pk=instance_id)
                except (ValidationError, models.BaseModel.DoesNotExist):
                    continue
                if instance_is_active:
                    deleted_at = None
                else:
                    deleted_at = timezone.now()
                instance.is_active = instance_is_active
                instance.deleted_at = deleted_at
                try:
                    instance.save(update_fields=('is_active', 'deleted_at'))
                except (ValidationError, IntegrityError) as ex:
                    raise drf_exceptions.ValidationError(f'Invalid data {each}: {ex.args}.')
        return Response('ok')
