from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from . import models


class GalleryModelInline(admin.TabularInline):
    model = models.GalleryModel
    fields = (
        'file',
        'sort',
        'is_main',
    )
    fk_name = 'related_object'
    extra = 0
    ordering = ('-is_main', 'sort', 'created_at')
    autocomplete_fields = ('file',)


@admin.register(models.GalleryModel)
class GalleryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'related_object',
        'file',
        'sort',
        'is_active',
        'is_main',
        'created_at',
        'is_image',
        'is_video',
        'is_audio'
    )
    readonly_fields = ('author',)
    autocomplete_fields = ('related_object', 'file',)
