import json

from django.db.models import Q

from common import page_config
from common.current_profile.middleware import get_current_authenticated_profile
from common.fields import FakeField
from users.utils import get_descendants_departments_related_organizations


class IssueDateFilterField(FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.DateFormField()
    filter_info = page_config.DateFilterField()
    tp_info = page_config.TPDateColumn()
    filter_lookup = {"start": "__lte", "end": "__gte", "value": ""}
    internal_type = "DateField"
    name = 'issue_date_filter'
    verbose_name = 'Дата обращения'
    default = None
    blank = True
    validators = ()

    def to_filter(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.filter(issue__issue_date__gte=start)
        if end is not None:
            queryset = queryset.filter(issue__issue_date__lte=end)
        return queryset

    def to_exclude(self, queryset, value):
        start = value.get('start')
        end = value.get('end')
        if start is None and end is None:
            return queryset
        if start is not None:
            queryset = queryset.exclude(issue__issue_date__gte=start)
        if end is not None:
            queryset = queryset.exclude(issue__issue_date__lte=end)
        return queryset


class IssueNumberFilterField(FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.CharFieldFormField()
    filter_info = page_config.CharFilterField()
    tp_info = page_config.TPStringColumn()
    filter_lookup = {"value": "__icontains"}
    name = 'issue_number_filter'
    verbose_name = 'Номер обращения'
    default = ''
    blank = True
    max_length = 200

    def to_filter(self, queryset, value):
        numbers = value.get('value')
        if isinstance(numbers, str):
            split_numbers = numbers.split(',')
            lookup = Q()
            for each in split_numbers:
                lookup = lookup | Q(issue__number__icontains=each.strip())
            try:
                queryset = queryset.filter(lookup)
            except ValueError:
                pass
        return queryset

    def to_exclude(self, queryset, value):
        numbers = value.get('value')
        if isinstance(numbers, str):
            split_numbers = numbers.split(',')
            lookup = Q()
            for each in split_numbers:
                lookup = lookup | Q(issue__number__icontains=each.strip())
            try:
                queryset = queryset.exclude(lookup)
            except ValueError:
                pass
        return queryset


class TotalValueFilterField(FakeField):
    filter_info = page_config.CharFilterField()
    name = 'total_value_filter'
    verbose_name = 'Баллы'
    max_length = 100
    default = None
    blank = True

    @staticmethod
    def get_lookup(value):
        lookup = Q()
        value = value.get('value')
        if not isinstance(value, list):
            return lookup
        if not value:
            return lookup
        for each in value:
            if each == 'white':
                lookup = lookup | Q(total_value__exact=0)
            elif each == 'yellow':
                lookup = lookup | Q(total_value__gte=1, total_value__lte=2)
            elif each == 'orange':
                lookup = lookup | Q(total_value__gte=3, total_value__lte=5)
            elif each == 'red':
                lookup = lookup | Q(total_value__gte=6)
            else:
                continue
        return lookup

    def to_filter(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.filter(lookup)
        return queryset

    def to_exclude(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.exclude(lookup)
        return queryset


class OrganizationsFilterField(FakeField):
    filter_info = page_config.CharFilterField()
    name = 'organizations_filter'
    verbose_name = 'Организации'
    max_length = 100
    default = None
    blank = True

    def get_lookup(self, value):
        lookup = Q()
        permitted_values = ['only_my', 'descendants']
        value = value.get('value')
        organizations = list()
        if not value:
            return lookup
        if not isinstance(value, str):
            return lookup
        if value not in permitted_values:
            return lookup
        user = get_current_authenticated_profile()
        if value == 'only_my':
            organizations = user.my_organizations
        elif value == 'descendants':
            organizations = get_descendants_departments_related_organizations(
                user.my_organizations,
                include_self=False
            )
        if organizations:
            lookup = lookup | Q(organization_id__in=organizations)
        return lookup

    def to_filter(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.filter(lookup)
        return queryset

    def to_exclude(self, queryset, value):
        lookup = self.get_lookup(value)
        queryset = queryset.exclude(lookup)
        return queryset


class CategoryFilterField(FakeField):
    filter_info = page_config.ForeignKeyFilterField()
    filter_info.widget_type = 'TreeSelect'
    model = 'risk_assessment.IssueCategoryModel'
    to_fields = ('id',)
    name = 'category_filter'
    verbose_name = 'Категория обращения'
    max_length = 100
    default = None
    blank = True

    def to_filter(self, queryset, value):
        categories_list = value.get('value', [])
        if len(categories_list) == 0:
            return queryset
        queryset = queryset.filter(issue__issue_category__in=categories_list)
        return queryset

    def to_exclude(self, queryset, value):
        categories_list = value.get('value', [])
        if len(categories_list) == 0:
            return queryset
        queryset = queryset.exclude(issue__issue_category__in=categories_list)
        return queryset
