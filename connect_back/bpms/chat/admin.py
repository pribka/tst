from django.contrib import admin
from common.admin import FileBaseModelInline, MentionInline
from . import models


class ChatMemberModelInline(admin.TabularInline):
    model = models.MemberModel
    fk_name = 'chat'
    extra = 0
    autocomplete_fields = ('user',)
    

@admin.register(models.ChatModel)
class ChatModelAdmin(admin.ModelAdmin):
    inlines = (ChatMemberModelInline,)
    list_filter = (
        'is_active',
        'is_public',
        'is_support',
    )
    list_display = (
        'id',
        'name',
        'author',
        'chat_author',
        'is_public',
        'is_active',
        'created_at',
        'updated_at'
    )
    list_editable = (
        'is_active',
    )
    autocomplete_fields = (
        'chat_author',
        'dealer',
        'meeting',
    )
    ordering = ('-created_at',)
    search_fields = ('name', 'member__user__user__first_name', 'member__user__user__last_name', 'member__user__user__email',)
    readonly_fields = ('author', 'created_at', 'deleted_at',)


@admin.register(models.MessageModel)
class MessageModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'message_uid',
        'chat',
        'text',
        'created',
        'forwarded',
        'is_deleted',
        'is_system',
        'is_pinned',
        'is_active',
    )
    ordering = ('-created', )
    inlines = (FileBaseModelInline, MentionInline)
    autocomplete_fields = ('chat', 'share', 'message_author', 'message_reply', 'message_forwarded', 'pin_author')
    search_fields = ('text',)


@admin.register(models.SupportMessageTemplateModel)
class SupportMessageTemplateModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'author',
        'is_public',
        'is_active',
    )


@admin.register(models.ChatSummaryModel)
class ChatSummaryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'chat',
        'user',
        'start_date',
        'end_date',
        'status',
    )
    list_filter = ('status', 'is_active')
    autocomplete_fields = ('chat', 'user')
    search_fields = (
        'chat__name',
        'user__user__first_name',
        'user__user__last_name',
        'user__user__email',
    )
    ordering = ('-started_at',)
    readonly_fields = ('started_at', 'completed_at')
