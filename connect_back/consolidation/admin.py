from ckeditor.fields import CKEditorWidget
from django.contrib import admin
from django.db.models import TextField

from . import models


class AttachmentsInline(admin.TabularInline):
    model = models.ReportFormModel.attachments.through
    autocomplete_fields = ('file', )
    extra = 0


class ConsolidationMembersInline(admin.TabularInline):
    model = models.ConsolidationMemberModel
    fields = (
        'organization',
    )
    fk_name = 'consolidation'
    extra = 0
    autocomplete_fields = ('organization', )


class ReportFileInline(admin.TabularInline):
    model = models.ReportModel.report_files.through
    extra = 0
    autocomplete_fields = ['file',]


class ConsolidationReportsInline(admin.TabularInline):
    model = models.ReportModel
    fk_name = 'parent'
    extra = 0
    fields = ('contractor', 'consolidator', 'status', 'without_attachments')
    autocomplete_fields = ('contractor', 'consolidator', 'status')


@admin.register(models.ConsolidationStatusModel)
class ConsolidationStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'color',
        'is_active',
        'sort',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )


@admin.register(models.ReportFileModel)
class ReportFileModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_generated',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )
    search_fields = (
        'name',
    )


@admin.register(models.ConsolidationFileModel)
class ConsolidationFileModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'author',
    )
    search_fields = ('name', 'code', 'id')


@admin.register(models.ReportStatusModel)
class ReportStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'color',
        'is_active',
        'sort',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )
    search_fields = ('name', 'code')


@admin.register(models.ReportFormModel)
class ReportFormModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'created_at',
        'updated_at',
        'author',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )
    search_fields = (
        'name',
        'code'
    )
    inlines = (AttachmentsInline,)


@admin.register(models.F2GOReportModel)
class F2GOReportModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'organization',
        'report_form',
        'start',
        'end',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )


@admin.register(models.AnalyticReportModel)
class AnalyticReportModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'report_form',
        'name',
        'is_active',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )


@admin.register(models.ReportModel)
class ReportModelAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': CKEditorWidget}}

    list_display = (
        'id',
        'parent',
        'contractor',
        'status',
        'created_at',
        'updated_at',
        'is_active',
        'author',
        'parent_id',
    )

    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )
    search_fields = ('contractor__name', 'contractor__full_name', 'parent__name', 'id', 'parent__id')
    autocomplete_fields = ('parent', 'contractor', 'consolidator')
    inlines = (ReportFileInline,)


@admin.register(models.ConsolidationModel)
class ConsolidationModelAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': CKEditorWidget}}

    list_display = (
        'id',
        'name',
        'status',
        'dead_line',
        'report_form',
        'created_at',
        'author',
        'auto_approve',
        'repeat_to',
        'is_active',
        'is_scheduled',
        'is_template_on',
        'next_creation_date',
        'repeat_period',
        'generate_report_files',
    )

    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )
    search_fields = ('name', 'org_administrator__name', 'id')
    inlines = (ConsolidationMembersInline, ConsolidationReportsInline)
    autocomplete_fields = ('org_administrator', 'consolidator', 'consolidation_files', 'template')
    list_filter = (
        'status',
        'report_form',
        'repeat_to',
        'is_active',
        'is_scheduled',
        'is_template_on',
        'next_creation_date',
    )


@admin.register(models.FileTypeModel)
class FileTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active',
        'widget',
    )


@admin.register(models.ConsolidationFileTypeModel)
class ConsolidationFileTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'is_active'
    )


@admin.register(models.ReportTypeInfoModel)
class ReportTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'is_active'
    )
    search_fields = ('name', 'code')


@admin.register(models.ContractorBalanceModel)
class ContractorBalanceModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'contractor',
        'balance',
        'year'
    )
    search_fields = (
        'contractor__id',
        'contractor__name'
    )
    autocomplete_fields = ('contractor', )


@admin.register(models.ReportPersonalReceptionModel)
class ReportPersonalReceptionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'report',
        'quantity',
        'no_personal_reception'
    )
    search_fields = (
        'report__id',
    )
    autocomplete_fields = (
        'report',
    )
