from django.contrib import admin

from . import models


class KeyResultsInlineAdmin(admin.TabularInline):
    model = models.KeyResultsModel

    fk_name = 'objective'
    extra = 0
    fields = (
        'description',
        'operator',
        'metrics',
        'date_start',
        'date_end',
        'base',
        'plan',
        'fact',
        'is_active',
    )
    autocomplete_fields = (
        'operator', 'metrics',
    )


class InitiativesInlineAdmin(admin.TabularInline):
    model = models.InitiativesModel

    fk_name = 'key_result'
    extra = 0
    fields = (
        'related_object_type',
        'related_object',
        'operator',
        'title',
        'description',
        'date_start',
        'date_end',
        'is_completed',
        'is_active',
    )
    autocomplete_fields = (
        'operator',
        'related_object',
    )


@admin.register(models.ValueEffortsModel)
class ValueEffortsModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'sort',
        'color',
        'hex_color',
    )
    ordering = ('sort',)
    list_editable = ['name', 'sort', 'color', 'hex_color',]


@admin.register(models.ObjectiveStatusModel)
class ObjectiveStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'sort',
        'color',
        'hex_color',
        'is_closed',
    )
    ordering = ('sort',)
    list_editable = ['name', 'sort', 'color', 'hex_color',]


@admin.register(models.NotificationFrequencyModel)
class NotificationFrequencyModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'sort',
        'description',
        'cron',
    )
    ordering = ('sort',)
    list_editable = ['name', 'sort', 'cron',]



@admin.register(models.InitiativesRelatedObjectType)
class InitiativesRelatedObjectTypeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'sort',
        'model_label',
    )
    ordering = ('sort',)
    list_editable = ['name', 'sort', 'model_label',]


@admin.register(models.MissionModel)
class MissionModelAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'organization',
        'created_at',
        'is_active'
    )

    search_fields = ('organization__id', 'organization__name',)
    autocomplete_fields = (
        'organization',
    )
    ordering = ('-created_at',)


@admin.register(models.ObjectivesModel)
class ObjectivesModelAdmin(admin.ModelAdmin):
    list_filter = (
        'is_public',
        'status',
        'is_active',
    )

    list_display = (
        'id',
        'organization',
        'department',
        'date_start',
        'date_end',
        'is_public',
        'is_active',
        'notify_at',
    )

    search_fields = ('id' ,'organization__id', 'organization__name', 'objective',)
    autocomplete_fields = (
        'parent',
        'organization',
        'department',
        'owner',
        'operator',
    )
    ordering = ('-created_at',)
    inlines = (KeyResultsInlineAdmin,)


@admin.register(models.KeyResultsModel)
class KeyResultsModelAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'objective',
        'metrics',
        'date_start',
        'date_end',
    )

    search_fields = ('id' ,'objective__id', 'description',)
    autocomplete_fields = (
        'objective',
        'operator',
    )
    ordering = ('-created_at',)
    inlines = (InitiativesInlineAdmin,)


@admin.register(models.InitiativesModel)
class InitiativesModelAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'key_result',
        'related_object_type',
        'date_start',
        'date_end',
        'is_completed',
    )

    search_fields = ('id' ,'key_result__id',)
    autocomplete_fields = (
        'key_result',
        'operator',
        'related_object',
    )
    ordering = ('-created_at',)


@admin.register(models.KeyResultMetricsModel)
class KeyResultMetricsModelAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'description',
        'contractor'
    )

    search_fields = ('id', 'description',)
    autocomplete_fields = (
        'contractor',
    )
    ordering = ('-created_at',)