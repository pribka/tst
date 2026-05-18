from django.utils.translation import gettext as _
from django.core.validators import DecimalValidator

from .common import BaseConfig, SetConfig, empty_func


class BaseFormFieldConfig(BaseConfig):
    field = None

    def set_field(self, field):
        self.field = field
        return self


class FormFieldSet(SetConfig):
    field = None

    def set_field(self, field):
        self.field = field
        for instance in self.instances:
            getattr(getattr(self, instance), 'set_field', empty_func)(field)
        return self


class BaseRulesConfig(BaseFormFieldConfig):
    message: str = ''
    trigger: str = 'change'


class RequiredRulesConfig(BaseRulesConfig):
    required: bool = False
    message = _('Required to fill')

    def set_field(self, field):
        super().set_field(field)
        self.required = not field.blank

    def get_dict(self):
        data = {
            'required': self.required,
            'message': self.message,
            'trigger': self.trigger
        }
        return data


class LengthRulesConfig(BaseRulesConfig):
    min_length: int = 0
    max_length: int = 255

    def set_field(self, field):
        super().set_field(field)
        self.max_length = field.max_length
        self.message = _(f'Minimum {self.min_length} characters, maximum {self.max_length} characters')

    def get_dict(self):
        data = {
            "min": 0,
            "max": self.max_length,
            "message": self.message,
            "trigger": self.trigger
        }
        return data


class BaseFormField(BaseFormFieldConfig):
    css_class: str = ''
    name: str = ''
    rules_config = FormFieldSet(required=RequiredRulesConfig(), instances=('required',))
    title: str = ''
    field_name: str = ''
    obj_type: str = ''
    disabled: bool = False
    placeholder: str = ''
    size: str = 'default'
    widget: str = ''
    default_value = None
    update: bool = False

    def set_field(self, field):
        super().set_field(field)
        if field.default is not None and not callable(field.default):
            self.default_value = field.default
        self.name = field.name
        self.title = field.verbose_name
        self.rules_config.set_field(field)
        return self

    def get_dict(self):
        data = {
            "class": self.css_class,
            "name": self.name,
            "title": self.title,
            "fieldName": self.field_name,
            "type": self.obj_type,
            "update": self.update,
            "rulesConfig": self.rules_config.get_dict(),
            "widgetConfig": {
                "disabled": self.disabled,
                "placeholder": self.placeholder,
                "size": self.size,
                "widget": self.widget
            }
        }
        if self.default_value is not None:
            data['defaultValue'] = self.default_value
        return data


class BooleanFormField(BaseFormField):
    default_check: bool = False
    default_value: bool = False
    obj_type: str = 'switch'
    widget: str = 'WidgetSwitch'

    def set_field(self, field):
        super().set_field(field)
        self.default_check = field.default

    def get_dict(self):
        data = super().get_dict()
        data['defaultCheck'] = self.default_check
        data['defaultValue'] = self.default_value
        return data


class CharFieldFormField(BaseFormField):
    obj_type: str = 'string'
    widget: str = 'WidgetString'
    rules_config = FormFieldSet(required=RequiredRulesConfig(), length=LengthRulesConfig(),
                                instances=('required', 'length'))


class TextAreaFormField(BaseFormField):
    obj_type: str = 'textarea'
    widget: str = 'WidgetTextarea'
    min_rows: int = 5
    max_rows: int = 10

    def get_dict(self):
        data = super().get_dict()
        data['autoSize'] = {'minRows': self.min_rows,
                            'maxRows': self.max_rows}
        return data


class DateFormField(BaseFormField):
    obj_type: str = 'date'
    current_date: bool = True
    widget: str = 'WidgetString'
    date_format: str = 'DD-MM-YYYY'
    placeholder: str = '__-__-____'

    def set_field(self, field):
        super().set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['currentDate'] = self.current_date
        data['dateFormat'] = self.date_format
        return data


class DateTimeFormField(BaseFormField):
    obj_type: str = 'datetime'
    current_date: bool = True
    widget: str = 'WidgetString'
    date_format: str = 'DD-MM-YYYY HH:mm'
    placeholder: str = '__-__-____ __:__'

    def set_field(self, field):
        super().set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['currentDate'] = self.current_date
        data['dateFormat'] = self.date_format
        return data


class FileFormField(BaseFormField):
    obj_type: str = 'file'
    widget: str = 'WidgetFile'
    multiple: bool = False
    max_files: int = 1
    list_type = 'Text'
    support_formats: tuple = tuple()
    max_file_size: int = 5

    def get_dict(self):
        data = {
            "class": self.css_class,
            "name": self.name,
            "title": self.title,
            "fieldName": self.field_name,
            "type": self.obj_type,
            "update": self.update,
            "rulesConfig": self.rules_config.get_dict(),
            "widgetConfig": {
                "widget": self.widget,
                "multiple": self.multiple,
                "maxFiles": self.max_files,
                "listType": self.list_type,
                "supportFormats": self.support_formats,
                "maxFileSize": self.max_file_size,
                "disabled": self.disabled,
            }
        }
        return data


class DecimalConfig(BaseFormFieldConfig):
    decimal_length = 0
    min_value: str = '0'
    max_value: str = '0'

    def set_field(self, field):
        super().set_field(field)
        self.decimal_length = getattr(field, 'decimal_places', 0)
        for each in field.validators:
            if isinstance(each, DecimalValidator):
                self.min_value = str(-10 ** each.max_digits)
                self.max_value = str(10 ** each.max_digits)

    def get_dict(self):
        data = {
            'decimalLength': self.decimal_length,
            'minValue': self.min_value,
            'maxValue': self.max_value,
        }
        return data


class DecimalFormField(BaseFormField):
    obj_type = 'decimal'
    widget = 'WidgetDecimal'
    decimal_config = DecimalConfig()

    def set_field(self, field):
        super().set_field(field)
        self.decimal_config.set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['decimalConfig'] = self.decimal_config.get_dict()
        return data


class IntegerFormField(BaseFormField):
    obj_type = 'integer'
    widget = 'integer'
    min_value: str = '-2147483648'
    max_value: str = '2147483647'
    placeholder = '0'

    def set_field(self, field):
        super().set_field(field)
        for each in field.validators:
            if each.code == 'min_value':
                self.min_value = str(each.limit_value)
            elif each.code == 'max_value':
                self.max_value = str(each.limit_value)

    def get_dict(self):
        data = super().get_dict()
        data['minValue'] = self.min_value
        data['maxValue'] = self.max_value
        return data


class TableKeyFormFieldConfig(BaseFormFieldConfig):
    name: str = ''
    key: str = ''
    widget: str = 'Default'

    def set_field(self, field):
        super().set_field(field)
        remote_field_model = getattr(field.remote_field, 'model', None)
        if remote_field_model:
            self.name = remote_field_model.get_page_name(action='list')
            self.key = remote_field_model.get_label()

    def get_dict(self):
        data = {
            'name': self.name,
            'key': self.key,
            'widget': self.widget,
        }
        return data


class ShowAllFormFieldConfig(BaseFormFieldConfig):
    table_key = TableKeyFormFieldConfig()
    table_path: str = ''

    def set_field(self, field):
        super().set_field(field)
        self.table_key.set_field(field)

    def get_dict(self):
        data = {
            'tableKey': self.table_key.get_dict(),
            'tablePath': self.table_path,
        }
        return data


class CreateOptionsFormFieldConfig(BaseFormFieldConfig):
    key: str = ''

    def set_field(self, field):
        super().set_field(field)
        try:
            self.key = f"edit_{field.remote_field.model.get_label()}"
        except AttributeError:
            pass

    def get_dict(self):
        data = {
            'key': self.key
        }
        return data


class ActionsForeignKey(BaseFormFieldConfig):
    show_all = ShowAllFormFieldConfig()
    create_options = CreateOptionsFormFieldConfig()

    def set_field(self, field):
        super().set_field(field)
        self.show_all.set_field(field)
        self.create_options.set_field(field)

    def get_dict(self):
        data = {
            'showAll': self.show_all.get_dict(),
            'createOptions': self.create_options.get_dict()
        }
        return data


class ForeignKeyFormField(BaseFormField):
    obj_type = 'select'
    divider: str = ''
    to_field: str = ''
    to_name: str = 'string_view'
    key: str = ''
    data_path: str = ''
    widget: str = 'WidgetSelect'
    actions = ActionsForeignKey()
    filters: list = None

    def set_field(self, field):
        super().set_field(field)
        try:
            to_field = field.to_fields[0]
        except KeyError:
            to_field = 'id'
        if to_field is None:
            to_field = 'id'
        self.to_field = to_field
        remote_field_model = getattr(field.remote_field, 'model', None)
        if remote_field_model:
            self.key = remote_field_model.get_label()
            self.data_path = f"/app_info/select_list/?model={self.key}"
        try:
            is_enum = remote_field_model.is_enum()
        except AttributeError:
            is_enum = False
        if is_enum is False:
            self.actions.set_field(field)
        else:
            self.actions = None

    def get_dict(self):
        data = super().get_dict()
        data['divider'] = self.divider
        data['toField'] = self.to_field
        data['toName'] = self.to_name
        data['key'] = self.key
        data['dataPath'] = self.data_path
        try:
            actions_dict = self.actions.get_dict()
        except AttributeError:
            actions_dict = None
        data['actions'] = actions_dict
        if self.filters:
            data['filters'] = self.filters
        return data
