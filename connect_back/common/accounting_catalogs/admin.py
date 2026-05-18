from django.contrib import admin
from . import models


@admin.register(models.BudgetFunctionalGroupModel)
class FunctionalGroupModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = (
        'name',
        'code',
    )

@admin.register(models.BudgetFunctionalSubgroupModel)
class FunctionalSubgroupModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'functional_group',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'code', 'functional_group__code')

@admin.register(models.BudgetProgramAdministratorModel)
class BudgetProgramAdministratorModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'f_group',
        'functional_subgroup',
        'code',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'code', 'functional_subgroup__code', 'functional_subgroup__functional_group__code')


@admin.register(models.BudgetProgramModel)
class ProgramModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'budget_program_administrator',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'code', 'budget_program_administrator__code')


@admin.register(models.BudgetSubprogramModel)
class SubprogramModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'program',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'code', 'program__code', 'program__budget_program_administrator__code',)


@admin.register(models.KATOCodesModel)
class KATOCodesModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'ab',
        'cd',
        'ef',
        'hij',
        'k',
        'name',
        'nn',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('code', 'name',)
