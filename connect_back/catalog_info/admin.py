from django.contrib import admin

from . import models


class CatalogInfoAppSectionRoleInline(admin.TabularInline):
    model = models.CatalogInfoAppSectionRoleThroughModel
    fields = (
        'app_section_role',
    )
    fk_name = 'catalog_info'
    extra = 0
    autocomplete_fields = ('app_section_role',)


@admin.register(models.CatalogSectionModel)
class CatalogSectionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'sort',
        'created_at',
        'updated_at',
    )
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)
    list_editable = ('sort',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.CatalogInfoModel)
class CatalogInfoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'section',
        'is_active',
        'sort',
        'created_at',
        'updated_at',
    )
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)
    list_editable = ('sort',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (CatalogInfoAppSectionRoleInline,)
