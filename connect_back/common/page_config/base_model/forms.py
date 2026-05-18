from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

from common.page_config.common import BaseConfig, ModelConfig, empty_str_func, empty_func
from .button_sets import BaseCatalogButtonSet


class BaseModelAction(BaseConfig):
    content_type = ''
    path = ''

    def get_dict(self):
        data = {
            'path': self.path,
        }
        if self.content_type:
            data['ContentType'] = self.content_type
        return data


class BaseModelActionSet(ModelConfig):
    create = BaseModelAction()
    update = BaseModelAction()
    retrieve = BaseModelAction()

    def set_model(self, model):
        self.model = model
        self.create.path = getattr(self.model, 'get_data_path', empty_str_func)()
        self.update.path = getattr(self.model, 'get_data_path', empty_str_func)() + '<id>/'
        self.retrieve.path = getattr(self.model, 'get_data_path', empty_str_func)() + '<id>/'

    def get_dict(self):
        data = {
            'create': self.create.get_dict(),
            'update': self.update.get_dict(),
            'retrieve': self.retrieve.get_dict(),
        }
        return data


class BaseModelI18n(ModelConfig):
    create_title = ''
    update_title = ''

    def set_model(self, model):
        self.model = model
        self.create_title = _('Create') + ' ' + getattr(getattr(self.model, '_meta', None), 'verbose_name', '')
        self.update_title = _('Edit') + ' ' + getattr(getattr(self.model, '_meta', None), 'verbose_name', '')

    def get_dict(self):
        data = {
            'create_title': self.create_title,
            'update_title': self.update_title,
        }
        return data


class BaseModelFields(ModelConfig):
    create: tuple = tuple()
    update: tuple = tuple()

    def set_model(self, model):
        self.model = model
        self.create = tuple(getattr(getattr(getattr(
            self.model, 'get_serializer_class', empty_func)(action='create'), 'Meta', None), 'fields', []))
        self.update = tuple(getattr(getattr(getattr(
            self.model, 'get_serializer_class', empty_func)(action='update'), 'Meta', None), 'fields', []))

    def get_dict(self):
        data = {
            'create': self.create,
            'update': self.update
        }
        return data


class BaseModelFieldInfo(ModelConfig):
    fields: tuple = tuple()

    def set_model(self, model):
        self.model = model
        if not getattr(model, 'is_enum', empty_func)():
            fields_create = list(model.get_serializer_class(action='create').Meta.fields)
            fields_update = list(model.get_serializer_class(action='update').Meta.fields)
            fields = set(fields_create + fields_update)
        else:
            fields = set(model.get_serializer_class(action='retrieve').Meta.fields)
        fields.discard('id')
        self.set_fields(tuple(fields))


    def set_fields(self, fields: tuple):  # TODO доработать возможность кастомизации.
        self.fields = fields
        fields_dict = dict()
        for each in getattr(getattr(self.model, '_meta', None), 'fields', []):
            fields_dict[each.name] = each
        if self.model and getattr(self.model, 'is_enum', empty_func)():
            disabled = True
        else:
            disabled = False
        for field in self.fields:
            if hasattr(fields_dict.get(field), 'field_info'):
                setattr(self, field, fields_dict.get(field).field_info)
                setattr(getattr(self, field, None), 'disabled', disabled)
        return self

    def add_field(self, name: str, field, position: int = None):
        if position is None:
            position = len(self.fields)
        setattr(self, name, field)
        fields = list(self.fields)
        try:
            fields.remove(name)
        except ValueError:
            pass
        fields.insert(position, name)
        self.fields = tuple(fields)

    def delete_fields(self, fields: tuple):
        field_names = list(self.fields)
        for field in fields:
            try:
                field_names.remove(field)
            except ValueError:
                pass
        self.fields = tuple(field_names)

    def get_dict(self):
        data = [
            getattr(self, field, None) if isinstance(getattr(self, field, None), dict) else getattr(getattr(self, field, None), 'get_dict', empty_func)()
            for field in self.fields]  # TODO заглушка пока не завершится рефакторинг полей форм.
        return data


class FormInfoPageConfig(ModelConfig):
    header_buttons = BaseCatalogButtonSet()

    def set_model(self, model):
        self.model = model
        self.header_buttons.set_model(model)
        return self

    def get_dict(self):
        data = {
            'headerButtons': self.header_buttons.get_dict(),
        }
        return data


class BaseModelCharacteristicEditablePart(ModelConfig):
    name = 'characteristic'
    title = 'Каталогизация'
    obj_type = 'parts'
    path = '/pvh/form_info/?model='

    def set_model(self, model):
        super().set_model(model)
        return self

    def get_dict(self):
        data = {
            'name': self.model._meta.label + '_parts',
            'title': self.title,
            'type': self.obj_type,
            'dataPath': self.path + self.model._meta.label,
        }
        return data


class BaseModelFormInfo(ModelConfig):
    name = ''
    show_comment = False
    show_author = False
    actions = BaseModelActionSet()
    i18n = BaseModelI18n()
    page_widget = 'Default'
    nav_widget = 'NavForm'
    fields = BaseModelFields()
    field_info = BaseModelFieldInfo()
    page_config = FormInfoPageConfig()
    table_key: str = ''
    editable_part = BaseModelCharacteristicEditablePart()

    def set_model(self, model):
        self.model = model
        self.name = f"edit_{getattr(getattr(self, 'model', None), 'get_label', empty_str_func)()}"
        self.actions.set_model(model)
        self.i18n.set_model(model)
        self.fields.set_model(model)
        self.field_info.set_model(model)
        self.editable_part.set_model(model)
        self.page_config.set_model(model)
        self.table_key = getattr(model, 'get_label', empty_str_func)()
        return self

    def delete_fields(self, fields: tuple):
        for field in fields:
            delattr(self.field_info, field)
            fields = list(self.field_info.fields)
            try:
                fields.remove(field)
            except ValueError:
                pass
            self.field_info.fields = tuple(fields)
            fields_create = list(self.fields.create)
            try:
                fields_create.remove(field)
            except ValueError:
                pass
            self.fields.create = tuple(fields_create)
            fields_update = list(self.fields.update)
            try:
                fields_update.remove(field)
            except ValueError:
                pass
            self.fields.update = fields_update

    def get_dict(self):
        data = {
            'name': self.name,
            'tableKey': self.table_key,
            'showComment': self.show_comment,
            'showAuthor': self.show_author,
            'actions': self.actions.get_dict(),
            'i18n': self.i18n.get_dict(),
            'pageWidget': self.page_widget,
            'navWidget': self.nav_widget,
            'fields': self.fields.get_dict(),
            'fieldInfo': self.field_info.get_dict(),
            'pageConfig': self.page_config.get_dict(),
        }
        if self.model.has_characteristics_plan():
            data['editablePart'] = [self.editable_part.get_dict()]
            data['pageWidget'] = 'TableForm'
        cache.set(f'form_info:{self.name}', data, timeout=None)

        return data


class ExtraModelFormInfo(BaseModelFormInfo):
    page_config = None
    actions = None
    i18n = None
    obj_type = 'form'
    fields: tuple = tuple()
    title = ''

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def get_fields(self):
        if self.model and self.fields:
            model_create_list = list(self.model.get_serializer_class(action='create').Meta.fields)
            create_list = list(set(model_create_list) & set(self.fields))
            model_update_list = list(self.model.get_serializer_class(action='create').Meta.fields)
            update_list = list(set(model_update_list) & set(self.fields))
            return {
                'create': create_list,
                'update': update_list
            }
        else:
            return {
                'create': [],
                'update': []
            }

    def set_model(self, model):
        self.model = model
        self.field_info.model = model
        self.field_info.set_fields(self.fields)
        return self

    def get_dict(self):
        data = {
            'name': self.name,
            'type': self.obj_type,
            'title': self.title,
            'showComment': self.show_comment,
            'showAuthor': self.show_author,
            'i18n': self.i18n.get_dict() if self.i18n else None,
            'pageWidget': self.page_widget,
            'navWidget': self.nav_widget,
            'fields': self.get_fields(),
            'fieldInfo': self.field_info.get_dict(),
            'pageConfig': self.page_config.get_dict() if self.page_config else {"headerButtons": []},
        }
        if self.actions:
            data['actions'] = self.actions.get_dict()
        cache.set(f'form_info:{self.name}', data, timeout=None)
        return data


class FormGroupFields(ModelConfig):
    obj_type: str = 'GroupFields'
    title: str = ''
    collapse: bool = True
    default_collapse: bool = False
    css_class: str = ''
    field_info = BaseModelFieldInfo()
    inline: bool = False
    width: int = None
    fields: tuple = tuple()

    def set_model(self, model):
        self.model = model
        self.field_info.model = model
        self.field_info.set_fields(self.fields)

    def get_dict(self):
        data = {
            "type": self.obj_type,
            "title": self.title,
            "collapse": self.collapse,
            "defaultCollapse": self.default_collapse,
            "class": self.css_class,
            "fieldInfo": self.field_info.get_dict(),
            "inline": self.inline,
            "width": self.width,
        }
        return data
