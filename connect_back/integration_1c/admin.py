from django.contrib import admin
from django.db.models import JSONField

from prettyjson.widgets import PrettyJSONWidget


from . import models


class Object1CFieldInline(admin.TabularInline):
    model = models.Object1CField
    fields = (
        'is_active',
        'name',
        'field_1c',
        'field_django',
        'field_search',
        'main_field',
        'is_binary_data',
    )
    extra = 0
    fk_name = 'object_1c'
    ordering = ('-created_at', )


@admin.register(models.Object1C)
class Object1CAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'name_object_1c',
        'organization',
        'model',
        'is_related',
        'create_if_missing',
        'update_if_exist',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    search_fields = ('name', 'name_object_1c', 'model',)
    ordering = ('-created_at',)
    inlines = (Object1CFieldInline,)
    autocomplete_fields = ('model_ct', 'organization',)


@admin.register(models.WriteLog)
class WriteLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ('source',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)

    formfield_overrides = {
            JSONField: {'widget': PrettyJSONWidget}
        }
    list_filter = ('action',)


@admin.register(models.Mapping1C)
class Mapping1CAdmin(admin.ModelAdmin):
    list_display = (
        'name_object_1c',
        'model',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    search_fields = ('name_object_1c', 'model',)
    ordering = ('-created_at',)


@admin.register(models.ModelToIntegrationModel)
class IntegrationModelsAdmin(admin.ModelAdmin):
    list_display = (
        'model_ct',
        'is_active',
    )


# class Profile1CDocumentsParametersModel(admin.TabularInline):
#     model = models.Profile1CDocumentsParametersModel
#     fk_name = 'owner'

@admin.register(models.Profile1CDocumentsModel)
class MyDocAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'name',
        'code',
        'contractor_is_required',
        'member_is_required',
        'contract_is_required',
        'start_date_is_required',
        'end_date_is_required',
    )
    autocomplete_fields = (
        'profile',
    )
    list_filter = (
        'code',
    )
    # inlines = [Profile1CDocumentsParametersModel]
# Register your models here.
