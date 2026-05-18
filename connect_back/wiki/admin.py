from django.contrib import admin
from .models import WikiSectionModel, WikiChapterModel, WikiPageModel, WikiAccessModel


class WikiAccessInline(admin.TabularInline):
    model = WikiAccessModel
    fields = (
        'contractor_profile',
    )
    extra = 0
    fk_name = 'wiki_section'
    autocomplete_fields = ('contractor_profile',)


@admin.register(WikiSectionModel)
class WikiSectionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'contractor',
        'public',
        'is_active',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('related_object', 'contractor',)
    search_fields = ('code', 'name',)
    inlines = (WikiAccessInline,)


@admin.register(WikiChapterModel)
class WikiChapterModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'is_active',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('related_object', 'section',)
    search_fields = ('name', 'code',)


@admin.register(WikiPageModel)
class WikiPageModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'is_active',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('related_object', 'chapter',)
