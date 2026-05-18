from django.contrib import admin

from . import models


@admin.register(models.UserVotesModel)
class UserVotesModelAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'related_object',
        'vote',
    )
    autocomplete_fields = ('related_object',)
    readonly_fields = ('author',)


@admin.register(models.UserRatingModel)
class UserRatingModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'related_object',
        'rating',
        'created_at',
    )