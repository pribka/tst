from django.utils.translation import gettext_lazy as _
from common import fields as common_fields, page_config


class IsNotBusyFilter(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'is_not_busy_filter'
    verbose_name = 'Не занят'
    default = None
    blank = True

    def to_filter(self, queryset, value):

        if value.get('value') is True:
            return queryset.filter(operator_tasks__isnull=True).distinct()
        else:
            return queryset.filter(operator_tasks__isnull=False).distinct()

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(operator_tasks__isnull=False).distinct()
        else:
            return queryset.filter(operator_tasks__isnull=True).distinct()


class FullNameFilter(common_fields.FakeField):
    filter_info = page_config.CharFilterField()
    name = 'full_name_filter'
    verbose_name = 'Полное имя'
    max_length = 100
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value', None):
            filtered_object_list = filter(lambda profile: profile.full_name.lower().find(value.get('value').lower()) != -1, queryset.all())
            filtered_object_list_indexes = [obj.id for obj in filtered_object_list]
            filtered_queryset = queryset.filter(id__in=filtered_object_list_indexes)
            return filtered_queryset
        else:
            return queryset

    def to_exclude(self, queryset, value):
        if value.get('value', None):
            filtered_object_list = filter(lambda profile: profile.full_name.lower().find(value.get('value').lower()) == -1, queryset.all())
            filtered_object_list_indexes = [obj.id for obj in filtered_object_list]
            filtered_queryset = queryset.filter(id__in=filtered_object_list_indexes)
            return filtered_queryset
        else:
            return queryset


class UserOrganizationFilter(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = "Организация"
    name = 'user_organization_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'catalogs.ContractorModel'
    model = 'catalogs.ContractorModel'
    data_path = '/users/my_organizations/?display=tree'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(contractors__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(contractors__in=value.get('value'))
        return queryset


class ProfileFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = "Профиль"
    name = 'profile_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/user/list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(pk__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(pk__in=value.get('value'))
        return queryset


class TariffFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Тариф")
    name = 'tariff_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'billing.TariffModel'
    model = 'billing.TariffModel'
    data_path = '/app_info/select_list/?model=billing.TariffModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(contractor__contractor_tariffs__tariff__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(contractor__contractor_tariffs__tariff__in=value.get('value'))
        return queryset
