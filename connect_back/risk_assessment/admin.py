from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from common.catalogs.admin import LocalPointInline
from . import models




class RiskAssessmentCriteriaInline(admin.TabularInline):
    model = models.RiskAssessmentCriteriaModel
    extra = 0
    fields = (
        'criteria',
        'value',
    )


class AssessmentTypeCriteriaModelInline(admin.TabularInline):
    model = models.AssessmentTypeCriteriaModel
    extra = 0
    fields = (
        'criteria',
        'max_value',
    )


@admin.register(models.AssessmentCriteriaModel)
class AssessmentCriteriaModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
    )
    ordering = ('sort', 'name',)
    readonly_fields = ('author', 'created_at',)


@admin.register(models.RiskAssessmentTypeModel)
class RiskAssessmentTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)
    inlines = (AssessmentTypeCriteriaModelInline,)


@admin.register(models.IssueTypeModel)
class IssueTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)


admin.site.register(models.IssueCategoryModel, MPTTModelAdmin)


@admin.register(models.IssueModel)
class IssueModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'issue_type',
        'number',
        'summary',
        'author',
        'issue_date',
        'created_at',
    )

    readonly_fields = ('author', 'created_at',)
    search_fields = ('number',)
    ordering = ('-created_at',)


@admin.register(models.RiskAssessmentStatusModel)
class RiskAssessmentStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
        'sort',
    )
    readonly_fields = ('created_at', 'author',)
    ordering = ('sort', 'created_at',)


@admin.register(models.RiskAssessmentModel)
class RiskAssessmentModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'assessment_type',
        'status',
        'issue',
        'organization',
        'total_value',
        'created_at',
        'author',
    )

    autocomplete_fields = ('issue', 'organization',)
    ordering = ('-created_at',)
    inlines = (LocalPointInline, RiskAssessmentCriteriaInline,)
    list_filter = ('status', 'assessment_type',)


@admin.register(models.CitizensSocialStatusModel)
class CitizensSocialStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code'
    )


@admin.register(models.PersonalReceptionStatusModel)
class PersonalReceptionStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code'
    )


@admin.register(models.PersonalReceptionModel)
class PersonalReceptionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'issue',
        'social_status',
        'status'
    )
