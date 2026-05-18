from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common import fields as common_fields
from common import page_config


class DailyTasksField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'is_daily_filter'
    verbose_name = _('Сегодняшние')
    default = None
    blank = True

    def get_time(self):
        local_datetime = timezone.now()
        local_time = local_datetime.timetz()
        result = local_datetime - timedelta(
            hours=local_time.hour,
            minutes=local_time.minute,
            seconds=local_time.second,
            microseconds=local_time.microsecond
        )
        return result

    def to_filter(self, queryset, value):
        local_time = self.get_time()
        if value.get('value') is True:
            return queryset.filter(created_at__gte=local_time)
        else:
            return queryset.filter(created_at__lt=local_time)

    def to_exclude(self, queryset, value):
        local_time = self.get_time()
        if value.get('value') is True:
            return queryset.filter(created_at__lt=local_time)
        else:
            return queryset.filter(created_at__gte=local_time)


class CounterFilterField(common_fields.FakeField):
    table_info = page_config.DefaultTableColumn()
    field_info = page_config.CharFieldFormField()
    filter_info = page_config.CharFilterField()
    tp_info = page_config.TPStringColumn()

    filter_lookup = {"value": "__icontains"}
    name = 'counter_filter'
    verbose_name = _('Номер')
    default = ''
    blank = True
    max_length = 200

    def to_filter(self, queryset, value):
        numbers = value.get('value')
        if isinstance(numbers, str):
            try:
                counters = [x.strip() for x in numbers.split(',')]
                counters = [f'{int(x):05d}' if x.isdigit() else x for x in counters]
                queryset = queryset.filter(counter__in=counters)
            except ValueError:
                pass
        return queryset

    def to_exclude(self, queryset, value):
        numbers = value.get('value')
        if isinstance(numbers, str):
            try:
                counters = [x.strip() for x in numbers.split(',')]
                counters = [f'{int(x):05d}' if x.isdigit() else x for x in counters]
                queryset = queryset.exclude(counter__in=counters)
            except ValueError:
                pass
        return queryset


class WithoutOrderFilterField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'without_order_filter'
    verbose_name = _('Без заказов')
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(task_delivery_points__isnull=True)
        else:
            return queryset.filter(task_delivery_points__isnull=False)

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(task_delivery_points__isnull=True)
        else:
            return queryset.exclude(task_delivery_points__isnull=False)


class OverdueFilterField(common_fields.FakeField):
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
        from .models import TaskStatusTypeModel
        not_complete_statuses = TaskStatusTypeModel.objects.filter(
            is_active=True,
            task_type='task',
            is_complete=False
        ).values_list('task_status', flat=True)
        return not_complete_statuses

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(dead_line__isnull=False,
                                   dead_line__lt=timezone.now(),
                                   status__in=self.get_not_complete_statuses()
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


class VisorFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Наблюдатель")
    name = 'is_visor_filter'
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
   

class CooperatorFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Соисполнитель")
    name = 'is_cooperator_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(cooperators__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(cooperators__in=value.get('value'))
        return queryset


class ExecutorFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Участник исполнения")
    name = 'is_executor_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        user_ids = value.get('value')
        queryset = queryset.filter(
            Q(operator__in=user_ids) | Q(cooperators__in=user_ids)
        ).distinct()
        return queryset

    def to_exclude(self, queryset, value):
        user_ids = value.get('value')
        queryset = queryset.exclude(
            Q(operator__in=user_ids) | Q(cooperators__in=user_ids)
        )
        return queryset


class ParticipantFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Участник задачи")
    name = 'is_participant_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        user_ids = value.get('value')
        queryset = queryset.filter(
            Q(operator__in=user_ids) |
            Q(cooperators__in=user_ids) |
            Q(owner__in=user_ids) |
            Q(visors__in=user_ids)
        ).distinct()
        return queryset

    def to_exclude(self, queryset, value):
        user_ids = value.get('value')
        queryset = queryset.exclude(
            Q(operator__in=user_ids) |
            Q(cooperators__in=user_ids) |
            Q(owner__in=user_ids) |
            Q(visors__in=user_ids)
        )
        return queryset


class OrganizationTimeExecutionField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Организация")
    name = 'organization_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'catalogs.ContractorModel'
    model = 'catalogs.ContractorModel'
    data_path = '/app_info/select_list/?model=catalogs.ContractorModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(task__organization=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(task__organization=value.get('value'))
        return queryset


class UserTimeExecutionField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.UserTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ProfileFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Сотрудник")
    name = 'user_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'users.ProfileModel'
    model = 'users.ProfileModel'
    data_path = '/app_info/select_list/?model=users.ProfileModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(author=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(author=value.get('value'))
        return queryset


class ProjectTimeExecutionField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Проект")
    name = 'project_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'workgroups.WorkgroupModel'
    model = 'workgroups.WorkgroupModel'
    data_path = '/app_info/select_list/?model=workgroups.WorkgroupModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(task__project=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(task__project=value.get('value'))
        return queryset


class SprintProjectFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField(filters=[{"name": "is_project",
                                                              'value': True,
                                                              'type': 'defined'}])
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Проекты")
    name = 'projects_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'workgroups.WorkgroupModel'
    model = 'workgroups.WorkgroupModel'
    data_path = '/app_info/select_list/?model=workgroups.WorkgroupModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(projects__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(projects__in=value.get('value'))
        return queryset
