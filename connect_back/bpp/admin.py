from django.contrib import admin
from . import models


@admin.register(models.EditionModel)
class EditionAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)


@admin.register(models.EditionPartModel)
class EditionPartAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)


@admin.register(models.EditionUnitModel)
class EditionUnitAdmin(admin.ModelAdmin):
    list_display = (
        'invoice',
        'warehouse',
        'price',
        'inventory_number'
    )
    readonly_fields = ('author',)


@admin.register(models.TPReceiptInvoiceEditionModel)
class TPReceiptInvoiceEditionModelAdmin(admin.ModelAdmin):
    list_display = ('owner',
                    'edition',
                    'price',
                    'warehouse'
                    )
    list_filter = ('edition', 'owner')
    readonly_fields = ('author',)


@admin.register(models.ReceiptInvoiceEditionUnitModel)
class IncomingInvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)


@admin.register(models.ActWriteOffEditionUnitModel)
class ActWriteOffEditionUnitModelAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)


@admin.register(models.TPActWriteOffEditionModel)
class TPActWriteOffEditionModelAdmin(admin.ModelAdmin):
    list_display = ('owner',
                    'edition',
                    'unit',
                    )
    readonly_fields = ('author',)


@admin.register(models.EditionAuthorModel)
class EditionAuthorAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)


@admin.register(models.TPEditionUnitTransferModel)
class TPActWriteOffEditionModelAdmin(admin.ModelAdmin):
    list_display = ('owner',
                    'edition',
                    'unit',
                    'recipient_warehouse',
                    )
    readonly_fields = ('author',)


@admin.register(models.EditionUnitTransferModel)
class EditionAuthorAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)
# Register your models here.
