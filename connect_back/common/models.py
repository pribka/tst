import os
import shutil
import magic
import uuid
from django_q.tasks import async_task
from sys import platform
from PIL import Image, UnidentifiedImageError
from urllib.parse import quote
from mptt.models import MPTTModel, TreeForeignKey
from django_currentuser.middleware import get_current_authenticated_user
from mptt.managers import TreeManager
from common.current_profile.middleware import get_current_authenticated_profile
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Q, Sum
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError, FieldDoesNotExist, BadRequest
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions

from model_utils import FieldTracker

from bkz3.settings import BACKEND_URL, CUSTOM_CASCADE, CUSTOM_PROTECT, AVATAR_ROOT, CUSTOM_SET_NULL, MEDIA_URL

try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None
from . import validators
from . import fields
from . import page_config


class CustomManager(models.Manager):
    """Кастомный менеджер для BaseModel. Поле для творчества"""

    def super_get(self, pk):
        """Возвращаем объект спределенного класса."""
        ct_id = (
            BaseModel.objects
            .filter(pk=pk)
            .values_list('ct_id', flat=True)
            .first()
        )
        if ct_id is None:
            return None

        model_class = ContentType.objects.get_for_id(ct_id).model_class()
        if model_class is None:
            return None

        return model_class._base_manager.get(pk=pk)


class BaseAbstractModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    author = fields.CustomCurrentProfileField(editable=False, verbose_name=_('Author'))
    is_active = fields.CustomBooleanField(
        default=True, db_index=True,
        verbose_name=_('Активный'),
    )

    created_at = fields.CustomDateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания'),
    )

    updated_at = fields.CustomDateTimeField(
        auto_now=True,
        verbose_name=_('Дата изменения'),
    )

    deleted_at = fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата удаления'),
    )

    sort = models.IntegerField(default=500, verbose_name=_('Сортировка'))

    class Meta:
        abstract = True

    @classmethod
    def get_report_computed_fields_meta(cls):
        """Базовый контракт для универсальных отчетов (приложение reports)."""
        return []

    #*********************************
    # PVH
    def get_pvh_values_model(self, model=None):
        """
        Получить модель хранения значений полей ПВХ

        Есть таблица хранения ПВХ полей для моделей, которые наследуют с BaseModel.

        У других моделей, которые не наследуют с BaseModel, могут быть свои таблицы хранения ПВХ полей.
        Параметр model нужен для таких случаев.
        """
        from pvh.models import PVHPropertyValue
        property_value_model = model
        if not property_value_model:
            property_value_model = PVHPropertyValue
        return property_value_model

    def get_first_property_value_or_values(self, queryset, multi=False):
        # когда добавлял 'owner' в select_related, замер скорости сериализации показывал больше цифру.
        result = queryset.select_related('prop', 'value_fk')
        if not multi:
            result = result.first()
            if not result:
                return None
            return result.get_value()
        else:
            return [prop_value.get_value() for prop_value in result]

    def get_property_value_using_self(self, prop, related_name=None, multi=False):
        assert isinstance(related_name, str), "related_name должен быть строковый"
        queryset = getattr(self, related_name).all().filter(prop=prop).order_by('value_index')
        return self.get_first_property_value_or_values(queryset, multi=multi)

    def get_property_value_using_model(self, prop, model=None, multi=False):
        property_value_model = self.get_pvh_values_model(model=model)
        queryset = property_value_model.objects.filter(owner=self, prop=prop).order_by('value_index')
        return self.get_first_property_value_or_values(queryset, multi=multi)

    def _get_property_value(self, prop, model=None, related_name=None, multi=False):
        if related_name:
            return self.get_property_value_using_self(prop, related_name=related_name, multi=multi)
        else:
            return self.get_property_value_using_model(prop, model=model, multi=multi)

    def get_prop_multi_method_name(self, prop):
        """ Имя функции, которая генерируется на лету """
        func_name_prefix = 'get_'
        prop_code = prop.code
        method_name = "{func_name_prefix}{prop_code}".format(prop_code=prop_code, func_name_prefix=func_name_prefix)
        return method_name

    def get_prop_multi_method_text(self, method_name=None, prop=None, related_name=None):
        prop_code = prop.code
        source = """def {method_name}(self):
                        prop_values = self.{related_name}.all().filter(prop__code='{prop_code}')
                        result = []
                        for prop_value in prop_values:
                            value = prop_value.get_value()
                            result.append(value)
                        return result
                    """.format(method_name=method_name, prop_code=prop_code, related_name=related_name)
        return source

    # def add_prop_multi_method(self, source, method_name):
    #     # https://docs.python.org/3/library/functions.html#compile
    #     # https://docs.python.org/3.8/reference/datamodel.html Искать по тексту Code objects
    #     code_obj = compile(source, '<string>', 'exec')
    #     # https://stackforgeeks.com/blog/python-dynamically-create-function-at-runtime
    #     # Сначала конвертируем в функцию
    #     func = types.FunctionType(code_obj.co_consts[0], locals(), method_name)
    #     # Когда функция готова, делам ее методом объекта
    #     setattr(self, method_name, types.MethodType(func, self))

    def add_prop_multi_values(self, related_name):
        # import website_bakery.pvh.models as pvh_models
        from pvh.models import PVHProperty
        props = PVHProperty.get_properties(self._meta.model, multi=True)
        for prop in props:
            method_name = self.get_prop_multi_method_name(prop)
            source = self.get_prop_multi_method_text(method_name=method_name, prop=prop, related_name=related_name)
            self.add_prop_multi_method(source, method_name)
            self.add_prop_multi_property(method_name, prop.code)

    def add_prop_multi_property(self, method_name, prop_code):
        """
        Пример использования.
        Пример предполагает, что методе __init__ происходит создание динамических полей.

        Иницализация с пустым значением
            tp_obj = TPGoodsOrderModel.objects.all().order_by('created_at').first()

        Добавляем ПВХ значения
            for num in range(0, 3):
                TPGoodsOrderModePropertyValue.objects.create(
                    owner=tp_obj, prop=prop_str_tp_multi,
                    value_index=num, value_str=f'значение {num}')
        На печать выйдет пустой список
            print(tp_obj.x_tp_prop_str_multi) -> []

        Если заново взять с базы
            tp_obj = TPGoodsOrderModel.objects.all().order_by('created_at').first()
        На печать выйдет
            print(tp_obj.x_tp_prop_str_multi) -> [('значение 0', None), ('значение 1', None), ('значение 2', None)]
        """
        assert method_name in dir(self), "Метод должен быть у объекта"
        prop_code = f'x_{prop_code}'
        values = getattr(self, method_name)()
        setattr(self, prop_code, values)
        assert prop_code in dir(self), "Проверка что свойство присвоилось объекту"

    def _load_virtual_fields(self, pvh_values_model=None, related_name=None):
        """
        pvh_values_model - модель хранения значений ПВХ полей

        Если вышла ошибка:
            ValueError: Cannot query "TPGoodsOrderModel object (0b5ea584-e311-44df-b0fd-2c89000557d1)": Must be "BaseModel" instance.
        Значит надо указать pvh_values_model или related_name

        Если ПВХ модель хранения значений отличается от PropertyValue
        то в to_representation сериализатора надо тоже вызывать этот метод.
        По итогам наблюдения за сериализатором таб части заказа (TPGoodsOrderModel)
        """
        from pvh.models import PVHProperty
        properties = PVHProperty.get_properties_for(self._meta.model)
        for prop in properties:
            prop_name = prop.get_name()
            if prop.multi:
                values = self._get_property_value(prop, model=pvh_values_model, related_name=related_name, multi=True)
                if len(values) == 0:
                    setattr(self, prop_name, [])
                    continue

                result = [val[0] for val in values]
                setattr(self, prop_name, result)
            else:
                val = self._get_property_value(prop, model=pvh_values_model, related_name=related_name)
                if val:
                    setattr(self, prop_name, val[0])
                else:
                    setattr(self, prop_name, None)

    def create_property_values(self, pvh_fields, bulk_create=True, pvh_values_model=None):
        """
        pvh_fields - словарь, содержащий ключ-значение ПВХ полей
        """
        # Создаем записи PropertyValue для свойств
        from pvh import models as pvh_models
        property_value_model = self.get_pvh_values_model(model=pvh_values_model)
        objs = []
        for prop_code, prop_value in pvh_fields.items():
            prop = pvh_models.PVHProperty.get_property(self._meta.model, prop_code)
            value_field = prop.get_value_field_name()
            if prop.property_type == pvh_models.PVHProperty.REFERENCE:
                value_field = value_field + '_id'

            if prop_value is not None:
                if not prop.multi:
                    if prop.property_type == pvh_models.PVHProperty.REFERENCE:
                        # prop_value = prop.fk_model.model_class().objects.get(id=prop_value.get('id'))
                        prop_value = prop_value.get('id')
                    obj = property_value_model(owner=self, prop=prop, **{value_field: prop_value})
                    objs.append(obj)
                else:
                    for value_index, value in enumerate(prop_value):
                        if prop.property_type == pvh_models.PVHProperty.REFERENCE:
                            # value = prop.fk_model.model_class().objects.get(id=value.get('id'))
                            value = value.get('id')
                        obj = property_value_model(owner=self, prop=prop, value_index=value_index, **{value_field: value})
                        objs.append(obj)

        if bulk_create:
            property_value_model.objects.bulk_create(objs)
        else:
            for item in objs:
                item.save()

    #***************************************

    @classmethod
    def get_default_cache_key(cls):
        return cls._meta.label_lower

    @classmethod
    def cache_timeout_one_hour(cls):
        return 60 * 60

    @classmethod
    def cache_timeout_one_day(cls):
        return cls.cache_timeout_one_hour() * 24

    @classmethod
    def cache_timeout_one_week(cls):
        return cls.cache_timeout_one_day() * 7

    @classmethod
    def cache_timeout_never_expire(cls):
        return None

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.get_queryset(request)

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_queryset(request).filter(
            Q(author__first_name__icontains=text) | Q(author__last_name__icontains=text) |
            Q(author__middle_name__icontains=text))

    @classmethod
    def get_label(cls) -> str:
        return cls._meta.label

    @classmethod
    def get_page_name(cls, action: str) -> [str, None]:
        if action == 'list':
            return f"page_list_{cls.get_label()}"
        else:
            return None

    @classmethod
    def get_table_need_action(cls):
        return True

    @classmethod
    def filter_fields(cls):
        return {
            'fields': cls._meta.fields,
            'm2m_fields': cls._meta.many_to_many,
            'fields_map': cls._meta.fields_map,
        }

    @classmethod
    def get_table_structure(cls):
        data = []
        accepted_fields = cls.get_table_columns()
        fields_dict = dict()
        extra_table_columns = cls.get_extra_table_columns()
        for each in cls._meta.fields:
            fields_dict[each.name] = each
        for field_name in accepted_fields:
            try:
                table_info = getattr(fields_dict.get(field_name), 'table_info').get_dict()
            except AttributeError:
                table_info = getattr(fields_dict.get(field_name), 'table_info', None)
            if table_info:
                data.append(table_info)
            else:
                table_info = extra_table_columns.get(field_name)
                if table_info:
                    data.append(table_info)
        result = {"table_columns": data,
                  'data_path': cls.get_data_path(),
                  'key': cls.get_label(),
                  'title': cls._meta.verbose_name_plural,
                  'update_condition': {"is_active": True},
                  'edit_form': f'edit_{cls.get_label()}',
                  'context_menu': cls.get_context_menu(),
                  'pageConfig': cls.get_page_config()
                  }
        return result

    @classmethod
    def get_extra_table_columns(cls):
        return {
            'status': {
                "headerName": "",
                "field": "status",
                "cellRenderer": "StatusRow",
                "sortable": False,
                "width": 70,
                "content": ['is_active', ]
            },
            'index_row': {
                "headerName": "№",
                "field": 'index_row',
                "cellRenderer": "IndexRow",
                "sortable": False,
                "width": 70,
            },
            'id': {
                "headerName": "ID",
                "field": "id",
                "cellRenderer": "IdRow",
                "sortable": False,
                "width": 70,
            }
        }

    @classmethod
    def get_page_config(cls):
        return {
            "showFilter": True,
            "headerButtons": cls.get_header_buttons()
        }

    @classmethod
    def get_header_buttons(cls):
        return page_config.BaseModelTableButtonSet(model=cls).get_dict()

    @classmethod
    def get_context_menu(cls):
        return page_config.BaseModelContextMenuButtonSet(model=cls).get_dict()

    @classmethod
    def get_table_columns(cls):
        return ['status', 'index_row', 'id']

    @classmethod
    def get_additional_table_columns(cls):
        return []

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import BaseModelSerializer
        NewBaseModelSerializer = type('NewBaseModelSerializer', (BaseModelSerializer,), {})
        NewBaseModelSerializer.Meta.model = cls
        return NewBaseModelSerializer

    @classmethod
    def get_data_path(cls):
        return '/base_model/'

    @classmethod
    def get_filterset_class(cls):
        from .filters import BaseModelFilter
        filterset = BaseModelFilter
        filterset.Meta.model = cls
        return filterset

    @classmethod
    def get_file_types(cls):
        """Получить разрешенные типы файлов.
        Возвращает список разрешенных типов (code из FileType).
        Если разрешены все типы, возвращает пустой список [].
        Если не разрешено привязывать файлы, возвращает None.
        """
        return None

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True)

    @classmethod
    def get_counter(cls) -> [str, int]:
        return ''

    @classmethod
    def get_hide(cls) -> bool:
        return False

    @classmethod
    def get_protected_fields(cls):
        """Возвращает список полей, по которым нельзя фильтровать для защиты персональных данных."""
        return []

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        filter_fields = []
        additional_field_names = cls.get_additional_table_columns()
        field_names = list(cls.get_table_columns()) + additional_field_names

        for each in field_names:
            try:
                field = cls._meta.get_field(each)
            except FieldDoesNotExist:
                field = getattr(cls, each, None)
                if not isinstance(field, fields.FakeField):
                    continue
            try:
                data = field.filter_info.get_dict()
                if each in additional_field_names:
                    data['is_additional'] = True
                if exclude is True:
                    if field.filter_info.is_exclude is True:
                        data['name'] = data['name'] + '__exclude'
                        filter_fields.append(data)
                    else:
                        continue
                else:
                    filter_fields.append(data)
            except AttributeError:
                continue
        return filter_fields

    @classmethod
    def get_order_param(cls):
        return ['-created_at', ]

    # TODO ликвидируем же?
    def get_final_instance(self):
        """Возвращает экземпляр конечного класса-потомка."""
        instance_id = self.id
        final_instance = self
        while True:
            for key, value in final_instance._meta.fields_map.items():
                current_instance = getattr(final_instance, key, None)
                if getattr(current_instance, 'id', 0) == instance_id:
                    final_instance = current_instance
                    break
            else:
                break
        return final_instance

    @classmethod
    def search_input(cls):
        """Выводить строку поиска?"""
        return False

    @classmethod
    def forms(self):
        return [
            {'list': [{'default': None}]},
            {'object': [{'default': None}]},
            {'select': [{'default': None}]}
        ]

    def set_is_active(self, value: bool, request):
        if not self.author == request.user.profile:
            raise exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise exceptions.ValidationError()
        else:
            pass


class MetadataAbstractModel(models.Model):
    """Модель добавляет json-поле к унаследованным объектам.
    Для сохранения выбора драйвера пользователя."""
    metadata = models.JSONField(default=dict,
                                blank=True,)

    class Meta:
        abstract = True


class FileBaseModel(BaseAbstractModel):
    """"M2M связь файлов и базовой моделью."""
    tracker = FieldTracker(fields=('folder',))

    file = models.ForeignKey('common.File',
                             on_delete=CUSTOM_CASCADE,
                             verbose_name=_('Файл'),
                             related_name='related_attaches',
                             null=True, )
    related_object = models.ForeignKey('common.BaseModel',
                                       on_delete=CUSTOM_CASCADE,
                                       related_name='files',
                                       verbose_name=_('Связанный объект'),
                                       null=True)
    folder = fields.CustomForeignKey(to='common.FolderModel',
                                     null=True,
                                     blank=True,
                                     on_delete=CUSTOM_CASCADE,
                                     verbose_name='Папка',
                                     related_name='related_files',
                                     )

    class Meta:
        verbose_name = "Прикрепленный файл"
        verbose_name_plural = "Прикрепленные файлы"
        unique_together = (('file', 'related_object', 'folder'),)

    def track_fields(self, changed_fields, action_date, created=False, deleted=False):
        try:
            related_object = BaseModel.objects.super_get(pk=self.related_object.pk)
        except BaseModel.DoesNotExist:
            return
        if created and hasattr(related_object, 'track_m2m_fields'):
            related_object.track_m2m_fields(
                self._meta.model,
                self.file._meta.model,
                {self.file.pk},
                'post_add',
                action_date
            )
        if deleted and hasattr(related_object, 'track_m2m_fields'):
            related_object.track_m2m_fields(
                self._meta.model,
                self.file._meta.model,
                {self.file.pk},
                'post_remove',
                action_date
            )


class FileBaseUpdateModel(BaseAbstractModel):
    """
    Модель для хранения времени обновления списка
    прикрепленных файлов (добавления или удаления файлов)
    """
    related_object = models.ForeignKey('common.BaseModel',
                                       on_delete=CUSTOM_CASCADE,
                                       related_name='object',
                                       verbose_name=_('Связанный объект'),
                                       null=True)
    updated_at = fields.CustomDateTimeField(auto_now=True,
                                            verbose_name=_('Дата обновления'), )

    class Meta:
        verbose_name = "Дата обновления прикрепленных файлов"
        verbose_name_plural = "Даты обновления прикрепленных файлов"
        unique_together = (('related_object', 'updated_at'),)


class ObjectViewerRelationModel(BaseAbstractModel):
    obj = models.ForeignKey('common.BaseModel', on_delete=models.CASCADE, related_name='object_viewer_relations')
    profile = models.ForeignKey('users.ProfileModel', on_delete=models.CASCADE, related_name='viewed_objects')

    class Meta:
        unique_together = ['obj', 'profile']


class BaseModel(BaseAbstractModel):
    meta_exclude_fields = ['author', 'created_at', 'mentions', 'ct',]

    attachments = models.ManyToManyField(
        'common.File',
        blank=True,
        verbose_name='Прикрепленные файлы',
        through='common.FileBaseModel',
    )
    viewers = models.ManyToManyField('users.ProfileModel',
                                     through='common.ObjectViewerRelationModel',
                                     blank=True,
                                     through_fields=('obj', 'profile'),
                                     related_name='object_viewers')

    ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=CUSTOM_CASCADE)

    objects = CustomManager()

    exchange = False

    mentions = models.ManyToManyField(
        'users.ProfileModel',
        blank=True,
        verbose_name=_('Упоминаемые пользователи'),
        through='common.MentionModel',
        through_fields=('related_object', 'user'),
        related_name='mention_objects'
    )

    def cluts(self):
        profile = get_current_authenticated_profile()
        if not profile:
            return
        try:
            self.viewers.add(profile)  # TODO ИГРАЙ РОВНЕЕ!!!!
        except:
            pass
        original_object = self.original_object
        if original_object.get_label() == 'comments.CommentModel':
            from .utils import notification_set_is_read
            transaction.on_commit(lambda: async_task(notification_set_is_read, [str(self.pk)], str(profile.pk)))

    @classmethod
    def bulk_cluts(cls, object_ids, profile_id):
        """Пометить объекты как просмотренные профилем одним запросом."""
        if not object_ids or not profile_id:
            return
        Through = cls.viewers.through
        already_read_ids = Through.objects.filter(
            obj_id__in=object_ids,
            profile_id=profile_id
        ).values_list('obj_id', flat=True)
        newly_read_object_ids = list(set(object_ids) - set(already_read_ids))
        if not newly_read_object_ids:
            return
        to_create = [
            Through(obj_id=oid, profile_id=profile_id, author_id=profile_id)
            for oid in newly_read_object_ids
        ]
        Through.objects.bulk_create(to_create, ignore_conflicts=True)
        original_object = cls.objects.super_get(object_ids[0])
        if original_object.get_label() == 'comments.CommentModel':
            ids_string = [
                str(_) for _ in newly_read_object_ids
            ]
            from .utils import notification_set_is_read
            transaction.on_commit(
                lambda: async_task(notification_set_is_read, ids_string, str(profile_id))
            )

    def save(self, *args, **kwargs):
        """Типизируем запись в таблице BaseModel в целях обеспечения процедуры super_get()."""
        if self.ct is None:
            self.ct = ContentType.objects.get_for_model(self)
        if self.exchange:
            self.before_save_by_exchange()
        super().save(*args, **kwargs)
        if self.exchange:
            self.after_save_by_exchange()

    def before_save_by_exchange(self):
        """Метод до записи объекта при интеграции"""
        pass

    def after_save_by_exchange(self):
        """Метод после записи объекта интеграции"""
        pass

    @classmethod
    def get_1c_model_name(cls):
        """Значения переопределяемое для интеграции"""
        return 'БазоваяМодель'

    @classmethod
    def has_characteristics_plan(cls):
        return False

    @classmethod
    def filter_fields(cls):
        return {
            'fields': cls._meta.fields,
            'm2m_fields': cls._meta.many_to_many,
            'fields_map': cls._meta.fields_map,
        }

    @classmethod
    def get_model_characteristics_fields(cls, **kwargs):
        """
        Получаем список характеристик для модели
        Returns QuerySet model:PlanOfCharacteristic
        -------
        """
        ct = ContentType.objects.get_for_model(cls)
        lookups = Q()
        if kwargs:
            for key, value in kwargs.items():
                lookups = lookups | Q(key=key, value=value)
            if not lookups:
                pvh_lookups = []
            else:
                pvh_lookups = ct.pvh_lookups.filter(lookups)
            data_fields = ct.planofcharacteristic_set.filter(
                entity_type='FIELD',
                lookups__in=pvh_lookups,
            ).order_by("field_code", "subfield_code")
            data_independent_fields = ct.planofcharacteristic_set.filter(
                entity_type='INDEPENDENT_FIELD',
                lookups__in=pvh_lookups,
            ).order_by(
                "field_code", "subfield_code"
            )
        else:
            data_fields = ct.planofcharacteristic_set.filter(
                entity_type='FIELD',
                lookups__isnull=True,
            ).order_by("field_code", "subfield_code")
            data_independent_fields = ct.planofcharacteristic_set.filter(
                entity_type='INDEPENDENT_FIELD',
                lookups__isnull=True,
            ).order_by(
                "field_code", "subfield_code"
            )
        return data_fields, data_independent_fields

    @classmethod
    def get_model_characteristics_subfields(cls, **kwargs):
        """
        Получаем список полей хранения данных
        Returns QuerySet model:PlanOfCharacteristic
        -------
        """
        ct = ContentType.objects.get_for_model(cls)
        data_fields = ct.planofcharacteristic_set.filter(entity_type__in=['SUBFIELD', 'INDEPENDENT_FIELD']).order_by(
            "field_code", 'subfield_code')
        return data_fields

    def get_update_permission(self, request) -> bool:
        """
        Возвращает True, если пользователь имеет разрешение на изменение объекта.
        Метод используется для определения доступа к изменению объекта, добавлению и удалению прикрепленных файлов
        и т. д.
        """
        return request.user.profile == self.author

    def get_attach_permission(self, request) -> bool:
        return self.get_update_permission(request)

    def get_update_tag_permission(self, request) -> bool:
        return self.get_update_permission(request)

    def get_detail_permission(self, request) -> bool:
        """
        Возвращает True, если пользователь имеет разрешение на получение деталки объекта.
        Метод используется для определения доступа к прикрепленным файлам, комментариям и т. д.
        """
        return request.user.profile == self.author

    @property
    def get_member_ids(self):
        """Возвращает список участников объекта (id ProfileModel). Для создания собраний."""
        return []

    @property
    def original_object(self):
        return BaseModel.objects.super_get(self.pk)

    @property
    def frontend_route(self):
        return ''  # переопределяем в целевой модели

    @property
    def label(self):
        return self._meta.label_lower.replace('.', '_').replace('model', '')

    def __str__(self):
        return f"{getattr(self.ct, 'app_labeled_name', '')} {str(self.id)}"

    class Meta:
        verbose_name = _('Базовая запись')
        verbose_name_plural = _('Базовые записи')


class BaseAbstractCatalog(models.Model):
    code = fields.CustomCharField(
        verbose_name=_('search code'),
        unique=True,
        null=False,
        default=uuid.uuid1,
        max_length=100,
        blank=True,
        table_info=page_config.DefaultTableColumn(width=300)
    )

    class Meta:
        abstract = True


class BaseCatalog(BaseModel):
    name = fields.CustomCharField(
        verbose_name=_('Название'),
        max_length=255,
        null=False,
        default='',
        blank=True,
        table_info=page_config.DefaultTableColumn(width=300)
    )  # TODO перенести в абстрактную модель BaseAbstractCatalog
    is_predefined = fields.CustomBooleanField(verbose_name=_('Предопределенное значение'), db_index=True, default=False)

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import BaseCatalogListSerializer, BaseCatalogCUDSerializer, BaseCatalogRetrieveSerializer
        if action == 'list':
            serializer_class = type('serializer_class', (BaseCatalogListSerializer,), {})
        elif action == 'retrieve':
            serializer_class = type('serializer_class', (BaseCatalogRetrieveSerializer,), {})
        elif action in ['create', 'update']:
            serializer_class = type('serializer_class', (BaseCatalogCUDSerializer,), {})
        else:
            serializer_class = type('serializer_class', (BaseCatalogListSerializer,), {})
        serializer_class.Meta.model = cls
        return serializer_class

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
    def get_select_queryset(cls, request=None):
        return super().get_select_queryset(request)

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_queryset(request).filter(name__icontains=text)

    @classmethod
    def get_data_path(cls):
        return '/base_catalog/'

    @classmethod
    def get_table_need_action(cls):
        return not cls.is_enum()

    @classmethod
    def get_table_columns(cls):
        if cls.is_enum():
            return ['status', 'name', 'code', 'created_at']
        else:
            return ['status', 'name', 'code', 'created_at', 'is_predefined']

    @classmethod
    def get_filterset_class(cls):
        from .filters import BaseCatalogFilter
        filterset = BaseCatalogFilter
        filterset.Meta.model = cls
        return filterset

    class Meta:
        verbose_name = _('Запись справочника')
        verbose_name_plural = _('Записи справочника')

    @classmethod
    def get_order_param(cls):
        return ['name']

    def __str__(self):
        return f"{self.name}"

    def set_is_active(self, value: bool, request):
        if self.is_enum() or self.is_predefined:
            raise exceptions.PermissionDenied()
        else:
            super().set_is_active(value, request)


class FileTypeFakeField(fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Тип файла")
    name = 'file_type'
    default = None
    blank = True
    to_fields = ('code',)
    remote_field = 'code'
    key = 'common.FileType'
    model = 'common.FileType'
    data_path = '/app_info/select_list/?model=common.FileType'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(
            mime_type__file_type__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(
            mime_type__file_type__in=value.get('value'))
        return queryset

    def get_order_param(self):
        return ['mime_type__file_type__name',]


def get_file_path(instance, filename):
    if instance.author:
        return f"user_{instance.author.id}/{uuid.uuid4()}.{instance.extension}"
    else:
        return f"1c/{filename}"


class FolderModel(MPTTModel, BaseCatalog, BaseAbstractCatalog):
    parent = TreeForeignKey('self',
                            on_delete=CUSTOM_CASCADE,
                            null=True,
                            blank=True,
                            related_name='children')
    related_object = models.ForeignKey('BaseModel',
                                       verbose_name='Хозяин папки',
                                       related_name='folders',
                                       null=True,
                                       on_delete=CUSTOM_CASCADE)
    level = models.IntegerField(default=0)
    lft = models.IntegerField(default=0)
    rght = models.IntegerField(default=0)
    tree_id = models.IntegerField(default=0)
    is_deleted = fields.CustomBooleanField(
        default=False,
        verbose_name=_('Удалён'),
        help_text='Совсем удален. Даже в корзине его нет.',
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Описание"),
    )

    objects = TreeManager()

    class Meta:
        verbose_name = 'Папка'
        verbose_name_plural = 'Папки'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .serializers import BaseFolderSerializer
        data = BaseFolderSerializer(instance=self).data
        cache.set('CachedBaseFolderSerializer_' + str(self.pk), data, timeout=None)


class File(BaseCatalog, BaseAbstractCatalog):
    upload = fields.CustomFileField(upload_to=get_file_path, verbose_name=_("Файл"), max_length=1000)
    extension = fields.CustomCharField(null=False, blank=True, editable=False,
                                       verbose_name=_("Расширение файла"), default='', max_length=100)
    mime_type = fields.CustomForeignKey(to='common.MimeType', to_field='code', null=True, blank=True, editable=False,
                                        on_delete=CUSTOM_PROTECT, verbose_name=_('MIME-тип'))
    size = fields.CustomPositiveIntegerField(blank=True, null=True, editable=False, verbose_name=_("Размер файла"))
    is_image = fields.CustomBooleanField(null=False, blank=True, default=False, verbose_name=_('Картинка'))
    is_video = fields.CustomBooleanField(null=False, blank=True, default=False, verbose_name=_('Видео'))
    is_audio = fields.CustomBooleanField(null=False, blank=True, default=False, verbose_name=_('Аудио'))
    is_voice = fields.CustomBooleanField(null=False, blank=True, default=False, verbose_name=_('Голосовое'))
    is_dynamic = fields.CustomBooleanField(default=False, verbose_name='Автоматически обновляемый файл')
    is_deleted = fields.CustomBooleanField(
        default=False,
        verbose_name=_('Удален'),
        help_text='Совсем удален. Даже в корзине его нет.',
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Описание"),
    )
    file_type = FileTypeFakeField()
    folder = fields.CustomForeignKey(
        to='common.FolderModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Каталог'),
        related_name='directly_files',
    )
    is_orphaned = fields.CustomBooleanField(
        null=False,
        blank=True,
        default=False,
        verbose_name='Без родителя',
        help_text='Файл не привязанный ни к одному из объектов.'
    )
    is_confined = fields.CustomBooleanField(
        null=False,
        blank=True,
        default=False,
        verbose_name='Ограниченный',
        help_text='Файл не будет показан в списке файлов пользователя.'
    )

    class Meta:
        verbose_name = _("Файл")
        verbose_name_plural = _("Файлы")

    def save(self, *args, **kwargs):
        explicit_is_voice = bool(self.is_voice)
        splitted_name = self.upload.file.name.split('.')
        if len(splitted_name) < 2:
            extension = ''
        else:
            extension = splitted_name.pop()
        if extension:
            extension.lower()
        self.extension = extension
        if not self.name:
            self.name = '.'.join(splitted_name)
        if platform == "win32":
            mime_type = magic.from_buffer(self.upload.read(2048), mime=True)
        else:
            mime_type = magic.detect_from_content(self.upload.read(2048)).mime_type
        # Поправка на баг библиотеки libmagic:
        if mime_type == 'application/CDFV2':
            if extension == 'doc':
                mime_type = 'application/msword'
            elif extension == 'xls':
                mime_type = 'application/vnd.ms-excel'
            elif extension == 'ppt':
                mime_type = 'application/vnd.ms-powerpoint'
        try:
            self.mime_type = MimeType.objects.get(code=mime_type)
        except ObjectDoesNotExist:
            new_mime_type = MimeType.objects.create(code=mime_type, name=mime_type)
            self.mime_type = new_mime_type
        if mime_type in ['video/3gpp',
                         'video/mpeg',
                         'video/mp4',
                         'video/ogg',
                         'video/quicktime',
                         'video/webm']:
            self.is_video = True
        else:
            self.is_video = False
        if mime_type in ['audio/3gpp',
                         'audio/aac',
                         'audio/flac',
                         'audio/mpeg',
                         'audio/mp3',
                         'audio/mp4',
                         'audio/ogg',
                         'audio/wav',
                         'audio/webm']:
            self.is_audio = True
        else:
            self.is_audio = False

        if explicit_is_voice:
            self.is_voice = True
            self.is_audio = True
            self.is_video = False
        else:
            self.is_voice = False

        self.size = self.upload.file.size
        super().save(*args, **kwargs)
        try:
            image = Image.open(self.upload)
            self.is_image = True
        except UnidentifiedImageError:
            self.is_image = False
        except OSError:  #: При загрузке файла формата .PSD (Photoshop Document)
            self.is_image = False

        super().save(update_fields=('is_image',), force_update=True)

    def copy_to_avatar_path(self):
        if os.path.exists(self.upload.path):
            logo_path = f"{AVATAR_ROOT}{self.pk}.{self.extension}"
            if not os.path.exists(logo_path):
                shutil.copyfile(self.upload.path, logo_path)

    @property
    def avatar_url(self):
        from .utils import get_logo_url
        filename = f"{self.pk}.{self.extension}" if self.extension else f"{self.pk}"
        return get_logo_url(filename)

    @property
    def absolute_url(self):
        return f"{BACKEND_URL}{self.upload.url}"

    @property
    def author_url(self):
        if DOWNLOADER_PATH is None:
            return self.absolute_url
        parent_path = quote(f"?id={self.pk}")
        return f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'

    @property
    def full_name(self):
        return f"{self.name}.{self.extension}" if self.extension else self.name

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import FileCreateSerializer, FileUpdateSerializer, FileListSerializer, AppFileSerializer
        if action is None:
            return AppFileSerializer
        elif action == 'create':
            return FileCreateSerializer
        elif action == 'update':
            return FileUpdateSerializer
        else:
            return AppFileSerializer

    @classmethod
    def get_queryset(cls, request=None):
        user = request.user.profile
        queryset = cls.objects.filter(is_active=True, author=user)
        return queryset.select_related('mime_type__file_type')

    @classmethod
    def get_data_path(cls):
        return '/files/'

    @classmethod
    def get_table_columns(cls):
        return ['name', 'extension', 'file_type', ]

    @classmethod
    def get_table_structure(cls):
        result = super().get_table_structure()
        result['table_columns'].append(cls.file_type.table_info.get_dict())
        return result

    @classmethod
    def search_input(cls):
        return True


class FileType(BaseCatalog, BaseAbstractCatalog):
    icon = fields.CustomCharField(
        null=False,
        default='',
        max_length=31,
        blank=True,
        verbose_name=_("Иконка"),
    )

    class Meta:
        verbose_name = _("Тип файла")
        verbose_name_plural = _("Типы файла")

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/filetypes/'


def _get_default_file_type():
    file_type, created = FileType.objects.get_or_create(code='other', defaults={'name': 'N/A'})
    return file_type.code


class MimeType(BaseCatalog, BaseAbstractCatalog):
    file_type = fields.CustomForeignKey(
        to='common.FileType',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        default=_get_default_file_type, verbose_name=_('Тип файла'), related_name='mime_type'
    )

    class Meta:
        verbose_name = _('MIME тип файла')
        verbose_name_plural = _('MIME типы файла')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MimeTypeCUDSerializer, MimeTypeListSerializer
        if action is None:
            return MimeTypeListSerializer
        elif action in ['create', 'update']:
            return MimeTypeCUDSerializer
        else:
            return MimeTypeListSerializer

    @classmethod
    def get_data_path(cls):
        return '/mimetypes/'

    @classmethod
    def get_table_columns(cls):
        return ['id', 'name', 'file_type', 'author', 'created_at', 'updated_at', 'deleted_at',
                'is_predefined']

    @classmethod
    def get_filterset_class(cls):
        from .filters import MimeTypeFilter
        filterset = MimeTypeFilter
        return filterset

    @classmethod
    def get_page_config(cls):
        return {"showFilter": True}

    @classmethod
    def get_context_menu(cls):
        return page_config.ModelSetConfig(model=cls, buttons=("edit",), edit=page_config.EditButton()).get_dict()


class Organization(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def get_data_path(cls):
        return '/organizations/'

    class Meta:
        verbose_name = _('Организация')
        verbose_name_plural = _('Организации')


def get_default_date():
    return timezone.localdate()


def get_default_datetime():
    return timezone.now()


class BaseDocument(BaseModel):
    organization = fields.CustomForeignKey(to='common.Organization',
                                           to_field='code',
                                           on_delete=CUSTOM_PROTECT,
                                           null=False,
                                           default='current',
                                           verbose_name=_('Организация'))
    doc_num = fields.CustomCharField(max_length=36, verbose_name=_('Номер документа'), blank=True, null=False,
                                     default=uuid.uuid1)
    doc_date = fields.CustomDateField(default=get_default_date, null=False, verbose_name=_('Document date'), blank=True)
    is_posted = fields.CustomBooleanField(default=False, verbose_name=_('Документ проведен'))
    is_draft = fields.CustomBooleanField(default=True,
                                         editable=False,
                                         verbose_name=_('Черновик'))
    comment = fields.CustomCharField(default='',
                                     max_length=1000,
                                     verbose_name=_('Комментарий'),
                                     blank=True)

    def __str__(self):
        return f"{self.ct.name} {self.doc_num} {self.doc_date}"

    class Meta:
        verbose_name = _("Документ")
        verbose_name_plural = _("Документы")

    @classmethod
    def get_data_path(cls):
        return '/base_documents/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import BaseDocumentListSerializer, BaseDocumentDetailSerializer, BaseDocumentCUDSerializer
        if action in ['update', 'partial_update', 'create']:
            serializer = BaseDocumentCUDSerializer
        elif action == 'retrieve':
            serializer = BaseDocumentDetailSerializer
        elif action == 'list':
            serializer = BaseDocumentListSerializer
        else:
            serializer = BaseDocumentListSerializer
        serializer.Meta.model = cls
        return serializer

    @classmethod
    def get_table_columns(cls):
        return ['status', 'doc_num', 'doc_date', 'author', 'created_at', 'updated_at', 'deleted_at',
                'is_predefined']

    @classmethod
    def get_extra_table_columns(cls):
        return {
            'status': {
                "headerName": "",
                "field": "status",
                "cellRenderer": "StatusRow",
                "sortable": False,
                "width": 70,
                "content": ['is_active', 'locked', 'is_posted']
            },
            'id': {
                "headerName": "ID",
                "field": "id",
                "cellRenderer": "IdRow",
                "sortable": False,
                "width": 70,
            }
        }

    @classmethod
    def get_tabular_parts(cls):
        """Возвращает словарь с табличными частями документа.
        Ключ: related_name табчасти документа.
        По ключу записывается сериализатор и фильтр, который необходимо применить.
        """
        return {
            'tabular_attr': 'model',  # TODO добавить модель табчасти
        }

    @classmethod
    def get_context_menu(cls):
        return page_config.BaseDocumentContextMenuButtonSet(model=cls).get_dict()

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.objects.filter(Q(doc_num__icontains=text) | Q(comment__icontains=text))

    @classmethod
    def has_registrars(cls):
        """
        Метод возвращает True у классов моделей которые создают запись в регистр
        Так же чтобы все работало корректно для такого класса нужно указать методы get_registrar_tabular_parts
        и get_type_of_accumulation
        """
        return False

    @classmethod
    def get_registrar_tabular_parts(cls):
        """
        Метод используется для мделей которые создают записи в регистрах (приходы,расходы и т.д)
        возвращает словаь ключами которого является related_name на таб.часть в значении list из моделей регистров в
        которые создадутся записи

        """
        return {
        }

    @classmethod
    def get_type_of_accumulation(cls):
        """
        Метод используется для моделей которые создают записи в регистрах (приходы,расходы и т.д)
        Возвращает:
                    int 1 для документа прихода
                    int -1 для документа расхода
                    None для обычного документа
        """
        return None

    @classmethod
    def is_transfer(self):
        """
        Является ли документ перемещением
        """
        return False

    def check_locking(self):
        locking = self.get_data_about_locking()
        if locking:
            current_user = get_current_authenticated_user()
            locking_user = locking.get('user', dict())
            if locking_user.get('id', 0) != current_user.id:
                user_fullname = f"{locking_user.get('last_name', '')} {locking_user.get('first_name', '')} {locking_user.get('middle_name', '')}"
                raise exceptions.PermissionDenied(_('Документ заблокирован пользователем') + ' ' + user_fullname)

    def get_data_about_locking(self):
        """Возвращает данные о блокировке записи из кэша (словарь). Если запписи нет, возвращает None."""
        return cache.get(f'locked_doc__{self.id}', None)

    def set_is_active(self, value: bool, request):
        if self.is_active is True and value is False and self.is_posted is True:
            self.set_is_posted(False)
        super().set_is_active(value, request)

    def set_is_posted(self, is_posted: bool):
        """Проводка/ отмена проводки документа"""
        self.is_posted = is_posted

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.check_locking()
            super().save(*args, **kwargs)
            if self.__class__.has_registrars():
                registrar_tabular_parts = self.__class__.get_registrar_tabular_parts()
                for related_name, register_models in registrar_tabular_parts.items():
                    for register_model in register_models:

                        old_register_records = register_model.objects.filter(registrar=self)
                        old_register_records.delete()

                        if hasattr(self, related_name):
                            edition_part_values = getattr(self,
                                                          related_name).all()  # получаем список елементов таб части
                            register_model.check_has_written_records(edition_part_values)
                            if self.is_posted:
                                register_model.objects.create_movement(self, edition_part_values)


class BaseAbstractTabularPart(BaseAbstractModel):
    @classmethod
    def get_table_structure(cls):
        data = []
        accepted_fields = cls.get_table_columns()
        fields_dict = dict()
        extra_table_columns = cls.get_extra_table_columns()
        for each in cls._meta.fields:
            fields_dict[each.name] = each
        for field_name in accepted_fields:
            try:
                table_info = getattr(fields_dict.get(field_name), 'tp_info').get_dict()
            except AttributeError:
                table_info = getattr(fields_dict.get(field_name), 'tp_info', None)
            if table_info:
                data.append(table_info)
            else:
                table_info = extra_table_columns.get(field_name)
                if table_info:
                    data.append(table_info)
        result = {"table_columns": data,
                  'data_path': cls.get_data_path(),
                  'key': cls.get_label(),
                  'title': cls._meta.verbose_name_plural,
                  'update_condition': {"is_active": True},
                  'edit_form': f'edit_{cls.get_label()}',
                  'context_menu': cls.get_context_menu(),
                  'pageConfig': cls.get_page_config(),
                  'tableWidget': 'FlatTable'
                  }
        return result

    @classmethod
    def get_table_columns(cls):
        data = ['index_row']
        return data

    @classmethod
    def get_page_config(cls):
        return {
            "showFilter": True,
            "headerButtons": cls.get_header_buttons()
        }

    @classmethod
    def get_header_buttons(cls):
        return page_config.TabularPartButtonSet(model=cls).get_dict()

    @classmethod
    def get_context_menu(cls):
        return page_config.TabularPartContextMenuButtonSet(model=cls).get_dict()

    class Meta:
        abstract = True


class Individual(BaseCatalog, BaseAbstractCatalog):
    """Физические лица"""
    iin = fields.CustomCharField(max_length=12, verbose_name=_('ИИН'), null=False, default='000000000000',
                                 blank=False, unique=True, validators=[validators.iin_validator])

    comment = fields.CustomCharField(default='',
                                     max_length=1000,
                                     verbose_name=_('Комментарий'),
                                     blank=True)

    @classmethod
    def get_data_path(cls):
        return '/individuals/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import IndividualSerializer, IndividualCUDSerializer, IndividualDetailSerializer
        if action == 'list':
            return IndividualSerializer
        elif action in ['update', 'create']:
            return IndividualCUDSerializer
        elif action == 'retrieve':
            return IndividualDetailSerializer
        else:
            return IndividualSerializer

    class Meta:
        verbose_name = _('Физическое лицо')
        verbose_name_plural = _('Физические лица')


class NotificationTypes(BaseCatalog):
    class Meta:
        verbose_name = "Тип уведомления"
        verbose_name_plural = "Типы уведомлений"


class RepetitionTypes(BaseCatalog):
    class Meta:
        verbose_name = 'Тип повторения события'
        verbose_name_plural = 'Тип повторения событий'

    def __str__(self):
        return self.name


class Participants(BaseModel):
    """
    Данная модель отвечает за включение пользователей в список участников мироприятия.
    В данной модели поля привязаны к users.Profile
    """

    participant_profiles = models.ManyToManyField(
        'users.ProfileModel',
        blank=True,
        verbose_name="Профили участников события",
        related_name="event_participant_profiles",
    )

    class Meta:
        verbose_name = "Участник события"
        verbose_name_plural = "Участники события"


class Events(BaseCatalog):
    event_start = models.DateTimeField(
        default=False,
        verbose_name='Дата и время начала события',
    )
    event_end = models.DateTimeField(
        default=False,
        verbose_name='Дата и время конец события',
    )
    event_place = models.TextField(
        default=False,
        blank=True,
        null=True,
        verbose_name='Место проведения'
    )
    creator = models.ForeignKey(
        'users.ProfileModel',
        blank=True,
        null=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Автор события',
        related_name='events_creator'
    )
    events_participants = models.ForeignKey(
        Participants,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Участники события',
        blank=True,
        null=True,
    )
    notification = models.ManyToManyField(
        NotificationTypes,
        blank=True,
        related_name="event_notifications",
        verbose_name='Уведомления участникам',
    )
    event_description = models.TextField(
        default=False,
        blank=True,
        null=True,
        verbose_name='Описание события',
    )
    repetition_type = models.ForeignKey(
        RepetitionTypes,
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Тип повторения события',
    )
    workgroup = models.ForeignKey(
        'workgroups.WorkgroupModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Рабочая группа',
    )

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return f'{self.name} созданно {self.creator.user.username}'


class FiltersStore(BaseAbstractModel):
    filters = models.JSONField(default=dict)
    model = models.CharField(
        blank=True,
        null=False,
        max_length=255,
        default=''
    )
    page_name = models.CharField(blank=True, null=False, default='', max_length=255)

    class Meta:
        verbose_name = 'Хранилище фильтров'
        verbose_name_plural = 'Хранилище фильтров'
        unique_together = (('author', 'model', 'page_name'),)


class RecentlySelectedUsersModel(BaseAbstractModel):
    """Список ранее выбранных пользователей для виджета выбора."""
    profile_ids = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = 'Ранее выбранные пользователи'
        verbose_name_plural = 'Ранее выбранные пользователи'
        unique_together = (('author',),)


class FieldTypeChoices(models.TextChoices):
    char = 'Char', _('Строка')
    foreign_key = 'FK', _('Ссылка')
    decimal = 'Decimal', _('Число')
    boolean = 'Boolean', _('Булеан')
    date = 'Date', _('Дата')
    date_time = 'DateTime', _('Дата, время')


class PlanOfCharacteristicBlock(BaseCatalog, BaseAbstractCatalog):

    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name_plural = "Блоки ПВХ"
        verbose_name = "Блок ПВХ"


class PlanOfCharacteristicLookup(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    target_model = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='pvh_lookups',
        verbose_name="целевая модель",
    )
    key = fields.CustomCharField(
        max_length=100,
        null=False,
        default='',
        blank=False,
        verbose_name="Ключ для выборки"
    )
    value = fields.CustomCharField(
        max_length=100,
        null=False,
        default='',
        blank=False,
        verbose_name="Значение для выборки",
    )

    info = models.JSONField(null=False, blank=True, default=dict, verbose_name='Информация для фронтенда')

    class Meta:
        verbose_name = "Лукап ПВХ"
        verbose_name_plural = "Лукапы ПВХ"
        unique_together = (('key', 'value', 'target_model',),)


class PlanOfCharacteristic(BaseModel, MPTTModel, BaseAbstractModel):
    """
    Модель ПВХ
    entity_type - поле указывает на тип объекта (FIELD - группы полей field_code обязательноеб, subfield_code не нужен;
                                                 SUBFIELD - поле,наследуется от FIELD subfield_code, field_code обязательное,
                                                                                                    subfield_code обязательное;
                                                 INDEPENDENT_FIELD - незавсимое поле subfield_code, field_code обязательное,
                                                                                                    subfield_code обязательное)
    """

    class RepetitiveChoices(models.TextChoices):
        REPEATS = 'True', _('REPEATS')
        NOT_REPEATS = 'False', _('NOT REPEATS')
        # CONDITIONALLY_REPEATS = 'udefined', _('CONDITIONALLY REPEATS')

    class RequiredChoices(models.TextChoices):
        REQUIRED = 'True', _('REQUIRED')
        # CONDITIONALLY_REQUIRED = 'CONDITIONALLY_REQUIRED', _('CONDITIONALLY REQUIRED')
        OPTIONAL = 'False', _('OPTIONAL')
        # UNDEFINED = 'UNDEFINED', _('UNDEFINED')
        # NOT_USED = 'NOT_USED', _('NOT USED')

    class BlockChoices(models.TextChoices):
        # Deprecated!!! Устарело!!! Теперь используется FK на PlanOfCharacteristicBlock.
        # Но для корректной работы миграций пусть будет.
        IDENTIFICATION = '00', _('IDENTIFICATION BLOCK')
        CODED_INFORMATION = '01', _('CODED INFORMATION BLOCK')
        DESCRIPTION = '02', _('DESCRIPTION BLOCK')
        NOTES = '03', _('NOTES BLOCK')
        RELATED_RECORD = '04', _('RELATED RECORD BLOCK')
        RELATED_TITLES = '05', _('RELATED TITLES BLOCK')
        ANALYSIS_AND_BIBLIOGRAPHIC_HISTORY = '06', _('ANALYSIS AND BIBLIOGRAPHIC HISTORY BLOCK')
        RESPONSIBILITY = '07', _('RESPONSIBILITY BLOCK')
        INTERNATIONAL_USE = '08', _('INTERNATIONAL USE BLOCK')
        LOCAL_USE = '09', _('LOCAL USE BLOCK')

    class EntityTypeChoices(models.TextChoices):
        INDEPENDENT_FIELD = 'INDEPENDENT_FIELD', _('INDEPENDENT FIELD')
        FIELD = 'FIELD', _('FIELD')
        SUBFIELD = 'SUBFIELD', _('SUBFIELD')

    parent = TreeForeignKey('self',
                            on_delete=CUSTOM_PROTECT,
                            null=True,
                            blank=True,
                            related_name='children')
    level = models.IntegerField(default=0)
    lft = models.IntegerField(default=0)
    rght = models.IntegerField(default=0)
    tree_id = models.IntegerField(default=0)
    block = fields.CustomForeignKey(
        to='common.PlanOfCharacteristicBlock',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=True,
        default='default',
        related_name='characteristics',
        verbose_name=_('Block')
    )
    entity_type = fields.CustomCharField(choices=EntityTypeChoices.choices,
                                         default=EntityTypeChoices.INDEPENDENT_FIELD,
                                         max_length=255,
                                         verbose_name=_('Characteristic type')
                                         )
    appointment = models.ManyToManyField(to=ContentType,
                                         verbose_name=_('Field appointment'))
    lookups = models.ManyToManyField(
        to='common.PlanOfCharacteristicLookup',
        blank=True,
        verbose_name='Лукапы',
    )
    field_code = fields.CustomCharField(max_length=5,
                                        blank=True,
                                        null=True,
                                        default=None,
                                        verbose_name=_('Field code'))
    subfield_code = fields.CustomCharField(max_length=5,
                                           blank=True,
                                           null=True,
                                           default=None,
                                           verbose_name=_('Subfield code'))
    name = fields.CustomCharField(max_length=255,
                                  verbose_name=_('Name'))
    collapse = fields.CustomBooleanField(verbose_name='collapse', default=False)
    default_collapse = fields.CustomBooleanField(verbose_name='default_collapse', default=False)
    is_predefined = fields.CustomBooleanField(verbose_name=_('Predefined value'), default=False)
    repetitive = fields.CustomCharField(choices=RepetitiveChoices.choices,
                                        null=True,
                                        blank=True,
                                        max_length=255,
                                        verbose_name=_('Repetitive')
                                        )
    required = fields.CustomCharField(choices=RequiredChoices.choices,
                                      null=True,
                                      blank=True,
                                      max_length=255,
                                      verbose_name=_('REQUIRED')
                                      )
    is_link_field = fields.CustomBooleanField(default=False)
    field_linked_to = fields.CustomForeignKey(to=ContentType,
                                              null=True,
                                              blank=True,
                                              on_delete=CUSTOM_CASCADE,
                                              related_name='poc',
                                              verbose_name=_('Field linked model'))
    is_duplicate_field = fields.CustomBooleanField(default=False,
                                                   verbose_name=_('Duplicate with main model'))
    duplicate_field_name = fields.CustomCharField(max_length=255,
                                                  null=True,
                                                  blank=True,
                                                  verbose_name=_('Field name in main model')
                                                  )
    delimiter = fields.CustomCharField(max_length=100,
                                       null=True,
                                       blank=True,
                                       verbose_name=_('Delimiter'))
    description = fields.CustomCharField(max_length=10000,
                                         blank=True,
                                         null=True,
                                         verbose_name=_('Description'))
    comment = fields.CustomCharField(max_length=255,
                                     blank=True,
                                     null=True,
                                     verbose_name=_('Комментарий'))
    field_type = fields.CustomCharField(max_length=255,
                                        blank=True,
                                        null=True,
                                        choices=FieldTypeChoices.choices,
                                        verbose_name=_('Field data type')
                                        )

    @classmethod
    def get_page_config(cls):
        if cls.is_enum():
            return {
                "showFilter": True
            }
        else:
            return super().get_page_config()

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['update_condition'] = {'is_active': True, 'is_predefined': False}
        if cls.is_enum():
            data.pop('edit_form', None)
            data.pop('update_condition', None)
        return data

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_table_columns(cls):
        data = []
        data.insert(1, 'name')
        data.insert(2, 'block')
        data.insert(3, 'entity_type')
        data.insert(4, 'field_type')
        data.insert(5, 'field_code')
        data.insert(6, 'subfield_code')
        data.insert(7, 'repetitive')
        data.insert(8, 'required')
        data.insert(9, 'field_linked_to')
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from pvh.serializers import PlanOfCharacteristicCUDSerializer, PlanOfCharacteristicListSerializer
        if action in ['create', 'update', 'partial_update']:
            return PlanOfCharacteristicCUDSerializer
        elif action in ['list', 'retrieve']:
            return PlanOfCharacteristicListSerializer
        else:
            return PlanOfCharacteristicListSerializer

    @property
    def get_field_linked_to(self):
        if self.field_linked_to:
            result = self.field_linked_to.model_class()._meta.label
        else:
            result = ''
        return result

    @classmethod
    def get_data_path(cls):
        return '/plan_of_characteristic/'

    @property
    def full_field_code(self):
        if self.field_code and self.subfield_code:
            return self.field_code + '_' + self.subfield_code

    @property
    def block_full_name(self):
        return f"{self.block.pk} {self.block.name}"

    class Meta:
        verbose_name = _('Plan Of Characteristic')
        verbose_name_plural = _('Plans Of Characteristic')

    def clean(self):
        if self.entity_type in ['SUBFIELD', 'INDEPENDENT_FIELD']:
            if not self.subfield_code:
                raise ValidationError('subfield_code обзаятелен для этого типа поля')
            if not self.field_type:
                raise ValidationError('field_type обзаятелен для этого типа поля')
        if self.entity_type in ['FIELD', 'INDEPENDENT_FIELD'] and not self.field_code:
            raise ValidationError('field_code обзаятелен для этого типа поля')
        if self.entity_type == 'SUBFIELD' and not self.parent:
            raise ValidationError('parent обзаятелен для этого типа поля')
        if self.entity_type == 'INDEPENDENT_FIELD' and self.repetitive == 'True':
            raise ValidationError('нельзя создать повторяемое независимое поле')

    def save(self, *args, **kwargs):
        if self.entity_type == 'SUBFIELD':
            self.field_code = self.parent.field_code
            self.block = self.parent.block
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PlanOfCharacteristicValue(BaseModel):
    """
    Модель значений ПВХ
    owner - глобальный объект к  которому относится значение
    linked_field - если значение с типом FK, ссылка на глобальный объект на который ссылается значение
    field_index - порядковый номер записи, если есть вариант повторяемости поля
    """
    prop = fields.CustomForeignKey(to='common.PlanOfCharacteristic',
                                   on_delete=CUSTOM_PROTECT,
                                   verbose_name=_('Property'))
    field_type = fields.CustomCharField(max_length=255,
                                        choices=FieldTypeChoices.choices,
                                        default=FieldTypeChoices.char,
                                        verbose_name=_('Field data type'))
    owner = fields.CustomForeignKey(to="common.BaseModel",
                                    on_delete=CUSTOM_CASCADE,
                                    blank=False,
                                    null=True,
                                    related_name='poc_value',
                                    verbose_name=_('Owner record')
                                    )
    linked_field = fields.CustomForeignKey(to="common.BaseModel",
                                           on_delete=CUSTOM_CASCADE,
                                           blank=True,
                                           null=True,
                                           related_name='poc_values',
                                           verbose_name=_('The record referenced by the field')
                                           )
    date_field = fields.CustomDateField(null=True,
                                        blank=True,
                                        verbose_name=_('Value field Date'))
    date_time_field = fields.CustomDateTimeField(null=True,
                                                 blank=True,
                                                 verbose_name=_('Value field DateTime'))
    decimal_field = fields.CustomDecimalField(null=True,
                                              blank=True,
                                              max_digits=21,
                                              decimal_places=3,
                                              verbose_name=_('Value field Number'))
    string_field = fields.CustomCharField(null=True,
                                          blank=True,
                                          max_length=255,
                                          verbose_name=_('Value field String'))
    boolean_field = fields.CustomBooleanField(null=True,
                                              blank=True,
                                              verbose_name=_('Value field Boolean'))
    field_index = fields.CustomDecimalField(default=0,
                                            max_digits=21,
                                            decimal_places=3,
                                            verbose_name=_('The ordinal number of the value, when repeated'))
    subfield_index = fields.CustomDecimalField(default=0,
                                               max_digits=21,
                                               decimal_places=3,
                                               verbose_name=_(
                                                   'The ordinal number of the value, when repeated subfield'))

    def get_related_field_object(self, field):
        attribute_value = getattr(self, field)
        if attribute_value:
            return BaseModel.objects.super_get(attribute_value.pk)
        else:
            return '-'

    @property
    def owner_object(self):
        return self.get_related_field_object('owner')

    @property
    def linked_object(self):
        return self.get_related_field_object('linked_field')

    @property
    def field_type_to_field_mapping(self):
        return {
            FieldTypeChoices.char: 'string_field',
            FieldTypeChoices.date: 'date_field',
            FieldTypeChoices.date_time: 'date_time_field',
            FieldTypeChoices.decimal: 'decimal_field',
            FieldTypeChoices.boolean: 'boolean_field',
            FieldTypeChoices.foreign_key: 'linked_field',
        }

    @property
    def field_type_to_field_mapping_for_reprp(self):
        return {
            FieldTypeChoices.char: 'string_field',
            FieldTypeChoices.date: 'date_field',
            FieldTypeChoices.date_time: 'date_time_field',
            FieldTypeChoices.decimal: 'decimal_field',
            FieldTypeChoices.boolean: 'boolean_field',
            FieldTypeChoices.foreign_key: 'linked_object',
        }

    @property
    def field_value(self):
        mapping = self.field_type_to_field_mapping
        value = getattr(self, mapping.get(self.field_type))
        if self.field_type == FieldTypeChoices.foreign_key:
            if self.linked_field:
                value = {"id": str(self.linked_field.pk),
                         "string_view": self.linked_object.__str__()}
            else:
                value = {"id": "",
                         "string_view": ""}

        return value

    @property
    def field_value_to_repr(self):
        mapping = self.field_type_to_field_mapping_for_reprp
        value = getattr(self, mapping.get(self.field_type))
        return value

    class Meta:
        verbose_name = _('Plan Of Characteristic Value')
        verbose_name_plural = _('Plan Of Characteristic Values')


class AbstractRegisterModel(BaseAbstractModel):
    """
    Абстрактная модель для Регистров
    """

    class Meta:
        abstract = True

    registrar = fields.CustomForeignKey(to="common.BaseDocument",
                                        on_delete=CUSTOM_CASCADE,
                                        # editable=False,
                                        related_name='accumulation_records',
                                        verbose_name='Регистратор')
    organization = fields.CustomForeignKey(to='common.Organization',
                                           to_field='code',
                                           on_delete=CUSTOM_PROTECT,
                                           null=True,
                                           default='current',
                                           verbose_name=_('Организация'))
    period = fields.CustomDateField(verbose_name='Дата накладной')
    quantity = fields.CustomDecimalField(default=0,
                                         max_digits=21,
                                         decimal_places=3,
                                         verbose_name=_('Количество'))  # Количество
    amount = fields.CustomDecimalField(default=0,
                                       max_digits=21,
                                       decimal_places=2,
                                       verbose_name=_('Amount'))  # Сумма
    type_of_accumulation = fields.CustomIntegerField(default=1,
                                                     verbose_name='Тип накопления')
    phantom_quantity = fields.CustomDecimalField(default=0,
                                                 max_digits=21,
                                                 editable=False,
                                                 decimal_places=3,
                                                 verbose_name=_('Phantom Quantity'))  # фантомное Количество
    phantom_amount = fields.CustomDecimalField(default=0,
                                               max_digits=21,
                                               editable=False,
                                               decimal_places=2,
                                               verbose_name=_('Phantom Amount'))  # фантомная Сумма

    @classmethod
    def get_amount(cls, **kwargs):
        queryset = cls.objects.filter(**kwargs)
        return queryset.aggregate(
            total_amount=Sum('phantom_amount'))['total_amount']

    @classmethod
    def get_count(cls, **kwargs):
        queryset = cls.objects.filter(**kwargs)
        return queryset.aggregate(
            total_count=Sum('phantom_quantity'))['total_count']

    @classmethod
    def get_count_and_amount_by_kwargs(cls, **kwargs):
        """
        Получаем количество и сумму активов по параметрам из kwargs
        """
        return cls.get_count(**kwargs), cls.get_amount(**kwargs)

    def save(self, *args, **kwargs):
        self.phantom_quantity = self.quantity * self.type_of_accumulation
        self.phantom_amount = self.amount * self.type_of_accumulation
        super().save(*args, **kwargs)


class RegistrarBaseManager(CustomManager):
    """
    абстрактный менеджер, использвутся только для наследования,
    обязательно переопределять метод create_movement
    """

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        for obj in objs:
            obj.phantom_quantity = obj.quantity * obj.type_of_accumulation
            obj.phantom_amount = obj.amount * obj.type_of_accumulation
        data = super().bulk_create(objs, batch_size, ignore_conflicts)
        return data

    def get_document_data(self, document):
        return {'organization': document.organization,
                'registrar': document,
                'period': document.doc_date,
                }

    def create_movement(self, document, edition_part_values):
        """
        Метод создания записей в регистре по шапке документа и  таб. частям с mapping
        """
        pass


class AssetInWarehouseManager(RegistrarBaseManager):
    def create_movement(self, document, edition_part_values):
        """
        Метод менеджера Активов склада, для создания записей на основе документа + таб части
        в модели таб. части нужно указать классовый метод registrar_mapping, чтобы понимать
        какие поля таб части отностся к полям записи в регстр
        """
        document_data = self.get_document_data(document)
        mapping = edition_part_values.model.registrar_mapping()[self.model.__name__]
        if document.__class__.get_type_of_accumulation() == 1:
            self.create_receipt(document_data, edition_part_values, mapping)
        elif document.__class__.get_type_of_accumulation() == -1:
            self.create_expense(document_data, edition_part_values, mapping)
        elif document.__class__.is_transfer():
            self.create_transfer(document_data, edition_part_values, mapping)
        else:
            pass

    def create_receipt(self, document_data, edition_part_values, mapping):
        """
        Регистрация прихода
        """
        document_data['type_of_accumulation'] = 1
        for edition_part in edition_part_values:
            units = edition_part.units.all()
            for unit in units:
                self.create(asset_owner=getattr(edition_part, mapping['asset_owner']),
                            asset=unit,
                            quantity=1,
                            amount=getattr(edition_part, mapping['amount']),
                            warehouse=getattr(edition_part, mapping['warehouse'], ),
                            **document_data)

    def create_expense(self, document_data, edition_part_values, mapping):
        """
        Регистрация выбытия
        """
        document_data['type_of_accumulation'] = -1
        for edition_part in edition_part_values:
            self.create(asset_owner=getattr(edition_part, mapping['asset_owner']),
                        asset=getattr(edition_part, mapping['asset']),
                        quantity=getattr(edition_part, mapping['quantity']),
                        amount=getattr(edition_part, mapping['amount']),
                        warehouse=getattr(edition_part, mapping['warehouse'], ),
                        **document_data)

    def create_transfer(self, document_data, edition_part_values, mapping):
        """
        Регистрация перемещения
        """
        for edition_part in edition_part_values:
            tp_data = dict()
            tp_data['asset_owner'] = getattr(edition_part, mapping['asset_owner'])
            tp_data['asset'] = getattr(edition_part, mapping['asset'])
            tp_data['quantity'] = getattr(edition_part, mapping['quantity'])
            tp_data['amount'] = getattr(edition_part, mapping['amount'])
            tp_data.update(document_data)
            expense = self.create(warehouse=getattr(edition_part, mapping['warehouse'], ),
                                  type_of_accumulation=-1,
                                  **tp_data)

            receipt = self.create(warehouse=getattr(edition_part, mapping['recipient_warehouse']),
                                  type_of_accumulation=1,
                                  **tp_data)


class AssetInWarehouse(AbstractRegisterModel):
    """
    Запись регистра "Активы на складах"
    """
    objects = AssetInWarehouseManager()
    asset = fields.CustomForeignKey(to="common.BaseModel",
                                    on_delete=CUSTOM_CASCADE,
                                    # editable=False,
                                    related_name='registered',
                                    verbose_name='Актив')
    asset_owner = fields.CustomForeignKey(to="common.BaseModel",
                                          on_delete=CUSTOM_CASCADE,
                                          # editable=False,
                                          null=True,
                                          blank=True,
                                          related_name='registered_asset',
                                          verbose_name='Родитель актива')
    warehouse = fields.CustomForeignKey(to='catalogs.WarehouseModel', to_field='code', verbose_name=_('Warehouse'),
                                        null=True, on_delete=CUSTOM_PROTECT,
                                        )

    @classmethod
    def check_has_written_records(cls, edition_part_values):
        """
        Проверка перед записью в регистр, есть ли списаные записи в отправляемом списке
        """
        qs = cls.objects.filter(type_of_accumulation=-1).exclude(
            registrar__ct__model='editionunittransfermodel')  # TODO продумать запрпрос
        if hasattr(edition_part_values.model, 'unit'):
            units = edition_part_values.values('unit__id')
            qs = qs.filter(asset__in=units)
        else:
            qs = qs.filter(asset__in=edition_part_values.values_list('units', flat=True))
        result = qs.exists()

        if result:
            raise BadRequest([{'type': 'TPError',
                               'message': _('The list contains an already written-off record')}])

    @classmethod
    def get_count_and_amount_in_warehouse(cls, warehouse, asset_owner):
        """
        Получем количество активов на складе опрделенного типа
        Например для получения осттатка изданий на конкретном складе (EditionModel - owner у экзмеляра(Unit))
        Возращает количество активов и сумму
        """
        data = cls.get_count_and_amount_by_kwargs(warehouse=warehouse, asset_owner=asset_owner)
        return data

    class Meta:
        verbose_name = _('Register record asset in warehouse')
        verbose_name_plural = _('Assets in warehouse')


class CKEditorFileModel(BaseAbstractModel):
    file = fields.CustomForeignKey(
        to='common.File',
        null=True,
        blank=False,
        verbose_name=_('Файл'),
        on_delete=CUSTOM_CASCADE,
    )
    related_object = fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        verbose_name=_('Связанный объект'),
        on_delete=CUSTOM_CASCADE,
        related_name='ckeditor_files',
    )
    field_name = fields.CustomCharField(
        null=False,
        default='',
        max_length=31,
        blank=False,
        verbose_name=_('Имя поля'),
    )

    class Meta:
        verbose_name = _("Файл для CKEditor")
        verbose_name_plural = _("Файлы для CKEditor")
        unique_together = ('file', 'related_object', 'field_name',)


class TechnicalIsolatedCallsControlModel(models.Model):
    name = models.CharField(verbose_name='Название функции', max_length=50)
    date_started = models.DateTimeField(verbose_name='Дата и время запуска задачи',
                                        blank=True,
                                        null=True)
    is_started = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Запись контроля выполнения изолированных функций(техническая)'
        verbose_name_plural = 'Записи контроля выполнения изолированных функций(техническая)'


class TableSettingsModel(models.Model):
    profile = models.ForeignKey(to='users.ProfileModel', on_delete=CUSTOM_CASCADE, null=False)
    field1 = models.CharField(default='', max_length=255)
    field2 = models.CharField(default='', max_length=255)
    field3 = models.CharField(default='', max_length=255)
    value = models.JSONField()


class InterfaceModel(models.Model):
    """ Модель описания интерфейса роли """

    role = models.ForeignKey('users.C1RoleModel', on_delete=CUSTOM_CASCADE)
    interface = models.JSONField(blank=False)


class CustomThemeModel(BaseCatalog):
    """ Модель описания кастомных стилей проекта. В перспективе, будем делать возможность выбора темы пользователем """
    css_text = models.TextField(verbose_name='css-текст. Внимание! Следи за метлой. Валидатора корректности нет')


class CustomJSModel(BaseCatalog):
    """ Модель описания кастомных скриптов проекта. """
    js_text = models.TextField(verbose_name='JS-текст. Внимание! Следи за метлой. Валидатора корректности нет')


class TGMessageModel(BaseAbstractModel):
    message_id = models.BigIntegerField(null=True, blank=True)
    chat_id = models.BigIntegerField(null=True, blank=True)
    bot_id = fields.CustomCharField(null=True, blank=True, max_length=255)
    ref1 = fields.CustomForeignKey(BaseModel, on_delete=CUSTOM_SET_NULL,
                             null=True, blank=True,
                             related_name='tg_messages_ref1')
    ref2 = fields.CustomForeignKey(BaseModel, on_delete=CUSTOM_SET_NULL,
                             null=True, blank=True,
                             related_name='tg_messages_ref2')
    ref3 = fields.CustomForeignKey(BaseModel, on_delete=CUSTOM_SET_NULL,
                             null=True, blank=True,
                             related_name='tg_messages_ref3')
    ref4 = fields.CustomForeignKey(BaseModel, on_delete=CUSTOM_SET_NULL,
                             null=True, blank=True,
                             related_name='tg_messages_ref4')
    context = models.TextField(blank=True)
    is_notify = fields.CustomBooleanField(default=False)


def desktop_application_release_upload_path(instance, filename):
    _, extension = os.path.splitext(filename or '')
    normalized_extension = extension.lower() or '.exe'
    return os.path.join(
        'desktop',
        f'connect_gos24_desktop{normalized_extension}',
    ).replace('\\', '/')


class DesktopApplicationReleaseStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            self.delete(name)
        return name


class DesktopApplicationVersionModel(BaseAbstractModel):
    version = models.CharField(default='',max_length=25)
    target_url = models.CharField(max_length=1000,default='')
    release_file = fields.CustomFileField(
        upload_to=desktop_application_release_upload_path,
        storage=DesktopApplicationReleaseStorage(),
        max_length=1000,
        blank=True,
        null=True,
        verbose_name=_('Файл обновления'),
    )


class MentionModel(BaseAbstractModel):
    related_object = models.ForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='mention_users_rel',
        verbose_name=_('Связанный объект')
    )
    user = models.ForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='mention_users',
        verbose_name=_('Пользователь')
    )

    class Meta:
        verbose_name = _('Упоминание')
        verbose_name_plural = _('Упоминания')
        unique_together = (('related_object', 'user',),)
        ordering = ('user__user__last_name', 'user__user__first_name', 'user__user__middle_name',)
