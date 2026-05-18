
from django.db.models import Q

from common import page_config
from common.current_profile.middleware import get_current_authenticated_profile
from common.fields import FakeField


class DepartmentsFilterField(FakeField):
    """В зависимости от значения фильтра departments_filter показывает:
    '' - цели организации и ее отделов
    'without_departments' - цели организации (без отделов)
    'only_departments' - цели только отделов (без целей организации). Возмжоно на фронте этот вариант не нужен.
    """
    filter_info = page_config.CharFilterField()
    name = 'departments_filter'
    verbose_name = 'Отделы'
    max_length = 100
    default = None
    blank = True

    def get_lookup(self, value):
        lookup = Q()
        permitted_values = ['without_departments', 'only_departments']
        value = value.get('value')
        if not value:
            return lookup
        if not isinstance(value, str):
            return lookup
        if value not in permitted_values:
            return lookup
        if value == 'without_departments':
            lookup &= Q(department__isnull=True)
        elif value == 'only_departments':
            lookup &= Q(department__isnull=False)
        return lookup

    def to_filter(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.filter(lookup)
        return queryset

    def to_exclude(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.exclude(lookup)
        return queryset


class CurrentContractorDepartmentsFKField(page_config.ForeignKeyFilterField):
    def get_dict(self):
        data = super().get_dict()
        user = get_current_authenticated_profile()
        if user:
            data["widget"]["filters"] = [{
                'type': 'defined',
                'name': 'contractor_id',
                'value': user.current_contractor_id
            }]
        return data


class UserCurrentContractorDepartmentsFilterField(FakeField):
    filter_info = CurrentContractorDepartmentsFKField()
    model = 'catalogs.ContractorDepartmentModel'
    to_fields = ('id',)
    name = 'user_current_contractor_departments_filter'
    verbose_name = 'Отдел'
    max_length = 100
    default = None
    blank = True

    def get_lookup(self, value):
        lookup = Q()
        value = value.get('value')
        if not value:
            return lookup
        if not isinstance(value, list):
            return lookup
        lookup &= Q(department_id__in=value)
        return lookup

    def to_filter(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.filter(lookup)
        return queryset

    def to_exclude(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.exclude(lookup)
        return queryset


class ObjectivePeriodDateFilterField(page_config.DateFilterField):
    widget_type = 'Period'
    date_format = 'YYYY-MM-DD'
    ranges: list = [  # Предустановленные периоды
        'year',  # Год
        'half_year_1',  # Первое полугодие
        'half_year_2',  # Второе полугодие
        'quarter_1',  # Первый квартал
        'quarter_2',  # Второй квартал
        'quarter_3',  # Третий квартал
        'quarter_4',  # Четвертый квартал
        'year_prev_1',  # Прошлый год
        'year_prev_2'  # Позапрошлый год
    ]

    def get_dict(self):
        data = super().get_dict()
        data['widget']['ranges'] = self.ranges
        return data


class ObjectivePeriodFilterField(FakeField):
    filter_info = ObjectivePeriodDateFilterField()
    verbose_name = 'Период'
    name = 'objective_period_filter'
    default = None
    blank = True
    max_length = 2
    internal_type = 'DateField'

    def get_lookup(self, value):
        lookup = Q()
        if not isinstance(value, dict):
            return lookup

        start = value.get('start', None)
        end = value.get('end', None)
        if start and end:
            lookup &= Q(date_end__gte=start, date_end__lte=end)
        return lookup

    def to_filter(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.filter(lookup)
        return queryset

    def to_exclude(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.exclude(lookup)
        return queryset
