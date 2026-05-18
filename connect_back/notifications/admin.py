from django.contrib import admin
from . import models


class EmailNotificationRecipientInline(admin.TabularInline):
    model = models.EmailNotificationRecipientModel
    fk_name = 'email_notification'
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class EmailNotificationAttachmentInline(admin.TabularInline):
    model = models.EmailNotificationAttachmentModel
    extra = 0


class WebNotificationRecipientInline(admin.TabularInline):
    model = models.WebNotificationRecipientModel
    extra = 0

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.EmailTemplateModel)
class EmailTemplateModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
    )


@admin.register(models.EmailNotificationModel)
class EmailNotificationModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'subject',
        'sent',
        'created_at',
        'emails',
    )
    list_filter = (
        'template',
    )
    inlines = (EmailNotificationRecipientInline, EmailNotificationAttachmentInline,)
    search_fields = ('recipients__recipient',)


@admin.register(models.WebNotificationModel)
class WebNotificationModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'event_type',
        'created_at',
    )
    ordering = ('-created_at',)
    readonly_fields = ('ct',)
    inlines = (WebNotificationRecipientInline,)


@admin.register(models.EventTypeModel)
class EventTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'category',
        'is_mention',
        'is_active',
    )
    list_filter = (
        'is_active',
        'category',
    )
    ordering = ('category__sort', 'name')


@admin.register(models.EmailNotificationErrorLog)
class EmailNotificationErrorLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'email',
    ]


@admin.register(models.SMSNotificationModel)
class SMSNotificationModelAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'recipient',
        'message',
        'sent',
    )
    readonly_fields = (
        'created_at',
        'recipient',
        'message',
        'sent',
    )


@admin.register(models.SMSNotificationErrorLog)
class SMSNotificationErrorLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'phone',
        'sms_notification',
    )
    readonly_fields = (
        'created_at',
        'phone',
        'sms_notification',
    )


@admin.register(models.NotificationCategoryModel)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )
    list_editable = ('sort',)
    search_fields = ('name', 'code',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    ordering = ('sort', 'name',)


@admin.register(models.NotificationEventTypePreferenceModel)
class NotificationEventTypePreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'event_type',
        'is_enabled',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'is_enabled',
        'event_type',
        'event_type__category',
    )
    search_fields = (
        'user__user__username',
        'user__user__email',
        'event_type__code',
        'event_type__name',
    )
    autocomplete_fields = ('user',)
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(models.NotificationCategoryPreferenceModel)
class NotificationCategoryPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'category',
        'is_enabled',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'is_enabled',
        'category',
    )
    search_fields = (
        'user__user__username',
        'user__user__email',
        'category__code',
        'category__name',
    )
    autocomplete_fields = ('user',)
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(models.MobilePushDeviceModel)
class MobilePushDeviceModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'profile',
        'platform',
        'push_provider',
        'device_id',
        'is_active',
        'last_seen_at',
    )
    list_filter = (
        'platform',
        'push_provider',
        'is_active',
    )
    search_fields = (
        'profile__user__username',
        'profile__user__email',
        'device_id',
        'token',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_seen_at',
        'last_error',
    )


@admin.register(models.WebPushSubscriptionModel)
class WebPushSubscriptionModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'profile',
        'browser',
        'platform',
        'is_active',
        'last_seen_at',
    )
    list_filter = (
        'browser',
        'platform',
        'is_active',
    )
    search_fields = (
        'profile__user__username',
        'profile__user__email',
        'profile__user__first_name',
        'profile__user__last_name',
        'auth',
        'endpoint',
    )
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_error',
        'user_agent',
    )
    autocomplete_fields = (
        'profile',
    )
