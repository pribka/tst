from django.contrib import admin
from django.db.models import TextField

from nested_inline.admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from prettyjson.widgets import PrettyJSONWidget

from common.admin import FileBaseModelInline
from . import models


class WorkflowRequestTypeVisorInline(admin.TabularInline):
    model = models.WorkflowRequestTypeVisorModel
    fields = (
        'contractor_profile',
    )
    ordering = ('-created_at',)
    autocomplete_fields = ('contractor_profile',)
    extra = 0


@admin.register(models.WorkflowRequestTypeModel)
class WorkflowRequestTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
        'author',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)
    formfield_overrides = {
        TextField: {'widget': PrettyJSONWidget}
    }
    inlines = (WorkflowRequestTypeVisorInline,)


@admin.register(models.WorkflowRequestStatusModel)
class WorkflowRequestStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'color',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
        'author',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)


class RequestRouteUserThroughInline(NestedTabularInline):
    model = models.RequestRouteUserThrough
    fields = (
        'user',
        'status',
    )
    autocomplete_fields = ('user',)
    fk_name = 'request_route'
    ordering = ('user__user__last_name', 'user__user__first_name',)
    extra = 0


class WorkflowRequestRouteInline(NestedStackedInline):
    model = models.WorkflowRequestRouteModel
    fields = (
        'workflow_position',
        'status',
        'template',
        'sort'
    )
    fk_name = 'workflow_request'
    autocomplete_fields = ('workflow_position', 'template',)
    readonly_fields = ('created_at',)
    ordering = ('sort',)
    inlines = (RequestRouteUserThroughInline,)
    extra = 0


@admin.register(models.WorkflowRequestModel)
class WorkflowRequestModelAdmin(NestedModelAdmin):
    list_display = (
        'id',
        'request_type',
        'status',
        'organization',
        'project',
        'money_under_report',
        'dead_line',
        'author',
        'advance_report_approved',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('organization__name', 'project__name', 'author__user__last_name', 'author__user__first_name')
    autocomplete_fields = ('organization', 'project',)
    inlines = (WorkflowRequestRouteInline, FileBaseModelInline,)


@admin.register(models.WorkflowPositionModel)
class WorkflowPositionAdmin(admin.ModelAdmin):
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
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)


@admin.register(models.WorkflowPositionUserModel)
class WorkflowPositionUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'workflow_position',
        'contractor_profile',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = (
        'contractor_profile__user__user__last_name',
        'contractor_profile__user__user__first_name',
        'contractor_profile__contractor__name',
        'workflow_position__name',
    )
    ordering = ('-created_at',)
    autocomplete_fields = ('contractor_profile', 'workflow_position',)


@admin.register(models.WorkflowRequestRouteStatusModel)
class WorkflowRequestRouteStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'color',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)


@admin.register(models.WorkflowRequestRouteModel)
class WorkflowRequestRouteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'workflow_request',
        'workflow_position',
        'status',
        # 'user',
        'template',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = (
        'workflow_request__name',
        'workflow_position__name',
        # 'user__user__last_name',
        # 'user__user__first_name',
    )
    ordering = ('-created_at',)
    autocomplete_fields = ('workflow_request', 'workflow_position', 'template',)


@admin.register(models.WorkflowRequestRouteTemplateModel)
class WorkflowRequestRouteTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request_type',
        'workflow_position',
        'parent',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_editable = ('sort',)
    search_fields = ('request_type__name', 'workflow_position__name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    autocomplete_fields = ('request_type', 'workflow_position', 'parent',)


@admin.register(models.AdvanceReportModel)
class AdvanceReportModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'date',
        'cost_item',
        'amount',
        'created_at',
        'updated_at',
        'author',
    )
    autocomplete_fields = ('owner', 'cost_item', )
    readonly_fields = ('author', 'created_at', 'created_at',)
    ordering = ('-created_at',)

