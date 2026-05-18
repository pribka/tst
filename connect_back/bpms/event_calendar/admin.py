from django.contrib import admin

from . import models


class EventCalendarMembersInline(admin.TabularInline):
    model = models.EventCalendarMemberModel
    fields = (
        'user',
    )
    fk_name = 'event'
    extra = 0
    autocomplete_fields = ('user', )


@admin.register(models.CalendarGroupModel)
class CalendarGroupModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'color',
        'sort',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', 'name', 'code')


@admin.register(models.CalendarModel)
class CalendarModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'color',
        'calendar_group',
        'related_object',
        'author',
        'created_at',
        'updated_at',
        'synchronize'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'author',
    )
    autocomplete_fields = (
        'related_object',
    )
    search_fields = ('name', 'id',)


@admin.register(models.EventCalendarTypeModel)
class EventCalendarTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'created_at',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)


@admin.register(models.EventCalendarPrivacyModel)
class EventCalendarPrivacyModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'created_at',
    )
    readonly_fields = ('author', 'created_at',)
    ordering = ('sort', 'name',)


@admin.register(models.EventCalendarModel)
class EventCalendarModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'calendar',
        'created_at',
    )
    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )
    search_fields = ('id', 'name',)
    ordering = ('-created_at',)
    autocomplete_fields = ('calendar', 'meeting',)
    inlines = (EventCalendarMembersInline,)


@admin.register(models.CalendarCustomSetModel)
class CalendarCustomSetModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'created_at',
        'updated_at',
        'is_active',
    )

    readonly_fields = (
        'author',
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at',)


@admin.register(models.EventCalendarAccessOrganizationModel)
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


@admin.register(models.EventCalendarAccessProfileModel)
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


@admin.register(models.EventCalendarAccessProfileMetadataModel)
class EventCalendarAccessProfileMetadataModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
    )
    autocomplete_fields = ('user',)
    search_fields = ('user__user__last_name', 'user__user__first_name', 'user__user__email')
    ordering = ('user__user__last_name', 'user__user__first_name',)
