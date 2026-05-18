# admin.py
from django.contrib import admin
from .models import ContentItem, OfficialClarificationOrgan, Partition, Tag, SettingsGos


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "created_at", "title", "publish", "draft", "publication_date", "planned_date", "is_active")
    list_filter = ("kind", "publish", "draft", "is_active", "main_in_week", "only_subscribed")
    search_fields = ("title", "slug", "summary", "description", "question", "answer")

@admin.register(OfficialClarificationOrgan)
class OfficialClarificationOrganAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'id',
    )

@admin.register(Partition)
class PartitionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'id',
    )

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'id',
    )

@admin.register(SettingsGos)
class SettingsGosAdmin(admin.ModelAdmin):
    list_display = (
        'is_active',
        'created_at',
        'id',
        'url_send_gos',
        'op_type',
    )

