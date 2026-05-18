from django.contrib import admin

from . import models


@admin.register(models.ReactionModel)
class ReactionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'icon',
        'name',
        'sort',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', '-created_at',)
    search_fields = ('code', 'name', 'icon',)
    list_editable = ('sort',)


@admin.register(models.ReactionObjectModel)
class ReactionObjectAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'related_object',
        'user',
        'reaction',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('reaction__name', 'user__user__last_name', 'user__user__first_name',)
    ordering = ('-created_at',)
    autocomplete_fields = ('related_object', 'user', 'reaction',)



