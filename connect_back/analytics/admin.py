from django.contrib import admin

from .models import ActivityDigestModel, ActivitySummaryModel, DashboardSectionModel, DashboardConfigModel


@admin.register(ActivityDigestModel)
class ActivityDigestModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "related_object",
        "date",
        "scope",
        "source",
        "is_active",
    )
    autocomplete_fields = ("related_object",)
    list_filter = ("date", "scope", "source", "is_active")
    search_fields = ("related_object__pk",)
    ordering = ("-date",)
    date_hierarchy = "date"

@admin.register(ActivitySummaryModel)
class ActivitySummaryModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "related_object",
        "user",
        "start_date",
        "end_date",
        "started_at",
        "completed_at",
        "is_active",
    )
    autocomplete_fields = ("related_object", "user")
    list_filter = ("status", "is_active")
    search_fields = ("related_object__pk", "user__pk",)
    ordering = ("-started_at",)
    date_hierarchy = "start_date"


@admin.register(DashboardSectionModel)
class DashboardSectionModelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sort", "is_active")
    list_editable = ("name", "sort", "is_active")
    search_fields = ("code", "name")
    ordering = ("sort", "code")


@admin.register(DashboardConfigModel)
class DashboardConfigModelAdmin(admin.ModelAdmin):
    list_display = (
        "section",
        "description",
        "scopes",
        "sort",
        "is_active",
    )
    list_editable = ("sort", "is_active")
    list_filter = ("section", "is_active")
    search_fields = ("section", "description")
    ordering = ("section__sort", "sort")
