# 🔹 Стандартная библиотека
import copy
from datetime import timedelta

# 🔹 Django
from django.core.cache import cache
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# 🔹 Django REST framework

# 🔹 Третьи библиотеки
from modeltranslation.translator import translator, NotRegistered
from modeltranslation.utils import build_localized_fieldname
from mptt.models import TreeForeignKey

# 🔹 Локальные импорты
from common.fields import CustomForeignKey


def get_field_meta(field_path, model):
    """Принимает название поля (в том числе в формате 'manager_position__name__title') и исходную модель.
    Возвращает метаописание поля: model._meta.get_field(field_path) и его модель.
    Для вычисляемых полей отчёта (get_report_computed_fields_meta) с type=ForeignKey возвращает (None, related_model)."""
    parts = field_path.split("__")
    current_model = model
    for i, part in enumerate(parts):
        try:
            field = current_model._meta.get_field(part)
        except Exception:
            # Вычисляемое поле отчёта (например main_specialist) — не в _meta
            # Важно: вычисляемые поля могут быть вложенными (например customer_card__tags),
            # тогда текущая модель уже смещена в related_model.
            if hasattr(current_model, 'get_report_computed_fields_meta'):
                for meta in current_model.get_report_computed_fields_meta():
                    if meta.get('name') == part and meta.get('type') == 'ForeignKey' and meta.get('related_model'):
                        rm = meta['related_model']
                        if '.' in rm:
                            app_label, model_name = rm.split('.', 1)
                        else:
                            app_label = current_model._meta.app_label
                            model_name = rm
                        return (None, apps.get_model(app_label, model_name))
            return (None, None)

        if isinstance(field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField, TreeForeignKey)):
            current_model = field.related_model

        # Последний элемент
        if i == len(parts) - 1:
            return (field, current_model)


def get_report_field_type(model_class, field_path):
    """Возвращает строковый тип report-поля (модельного или computed)."""
    if not field_path or not model_class:
        return None

    model_field, resolved_model = get_field_meta(field_path, model_class)
    if model_field is not None:
        return model_field.get_internal_type()

    def _get_computed_type(target_model, target_name):
        if not target_model or not hasattr(target_model, "get_report_computed_fields_meta"):
            return None
        for field_meta in target_model.get_report_computed_fields_meta():
            if field_meta.get("name") == target_name:
                return field_meta.get("type")
        return None

    if "__" in field_path:
        relation_path, leaf_name = field_path.rsplit("__", 1)
        _, relation_model = get_field_meta(relation_path, model_class)
    else:
        leaf_name = field_path
        relation_model = None

    # Локальное computed-поле
    resolved_type = _get_computed_type(model_class, field_path)
    if resolved_type:
        return resolved_type

    # Computed-поле связанной модели
    resolved_type = _get_computed_type(relation_model, leaf_name)
    if resolved_type:
        return resolved_type

    # Fallback по модели, на которой завершился путь
    return _get_computed_type(resolved_model, leaf_name)


# Поля, которые исключаются у мета-описания ВСЕХ моделей, если exclude_fields=true.
META_EXCLUDE_FIELDS = [
    'id',
    # 'ct',
    # 'owner',
    'is_active',
    # 'created_at',
    'updated_at',
    'deleted_at',
    'name_predefined',
    'is_predefined',
    'is_folder',
    # 'parent',
    'lft',
    'rght',
    'tree_id',
    'level',
    'metadata',
    'viewers',
    'sort',
    'attachments',
    'telegram_connect_token',
    'password',
]


def find_related_models(model):
    """Возвращает список моделей, которые ссылаются на указанную модель 
    через CustomForeignKey или OneToOneField (кроме table parts)."""
    result = []
    model_tps = getattr(model, 'tps', [])
    for model_class in apps.get_models():
        for field in model_class._meta.get_fields():
            if isinstance(field, (CustomForeignKey,
                                  models.OneToOneField)) and field.remote_field.model == model and not model_class.__name__ in model_tps:
                result.append({
                    "model": model_class.__name__,
                    "field": field.name,
                    "title": model_class._meta.verbose_name_plural
                })
    return result


def build_model_meta(request, model_class, instance=None, exclude_fields=True):
    """Строит полное мета-описание модели для использования на клиенте.
    Включает информацию о:
        - полях модели (с учетом исключений),
        - табличных частях (`table parts`, если заданы в model_class.tps),
        - связанных моделях (related),
        - конфигурации форм (model_class.forms()),
        - типе модели (ContentType).
    Использует кэш Redis/Django (через django.core.cache) с ключом вида 'meta<ModelClass><pk>_<lang>' для ускорения повторных вызовов."""
    from .serializers import CTSerializer
    user = request.user
    lang_code = getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)
    pk = str(instance.pk) if instance else ""

    model_path = f"{model_class.__module__}.{model_class.__name__}"

    cache_key = f"meta_{model_path}_{pk + '_' if pk else ''}{lang_code}"
    data = cache.get(cache_key)
    if data:
        return data

    meta = {}
    model_tps = getattr(model_class, 'tps', [])
    meta['tps'] = model_tps

    meta['fields'] = get_field_info_for_model(model_class, user, instance, exclude_fields)

    app_label = model_class._meta.app_label
    for item in meta['tps']:
        mc = apps.get_model(app_label, item)

        tp = {
            'name': item,
            'type': 'table_part',
            'fields': get_field_info_for_model(mc, user, instance, exclude_fields)
        }

        meta['fields'].append(tp)

    #  meta[field.name] = field_info

    # meta['user_rights'] = get_user_rights(user, model_class)

    # Обработка forms
    updated_forms = []

    model_fields = get_model_fields_for_form(model_class, exclude_fields)

    # if instance:
    meta['related'] = find_related_models(model_class)

    for form in copy.deepcopy(model_class.forms()):
        for key, value in form.items():
            for entry in value:
                if entry.get('default') is None:
                    entry['default'] = {'auto': True, 'children': []}
                    if key in ['list', 'select']:
                        entry['default']['children'].append(
                            {'type': 'd_list',
                             'source': 'models.' + model_class.__name__,
                             'verbose_name': str(model_class._meta.verbose_name_plural),
                             'fields': model_fields
                             })
                    if key in ['object']:
                        for field in model_fields:
                            entry['default']['children'].append(
                                {'type': 'field', 'name': field['name'], 'source': field['source']}
                            )

                        if len(model_tps) > 1:
                            entry['default']['children'].append(
                                {
                                    'type': 'tabs',
                                    'name': 'tabs',
                                    'tabs': get_tp_tabs(model_class)
                                }
                            )
                        if len(model_tps) == 1:
                            tabs = get_tp_tabs(model_class)
                            entry['default']['children'].append(
                                tabs[0]['children'][0]
                            )
                else:
                    if key in ['object']:
                        for field in model_fields:
                            entry['default']['children'].append(
                                {'type': 'field', 'name': field['name'], 'source': field['source']}
                            )

        updated_forms.append(form)

    meta['forms'] = updated_forms

    # Добавляем ContentType
    ct = ContentType.objects.get_for_model(model_class)
    meta['ct'] = CTSerializer(ct).data
    cache.set(cache_key, meta, timeout=timedelta(hours=12).total_seconds())
    # print('Meta No CACHE')
    return meta


def get_fields_list_for_model(model_class, exclude_fields=True):
    """
    Возвращает список полей модели, исключая системные, явно исключённые и переводные (modeltranslation).
    """
    if exclude_fields:
        model_meta_exclude_fields = getattr(model_class, 'meta_exclude_fields', [])
        exclude_fields = set(META_EXCLUDE_FIELDS) | set(model_meta_exclude_fields)
    else:
        exclude_fields = set(META_EXCLUDE_FIELDS)

    # Определим список полей, автосозданных для переводов
    translation_fields = set()
    try:
        opts = translator.get_options_for_model(model_class)
        for base_field in opts.fields:
            for lang_code, _ in settings.LANGUAGES:
                localized_name = build_localized_fieldname(base_field, lang_code)
                translation_fields.add(localized_name)
    except NotRegistered:
        pass  # Модель не зарегистрирована в переводах

    fs = [
        f for f in model_class._meta.get_fields()
        if not f.name.endswith('_ptr')
        and not f.auto_created
        and f.name not in exclude_fields
        and f.name not in translation_fields
    ]
    return fs


def get_field_info_for_model(model_class, user, instance, exclude_fields=True):
    """Возвращает мета-описание полей модели, пригодное для сериализации и использования в интерфейсах."""
    fs = get_fields_list_for_model(model_class, exclude_fields)

    fields = []
    for field in fs:
        field_info = {
            "type": field.__class__.__name__,
        }

        # Базовые атрибуты
        for attr in [
            "null",
            "blank",
            #    "unique",
            "primary_key",
            "editable",
            "help_text",
            #    "db_column",
            #    "db_index"
        ]:
            if hasattr(field, attr):
                field_info[attr] = getattr(field, attr)

        # default отдельно обрабатываем
        if hasattr(field, "default") and field.default is not models.fields.NOT_PROVIDED:
            if not callable(field.default):
                field_info["default"] = field.default
            # Вариант ниже вызвал ошибку для поля author = fields.CustomCurrentProfileField 
            # default_value = field.default
            # field_info["default"] = default_value() if callable(default_value) else default_value

        # verbose_name как строка
        field_verbose_name = (
            getattr(model_class, 'field_verbose_names', {}).get(field.name) or
            (str(field.verbose_name) if hasattr(field, "verbose_name") and field.verbose_name else None)
        )
        if field_verbose_name:
            field_info["verbose_name"] = str(field_verbose_name)

        # max_length
        if hasattr(field, "max_length") and field.max_length:
            field_info["max_length"] = field.max_length

        # auto_now / auto_now_add
        if hasattr(field, "auto_now"):
            field_info["auto_now"] = field.auto_now
        if hasattr(field, "auto_now_add"):
            field_info["auto_now_add"] = field.auto_now_add

        # choices — как список [value, label]
        if hasattr(field, "choices") and field.choices:
            field_info["choices"] = [[choice[0], str(choice[1])] for choice in field.choices]

        # ForeignKey / OneToOne / M2M
        if hasattr(field, "related_model") and field.related_model:
            field_info["related_model"] = field.related_model.__name__
            if hasattr(field, "related_name") and field.related_name:

                field_info["related_name"] = field.related_name

            if hasattr(field, "target_field") and field.target_field is not None:
                target_field_name = field.target_field.name
                if target_field_name != field.related_model._meta.pk.name:
                    # Только если явно указано нестандартное поле
                    field_info["to_field"] = target_field_name
            
            # Определяем is_leaf для ссылочных полей
            # is_leaf=True означает, что у связанной модели нет полей в метаданных
            related_model_fields = get_fields_list_for_model(field.related_model, exclude_fields)
            field_info["is_leaf"] = len(related_model_fields) == 0

        if hasattr(field, "filter_rules") and field.filter_rules:
            field_info["filter_rules"] = field.filter_rules

        #  if hasattr(field, "symmetrical"):
        #      field_info["symmetrical"] = field.symmetrical

        field_info['name'] = field.name
        fields.append(field_info)
    # Добавляем вычисляемые (computed) поля, если модель их объявляет
    if hasattr(model_class, 'get_report_computed_fields_meta'):
        for item in model_class.get_report_computed_fields_meta():
            field_info = {
                "name": item["name"],
                "type": item.get("type", "CharField"),
                "verbose_name": item.get("verbose_name") or item.get("title"),
                "editable": False,
            }
            # Добавляем choices, если они указаны
            if "choices" in item:
                field_info["choices"] = item["choices"]
            if item.get("type") == "ForeignKey" and item.get("related_model"):
                # Только имя модели, как у обычных FK (field.related_model.__name__), чтобы фронт строил URL вида /reports/profilemodel/select_list/
                rm = item["related_model"]
                field_info["related_model"] = rm.rsplit(".", 1)[-1] if "." in rm else rm
                app_label, model_name = rm.split(".", 1)
                related_model = apps.get_model(app_label, model_name)
                related_model_fields = get_fields_list_for_model(related_model, exclude_fields)
                field_info["is_leaf"] = len(related_model_fields) == 0
            fields.append(field_info)

    # Порядок полей: сначала из meta_sort_fields (если задан), остальные — в исходном порядке
    meta_sort_fields = getattr(model_class, 'meta_sort_fields', None)
    if meta_sort_fields:
        sort_set = set(meta_sort_fields)
        ordered = []
        for name in meta_sort_fields:
            for f in fields:
                if f['name'] == name:
                    ordered.append(f)
                    break
        rest = [f for f in fields if f['name'] not in sort_set]
        fields = ordered + rest

    return fields


def get_model_fields_for_form(model_class, exclude_fields=True):
    """Возвращает список полей модели в формате, пригодном для использования в формах."""
    model_fields_s = get_fields_list_for_model(model_class, exclude_fields)

    model_fields = []
    for item in model_fields_s:
        upd_field = {
            "name": item.name,
            'source': item.name
        }
        model_fields.append(upd_field)
    return model_fields


def get_tp_tabs(model_class):
    tabs = []
    model_tps = getattr(model_class, 'tps', [])
    for item in model_tps:
        # item — строка, например: "BookModel"
        # нужно найти модель в том же app, что и model_class
        app_label = model_class._meta.app_label
        try:
            related_model = apps.get_model(app_label, item)
            updated_forms = []

            model_fields = get_model_fields_for_form(related_model)

            tab_content = {
                'type': 'tab',
                'name': related_model._meta.verbose_name_plural,
            }

            table_part = {
                'type': 'table_part',
                'name': related_model._meta.verbose_name_plural,
                'source': item,
                'fields': []
            }

            for field in model_fields:

                if field['name'] == 'owner':
                    continue

                field['source'] = item + '.' + field['source']
                table_part['fields'].append(field)

            tab_content['children'] = [table_part]

            tabs.append(
                tab_content
            )

        except LookupError:
            print(f"Модель {item} не найдена в приложении {app_label}")
    return tabs


# def get_user_rights(user, model_class):
#     ct = ContentType.objects.get_for_model(model_class)

#     # Все булевые поля кроме служебных
#     bool_fields = [
#         field.name for field in Right._meta.fields
#         if isinstance(field, models.BooleanField) and field.name not in ['id']
#     ]

#     # Изначально все права — False
#     rights_dict = {field: False for field in bool_fields}

#     # Получаем роли, связанные с группами пользователя через профили доступа
#     roles = Role.objects.filter(
#         access_profiles__groups__in=user.groups.all()
#     ).distinct()

#     if not roles.exists():
#         return rights_dict

#     # Агрегируем максимум по каждому булевому полю
#     agg = {field: Max(field) for field in bool_fields}
#     result = Right.objects.filter(role__in=roles, ct=ct).aggregate(**agg)

#     # Заполняем rights_dict значениями True, если хотя бы одна роль давала право
#     for field in bool_fields:
#         if result.get(field):
#             rights_dict[field] = True

#     return rights_dict


# ... existing code ...

def _clear_meta_cache():
    """
    Очищает кэш мета-данных для всех моделей из REPORTS_UNIVERSAL_MODELS.
    """
    from django.core.cache import cache
    from django.apps import apps
    from django.conf import settings
    
    cleared_keys_count = 0
    
    for model_path in settings.REPORTS_UNIVERSAL_MODELS:
        try:
            app_label, model_name = model_path.split('.', 1)
            model_class = apps.get_model(app_label, model_name)
            full_model_path = f"{model_class.__module__}.{model_class.__name__}"

            key_pattern = f"meta_{full_model_path}_*"
            if not hasattr(cache, "delete_pattern"):
                raise RuntimeError("Current cache backend does not support delete_pattern")

            deleted_count = cache.delete_pattern(key_pattern) or 0
            cleared_keys_count += int(deleted_count)
                
        except Exception as e:
            print(f"Ошибка при очистке кэша для модели {model_path}: {e}")
            continue
    return {'cleared_keys_count': cleared_keys_count}