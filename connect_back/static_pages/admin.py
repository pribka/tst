from django.contrib import admin
from . import models


@admin.register(models.StaticPageModel)
class StaticPageModelAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)
    list_display = ('id', 'code', 'name', 'created_at')
    search_fields = ('code', 'name',)
    ordering = ('code', 'name', '-created_at',)
