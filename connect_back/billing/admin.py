from django.contrib import admin

from contractor_permissions.models import TariffAccessGroupThrough, TariffAppSectionThrough
from . import models


class TariffDiscountInlineAdmin(admin.TabularInline):
    model = models.TariffDiscountModel

    fk_name = 'tariff'
    extra = 0
    fields = (
        'value',
        'date_start',
        'date_end'
    )


class TariffAccessGroupInline(admin.TabularInline):
    model = TariffAccessGroupThrough
    fk_name = 'tariff'
    extra = 0
    fields = (
        'access_group',
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "access_group":
            kwargs["queryset"] = db_field.related_model.objects.filter(is_predefined=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TariffAppSectionInline(admin.TabularInline):
    model = TariffAppSectionThrough
    fields = (
        'app_section',
    )
    extra = 0
    fk_name = 'tariff'


@admin.register(models.TariffModel)
class TariffModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'modules',
        'created_at',
        'updated_at',
        'is_active',
    )

    ordering = ('name', 'created_at',)
    search_fields = ('name',)
    readonly_fields = ('updated_at', 'created_at', 'author',)
    inlines = (TariffDiscountInlineAdmin, TariffAccessGroupInline, TariffAppSectionInline)


@admin.register(models.ContractorTariffModel)
class ContractorTariffModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contractor',
        'tariff',
        'created_at',
        'updated_at',
    )
    search_fields = ('contractor__name', 'contractor__full_name', 'tariff__name',)
    ordering = ('-created_at',)
    autocomplete_fields = ('contractor', 'tariff')
    list_filter = ('tariff',)

@admin.register(models.ContractorTariffNotificationLog)
class ContractorTariffNotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_contractor_name",
        "get_tariff_name",
        "notification_type",
        "created_at",
    )
    list_filter = (
        "notification_type",
        "created_at",
    )
    search_fields = (
        "contractor_tariff__contractor__name",
        "contractor_tariff__contractor__full_name",
        "contractor_tariff__tariff__name",
    )
    autocomplete_fields = ("contractor_tariff",)
    readonly_fields = ("created_at", "updated_at", "author")
    ordering = ("-created_at",)

    def get_contractor_name(self, obj):
        return obj.contractor_tariff.contractor.name if obj.contractor_tariff and obj.contractor_tariff.contractor else "-"
    get_contractor_name.short_description = "Организация"

    def get_tariff_name(self, obj):
        return obj.contractor_tariff.tariff.name if obj.contractor_tariff and obj.contractor_tariff.tariff else "-"
    get_tariff_name.short_description = "Тариф"
