from common.page_config.base_model.forms import ModelConfig, BaseConfig, FormGroupFields
from common.models import PlanOfCharacteristicValue, PlanOfCharacteristic


class BaseCharacteristicSubField(BaseConfig):  # TODO
    characteristic_instance = PlanOfCharacteristic()
    subfield_code = ''
    index = 0
    owner_model = None


class BaseCharacteristicFieldGroup(FormGroupFields):  # TODO
    characteristic_instance = PlanOfCharacteristic()
    multiply = False
    field_info = BaseCharacteristicSubField()
    owner_model = None


class BaseCharacteristicBlock(BaseConfig):
    name = ''
    title = ''
    type_for_front = ''
    block_code = ''
    owner_model = None
    fields = BaseCharacteristicFieldGroup()
    independent_fields = BaseCharacteristicSubField()
    nav_widget = "NavForm"
    page_widget = 'Default'
    show_author = False
    show_comment = False
    i18n = None
    page_config = {}

    def get_dict(self):
        result = {}
        result['name'] = self.name
        result['title'] = self.title
        result['type'] = self.type_for_front
        result['fieldInfo'] = []  # self.fields + self.independent_fields
        result['pageWidget'] = self.page_widget
        result['navWidget'] = self.nav_widget
        result['showAuthor'] = self.show_author
        result['showComment'] = self.show_comment
        result['i18n'] = self.i18n
        fields_names = list(map(lambda x: x['name'], result['fieldInfo']))
        result['fields'] = {
            "create": fields_names,
            "update": fields_names,
        }
        result['pageConfig'] = {"headerButtons": []}
        return result

    def get_list(self):
        blocks_choices = PlanOfCharacteristic.BlockChoices.choices
        blocks = []
        characteristics, independent_fields = self.owner_model.get_model_characteristics_fields()
        for choice_code, choice_name in blocks_choices:
            block_characteristic = characteristics.filter(block=choice_code)
            independent_fields_blocks = independent_fields.filter(block=choice_code)  # TODO
        return blocks


class BaseCharacteristicForm(BaseConfig):
    title = 'Каталогизация'
    name: str = ''
    type_key = 'form'
    nav_widget = 'NavForm'
    page_widget = 'TableForm'
    blocks = BaseCharacteristicBlock()
    owner_model = None

    def get_dict(self):
        data = {
            'title': self.title,
            'name': self.name,
            'type': self.type_key,
            'navWidget': self.nav_widget,
            'pageWidget': self.page_widget,
            'editablePart': self.blocks.get_dict(),
        }
        return data
