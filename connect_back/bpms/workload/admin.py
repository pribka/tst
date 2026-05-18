from django.contrib import admin

from . import models as wl_models


@admin.register(wl_models.WorkScheduleModel)
class WorkScheduleModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'profile',
        'color',
        'work_days',
        'start_hour',
        'end_hour',
        'break_exist',
        'break_start',
        'break_end',
        'work_hours',
    )
    autocomplete_fields = (
        'profile',
    )


@admin.register(wl_models.ExceptionTypeModel)
class ExceptionTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )


@admin.register(wl_models.ExceptionDatesModel)
class ExceptionDatesModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'exception',
        'start_date',
        'end_date',
    )


class ExceptionDatesInline(admin.TabularInline):
    model = wl_models.ExceptionDatesModel
    extra = 0
    fk_name = 'exception'


@admin.register(wl_models.ExceptionModel)
class ExceptionModelAdmin(admin.ModelAdmin):
    inlines = (ExceptionDatesInline,)
    list_display = (
        'id',
        'profile',
        'exception_type',
        'start_date',
        'end_date',
        'is_repeatable',
        'repeat_frequency',
        'repeat_end',
        'start_hour',
        'end_hour',
    )
    autocomplete_fields = (
        'profile',
    )


@admin.register(wl_models.MembersListModel)
class MembersListModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'related_object',
        'members',
    )
    autocomplete_fields = (
        'related_object',
    )


@admin.register(wl_models.WorkLoadModel)
class WorkLoadModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'profile',
        'overload',
        'tasks_num',
        'total_duration',
        'percents',
    )
    autocomplete_fields = (
        'profile',
    )
    readonly_fields = (
        'overload',
        'tasks_num',
        'total_duration',
        'percents',
    )


@admin.register(wl_models.TaskDurationModel)
class TaskDurationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task',
        'is_distributed',
        'durations',
    )
