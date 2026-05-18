from functools import reduce

from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType

from rest_framework import exceptions as drf_exceptions

from common import models as common_models

from . import models


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return reduce(_getattr, [obj] + attr.split('.'))


def get_pvh_property_data_for_instance(instance):
    qs = get_pvh_property_through_for_instance(instance)
    if qs:
        return qs.values_list('property__code', 'name', 'widget',)
    else:
        return None


def get_pvh_property_through_for_instance(instance):
    content_type = ContentType.objects.get_for_model(instance.__class__)
    pvh = models.PVH.objects.filter(content_type=content_type).first()
    if not pvh:
        return None
    attr_names = pvh.attr_names
    condition = dict()
    if attr_names:
        for attr_name in attr_names:
            condition[attr_name] = rgetattr(instance, attr_name)
    pvh_property_through = get_pvh_property_through_for_pvh(pvh, condition)
    return pvh_property_through


def get_pvh_property_through_for_pvh(pvh, condition: dict):
    lookup = dict()
    for key, value in condition.items():
        lookup[f'condition__{key}__contains'] = value
    properties_through = pvh.pvh_property_through.filter(
        Q(condition__isnull=True) | Q(**lookup)
    ).distinct().order_by('sort', )
    return properties_through


def set_characteristics_values(initial_data, instance):
    """
    используется при переопределнии create() и update() у ModelSerializer в !!! АТОМНОЙ ТРАНЗАКЦИИ !!!
    """
    plan_of_characteristics = common_models.PlanOfCharacteristic.objects.filter(
        appointment=ContentType.objects.get_for_model(instance.__class__))

    old_values = instance.poc_value.all()
    old_values.delete()  # удаляем страые значения ПВХ
    errors_list = list()
    not_repetitive_subfields = plan_of_characteristics.filter(entity_type='SUBFIELD',
                                                              parent__repetitive='False')
    # Обходим поля в группах полей без повторов
    for field in not_repetitive_subfields:
        field_code = field.field_code
        full_field_code = field.full_field_code
        initial_data_list = initial_data[field_code]
        sub_field_group_code = full_field_code + '_group'
        initial_data_dict = initial_data_list[0]  # т.к не повторяется всегда будет 1 елемент
        if field.repetitive == 'True':
            if sub_field_group_code in initial_data_dict:
                subfield_values = initial_data_dict[sub_field_group_code]
                for subfield_index in range(subfield_values.__len__()):  # получаем index повторения поля
                    field_value = subfield_values[subfield_index][full_field_code]
                    save_characteristic_value(instance, field, field_value, 0, subfield_index,
                                                   errors_list=errors_list)
        else:
            if full_field_code in initial_data_dict:
                field_value = initial_data_dict[full_field_code]
                save_characteristic_value(instance, field, field_value, errors_list=errors_list)
    # Получаем независимые поля
    independent_fields = plan_of_characteristics.filter(entity_type='INDEPENDENT_FIELD')
    for field in independent_fields:
        full_field_code = field.full_field_code
        if full_field_code in initial_data:
            field_value = initial_data[full_field_code]
            save_characteristic_value(instance, field, field_value, errors_list=errors_list)
    # Получаем группы полей, из них получим поля (детей)
    repetitive_characteristics_group_fields = plan_of_characteristics.filter(entity_type='FIELD',
                                                                             repetitive='True')
    # Обходим ПВХ повторяющихся гурпп полей
    for field_group in repetitive_characteristics_group_fields:
        field_group_code = field_group.field_code
        children = field_group.get_descendants()  # Получаем поля (entity_type = subfield) Группы полей
        if field_group_code in initial_data:
            field_group_initial_data = initial_data[
                field_group_code]  # словарь со знаяениями с фронта для данной группы полей
            for field in children:  # ищем зачения ПВХ в тех что пошли с фронта
                field_code = field.full_field_code
                for index in range(field_group_initial_data.__len__()):  # Получаем номера повторов групп полей
                    field_group_initial_dict = field_group_initial_data[index]
                    if field.repetitive == 'True':  # Проверяем поле, повторяется ли оно
                        sub_field_group_code = field_code + '_group'
                        if sub_field_group_code in field_group_initial_dict:
                            subfield_values = field_group_initial_dict[sub_field_group_code]
                            for subfield_index in range(subfield_values.__len__()):  # Получаем номер повтора полея
                                field_value = subfield_values[subfield_index][field_code]
                                save_characteristic_value(instance, field, field_value, index, subfield_index,
                                                               errors_list=errors_list)
                    elif field.repetitive == 'False' and field_code in field_group_initial_dict:
                        field_value = field_group_initial_dict[field_code]
                        save_characteristic_value(instance, field, field_value, index, errors_list=errors_list)

    if errors_list:
        raise drf_exceptions.ValidationError(errors_list)


def save_characteristic_value(instance, field, field_value, index=0, subfield_index=0, errors_list=None):
    """
    Сохранение одного значения ПВХ

    """

    is_required = field.required == 'True'
    is_empty_field = field_value == '' or field_value is None
    if is_required and is_empty_field:
        errors_list.append({'type': 'formError',
                            'message': 'Поле ' + field.name + ' в ' +
                                       field.block_full_name + ' обязательно для заполнения!'})
    elif errors_list:
        pass
    else:
        poc_value = common_models.PlanOfCharacteristicValue()
        poc_value.prop = field
        poc_value.field_type = field.field_type
        poc_value.owner = instance
        poc_value.field_index = index
        poc_value.subfield_index = subfield_index
        mapping = poc_value.field_type_to_field_mapping
        field_name = mapping.get(field.field_type)
        if not is_empty_field:
            if field_name == 'linked_field':
                poc_value.linked_field_id = field_value
            else:
                setattr(poc_value, field_name, field_value)
        poc_value.save()
        duplicate_field_name = field.duplicate_field_name if field.duplicate_field_name else ''

        if field.is_duplicate_field and hasattr(instance, duplicate_field_name):
            parent_delimiter = field.parent.delimiter if field.parent.delimiter else ''
            delimiter = field.delimiter
            # Записываем значение в поля у основной модели
            if index == 0:
                delimited_value = parent_delimiter + field_value
            else:
                delimited_value = getattr(instance, duplicate_field_name) + delimiter + field_value
            setattr(instance, duplicate_field_name, delimited_value)
            instance.save()


def get_pvh_data(instance):
    from .serializers import PlanOfCharacteristicValuesSerializer
    data = dict()
    model = instance.__class__
    if not model.has_characteristics_plan():
        return data
    poc_values = instance.poc_value.all().prefetch_related('prop')
    poc_independent_values = poc_values.filter(prop__entity_type='INDEPENDENT_FIELD')
    serialized_poc_independent_values = PlanOfCharacteristicValuesSerializer(poc_independent_values,
                                                                                         many=True).data
    data_fields, data_independent_fields = model.get_model_characteristics_fields()
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