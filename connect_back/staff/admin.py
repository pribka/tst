from django.contrib import admin
from . import models


@admin.register(models.Recruitment)
class RecruitmentModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'doc_num',
        'doc_date',
        'author'
    )


@admin.register(models.TPRecruitmentWorkers)
class TPRecruitmentWorkersModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'author'
    )
    readonly_fields = ('author',)


@admin.register(models.TPRecruitmentAccruals)
class TPRecruitmentWorkersModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'author'
    )
    readonly_fields = ('author',)


@admin.register(models.TypeOfEmployment)
class TypeOfEmploymentModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'author'
    )
    readonly_fields = ('author',)


@admin.register(models.Dismissal)
class DismissalModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'doc_num',
        'doc_date',
        'author'
    )


@admin.register(models.TPDismissalStaff)
class TPDismissalStaffModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'author'
    )
