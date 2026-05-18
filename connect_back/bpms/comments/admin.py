from django.contrib import admin
from common.admin import FileBaseModelInline
from . import models


@admin.register(models.CommentModel)
class CommentModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'related_object',
        'created_at',
        'is_active',
    )
    ordering = ('-created_at',)
    inlines = (FileBaseModelInline, )
    search_fields = ('id', 'related_object__id',)
    autocomplete_fields = ('related_object', 'parent',)