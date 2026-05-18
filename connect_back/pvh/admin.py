from django.contrib import admin
from . import models


class PropertyInline(admin.TabularInline):
    model = models.PVHPropertyThrough
    fields = (
        'property',
        'name',
        'condition',
        'widget',
        'sort',
    )
    extra = 0


@admin.register(models.PVH)
class PVHAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'content_type',
        'created_at',
    )
    search_fields = ('content_type',)
    readonly_fields = ('author', 'created_at', 'updated_at', 'deleted_at',)
    inlines = [PropertyInline]


class PropertyValueInline(admin.TabularInline):
    model = models.PVHPropertyValue
    fk_name = 'owner'
    extra = 1


class ExtraCatalogPVHPropertyInline(admin.TabularInline):
    model = models.ExtraCatalogPropertyThroughModel
    fields = (
        'extra_catalog',
    )
    extra = 0
    fk_name = 'pvh_property'
    autocomplete_fields = ('extra_catalog',)


@admin.register(models.PVHProperty)
class PVHPropertyModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'multi',
        'property_type',

    )
    search_fields = ('code',)
    inlines = (ExtraCatalogPVHPropertyInline,)


@admin.register(models.PVHPropertyValue)
class PVHPropertyValueAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'prop',
        'value',
    )
    autocomplete_fields = ('owner', 'value_fk', 'prop')
    readonly_fields = ('author', 'created_at', 'updated_at', 'deleted_at',)
    search_fields = ('prop', 'owner',)


class PVHPropertyExtraCatalogInline(admin.TabularInline):
    model = models.ExtraCatalogPropertyThroughModel
    fields = (
        'pvh_property',
    )
    extra = 0
    fk_name = 'extra_catalog'
    autocomplete_fields = ('pvh_property',)

@admin.register(models.ExtraCatalogModel)
class ExtraCatalogModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
        'author',
    )
    search_fields = ('pvh_properties__name', 'name', 'code',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (PVHPropertyExtraCatalogInline,)
