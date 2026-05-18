from django.contrib import admin
from . import models


@admin.register(models.AccountingReportStatusModel)
class AccountingReportStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'color',
        'sort',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)


@admin.register(models.AccountingReportTypeModel)
class AccountingReportTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'widget',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)


@admin.register(models.AccountingReportSubtypeModel)
class AccountingReportSubtypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)




@admin.register(models.SpecificityStructureModel)
class SpecificityStructureAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'code',)

@admin.register(models.ProposalItemModel)
class ProposalItemModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'report',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )


@admin.register(models.RationaleModel)
class RationaleModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'rationale',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('rationale', )


@admin.register(models.FPCReportModel)
class FPCReportModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'number',
        'date',
        'status',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )


@admin.register(models.IpfProposalConsolidationExtraModel)
class IpfProposalConsolidationExtraModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'consolidation_id',
        'number',
        'date',
        'subtype',
    )
    search_fields = (
        'id',
        'consolidation__id',
        'number',
    )
    autocomplete_fields = ('consolidation', )


@admin.register(models.ChangeCalculationReportModel)
class ChangeCalculationReportModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'start',
        'end',
        'status',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'organization__name')
    autocomplete_fields = ('organization',)


@admin.register(models.ChangeCalculationItemModel)
class ChangeCalculationItemModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'report',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    autocomplete_fields = (
        'report',
        'functional_group',
        'functional_subgroup',
        'budget_program_administrator',
        'program',
        'subprogram',
        'specificity',
        'rationale',
    )
