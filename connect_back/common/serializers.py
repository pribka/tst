import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils.timezone import localdate
from django.utils.translation import get_language, gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError, BadRequest
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework import exceptions
from django.core.cache import cache

try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None

from users.serializers import AppUserSerializer, ProfileFilterSerializer

from .models import File
from . import models


class CodeRelatedField(serializers.RelatedField):
    def to_internal_value(self, data):
        return self.queryset.get(code=data)

    def to_representation(self, value):
        return value.code


class SelectListSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField(label=_('search code'))
    string_view = serializers.SerializerMethodField(label=_('String view'))

    def get_id(self, instance):
        return getattr(instance, 'id', None)

    def get_code(self, instance):
        return getattr(instance, 'code', None)

    def get_string_view(self, instance):
        return instance.__str__()

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        # для иерархических справочников MPTT
        try:
            is_leaf = instance.is_leaf_node()
        except:
            pass
        else:
            data['isLeaf'] = is_leaf
        if hasattr(instance, 'color'):
            data['color'] = instance.color
        get_logo = getattr(instance, 'get_select_list_logo_url', None)
        if callable(get_logo):
            data['logo'] = get_logo() or ''
        return data


class BaseModelSerializer(serializers.ModelSerializer):
    author = AppUserSerializer(label=_('Author'))
    string_view = serializers.SerializerMethodField(label=_('String view'))

    class Meta:
        model = models.BaseModel
        fields = [
            'id',
            'author',
            'created_at',
            'updated_at',
            'deleted_at',
            'is_active',
            'sort',
            'string_view'
        ]

    def get_string_view(self, instance):
        return instance.__str__()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'view' in self.context:
            action = self.context['view'].action
            if hasattr(instance._meta.model, 'has_characteristics_plan'):
                if instance._meta.model.has_characteristics_plan() and action == 'retrieve':
                    from pvh.serializers import PlanOfCharacteristicValuesSerializer
                    poc_values = instance.poc_value.all().prefetch_related('prop')
                    poc_independent_values = poc_values.filter(prop__entity_type='INDEPENDENT_FIELD')
                    serialized_poc_independent_values = PlanOfCharacteristicValuesSerializer(poc_independent_values,
                                                                                             many=True).data
                    data_fields, data_independent_fields = instance._meta.model.get_model_characteristics_fields()
                    group_field_list = []
                    for group_field in data_fields:
                        group_field_code = group_field.field_code
                        subfield_values = poc_values.filter(prop__entity_type='SUBFIELD',
                                                            prop__field_code=group_field_code)
                        indexes = subfield_values.values_list('field_index', flat=True).annotate(
                            total=Count('field_index')).order_by('field_index')
                        # indexes = subfield_values.values_list('field_index', 'subfield_index').annotate(total=Count('field_index'),total_subfield=Count('subfield_index'))
                        field_values = []
                        for index in indexes:
                            field_by_index = subfield_values.filter(field_index=index)

                            serialized_poc_value_dict = {}
                            for each in field_by_index:
                                if each.prop.repetitive == 'False':
                                    serialized_field = PlanOfCharacteristicValuesSerializer(each).data
                                    list(map(lambda x: serialized_poc_value_dict.__setitem__(x[0], x[1]),
                                             list(serialized_field.items())))
                                else:
                                    subfield_value = {each.prop.full_field_code: each.field_value}
                                    if each.prop.full_field_code + '_group' in serialized_poc_value_dict:
                                        serialized_poc_value_dict[each.prop.full_field_code + '_group'].append(
                                            subfield_value)
                                    else:
                                        serialized_poc_value_dict[each.prop.full_field_code + '_group'] = [
                                            subfield_value]

                            field_values.append(serialized_poc_value_dict)
                        if field_values:
                            group_field_list.append({group_field_code: field_values})

                    list(map(lambda x: data.update(x), serialized_poc_independent_values))
                    if group_field_list:
                        list(map(lambda x: data.update(x), group_field_list))
        return data


class BaseCatalogListSerializer(BaseModelSerializer):
    code = serializers.SerializerMethodField(label=_('search code'))

    class Meta(BaseModelSerializer.Meta):
        model = models.BaseCatalog
        fields = BaseModelSerializer.Meta.fields + [
            'name',
            'code',
            'is_predefined',
        ]

    def get_code(self, instance):
        return getattr(instance, 'code', None)

    def update(self, instance, validated_data):
        if instance.is_predefined:
            raise exceptions.PermissionDenied()  # TODO Создать общий вывод исключения.
        return super().update(instance, validated_data)


class BaseCatalogRetrieveSerializer(BaseModelSerializer):
    code = serializers.SerializerMethodField()

    class Meta:
        model = models.BaseCatalog
        fields = (
            'id',
            'name',
            'code',
            'created_at'
        )

    def get_code(self, instance):
        return getattr(instance, 'code', None)


# class BaseModelSetCharacteristic:
#     """
#     Класс для сохранения значений ПВХ (наследовать вместе с ModelSerializer)
#     """
#
#     def save_characteristic_value(self, instance, field, field_value, index=0, subfield_index=0, errors_list=None):
#         """
#         Сохранение одного значения ПВХ
#
#         """
#
#         is_required = field.required == 'True'
#         is_empty_field = field_value == '' or field_value is None
#         if is_required and is_empty_field:
#             errors_list.append({'type': 'formError',
#                                 'message': 'Поле ' + field.name + ' в ' +
#                                            field.block_full_name + ' обязательно для заполнения!'})
#         elif errors_list:
#             pass
#         else:
#             poc_value = models.PlanOfCharacteristicValue()
#             poc_value.prop = field
#             poc_value.field_type = field.field_type
#             poc_value.owner = instance
#             poc_value.field_index = index
#             poc_value.subfield_index = subfield_index
#             mapping = poc_value.field_type_to_field_mapping
#             field_name = mapping.get(field.field_type)
#             if not is_empty_field:
#                 if field_name == 'linked_field':
#                     poc_value.linked_field_id = field_value
#                 else:
#                     setattr(poc_value, field_name, field_value)
#             poc_value.save()
#             duplicate_field_name = field.duplicate_field_name if field.duplicate_field_name else ''
#
#             if field.is_duplicate_field and hasattr(instance, duplicate_field_name):
#                 parent_delimiter = field.parent.delimiter if field.parent.delimiter else ''
#                 delimiter = field.delimiter
#                 # Записываем значение в поля у основной модели
#                 if index == 0:
#                     delimited_value = parent_delimiter + field_value
#                 else:
#                     delimited_value = getattr(instance, duplicate_field_name) + delimiter + field_value
#                 setattr(instance, duplicate_field_name, delimited_value)
#                 instance.save()
#
#     def set_characteristics_values(self, instance):
#         """
#         используется при переопределнии create() и update() у ModelSerializer в !!! АТОМНОЙ ТРАНЗАКЦИИ !!!
#         """
#         initial_data = self.initial_data
#         plan_of_characteristics = models.PlanOfCharacteristic.objects.filter(
#             appointment=ContentType.objects.get_for_model(self.Meta.model))
#
#         old_values = instance.poc_value.all()
#         old_values.delete()  # удаляем страые значения ПВХ
#         errors_list = list()
#         not_repetitive_subfields = plan_of_characteristics.filter(entity_type='SUBFIELD',
#                                                                   parent__repetitive='False')
#         # Обходим поля в группах полей без повторов
#         for field in not_repetitive_subfields:
#             field_code = field.field_code
#             full_field_code = field.full_field_code
#             initial_data_list = initial_data[field_code]
#             sub_field_group_code = full_field_code + '_group'
#             initial_data_dict = initial_data_list[0]  # т.к не повторяется всегда будет 1 елемент
#             if field.repetitive == 'True':
#                 if sub_field_group_code in initial_data_dict:
#                     subfield_values = initial_data_dict[sub_field_group_code]
#                     for subfield_index in range(subfield_values.__len__()):  # получаем index повторения поля
#                         field_value = subfield_values[subfield_index][full_field_code]
#                         self.save_characteristic_value(instance, field, field_value, 0, subfield_index,
#                                                        errors_list=errors_list)
#             else:
#                 if full_field_code in initial_data_dict:
#                     field_value = initial_data_dict[full_field_code]
#                     self.save_characteristic_value(instance, field, field_value, errors_list=errors_list)
#         # Получаем независимые поля
#         independent_fields = plan_of_characteristics.filter(entity_type='INDEPENDENT_FIELD')
#         for field in independent_fields:
#             full_field_code = field.full_field_code
#             if full_field_code in initial_data:
#                 field_value = initial_data[full_field_code]
#                 self.save_characteristic_value(instance, field, field_value, errors_list=errors_list)
#         # Получаем группы полей, из них получим поля (детей)
#         repetitive_characteristics_group_fields = plan_of_characteristics.filter(entity_type='FIELD',
#                                                                                  repetitive='True')
#         # Обходим ПВХ повторяющихся гурпп полей
#         for field_group in repetitive_characteristics_group_fields:
#             field_group_code = field_group.field_code
#             children = field_group.get_descendants()  # Получаем поля (entity_type = subfield) Группы полей
#             if field_group_code in initial_data:
#                 field_group_initial_data = initial_data[
#                     field_group_code]  # словарь со знаяениями с фронта для данной группы полей
#                 for field in children:  # ищем зачения ПВХ в тех что пошли с фронта
#                     field_code = field.full_field_code
#                     for index in range(field_group_initial_data.__len__()):  # Получаем номера повторов групп полей
#                         field_group_initial_dict = field_group_initial_data[index]
#                         if field.repetitive == 'True':  # Проверяем поле, повторяется ли оно
#                             sub_field_group_code = field_code + '_group'
#                             if sub_field_group_code in field_group_initial_dict:
#                                 subfield_values = field_group_initial_dict[sub_field_group_code]
#                                 for subfield_index in range(subfield_values.__len__()):  # Получаем номер повтора полея
#                                     field_value = subfield_values[subfield_index][field_code]
#                                     self.save_characteristic_value(instance, field, field_value, index, subfield_index,
#                                                                    errors_list=errors_list)
#                         elif field.repetitive == 'False' and field_code in field_group_initial_dict:
#                             field_value = field_group_initial_dict[field_code]
#                             self.save_characteristic_value(instance, field, field_value, index, errors_list=errors_list)
#
#         if errors_list:
#             raise BadRequest(errors_list)


class BaseCatalogCUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BaseCatalog
        fields = [
            # 'id',
            'name',
        ]

    def to_representation(self, instance):
        data = BaseCatalogListSerializer(instance).data
        if instance.has_characteristics_plan():
            poc_values = instance._meta.model.get_model_characteristics_subfields()
            for poc_value in poc_values:
                data[poc_value.full_field_code] = self.context.get(poc_value.full_field_code)
        return data

    def create(self, validated_data):
        with transaction.atomic():
            result = super().create(validated_data)
            from pvh.utils import set_characteristics_values
            set_characteristics_values(self.initial_data, result)
        return result

    def update(self, instance, validated_data):
        if instance.is_predefined:
            raise exceptions.ValidationError(_('This record is predefined'))
        with transaction.atomic():
            data = super().update(instance, validated_data)
            from pvh.utils import set_characteristics_values
            set_characteristics_values(self.initial_data, instance)
        return data


class FileListSerializer(serializers.ModelSerializer):
    file_type = serializers.SerializerMethodField(label=_('File type'))
    path = serializers.SerializerMethodField()

    class Meta(BaseCatalogListSerializer.Meta):
        model = models.File
        fields = (
            'upload',
            'size',
            'extension',
            'mime_type',
            'file_type',
            'is_image',
            'path',
        )

    def get_file_type(self, instance):
        return BaseCatalogRetrieveSerializer(instance.mime_type.file_type).data

    def get_path(self, instance):
        return instance.absolute_url


class FileCreateSerializer(BaseCatalogCUDSerializer):
    class Meta(BaseCatalogCUDSerializer.Meta):
        model = models.File
        fields = (*BaseCatalogCUDSerializer.Meta.fields, 'upload')

    def to_representation(self, instance):
        return FileListSerializer(instance).data


class FileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.File
        fields = (
            'id',
            'name',
            'description'
        )

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        cache.delete_pattern(f'CachedFileAndFolderSerializer_{instance.pk}_ro_*')
        cache.delete('CachedAppFileSerializer_' + str(instance.pk))
        return instance

    def to_representation(self, instance):
        return AppFileSerializer(instance).data


class MimeTypeListSerializer(BaseCatalogListSerializer):
    file_type = BaseCatalogListSerializer(label=_('File type'))

    class Meta(BaseCatalogListSerializer):
        model = models.MimeType
        fields = BaseCatalogListSerializer.Meta.fields + ['file_type']


class MimeTypeCUDSerializer(BaseCatalogCUDSerializer):
    class Meta(BaseCatalogCUDSerializer.Meta):
        model = models.MimeType
        fields = ['file_type']

    def to_representation(self, instance):
        return MimeTypeListSerializer(instance).data


class BaseDocumentListSerializer(BaseModelSerializer):
    organization = BaseCatalogListSerializer(label=_('Организация'))
    locked = serializers.SerializerMethodField(label=_('Locked'))

    class Meta(BaseModelSerializer.Meta):
        model = models.BaseDocument
        fields = BaseModelSerializer.Meta.fields + [
            'organization',
            'doc_num',
            'doc_date',
            'is_posted',
            'locked',
        ]

    def get_locked(self, instance):
        return getattr(instance, 'locked', None)


class BaseDocumentDetailSerializer(BaseModelSerializer):
    organization = BaseCatalogListSerializer(label=_('Организация'))
    locked = serializers.SerializerMethodField(label=_('Locked'))

    class Meta(BaseModelSerializer.Meta):
        model = models.BaseDocument
        fields = BaseModelSerializer.Meta.fields + [
            'organization',
            'doc_num',
            'doc_date',
            'is_posted',
            'locked',
            'comment',
        ]

    def get_locked(self, instance):
        return instance.get_data_about_locking()


class BaseDocumentCUDSerializer(serializers.ModelSerializer):
    doc_num = serializers.CharField(required=False, allow_blank=True, default="", max_length=36,
                                    label=_('Document number'))
    doc_date = serializers.DateField(required=False, allow_null=True, label=_('Document date'))
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000, label=_('Comment'), )

    def validate_doc_date(self, data):
        if not data:
            data = localdate()
        return data

    class Meta:
        model = models.BaseDocument
        fields = [
            # 'id',
            'doc_num',
            'doc_date',
            'comment',
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            result = super().update(instance, validated_data)
            self.set_tabular_parts(instance)
            self.set_characteristics_values(instance)
            to_post = self.initial_data.get('to_post')
            if isinstance(to_post, bool):
                instance.set_is_posted(to_post)
                instance.save()
        return result

    def create(self, validated_data):
        with transaction.atomic():
            result = super().create(validated_data)
            self.set_tabular_parts(result)
            self.set_characteristics_values(result)
            to_post = self.initial_data.get('to_post')
            if isinstance(to_post, bool) and to_post is True:
                result.set_is_posted(to_post)
                result.save()
        return result

    def set_tabular_parts(self, instance):
        initial_data = self.initial_data
        tabular_parts = self.Meta.model.get_tabular_parts()
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
                                raise exceptions.ValidationError(f'Запись табличной части {each.get("id")} не найдена')
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
                    self.context[tp_attr] = {
                        "add": create_list_result,
                        "edit": edit_list_result,
                        "delete": delete_list_result,
                    }

    def to_representation(self, instance):
        data = BaseDocumentDetailSerializer(instance=instance).data
        for tp_attr, model in instance.get_tabular_parts().items():
            data[tp_attr] = self.context.get(tp_attr)
        if instance.has_characteristics_plan():
            poc_values = instance._meta.model.get_model_characteristics_subfields()
            for poc_value in poc_values:
                data[poc_value.full_field_code] = self.context.get(poc_value.full_field_code)
        return data


class IndividualSerializer(BaseCatalogListSerializer):
    class Meta(BaseCatalogListSerializer.Meta):
        model = models.Individual
        fields = BaseCatalogListSerializer.Meta.fields + ['iin']


class IndividualDetailSerializer(IndividualSerializer):
    class Meta(IndividualSerializer.Meta):
        fields = IndividualSerializer.Meta.fields + ['comment']


class IndividualCUDSerializer(BaseCatalogCUDSerializer):
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000, label=_('Comment'), )

    class Meta(BaseCatalogCUDSerializer):
        model = models.Individual
        fields = (*BaseCatalogCUDSerializer.Meta.fields, 'iin', 'comment')
        validators = []

    def to_representation(self, instance):
        return IndividualDetailSerializer(instance).data


class IsActiveSetSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=models.BaseModel.objects.all(), required=True)
    is_active = serializers.BooleanField(required=True)


class IsPostedSetSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=models.BaseDocument.objects.all(), required=True)
    is_posted = serializers.BooleanField(required=True)


class FilterValuesSerailizer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ()

    def to_representation(self, instance):
        if instance._meta.label != 'users.ProfileModel':
            data = super().to_representation(instance)
            if instance._meta.label == 'users.CustomUser':
                data['full_name'] = instance.profile.full_name
                data['avatar'] = ''
                # TODO расскоментировать или переписать когда появится поле аватар
                # if instance.profile.avatar:
                #     data['avatar'] = instance.profilemodel.avatar.absolute_url
            return data
        else:
            return ProfileFilterSerializer(instance).data


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FileType
        fields = (
            'name',
            'icon',
        )


class AppFileSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    file_type = FileTypeSerializer(source='mime_type.file_type')
    obj_type = serializers.CharField(default='file')

    def get_content_type(self, instance):
        return getattr(instance, 'mime_type_id', '')

    def get_path(self, instance):
        return instance.author_url

    class Meta:
        model = File
        fields = (
            'id',
            'name',
            'content_type',
            'extension',
            'path',
            'size',
            'is_image',
            'is_video',
            'is_audio',
            'is_voice',
            'file_type',
            'is_dynamic',
            'description',
            'obj_type',
        )


class CachedAppFileSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, models.File):
            instance_pk = instance.pk
        else:
            instance_pk = instance
        data = cache.get('CachedAppFileSerializer_' + str(instance_pk))
        if not data:
            obj = models.File.objects.get(pk=instance_pk)
            data = AppFileSerializer(instance=obj).data
            cache.set('CachedAppFileSerializer_' + str(instance_pk), data, timeout=None)
        return data


class FolderCreateSerializer(serializers.ModelSerializer):
    obj_type = serializers.CharField(default='folder', read_only=True)

    class Meta:
        model = models.FolderModel
        fields = (
            'id',
            'name',
            'parent',
            'related_object',
            'description',
            'obj_type',
        )


class FolderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FolderModel
        fields = (
            'id',
            'name',
            'description'
        )

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        cache.delete_pattern(f'CachedFileAndFolderSerializer_{instance.pk}_ro_*')
        cache.delete('CachedBaseFolderSerializer_' + str(instance.pk))
        return instance


class BaseFolderSerializer(serializers.ModelSerializer):
    obj_type = serializers.CharField(default='folder')
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = models.FolderModel
        fields = (
            'id',
            'name',
            'obj_type',
            'description',
            'has_children',
        )

    def get_has_children(self, instance):
        return not instance.is_leaf_node()


class CachedBaseFolderSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, models.FolderModel):
            instance_pk = instance.pk
        else:
            instance_pk = instance
        data = cache.get('CachedBaseFolderSerializer_' + str(instance_pk))
        if not data:
            obj = models.FolderModel.objects.get(pk=instance_pk)
            data = BaseFolderSerializer(instance=obj).data
            cache.set('CachedBaseFolderSerializer_' + str(instance_pk), data, timeout=None)
        return data


class FileAndFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BaseCatalog
        fields = (
            'id',
        )

    def to_representation(self, instance):
        file_ct_id = self.context.get('file_ct_id')
        if not file_ct_id:
            file_ct_id = ContentType.objects.get_for_model(models.File).pk
            self.context['file_ct'] = file_ct_id
        folder_ct_id = self.context.get('folder_ct_id')
        if not folder_ct_id:
            folder_ct_id = ContentType.objects.get_for_model(models.FolderModel).pk
            self.context['folder_ct_id'] = folder_ct_id
        ct_id = instance['ct']
        if ct_id == file_ct_id:
            data = CachedAppFileSerializer(instance['pk'], context=self.context).data
        elif ct_id == folder_ct_id:
            data = CachedBaseFolderSerializer(instance['pk']).data
        else:
            data = {}
        return data


class CachedBaseModelSerializer(serializers.Serializer):
    """Универсальный кэширующий сериализатор моделей, унаследованных от BaseModel."""
    def __init__(self, *args, serializer_class=None, **kwargs):
        self.serializer_class = serializer_class
        super().__init__(*args, **kwargs)

    @staticmethod
    def build_cache_key(serializer_class_name, instance_pk, lang):
        return f"{serializer_class_name}_{lang}_{instance_pk}"

    def to_representation(self, instance):
        instance_pk = str(instance.pk if hasattr(instance, 'pk') else instance)
        lang = get_language()
        cache_key = self.build_cache_key(self.serializer_class.__name__, instance_pk, lang)

        data = cache.get(cache_key)
        if data is not None:
            return data

        base_obj = models.BaseModel.objects.get(pk=instance_pk)
        original_object = base_obj.original_object

        serializer = self.serializer_class(original_object, context=self.context)
        data = serializer.data
        cache.set(cache_key, data, timeout=timedelta(days=1).total_seconds())
        return data


class CachedBaseCatalogSerializer(serializers.Serializer):
    """
    Универсальный кэширующий сериализатор моделей, унаследованных от BaseCatalog.
    Используется для связи по code
    """

    def __init__(self, *args, serializer_class=None, model=None, **kwargs):
        self.serializer_class = serializer_class
        self.model = model
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        instance_pk = str(instance.code if hasattr(instance, 'code') else instance)
        lang = get_language()
        cache_key = f"{self.serializer_class.__name__}_{lang}_{instance_pk}"

        data = cache.get(cache_key)
        if data is not None:
            return data

        original_object = self.model.objects.get(code=instance_pk)

        serializer = self.serializer_class(original_object)
        data = serializer.data
        cache.set(cache_key, data, timeout=timedelta(days=1).total_seconds())
        return data


class RelatedObjectSerializer(serializers.Serializer):
    """Сериализатор для BaseModel, когда он является ссылкой related_object."""
    
    def to_representation(self, instance):
        if not instance:
            return None
        
        related_object = instance.original_object
        return {
            'id': str(related_object.pk),
            'name': str(related_object),
            'type': related_object.get_label()
        }
