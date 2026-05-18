from django.contrib import admin

from . import models


@admin.register(models.FavoriteModel)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'related_object',
        'created_at',
        'updated_at',
        'is_active',
    )
    autocomplete_fields = (
        'user',
        'related_object',
    )
    search_fields = ('user__user__last_name', 'user__user__first_name', 'user__user__email',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
