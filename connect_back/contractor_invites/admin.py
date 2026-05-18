from django.contrib import admin

from . import models


@admin.register(models.ContractorInviteStatusModel)
class ContractorInviteStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'sort',
    )


@admin.register(models.ContractorInviteModel)
class ContractorInviteModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contractor_owner',
        'contractor_parent',
        'contractor',
        'is_active',
        'author',
        'created_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('contractor_owner', 'contractor_parent', 'contractor',)
