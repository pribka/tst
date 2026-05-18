from .common import BaseConfig, ModelSetConfig, empty_str_func


class Button(BaseConfig):
    """Базовая кнопка"""
    action = ''
    css_class = ''
    icon = ''
    size = 'default'
    title = ''
    obj_type = 'default'
    widget = 'Default'
    disabled = False
    form = ''

    def get_dict(self):
        data = {
            'action': self.action,
            'class': self.css_class,
            'icon': self.icon,
            'size': self.size,
            'title': self.title,
            'type': self.obj_type,
            'widget': self.widget,
            'disabled': self.disabled
        }
        if self.form:
            data['form'] = self.form
        return data


class ModelButton(Button):
    """Базовая кнопка с атрибутом model.
    Метод set_model() устанавилвает модель экземпляру и каскадно - всем вложенным кнопкам.
    """
    model = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        model = kwargs.get('model')
        if model is not None:
            self.set_model(model)

    def set_model(self, model):
        self.model = model
        return self


class ModelFormButton(ModelButton):
    """
    Кнопка с моделью и формой по умолчанию.
    """
    def set_model(self, model):
        super().set_model(model)
        self.form = f"edit_{getattr(getattr(self, 'model'), 'get_label', empty_str_func)()}"


class DropdownButton(ModelButton):
    """
    Базовая dropdown-кнопка (кнопка с выпадающим списком кнопок).
    children - Вложенные кнопки. Является объектом ButtonSet (набор кнопок).
    """
    obj_type = 'default'
    widget = 'Dropdown'
    trigger = ['hover']
    children = ModelSetConfig()

    def get_dict(self):
        result = super().get_dict()
        result['children'] = self.children.get_dict()
        return result

    def set_model(self, model):
        super().set_model(model)
        self.children.set_model(model)
        return self


class DropdownActionsButton(ModelButton):
    """
    Базовая кнопка DropdownActions. Кнопка с дополнительной кнопкой, в которой находятся вложенные кнопки (опции
    основной кнопки).
    """
    obj_type = 'default'
    widget = 'DropdownActions'
    children = ModelSetConfig()

    def get_dict(self):
        result = super().get_dict()
        result['children'] = self.children.get_dict()
        return result

    def set_model(self, model):
        self.model = model
        self.children.set_model(model)
        return self
