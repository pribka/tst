from django.contrib import admin
from django.db.models import TextField
from ckeditor.fields import CKEditorWidget

from . import models


class ContractorDocMembersInline(admin.TabularInline):
    model = models.ContractorDocMemberModel
    fields = (
        'user',
    )
    fk_name = 'contractor_doc'
    extra = 0
    autocomplete_fields = ('user', )


@admin.register(models.ContractorDocDeliveryStatusModel)
class ContractorDocDeliveryStatusModelAdmin(admin.ModelAdmin):
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


@admin.register(models.ContractorDocApprovalStatusModel)
class ContractorDocApprovalStatusModelAdmin(admin.ModelAdmin):
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


@admin.register(models.ContractorDocTypeModel)
class ContractorDocTypeModelAdmin(admin.ModelAdmin):
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


@admin.register(models.ContractorDocTemplateModel)
class ContractorDocTemplateModelAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': CKEditorWidget}}
    list_display = (
        'id',
        'code',
        'name',
        'doc_type',
        'author',
        'created_at',
        'updated_at',
    )

    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'name',
        'code',
    )


@admin.register(models.ContractorDocModel)
class ContractorDocModelAdmin(admin.ModelAdmin):
    formfield_overrides = {TextField: {'widget': CKEditorWidget}}

    list_display = (
        'id',
        'name',
        # 'contractor',
        # 'customer',
        'template',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )

    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = (
        # 'contractor',
        # 'customer',
        'template',
    )

    inlines = (ContractorDocMembersInline,)
