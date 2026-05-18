from django.core.validators import DecimalValidator
from django.utils import timezone
from datetime import timedelta

from common import fields as common_fields
from common import page_config


class GoodsFakeField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = "Товар"
    name = 'goods'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'catalogs.GoodsModel'
    model = 'catalogs.GoodsModel'
    data_path = '/app_info/select_list/?model=catalogs.GoodsModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(tp_goodsorders__goods__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(tp_goodsorders__goods__in=value.get('value'))


class AmountFakeField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.DecimalFormField()
    filter_info = page_config.DecimalFilterField()
    tp_info = page_config.TPDecimalColumn()
    filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}
    internal_type = "DecimalField"
    name = 'amount'
    verbose_name = 'Сумма'
    default = None
    blank = True
    validators = (DecimalValidator(max_digits=15, decimal_places=2),)
    decimal_places = 2
    max_digits = 15

    def to_filter(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.filter(amount__gte=start)
        if end is not None:
            queryset = queryset.filter(amount__lte=end)
        return queryset

    def to_exclude(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.exclude(amount__gte=start)
        if end is not None:
            queryset = queryset.exclude(amount__lte=end)
        return queryset


class QuantityFakeField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.DecimalFormField()
    filter_info = page_config.DecimalFilterField()
    tp_info = page_config.TPDecimalColumn()
    filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}
    internal_type = "DecimalField"
    name = 'quantity'
    verbose_name = 'Количество'
    default = None
    blank = True
    validators = (DecimalValidator(max_digits=15, decimal_places=3),)
    decimal_places = 3
    max_digits = 15

    def to_filter(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.filter(quantity__gte=start)
        if end is not None:
            queryset = queryset.filter(quantity__lte=end)
        return queryset

    def to_exclude(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.exclude(quantity__gte=start)
        if end is not None:
            queryset = queryset.exclude(quantity__lte=end)
        return queryset


class IsDailyCreatedField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'is_daily_created_filter'
    verbose_name = 'Сегодня создан'
    default = None
    blank = True

    def get_time(self):
        local_datetime = timezone.now()
        local_time = local_datetime.timetz()
        result = local_datetime - timedelta(
            hours=local_time.hour,
            minutes=local_time.minute,
            seconds=local_time.second,
            microseconds=local_time.microsecond
        )
        return result

    def to_filter(self, queryset, value):
        local_time = self.get_time()
        if value.get('value') is True:
            return queryset.filter(created_at__gte=local_time)
        else:
            return queryset.filter(created_at__lt=local_time)

    def to_exclude(self, queryset, value):
        local_time = self.get_time()
        if value.get('value') is True:
            return queryset.filter(created_at__lt=local_time)
        else:
            return queryset.filter(created_at__gte=local_time)


class IsDailyDeliveryField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'is_daily_delivery_filter'
    verbose_name = 'Сегодня отгрузка'
    default = None
    blank = True

    def get_time(self):
        local_datetime = timezone.now()
        local_time = local_datetime.timetz()
        result = local_datetime - timedelta(
            hours=local_time.hour,
            minutes=local_time.minute,
            seconds=local_time.second,
            microseconds=local_time.microsecond
        )
        return result

    def to_filter(self, queryset, value):
        local_time = self.get_time()
        if value.get('value') is True:
            return queryset.filter(delivery_date_plan_gte__gte=local_time)
        else:
            return queryset.filter(delivery_date_plan_gte__lt=local_time)

    def to_exclude(self, queryset, value):
        local_time = self.get_time()
        if value.get('value') is True:
            return queryset.filter(delivery_date_plan_gte__lt=local_time)
        else:
            return queryset.filter(delivery_date_plan_gte__gte=local_time)


class WithoutLogisticTaskFilterField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'without_logistic_task_filter'
    verbose_name = 'Нераспределенные'
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(pickup=False, task_delivery_point__isnull=True)
        else:
            return queryset.filter(pickup=False, task_delivery_point__isnull=False)

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(pickup=False, task_delivery_point__isnull=False)
        else:
            return queryset.filter(pickup=False, task_delivery_point__isnull=True)