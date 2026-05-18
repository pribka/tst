from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import IsoDateTimeFromToRangeFilter, NumberFilter
from .models import TaskModel, TaskOverdue
from common.filters import IntegerListFilter, IntegerListExcludeFilter
from django_filters.rest_framework import filters
from django_filters.rest_framework import filters


# class CustomIsoDateTimeFromToRangeFilter(IsoDateTimeFromToRangeFilter):
#     def filter(sels,qs, value):
#         data = super().filter(qs,value)
#         return data


# Фильтрация задач:
class TaskFilter(FilterSet):
    # dead_line = CustomIsoDateTimeFromToRangeFilter()
    # dead_line = IsoDateTimeFromToRangeFilter()
    created = IsoDateTimeFromToRangeFilter()
    updated = IsoDateTimeFromToRangeFilter()
    deleted = IsoDateTimeFromToRangeFilter()
    status = filters.BaseInFilter()
    status__exclude = filters.BaseInFilter(field_name='status', exclude=True)
    project = IntegerListFilter(field_name='project', lookup_expr='in')
    project__exclude = IntegerListExcludeFilter(field_name='project', lookup_expr='in')
    workgroup = filters.BaseInFilter(field_name='workgroup', lookup_expr='in')
    workgroup__exclude = IntegerListExcludeFilter(field_name='workgroup', lookup_expr='in')
    operator = IntegerListFilter(field_name='operator', lookup_expr='in')
    operator__exclude = IntegerListExcludeFilter(field_name='operator', lookup_expr='in')
    owner = IntegerListFilter(field_name='owner', lookup_expr='in')
    owner__exclude = IntegerListExcludeFilter(field_name='owner', lookup_expr='in')
    author = IntegerListFilter(field_name='author', lookup_expr='in')
    author__exclude = IntegerListExcludeFilter(field_name='author', lookup_expr='in')
    visors = IntegerListFilter(field_name='visors', lookup_expr='in')
    visors__exclude = IntegerListExcludeFilter(field_name='visors', lookup_expr='in')
    priority = IntegerListFilter(field_name='priority', lookup_expr='in')
    finished_date = IsoDateTimeFromToRangeFilter()

    class Meta:
        model = TaskModel
        fields = (
            'name',
            'dead_line',
            'owner',
            'operator',
            'author',
            'visors',
            'status',
            'finished_date',
            'created',
            'updated',
            'deleted',
            'project',
            'workgroup',
            'status__exclude',
            'priority',
        )


class TaskOverdueFilter(FilterSet):
    created = IsoDateTimeFromToRangeFilter()
    updated = IsoDateTimeFromToRangeFilter()
    deleted = IsoDateTimeFromToRangeFilter()
    overdue_date = IsoDateTimeFromToRangeFilter()
    priority = IntegerListFilter(field_name='task__priority', lookup_expr='in', )
    operator = IntegerListFilter(field_name='operator', lookup_expr='in')
    owner = IntegerListFilter(field_name='task__owner', lookup_expr='in')
    project = IntegerListFilter(field_name='task__project', lookup_expr='in')
    status = IntegerListFilter(field_name='task__status', lookup_expr='in')
    finished_date = IsoDateTimeFromToRangeFilter(field_name='task__finished_date')

    class Meta:
        model = TaskOverdue
        fields = (
            'operator',
            'owner',
            'priority',
            'overdue_date',
            'project',
            'status',
            'finished_date',
            'created',
            'updated',
            'deleted',
        )
