from django.db.models import TextField
from django.contrib import admin

from prettyjson.widgets import PrettyJSONWidget

from . import models


@admin.register(models.AppInfo)
class AppInfoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'created_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('code', 'name')
    formfield_overrides = {
        TextField: {'widget': PrettyJSONWidget}
    }


@admin.register(models.CustomRoutesModel)
class CustomRoutesModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'is_active',
        'created_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('author',)
    formfield_overrides = {
        TextField: {'widget': PrettyJSONWidget}
    }
