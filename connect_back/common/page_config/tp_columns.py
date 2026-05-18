from django.core.validators import DecimalValidator

from .table_columns import BaseTableColumn, ForeignKeyTableColumn, BooleanTableColumn, DefaultTableColumn
from .form_fields import DecimalConfig, BaseRulesConfig, BaseFormFieldConfig, FormFieldSet, RequiredRulesConfig, \
    ActionsForeignKey, LengthRulesConfig


class BaseCellEditorParams(BaseFormFieldConfig):
    rules_config = FormFieldSet(required=RequiredRulesConfig(), instances=('required',))

    def set_field(self, field):
        super().set_field(field)
        self.rules_config.set_field(field)

    def get_dict(self):
        data = {
            'rulesConfig': self.rules_config.get_dict()
        }
        return data


class TPDecimalColumn(BaseTableColumn):
    cell_renderer: str = 'DecimalRow'
    editable: bool = True
    cell_editor: str = 'WidgetDecimal'
    cell_editor_params = BaseCellEditorParams()
    decimal_length = 0
    min_value: str = '0'
    max_value: str = '0'
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.cell_editor_params.set_field(field)
        self.decimal_length = getattr(field, 'decimal_places', 0)
        for each in field.validators:
            if isinstance(each, DecimalValidator):
                self.min_value = str(-10 ** each.max_digits)
                self.max_value = str(10 ** each.max_digits)

    def get_dict(self):
        data = super().get_dict()
        data['editable'] = self.editable
        data['cellEditor'] = self.cell_editor
        data['cellEditorParams'] = self.cell_editor_params.get_dict()
        data['cellEditorParams']['decimalLength'] = self.decimal_length
        data['cellEditorParams']['minValue'] = self.min_value
        data['cellEditorParams']['maxValue'] = self.max_value
        data['cellRendererParams'] = {'fComputed': self.f_computed}
        return data


class ForeignKeyCellEditorParams(BaseFormFieldConfig):
    name: str = ''
    title: str = ''
    obj_type: str = 'WidgetSelect'
    to_field: str = ''
    to_name: str = 'string_view'
    key: str = ''
    data_path: str = ''
    rules_config = FormFieldSet(required=RequiredRulesConfig(), instances=('required',))
    actions = ActionsForeignKey()
    default_value = None
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        self.title = field.verbose_name
        try:
            to_field = field.to_fields[0]
        except KeyError:
            to_field = 'id'
        if to_field is None:
            to_field = 'id'
        self.to_field = to_field
        remote_field_model = getattr(getattr(field, 'remote_field', None), 'model', None)
        if remote_field_model:
            self.key = remote_field_model.get_label()
            self.data_path = f"/app_info/select_list/?model={remote_field_model.get_label()}"
        self.rules_config.set_field(field)
        try:
            is_enum = remote_field_model.is_enum()
        except AttributeError:
            is_enum = False
        if is_enum is False:
            self.actions.set_field(field)
        else:
            self.actions = None
        if field.default is not None and not callable(field.default):
            self.default_value = field.default

    def get_dict(self):
        try:
            actions = self.actions.get_dict()
        except AttributeError:
            actions = None
        data = {
            'name': self.name,
            'title': self.title,
            'type': self.obj_type,
            'toField': self.to_field,
            'toName': self.to_name,
            'key': self.key,
            'dataPath': self.data_path,
            'rulesConfig': self.rules_config.get_dict(),
            'actions': actions,
            'cellRendererParams': {'fComputed': self.f_computed}
        }
        if self.default_value is not None:
            data['defaultValue'] = self.default_value
        return data


class TPForeignKeyColumn(ForeignKeyTableColumn):
    editable: bool = True
    cell_editor: str = 'WidgetSelect'
    cell_editor_params = ForeignKeyCellEditorParams()
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.cell_editor_params.set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['editable'] = self.editable
        data['cellEditor'] = self.cell_editor
        data['cellEditorParams'] = self.cell_editor_params.get_dict()
        data['cellRendererParams'] = {'fComputed': self.f_computed}
        return data


class BooleanCellEditorParams(BaseCellEditorParams):
    name: str = ''
    default_check: bool = False
    obj_type: str = 'WidgetSwitch'
    title: str = ''

    def set_field(self, field):
        super().set_field(field)
        self.name = field.name
        self.default_check = field.default
        self.title = field.verbose_name

    def get_dict(self):
        data = super().get_dict()
        data['name'] = self.name
        data['defaultCheck'] = self.default_check
        data['type'] = self.obj_type
        data['title'] = self.title
        return data


class TPSwitchColumn(BaseTableColumn):
    editable: bool = True
    cell_renderer: str = 'SwitchRow'
    cell_editor: str = 'WidgetSwitch'
    cell_editor_params = BooleanCellEditorParams()
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.cell_editor_params.set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['editable'] = self.editable
        data['cellEditor'] = self.cell_editor
        data['cellEditorParams'] = self.cell_editor_params.get_dict()
        data['cellRendererParams'] = {'fComputed': self.f_computed}
        return data


class StringColumnCellEditorParams(BaseCellEditorParams):
    rules_config = FormFieldSet(required=RequiredRulesConfig(), length=LengthRulesConfig(), instances=('required', 'length'))


class TPStringColumn(DefaultTableColumn):
    header_name: str = ''
    editable: bool = True
    cell_editor: str = 'WidgetString'
    cell_editor_params = StringColumnCellEditorParams()
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.header_name = field.verbose_name
        self.cell_editor_params.set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['editable'] = self.editable
        data['headerName'] = self.header_name
        data['cellEditor'] = self.cell_editor
        data['cellEditorParams'] = self.cell_editor_params.get_dict()
        data['cellRendererParams'] = {'fComputed': self.f_computed}
        return data


class TPDateColumn(DefaultTableColumn):
    cell_renderer: str = 'DateTimeRow'
    header_name: str = ''
    editable: bool = True
    cell_editor: str = 'WidgetDateTime'
    cell_editor_params = BaseCellEditorParams()
    placeholder: str = '__-__-____'
    current_date: bool = False
    date_format: str = 'DD-MM-YYYY'
    time: bool = False
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.header_name = field.verbose_name
        self.cell_editor_params.set_field(field)

    def get_dict(self):
        data = super().get_dict()
        data['editable'] = self.editable
        data['headerName'] = self.header_name
        data['cellEditor'] = self.cell_editor
        data['cellEditorParams'] = self.cell_editor_params.get_dict()
        data['cellEditorParams']['time'] = self.time
        data['cellEditorParams']['dateFormat'] = self.date_format
        data['cellEditorParams']['currentDate'] = self.current_date
        data['cellEditorParams']['placeholder'] = self.placeholder
        data['cellRendererParams'] = {'fComputed': self.f_computed}
        return data


class TPDateTimeColumn(TPDateColumn):
    time: bool = True
    placeholder: str = '__-__-____ __:__'
    current_date: bool = False
    date_format: str = 'DD-MM-YYYY HH:mm'


class TPIntegerColumn(DefaultTableColumn):
    cell_renderer: str = 'IntegerRow'
    header_name: str = ''
    editable: bool = True
    cell_editor: str = 'WidgetInteger'
    cell_editor_params = BaseCellEditorParams()
    placeholder: str = '0'
    default_value: int = 0
    min_value: str = '-2147483648'
    max_value: str = '2147483647'
    f_computed: bool = False

    def set_field(self, field):
        super().set_field(field)
        self.header_name = field.verbose_name
        self.cell_editor_params.set_field(field)
        if field.default is not None:
            self.placeholder = str(field.default)
            self.default_value = field.default
        for each in field.validators:
            if each.code == 'min_value':
                self.min_value = str(each.limit_value)
            elif each.code == 'max_value':
                self.max_value = str(each.limit_value)

    def get_dict(self):
        data = super().get_dict()
        data['headerName'] = self.header_name
        data['cellEditor'] = self.cell_editor
        data['cellEditorParams'] = self.cell_editor_params.get_dict()
        data['editable'] = self.editable
        data['minValue'] = self.min_value
        data['maxValue'] = self.max_value
        data['defaultValue'] = self.default_value
        data['cellRendererParams'] = {'fComputed': self.f_computed}
        return data
