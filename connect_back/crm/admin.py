from django.contrib import admin

from common.admin import FileBaseModelInline

from . import models


class CoExecutorsInline(admin.TabularInline):
    model = models.OrderCoExecutorModel
    fields = ('user',)
    autocomplete_fields = ('user',)
    extra = 0


@admin.register(models.OrderManagerModel)
class OrderManagerModelAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
    )


@admin.register(models.GoodsOrderExecuteStatusModel)
class GoodsOrderExecuteStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'color',
        'icon'
    )


class TPOrderGoodsModelInline(admin.TabularInline):
    model = models.TPGoodsOrderModel
    list_display = (
        'id',
        'goods',
        'quantity',
        'amount',
        'warehouse',
    )
    fk_name = 'owner'
    extra = 0
    autocomplete_fields = ('goods', 'warehouse', 'goods_for_print')


class CashPaymentOrderModelInline(admin.TabularInline):
    model = models.CashPaymentOrderModel
    extra = 0
    fk_name = 'owner'
    list_display = (
        'id',
        'cash_pay_type',
        'amount',
        'created_at',
    )


@admin.register(models.ShoppingCartModel)
class ShoppingCartModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'cart_type',
        'goods',
        'warehouse',
        'created_at',
    )
    readonly_fields = ('author',)
    autocomplete_fields = ('user', 'goods',)
    ordering = ('user', 'cart_type', '-created_at')
    list_filter = ('cart_type',)


@admin.register(models.GoodsOrderModel)
class GoodsOrderModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'counter',
        'user',
        'contract',
        'contractor',
        'warehouse',
        'is_active',
        'created_at',
        'reason',
    )
    autocomplete_fields = ('user', 'contract', 'contractor', 'warehouse', 'reason', 'counter', 'contractor_member',)
    list_filter = ('warehouse',)
    readonly_fields = ['pay_file', 'order_form']
    inlines = (TPOrderGoodsModelInline, FileBaseModelInline, CashPaymentOrderModelInline, CoExecutorsInline)


@admin.register(models.OrderOperationTypeModel)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
    )


@admin.register(models.OrderCounterModel)
class OrderCounterModelAdmin(admin.ModelAdmin):
    search_fields = ('id',)


@admin.register(models.PayTypeModel)
class PayTypeModelAdmin(admin.ModelAdmin):
    search_fields = ('code', 'name',)
    list_display = ('id', 'code', 'name', 'required', 'is_active')
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.DeliveryStatusModel)
class DeliveryStatusModelAdmin(admin.ModelAdmin):
    search_fields = ('code', 'name',)
    list_display = ('id', 'code', 'name', 'color', 'icon', 'sort', 'is_active')
    readonly_fields = ('author',)
    ordering = ('sort', 'code', 'name')


@admin.register(models.PaymentStatusModel)
class PaymentStatusModelAdmin(admin.ModelAdmin):
    search_fields = ('code', 'name',)
    list_display = ('id', 'code', 'name', 'color', 'icon', 'sort', 'is_active')
    readonly_fields = ('author',)
    ordering = ('sort', 'code', 'name',)


@admin.register(models.CartTypeModel)
class PaymentStatusModelAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CashPayTypeModel)
class CashPayTypeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'is_active')
    readonly_fields = ('author',)


@admin.register(models.DealStageModel)
class DealStageModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'color', 'sort', 'is_final', 'is_success', 'is_active')
    readonly_fields = ('author',)
    search_fields = ['id','name']
    ordering = ('sort', 'name')


@admin.register(models.DealModel)
class DealModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stage', 'customer_card', 'responsible', 'planned_close_date', 'updated_at', 'is_active')
    autocomplete_fields = ('stage', 'responsible', 'customer_card', 'source_ticket', 'members', 'observers')
    readonly_fields = ('author',)
    search_fields = ['id']
