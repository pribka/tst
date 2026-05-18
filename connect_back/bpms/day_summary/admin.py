from django.contrib import admin

from .models import DaySummaryNoteModel, DaySummaryNoteStatusModel, DaySummaryNoteCategoryModel


@admin.register(DaySummaryNoteStatusModel)
class DaySummaryNoteStatusModelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "color", "sort")
    list_editable = ("name", "color", "sort")


@admin.register(DaySummaryNoteCategoryModel)
class DaySummaryNoteCategoryModelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "icon", "hex_color", "sort")
    list_editable = ("name", "icon", "hex_color", "sort")


@admin.register(DaySummaryNoteModel)
class DaySummaryNoteModelAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "author", "status", "created_at", "is_ai_summary", "is_active")
    list_filter = ("date", "is_ai_summary", "is_active")
    search_fields = ("id", "author__user__first_name", "author__user__last_name", "author__user__email")
    readonly_fields = ("author", "created_at", "updated_at")
    date_hierarchy = "date"

    def content_short(self, obj):
        if not obj.content:
            return ""
        return obj.content[:80] + "…" if len(obj.content) > 80 else obj.content

    content_short.short_description = "Текст"
