from django.contrib import admin

from . import models


@admin.register(models.RetrospectiveModel)
class RetrospectiveModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'related_object',
        'retrospective_type',
        'author',
        'created_at',
        'updated_at',
        'deleted_at',
        'is_active',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('-created_at',)


@admin.register(models.RetrospectiveTypeModel)
class RetrospectiveTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
