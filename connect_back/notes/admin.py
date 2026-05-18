from django.contrib import admin

from . import models


@admin.register(models.ColorNoteModel)
class ColorNoteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'o_color',
        'sort',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', 'code', 'created_at',)
    search_fields = ('code', 'name',)


@admin.register(models.NoteModel)
class NoteModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'color',
        'title',
        'created_at',
        'updated_at',
        'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    search_fields = ('title',)
    autocomplete_fields = ('related_object',)

