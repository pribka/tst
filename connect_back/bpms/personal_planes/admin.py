from django.contrib import admin
from . import models


@admin.register(models.PersonalPlaneStatusModel)
class PersonalPLaneStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
        'updated_at',
        'is_active',
    )
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


class PersonalPlaneItemInline(admin.TabularInline):
    model = models.PersonalPlaneItemModel
    fields = (
        'task',
        'description',
        'work_type',
        'duration_plane',
        'duration_fact',
        'is_result',
    )
    fk_name = 'plane'
    autocomplete_fields = ('task',)
    extra = 0


@admin.register(models.PersonalPlaneModel)
class PersonalPlaneModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'plane_date',
        'author',
        'is_active',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (PersonalPlaneItemInline,)


@admin.register(models.PersonalPlaneItemModel)
class PersonalPlaneItemModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'plane',
        'author',
        'task',
        'description',
        'work_type',
        'duration_plane',
        'duration_fact',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('task',)


@admin.register(models.PersonalPlaneAccessOrganizationModel)
class PersonalPlaneAccessOrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'organization',
        'created_at',
        'updated_at',
        'is_active',
    )
    autocomplete_fields = ('owner', 'organization',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.PersonalPlaneAccessProfileModel)
class PersonalPlaneAccessProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'user',
        'created_at',
        'updated_at',
        'is_active',
    )
    autocomplete_fields = ('owner', 'user',)
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.PersonalPlanAccessProfileMetadataModel)
class PersonalPlanAccessProfileMetadataModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
    )
    autocomplete_fields = ('user',)
    search_fields = ('user__user__last_name', 'user__user__first_name', 'user__user__email')
    ordering = ('user__user__last_name', 'user__user__first_name',)
