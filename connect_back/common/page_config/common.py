import copy


def empty_func(*args, **kwargs):
    return


def empty_str_func(*args, **kwargs):
    return ''


class BaseConfig:
    """Базовый класс для всех конфигов, возвращаемых фронтенду.
    Метод get_dict() собирает JSON с информацией об отрисовке элемента.
    """

    def __new__(cls, *args, **kwargs):
        instance = super(BaseConfig, cls).__new__(cls)
        for name in dir(cls):
            value = getattr(cls, name)
            if isinstance(value, BaseConfig):
                setattr(instance, name, copy.deepcopy(value))
        return instance

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if value is None:
                setattr(self, key, getattr(self, key))
            else:
                setattr(self, key, value)
        variables = vars(self)
        for key, value in variables.items():
            if isinstance(value, BaseConfig):
                setattr(self, key, copy.deepcopy(value))

    def get_dict(self):
        return dict()


class ModelConfig(BaseConfig):
    """Базовый конфиг с атрибутом model.
    Метод set_model() устанавилвает модель экземпляру и каскадно - всем вложенным конфигам.
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


class SetConfig(ModelConfig):
    instances: tuple = tuple()

    def set_instance(self, name: str, instance: BaseConfig = None, position: int = None):
        if position is None:
            position = len(self.instances)
        setattr(self, name, instance)
        instances = list(self.instances)
        try:
            instances.remove(name)
        except ValueError:
            pass
        instances.insert(position, name)
        self.instances = tuple(instances)
        return self

    def get_dict(self):
        return [getattr(self, child).get_dict() for child in self.instances]


class ModelSetConfig(SetConfig):

    def set_model(self, model):
        self.model = model
        for instance in self.instances:
            getattr(getattr(self, instance), 'set_model', empty_func)(model)
        return self


class BaseMetaPageConfig(ModelConfig):
    page_widget: str = 'PageTable'
    nav_widget: str = 'NavPage'
    item_widget: str = 'ItemWidget'
    title: str = ''
    is_hide: bool = False
    favorite_support: bool = True
    background_color: str = '#fff'
    drawer_mode: bool = False
    modal_mode: bool = False
    page_config = None
    badge: dict = None
    badge_counter: bool = False
    extra: dict = None

    @property
    def counter(self):
        return getattr(self.model, 'get_counter', empty_str_func)()

    def set_model(self, model):
        super().set_model(model)
        getattr(self.page_config, 'set_model', empty_func)(model)

    def get_dict(self):
        data = {
            'pageWidget': self.page_widget,
            'navWidget': self.nav_widget,
            'itemWidget': self.item_widget,
            'title': self.title,
            'counter': self.counter,
            'favoriteSupport': self.favorite_support,
            'hide': self.is_hide,
            'backgroundColor': self.background_color,
            'drawerMode': self.drawer_mode,
            'modalMode': self.modal_mode,
            'badgeCounter': self.badge_counter,
            'pageConfig': getattr(self.page_config, 'get_dict', empty_str_func)()
        }
        if self.badge:
            data['badge'] = self.badge
        if self.extra:
            for key, value in self.extra.items():
                data[key] = value
        return data


class BasePage(ModelConfig):
    name: str = ''
    path: str = ''
    meta = BaseMetaPageConfig()
    icon_supplier: str = 'ant'
    icon: str = 'folder'
    is_page: bool = True

    def set_model(self, model):
        self.model = model
        self.name = f"page_list_{self.model.get_label()}"
        self.path = self.model.get_label().lower()
        self.meta.set_model(model)
        return self

    def get_dict(self):
        data = {
            'name': self.name,
            'path': self.path,
            'meta': self.meta.get_dict()
        }
        data['meta']['icon'] = self.icon
        data['meta']['iconSupplier'] = self.icon_supplier
        data['meta']['isPage'] = self.is_page
        return data


class BaseEmbeddedPage(BasePage):
    page_redirect: str = ''
    children_type: str = ''
    children_config: str = ''
    children_config_path: str = ''

    def get_dict(self):
        data = super().get_dict()
        data['pageRedirect'] = self.page_redirect
        if self.children_type:
            data['children'] = {'type': self.children_type, 'config': self.children_config,
                                'configPath': self.children_config_path}
        return data


class BaseMobileAppPage(BaseConfig):
    name: str = ''
    title: str = ''
    component: str = ''
    icon: str = ''
    options: dict = {}

    def get_dict(self):
        data = {
            'name': self.name,
            'title': self.title,
            'component': self.component,
            'icon': self.icon,
            'options': self.options,
        }
        return data


class Category(BaseConfig):
    name: str = ''
    path: str = ''
    title: str = ''
    children: SetConfig = SetConfig()
    redirect: str = ''
    icon_supplier: str = 'ant'
    menu_widget: str = 'ListWidget'
    icon = ''

    def get_dict(self):
        self.prepare_children()
        data = {
            'name': self.name,
            'path': self.path,
            'redirect': {'name': self.redirect},
            'meta': {
                'title': self.title,
                'iconSupplier': self.icon_supplier,
                'menuWidget': self.menu_widget,
                'icon': self.icon,
            },
            'children': self.children.get_dict(),
        }
        return data

    def prepare_children(self):
        for each in self.children.instances:
            getattr(self, f'prepare_{each}', empty_func)()
