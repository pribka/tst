from django.contrib import admin

from common.admin import FileBaseModelInline

from . import models


class FundingSourceAndAmountModelInline(admin.TabularInline):
    model = models.FundingSourceAndAmountModel
    fields = (
        'funding_source',
        'amount',
        'comment',
    )
    fk_name = 'invest_project_info'
    extra = 0


@admin.register(models.InvestProjectInfoModel)
class InvestProjectInfoModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'location',
        'organization',
        'category',
        'project_name',
        'company_name',
        'has_documentation',
        'installation_stage',
        'created_at',
        'is_active',

    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    autocomplete_fields = (
        'organization',
        'location',
    )
    search_fields = ('organization', 'company_name', 'company_bin', 'project_name', 'cadaster')
    inlines = (FundingSourceAndAmountModelInline, FileBaseModelInline)


@admin.register(models.InvestProjectFundingSourceModel)
class InvestProjectFundingSourceModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'short_name',
        'name',
        'created_at',
        'is_active',
    )
    ordering = ('name', 'created_at',)
    readonly_fields = ('author', 'created_at',)
    search_fields = ('name',)




@admin.register(models.InvestProjectCategoryModel)
class InvestProjectCategoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
        'is_active',
    )
    ordering = ('name', '-created_at',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name',)


@admin.register(models.InvestProjectSubcategoryModel)
class InvestProjectSubcategoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'category',
        'created_at',
        'is_active',
    )
    ordering = ('name', '-created_at',)
    autocomplete_fields = ('category',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name',)


@admin.register(models.InvestProjectMeasureUnitModel)
class InvestProjectMeasureUnitModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'name_short',
        'name_plural',
        'created_at',
        'is_active',
    )
    ordering = ('name', '-created_at',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name',)


@admin.register(models.InvestProjectStageModel)
class InvestProjectStageModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
    )
    ordering = ('sort', '-created_at',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name', 'code')


@admin.register(models.InvestProjectPermissionTypeModel)
class InvestProjectPermissionTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
    )


class InvestProjectStatusDependsModelInline(admin.TabularInline):
    model = models.InvestProjectStatusDependsModel
    extra = 0
    fields = (
        'status',
    )
    fk_name = 'next_status'


@admin.register(models.InvestProjectStatusModel)
class InvestProjectStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'sort',
        'color',
        'btn_title',
    )
    readonly_fields = ('author',)
    ordering = ('sort',)
    list_editable = ['sort']
    inlines = (InvestProjectStatusDependsModelInline,)
