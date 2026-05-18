import re
from django.db.models import NOT_PROVIDED
from common.page_config import BaseFormFieldConfig, DecimalConfig


class BaseFilterField(BaseFormFieldConfig):
    """is_exclude - признак, что можно фильтровать это поле по исключению."""
    name: str = ''
    obj_type: str = ''
    verbose_name: str = ''
    is_exclude: bool = True
    widget_type: str = ''
    mode: str = 'tags'

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        if not self.obj_type:
            self.obj_type = field.get_internal_type()
        self.verbose_name = field.verbose_name
        return self

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
            }
        }
        return data


class CharFilterField(BaseFilterField):
    widget_type: str = 'Input'


class DateTimeFilterField(BaseFilterField):
    widget_type: str = 'DateTime'
    time: bool = True
    date_format: str = 'DD.MM.YYYY HH:mm'
    placeholder: str = '__.__.____ __:__'
    currentDate: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        self.verbose_name = field.verbose_name
        return self

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "time": self.time,
                "currentDate": self.currentDate,
                "dateFormat": self.date_format,
                "placeholder": self.placeholder
            }
        }
        return data


class DateFilterField(BaseFilterField):
    widget_type: str = 'Date'
    time: bool = False
    date_format: str = 'DD.MM.YYYY'
    placeholder: str = '__.__.____'
    currentDate: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        self.verbose_name = field.verbose_name
        return self

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "time": self.time,
                "currentDate": self.currentDate,
                "dateFormat": self.date_format,
                "placeholder": self.placeholder
            }
        }
        return data


class ForeignKeyFilterField(BaseFilterField):
    widget_type: str = 'Select'
    model: str = ''
    to_field: str = ''
    filters: list = []

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        self.verbose_name = field.verbose_name
        try:
            self.model = field.remote_field.model.get_label()
        except AttributeError:
            self.model = field.model
        to_field = field.to_fields[0]
        if to_field is None:
            to_field = 'id'
        self.to_field = to_field
        return self

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "model": self.model,
                "toField": self.to_field,
            }
        }
        if self.filters:
            data["widget"]["filters"] = self.filters
        return data


class ChoiceFilterField(BaseFilterField):
    widget_type: str = 'Select'
    choices: tuple = tuple()
    to_field: str = 'id'

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        self.verbose_name = field.verbose_name
        if field.choices:
            self.choices = field.choices
        else:
            self.choices = tuple()
        return self

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "toField": self.to_field,
                "choices": [{'id': choice[0], 'code': None, 'string_view': choice[1]} for choice in self.choices]
            }
        }
        return data


class BooleanFilterField(BaseFilterField):
    widget_type: str = 'IsActiveField'


class IntegerFilterField(BaseFilterField):
    widget_type: str = 'Integer'
    min_value: str = '-2147483648'
    max_value: str = '2147483647'
    placeholder = '0'
    default_value: int = 0

    def set_field(self, field):
        super().set_field(field)
        if field.default is not None and not field.default == NOT_PROVIDED:
            self.placeholder = str(field.default)
            self.default_value = field.default
        for each in field.validators:
            if each.code == 'min_value':
                self.min_value = str(each.limit_value)
            elif each.code == 'max_value':
                self.max_value = str(each.limit_value)

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "minValue": self.min_value,
                "maxValue": self.max_value,
                "defaultValue": self.default_value
            }
        }
        return data


class UserFilterField(BaseFilterField):
    widget_type: str = 'UserSelect'
    model: str = 'users.CustomUser'

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "model": self.model
            }
        }
        return data


class ProfileFilterField(BaseFilterField):
    widget_type: str = 'UserSelect'
    model: str = 'users.ProfileModel'
    to_field: str = ''

    def set_field(self, field):
        super().set_field(field)
        to_field = field.to_fields[0]
        if to_field is None:
            to_field = 'id'
        self.to_field = to_field

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "model": self.model,
                "toField": self.to_field,
            }
        }
        return data


class DecimalFilterField(BaseFilterField):
    widget_type: str = 'Decimal'
    decimal_config = DecimalConfig()

    def set_field(self, field):
        super().set_field(field)
        self.decimal_config.set_field(field)

    def get_dict(self):
        data = {
            "name": self.name,
            "type": self.obj_type,
            "verbose_name": self.verbose_name,
            "widget": {
                "type": self.widget_type,
                "mode": self.mode,
                "minValue": self.decimal_config.min_value,
                "maxValue": self.decimal_config.max_value,
                "decimalLength": self.decimal_config.decimal_length
            }
        }
        return data
