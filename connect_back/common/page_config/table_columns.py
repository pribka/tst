from django.utils.translation import gettext as _

from .common import BaseConfig
from .form_fields import DecimalConfig, BaseRulesConfig, BaseFormFieldConfig, FormFieldSet, RequiredRulesConfig, \
    ActionsForeignKey


class BaseTableColumn(BaseConfig):
    header_name: str = ''
    field: str = ''
    sortable: bool = True
    cell_renderer: str = ''
    width: int = None

    def set_field(self, field):
        self.header_name = field.verbose_name
        self.field = field.name

    def get_dict(self):
        data = {
            "headerName": self.header_name,
            "field": self.field,
            "sortable": self.sortable,
            "cellRenderer": self.cell_renderer
        }
        if self.width:
            data['width'] = self.width
        return data


class DefaultTableColumn(BaseTableColumn):
    cell_renderer = 'DefaultRow'


class BooleanTableColumn(BaseTableColumn):
    boolean_true: str = _('Yes')
    boolean_false: str = _('No')
    cell_renderer = 'BooleanRow'

    def get_dict(self):
        data = super().get_dict()
        data['boolean_true'] = self.boolean_true
        data['boolean_false'] = self.boolean_false
        return data


class DateTableColumn(BaseTableColumn):
    cell_renderer = 'DateRow'
    date_format: str = 'DD-MM-YYYY'

    def get_dict(self):
        data = super().get_dict()
        data['cellRendererParams'] = {'dateFormat': self.date_format}
        return data


class DateTimeTableColumn(DateTableColumn):
    cell_renderer = 'DateTimeRow'
    date_format: str = 'DD-MM-YYYY HH:mm'


class UserTableColumn(BaseTableColumn):
    cell_renderer = 'UserRow'


class ForeignKeyTableColumn(BaseTableColumn):
    cell_renderer: str = 'RelatedRow'
    interpretation_field: str = 'name'

    def get_dict(self):
        data = super().get_dict()
        data['cellRendererParams'] = {
            'interpretationField': self.interpretation_field,
        }
        return data
