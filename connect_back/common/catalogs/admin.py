from django.contrib import admin
from django.contrib.gis import admin as geo_admin

from django.contrib import admin, messages
from django.http import HttpResponseRedirect

from common.admin import FileBaseModelInline
from common.catalogs import models

from gallery.admin import GalleryModelInline

from billing.models import ContractorTariffModel


@admin.register(models.LegalEntityModel)
class LegalEntityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'external_id',
        'name',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name', 'external_id',)
    ordering = ('-created_at',)


class LocalPointInline(admin.TabularInline):
    model = models.LocationPointModel
    extra = 0
    fields = (
        'lon',
        'lat',
        'name',
        'address',
        'admin_area'
    )
    autocomplete_fields = ('admin_area',)
    fk_name = 'related_object'


@admin.register(models.LocationPointModel)
class LocationPointModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'address',
        'lat',
        'lon',
        'admin_area',
        'related_object',
        'created_at',
        'created_at',
        'is_active',
    )
    search_fields = ('name', 'address',)
    autocomplete_fields = ('admin_area', 'related_object',)
    readonly_fields = ('author', 'created_at', 'updated_at',)

class GoodsPriceInline(admin.TabularInline):
    model = models.GoodsPriceModel
    extra = 0
    fields = ('price_type', 'price',)


class GoodsRemnantInline(admin.TabularInline):
    model = models.GoodsRemnantModel
    extra = 0
    fields = ('warehouse', 'quantity', 'is_active',)


class BarcodesInline(admin.TabularInline):
    model = models.GoodsBarcodeModel
    extra = 0
    fields = ('barcode',)


class ContractContractorInLine(admin.TabularInline):
    model = models.ContractContractorModel
    extra = 0
    fields = ('contract', 'default',)
    autocomplete_fields = ('contract',)


class ContractorDeliveryPointInline(admin.TabularInline):
    model = models.ContractorDeliveryPointModel
    extra = 0
    fields = ('delivery_point',)
    autocomplete_fields = ('delivery_point',)
    fk_name = 'contractor'


class BankRequisitesInLine(admin.TabularInline):
    model = models.BankRequisitesModel
    extra = 0
    fk_name = 'contractor_member'
    fields = ('bank_name', 'correspondent_account', 'is_default', )


class ClinetContractorInLine(admin.TabularInline):
    model = models.ContractorMemberModel
    extra = 0
    fk_name = 'contractor'
    fields = ('name', 'inn')


class DeliveryAddressInline(admin.TabularInline):
    model = models.DeliveryAddress
    extra = 0
    fields = ('address',)


class WarehouseContractorInline(admin.TabularInline):
    model = models.WarehouseContractorModel
    extra = 0
    fields = ('warehouse',)
    verbose_name = 'Склад клиента'
    verbose_name_plural = 'Склады клиента'


class ContractorTariffInline(admin.TabularInline):
    model = ContractorTariffModel
    extra = 0
    fields = ('tariff',)
    verbose_name = 'Тариф'
    verbose_name_plural = 'Тарифы'


@admin.register(models.CurrencyModel)
class CurrencyModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'icon',
        'is_active',
        'sort',
    )
    list_editable = ('is_active', 'sort',)
    ordering = ('name', 'code')
    readonly_fields = ('author',)
    search_fields = ('name', 'code', 'icon')


@admin.register(models.GoodsCategoryModel)
class GoodsCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'is_active',
    )


@admin.register(models.WarehouseModel)
class WareHouseModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'default_warehouse',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author',)
    ordering = ('-created_at',)
    search_fields = ('name', 'code')
    autocomplete_fields = ('manager',)


@admin.register(models.PriceTypeModel)
class PriceTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author',)
    ordering = ('sort',)
    search_fields = ('name', 'code',)


@admin.register(models.GoodsModel)
class GoodsModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'article_number',
        'name',
        'price_by_catalog',
        'base_measure_unit',
        'popularity',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author',)
    list_editable = ('price_by_catalog', 'base_measure_unit')
    ordering = ('-created_at',)
    inlines = (GoodsPriceInline, FileBaseModelInline, GalleryModelInline, GoodsRemnantInline, BarcodesInline)
    search_fields = ('name', 'article_number',)


@admin.register(models.NomenclatureModel)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'article_number',
        'name',
        'contractor',
        'price_by_catalog',
        'base_measure_unit',
        'show_in_catalog',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author',)
    list_editable = ('price_by_catalog', 'base_measure_unit', 'show_in_catalog')
    ordering = ('-created_at',)
    search_fields = ('name', 'article_number',)
    autocomplete_fields = ('contractor',)


@admin.register(models.DeliveryAddress)
class DeliveryAddressesModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'contractor',
        'address',
        'created_at',
        'is_active',
    )
    readonly_fields = ('author',)
    autocomplete_fields = ('contractor',)
    ordering = ('-created_at',)
    search_fields = ('contractor__name',)


class ProfileContractorInline(admin.TabularInline):
    model = models.ContractorProfileModel
    extra = 0
    list_display = (
        'id',
        'user',
        'contractor'
        'created_at',
    )
    verbose_name = 'Участник организации'
    verbose_name_plural = 'Участники организации'
    autocomplete_fields = ('user', 'contractor',)


class ProfileDepartmentInline(admin.TabularInline):
    model = models.ContractorDepartmentProfileModel
    extra = 0
    list_display = (
        'id',
        'contractor_profile',
    )
    autocomplete_fields = ('contractor_profile',)


class ContractorDepartmentInline(admin.TabularInline):
    model = models.ContractorDepartmentModel
    extra = 0
    list_display = (
        'id',
        'name',
        'is_active',
    )
    fk_name = 'contractor'


@admin.register(models.ContractorProfileModel)
class ContractorProfileModelAdmin(admin.ModelAdmin):
    search_fields = ('contractor__name', 'user__user__first_name', 'user__user__last_name')
    autocomplete_fields = ('contractor', 'user',)


@admin.register(models.ContractorDepartmentModel)
class ContractorDepartmentModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'contractor',
        'is_active',
        'author',
        'created_at',
    )
    readonly_fields = ('author',)
    autocomplete_fields = ('contractor',)
    ordering = ('-created_at',)
    inlines = (ProfileDepartmentInline,)
    search_fields = ('name_ru',)


@admin.register(models.ContractorModel)
class ContractorModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'member_inn',
        'created_at',
        'is_active',
        'budget_program_administrator',
        'code_gu',
        'external_id',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    inlines = (
        ContractorDeliveryPointInline,
        DeliveryAddressInline,
        ProfileContractorInline,
        ContractContractorInLine,
        ClinetContractorInLine,
        WarehouseContractorInline,
        ContractorDepartmentInline,
        ContractorTariffInline,
        FileBaseModelInline,
    )
    search_fields = ('id', 'name_ru', 'name_kk', 'full_name_ru', 'full_name_kk', 'contractor_members__inn')
    autocomplete_fields = ('curator', 'contact_person', 'budget_program_administrator')


@admin.register(models.ContractModel)
class ContractModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'price_type',
        'is_active',
    )
    readonly_fields = ('author',)
    autocomplete_fields = ('payment',)
    search_fields = ('code', 'name', 'id',)


@admin.register(models.PotentialContractorModel)
class PotentialContractorModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        # 'price_type',
        'is_active',
    )
    readonly_fields = ('author',)
    search_fields = ('code', 'name', 'id',)


@admin.register(models.GoodsRemnantModel)
class GoodsRemnantModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'goods',
        'warehouse',
        'quantity',
        'is_active',
    )
    autocomplete_fields = ('goods', 'warehouse',)
    readonly_fields = ('author',)

    search_fields = ('goods__name', 'goods__article_number',)


@admin.register(models.GoodsPriceModel)
class GoodsPriceModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'goods',
        'price_type',
        'price',
        'is_active',
        'created_at',
    )
    readonly_fields = ('author',)
    autocomplete_fields = ('goods',)
    search_fields = ('goods__name', 'goods__article_number')


@admin.register(models.PaymentFormModel)
class PaymentFormAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
    )
    readonly_fields = ('author',)


class PaymentStageInline(admin.TabularInline):
    model = models.PaymentStageModel
    fields = (
        'sort',
        'payment_option',
        'payment_percent',
        'duration',
    )
    fk_name = 'owner'
    ordering = ('sort',)
    extra = 0


@admin.register(models.TypeOrderPaymentModel)
class TypeOrderPaymentModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'payment_form',
        'created_at'
    )
    readonly_fields = ('author',)
    inlines = (PaymentStageInline,)
    search_fields = ('id', 'payment_form__name')


@admin.register(models.GoodsTypeModel)
class GoodsTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
    )


@admin.register(models.DeliveryPointModel)
class DeliveryPointModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'lat',
        'lon'
    )
    search_fields = ('name', 'lat', 'lon')


@admin.register(models.MeasureUnitModel)
class MeasureUnitModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'name_short',
        'sort',
    )
    search_fields = ('name', 'name_short',)
    readonly_fields = ('author',)


@admin.register(models.ContractorMemberModel)
class ContractorMemberModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contractor',
        'created_at',
        'updated_at',
        'is_active',
        'inn',
    )
    autocomplete_fields = ('contractor',)
    readonly_fields = ('author', 'created_at', 'updated_at', 'inn',)
    search_fields = ('id', 'name', 'contractor__name')
    view_on_site = False
    inlines = (
        BankRequisitesInLine,
    )


@admin.register(models.CashUnitModel)
class CashUnitModelAdmin(admin.ModelAdmin):
    list_display = (
        # 'code',
        'name',

    )
    search_fields = ('name',)
    # readonly_fields = ('author',)

@admin.register(models.OfferModel)
class OfferModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
    )
    search_fields = ('id',)


@admin.register(models.UserURLsModel)
class UserURLsModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
    search_fields = ('name',)


@admin.register(models.RegisterHelpModel)
class RegisterHelpModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
    )
    search_fields = ('id',)


@admin.register(models.DeliveryPurposeModel)
class DeliveryPurposeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'purpose',
    )
    search_fields = ('purpose',)


@admin.register(models.ContractorRelationModel)
class ContractorRelationModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contractor_root',
        'contractor_parent',
        'contractor',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ('contractor_parent', 'contractor',)
    readonly_fields = ('created_at', 'updated_at', 'author', 'contractor_root')
    search_fields = (
        'contractor_parent__name',
        'contractor__name',
        'contractor_parent__contractor_members__inn',
        'contractor__contractor_members__inn'
    )


@admin.register(models.ContractorRelationTypeModel)
class ContractorRelationTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'name_parent',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('created_at', 'updated_at', 'author',)
    search_fields = ('name', 'code')


@admin.register(models.BankRequisitesModel)
class BankRequisitesModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'created_at',
    )

    readonly_fields = ('created_at', 'updated_at', 'author',)


@admin.register(models.ContractorProfileRequestModel)
class ContractorProfileRequestModelAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'is_touched',
        'is_approved',
        'user',
        'organization',
    )

    readonly_fields = ('is_touched', 'created_at', 'updated_at', 'author',)

    autocomplete_fields = ('user', 'organization',)

    ordering = ('-created_at',)

    list_filter = ('is_touched', 'is_approved',)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            self.message_user(request, e, level=messages.ERROR)
            return HttpResponseRedirect(request.path)


@admin.register(models.LocationAdminAreaModel)
class LocationAdminAreaModelAdmin(geo_admin.ModelAdmin):
    list_display = (
        'id',
        'parent',
        'osm_id',
        'kato',
        'name_ru',
        'admin_level',
        'sort',
        'is_active',
    )

    search_fields = (
        'osm_id',
        'kato__code',
        'name_ru',
    )
    autocomplete_fields = ('parent',)
    ordering = ('sort', 'admin_level', 'name_ru',)


@admin.register(models.CostItemModel)
class CostItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'contractor',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('contractor',)
    search_fields = ('name', 'code')
    ordering = ('-created_at',)


@admin.register(models.Contractor1CAccessTokenModel)
class Contractor1CAccessTokenAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'contractor',
        'expires_at',
        'last_used_at',
        'is_active',
        'is_expired',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    autocomplete_fields = ('contractor',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    search_fields = ('name', 'contractor__name',)


@admin.register(models.WorkDirectionModel)
class WorkDirectionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'contractor',
        'is_archive',
        'is_active',
        'created_at',
        'updated_at',
        'author',
    )
    autocomplete_fields = ('contractor',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    search_fields = ('name', 'code', 'contractor__name',)


@admin.register(models.ExternalCustomerModel)
class ExternalCustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'full_name',
        'source',
        'is_active',
        'org_admin',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ('org_admin', 'source',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    search_fields = ('inn', 'name', 'full_name',)
