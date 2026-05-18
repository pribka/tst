from common.page_config.common import ModelConfig, ModelSetConfig
from common.page_config.base_model.forms import ExtraModelFormInfo, BaseModelFormInfo, FormInfoPageConfig, \
    BaseModelCharacteristicEditablePart

from .button_sets import BaseDocumentButtonSet


class BaseDocumentTabularPart(ModelConfig):
    name = None
    title = None
    obj_type = 'table'
    table_info = None
    filter_info = ''  # TODO прописать filter_info
    form_info: ExtraModelFormInfo = None
    grid_type: str = ''

    def get_dict(self):
        data = {
            'name': self.name,
            'title': self.title,
            'type': self.obj_type,
            'tableInfo': self.table_info,
            'formInfo': self.form_info.get_dict() if self.form_info else None,
            'filterInfo': self.filter_info,
        }
        if self.grid_type:
            data['gridType'] = self.grid_type
        return data


class BaseDocumentEditablePart(ModelSetConfig):

    def set_model(self, model):
        super().set_model(model)
        tabular_parts = model.get_tabular_parts()
        for key, value in tabular_parts.items():
            self.set_instance(key, BaseDocumentTabularPart(
                name=key,
                title=value._meta.verbose_name,
                table_info=value.get_table_structure(),
                filter_info='',  # TODO прописать filter_info
            ))
        return self


class BaseDocumentFormInfo(BaseModelFormInfo):
    page_widget = 'TableForm'
    show_comment = True
    show_author = True
    editable_part = BaseDocumentEditablePart()
    characteristic_editable_parts = BaseModelCharacteristicEditablePart()
    page_config = FormInfoPageConfig(header_buttons=BaseDocumentButtonSet())

    def get_dict(self):
        data = super().get_dict()
        data['editablePart'] = self.editable_part.get_dict()
        if self.model.has_characteristics_plan():
            self.characteristic_editable_parts.set_model(self.model)
            data['editablePart'].append(self.characteristic_editable_parts.get_dict())
        return data

    def set_model(self, model):
        super().set_model(model)
        self.editable_part.set_model(model)
        if self.show_comment:
            fields = list(self.field_info.fields)
            try:
                fields.remove('comment')
            except ValueError:
                pass
            self.field_info.fields = tuple(fields)
        return self
