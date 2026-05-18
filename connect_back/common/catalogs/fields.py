from django.core.validators import MinValueValidator

from common import fields as common_fields
from common import page_config


class OrdersInProgressField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.IntegerFormField()
    filter_info = page_config.IntegerFilterField()
    tp_info = page_config.TPIntegerColumn()
    filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}
    internal_type = "IntegerField"
    name = 'orders_in_progress_filter'
    verbose_name = 'Кол-во заказов в обработке'
    default = None
    blank = True
    validators = (MinValueValidator(limit_value=0),)

    def to_filter(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.filter(orders_in_progress__gte=start)
        if end is not None:
            queryset = queryset.filter(orders_in_progress__lte=end)
        return queryset

    def to_exclude(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.exclude(orders_in_progress__lte=start)
        if end is not None:
            queryset = queryset.exclude(orders_in_progress__gte=end)
        return queryset


class LastOrderDateField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.DateTimeFormField()
    filter_info = page_config.DateTimeFilterField()
    tp_info = page_config.TPDateTimeColumn()
    filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}
    internal_type = "DateTimeField"
    name = 'last_order_date_filter'
    verbose_name = 'Дата предыдущего заказа'
    default = None
    blank = True
    validators = ()

    def to_filter(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.filter(last_order_date__gte=start)
        if end is not None:
            queryset = queryset.filter(last_order_date__lte=end)
        return queryset

    def to_exclude(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.exclude(last_order_date__gte=start)
        if end is not None:
            queryset = queryset.exclude(last_order_date__lte=end)
        return queryset


class LeadSatusField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.CharFieldFormField()
    filter_info = page_config.ChoiceFilterField()
    tp_info = page_config.TPStringColumn()
    name = 'lead_status_filter'
    verbose_name = 'Статус'
    default = None
    blank = True
    max_length = 255
    choices = (
        ('Новый', 'Новый'),
        ('Текущий', 'Текущий'),
        ('Архивный', 'Архивный'),
        ('Создан клиент', 'Создан клиент'),
    )

    def to_filter(self, queryset, value):
        statuses = value.get('value')
        if statuses is None:
            return queryset
        else:
            queryset = queryset.filter(status__in=statuses)
        return queryset

    def to_exclude(self, queryset, value):
        statuses = value.get('value')
        if statuses is None:
            return queryset
        else:
            queryset = queryset.exclude(status__in=statuses)
        return queryset


class ContractorSatusField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.CharFieldFormField()
    filter_info = page_config.ChoiceFilterField()
    tp_info = page_config.TPStringColumn()
    name = 'contractor_status_filter'
    verbose_name = 'Статус'
    default = None
    blank = True
    max_length = 255
    choices = (
        ('Новый', 'Новый'),
        ('Текущий', 'Текущий'),
        ('Архивный', 'Архивный'),
    )

    def to_filter(self, queryset, value):
        statuses = value.get('value')
        if statuses is None:
            return queryset
        else:
            queryset = queryset.filter(status__in=statuses)
        return queryset

    def to_exclude(self, queryset, value):
        statuses = value.get('value')
        if statuses is None:
            return queryset
        else:
            queryset = queryset.exclude(status__in=statuses)
        return queryset
