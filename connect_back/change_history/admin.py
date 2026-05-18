from django.contrib import admin
from . import models


@admin.register(models.ChangeHistoryActionModel)
class ChangeHistoryActionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
    )
    readonly_fields = ('author',)
    search_fields = ('name',)
    ordering = ('name', 'created_at',)


@admin.register(models.ChangeHistoryObjectPropertyModel)
class ChangeHistoryObjectPropertyModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'prefix',
        'model_label',
        'created_at',
    )
    readonly_fields = ('author',)
    search_fields = ('name',)
    ordering = ('name', 'created_at',)
    list_filter = ('prefix', 'model_label',)


@admin.register(models.ChangeHistoryModel)
class ChangeHistoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'related_object',
        'action',
        'action_date',
        'created_at',
        'object_property'
    )
    autocomplete_fields = ('related_object',)
    readonly_fields = ('author', 'created_at',)
    list_filter = ('action', 'object_property',)
    ordering = ('-action_date', '-created_at',)


