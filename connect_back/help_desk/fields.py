from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, F

from common import page_config
from common.fields import FakeField


class TicketIsOverdueFilterField(FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'is_overdue_filter'
    verbose_name = _('Просроченные')
    default = None
    blank = True

    def get_not_complete_statuses(self):
        from .utils import get_completed_statuses_id
        from .models import HelpDeskTicketStatusModel
        return list(
            HelpDeskTicketStatusModel.objects.filter(
                is_active=True
            ).exclude(
                code__in=get_completed_statuses_id()
            ).values_list('code', flat=True)
        )

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(dead_line__isnull=False,
                                   dead_line__lt=timezone.now(),
                                   status_id__in=self.get_not_complete_statuses()
                                   )
        else:
            return queryset.filter(dead_line__isnull=False,
                                   dead_line__gt=timezone.now(),
                                   status__in=self.get_not_complete_statuses()
                                   )

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(dead_line__isnull=False,
                                   dead_line__gt=timezone.now(),
                                   status__in=self.get_not_complete_statuses()
                                   )
        else:
            return queryset.filter(dead_line__isnull=False,
                                   dead_line__lt=timezone.now(),
                                   status__in=self.get_not_complete_statuses()
                                   )


class VisorFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Наблюдатель")
    name = 'visors_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(visors__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(visors__in=value.get('value'))
        return queryset


class MemberFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Участник")
    name = 'members_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(members__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(members__in=value.get('value'))
        return queryset


class OrgAdminFKField(page_config.ForeignKeyFilterField):
    def get_dict(self):
        data = super().get_dict()
        data["widget"]["filters"] = [{
            'type': 'defined',
            'name': 'permission_type',
            'value': 'help_desk_manager'
        }]
        return data


class HelpDeskTicketOrgAdminFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = OrgAdminFKField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Организация техподдержки")
    name = 'help_desk_ticket_org_admin_filter'
    
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'catalogs.ContractorModel'
    model = 'catalogs.ContractorModel'
    data_path = '/app_info/select_list/?model=catalogs.ContractorModel'
    
    def to_filter(self, queryset, value):
        queryset = queryset.filter(customer_card__org_admin__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(customer_card__org_admin__in=value.get('value'))
        return queryset


class OrgAdminFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = OrgAdminFKField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Организация техподдержки")
    name = 'org_admin_filter'
    
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'catalogs.ContractorModel'
    model = 'catalogs.ContractorModel'
    data_path = '/app_info/select_list/?model=catalogs.ContractorModel'
    
    def to_filter(self, queryset, value):
        queryset = queryset.filter(org_admin__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(org_admin__in=value.get('value'))
        return queryset


class SpecialistFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Специалист")
    name = 'specialist_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'
    is_reserve = None

    def get_queryset_filters(self, value):
        filters = {
            'customer_support_specialists__user_id__in': value.get('value'),
        }
        if self.is_reserve is not None:
            filters['customer_support_specialists__is_reserve'] = self.is_reserve
        return filters

    def to_filter(self, queryset, value):
        queryset = queryset.filter(**self.get_queryset_filters(value))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(**self.get_queryset_filters(value))
        return queryset


class MainSpecialistFilterField(SpecialistFilterField):
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Основной специалист")
    name = 'main_specialist_filter'
    is_reserve = False


class ReserveSpecialistFilterField(SpecialistFilterField):
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Заменяющий специалист")
    name = 'reserve_specialist_filter'
    is_reserve = True


class RatingFilterField(FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.CharFieldFormField()
    filter_info = page_config.ChoiceFilterField()
    tp_info = page_config.TPStringColumn()
    choices = (
        ('1', _('Очень плохо')),
        ('2', _('Плохо')),
        ('3', _('Средне')),
        ('4', _('Хорошо')),
        ('5', _('Очень хорошо')),
    )
    filter_lookup = {"value": "__in"}
    name = 'rating_filter'
    verbose_name = _('Оценка')
    default = ''
    blank = True
    max_length = 2

    def to_filter(self, queryset, value):
        ratings = [int(_) for _ in value.get('value')]
        queryset = queryset.filter(ratings__rating__in=ratings)
        return queryset

    def to_exclude(self, queryset, value):
        ratings = [int(_) for _ in value.get('value')]
        queryset = queryset.exclude(ratings__rating__in=ratings)
        return queryset


class HasProfileFilterField(FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'has_profile_filter'
    verbose_name = _('Профиль активен')
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(user__isnull=False)
        else:
            return queryset.filter(user__isnull=True)

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(user__isnull=False)
        else:
            return queryset.exclude(user__isnull=True)


class SlaFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = OrgAdminFKField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("SLA")
    name = 'sla_filter'

    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'sla.SLAModel'
    model = 'sla.SLAModel'
    data_path = '/app_info/select_list/?model=sla.SLAModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(
            Q(sla_rels__sla_id__in=value.get('value'),
              sla_rels__sla__contractor_id=F('customer_card__org_admin_id')) |
            Q(
                sla_rels__isnull=True,
                post_inst__isnull=False,
                post_inst__sla_rels__sla_id__in=value.get('value'),
                post_inst__sla_rels__sla__contractor_id=F('customer_card__org_admin_id')
            )
        )
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(
            Q(sla_rels__sla_id__in=value.get('value'),
              sla_rels__sla__contractor_id=F('customer_card__org_admin_id')) |
            Q(
                sla_rels__isnull=True,
                post_inst__isnull=False,
                post_inst__sla_rels__sla_id__in=value.get('value'),
                post_inst__sla_rels__sla__contractor_id=F('customer_card__org_admin_id')
            )
        )
        return queryset


class CustomerCardAdminsFilterField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Администратор")
    name = 'admins_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'help_desk.CustomerCardAdminModel'
    model = 'help_desk.CustomerCardAdminModel'
    data_path = '/app_info/select_list/?model=help_desk.CustomerCardAdminModel'
    is_reserve = None

    def to_filter(self, queryset, value):
        queryset = queryset.filter(admins__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(admins__in=value.get('value'))
        return queryset


class MainContactExistField(FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'main_contact_exist_filter'
    verbose_name = _('Есть основной контакт')
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(main_contact_person__isnull=False)
        else:
            return queryset.filter(main_contact_person__isnull=True)

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(main_contact_person__isnull=False)
        else:
            return queryset.exclude(main_contact_person__isnull=True)


class MainContactPersonPostField(FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Должность основного контакта")
    name = 'main_contact_post_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'help_desk.ContactPersonPostModel'
    model = 'help_desk.ContactPersonPostModel'
    data_path = '/app_info/select_list/?model=help_desk.ContactPersonPostModel'
    is_reserve = None

    def to_filter(self, queryset, value):
        queryset = queryset.filter(main_contact_person__post_inst__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(main_contact_person__post_inst__in=value.get('value'))
        return queryset
