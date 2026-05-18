import json
from uuid import UUID

from django.core.exceptions import ValidationError

from rest_framework import serializers

from common import serializers as common_serializers
from common import models as common_models
from common.page_config import form_fields

from . import models, utils


class PVHPropertyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PVHProperty
        fields = (
            'id',
            'code',
            'sort',
        )


class PVHPropertyThroughSerializer(serializers.ModelSerializer):
    property = PVHPropertyListSerializer()

    class Meta:
        model = models.PVHPropertyThrough
        fields = (
            'id',
            'name',
            'property',
            'widget',
            'condition',
        )


class PVHWriteMixin(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        models.PVHProperty.add_serializer_fields(self, self.Meta.model, required=False)
        pass

    def create(self, validated_data):
        pvh_fields = models.PVHProperty.remove_pvh_fields(validated_data, self.Meta.model)
        instance = super().create(validated_data)
        instance.create_property_values(pvh_fields)
        return instance

    def update(self, instance, validated_data):
        pvh_fields = models.PVHProperty.remove_pvh_fields(validated_data, self.Meta.model)
        instance = super().update(instance, validated_data)
        instance.property_values.all().delete()
        instance.create_property_values(pvh_fields)
        return instance


class PVHReadMixin(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        models.PVHProperty.add_serializer_fields(self, self.Meta.model, required=False)

    def to_representation(self, instance):
        instance._load_virtual_fields()
        data = super().to_representation(instance)
        pvh_data = dict()
        for key, value in data.items():
            if key.startswith('x_'):
                pvh_data[key] = value
        for key, value in pvh_data.items():
            data.pop(key)
        property_data = utils.get_pvh_property_data_for_instance(instance)
        if property_data:
            for each in property_data:
                if f'x_{each[0]}' in pvh_data:
                    try:
                        widget_type = each[2].get('type', 'Input')
                    except AttributeError:
                        widget_type = 'input'
                    data[f'x_{each[0]}'] = {
                        'value': pvh_data[f'x_{each[0]}'],
                        'name': each[1],
                        'widgetType': widget_type
                    }
        return data


class FastModelSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(read_only=False)
    name = serializers.CharField(required=False)
    code = serializers.CharField(required=False)

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.model = model

    class Meta:
        fields = ['id', 'name', 'code']

    def to_representation(self, instance):
        if not isinstance(instance, (common_models.BaseModel, UUID)):
            raise ValidationError('Допускаются только BaseModel и UUID BaseModel')

        if isinstance(instance, common_models.BaseModel):
            instance = instance.original_object

        if isinstance(instance, UUID):
            instance = common_models.BaseModel.objects.get(pk=instance)

        data = super().to_representation(instance)
        return data









# DEPRECATED -->>
class PVHSerializer(serializers.ModelSerializer):

    class Meta:
        model = common_models.BaseModel

        fields = (
            'id',
        )


# PlanOfCharacteristic
class PlanOfCharacteristicCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = common_models.PlanOfCharacteristic
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + [
            'field_type',
            # 'entity_type',
            'field_code',
            'subfield_code',
            'name',
            # 'repetitive',
            # 'required',
            'is_link_field',
            # 'field_linked_to',
            'description',
            'comment',
        ]

        validators = []


class PlanOfCharacteristicListSerializer(common_serializers.BaseCatalogListSerializer):
    field_linked_to = serializers.SerializerMethodField(read_only=True,
                                                        method_name='linked_to_str')

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = common_models.PlanOfCharacteristic
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + [
            'field_type',
            'entity_type',
            'field_code',
            'subfield_code',
            'name',
            'repetitive',
            'required',
            'field_linked_to',
            'description',
            'comment',
            'block',
        ]

    def linked_to_str(self, instance):
        has_filed_linked_to = getattr(instance, 'field_linked_to')
        if has_filed_linked_to:
            name = has_filed_linked_to.app_labeled_name
        else:
            name = '-'

        return {"name": name}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['block'] = instance.block_full_name
        return data


#################################################
#################################################
#################################################


class PlanOfCharacteristicBaseSerializer(serializers.ModelSerializer):
    """
    Сериалайзер собщими полями для групп полей\полей\независимых полей
    """
    required = serializers.BooleanField()
    repetitive = serializers.BooleanField()
    # type_for_front = serializers.CharField(default='GroupFields')
    type_for_front = serializers.CharField(default='MultiplyGroupFields')

    class Meta:
        model = common_models.PlanOfCharacteristic
        fields = [
            'name',
            'type_for_front',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['type'] = data.pop('type_for_front')
        data['multiply'] = json.loads(instance.repetitive.lower())
        return data


class PlanOfCharacteristicSubFieldsSerializer(PlanOfCharacteristicBaseSerializer):
    """
    Собираем поле
    PlanOfCharacteristic с entity_type = 'SUBFIELD' нааследованные от группы полей (entity_type = 'FIELD')
    PlanOfCharacteristic с entity_type = 'INDEPENDENT_FIELD' независимое поле, хранит subfield_code и field_Code
    """

    class Meta(PlanOfCharacteristicBaseSerializer.Meta):
        model = common_models.PlanOfCharacteristic
        fields = PlanOfCharacteristicBaseSerializer.Meta.fields + [
            'subfield_code',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        field_type = instance.field_type
        if field_type == 'Decimal':
            field_data = form_fields.DecimalFormField()
            field_data.decimal_config = form_fields.DecimalConfig()
            field_data.decimal_config.decimal_length = 3
            field_data.decimal_config.min_value = str(-10 ** 21)
            field_data.decimal_config.max_value = str(10 ** 21)
        elif field_type == 'FK':
            field_data = form_fields.ForeignKeyFormField()
            field_data.to_field = "id"
            field_data.key = instance.get_field_linked_to
            field_data.data_path = '/app_info/select_list/?model=' + field_data.key
        elif field_type == 'Char':
            field_data = form_fields.CharFieldFormField()
        elif field_type == 'Boolean':
            field_data = form_fields.BooleanFormField()
            field_data.default_check = False
            field_data.default_value = False
        elif field_type == 'Date':
            field_data = form_fields.DateFormField()
            field_data.current_date = False
        elif field_type == 'DateTime':
            field_data = form_fields.DateTimeFormField()
            field_data.current_date = False
        else:
            field_data = form_fields.CharFieldFormField()

        required_info = form_fields.RequiredRulesConfig()
        required_info.required = json.loads(instance.required.lower())
        field_data.name = instance.full_field_code
        field_data.title = instance.name
        field_data.rules_config.required = required_info
        field_data.field_name = ""
        field_data.disabled = False
        field_data_dict = field_data.get_dict()
        if field_type == 'FK':
            field_data_dict['defaultValue'] = None
            if instance.field_linked_to.model_class().is_enum():
                field_data_dict['actions'] = None
            else:
                field_data_dict['actions'] = {
                    "showAll": {
                        "tableKey": {
                            "name": instance.field_linked_to.model_class().get_page_name(action='list'),
                            "key": instance.get_field_linked_to,
                            "widget": "Default"
                        },
                        "tablePath": ""
                    },
                    "createOptions": {"key": "edit_" + instance.get_field_linked_to}}

        data.update(field_data_dict)
        if json.loads(instance.repetitive.lower()):
            new_data = PlanOfCharacteristicFieldSerializer(instance).data
            data['title'] = ''
            new_data['fieldInfo'] = [data]

            new_data.pop('subfields')
            data = new_data

        return data


class PlanOfCharacteristicFieldSerializer(PlanOfCharacteristicBaseSerializer):
    """
    Собирем группы полей
    PlanOfCharacteristic с entity_type = 'FIELD'
    """
    subfields = serializers.SerializerMethodField()

    class Meta(PlanOfCharacteristicBaseSerializer.Meta):
        model = common_models.PlanOfCharacteristic
        fields = PlanOfCharacteristicBaseSerializer.Meta.fields + [
            'field_code',
            'subfields',
            'collapse',
            'default_collapse',
        ]

    def get_subfields(self, instance):
        return PlanOfCharacteristicSubFieldsSerializer(instance.get_descendants().order_by(
            "field_code", 'subfield_code'), many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['class'] = ''
        data['defaultCollapse'] = data.pop('default_collapse')
        data['name'] = instance.field_code
        data['title'] = instance.name
        data['groupInline'] = False
        if json.loads(instance.repetitive.lower()):
            data['groupInline'] = True
            data['type'] = 'MultiplyGroupFields'

        if instance.entity_type == 'SUBFIELD':
            data['name'] = instance.full_field_code + '_group'
            data['groupInline'] = False

        if data['subfields']:
            data['fieldInfo'] = data.pop('subfields')
        return data


class PlanOfCharacteristicBlockSerializer(serializers.Serializer):
    """
    Собираем блок
    fields: Сериализуем группы полей
    independent_fields: Сериализуем независимые поля
    """
    name = serializers.CharField()
    title = serializers.CharField()
    type_for_front = serializers.CharField()
    fields = PlanOfCharacteristicFieldSerializer(many=True)
    independent_fields = PlanOfCharacteristicSubFieldsSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['headerTitle'] = data.pop('title')
        data['title'] = instance['block_code']
        data['type'] = data.pop('type_for_front')
        data['fieldInfo'] = data.pop('fields')
        independent_fields = data.pop('independent_fields')
        list(map(lambda x: data['fieldInfo'].append(x), independent_fields))  # Независимые поля добавляем в fieldInfo
        data['pageWidget'] = 'Default'
        data['navWidget'] = "NavForm"
        data['showAuthor'] = False
        data['showComment'] = False
        data['i18n'] = None
        fields_names = list(map(lambda x: x['name'], data['fieldInfo']))
        data['fields'] = {
            "create": fields_names,
            "update": fields_names,
        }
        data['pageConfig'] = {"headerButtons": []}
        title_field = {
            "type": "title",
            "class": "",
            "title": data['headerTitle'],
            "level": "h1",
        }
        data['fieldInfo'].insert(0, title_field)
        return data


class PlanOfCharacteristicValuesSerializer(serializers.ModelSerializer):
    """
    Значения полей ПВХ
    """

    class Meta:
        model = common_models.PlanOfCharacteristicValue
        fields = ['field_type', ]

    def to_representation(self, instance):
        data = {
            instance.prop.full_field_code: instance.field_value,

        }
        return data