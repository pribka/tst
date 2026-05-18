from django.db import models
from django.utils.functional import cached_property
import decimal
from rest_framework.serializers import DecimalField

from .page_config import BooleanTableColumn, BooleanFormField, CharFieldFormField, DefaultTableColumn, \
    DateTableColumn, DateFormField, DateTimeTableColumn, DateTimeFormField, FileFormField, DecimalFormField, \
    UserTableColumn, TPDecimalColumn, ForeignKeyTableColumn, ForeignKeyFormField, TPForeignKeyColumn, TPSwitchColumn, \
    TPStringColumn, TPDateColumn, TPDateTimeColumn, TPIntegerColumn, IntegerFormField
from .current_profile.db.models import CurrentProfileField
from .page_config.filter_fields import BooleanFilterField, CharFilterField, DateFilterField, DateTimeFilterField, \
    IntegerFilterField, ProfileFilterField, ForeignKeyFilterField, DecimalFilterField


class CustomBooleanField(models.BooleanField):
    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = BooleanTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = BooleanFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = BooleanFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPSwitchColumn()

        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"value": ""}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.filter_info.set_field(self)
        self.tp_info.set_field(self)


class CustomCharField(models.CharField):

    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DefaultTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = CharFieldFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = CharFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPStringColumn()

        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"value": "__icontains"}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.filter_info.set_field(self)
        self.tp_info.set_field(self)


class CustomDateField(models.DateField):

    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DateTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = DateFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = DateFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPDateColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"start": "__gte", "end": "__lte", "value": ""}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.filter_info.set_field(self)
        self.tp_info.set_field(self)


class CustomDateTimeField(models.DateTimeField):

    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None,filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DateTimeTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = DateTimeFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = DateTimeFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPDateTimeColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"start": "__gte", "end": "__lte", "value": ""}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.filter_info.set_field(self)
        self.tp_info.set_field(self)


class CustomFileField(models.FileField):

    def __init__(self, *args, table_info=None, field_info=None, **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DefaultTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = FileFormField()

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)


class CustomPositiveIntegerField(models.PositiveIntegerField):
    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DefaultTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = IntegerFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = IntegerFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPIntegerColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.filter_info.set_field(self)
        self.tp_info.set_field(self)


class CustomIntegerField(models.IntegerField):
    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None,filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DefaultTableColumn()
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = IntegerFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = IntegerFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPIntegerColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.tp_info.set_field(self)
        self.filter_info.set_field(self)


class CustomCurrentProfileField(CurrentProfileField):  # TODO добавить field_info
    def __init__(self, *args, table_info=None, filter_info=None,filter_lookup=None, **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = UserTableColumn()
        if filter_info is not None:
            self.filter_info = table_info
        else:
            self.filter_info = ProfileFilterField()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"value": "__in"}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.filter_info.set_field(self)


class CustomForeignKey(models.ForeignKey):

    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = ForeignKeyTableColumn()
        if field_info is not None:
            self._field_info = field_info
        else:
            self._field_info = ForeignKeyFormField()
        if filter_info is not None:
            self._filter_info = filter_info
        else:
            self._filter_info = ForeignKeyFilterField()
        if tp_info is not None:
            self._tp_info = tp_info
        else:
            self._tp_info = TPForeignKeyColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"value": "__in"}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)

    @cached_property
    def field_info(self):
        self._field_info.set_field(self)
        return self._field_info

    @cached_property
    def filter_info(self):
        self._filter_info.set_field(self)
        return self._filter_info

    @cached_property
    def tp_info(self):
        self._tp_info.set_field(self)
        return self._tp_info


class CustomOneToOneField(models.OneToOneField):  # TODO прописать виджеты для OneToOneField. Пока что используются от ForeignKey.

    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = ForeignKeyTableColumn()
        if field_info is not None:
            self._field_info = field_info
        else:
            self._field_info = ForeignKeyFormField()
        if filter_info is not None:
            self._filter_info = filter_info
        else:
            self._filter_info = ForeignKeyFilterField()
        if tp_info is not None:
            self._tp_info = tp_info
        else:
            self._tp_info = TPForeignKeyColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"value": "__in"}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)

    @cached_property
    def field_info(self):
        self._field_info.set_field(self)
        return self._field_info

    @cached_property
    def filter_info(self):
        self._filter_info.set_field(self)
        return self._filter_info

    @cached_property
    def tp_info(self):
        self._tp_info.set_field(self)
        return self._tp_info


class CustomDecimalField(models.DecimalField):
    def __init__(self, *args, table_info=None, field_info=None, tp_info=None, filter_info=None, filter_lookup=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if table_info is not None:
            self.table_info = table_info
        else:
            self.table_info = DefaultTableColumn(cell_renderer='DecimalRow')
        if field_info is not None:
            self.field_info = field_info
        else:
            self.field_info = DecimalFormField()
        if filter_info is not None:
            self.filter_info = filter_info
        else:
            self.filter_info = DecimalFilterField()
        if tp_info is not None:
            self.tp_info = tp_info
        else:
            self.tp_info = TPDecimalColumn()
        if filter_lookup is not None:
            self.filter_lookup = filter_lookup
        else:
            self.filter_lookup = {"start": "__gte", "end": "__lte", "value": ""}

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.table_info.set_field(self)
        self.filter_info.set_field(self)
        self.field_info.set_field(self)
        self.tp_info.set_field(self)


class FakeField:
    table_info = DefaultTableColumn()
    field_info = CharFieldFormField()
    filter_info = CharFilterField()
    tp_info = TPStringColumn()
    internal_type = 'CharField'

    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.table_info.set_field(self)
        self.field_info.set_field(self)
        self.filter_info.set_field(self)
        self.tp_info.set_field(self)

    def get_internal_type(self):
        return self.internal_type


class RoundingDecimalField(DecimalField):
    """Поле для сериализатора, которое позволяет не вызывать ошибку, если передано больше значащих цифр после запятой.
    Число в таком случае округляется."""
    
    def validate_precision(self, value):
        # This is needed to avoid to raise an error if `value` has more decimals than self.decimal_places.
        with decimal.localcontext() as ctx:
            if self.rounding:
                ctx.rounding = self.rounding
            value = round(value, self.decimal_places)
        return super().validate_precision(value)