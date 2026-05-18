from django.contrib import admin
from . import models


@admin.register(models.UserWorkStatusModel)
class UserWorkStatusModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'is_active',)

    readonly_fields = ('author',)


@admin.register(models.UserWorkStatusReasonModel)
class UserWorkStatusReasonModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'is_active', 'sort')
    readonly_fields = ('author',)
    list_editable = ('sort',)
    ordering = ('sort', '-created_at',)


@admin.register(models.UserWorkStatusRecordingModel)
class UserWorkStatusRecordingModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'status', 'reason', 'created_at',)
    readonly_fields = ('author', 'created_at',)
    ordering = ('-created_at',)
    list_filter = ('status', 'reason',)