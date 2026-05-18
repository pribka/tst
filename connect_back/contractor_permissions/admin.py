from django.contrib import admin

from nested_inline.admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline

from . import models


class ContractorPermissionRoleProfileInline(NestedTabularInline):
    model = models.ContractorPermissionRoleProfileModel
    list_display = (
        'contractor_profile',
    )
    autocomplete_fields = ('contractor_profile',)
    fk_name = 'contractor_permission_role'
    extra = 0


class PermissionAuxConditionInline(admin.TabularInline):
    model = models.ContractorPermissionAuxConditionModel
    list_display = (
        'aux_condition',
    )
    autocomplete_fields = ('aux_condition',)
    fk_name = 'contractor_permission'
    extra = 0


@admin.register(models.AppSectionRoleThroughModel)
class AppSectionRoleThroughAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'app_section',
        'role',
        'permission_type',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at')
    autocomplete_fields = ('app_section', 'role')
    search_fields = ('app_section__name', 'role__name',)
    ordering = ('app_section__name', 'role__name',)


@admin.register(models.ContractorPermissionTypeModel)
class ContractorPermissionTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'author',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.ContractorPermissionModel)
class ContractorPermissionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'permission_type',
        'author',
        'created_at',
        'updated_at',
    )
    list_filter = ('permission_type',)
    readonly_fields = ('created_at', 'updated_at', 'author',)
    inlines = (PermissionAuxConditionInline,)


class ContractorPermissionAuxConditionInline(NestedTabularInline):
    model = models.ContractorPermissionAuxConditionModel
    list_display = (
        'aux_condition',
    )
    autocomplete_fields = ('aux_condition',)
    extra = 0
    fk_name = 'contractor_permission'
    fields = ('aux_condition',)


class ContractorPermissionModelInlineAdmin(NestedStackedInline):
    model = models.ContractorPermissionModel
    extra = 1
    list_display = (
        'permission_type',
    )
    fk_name = 'contractor_permission_role'
    inlines = (ContractorPermissionAuxConditionInline,)
    fields = ('permission_type',)


@admin.register(models.ContractorPermissionRoleModel)
class ContractorPermissionRoleModelAdmin(NestedModelAdmin):
    list_display = (
        'id',
        'name',
        'contractor',
        'author',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('contractor',)
    inlines = (ContractorPermissionRoleProfileInline, ContractorPermissionModelInlineAdmin,)


# Права доступа и видимость разделов:

class AccessGroupAppSectionRoleThroughInline(admin.TabularInline):
    model = models.AccessGroupAppSectionRoleThrough
    fields = (
        'app_section_role',
    )
    autocomplete_fields = ('app_section_role',)
    fk_name = 'access_group'
    extra = 0


@admin.register(models.AccessGroupMemberThroughModel)
class AccessGroupMemberModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'member',
        'access_group',
        'created_at',
    )
    search_fields = ('member__user__user__first_name', 'member__user__user__last_name', 'access_group__name')
    autocomplete_fields = ('member', 'access_group',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    list_filter = ('access_group',)


@admin.register(models.AccessGroupModel)
class AccessGroupModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_predefined',
        'contractor',
        'is_active',
    )
    search_fields = ('name',)
    list_filter = ('is_predefined', 'is_active',)
    ordering = ('-is_predefined', 'contractor', 'name')
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('contractor',)
    inlines = (AccessGroupAppSectionRoleThroughInline,)


class AppSectionRoleThroughInline(admin.TabularInline):
    model = models.AppSectionRoleThroughModel
    fields = (
        'role',
        'routes_meta',
        'permission_type',
        'created_at',
    )
    readonly_fields = ('created_at',)
    fk_name = 'app_section'
    extra = 0


@admin.register(models.AppSectionModel)
class AppSectionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (AppSectionRoleThroughInline,)
    search_fields = ('name', 'code')


@admin.register(models.AppSectionRoleModel)
class AppSectionRoleModelAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code',)
