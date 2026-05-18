from django.contrib import admin

from common.models import Events, Participants
from . import models

from mptt.admin import MPTTModelAdmin


@admin.register(models.WorkTimeLineModel)
class WorkTimeLineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "profile",
        "organization",

    )


@admin.register(models.SocialWebType)
class SocialWebTypesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )


@admin.register(models.SocialURLs)
class SocialLinksURLs(admin.ModelAdmin):
    list_display = (
        "social_link",
        "id",
        "social_web_type",
    )
    search_fields = [
        "social_link",
    ]
    list_filter = [
        "social_web_type",
    ]


@admin.register(models.NewsCategoryModel)
class NewsCategoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
    )
    search_fields = ('name', 'code',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'author',)


class NewsModelAdmin(MPTTModelAdmin):
    autocomplete_fields = ["addressees",
                           "work_groups",
                           "image", "author", "related_object",]
    list_display = ["title", 'category', "author", "is_important", "is_independent"]
    list_filter = ["is_independent"]
    list_display_links = ["title"]
    list_per_page = 20
    list_select_related = ["author"]


@admin.register(models.CounterpartyModel)
class CounterPartyModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    search_fields = ('name',)
    ordering = ('sort', 'name')
    readonly_fields = ('created_at', 'updated_at', 'author',)


@admin.register(models.CostingObjectModel)
class CostingObjectModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    search_fields = ('name',)
    ordering = ('sort', 'name')
    readonly_fields = ('created_at', 'updated_at', 'author',)


@admin.register(models.ProgramModel)
class ProgramModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    search_fields = ('name',)
    ordering = ('sort', 'name')
    readonly_fields = ('created_at', 'updated_at', 'author',)


admin.site.register(models.NewsModel, NewsModelAdmin)
models = [

    Events, Participants
]

admin.site.register(models)
