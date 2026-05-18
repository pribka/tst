from django.contrib import admin

# Register your models here.
from . import models


class RoleAccessModelInline(admin.TabularInline):
    model = models.RoleAccessModel
    extra = 0


@admin.register(models.RoleModel)
class RoleModelAdmin(admin.ModelAdmin):
    inlines = [RoleAccessModelInline]


@admin.register(models.AccessProfileModel)
class AccessProfileModelAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AccessTemplateModel)
class AccessTemplateModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_field']


@admin.register(models.UserAccessProfileModel)
class UserAccessProfileModelAdmin(admin.ModelAdmin):
    pass


@admin.register(models.SessionParameterModel)
class SessionParameterModelAdmin(admin.ModelAdmin):
    # list_editable = ['organization']
    autocomplete_fields = ['user', 'organization']
    list_display = ['user']
