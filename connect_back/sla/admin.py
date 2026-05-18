from django.contrib import admin

from . import models


class SlaValueSourceInline(admin.TabularInline):
    model = models.SLAValueSourceModel
    fields = (
        'related_object',
        'description',
        'first_reaction_time',
        'solve_time',
    )
    fk_name = 'owner'
    extra = 0
    autocomplete_fields = ('related_object',)


@admin.register(models.SLAModel)
class SLAAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contractor',
        'level',
        'name',
        'color',
        'first_reaction_time',
        'solve_time',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )
    search_fields = ('name', 'contractor__name',)
    autocomplete_fields = ('contractor',)
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('-created_at',)


@admin.register(models.SLARelatedObjectModel)
class SLARelatedObjectModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sla',
        'related_object',
        'author',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ('sla', 'related_object',)
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('-created_at',)


@admin.register(models.SLAValueModel)
class SlaValueModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'related_object',
    )
    autocomplete_fields = ('related_object',)
    inlines = (SlaValueSourceInline,)
