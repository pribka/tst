from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import IsoDateTimeFromToRangeFilter, NumberFilter
from common.filters import IntegerListFilter, IntegerListExcludeFilter
from django_filters.rest_framework import filters
from django_filters.rest_framework import filters
from . import models


class MeetingFilter(FilterSet):
    date_begin = IsoDateTimeFromToRangeFilter()
    author = IntegerListFilter(field_name='author', lookup_expr='in')
    author__exclude = IntegerListExcludeFilter(field_name='author', lookup_expr='in')
    members = IntegerListFilter(field_name='members', lookup_expr='in')
    members__exclude = IntegerListExcludeFilter(field_name='members', lookup_expr='in')

    class Meta:
        model = models.PlannedMeetingModel
        fields = (
            'name',
            'description',
            'author',
            'members',
            'date_begin',
            'members__exclude',
            'author__exclude',
        )
