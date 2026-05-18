from django.contrib import admin

from . import models


@admin.register(models.Configuration1cModel)
class Configuration1cModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    readonly_fields = ('author',)


@admin.register(models.Tariff1CModel)
class Tariff1CModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    readonly_fields = ('author',)


@admin.register(models.TicketTypeModel)
class TicketTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    readonly_fields = ('author',)


@admin.register(models.TicketTypeOptionModel)
class TicketTypeOptionModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    readonly_fields = ('author',)


@admin.register(models.TicketModel)
class TicketModelAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'created_at',
        'tarif',
        'admin_status'
    )
