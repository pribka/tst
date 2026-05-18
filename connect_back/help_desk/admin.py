from django.contrib import admin
from django.db.models import TextField

from nested_inline.admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline

from ckeditor.fields import CKEditorWidget

from common.admin import FileBaseModelInline, ViewerInline

from . import models


class VacationDateInline(NestedTabularInline):
    model = models.VacationDateModel
    # list_display = (
    #     'start_date',
    #     'end_date',
    # )
    extra = 0
    fields = (
        'start_date',
        'end_date',
    )
    fk_name = 'specialist'


class CustomerSpecialistInline(NestedStackedInline):
    model = models.CustomerSupportSpecialistModel
    fields = (
        'user',
        'is_reserve',
        'start_date',
        'end_date',
        'duration_plan',
    )
    autocomplete_fields = ('user', )
    extra = 0
    fk_name = 'customer_card'
    inlines = (VacationDateInline,)


class CustomerCardAdminInline(admin.TabularInline):
    model = models.CustomerCardAdminThroughModel
    fields = (
        'admin',
    )
    autocomplete_fields = ('admin',)
    pk_field = 'customer_card',
    extra = 0


class TicketMessageThroughInline(admin.TabularInline):
    model = models.MessageTicketThroughModel
    fields = ('ticket',)
    fk_name = 'message'
    extra = 0
    autocomplete_fields = ('ticket',)


class WorkLogInline(admin.TabularInline):
    model = models.HelpDeskWorkLogModel
    fk_name = 'ticket'
    fields = (
        'user',
        'date',
        'finished_date',
        'description',
        'duration',
        'is_current',
        'edited',
        'is_result',
    )
    autocomplete_fields = ('user',)
    extra = 0


@admin.register(models.HelpDeskWorkLogModel)
class HelpDeskWorkLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ticket_customer_card',
        'ticket',
        'user',
        'duration',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('user', 'ticket',)
    search_fields = (
        'user__user__last_name',
        'user__user__first_name',
        'user__user__email',
        'ticket__name',
        'ticket__customer_card__name',
    )
    ordering = ('-created_at',)


@admin.register(models.CustomerSupportSpecialistModel)
class CustomerSupportSpecialistAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'customer_card',
        'created_at',
        'updated_at',
        'is_reserve',
        'start_date',
        'end_date',
        'duration_plan',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('user', 'customer_card',)
    ordering = ('-created_at',)
    search_fields = ('user__user__last_name',
                     'user__user__first_name',
                     'user__user__email',
                     'customer_card__org_admin__name',
                     'customer_card__name',)


@admin.register(models.CustomerCardAdminModel)
class CustomerCardAdminModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'bin',
        'name',
        'org_admin',
        'created_at',
        'updated_at',
        'author',
    )

    autocomplete_fields = ('org_admin',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    search_fields = ('bin', 'name',)


@admin.register(models.CustomerCardModel)
class CustomerCardModelAdmin(NestedModelAdmin):
    list_display = (
        'org_admin',
        'name',
        'customer',
        'main_contact_person',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )

    autocomplete_fields = (
        'org_admin',
        'customer',
        'main_contact_person',
        'external_customer',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('-created_at',)
    inlines = (
        CustomerSpecialistInline,
        # CustomerCardAdminInline,
    )
    formfield_overrides = {TextField: {'widget': CKEditorWidget}}
    search_fields = ('name', 'full_name', 'inn')


@admin.register(models.HelpDeskConfigModel)
class HelpDeskConfigModelAdmin(admin.ModelAdmin):
    list_display = (
        'contractor',
        'telegram_token',
        'telegram_user',
        'created_at',
        'updated_at',
        'is_active',
        'author',
    )
    autocomplete_fields = ('contractor',)
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('-created_at',)


@admin.register(models.ContactPersonModel)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = (
       'id',
       'customer_card',
       'name',
       'user',
       'phone',
       'telegram',
       'email',
       'post_inst',
       'created_at',
       'updated_at',
       'is_active',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('customer_card', 'user', 'post_inst',)
    search_fields = ('name', 'telegram', 'phone', 'email',)


@admin.register(models.ContactPersonMessageModel)
class ContactPersonMessageModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'channel',
        'contact_person',
        'author',
        'created_at',
        'updated_at',
        'is_active',
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'author',)
    autocomplete_fields = ('contact_person', 'reply')
    inlines = (TicketMessageThroughInline, FileBaseModelInline, ViewerInline,)
    search_fields = ('text',)


# Тикеты

class TicketVisorInline(admin.TabularInline):
    model = models.HelpDeskTicketVisorsModel
    fields = (
        'user',
    )
    autocomplete_fields = ('user',)
    extra = 0


class TicketMemberInline(admin.TabularInline):
    model = models.HelpDeskTicketMembersModel
    fields = (
        'user',
    )
    autocomplete_fields = ('user',)
    fk_name = 'ticket'
    extra = 0


@admin.register(models.HelpDeskTicketTypeModel)
class HelpDeskTicketTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'is_active',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)


@admin.register(models.HelpDeskTicketModel)
class HelpDeskTicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'contact_person',
        'specialist',
        'status',
        'priority',
        'category',
        'customer_card',
        'dead_line',
        'start_date',
        'end_date',
        'author',
        'created_at',
        'updated_at',
        'is_active',
    )

    list_filter = (
        'status',
        'priority',
        'ticket_type',
    )
    autocomplete_fields = (
        'customer_card',
        'category',
        'contact_person',
        'specialist',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('-created_at',)
    search_fields = ('name', 'number',)
    inlines = (TicketVisorInline, TicketMemberInline, WorkLogInline, FileBaseModelInline,)


@admin.register(models.HelpDeskTicketPriorityModel)
class HelpDeskTicketPriorityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code',)


@admin.register(models.HelpDeskTicketCategoryModel)
class HelpDeskCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code',)
    autocomplete_fields = ('contractor',)


@admin.register(models.ContactPersonPostModel)
class ContactPersonPostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code',)
    autocomplete_fields = ('contractor',)


@admin.register(models.HelpDeskTicketStatusModel)
class HelpDeskStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'color',
        'created_at',
        'updated_at',
        'is_active',
        'sort',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code',)


@admin.register(models.HelpDeskChannelModel)
class HelpDeskChannelModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'icon',
        'updated_at',
        'created_at',
        'is_active',
        'sort',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    ordering = ('sort', 'name',)
    search_fields = ('name', 'code',)


@admin.register(models.HelpDeskTicketCounterModel)
class HelpDeskTicketCounterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'org_admin',
        'number',
        'number_formatted',
    )
    search_fields = ('org_admin__name', 'number_formatted',)
    autocomplete_fields = ('org_admin',)
    ordering = ('-number_formatted',)


@admin.register(models.CustomerCardStatusModel)
class CustomerCardStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'sort',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at', 'author',)
    search_fields = ('name', 'code',)
    ordering = ('sort', 'name',)


@admin.register(models.HelpDeskCostModel)
class HelpDeskCostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'is_active',
        'author',
        'quantity',
        'amount',
        'measure_unit',
        'period',
        'created_at',
        'updated_at',
        'deleted_at',
    )
    ordering = ('-created_at',)
    search_fields = ('owner__name', 'owner__number')
    autocomplete_fields = ('owner', 'measure_unit', 'base_measure_unit',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
