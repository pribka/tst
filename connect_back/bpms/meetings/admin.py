from django.contrib import admin
from common.admin import FileBaseModelInline
from . import models


class MeetingRecordStatusFilter(admin.SimpleListFilter):
    title = 'Статус записи'
    parameter_name = 'record_status'

    def lookups(self, request, model_admin):
        return (
            ('new', 'Новая'),
            ('processing', 'В процессе'),
            ('done', 'Готова'),
            ('error', 'Ошибка'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(records__status=value).distinct()
        return queryset


class CallHasTicketFilter(admin.SimpleListFilter):
    title = 'Связан с обращением'
    parameter_name = 'has_ticket'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(ticket__isnull=False)
        if value == 'no':
            return queryset.filter(ticket__isnull=True)
        return queryset


class CallHasChatFilter(admin.SimpleListFilter):
    title = 'Связан с чатом'
    parameter_name = 'has_chat'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(chat__isnull=False)
        if value == 'no':
            return queryset.filter(chat__isnull=True)
        return queryset


admin.site.register(models.MeetingServerModel)


@admin.register(models.CallStatusModel)
class CallStatusModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_ru', 'code', 'color', 'is_active')
    list_editable = ('color',)
    list_filter = ('is_active',)
    search_fields = ('id', 'name_ru', 'code')

class MeetingSectionInline(admin.TabularInline):
    model = models.MeetingSectionModel
    extra = 0
    fields = ('status', 'date_start', 'date_end', 'duration',)


class MeetingMemberInline(admin.TabularInline):
    model = models.MeetingMemberModel
    extra = 0
    fields = ('user', 'is_moderator',)
    autocomplete_fields = ('user',)


class CallCurrentTargetInline(admin.TabularInline):
    model = models.CallModel.current_target.through
    extra = 1
    autocomplete_fields = ('profilemodel',)
    verbose_name = 'Текущий целевой участник'
    verbose_name_plural = 'Текущие целевые участники'


@admin.register(models.PlannedMeetingModel)
class PlannedMeetingModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'date_begin',
        'duration',
        'has_record',
        'created_at',
        'is_active',
    )
    inlines = (MeetingSectionInline, MeetingMemberInline, FileBaseModelInline, )
    ordering = ('-created_at', )
    list_filter = ('status',)
    search_fields = ('id', 'name_ru',)
    autocomplete_fields = ('related_object', 'project',)
    readonly_fields = ('author',)


@admin.register(models.MeetingMemberModel)
class MeetingMemberAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'meeting',
        'user'

    )


@admin.register(models.CallModel)
class CallModelAdmin(admin.ModelAdmin):
    inlines = (CallCurrentTargetInline,)
    exclude = ('current_target',)
    list_display = (
        'id',
        'status',
        'initiator',
        'accepted_by',
        'started_at',
        'ticket',
        'chat',
        'ring_attempt',
    )
    list_filter = (
        'status',
        'started_at',
        CallHasTicketFilter,
        CallHasChatFilter,
        'ring_attempt',
        'is_active',
    )
    autocomplete_fields = (
        'initiator',
        'accepted_by',
        'ticket',
        'chat',
        'meeting',
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'author')
    search_fields = (
        'id',
        'initiator__user__last_name',
        'initiator__user__first_name',
        'accepted_by__user__last_name',
        'accepted_by__user__first_name',
        'chat__chat_uid',
    )


@admin.register(models.MeetingRecordsModel)
class MeetingRecordsAdmin(admin.ModelAdmin):
    list_display = (
        'meeting_short',
        'is_summary_ready',
        'is_intents_ready',
        'created_at',

    )
    search_fields = ('id', 'meeting__id', 'section__id', 'meeting__name_ru',)
    ordering = ('-created_at',)
    list_filter = ('is_summary_ready', 'is_intents_ready',)
    autocomplete_fields = ('meeting', 'section', 'record_file',)

    def meeting_short(self, obj):
        if obj.meeting_id is None:
            return ''
        text = str(obj.meeting)
        return text[:67] + '...' if len(text) > 70 else text

    meeting_short.short_description = 'meeting'

class MeetingSectionMemberInline(admin.TabularInline):
    model = models.MeetingSectionMemberModel
    extra = 0
    fields = ('user', 'duration',)
    autocomplete_fields = ('user',)


@admin.register(models.MeetingSectionModel)
class MeetingSectionAdmin(admin.ModelAdmin):
    list_display = ('meeting_id', 'meeting', 'status', 'date_start', 'date_end', 'duration')
    list_filter = ('meeting__status', MeetingRecordStatusFilter)
    ordering = ('-date_start',)
    autocomplete_fields = ('meeting',)
    inlines = [MeetingSectionMemberInline]
    search_fields = ('id', 'meeting__id', 'meeting__name_ru',)