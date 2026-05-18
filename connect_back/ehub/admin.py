from django.contrib import admin
from . import models


@admin.register(models.EhubServerGroupModel)
class EhubServerGroupModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
        'deleted_at',
    )


@admin.register(models.EhubRegionModel)
class EhubRegionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'internal_url',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
        'deleted_at',
    )

@admin.register(models.EhubServerModel)
class EhubServerModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'internal_url',
        'frontend_url',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
        'deleted_at',
    )
