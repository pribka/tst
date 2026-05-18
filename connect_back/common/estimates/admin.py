from django.contrib import admin
from . import models


@admin.register(models.AccumulationRegister)
class AccumulationRegisterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'doc_fact',
        'registrar',
        'quantity_fact',
        'amount_fact',
        'is_active',
        'section',
        'author',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    ordering = ('-created_at',)
    autocomplete_fields = (
        'calc_object',
        'doc_fact',
        'registrar',
        'stuff',
        'base_measure_unit',
        'measure_unit',
        'work_type',
    )
    readonly_fields = ('author', 'created_at', 'updated_at', 'deleted_at',)


@admin.register(models.RegistrarSectionModel)
class RegistrarSectionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'author',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    ordering = ('sort', 'name')
    readonly_fields = ('author', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('name', 'code',)


@admin.register(models.RegistrarDataSourceModel)
class RegistrarDataSourceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'author',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    ordering = ('sort', 'name')
    readonly_fields = ('author', 'created_at', 'updated_at', 'deleted_at')
    search_fields = ('name', 'code',)

