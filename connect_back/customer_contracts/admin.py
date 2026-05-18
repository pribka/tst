from django.contrib import admin

from . import models
from .utils import ensure_deal_for_customer_contract


class CustomerContractProjectInline(admin.TabularInline):
    model = models.CustomerContractProjectModel
    fields = (
        'project',
    )
    extra = 0
    autocomplete_fields = ('project',)
    fk_name = 'customer_contract'


class CustomerContractSubjectInline(admin.TabularInline):
    # CRM: предмет договора можно быстро сверить прямо из карточки договора.
    model = models.CustomerContractSubjectModel
    fields = (
        'source_interest',
        'source_need',
        'goods',
        'quantity',
        'price',
        'amount',
        'comment',
    )
    readonly_fields = ('amount',)
    extra = 0
    autocomplete_fields = ('source_interest', 'goods',)
    fk_name = 'customer_contract'


@admin.register(models.CustomerContractStatusModel)
class CustomerContractStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'created_at',
        'updated_at',
        'is_active',
    )
    ordering = ('sort', 'name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name', 'code',)


@admin.register(models.CustomerContractModel)
class CustomerContractAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'external_id',
        'number',
        'status',
        'deal',
        'organization',
        'customer_card',
        'legal_entity',
        'source',
        'contract_date',
        'hours_plan',
        'hours_fact',
        'is_signed',
        'is_exists',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = (
        'status',
        'deal',
        'organization',
        'customer_card',
        'legal_entity',
        'source',
        'external_customer',
    )
    ordering = ('-created_at',)
    search_fields = ('number',)
    inlines = (CustomerContractSubjectInline, CustomerContractProjectInline,)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ensure_deal_for_customer_contract(obj)


@admin.register(models.CustomerContractSubjectModel)
class CustomerContractSubjectAdmin(admin.ModelAdmin):
    # CRM: отдельная админка нужна для диагностики цепочки
    # "интерес -> потребность -> предмет договора -> заказ".
    list_display = (
        'id',
        'customer_contract',
        'source_interest',
        'goods',
        'quantity',
        'price',
        'amount',
        'is_active',
        'created_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at', 'amount',)
    autocomplete_fields = ('customer_contract', 'source_interest', 'goods',)
    search_fields = ('name', 'article_number', 'comment',)
