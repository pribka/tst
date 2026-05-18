from datetime import timedelta
import os
import json
import time
import uuid
import zipfile
from uuid import UUID
from enum import Enum
from urllib.parse import quote
from datetime import datetime
import pytz

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist, FieldError, ObjectDoesNotExist, ValidationError
from django.db.models import ManyToOneRel, Case, When, Value, IntegerField
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.html import strip_tags
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder

from rest_framework import exceptions as drf_exceptions
from rest_framework.exceptions import PermissionDenied

from haystack.query import SearchQuerySet

from bkz3.settings import BACKEND_URL, TOKEN_URV, HAYSTACK_CONNECTIONS, ZIPFILES_ROOT, MEDIA_URL, ZIP_FILE_SUFFIX, \
    ZIPFILES_EXPIRE, TIME_ZONE, USE_ACCESS_GROUPS, SOCKETIO_SYSTEM_CHANNEL
from es_search.utils import universal_search

try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None


from app_info.models import AppInfo, CustomRoutesModel

from contractor_permissions.models import AccessGroupModel, AppSectionModel

from . import models, defaults
from .redis import socketio_redis
import re


def html_description_to_plain(html_str):
    """Убирает HTML-теги, сохраняя переносы строк (</p>, <br> и т.п. → \\n)."""
    if not html_str:
        return ''
    s = re.sub(r'</p>|</div>|</tr>|</li>|<br\s*/?>', '\n', html_str, flags=re.I)
    return re.sub(r'\n\s*\n+', '\n', strip_tags(s)).strip()


def get_datetime_param(request, param_name):
    """
    Извлекает параметр даты/времени (например, start=2026-01-13T00:00:00.000+03:00) из request.query_params
    и исправляет проблему с декодированием URL: знак + декодируется как пробел.
    """
    value = request.query_params.get(param_name)
    if value:
        # Заменяем пробел перед часовым поясом (формат HH:MM или HH:MM:SS) на +
        value = re.sub(r'\s(\d{2}:\d{2}(:\d{2}(\.\d+)?)?)$', r'+\1', value)
    return value


def _es_escape(s: str) -> str:
    # Экраним Lucene-символы, но НЕ трогаем * (мы сами добавляем)
    # + - && || ! ( ) { } [ ] ^ " ~ ? : \ /
    return re.sub(r'([+\-!(){}\[\]^"~?:\\\/])', r'\\\1', s)

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def is_protected_field(filter_key, model):
    """Проверяет, является ли ключ фильтра защищенным полем.
    Проверяет каждую часть пути в соответствующей модели цепочки связей.
    """
    from django.core.exceptions import FieldDoesNotExist
    
    parts = filter_key.split('__')
    current_model = model
    remaining_parts = parts
    
    # Проверяем путь по частям, переходя по связям
    for i in range(len(parts)):
        if not remaining_parts:
            break
            
        # Проверяем защищенные поля текущей модели для оставшейся части пути
        try:
            protected_fields = current_model.get_protected_fields()
        except AttributeError:
            protected_fields = []
        
        remaining_path = '__'.join(remaining_parts)
        for protected_field in protected_fields:
            if remaining_path == protected_field or remaining_path.startswith(protected_field + '__'):
                return True
        
        # Если это не последняя часть, переходим к связанной модели
        if i < len(parts) - 1:
            field_name = parts[i]
            try:
                field = current_model._meta.get_field(field_name)
                if hasattr(field, 'related_model'):
                    current_model = field.related_model
                    remaining_parts = parts[i+1:]  # Оставшаяся часть пути
                else:
                    break  # Не связь, дальше не идем
            except FieldDoesNotExist:
                break
    
    return False


def get_filter_queryset(request, model, queryset, not_filter=tuple()):
    from .fields import FakeField
    
    if request.method == 'POST':
        query_params = request.data
    else:
        try:
            query_params = request.query_params
        except AttributeError:
            query_params = request.GET
    not_filter = list(not_filter)
    
    if 'filters' in list(query_params.keys()):
        try:
            filters_dict = json.loads(query_params.get('filters'))
        except (json.JSONDecodeError, TypeError):
            # TypeError возникает, когда get-параметр filters пришел из api/v1/reports/, и по нему здесь фильтровать не надо.
            # Тогда он имеет формат списка [{'field': 'project', 'comparison_type': '=', 'value': '10e2ac92-da11-11ef-bfc8-4216f3de51df'}]
            filters_dict = dict()
        
        # Удаляем защищенные поля из filters_dict перед фильтрацией
        filters_dict = {key: value for key, value in filters_dict.items() 
                       if not is_protected_field(key, model)}
        
        if 'name__icontains' in filters_dict:
            try:
                #   filters_dict['ORR_counter_id'] = int(filters_dict['name__icontains'])
                filters_dict['ORR_counter'] = (filters_dict['name__icontains'])
            except:
                pass
            filters_dict['ORR_operator__user__last_name__icontains'] = filters_dict['name__icontains']

        queryset = filter_queryset_from_get_param(filters_dict, queryset)

        try:
            filters_dict.pop('ORR_counter')
        #  filters_dict.pop('ORR_counter_id')
        except:
            pass

        try:
            filters_dict.pop('ORR_operator__user__last_name__icontains')
        except:
            pass

        if filters_dict:
            not_filter = not_filter + [key for key, value in filters_dict.items()]
    try:
        filter_store = models.FiltersStore.objects.get(author=request.user.profile,
                                                       model=model.get_label(),
                                                       page_name=query_params.get('page_name', '')
                                                       )
    except models.FiltersStore.DoesNotExist:
        filter_store = None
    filter_lookup = dict()
    exclude_lookup = dict()
    fake_filter_fields = []
    fake_exclude_fields = []
    ordering_fields = []
    if filter_store is not None:
        filter_fields = filter_store.filters.get('values', dict())
        ordering_fields = filter_store.filters.get('ordering', list())
        if isinstance(filter_fields, dict):
            for key, value in filter_fields.items():
                if not value.get('active'):
                    continue
                if key in not_filter:
                    continue
                # Пропускаем защищенные поля
                if is_protected_field(key, model):
                    continue
                try:
                    field = model._meta.get_field(key)
                except FieldDoesNotExist:
                    try:
                        field = model._meta.get_field(key.replace('__exclude', ''))
                    except FieldDoesNotExist:
                        #  TODO добавить рекурсивный алгоритм.
                        try:
                            field = model._meta.get_field(key.split('__')[0])
                        except FieldDoesNotExist:
                            if isinstance(getattr(model, key, None), FakeField):
                                fake_filter_fields.append({"key": key, "value": value.get('values', dict())})
                            if key.endswith('__exclude') and isinstance(
                                    getattr(model, key.replace('__exclude', ''), None), FakeField):
                                fake_exclude_fields.append(
                                    {"key": key.replace('__exclude', ''), "value": value.get('values', dict())})
                            continue
                prefix = ''
                if isinstance(field, ManyToOneRel):
                    try:
                        field = field.related_model._meta.get_field(key.split('__')[1])
                    except FieldDoesNotExist:
                        try:
                            field = model._meta.get_field(key.replace('__exclude', ''))
                        except FieldDoesNotExist:
                            continue
                    prefix = key.split('__')[0] + '__'
                    key = key.split('__')[1]
                if field is not None:
                    field_lookup = field.filter_lookup
                    if field_lookup:
                        for key_lookup, value_lookup in value.get('values').items():
                            if key_lookup == 'value' and (value_lookup is None or value_lookup == [None]):
                                filter_lookup[prefix + key.replace('__exclude', '') + '__isnull'] = True
                            else:
                                if value_lookup is None:
                                    continue
                                if not key.endswith('__exclude'):
                                    filter_lookup[prefix + key + field_lookup.get(key_lookup)] = value_lookup
                                else:
                                    exclude_lookup[prefix + key.replace('__exclude', '')
                                                   + field_lookup.get(key_lookup)] = value_lookup
    if filter_lookup:
        try:
            queryset = queryset.filter(**filter_lookup)
        except ValueError:
            pass
    for each in fake_filter_fields:
        queryset = getattr(model, each['key']).to_filter(queryset, each['value'])
    if exclude_lookup:
        try:
            queryset = queryset.exclude(**exclude_lookup)
        except ValueError:
            pass
    for each in fake_exclude_fields:
        queryset = getattr(model, each['key']).to_exclude(queryset, each['value'])

    text = None
    if filter_store:
        text = filter_store.filters.get('search')
    if not text:
        text = query_params.get('search')

    if text and model.search_input():
        if len(text) >= 3:
            queryset = filter_by_search(text, model, queryset)
    queryset = order_queryset(model, queryset, ordering_fields)
    return queryset


def filter_by_search(text, model, queryset):
    if len(text) >= 3:
        search_result = get_search_result(model, text)  # sr = search_result
        # Извлекаем ID из словарей
        search_result_ids = [item['id'] for item in search_result]
        if not search_result_ids:
            search_result_ids.append(
                '00000000-0000-0000-0000-000000000000')  # парни, не убирайте его. Если массив окажется пустым, то там далее при укладке во временную таблицу будет косяк. Хотя бы один в массиве должен быть
        queryset = queryset.filter(pk__in=search_result_ids)

        # Создаем preserved_order для всех результатов
        # Результаты из search_result получают позиции по релевантности
        # Остальные результаты получают большое значение и идут в конец
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(search_result_ids)],
            default=Value(len(search_result_ids) * 1000),
            output_field=IntegerField()
        )
        # Сразу сортируем по релевантности вместо создания аннотации
        queryset = queryset.order_by(preserved_order)
        return queryset


def has_active_search_query(request, model):
    """
    Определяет, активен ли поисковый запрос (из параметров запроса или сохраненных фильтров)
    для текущей страницы.
    """
    if request.method == 'POST':
        query_params = request.data
    else:
        try:
            query_params = request.query_params
        except AttributeError:
            query_params = request.GET

    search_value = query_params.get('search')
    if isinstance(search_value, str) and len(search_value.strip()) >= 3:
        return True

    try:
        filter_store = models.FiltersStore.objects.get(
            author=request.user.profile,
            model=model.get_label(),
            page_name=query_params.get('page_name', '')
        )
    except models.FiltersStore.DoesNotExist:
        return False

    text = filter_store.filters.get('search')
    return isinstance(text, str) and len(text.strip()) >= 3


def get_search_result(model, text: str, limit: int = 300) -> list:
    """
    Поиск по модели. Возвращает список словарей {'id', 'score'} найденных объектов.
    """
    # Модели, в поиске которых используем ElasticSearch DSL, а не Haystack
    model_label = model._meta.label
    ES_SEARCH_MODELS = ('users.ProfileModel', 'processes.WorkflowRequestModel')
    if model_label in ES_SEARCH_MODELS:
        result = universal_search(model=model_label, search=text)
        if 'error' in result:
            return []
        return result

    """
    1. text_exact — строгое совпадение
    2. text_exact — префикс (*)    
    3. fuzzy — допускаем до 2 ошибок
        Возвращает список словарей {'id', 'score'}.
    """
    q = (text or "").strip()
    if not q:
        return []

    sqs = SearchQuerySet().models(model)

    if len(q) >= 3:
        # 1. строгое совпадение.
        # НЕ ИСПОЛЬЗУЕМ, ПОТОМУ ЧТО ПОД ТОЧНОЕ СОВПАДЕНИЕ МОГУТ ПОПАСТЬ ОБЪЕКТЫ, К КОТОРЫМ У НАС НЕТ ДОСТУПА
        # И ПРИ ДАЛЬШЕЙШЕЙ ФИЛЬТРАЦИИ ПО ПРАВАМ ПОЛУЧИМ ПУСТОЙ QUERYSET
        # results = sqs.filter(text_exact__exact=q)[:limit]
        # if results:
        #     return [{'id': str(result.pk), 'score': result.score} for result in results]
        # 2. префикс по text
        prefix = _es_escape(q)
        results = sqs.raw_search(f"text:{prefix}*")[:limit]
        if results:
            return [{'id': str(result.pk), 'score': result.score} for result in results]
        # 3. fuzzy (очепятки)
        terms = [t for t in q.split() if t]
        if terms:
            fuzzy = " ".join(f"{_es_escape(t)}~2" for t in terms)
            results = sqs.raw_search(fuzzy)[:limit]
            if results:
                return [{'id': str(result.pk), 'score': result.score} for result in results]
    return []


def filter_queryset_by_search_score(qs, search_result: list, score_threshold_ratio: float = 0.5):
    """
    Фильтрует queryset по результатам поиска с учетом релевантности (score).
    
    Алгоритм:
    1. Фильтрует queryset по ID из search_result
    2. Определяет максимальный score среди оставшихся после фильтрации записей
    3. Отфильтровывает записи с score ниже порога (score_threshold_ratio от максимального)
    4. Сортирует результаты по порядку из исходного search_result
    """
    if not search_result:
        return qs.none()
    
    search_result_ids = [item['id'] for item in search_result]
    
    # Сначала фильтруем queryset, чтобы узнать, какие pk остались после фильтрации
    qs = qs.filter(pk__in=search_result_ids)
    
    # Получаем список pk, которые остались после фильтрации
    remaining_pks = list(qs.values_list('pk', flat=True))
    
    if not remaining_pks:
        return qs.none()
    
    # Создаем словарь {id: score} для быстрого доступа (id в search_result - строки)
    score_map = {item['id']: item['score'] for item in search_result}
    
    # Находим максимальный score среди оставшихся pk
    remaining_scores = [score_map[str(pk)] for pk in remaining_pks]
    max_score = max(remaining_scores)
    
    # Фильтруем по порогу от максимального score
    score_threshold = max_score * score_threshold_ratio
    filtered_pks = [
        pk for pk in remaining_pks 
        if score_map[str(pk)] >= score_threshold
    ]
    
    # Создаем preserved_order с учетом отфильтрованных результатов
    # Сохраняем порядок из исходного search_result
    id_to_position = {item['id']: idx for idx, item in enumerate(search_result)}
    filtered_pks_sorted = sorted(filtered_pks, key=lambda pk: id_to_position.get(str(pk), float('inf')))
    
    preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(filtered_pks_sorted)])
    qs = qs.filter(pk__in=filtered_pks_sorted).order_by(preserved_order)
    return qs



def filter_queryset_from_get_param(filters_dict, queryset):
    """Берёт параметр filters из реквеста и фильтрует по нему кверисет."""
    if not filters_dict:
        return queryset
    try:
        lookup = Q()
        for each in filters_dict:
            d = {}
            if each[:4] == 'ORR_':
                d[each[4:]] = filters_dict[each]
                lookup |= Q(**d)
            else:
                d[each] = filters_dict[each]
                lookup &= Q(**d)

        queryset = queryset.filter(lookup).distinct()
    except FieldError:
        pass
    return queryset


def order_queryset_from_get_param(request, model, queryset):
    field_keys = get_field_keys(request, model)
    if field_keys:
        try:
            queryset = queryset.order_by(*field_keys)
        except FieldError:
            pass
    return queryset


def order_queryset(model, queryset, ordering_fields):
    if ordering_fields:
        try:
            queryset = queryset.order_by(*get_order_fields(ordering_fields, model))
        except FieldError:
            pass
    return queryset



def get_field_keys(request, model):
    try:
        query_params = request.query_params
    except AttributeError:
        query_params = request.GET
    ordering_fields = query_params.get('ordering')
    field_keys = []
    if ordering_fields:
        ordering_fields = ordering_fields.split(',')
        field_keys = get_order_fields(ordering_fields, model)
    return field_keys


def get_order_fields(ordering_fields, model):
    from .fields import FakeField
    field_keys = []
    for field in ordering_fields:
        prefix = '-' if field.startswith('-') else ''
        try:
            field_keys = field_keys + [
                f"{field}__{each}" for each in getattr(
                    model, field.replace(prefix, '', 1)
                ).field.related_model.get_order_param()
            ]
        except AttributeError:
            if isinstance(getattr(model, field.replace(prefix, '', 1), None), FakeField):
                field_keys = field_keys + [getattr(model, field.replace(prefix, '', 1)).get_order_param()]
            else:
                field_keys = field_keys + [field]
    return field_keys


def choices_to_list_of_dict(choices):
    result = []
    for choice in choices:
        result.append({"id": choice[0], "code": choice[1]})
    return result


def get_fields_for_select(model):
    model_label = model._meta.label

    if model_label == 'users.CustomUser':
        result = ('id',)
    elif model_label == 'users.ProfileModel':
        result = ('id',
                  'first_name',
                  'last_name',
                  'middle_name',
                  )
    else:
        result = ('id',
                  'name',
                  'sort')

    return result


def set_attributes_from_name_decorator(fnk):
    """
    Декоратор для метода set_attributes_from_name
    Исаользуется в классах полей (fields.py)

    Parameters
    ----------
    fnk - function

    Returns
    -------

    """

    def wrapper(self, name):
        super_fnk = getattr(super(self.__class__, self), fnk.__name__)
        super_fnk(name)
        external_set_attributes_from_name(self)

    return wrapper


def external_set_attributes_from_name(instance):
    """
    Выполнить set_field для аттрибутов класса
    Вызывается в декораторе :56 set_attributes_from_name_decorator

    Parameters
    ----------
    instance - Екземпляр класса поля - class obj

    Returns
    -------
    """
    common_attrs = instance.default_values_to_front.keys()

    for attr in common_attrs:
        try:
            getattr(instance,
                    attr).set_field(instance)
        except:
            pass


def field_set_attributes(instance,
                         _locals):
    """
    Проверка знайчений и начначение атрибудтов для классов полей при инициализации
    изпользуется в fields.py

    Parameters
    ----------
    instance - Екземпляр класса поля - class obj
    _locals - Зачение locals() (для обращения к значением перемных по str) - {}

    Returns
    -------
    """
    default_values = instance.default_values_to_front
    for name, value in default_values.items():
        if _locals[name] is None:
            setattr(instance,
                    name,
                    value)
        else:
            setattr(instance,
                    name,
                    _locals[name])


test_samopal_data_for_front = {
    "tableInfo": {
        "table_columns": [
            {
                "headerName": "№",
                "field": "index_row",
                "cellRenderer": "IndexRow",
                "sortable": False,
                "width": 70
            },
            {
                "headerName": "Справочник",
                "field": "catalog",
                "sortable": True,
                "cellRenderer": "RelatedRow",
                "cellRendererParams": {
                    "interpretationField": "name"
                },
                "editable": True,
                "cellEditor": "WidgetSelect",
                "cellEditorParams": {
                    "name": "catalog",
                    "title": "Справочник",
                    "type": "WidgetSelect",
                    "toField": "code",
                    "toName": "string_view",
                    "key": "staff.MyCatalog",
                    "dataPath": "/app_info/select_list/?model=staff.MyCatalog",
                    "rulesConfig": [
                        {
                            "required": True,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        }
                    ],
                    "actions": {
                        "showAll": {
                            "tableKey": {
                                "name": "page_list_staff.MyCatalog",
                                "key": "staff.MyCatalog",
                                "widget": "Default"
                            },
                            "tablePath": ""
                        },
                        "createOptions": {
                            "key": "edit_staff.MyCatalog"
                        }
                    }
                }
            },
            {
                "headerName": "Сумма",
                "field": "amount",
                "sortable": True,
                "cellRenderer": "DecimalRow",
                "editable": True,
                "cellEditor": "WidgetDecimal",
                "cellEditorParams": {
                    "rulesConfig": [
                        {
                            "required": True,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        }
                    ],
                    "decimalLength": 3,
                    "minValue": "-1000000000000000000000",
                    "maxValue": "1000000000000000000000"
                }
            },
            {
                "headerName": "ок",
                "field": "is_ok",
                "sortable": True,
                "cellRenderer": "SwitchRow",
                "editable": True,
                "cellEditor": "WidgetSwitch",
                "cellEditorParams": {
                    "rulesConfig": [
                        {
                            "required": True,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        }
                    ],
                    "name": "is_ok",
                    "defaultCheck": True,
                    "type": "WidgetSwitch",
                    "title": "ок"
                }
            },
            {
                "headerName": "Some string",
                "field": "some_string",
                "sortable": True,
                "cellRenderer": "DefaultRow",
                "editable": True,
                "cellEditor": "WidgetString",
                "cellEditorParams": {
                    "rulesConfig": [
                        {
                            "required": True,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        },
                        {
                            "min": 0,
                            "max": 51,
                            "message": "Minimum 0 characters, maximum 51 characters",
                            "trigger": "change"
                        }
                    ]
                }
            },
            {
                "headerName": "Некая дата",
                "field": "some_date",
                "sortable": True,
                "cellRenderer": "DateTimeRow",
                "editable": True,
                "cellEditor": "WidgetDateTime",
                "cellEditorParams": {
                    "rulesConfig": [
                        {
                            "required": False,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        }
                    ],
                    "time": False,
                    "dateFormat": "DD-MM-YYYY",
                    "currentDate": False,
                    "placeholder": "__-__-____"
                }
            },
            {
                "headerName": "Некая датавремя",
                "field": "some_datetime",
                "sortable": True,
                "cellRenderer": "DateTimeRow",
                "editable": True,
                "cellEditor": "WidgetDateTime",
                "cellEditorParams": {
                    "rulesConfig": [
                        {
                            "required": False,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        }
                    ],
                    "time": True,
                    "dateFormat": "DD-MM-YYYY HH:mm",
                    "currentDate": True,
                    "placeholder": "__-__-____ __:__"
                }
            },
            {
                "headerName": "Некое целое",
                "field": "some_integer",
                "sortable": True,
                "cellRenderer": "IntegerRow",
                "cellEditor": "WidgetInteger",
                "cellEditorParams": {
                    "rulesConfig": [
                        {
                            "required": False,
                            "message": "Обязательно для заполнения",
                            "trigger": "change"
                        }
                    ]
                },
                "editable": True,
                "minValue": "0",
                "maxValue": "2147483647",
                "defaultValue": 0
            }
        ],
        "data_path": "/staff/mydocument/<id>/catalog/",
        "key": "staff.TPCatalog",
        "title": "Справочники",
        "update_condition": {
            "is_active": True
        },
        "edit_form": "edit_staff.TPCatalog",
        "context_menu": [
            {
                "action": "create",
                "class": "",
                "icon": "plus",
                "size": "default",
                "title": "Добавить",
                "type": "default",
                "widget": "Default",
                "disabled": False,
                "form": "edit_staff.TPCatalog"
            },
            {
                "action": "delete",
                "class": "",
                "icon": "",
                "size": "default",
                "title": "Удалить",
                "type": "default",
                "widget": "Default",
                "disabled": False
            },
            {
                "action": "copy",
                "class": "",
                "icon": "",
                "size": "default",
                "title": "Копировать",
                "type": "default",
                "widget": "Default",
                "disabled": False,
                "form": "edit_staff.TPCatalog"
            },
            {
                "action": "select_all",
                "class": "",
                "icon": "",
                "size": "default",
                "title": "Выделить все",
                "type": "default",
                "widget": "Default",
                "disabled": False
            }
        ],
        "pageConfig": {
            "showFilter": True,
            "headerButtons": [
                {
                    "action": "create",
                    "class": "",
                    "icon": "plus",
                    "size": "default",
                    "title": "Добавить",
                    "type": "default",
                    "widget": "Default",
                    "disabled": False,
                    "form": "edit_staff.TPCatalog"
                }
            ]
        },
        "tableWidget": "FlatTable"
    },
    "formInfo": {
        "name": "form_in_table2",
        "type": "form",
        "title": "",
        "showComment": False,
        "showAuthor": False,
        "i18n": None,
        "pageWidget": "Default",
        "navWidget": "NavForm",
        "fields": {
            "create": [
                "reason",
                "text"
            ],
            "update": [
                "reason",
                "text"
            ]
        },
        "fieldInfo": [
            {
                "class": "inline",
                "name": "reason",
                "title": "Причина",
                "fieldName": "",
                "type": "string",
                "rulesConfig": [
                    {
                        "required": False,
                        "message": "Обязательно для заполнения",
                        "trigger": "change"
                    },
                    {
                        "min": 0,
                        "max": 36,
                        "message": "Минимум 0 символов, максимум 36 символов",
                        "trigger": "change"
                    }
                ],
                "widgetConfig": {
                    "disabled": False,
                    "placeholder": "",
                    "size": "default",
                    "widget": "WidgetString"
                }
            },
            {
                "class": "inline",
                "name": "text",
                "title": "Текст",
                "fieldName": "",
                "type": "string",
                "rulesConfig": [
                    {
                        "required": False,
                        "message": "Обязательно для заполнения",
                        "trigger": "change"
                    },
                    {
                        "min": 0,
                        "max": 36,
                        "message": "Минимум 0 символов, максимум 36 символов",
                        "trigger": "change"
                    }
                ],
                "widgetConfig": {
                    "disabled": False,
                    "placeholder": "",
                    "size": "default",
                    "widget": "WidgetString"
                }
            }
        ],
        "pageConfig": {
            "headerButtons": [

            ]
        }
    },
    "filterInfo": ""

}


def check_request_from_urv(request):
    """
    Проверка запроса от УРВ. Если GET-параметр 't' (или POST-параметр) не равен TOKEN_URV, поднимает PermissionDenied.
    Ничего не возвращает. Процедуру необходимо вызывать в начале любого обработчика запроса для УРВ.
    """
    if request.method == 'GET':
        token = request.query_params.get('t', '')
    elif request.method in ['POST', 'PUT', 'PATCH']:
        token = request.data.get('t', '')
    else:
        token = ''
    if not TOKEN_URV == token:
        raise PermissionDenied()


def get_serialized_attachments(instance, filter_lookup=None):
    from common.serializers import AppFileSerializer
    qs = instance.attachments.all()
    if filter_lookup:
        qs = qs.filter(**filter_lookup)
    attachments = filter(lambda x: x.is_active, qs)
    s_data = AppFileSerializer(attachments, many=True).data
    if DOWNLOADER_PATH is not None:
        for each in s_data:
            parent_path = quote(f"?obj={instance.pk}&id={each.get('id')}&target=attachments")
            each['path'] = f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'
    return s_data


def profile_is_online(profile_id):
    status_data = socketio_redis.get(F"status:{profile_id}")
    if status_data:
        status_info = json.loads(status_data)
        return status_info['online']
    return False


def get_search_bool():
    search_bool = True
    if HAYSTACK_CONNECTIONS['default'].get(
            'ENGINE') == 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine':
        search_bool = 'true'
    return search_bool


class FilesFrom(Enum):
    directly_files = 'directly_files'
    related_files = 'related_files'


def create_zip_file(user, folder: models.FolderModel, files_from: FilesFrom, instance=None):
    """
    Создает zip-файл из каталога во вложенных файлах.
    Файл собирается из каталога и всех подкаталогов этого каталога.
    Если folder пустой, создаёт zip-файл из всех вложений экземпляра.
    Параметры:
    instance: экземпляр объекта, которому принадлежат каталоги и вложенные файлы.
    folder: экземпляр каталога FolderModel, из которого необходимо создать zip-архив.
    """
    from .notifications import notify_about_zipfile_created
    already_working_key = get_already_working_key(user.pk, folder, files_from, instance=instance)
    cache.set(already_working_key, True, timeout=ZIPFILES_EXPIRE)
    if folder:
        # Если указан корневой каталог, сохраняем, начиная с этого каталога.
        root_folders = (folder,)
        root_files = tuple()
        folder_name = folder.name
    else:
        # Иначе собираем все корневые каталоги моих файлов. Не забываем про файлы в корне.
        if files_from == FilesFrom.directly_files:
            root_folders = models.FolderModel.objects.filter(parent__isnull=True, related_object=user)
            root_files = models.File.objects.filter(folder__isnull=True, author=user, is_active=True)
            folder_name = _('My files')
        elif files_from == FilesFrom.related_files:
            root_folders = instance.folders.filter(parent__isnull=True)
            root_files = [file.file for file in instance.files.filter(folder__isnull=True).distinct('file_id')]
            folder_name = getattr(instance, 'name', instance.__str__())
        else:
            return
    path = ''
    zf_name = f"{uuid.uuid4()}.zip"
    zf_path = os.path.join(ZIPFILES_ROOT, zf_name)
    with zipfile.ZipFile(
        zf_path,
        mode='a',
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        # Добавляем в архив корневые файлы.
        write_files(zf, root_files, path)
        # Рекурсивно добавляем в архив подкаталоги.
        for each in root_folders:
            add_folder_to_zip_file(each, path, zf, files_from)
    notify_about_zipfile_created(
        recipients=(user.pk,),
        url=f"{BACKEND_URL}{MEDIA_URL}{ZIP_FILE_SUFFIX}/{zf_name}",
        folder_name=folder_name,
        file_size=os.path.getsize(zf_path)
    )
    cache.delete(already_working_key)


def add_folder_to_zip_file(current_folder: models.FolderModel,
                           path: str,
                           zf: zipfile.ZipFile,
                           files_from: FilesFrom):
    """
    Рекурсивная процедура, которая добавляет каталоги и файлы в zip-файл.
    Параметры:
    current_folder - текущий каталог для добавления в zip-файл. Экземпляр FolderModel.
    path - текущий путь до каталога в файловой структуре zip-файла.
    zf - zip-файл, в который необходимо добавить каталог и его содержимое. Экземпляр ZipFile.
    files_from - откуда берем файлы. directly_files - Мои файлы, related_files - аттачи.
    Каталог добавляется в zip-файл, даже если он пустой.
    """
    path = os.path.join(path, current_folder.name)
    if files_from == FilesFrom.directly_files:
        files = current_folder.directly_files.filter(is_active=True)
    elif files_from == FilesFrom.related_files:
        files = [file.file for file in current_folder.related_files.select_related('file').all().distinct('file_id')]
    else:
        return
    write_files(zf, files, path)
    children = current_folder.get_children()
    if not files and not children:
        # Добавляем каталог, даже если он пустой.
        zip_info = zipfile.ZipInfo(os.path.join(path, ''))
        zf.writestr(zip_info, "")
    for each in children:
        add_folder_to_zip_file(each, path, zf, files_from)


def write_files(zf, files, path):
    completed_file_names = []
    for file in files:
        file_name = file.full_name
        if file_name in completed_file_names:
            fixed_file_name = f"{file.name}({len(list(filter(lambda x: x == file_name, completed_file_names)))}){f'.{file.extension}' if file.extension else ''}"
        else:
            fixed_file_name = file_name
        try:
            zf.write(file.upload.path, arcname=os.path.join(path, fixed_file_name))
        except FileNotFoundError:
            continue
        completed_file_names.append(file_name)


def get_already_working_key(user_id, folder, files_from: FilesFrom, instance=None) -> str:
    if files_from == FilesFrom.directly_files:
        return f"{user_id}__{getattr(folder, 'pk', 'root')}"
    elif files_from == FilesFrom.related_files:
        return f"{user_id}__{instance.pk}__{getattr(folder, 'pk', 'root')}"


def check_chat_attachments(request) -> bool:
    try:
        from bpms.chat.models import ChatModel, MessageModel
    except ImportError:
        return False
    chat_uid = request.query_params.get('chat_uid', '')
    message_uid = request.query_params.get('message_uid', '')
    if not chat_uid or not message_uid:
        return False
    file_id = request.query_params.get('id')
    if not file_id:
        file_id = request.query_params.get('file_id')
    try:
        chat = ChatModel.objects.get(chat_uid=chat_uid)
    except (ChatModel.DoesNotExist, ValidationError):
        return False
    if not chat.get_detail_permission(request):
        user = request.user.profile
        return check_message_forwarding_attachment(chat, message_uid, file_id, user)
    message_from_cache = socketio_redis.hget(f"messages:{chat_uid}", message_uid)
    if message_from_cache:
        message_dict = json.loads(message_from_cache)
        attachments = message_dict.get('attachments', [])
        if attachments:
            for attach in attachments:
                if attach.get('id') == file_id:
                    return True
        else:
            return False
    else:
        try:
            message = chat.messages.get(message_uid=message_uid)
        except (ObjectDoesNotExist, ValidationError):
            return False
        return message.attachments.filter(pk=file_id, is_active=True).exists()


def check_message_forwarding_attachment(chat, message_uid, file_id, user) -> bool:
    try:
        from bpms.chat.models import MessageModel, MemberModel
    except ImportError:
        return False
    try:
        message = MessageModel.objects.get(message_uid=message_uid)
    except (ValidationError, ObjectDoesNotExist):
        return False
    if not message.chat == chat:
        return False
    if not message.attachments.filter(pk=file_id).exists():
        return False
    forwarded_chats = set(
        message.forwarded_messages.filter(
            is_deleted=False,
        ).values_list('chat', flat=True)
    )
    if forwarded_chats:
        return MemberModel.objects.filter(is_active=True, chat_id__in=forwarded_chats, user=user).exists()
    else:
        return False


def get_model(request):
    model_app_label = request.query_params.get('model', None)
    if not model_app_label:
        return None
    try:
        app_name, model_name = model_app_label.split('.')
    except ValueError:
        return None
    try:
        model = apps.get_model(app_name, model_name)
    except LookupError:
        return None
    return model


def is_mobile_app(request) -> bool:
    return request.META.get('HTTP_APP_TYPE', '') == 'mobile-app'


def validate_settings(settings) -> bool:
    return (
        isinstance(settings, dict) and
        ('columns' in settings) and
        ('page_size' in settings) and
        ('ordering' in settings)
    )


def get_cache_key_name(page_name, profile) -> str:
    return f'{page_name}_{profile.id}'


def convert_to_local_timezone(value: datetime, timezone_code: str = None):
    if value is None:
        return None
    timezone_value = timezone_code or TIME_ZONE
    if timezone.is_naive(value):
        value = pytz.utc.localize(value)
    return value.astimezone(pytz.timezone(timezone_value))


def get_my_access_groups(profile, contractor_id=None, apply_tariffs=True):
    """Возвращает queryset с группами доступа, в которых состоит профиль пользователя profile."""
    from contractor_permissions.utils import get_tariffs_id_by_contractors
    if not contractor_id:
        user_organizations = profile.my_organizations
    else:
        user_organizations = (contractor_id,)
    if apply_tariffs:
        tariff_section_codes = get_tariff_section_codes(profile)
        access_groups = AccessGroupModel.objects.filter(
            is_active=True,
            app_section_roles__app_section_id__in=tariff_section_codes,
            members__user_id=profile.pk,
            members__contractor_id__in=user_organizations
            ).exclude(app_section_roles__role_id='banned').distinct()
    else:
        # Без учета окончания тарифов. Нужно для вычисления has_admin_access_group в CustomUserDetailSerializer
        access_groups = AccessGroupModel.objects.filter(
            is_active=True,
            members__user_id=profile.pk,
            members__contractor_id__in=user_organizations
        ).distinct()
    return access_groups


def get_tariff_section_codes(profile) -> list:
    """Возвращает список code разделов (AppSectionModel), доступных ОРГАНИЗАЦИЯМ пользователя. С кэшированием"""
    SENTINEL = object() # на случай, если ключа в кэше нет вообще
    cache_key = f'tariff_section_codes_{str(profile.pk)}'
    app_sections_codes = cache.get(cache_key, default=SENTINEL)
    if app_sections_codes is SENTINEL:
        from contractor_permissions.utils import get_tariffs_id_by_contractors
        tariffs = get_tariffs_id_by_contractors(profile.my_organizations)
        if not tariffs:
            app_sections_codes = list()
        else:
            app_sections_codes = set(AppSectionModel.objects.filter(tariffs__in=tariffs).values_list('code', flat=True).distinct())
            app_sections_codes = list(app_sections_codes)
            cache.set(cache_key, app_sections_codes, timeout=timedelta(hours=1).total_seconds())
    return app_sections_codes


def get_available_section_codes(profile) -> set:
    """Возвращает список code разделов, доступных ПОЛЬЗОВАТЕЛЮ.
    Складывается из разделов, доступных организациям пользователя, и групп доступа, куда добавлен пользователь."""
    tariff_section_codes = get_tariff_section_codes(profile)
    app_sections_codes = set(
        AccessGroupModel.objects.filter(
            is_active=True,
            app_section_roles__app_section_id__in=tariff_section_codes,
            members__user_id=profile.pk,
        ).exclude(
            app_section_roles__role_id='banned',
        ).values_list('app_section_roles__app_section_id', flat=True).distinct()
    )
    from help_desk.models import HelpDeskTicketMembersModel
    if HelpDeskTicketMembersModel.objects.filter(user=profile, ticket__is_active=True).exists():
        app_sections_codes.add('help_desk')
    return app_sections_codes


def get_available_app_section_roles_through(profile):
    tariff_section_codes = get_tariff_section_codes(profile)
    app_sections_codes = AccessGroupModel.objects.filter(
        is_active=True,
        app_section_roles__app_section_id__in=tariff_section_codes,
        members__user_id=profile.pk,
    ).exclude(
        app_section_roles__role_id='banned',
    ).values_list('app_section_roles', flat=True).distinct()
    return set(app_sections_codes)


def get_alt_routes(request,):
    user = request.user.profile
    # try:
    #     route_groups = AppInfo.objects.get(code='route_groups').metadata
    # except ObjectDoesNotExist:
    #     route_groups = dict()
    if use_access_groups(user.pk):
        section_codes_set = get_available_section_codes(user)
        app_sections = AppSectionModel.objects.filter(
            code__in=section_codes_set,
            is_active=True,
        ).order_by('sort', 'name',)
        data = dict()
        route_view = request.query_params.get('view', '')
        if route_view == 'desktop':
            for app_section in app_sections:
                data.update(app_section.routes)
        else:
            for app_section in app_sections:
                data.update(app_section.mobile_routes)

        # if 'deals' not in data:
        #     data['deals'] = dict(defaults.DEFAULT_ROUTES['deals'])
        #     if route_view != 'desktop':
        #         data['deals']['isShowMobile'] = True
        # if isinstance(data.get('deals'), dict):
        #     data['deals']['title'] = _('Сделки / контракты')

        # data.update(route_groups)
        if user.is_support:
            # data['moderation-group'] = {
            #     "icon": "fi-rr-chart-pie-alt",
            #     "title": "Модерация",
            #     "type": "group",
            #     "descOrder": 28,
            #     "isShow": True
            # }
            data['moderation'] = {
                "icon": "fi-rr-comment-alt-middle",
                "title": "Модерация",
                "isShow": True,
                "isFooter": False,
                "descOrder": 160,
                "hideMobile": False,
                "pageWidget": "Moderation",
                "mobileOrder": 28,
                "isShowMobile": True
            }
            # data['moderation-list'] = {
            #     "icon": "fi-rr-comment-alt-middle",
            #     "type": "link",
            #     "group": "moderation-group",
            #     "title": "Модерация",
            #     "isShow": True,
            #     "descOrder": 1
            # }
            # data['moderation-new-clients'] = {
            #     "icon": "fi-rr-users-alt",
            #     "type": "link",
            #     "group": "moderation-group",
            #     "title": "Новые пользователи",
            #     "isShow": True,
            #     "descOrder": 1
            # }

        custom_route = CustomRoutesModel.objects.filter(is_active=True, author=user).first()
        if custom_route:
            custom_data = custom_route.metadata
            if custom_data:
                for key, value in custom_data.items():
                    try:
                        data[key].update(value)
                    except KeyError:
                        pass
        return data
    else:
        try:
            data = AppInfo.objects.get(code='alter_front_routes', is_active=True).metadata
        except AppInfo.DoesNotExist:
            data = defaults.DEFAULT_ROUTES
        if 'deals' not in data:
            data['deals'] = defaults.DEFAULT_ROUTES['deals']
        if isinstance(data.get('deals'), dict):
            data['deals']['title'] = _('Сделки / контракты')
        user = request.user.profile
        custom_route = CustomRoutesModel.objects.filter(is_active=True, author=user).first()
        if not user.is_support:
            data.pop('moderation', None)
        if not custom_route:
            return data
        custom_data = custom_route.metadata
        for key, value in custom_data.items():
            try:
                data[key].update(value)
            except KeyError:
                pass
        # data.update(route_groups)
        return data


def get_logo_url(filename: str):
    return f"{BACKEND_URL}{MEDIA_URL}avatars/{filename}"


def set_tabular_parts(serializer, instance):
    initial_data = serializer.initial_data
    tabular_parts = serializer.Meta.model.get_tabular_parts()
    if isinstance(tabular_parts, dict):
        for tp_attr, tp_model in tabular_parts.items():
            tp_objects = initial_data.get(tp_attr)
            if tp_objects:
                tp_list_serializer = tp_model.get_serializer_class(action='list')
                #  Создание записей табчасти
                create_list = tp_objects.get('add')
                create_list_result = []
                if create_list:
                    tp_serializer = tp_model.get_serializer_class(action='create')
                    for each in create_list:
                        uid = each.pop('uid')
                        each['owner'] = instance.pk
                        tp_serialized = tp_serializer(data=each)
                        tp_serialized.is_valid(raise_exception=True)
                        created_object = tp_serialized.save()
                        serialized_created_object = tp_list_serializer(instance=created_object).data
                        serialized_created_object['uid'] = uid
                        create_list_result.append(serialized_created_object)

                edit_list = tp_objects.get('edit')
                edit_list_result = []
                if edit_list:
                    tp_serializer = tp_model.get_serializer_class(action='update')
                    for each in edit_list:
                        try:
                            edited_object = tp_model.objects.get(owner_id=instance.pk, pk=each.get('id'))
                        except ObjectDoesNotExist:
                            raise drf_exceptions.ValidationError(f'Запись табличной части {each.get("id")} не найдена')
                        each['owner'] = instance.pk
                        tp_serialized = tp_serializer(instance=edited_object, data=each, partial=True)
                        tp_serialized.is_valid(raise_exception=True)
                        edited_object = tp_serialized.save()
                        serialized_edited_object = tp_list_serializer(instance=edited_object).data
                        edit_list_result.append(serialized_edited_object)
                delete_list = tp_objects.get('delete')
                delete_list_result = []
                if isinstance(delete_list, list):
                    tp_model.objects.filter(owner=instance, pk__in=delete_list).delete()
                    delete_list_result = delete_list
                serializer.context[tp_attr] = {
                    "add": create_list_result,
                    "edit": edit_list_result,
                    "delete": delete_list_result,
                }


def to_representation_tabular_parts(serializer, instance, data):
    for tp_attr, model in instance.get_tabular_parts().items():
        data[tp_attr] = serializer.context.get(tp_attr)
    if instance.has_characteristics_plan():
        poc_values = instance._meta.model.get_model_characteristics_subfields()
        for poc_value in poc_values:
            data[poc_value.full_field_code] = serializer.context.get(poc_value.full_field_code)
    return data


def use_access_groups(user_id=None) -> bool:
    if USE_ACCESS_GROUPS:
        return True
    return False
    #     if user_id:
    #         try:
    #             app_info = AppInfo.objects.get(is_active=True, code='use_access_groups')
    #         except AppInfo.DoesNotExist:
    #             return True
    #         users_id = app_info.metadata
    #         if not users_id:
    #             return True
    #         if str(user_id) in users_id:
    #             return True
    #     else:
    #         return True
    # else:
    #     return False


def is_uuid(obj):
    """Проверка того, что оъект является валидным uuid."""
    if isinstance(obj, uuid.UUID):
        return True
    if isinstance(obj, str):
        try:
            uuid.UUID(obj)
            return True
        except ValueError:
            return False
    return False


# Ключ в Redis: до какого timestamp (float) OLLAMA/task_klass не должен вызываться (пауза по запросу pribka@mail.ru).
TASK_KLASS_PAUSE_UNTIL_KEY = 'task_klass_pause_until'


def wait_if_paused():
    """Ждёт окончания паузы (ключ в Redis). В паузу не вызываем OLLAMA (task_klass и invoke_role_prompt gos24.kz)."""
    while True:
        pause_until_ts = cache.get(TASK_KLASS_PAUSE_UNTIL_KEY)
        if not pause_until_ts or time.time() >= pause_until_ts:
            break
        time.sleep(30)


def notification_set_is_read(comments_id: list, profile_id: str):
    from notifications.models import WebNotificationModel, WebNotificationRecipientModel
    total_notification_list = list()
    for comment_id in comments_id:
        notifications_id = list(
            WebNotificationModel.objects.filter(
                is_active=True,
                data__contains={'obj': {'id': comment_id}}
            ).values_list('pk', flat=True)
        )
        total_notification_list.append(notifications_id)
        if notifications_id:
            recipients = WebNotificationRecipientModel.objects.filter(
                notification_id__in=notifications_id,
                recipient_id=profile_id,
                is_read=False,
            )
            for each in recipients:
                each.is_read = True
                each.save()
    if total_notification_list:
        data = json.dumps(
            {
                "event": "notify",
                "data": {
                    "message": {
                        "event_type": "read_notifications",
                        "notifications": total_notification_list,
                    },
                    "recipients": [str(profile_id)],
                },
            },
            cls=DjangoJSONEncoder,
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_update_current_work(recipients_id,):
    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": {
                    "event_type": "update_current_work",
                    "current_work": 'update'
                },
                "recipients": recipients_id,
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
