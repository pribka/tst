from common.page_config.common import ModelConfig, empty_str_func, BaseMetaPageConfig, BasePage, ModelSetConfig
from .forms import BaseModelFormInfo, BaseModelFieldInfo
from django.core.exceptions import FieldDoesNotExist


class BaseModelPageConfig(ModelConfig):
    form_info = BaseModelFormInfo()
    table_info = None  # TODO написать объект TableInfo()

    def set_model(self, model):
        self.model = model
        self.table_info = getattr(self.model, 'get_table_structure', empty_str_func)()
        self.form_info.set_model(model)

    def get_dict(self):
        data = {
            'tableInfo': [self.table_info],
            'formInfo': [self.form_info.get_dict()],
        }
        return data


class BaseModelMetaConfig(BaseMetaPageConfig):
    page_config = BaseModelPageConfig()

    @property
    def counter(self):
        return getattr(self.model, 'get_counter', empty_str_func)()

    def set_model(self, model):
        super().set_model(model)
        self.title = getattr(getattr(self.model, '_meta', None), 'verbose_name_plural', '')
        self.is_hide = getattr(self.model, 'get_hide', empty_str_func)()
        self.page_config.set_model(model)

    def get_dict(self):
        data = super().get_dict()
        data['pageConfig'] = self.page_config.get_dict()
        return data


class BaseModelPage(BasePage):
    name: str = ''
    path: str = ''
    meta = BaseModelMetaConfig()

    def set_model(self, model):
        self.model = model
        self.name = f"page_list_{self.model.get_label()}"
        self.path = self.model.get_label().lower()
        self.meta.set_model(model)
        return self

