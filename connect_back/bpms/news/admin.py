from django.contrib import admin
from . import models


@admin.register(models.CheckedNewsCategoryModel)
class CheckedNewsCategoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'created_at',
        'is_active',
    )
    search_fields = ('user__user__first_name', 'user__user__last_name',)
    readonly_fields = ('author',)
    autocomplete_fields = ('user',)
