from django.contrib import admin

from . import models


@admin.register(models.TagModel)
class TagModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name',)


@admin.register(models.TagContractorThrough)
class TagContractorThroughAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tag',
        'contractor',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('contractor', 'tag',)
    search_fields = ('tag__name', 'contractor__name')


@admin.register(models.TagRelatedObjectThrough)
class TagRelatedObjectThroughAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tag',
        'related_object',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('related_object', 'tag',)
    search_fields = ('tag__name',)
