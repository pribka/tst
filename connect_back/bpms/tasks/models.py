import json
import datetime
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP

from django.utils import timezone, dateparse
from django.db import models, IntegrityError, transaction
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.core.exceptions import BadRequest
from django.core.cache import cache
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Q, Value, ExpressionWrapper, DurationField, Subquery, OuterRef, Sum
from django.db.models.aggregates import Max
from django.db.models.functions import Concat, Cast, Coalesce, NullIf, TruncDate, TruncWeek, TruncMonth
from django.db.models.expressions import Func, ExpressionWrapper

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import DateTimeField
from rest_framework import exceptions as drf_exceptions

from model_utils import FieldTracker
from mptt.models import MPTTModel, TreeForeignKey
from django_q.tasks import async_task

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT, SOCKETIO_SYSTEM_CHANNEL, \
    TASK_DATES_CONTROL, FILTER_BY_ORGANIZATIONS, FRONTEND_URL, URLS

from common.current_profile.middleware import get_current_authenticated_profile
from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel
from common import fields as common_fields
from common.page_config.filter_fields import ChoiceFilterField, ForeignKeyFilterField, ProfileFilterField, \
    CharFilterField
from common.page_config import DefaultTableColumn
from common.redis import socketio_redis
from common.utils import UUIDEncoder
from common.estimates.models import AccumulationRegister
from common.catalogs.models import KlassificationModel

from change_history import utils as change_history_utils

from users.models import CustomUser, ProfileModel

from bpms.chat.models import ChatModel, MemberModel, MessageModel
from bpms.favorites.fields import InFavoritesFilterField
from telegram_bot.base import welcome_bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from . import fields

AVAILABLE_STATUSES = {
    'owner': {
        'new', 'in_work', 'on_check', 'on_rework', 'on_testing', 'second_queue', 'need_help', 'on_pause', 'completed',
    },
    'operator': {
        'new', 'in_work', 'on_check', 'on_rework', 'second_queue', 'need_help', 'on_pause',
    },
    'project_moderator': {
        'new', 'in_work', 'on_check', 'on_rework', 'on_testing', 'second_queue', 'need_help', 'on_pause', 'completed',
    },
}

AVAILABLE_COOP_STATUSES = {
    'owner': {
        'new', 'in_work', 'on_check', 'on_rework', 'on_testing', 'second_queue', 'need_help', 'on_pause', 'completed',
    },
    'operator': {
        'new', 'in_work', 'on_check', 'on_rework', 'on_testing', 'second_queue', 'need_help', 'on_pause', 'completed',
    },
    'project_moderator': {
        'new', 'in_work', 'on_check', 'on_rework', 'on_testing', 'second_queue', 'need_help', 'on_pause', 'completed',
    },
    'cooperator': {
        'new', 'in_work', 'on_check', 'on_testing', 'second_queue', 'need_help', 'on_pause',
    },
}


# Убираем Более не будет использоваться
def get_task_count(instance):
    counter = TaskCounterModel.objects.create(organization=instance.organization,
                                              task_type=instance.task_type)
    return counter.pk


class TaskCounterModel(models.Model):
    organization = models.ForeignKey('catalogs.ContractorModel',
                                     null=True,
                                     blank=False,
                                     verbose_name=_('Организация для нумерации'),
                                     on_delete=CUSTOM_CASCADE)
    number = models.IntegerField(default=0,
                                 verbose_name=_('Числовой инкрементальный номер'))
    number_formatted = models.CharField(default='',
                                        verbose_name=_('Строковый номер с префиксом'),
                                        max_length=20,
                                        db_index=True)
    task_type = common_fields.CustomForeignKey(
        to='tasks.TaskTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        default='',
        verbose_name=_('Тип задачи для нумерации')
    )

    do_magic = True

    def __str__(self):
        return self.number_formatted

    def save(self, *args, **kwargs):

        if not self.do_magic:
            super().save(*args, **kwargs)
            return

        with transaction.atomic():
            for_lock = self.__class__.objects.filter(organization=self.organization,
                                                     task_type=self.task_type).select_for_update(nowait=False)

            max_number = for_lock.aggregate(number=Max('number'))
            numb = max_number['number']
            if not numb:
                numb = 0
            self.number = numb + 1

            prefix = ''
            if self.organization.doc_prefix.strip() != '':
                prefix = self.organization.doc_prefix + '-'

            self.number_formatted = prefix + "{:05d}".format(self.number)

            super().save(*args, **kwargs)

    class Meta:
        index_together = ['organization', 'task_type']


class TaskSprintModel(BaseModel):
    meta_exclude_fields = ['is_demo', 'task_count_history', 'time_interval', 'created_at', 'mentions', 'ct',
    'workgroup', 'project', ]
    field_verbose_names = {
        'author': _('Автор спринта'),
        'status': _('Статус спринта'),
    }
    name = common_fields.CustomCharField(max_length=255,
                                         null=False,
                                         default="",
                                         verbose_name=_('Название'))
    dead_line = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Крайний срок"),
    )
    STATUS_CHOICES = (
        ('new', _('Новый')),
        ('in_process', _('В процессе')),
        ('completed', _('Завершен')))
    status = common_fields.CustomCharField(
        choices=STATUS_CHOICES,
        max_length=10,
        null=False,
        default='new',
        verbose_name=_('Статус'),
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'}
    )
    begin_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала'),
    )
    finished_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Дата завершения"),
    )

    # Deprecated
    TIME_INTERVAL_CHOICES = (('week', 'Неделя'),
                             ('two_week', 'Две недели'),
                             ('month', 'Месяц'),)
    # Deprecated
    time_interval = common_fields.CustomCharField(
        choices=TIME_INTERVAL_CHOICES,
        max_length=10,
        null=False,
        default='month',
        verbose_name=_('Временной промежуток'),
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'}
    )

    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        default=7,
        verbose_name=_('Продолжительность'),
        blank=False,
    )
    target = common_fields.CustomCharField(max_length=255,
                                           null=False,
                                           blank=True,
                                           default="",
                                           verbose_name=_('Цель'))
    expected_result = ArrayField(
        models.CharField(max_length=1023, blank=True),
        size=40,
        default=list,
        blank=True,
        verbose_name=_('Ожидаемый результат'),
    )
    members = models.ManyToManyField('users.ProfileModel',
                                     through='TaskSprintMember',
                                     related_name='task_sprint_members',
                                     verbose_name=_('Участники'),
                                     )
    # DEPRECATED
    workgroup = common_fields.CustomForeignKey(
        'workgroups.WorkgroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_("Команда"),
        related_name='workgroup_sprints',
        null=True,
        blank=True,
        filter_info=ForeignKeyFilterField(filters=[{"name": "is_project",
                                                    'value': False,
                                                    'type': 'defined'}])
    )
    # DEPRECATED
    project = common_fields.CustomForeignKey(
        'workgroups.WorkgroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Project'),
        related_name='project_sprints',
        null=True,
        blank=True,
        filter_info=ForeignKeyFilterField(filters=[{"name": "is_project",
                                                    'value': True,
                                                    'type': 'defined'}])
    )

    projects = models.ManyToManyField(
        to='workgroups.WorkgroupModel',
        related_name='sprints',
        through='SprintProjectThroughModel',
        through_fields=('sprint', 'project',),
        verbose_name=_('Проекты'),
    )

    task_count_history = models.JSONField(
        null=False,
        blank=True,
        default=dict,
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')

    projects_filter = fields.SprintProjectFilterField()

    def update_dead_line(self):
        now = timezone.now()
        dead_line = now + datetime.timedelta(days=self.duration)
        self.dead_line = dead_line
        if not self.begin_date:
            self.begin_date = now
        # sprint_tasks = self.tasks.all()
        # for task in sprint_tasks:
        #     task.is_indefinite = False
        #     task.dead_line = dead_line
        #     task.save()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.status == 'in_process' and not self.dead_line:
                self.update_dead_line()
            # elif self.status == 'completed':
            #     self.finished_date = timezone.now()
            #     not_finished_tasks = self.tasks.exclude(status='completed')
            #     for task in not_finished_tasks:
            #         task.sprint = None
            #         task.sprint_history.add(self)
            #         task.save()
            super().save(*args, **kwargs)

    data_path = '/tasks/sprint/list/'

    @classmethod
    def get_table_columns(cls):
        return ['name', 'status', 'target', 'dead_line', 'author', 'projects_filter']

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TaskSprintListSerializer, TaskSprintShortSerializer
        if action == 'notify':
            return TaskSprintShortSerializer
        elif action == 'list':
            return TaskSprintShortSerializer
        return TaskSprintListSerializer

    def __str__(self):
        return f'{self.name}'

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import get_task_sprint_queryset
        queryset = get_task_sprint_queryset(request)
        return queryset

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_queryset(request).filter(
            models.Q(name__icontains=text),
            is_active=True,
        ).order_by(
            '-created_at',
        ).distinct()

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.get_queryset(request)

    @classmethod
    def search_input(cls):
        return True

    def get_detail_permission(self, request) -> bool:
        from .utils import get_task_sprint_queryset
        return get_task_sprint_queryset(request).filter(pk=self.pk).exists()

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if user == self.author:
            return True
        projects = self.projects.all()
        for project in projects:
            if project.get_update_permission(request):
                return True
        return False

    def set_is_active(self, value: bool, request):
        with transaction.atomic():
            if value is False:
                self.is_active = False
                self.deleted_at = timezone.now()
                TaskModel.objects.filter(sprint=self).update(sprint=None)

    @property
    def progress(self):
        """Процент выполнения задач спринта."""
        tasks = self.tasks.filter(is_active=True, task_type='task')
        if tasks.exists():
            from bpms.tasks.utils import get_tasks_status_count
            tasks_status = get_tasks_status_count(tasks)
            percent = round(tasks_status['completed'] / tasks.count(), 2)
            return percent
        else:
            return None

    class Meta:
        verbose_name = _("Спринт")
        verbose_name_plural = _("Спринты")


class SprintExpectedResultModel(BaseModel):
    sprint = common_fields.CustomForeignKey(
        to='tasks.TaskSprintModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='sprint_expected_results',
        verbose_name=_('Спринт')
    )
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='sprint_expected_results',
        verbose_name=_('Задача')
    )
    comment = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Комментарий')
    )
    approved = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Принято')
    )

    class Meta:
        verbose_name = _('Ожидаемый результат')
        verbose_name_plural = _('Ожидаемые результаты')
        unique_together = (('task', 'sprint',),)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SprintExpectedResultListSerializer
        return SprintExpectedResultListSerializer

    def get_update_permission(self, request) -> bool:
        return self.sprint.get_update_permission(request)


class MovedToChoices(models.TextChoices):
    BACKLOG = 'backlog', _('бэклог')
    SPRINT = 'sprint', _('спринт')


class TaskSprintHistoryModel(BaseAbstractModel):
    task = models.ForeignKey(
        'tasks.TaskModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='task_sprint_history',
        verbose_name=_('Задача'),
    )
    sprint = models.ForeignKey(
        'tasks.TaskSprintModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='task_sprint_history',
        verbose_name=_('Спринт'),
    )
    moved_to_sprint = models.ForeignKey(
        'tasks.TaskSprintModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='task_sprint_history_moved',
        verbose_name=_('Перемещено в спринт'),

    )
    moved_to = models.CharField(
        max_length=31,
        choices=MovedToChoices.choices,
        default=MovedToChoices.BACKLOG,
        null=False,
        blank=False,
        verbose_name=_('Перемещено в')
    )
    status = models.ForeignKey(
        'tasks.TaskStatusModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=False,
        default='in_work',
        related_name='task_sprint_history',
        verbose_name=_('Статус')
    )
    for_completed = models.BooleanField(
        default=False,
    )
    add_sprint_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата добавления в спринт'
    )
    blockers = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Блокеры')
    )

    class Meta:
        verbose_name = 'История задач спринта'
        verbose_name_plural = 'Истории задач спринта'
        unique_together = (('task', 'sprint',),)


class SprintProjectThroughModel(BaseAbstractModel):
    project = common_fields.CustomForeignKey(
        to='workgroups.WorkgroupModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='sprints_through',
    )
    sprint = common_fields.CustomForeignKey(
        to='tasks.TaskSprintModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='projects_through',
    )

    class Meta:
        verbose_name = _('Спринт M2M')
        verbose_name_plural = _('Спринты M2M')
        unique_together = (('project', 'sprint',),)


class TaskSprintMember(models.Model):
    class Meta:
        unique_together = (('user', 'sprint'),)
        verbose_name = _('Участник спринта')
        verbose_name_plural = _('Участники спринта')

    log_target_field = 'members'
    user = models.ForeignKey('users.ProfileModel',
                             null=True,
                             on_delete=CUSTOM_CASCADE, )
    sprint = models.ForeignKey(TaskSprintModel,
                               null=True,
                               on_delete=CUSTOM_CASCADE,
                               related_name='task_sprint_members')

    def __str__(self):
        return f'{self.user.full_name} {self.sprint.name}'


class TaskScenarioModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Сценарий задачи')
        verbose_name_plural = _('Сценарии задачи')


class TaskStatusWorkTypeConnectModel(BaseAbstractModel):
    status = common_fields.CustomOneToOneField(to='tasks.TaskStatusModel', on_delete=CUSTOM_CASCADE)
    worktype = models.ManyToManyField('tasks.TaskWorkTypeModel')


class TaskTypeModel(BaseCatalog, BaseAbstractCatalog):
    meta_exclude_fields = ['show_step', 'author', 'name', 'code', 'created_at', 'mentions', 'ct', ]
    show_step = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Показать шаг'),
    )

    class Meta:
        verbose_name = _('Тип задачи')
        verbose_name_plural = _('Типы задач')

    @classmethod
    def is_enum(cls):
        return True


class TaskModel(BaseModel, MPTTModel, MetadataAbstractModel):
    """Модель задач."""
    tps = []
    meta_exclude_fields = ['number_from_counter', 'counter_old', 'parent', 'level', 'lft', 'rght',
                           'tree_id', 'reason', 'contractor', 'potential_contractor', 'lead_source', 'rejection_reason',
                           'prerequisites', 'date_start_fact',
                           'rejected', 'is_overdue', 'is_visor_create', 'is_auction', 'with_chat', 'linked_chat', 'mentions', 'ct',
                           'sprint_history', 'scenario',
                           'tmp_phone', 'color', 'is_need_to_make_event', 'measure_unit', 'is_demo', 'is_onboarding',
                           'add_sprint_date', 'is_active_custom', 'is_sign_task', 'is_auto_created', 'watchlist_snoozed_until',]

    # Переопределение verbose_name для унаследованных полей
    field_verbose_names = {'author': _('Автор задачи'), }

    meta_sort_fields = ['author', 'task_link', 'counter', 'name', 'created_at', 'result',
                        'sprint', 'organization', 'project', 'workgroup', 'owner',
                        'contract',
                        'operator', 'status', 'dead_line', 'date_start_plan', 'from_urv',
                        'description', 'priority', 'funds', 'execution_time_plan', 'is_indefinite',
                        'task_type', 'visors', 'cooperators', 'ticket_link',]

    tracker = FieldTracker(
        fields=(
            'name',
            'description',
            'priority',
            'is_auction',
            'dead_line',
            'date_start_plan',
            'owner_id',
            'operator_id',
            'status_id',
            'project_id',
            'workgroup_id',
            'contract_id',
            'sprint_id',
            'organization_id',
            'parent_id',
        )
    )

    m2m_track_fields = ('attachments', 'visors', 'cooperators',)

    counter = common_fields.CustomCharField(max_length=20,
                                            default='',
                                            blank=False,
                                            verbose_name=_("Номер задачи", )
                                            )
    number_from_counter = models.IntegerField(default=0, blank=True)
    counter_old = common_fields.CustomOneToOneField(
        to='tasks.TaskCounterModel',
        on_delete=CUSTOM_SET_NULL,
        null=True,
        # default=get_task_count,
        filter_info=CharFilterField(obj_type='CharField'),
        filter_lookup={"value": ""},
        verbose_name=_("Номер", )
    )

    parent = TreeForeignKey('self', on_delete=CUSTOM_PROTECT, null=True, blank=True, related_name='children')
    # level = models.IntegerField(default=0)
    # lft = models.IntegerField(default=0)
    # rght = models.IntegerField(default=0)
    # tree_id = models.IntegerField(default=0)

    level = models.PositiveIntegerField(db_index=True, editable=False)
    lft = models.PositiveIntegerField(db_index=True, editable=False)
    rght = models.PositiveIntegerField(db_index=True, editable=False)
    tree_id = models.PositiveBigIntegerField(db_index=True, editable=False)

    is_active_custom = common_fields.CustomBooleanField(default=True, editable=False)

    name = common_fields.CustomCharField(max_length=255,
                                         null=False,
                                         default="",
                                         verbose_name=_('Название'))
    result = common_fields.CustomCharField(max_length=255,
                                           null=True,
                                           blank=True,
                                           default='',
                                           verbose_name=_('Результат'))
    reason = common_fields.CustomCharField(
        max_length=36,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Источник'),
    )
    sprint = common_fields.CustomForeignKey('tasks.TaskSprintModel',
                                            null=True,
                                            blank=True,
                                            verbose_name=_('Спринт'),
                                            related_name='tasks',
                                            on_delete=CUSTOM_PROTECT,
                                            filter_info=ForeignKeyFilterField())
    add_sprint_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата добавления в спринт')
    )
    PRIORITY_CHOICES = (
        (0, _('Очень низкий')), (1, _('Низкий')), (2, _('Обычный')), (3, _('Высокий')), (4, _('Очень высокий')))
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_("Организация"),
        related_name="tasks",
        null=True,
        blank=False,
    )
    project = common_fields.CustomForeignKey(
        'workgroups.WorkgroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Проект'),
        related_name='project_tasks',
        null=True,
        blank=True,
        filter_info=ForeignKeyFilterField(filters=[{"name": "is_project",
                                                    'value': True,
                                                    'type': 'defined'}])
    )
    contract = common_fields.CustomForeignKey(
        'customer_contracts.CustomerContractModel',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Контракт'),
        related_name='tasks',
        null=True,
        blank=True,
        filter_info=ForeignKeyFilterField(),
    )
    customer_card = common_fields.CustomForeignKey(
        'help_desk.CustomerCardModel',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Клиент'),
        related_name='tasks',
        null=True,
        blank=True,
        filter_info=ForeignKeyFilterField(),
    )
    workgroup = common_fields.CustomForeignKey(
        'workgroups.WorkgroupModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_("Команда"),
        related_name='workgroup_tasks',
        null=True,
        blank=True,
        filter_info=ForeignKeyFilterField(filters=[{"name": "is_project",
                                                    'value': False,
                                                    'type': 'defined'}])
    )
    owner = common_fields.CustomForeignKey(
        'users.ProfileModel',
        null=True,
        on_delete=CUSTOM_PROTECT,
        related_name='owner_tasks',
        verbose_name=_('Постановщик'),
        filter_info=ProfileFilterField(),
    )
    operator = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Ответственный'),
        related_name='operator_tasks',
        filter_info=ProfileFilterField(),
    )
    status = common_fields.CustomForeignKey(
        'tasks.TaskStatusModel',
        to_field='code',
        null=False,
        default='new',
        verbose_name=_('Статус'),
        on_delete=CUSTOM_PROTECT,
        related_name='tasks',
    )
    contractor = common_fields.CustomForeignKey(
        'catalogs.ContractorModel',
        null=True,
        blank=True,
        verbose_name=_('Контрагент'),
        on_delete=CUSTOM_PROTECT,
        related_name='my_tasks',
    )
    potential_contractor = common_fields.CustomForeignKey(
        'catalogs.PotentialContractorModel',
        null=True,
        blank=True,
        verbose_name=_('Лид'),
        on_delete=CUSTOM_PROTECT,
        related_name='my_tasks',
    )
    lead_source = common_fields.CustomForeignKey(
        'tasks.LeadSourceModel',
        null=True,
        blank=True,
        verbose_name=_('Источник лида'),
        on_delete=CUSTOM_PROTECT,
        related_name='tasks',
    )
    rejection_reason = common_fields.CustomForeignKey(
        'tasks.RejectionReasonModel',
        null=True,
        blank=True,
        verbose_name=_('Причина отказа'),
        on_delete=CUSTOM_PROTECT,
        related_name='tasks',
    )
    visors = models.ManyToManyField(
        'users.ProfileModel',
        through='TaskVisor',
        verbose_name=_('Наблюдатели'),
        related_name='visor_tasks',
    )
    cooperators = models.ManyToManyField(
        'users.ProfileModel',
        through='TaskCooperator',
        verbose_name=_('Соисполнители'),
        related_name='cooperator_tasks',
    )
    prerequisites = models.ManyToManyField('self',
                                           related_name='postrequisites',
                                           through='TaskPrerequisite',
                                           verbose_name=_('Предшествующие задачи'),
                                           symmetrical=False)
    dead_line = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Крайний срок"),
    )
    date_start_plan = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Планируемая дата начала")
    )
    date_start_fact = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Фактическая дата начала")
    )
    finished_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Фактическая дата завершения"),
    )
    rejected = common_fields.CustomBooleanField(default=False,
                                                verbose_name=_('Отвергнутая'))
    from_urv = common_fields.CustomBooleanField(default=False,
                                                verbose_name=_('Задача из УРВ'))
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Описание"),
    )
    priority = common_fields.CustomPositiveIntegerField(
        choices=PRIORITY_CHOICES,
        null=True,
        blank=True,
        default=2,
        verbose_name=_("Приоритет"),
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'},
    )
    funds = common_fields.CustomDecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        verbose_name=_('Стоимость задачи'),
        null=False,
        blank=False,
        validators=(MinValueValidator(0, message=_('The value can only positive or 0')),)
    )
    execution_time_plan = common_fields.CustomDecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Планируемые трудозатраты в часах'),
        validators=(MinValueValidator(0, message=_('The value can only be positive or 0')),)
    )
    is_overdue = common_fields.CustomBooleanField(default=False, verbose_name=_("Просрочена"))
    is_indefinite = common_fields.CustomBooleanField(default=False, verbose_name=_("Без срока"))
    is_visor_create = common_fields.CustomBooleanField(default=False,
                                                       verbose_name=_('Наблюдатели могут создавать подзадачи'))
    is_auction = common_fields.CustomBooleanField(default=False,
                                                  verbose_name=_('Аукцион'))
    with_chat = common_fields.CustomBooleanField(default=False, verbose_name=_("Задача с чатом"))
    linked_chat = common_fields.CustomForeignKey('chat.ChatModel',
                                                 to_field='chat_uid',
                                                 verbose_name=_("Связанный чат"),
                                                 null=True,
                                                 blank=True,
                                                 on_delete=CUSTOM_PROTECT)
    sprint_history = models.ManyToManyField('tasks.TaskSprintModel',
                                            related_name='not_completed_tasks',
                                            blank=True,
                                            verbose_name=_('История спринтов'))

    task_type = common_fields.CustomForeignKey(
        to='tasks.TaskTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=False,
        default='task',
        verbose_name=_('Тип задачи')
    )
    scenario = common_fields.CustomForeignKey(
        to='tasks.TaskScenarioModel',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        verbose_name=_('Сценарий')
    )
    tmp_phone = models.CharField(verbose_name=_('Phone'), max_length=20, null=True, blank=True, default='')
    color = common_fields.CustomCharField(
        max_length=7,
        verbose_name=_('Цвет'),
        null=False,
        blank=True,
        default='',
    )
    is_need_to_make_event = common_fields.CustomBooleanField(default=False,
                                                             verbose_name=_('Создавать событие'))
    is_onboarding = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Для знакомства с системой'),
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')
    is_sign_task = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Задача на подпись'))
    is_auto_created = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Создана автоматически'),
        help_text=_('Трудозатраты с видеовстречи'))
    watchlist_snoozed_until = common_fields.CustomDateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Отложено в контрольном списке до'),
    )

    is_daily_filter = fields.DailyTasksField()
    counter_filter = fields.CounterFilterField()
    without_order_filter = fields.WithoutOrderFilterField()
    is_overdue_filter = fields.OverdueFilterField()
    is_visor_filter = fields.VisorFilterField()
    is_cooperator_filter = fields.CooperatorFilterField()
    is_executor_filter = fields.ExecutorFilterField()
    is_participant_filter = fields.ParticipantFilterField()
    in_favorites_filter = InFavoritesFilterField()
    data_path = '/tasks/task/list/'

    @classmethod
    def get_snapshot(cls, id):
        """Короткий снимок для IntentModel (id, repr, image)."""
        from .serializers import ShortTaskSerializer

        task = cls.objects.get(id=id)
        serializer_data = ShortTaskSerializer().to_representation(task)

        return {
            "id": str(id),
            "repr": serializer_data.get("name", ""),
            "image": None,
        }

    def __str__(self):
        return f'{getattr(self, "counter", "")} {self.name}'

    class Meta:
        verbose_name = _("Задача")
        verbose_name_plural = _("Задачи")

    def track_m2m_fields(self, sender, model, pk_set, action, action_date):
        try:
            sender_label = sender.get_label()
        except AttributeError:
            return
        if sender_label == 'common.FileBaseModel':
            object_property_id = 'task__attachments'
            str_view = ','.join([each.full_name for each in list(model.objects.filter(pk__in=pk_set))])
        elif sender_label == 'tasks.TaskVisor':
            object_property_id = 'task__visors'
            str_view = ','.join([each.full_name for each in list(model.objects.filter(pk__in=pk_set))])
        elif sender_label == 'tasks.TaskCooperator':
            object_property_id = 'task__cooperators'
            str_view = ','.join([each.full_name for each in list(model.objects.filter(pk__in=pk_set))])
        else:
            return
        if action == 'post_add':
            change_history_utils.create_add_m2m(
                self.pk,
                action_date,
                object_property_id,
                str_view,
                pk_set,
            )
        elif action == 'post_remove':
            change_history_utils.create_remove_m2m(
                self.pk,
                action_date,
                object_property_id,
                str_view,
                pk_set,
            )

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        if 'name' in changed_fields:
            before = changed_fields['name'],
            after = self.name,
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'task__name',
                before,
                after,
            )
        if 'description' in changed_fields:
            before = changed_fields['description']
            after = self.description
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'task__description',
                before,
                after,
            )
        if 'priority' in changed_fields:
            before = self.priority_choices_dict.get(changed_fields['priority'], '')
            after = self.priority_choices_dict.get(self.priority)
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'task__priority',
                before,
                after,
            )
        if 'is_auction' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'task__is_auction',
                self.is_auction,
            )
        if 'dead_line' in changed_fields:
            dead_line_before = changed_fields['dead_line']
            dead_line_after = self.dead_line
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'task__dead_line',
                dead_line_before,
                dead_line_after,
            )
        if 'date_start_plan' in changed_fields:
            date_start_plan_before = changed_fields['date_start_plan']
            date_start_plan_after = self.date_start_plan
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'task__date_start_plan',
                date_start_plan_before,
                date_start_plan_after,
            )
        if 'owner_id' in changed_fields:
            owner_id_before = changed_fields['owner_id']
            owner_after = self.owner
            if owner_after:
                owner_id_after = self.owner.pk
            else:
                owner_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'task__owner',
                owner_id_before,
                owner_id_after,
            )
        if 'operator_id' in changed_fields:
            operator_id_before = changed_fields['operator_id']
            operator_after = self.operator
            if operator_after:
                operator_id_after = self.operator.pk
            else:
                operator_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'task__operator',
                operator_id_before,
                operator_id_after,
            )
        if 'status_id' in changed_fields:
            status_code_before = changed_fields['status_id']
            if status_code_before:
                status_id_before = TaskStatusModel.objects.get(code=status_code_before).pk
            else:
                status_id_before = None
            status_id_after = self.status.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'task__status',
                status_id_before,
                status_id_after,
            )
        if 'project_id' in changed_fields:
            project_after = self.project
            if project_after:
                project_id_after = project_after.pk
            else:
                project_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'task__project',
                changed_fields['project_id'],
                project_id_after,
            )
        if 'workgroup_id' in changed_fields:
            workgroup_after = self.workgroup
            if workgroup_after:
                workgroup_id_after = workgroup_after.pk
            else:
                workgroup_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'task__workgroup',
                changed_fields['workgroup_id'],
                workgroup_id_after,
            )
        if 'sprint_id' in changed_fields:
            sprint_id_before = changed_fields['sprint_id']
            sprint_after = self.sprint
            if sprint_after:
                sprint_id_after = sprint_after.pk
            else:
                sprint_id_after = None

            # Добавление задачи в спринт
            if sprint_id_before is None and sprint_id_after is not None:
                sprint = TaskSprintModel.objects.get(pk=sprint_id_after)
                description = f'Задача добавлена в спринт {sprint.name}'
                change_history_utils.create_add_m2m(
                    self.pk,
                    action_date,
                    'task__sprint',
                    sprint.name,
                    {sprint_id_after},
                    description=description,
                )
            # Удаление задачи из спринта
            elif sprint_id_before is not None and sprint_id_after is None:
                sprint = TaskSprintModel.objects.get(pk=sprint_id_before)
                description = f'Задача удалена из спринта {sprint.name}'
                change_history_utils.create_remove_m2m(
                    self.pk,
                    action_date,
                    'task__sprint',
                    sprint.name,
                    {sprint_id_before},
                    description=description,
                )
            # Изменение спринта (замена одного спринта на другой)
            elif sprint_id_before is not None and sprint_id_after is not None and sprint_id_before != sprint_id_after:
                sprint_before = TaskSprintModel.objects.get(pk=sprint_id_before)
                sprint_after_obj = TaskSprintModel.objects.get(pk=sprint_id_after)
                # Сначала удаление старого спринта
                change_history_utils.create_remove_m2m(
                    self.pk,
                    action_date,
                    'task__sprint',
                    sprint_before.name,
                    {sprint_id_before},
                )
                # Затем добавление нового спринта
                description = f'Задача добавлена в спринт {sprint_after_obj.name}'
                change_history_utils.create_add_m2m(
                    self.pk,
                    action_date,
                    'task__sprint',
                    sprint_after_obj.name,
                    {sprint_id_after},
                    description=description,
                )
        if 'organization_id' in changed_fields:
            organization_after = self.organization
            if organization_after:
                organization_id_after = organization_after.pk
            else:
                organization_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'task__organization',
                changed_fields['organization_id'],
                organization_id_after,
            )
        if 'parent_id' in changed_fields:
            parent_after = self.parent
            if parent_after:
                parent_id_after = parent_after.pk
            else:
                parent_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'task__parent',
                changed_fields['parent_id'],
                parent_id_after,
            )

    def create_chat(self, members, linked_chat):
        from bpms.chat.serializers import MessageListSerializer
        if not linked_chat:
            chat = ChatModel.objects.create(
                is_public=True,
                chat_author=self.author,
                name=self.name,
                last_sent=timezone.now(),
            )
            chat_members = []
            for each in members:
                member = MemberModel()
                member.chat = chat
                member.user = each
                if each in [self.author, self.owner]:
                    member.is_moderator = True
                try:
                    member.save()
                except IntegrityError:
                    continue
                chat_members.append(member)
            self.linked_chat = chat
            self.save()
            data = json.dumps(
                {"event": "chat_create_chat",
                 "data": {
                     "chat_uid": str(chat.chat_uid),
                     "is_public": True,
                     "members": [{"user": str(each.user_id), "is_moderator": str(each.is_moderator)} for each in
                                 chat_members],
                     "name": chat.name,
                     "chat_author": str(chat.chat_author.pk),
                     "last_sent": DateTimeField().to_representation(chat.last_sent),
                     "new_message_count": 0,
                     "member_count": len(chat_members),
                     "is_active": True,
                 }
                 }
            )
            socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
        if linked_chat:
            self.linked_chat = linked_chat
            self.save()
        message = MessageModel()
        message.chat = self.linked_chat
        message.is_system = True
        message.created = timezone.now()
        message.share = self
        message.text = f'Пользователь {self.author.full_name} прикрепил чат к задаче \"{self.name}\"'
        message.save()
        message_data = MessageListSerializer(message).data
        message_data['chat_uid'] = str(message.chat.chat_uid)
        message_data['chat_name'] = message.chat.name
        message_data['is_public'] = message.chat.is_public
        message_data['is_new'] = True
        data = json.dumps(
            {
                "event": "chat_message",
                "data": message_data,
            },
            cls=UUIDEncoder
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)

    def check_dates(self):
        pass
        if self.date_start_plan and self.dead_line and self.date_start_plan > self.dead_line:
            raise drf_exceptions.ValidationError('Дата начала не может быть позже даты окончания.')
        parent = self.parent
        if parent and parent.date_start_plan and self.date_start_plan and parent.date_start_plan > self.date_start_plan:
            raise drf_exceptions.ValidationError('Дата начала не может быть раньше чем у родительской задачи.')
        if parent and parent.dead_line and self.dead_line and parent.dead_line < self.dead_line:
            raise drf_exceptions.ValidationError('Крайний срок не может быть позже чем у родительской задачи.')
        if self.dead_line and self.pk and self.get_descendants().filter(
                is_active=True,
                dead_line__gt=self.dead_line,
                dead_line__isnull=False
        ).exists():
            raise drf_exceptions.ValidationError('Крайний срок не может быть раньше чем у подзадач.')
        if self.date_start_plan and self.pk and self.get_descendants().filter(
                is_active=True,
                date_start_plan__lt=self.date_start_plan,
                date_start_plan__isnull=False
        ).exists():
            raise drf_exceptions.ValidationError('Дата начала не может быть позже чем у подзадач.')
        # project = self.project
        # if project and project.control_dates:
        #     if project.dead_line and self.dead_line and project.dead_line < self.dead_line:
        #         raise drf_exceptions.ValidationError('Крайний срок не может быть позже крайнего срока проекта.')
        #     if project.date_start_plan and self.date_start_plan and project.date_start_plan > self.date_start_plan:
        #         raise drf_exceptions.ValidationError('Дата начала не может быть раньше чем у проекта.')

    def get_task_count_char(self):
        counter = TaskCounterModel.objects.create(organization=self.organization,
                                                  task_type=self.task_type)
        return counter.number, counter.number_formatted

    def save(self, *args, **kwargs):

        # убираем. Не сработала гипотеза
        self.is_sign_task = False

        is_created = True if self.pk is None else False

        if FILTER_BY_ORGANIZATIONS and self.organization_id is None:
            raise ValidationError('Должно быть заполнено поле Организация')

        if is_created:
            number, pref_number = self.get_task_count_char()

            self.number_from_counter = number
            self.counter = pref_number

        if self.is_indefinite is True:
            self.dead_line = None
        if self.dead_line:
            self.is_indefinite = False
        if TASK_DATES_CONTROL:
            self.check_dates()
        if self.owner is None:
            self.owner = self.author
        if self.operator is None:
            self.operator = self.author
        if self.priority is None:
            self.priority = 2
        if self.pk:
            history_records_count = self.task_sprint_history.all().count()
            if history_records_count >= 3:
                self.rejected = True
        parent = self.parent
        if parent:
            self.project = getattr(parent, 'project', None)
            self.workgroup = getattr(parent, 'workgroup', None)
            self.contract = getattr(parent, 'contract', None)
            self.customer_card = getattr(parent, 'customer_card', None)
        if self.task_type.code == 'helpdesk':
            self.operator = self.workgroup.author

        if not is_created:
            old_operator = TaskModel.objects.get(pk=self.pk).operator_id
            if old_operator:
                cache.set('CachedAppUserSerializer_' + str(old_operator), None)

        self.is_active_custom = self.is_active

        # Сохраняем старые значения проекта/команды и имени до сохранения
        old_project = None
        old_workgroup = None
        old_name = None
        if not is_created:
            old_task = TaskModel.objects.only('project', 'workgroup', 'name').get(pk=self.pk)
            old_project = old_task.project
            old_workgroup = old_task.workgroup
            old_name = old_task.name

        # Проверяем, что новый проект не завершен
        if self.project and (is_created or old_project != self.project):
            if self.project.is_finished:
                raise ValidationError(gettext('Нельзя добавить задачу в завершённый проект'))
        old_status_code = self.tracker.changed().get('status_id', '')
        new_status_code = self.status.code
        old_contract_id = self.tracker.changed().get('contract_id', '')
        new_contract = self.contract
        super().save(*args, **kwargs)
        from .utils import get_cached_statuses
        _, not_completed_statuses, completed_statuses = get_cached_statuses()
        if old_status_code in not_completed_statuses and new_status_code in completed_statuses:
            transaction.on_commit(lambda: self.complete_timers())
        if old_name != self.name:
            from bpms.event_calendar.utils import sync_related_calendar_name
            sync_related_calendar_name(related_object_id=self.pk)
        from .utils import check_need_set_calendar_event_by_task

        # Пересчёт прогресса рабочей группы/проекта
        from bpms.workgroups.utils import compute_workgroup_progress

        def update_workgroup_progress():
            # Проверяем изменение project
            if old_project != self.project:
                if old_project:
                    old_project.refresh_from_db()
                    old_progress = compute_workgroup_progress(old_project)
                    if old_project.progress != old_progress:
                        old_project.progress = old_progress
                        old_project.save(update_fields=["progress"])

                if self.project:
                    self.project.refresh_from_db()
                    new_progress = compute_workgroup_progress(self.project)
                    if self.project.progress != new_progress:
                        self.project.progress = new_progress
                        self.project.save(update_fields=["progress"])
            elif self.project:
                self.project.refresh_from_db()
                new_progress = compute_workgroup_progress(self.project)
                if self.project.progress != new_progress:
                    self.project.progress = new_progress
                    self.project.save(update_fields=["progress"])

            # Проверяем изменение workgroup
            if old_workgroup != self.workgroup:
                if old_workgroup:
                    old_workgroup.refresh_from_db()
                    old_progress = compute_workgroup_progress(old_workgroup)
                    if old_workgroup.progress != old_progress:
                        old_workgroup.progress = old_progress
                        old_workgroup.save(update_fields=["progress"])

                if self.workgroup:
                    self.workgroup.refresh_from_db()
                    new_progress = compute_workgroup_progress(self.workgroup)
                    if self.workgroup.progress != new_progress:
                        self.workgroup.progress = new_progress
                        self.workgroup.save(update_fields=["progress"])
            elif self.workgroup:
                self.workgroup.refresh_from_db()
                new_progress = compute_workgroup_progress(self.workgroup)
                if self.workgroup.progress != new_progress:
                    self.workgroup.progress = new_progress
                    self.workgroup.save(update_fields=["progress"])

        transaction.on_commit(update_workgroup_progress)

        if is_created and getattr(self.operator, 'telegram_id'):

            task = self
            formatted_deadline = "Не указан"
            if task.dead_line:
                formatted_deadline = task.dead_line.strftime("%Y-%m-%d %H:%M:%S")  # Format the deadline

            response_text = (
                f"Новая задача!"
                f"\u2714 {task.name}\n"
                f"Номер: {task.counter}\n"
                f"Автор: {task.owner}\n"
                f"Создана: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Приоритет: {task.priority}\n"
                f"Статус: {task.status}\n"
                f"Дедлайн: {formatted_deadline}\n\n"
            )
            row = 1

            buttons = []
            button1 = InlineKeyboardButton(text="В работу",
                                           callback_data=f"task_status_set_inwork_{task.id}")
            buttons.append(button1)

            markup = InlineKeyboardMarkup(row_width=row)
            markup.add(*buttons)
            # welcome_bot.send_message(chat_id=task.operator.telegram_id,
            #                         reply_markup=markup,
            #                         text=response_text)

        if self.operator:
            cache.set('CachedAppUserSerializer_' + str(self.operator.pk), None)
        from .utils import send_socketio_about_task_touch, send_socketio_about_update_task, \
            send_socketio_about_delete_task

        transaction.on_commit(lambda: async_task(send_socketio_about_task_touch, self))

        if not is_created and self.is_active:
            transaction.on_commit(lambda: async_task(send_socketio_about_update_task, self))
        if not is_created and not self.is_active:
            transaction.on_commit(lambda: async_task(send_socketio_about_delete_task, self))
            if self.contract:
                self.contract.recalculate_hours_fact()
        transaction.on_commit(lambda: async_task(check_need_set_calendar_event_by_task, self.id))

        KlassificationModel.objects.filter(related_object=self).delete()
        if old_contract_id:
            from customer_contracts.models import CustomerContractModel
            old_contract = CustomerContractModel.objects.filter(pk=old_contract_id).first()
            if old_contract:
                transaction.on_commit(lambda: old_contract.recalculate_hours_fact())
        if new_contract:
           new_contract.recalculate_hours_fact()

    def complete_timers(self):
        qs = self.execution_time.filter(is_current=True)
        from .utils import stop_work_log_timer
        for each in qs:
            user = each.user
            task = each.task
            stop_work_log_timer(user, task,)
        profiles_id = list(ProfileModel.objects.filter(current_work_id=self.pk).values_list('pk', flat=True))
        if profiles_id:
            ProfileModel.objects.filter(pk__in=profiles_id,).update(current_work=None)
            from common.utils import send_socketio_about_update_current_work
            transaction.on_commit(
                lambda: async_task(send_socketio_about_update_current_work, [str(_) for _ in profiles_id], )
            )

    def get_task_roles(self, profile_id):
        """Возвращает список ролей пользователя в текущей задаче."""
        task_roles = list()
        if self.owner_id == profile_id:
            task_roles.append('owner')
        if self.operator_id == profile_id:
            task_roles.append('operator')
        project = self.project
        if project:
            # если был Prefetch в атрибут prefetched_members
            if hasattr(project, 'prefetched_members'):
                for member in getattr(project, 'prefetched_members', None):
                    if (member.is_active and
                            member.membership_request_status.code == 'APPROVED' and
                            member.membership_role.code in ('FOUNDER', 'MODERATOR') and
                            member.member_id == profile_id):
                        task_roles.append('project_moderator')
                        break
            else:  # не оптимально, лучше делать через prefetched_members
                if project.workgroupmembersmodel_set.filter(
                        is_active=True,
                        membership_request_status__code='APPROVED',
                        membership_role__code__in=('FOUNDER', 'MODERATOR'),
                        member_id=profile_id,
                ).exists():
                    task_roles.append('project_moderator')
        if any(c.pk == profile_id for c in self.cooperators.all()):
            task_roles.append('cooperator')
        if any(c.pk == profile_id for c in self.visors.all()):
            task_roles.append('visor')
        return task_roles

    def get_available_statuses(self, profile_id):
        """Возвращает кортеж кодов статусов, разрешенных профилю profile менять в задаче."""
        task_roles = self.get_task_roles(profile_id)
        available_statuses = set()
        for task_role in task_roles:
            try:
                available_statuses.update(AVAILABLE_STATUSES[task_role])
            except KeyError:
                pass
        return tuple(available_statuses)

    def get_available_coop_statuses(self, profile_id):
        """Возвращает кортеж кодов статусов соисполнителя, разрешенных профилю profile менять в задаче."""
        task_roles = self.get_task_roles(profile_id)
        available_statuses = set()
        for task_role in task_roles:
            try:
                available_statuses.update(AVAILABLE_COOP_STATUSES[task_role])
            except KeyError:
                pass
        return tuple(available_statuses)

    @property
    def get_member_ids(self):
        """Возвращает список ID ProfileModel участников задачи.
        Участниками считаются: автор, постановщик, ответственный, наблюдатели, соисполнители."""
        member_ids = set()

        if self.author_id:
            member_ids.add(self.author_id)
        if self.owner_id:
            member_ids.add(self.owner_id)
        if self.operator_id:
            member_ids.add(self.operator_id)
        member_ids.update(self.visors.filter(is_active=True).values_list('pk', flat=True))
        member_ids.update(self.cooperators.all().values_list('pk', flat=True))
        return list(member_ids)

    def get_detail_permission(self, request) -> bool:
        from .utils import filter_by_permissions
        return filter_by_permissions(self._meta.model.objects.filter(is_active=True, pk=self.pk),
                                     request.user.profile).exists()

    def get_update_permission(self, request) -> bool:
        profile = request.user.profile
        roles = set(self.get_task_roles(profile.pk))
        if not roles.isdisjoint({'owner', 'project_moderator'}):
            return True
        else:
            return False

    def get_attach_permission(self, request) -> bool:
        profile = request.user.profile
        roles = set(self.get_task_roles(profile.pk))
        if not roles.isdisjoint({'operator', 'cooperator', 'owner', 'project_moderator'}):
            return True
        else:
            return False

    def get_update_tag_permission(self, request) -> bool:
        profile = request.user.profile
        roles = set(self.get_task_roles(profile.pk))
        if not roles.isdisjoint({'operator', 'cooperator', 'owner', 'visor', 'project_moderator'}):
            return True
        else:
            return False

        # user = request.user.profile
        # im_project_author = False
        # im_group_author = False
        # im_sprint_author = False
        # task_project = self.project
        # if task_project:
        #     im_project_author = task_project.author == user
        # task_group = self.workgroup
        # if task_group:
        #     im_group_author = task_group.author == user
        # task_sprint = self.sprint
        # if task_sprint and not task_sprint.status == 'completed' and task_sprint.author == user:
        #     im_sprint_author = True
        # im_dealer = False
        # contractor = self.contractor
        # if contractor:
        #     im_dealer = user in contractor.profiles.all()  # noqa
        # if user == self.owner or user == self.operator or im_dealer or im_group_author or im_project_author or \
        #         im_sprint_author:
        #     return True
        # else:
        #     return False

    @classmethod
    def get_queryset(cls, request=None):
        queryset = TaskModel.objects.filter(is_active=True)
        from .utils import get_task_queryset
        queryset = get_task_queryset(request, queryset)
        return queryset

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_table_structure(cls):
        columns = super().get_table_structure()
        for column in columns:
            key = column.get('key', '')
            if key == 'status':
                column['scopedSlots']['customRender'] = "TasksStatusRow"
        return columns

    # @classmethod
    # def get_table_columns(cls):
    #     return ['counter_filter', 'name', 'operator', 'is_cooperator_filter', 'author', 'owner', 'is_visor_filter',
    #             'is_executor_filter', 'is_participant_filter',
    #             'is_indefinite', 'is_overdue_filter', 'status',
    #             'workgroup', 'project', 'sprint', 'priority',
    #             'created_at', 'date_start_plan', 'dead_line', 'finished_date',
    #             'is_daily_filter', 'without_order_filter', 'in_favorites_filter',]

    @classmethod
    def get_table_columns(cls):
        return ['operator', 'is_cooperator_filter', 'author', 'owner', 'is_visor_filter',
                'is_executor_filter', 'is_participant_filter',
                'status', 'workgroup', 'project',
                'is_daily_filter', 'without_order_filter', ]

    @classmethod
    def get_additional_table_columns(cls):
        return ['counter_filter', 'name', 'sprint',
                'created_at', 'date_start_plan', 'dead_line', 'finished_date',
                'is_indefinite', 'is_overdue_filter', 'priority', ]

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        data = super().get_filter_fields(exclude=exclude, request=request)
        if request:
            page_name = request.query_params.get('page_name', '')
            is_interest = page_name.find('interest') > 0
            if is_interest and exclude is False:
                data.extend([
                    {
                        "name": "lead_source",
                        "type": "CustomForeignKey",
                        "verbose_name": _("Источник обращения"),
                        "widget": {
                            "type": "Select",
                            "mode": "tags",
                            "model": "tasks.LeadSourceModel",
                            "toField": "id",
                        },
                    },
                    {
                        "name": "rejection_reason",
                        "type": "CustomForeignKey",
                        "verbose_name": _("Причина отказа"),
                        "widget": {
                            "type": "Select",
                            "mode": "tags",
                            "model": "tasks.RejectionReasonModel",
                            "toField": "id",
                        },
                    }
                ])
            if is_interest and exclude is True:
                data.extend([
                    {
                        "name": "lead_source__exclude",
                        "type": "CustomForeignKey",
                        "verbose_name": _("Источник обращения"),
                        "widget": {
                            "type": "Select",
                            "mode": "tags",
                            "model": "tasks.LeadSourceModel",
                            "toField": "id",
                        },
                    },
                    {
                        "name": "rejection_reason__exclude",
                        "type": "CustomForeignKey",
                        "verbose_name": _("Причина отказа"),
                        "widget": {
                            "type": "Select",
                            "mode": "tags",
                            "model": "tasks.RejectionReasonModel",
                            "toField": "id",
                        },
                    }
                ])
            if FILTER_BY_ORGANIZATIONS and exclude is False:
                data.extend([
                    {
                        "name": "organization",
                        "type": "CustomForeignKey",
                        "verbose_name": _("Организация"),
                        "widget": {
                            "type": "Select",
                            "mode": "tags",
                            "model": "catalogs.ContractorModel",
                            "toField": "id",
                        },
                    }])
            if FILTER_BY_ORGANIZATIONS and exclude is True:
                data.extend([
                    {
                        "name": "organization__exclude",
                        "type": "CustomForeignKey",
                        "verbose_name": _("Организация"),
                        "widget": {
                            "type": "Select",
                            "mode": "tags",
                            "model": "catalogs.ContractorModel",
                            "toField": "id",
                        },
                    }])
            is_logistic = page_name.find('logistic') > 0
            if is_logistic:
                for each in data:
                    name = each.get('name', '')
                    if name in ('operator', 'operator__exclude',):
                        each['verbose_name'] = _('Водитель')
                    elif name in ('owner', 'owner__exclude',):
                        each['verbose_name'] = _('Логист')
                    elif name in ('visors', 'visors__exclude',):
                        each['verbose_name'] = _('Экипаж')
                    else:
                        pass
                data = list(filter(
                    lambda x: x.get('name', '') not in (
                        'workgroup',
                        'workgroup__exclude',
                        'project',
                        'project__exclude',
                        'sprint',
                        'sprint__exclude',
                        'is_auction',
                        'is_auction__exclude',
                        'organization',
                        'organization__exclude'
                    ),
                    data
                ))
            else:
                data = list(
                    filter(
                        lambda x: x.get('name', '') not in (
                            'is_daily_filter',
                            'is_daily_filter__exclude',
                            'without_order_filter',
                            'without_order_filter__exclude'
                        ),
                        data
                    )
                )
            if is_interest:
                task_status_type = 'interest'
            elif is_logistic:
                task_status_type = 'logistic'
            else:
                task_status_type = 'task'

            for each in data:
                name = each.get('name', '')
                if name in ('status', 'status__exclude'):
                    each['widget']['filters'] = [
                        {"name": "task_status_type__task_type", "value": task_status_type, "type": "defined"}
                    ]
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import CreateTaskSerializer, UpdateTaskSerializer, DetailTaskSerializer, ListTaskSerializer
        if action == 'create':
            return CreateTaskSerializer
        elif action in ['update', 'partial_update']:
            return UpdateTaskSerializer
        elif action == 'retrieve':
            return DetailTaskSerializer
        elif action == 'list':
            return ListTaskSerializer
        else:
            return ListTaskSerializer

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):

        qs = cls.get_select_queryset(request)
        return qs.filter(Q(name__icontains=text) | Q(counter__icontains=text)).distinct()

    @classmethod
    def get_select_queryset(cls, request=None):
        from .utils import filter_by_permissions
        qs = filter_by_permissions(cls.objects.filter(is_active=True), request.user.profile)
        return qs

    @classmethod
    def get_data_path(cls) -> str:
        return '/tasks/'

    @classmethod
    def get_order_param(cls):
        return ['name', ]

    @classmethod
    def has_characteristics_plan(cls):
        return True

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def _extract_report_bounds(cls, request, field_names):
        """Возвращает границы периода (date_from, date_to) из списка фильтров поля."""
        if not field_names:
            return None, None

        cache_attr = "_task_report_bounds_cache"
        cache_value = getattr(request, cache_attr, None)
        if not isinstance(cache_value, dict):
            cache_value = {}
            setattr(request, cache_attr, cache_value)
        cache_key = tuple(sorted(field_names))
        if cache_key in cache_value:
            return cache_value[cache_key]

        filters_raw = None
        query_params = getattr(request, "query_params", None)
        if query_params is not None:
            filters_raw = query_params.get("filters")
        if filters_raw in (None, "") and hasattr(request, "data"):
            request_data = request.data
            if isinstance(request_data, dict):
                filters_raw = request_data.get("filters")

        if not filters_raw:
            cache_value[cache_key] = (None, None)
            return None, None

        parsed_filters = filters_raw
        if isinstance(filters_raw, str):
            try:
                parsed_filters = json.loads(filters_raw)
            except (TypeError, json.JSONDecodeError):
                cache_value[cache_key] = (None, None)
                return None, None

        if isinstance(parsed_filters, list):
            parsed_filters = {
                "logic": "and",
                "filters": parsed_filters,
            }

        if not isinstance(parsed_filters, dict):
            cache_value[cache_key] = (None, None)
            return None, None

        def to_date(raw_value):
            if raw_value is None:
                return None
            if isinstance(raw_value, datetime.datetime):
                return raw_value.date()
            if isinstance(raw_value, datetime.date):
                return raw_value
            if isinstance(raw_value, str):
                parsed_datetime = dateparse.parse_datetime(raw_value)
                if parsed_datetime is not None:
                    return parsed_datetime.date()
                parsed_date = dateparse.parse_date(raw_value)
                if parsed_date is not None:
                    return parsed_date
            return None

        def iter_leaf_filters(group):
            for filter_item in group.get("filters", []):
                if "filters" in filter_item and isinstance(filter_item, dict):
                    yield from iter_leaf_filters(filter_item)
                elif isinstance(filter_item, dict):
                    yield filter_item

        period_from = None
        period_to = None
        field_names_set = set(field_names)
        for filter_item in iter_leaf_filters(parsed_filters):
            if filter_item.get("field") not in field_names_set:
                continue
            comparison_type = filter_item.get("comparison_type")
            raw_value = filter_item.get("value")
            normalized_date = to_date(raw_value)
            if normalized_date is None:
                continue

            if comparison_type in (">=", ">"):
                if period_from is None or normalized_date > period_from:
                    period_from = normalized_date
            elif comparison_type in ("<=", "<"):
                if period_to is None or normalized_date < period_to:
                    period_to = normalized_date

        cache_value[cache_key] = (period_from, period_to)
        return period_from, period_to

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        """Возвращает SQL-аннотации для отчётов."""
        annotations = {}
        names = set(requested_computed or [])
        outer_ref_column = kwargs.get('outer_ref_column')
        period_from, period_to = cls._extract_report_bounds(
            request,
            ["report_day", "report_week", "report_month", "report_period", "created_at"],
        )

        if 'report_day' in names:
            annotations['report_day'] = TruncDate('created_at')
        if 'report_week' in names:
            annotations['report_week'] = TruncWeek('created_at')
        if 'report_month' in names:
            annotations['report_month'] = TruncMonth('created_at')

        not_completed_statuses = []
        completed_statuses = []
        if names.intersection({
            'currently_completed',
            'currently_overdue',
            'closed_in_period',
            'currently_stalled',
        }):
            from bpms.tasks.utils import get_cached_statuses
            cached_statuses = get_cached_statuses()
            not_completed_statuses = cached_statuses[1]
            completed_statuses = cached_statuses[2]

        if 'currently_completed' in names:
            annotations['currently_completed'] = models.Case(
                models.When(status_id__in=completed_statuses, then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            )

        if 'currently_overdue' in names:
            annotations['currently_overdue'] = models.Case(
                models.When(
                    dead_line__isnull=False,
                    dead_line__lt=timezone.now(),
                    status_id__in=not_completed_statuses,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=models.BooleanField(),
            )

        created_period_filter = Q()
        created_period_is_set = False
        if period_from is not None:
            created_period_filter &= Q(created_at__date__gte=period_from)
            created_period_is_set = True
        if period_to is not None:
            created_period_filter &= Q(created_at__date__lte=period_to)
            created_period_is_set = True

        if 'created_in_period' in names:
            if created_period_is_set:
                annotations['created_in_period'] = models.Case(
                    models.When(created_period_filter, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            else:
                annotations['created_in_period'] = Value(False, output_field=models.BooleanField())

        closed_period_filter = Q(status_id__in=completed_statuses, finished_date__isnull=False)
        closed_period_is_set = False
        if period_from is not None:
            closed_period_filter &= Q(finished_date__date__gte=period_from)
            closed_period_is_set = True
        if period_to is not None:
            closed_period_filter &= Q(finished_date__date__lte=period_to)
            closed_period_is_set = True

        if 'closed_in_period' in names:
            if closed_period_is_set:
                annotations['closed_in_period'] = models.Case(
                    models.When(closed_period_filter, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            else:
                annotations['closed_in_period'] = Value(False, output_field=models.BooleanField())

        if 'currently_stalled' in names:
            from django.db.models import Exists
            from bpms.comments.models import CommentModel
            stale_border_datetime = timezone.now() - datetime.timedelta(days=30)
            stale_border_date = stale_border_datetime.date()
            recent_comment_subquery = CommentModel.objects.filter(
                is_active=True,
                related_object_id=OuterRef('pk'),
                created_at__gte=stale_border_datetime,
            )
            recent_execution_subquery = TaskExecutionTimeModel.objects.filter(
                is_active=True,
                task_id=OuterRef('pk'),
                date__gte=stale_border_date,
            )
            has_recent_comment = Exists(recent_comment_subquery)
            has_recent_execution = Exists(recent_execution_subquery)
            annotations['currently_stalled'] = models.Case(
                models.When(
                    status_id__in=not_completed_statuses,
                    then=models.Case(
                        models.When(has_recent_comment, then=Value(False)),
                        models.When(has_recent_execution, then=Value(False)),
                        default=Value(True),
                        output_field=models.BooleanField(),
                    ),
                ),
                default=Value(False),
                output_field=models.BooleanField(),
            )

        if 'root_organization' in names:
            from common.catalogs.models import ContractorRelationModel

            organization_pk_field = cls._meta.get_field('organization').target_field
            if outer_ref_column:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                task_root_subquery = cls.objects.filter(
                    pk=OuterRef(outer_ref_column),
                ).annotate(
                    resolved_root_organization=Coalesce(
                        Subquery(root_organization_subquery),
                        F('organization_id'),
                        output_field=organization_pk_field,
                    )
                ).values('resolved_root_organization')[:1]
                annotations['root_organization'] = Subquery(
                    task_root_subquery,
                    output_field=organization_pk_field,
                )
            else:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                annotations['root_organization'] = Coalesce(
                    Subquery(root_organization_subquery),
                    F('organization_id'),
                    output_field=organization_pk_field,
                )

        if 'task_link' in names:
            base_url = URLS['tasks']
            url_expr = Concat(
                Value(base_url),
                Value('?task='),
                Cast(F('id'), models.CharField())
            )
            # Используем jsonb_build_object для формирования JSON на стороне БД
            annotations['task_link'] = Func(
                Value('repr'), F('counter'),
                Value('url'), url_expr,
                function='jsonb_build_object',
                output_field=models.JSONField()
            )
        if 'ticket_link' in names:
            from django.db.models import Case, CharField, Exists, When
            from help_desk.models import HelpDeskTicketModel

            helpdesk_base_url = URLS['helpdesk_tickets']
            ticket_url_expr = Concat(
                Value(helpdesk_base_url),
                Value('?ticketView='),
                F('reason'),
            )
            ticket_qs = HelpDeskTicketModel.objects.filter(is_active=True).annotate(
                ticket_pk_str=Cast(F('pk'), models.CharField())
            ).filter(
                ticket_pk_str=OuterRef('reason')
            )
            ticket_number_subquery = ticket_qs.values('number')[:1]
            ticket_exists = Exists(ticket_qs)
            annotations['ticket_link'] = Case(
                When(
                    ticket_exists,
                    then=Func(
                        Value('repr'),
                        Subquery(ticket_number_subquery, output_field=CharField()),
                        Value('url'),
                        ticket_url_expr,
                        function='jsonb_build_object',
                        output_field=models.JSONField(),
                    )
                ),
                default=Value(None, output_field=models.JSONField()),
                output_field=models.JSONField(),
            )
        return annotations

    @classmethod
    def apply_report_pandas_aggregates(cls, df, aggregate_fields, pandas_computed_fields, request=None, base_queryset=None):
        import pandas as pd

        created_aliases = []
        closed_aliases = []
        closure_rate_aliases = []
        created_alias_for_rate = None
        closed_alias_for_rate = None

        for aggregate_config in aggregate_fields or []:
            aggregate_name = aggregate_config.get("name")
            if not aggregate_name:
                continue
            aggregate_values = set(aggregate_config.values())
            if aggregate_config.get("sum") == "created_in_period":
                created_aliases.append(aggregate_name)
                if created_alias_for_rate is None:
                    created_alias_for_rate = aggregate_name
            if aggregate_config.get("sum") == "closed_in_period":
                closed_aliases.append(aggregate_name)
                if closed_alias_for_rate is None:
                    closed_alias_for_rate = aggregate_name
            if 'task_closure_rate' in aggregate_values:
                closure_rate_aliases.append(aggregate_name)

        axis_granularity_by_field = {}
        for field_meta in cls.get_report_computed_fields_meta():
            field_name = field_meta.get("name")
            if field_name and field_meta.get("date_axis") is True:
                axis_granularity_by_field[field_name] = field_meta.get("axis_granularity", "day")

        active_axis_field = None
        active_axis_granularity = "day"
        for field_name, axis_granularity in axis_granularity_by_field.items():
            if field_name in df.columns:
                active_axis_field = field_name
                active_axis_granularity = axis_granularity or "day"
                break

        if active_axis_field and (created_aliases or closed_aliases):
            period_from, period_to = cls._extract_report_bounds(
                request,
                [active_axis_field, "report_day", "report_week", "report_month", "report_period", "created_at"],
            )
            if period_from and period_to:
                target_queryset = base_queryset if base_queryset is not None else cls.objects.filter(is_active=True)

                from bpms.tasks.utils import get_cached_statuses
                completed_statuses = get_cached_statuses()[2]

                if active_axis_granularity == "month":
                    created_axis = TruncMonth("created_at")
                    closed_axis = TruncMonth("finished_date")
                elif active_axis_granularity == "week":
                    created_axis = TruncWeek("created_at")
                    closed_axis = TruncWeek("finished_date")
                else:
                    created_axis = TruncDate("created_at")
                    closed_axis = TruncDate("finished_date")

                def normalize_axis_value(value):
                    if value is None:
                        return None
                    if isinstance(value, datetime.datetime):
                        return value.date()
                    if isinstance(value, datetime.date):
                        return value
                    parsed_value = pd.to_datetime(value, errors="coerce")
                    if pd.isna(parsed_value):
                        return None
                    return parsed_value.date()

                created_daily_rows = target_queryset.filter(
                    created_at__date__gte=period_from,
                    created_at__date__lte=period_to,
                ).annotate(
                    report_axis_sql=created_axis
                ).values("report_axis_sql").annotate(cnt=models.Count("pk"))
                created_daily_map = {
                    normalize_axis_value(row["report_axis_sql"]): row["cnt"]
                    for row in created_daily_rows
                }

                closed_daily_rows = target_queryset.filter(
                    finished_date__isnull=False,
                    status_id__in=completed_statuses,
                    finished_date__date__gte=period_from,
                    finished_date__date__lte=period_to,
                ).annotate(
                    report_axis_sql=closed_axis
                ).values("report_axis_sql").annotate(cnt=models.Count("pk"))
                closed_daily_map = {
                    normalize_axis_value(row["report_axis_sql"]): row["cnt"]
                    for row in closed_daily_rows
                }

                report_axis_series = pd.to_datetime(df[active_axis_field], errors="coerce").dt.date
                for created_alias in created_aliases:
                    if created_alias in df.columns:
                        df[created_alias] = report_axis_series.map(created_daily_map).fillna(0).astype(int)
                for closed_alias in closed_aliases:
                    if closed_alias in df.columns:
                        df[closed_alias] = report_axis_series.map(closed_daily_map).fillna(0).astype(int)

        if not closure_rate_aliases:
            return df
        if not created_alias_for_rate or not closed_alias_for_rate:
            for closure_rate_alias in closure_rate_aliases:
                df[closure_rate_alias] = 0
            return df
        if created_alias_for_rate not in df.columns or closed_alias_for_rate not in df.columns:
            for closure_rate_alias in closure_rate_aliases:
                df[closure_rate_alias] = 0
            return df

        created_series = pd.to_numeric(df[created_alias_for_rate], errors='coerce')
        closed_series = pd.to_numeric(df[closed_alias_for_rate], errors='coerce')
        denominator = created_series.where(created_series != 0)
        closure_rate_series = closed_series.divide(denominator).fillna(0).round(4)
        for closure_rate_alias in closure_rate_aliases:
            df[closure_rate_alias] = closure_rate_series
        return df

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                "name": "report_day",
                "type": "DateField",
                "verbose_name": _("Дата отчета"),
                "date_axis": True,
                "axis_granularity": "day",
                "axis_freq": "D",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "created_at",
                    "end_field": "created_at",
                },
            },
            {
                "name": "report_week",
                "type": "DateField",
                "verbose_name": _("Неделя отчета"),
                "date_axis": True,
                "axis_granularity": "week",
                "axis_freq": "W-MON",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "created_at",
                    "end_field": "created_at",
                },
            },
            {
                "name": "report_month",
                "type": "DateField",
                "verbose_name": _("Месяц отчета"),
                "date_axis": True,
                "axis_granularity": "month",
                "axis_freq": "MS",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "created_at",
                    "end_field": "created_at",
                },
            },
            {
                "name": "task_link",
                "type": "CharField",
                "verbose_name": _("Ссылка на задачу"),
                "order_by_field": "counter",
            },
            {
                "name": "ticket_link",
                "type": "CharField",
                "verbose_name": _("Обращение"),
                "order_by_field": "reason",
            },
            {
                "name": "currently_completed",
                "type": "BooleanField",
                "verbose_name": _("Завершенная"),
            },
            {
                "name": "currently_overdue",
                "type": "BooleanField",
                "verbose_name": _("Просроченная"),
            },
            {
                "name": "created_in_period",
                "type": "BooleanField",
                "verbose_name": _("Созданная за период"),
            },
            {
                "name": "closed_in_period",
                "type": "BooleanField",
                "verbose_name": _("Закрытая за период"),
            },
            {
                "name": "task_closure_rate",
                "type": "DecimalField",
                "verbose_name": _("Коэффициент закрытия задач"),
            },
            {
                "name": "currently_stalled",
                "type": "BooleanField",
                "verbose_name": _("Без движения"),
            },
            {
                "name": "root_organization",
                "type": "ForeignKey",
                "related_model": "catalogs.ContractorModel",
                "verbose_name": _("Головная организация"),
            },
        ]

    # Заменено на аннотацию participants_count в целях оптимизации. 25.06.2025
    # @property
    # def participants_count(self):
    #     """
    #     Количество пользователей, занятых в задаче.
    #     """
    #     visors = self.visors.filter(
    #         is_active=True
    #     ).values_list('id', flat=True)
    #     participants = set(
    #         [self.owner_id, self.operator_id] + list(visors)
    #     )
    #     participants_count = ProfileModel.objects.filter(
    #         is_active=True,
    #         id__in=participants
    #     ).count()
    #     return participants_count

    @property
    def frontend_route(self):
        return '/?task=' + str(self.id)  # переопределяем в целевой модели

    # Заменено на Prefetch prefetched_exec_times в целях оптимизации. 25.06.2025
    # @property
    # def last_execution_time(self):
    #     last_execution_time = self.execution_time.filter(
    #         is_active=True
    #     ).order_by('-date').first()
    #     if last_execution_time is not None:
    #         return last_execution_time.work_type.name
    #     else:
    #         return None

    # Заменено на Prefetch prefetched_future_events в целях оптимизации. 25.06.2025
    # @property
    # def nearest_event(self):
    #     calendar = self.event_calendars.first()
    #     if calendar:
    #         events = calendar.events.filter(
    #             is_active=True,
    #             is_finished=False
    #         )
    #         if events:
    #             current_time = timezone.now()
    #             nearest_event = events.annotate(
    #                 time_difference=ExpressionWrapper(
    #                     F('start_at') - current_time,
    #                     output_field=DurationField()
    #                 )
    #             ).filter(
    #                 time_difference__gte=timezone.timedelta(0)
    #             ).order_by(
    #                 'time_difference'
    #             ).first()
    #             return nearest_event
    #     return None

    @property
    def priority_choices_dict(self) -> dict:
        return dict(self.PRIORITY_CHOICES)

    @property
    def milestone_status(self):
        """Текущий статус вехи. Зависит текущей даты и статуса предыдущих задач ЭТОГО ЖЕ УРОВНЯ."""
        if not self.dead_line:
            return 'milestone_planned'  # or some default status

        now = timezone.now()
        # задачи этого же уровня с дедлайном до даты вехи
        tasks = self.get_siblings(include_self=False).filter(
            is_active=True,
            task_type_id='task',
            dead_line__lte=self.dead_line,
        ).only('status', 'dead_line')
        from bpms.tasks.utils import get_tasks_status_count
        tasks_status = get_tasks_status_count(tasks)
        tasks_total = sum(v for k, v in tasks_status.items() if k != 'overdue')
        if tasks_total == 0:
            if now > self.dead_line:
                status = 'milestone_passed'
            else:
                status = 'milestone_planned'
        else:
            if tasks_total == tasks_status['completed']:
                status = 'milestone_passed'
            else:
                if now > self.dead_line:
                    status = 'milestone_overdue'
                else:
                    status = 'milestone_planned'
        return status

    @property
    def stage_status(self):
        """Текущий статус этапа. Зависит текущей даты и статуса его задач ВСЕХ УРОВНЕЙ ВЛОЖЕННОСТИ."""
        if not self.date_start_plan or not self.dead_line:
            return 'stage_planned'
        now = timezone.now()
        tasks = self.get_descendants(include_self=False).filter(
            is_active=True,
            task_type_id='task',
        ).only('status', 'dead_line')
        from bpms.tasks.utils import get_tasks_status_count
        tasks_status = get_tasks_status_count(tasks)
        tasks_total = sum(v for k, v in tasks_status.items() if k != 'overdue')
        if tasks_total == 0:
            if now > self.date_start_plan:
                if now > self.dead_line:
                    status = 'stage_completed'
                else:
                    status = 'stage_open'
            else:
                status = 'stage_planned'
        else:
            if tasks_total == tasks_status['completed']:
                status = 'stage_completed'
            else:
                if now > self.date_start_plan:
                    if now > self.dead_line:
                        status = 'stage_overdue'
                    else:
                        status = 'stage_open'
                else:
                    # Есть хотя бы одна начатая задача?
                    if tasks_total > tasks_status['new']:
                        status = 'stage_open'
                    else:
                        status = 'stage_planned'
        return status

    @property
    def duration_days(self):
        """Продолжительность задачи в днях. Количество суток с округлением в бОльшую сторону."""
        if self.dead_line and self.date_start_plan:
            duration = self.dead_line - self.date_start_plan
            if duration.seconds > 0:
                duration_days = duration.days + 1
            else:
                duration_days = duration.days
        else:
            duration_days = None
        return duration_days

    @property
    def duration_minutes(self):
        """Продолжительность задачи в минутах. Для диаграммы Ганта."""
        if self.date_start_plan and self.dead_line and self.date_start_plan < self.dead_line:
            duration = self.dead_line - self.date_start_plan
            duration_minutes = duration.total_seconds() / 60
        else:
            duration_minutes = None
        return duration_minutes

    @property
    def progress(self):
        """Процент выполнения подзадач задачи."""
        subtasks = self.get_descendants(include_self=False).filter(is_active=True, task_type='task')
        if subtasks.exists():
            from bpms.tasks.utils import get_tasks_status_count
            tasks_status = get_tasks_status_count(subtasks)
            percent = round(tasks_status['completed'] / subtasks.count(), 2)
            return percent
        else:
            return None


class LeadSourceModel(BaseAbstractModel):
    name = common_fields.CustomCharField(
        verbose_name=_('Источник'),
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )

    class Meta:
        verbose_name = _("Источник обращения")
        verbose_name_plural = _("Источники обращения")

    def __str__(self):
        return self.name


class RejectionReasonModel(BaseAbstractModel):
    name = common_fields.CustomCharField(
        verbose_name=_('Причина отказа'),
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )

    class Meta:
        verbose_name = _("Причина отказа")
        verbose_name_plural = _("Причины отказа")

    def __str__(self):
        return self.name


class TaskStatusModel(BaseCatalog, BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'color', 'btn_title', 'progress', 'name', 'code', 'created_at', 'mentions', 'ct', ]
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )
    btn_title = common_fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=31,
        verbose_name=_('Название кнопки'),
    )
    progress = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=False,
        default=0,
        verbose_name=_("Прогресс"),
        validators=(MaxValueValidator(limit_value=100),)
    )

    class Meta:
        verbose_name = _("Статус задачи")
        verbose_name_plural = _("Статусы задач")

    def save(self, *args, **kwargs):
        if self.pk:
            # Сбрасываем кэш у всех типов CachedTaskStatusTypeModelSerializer_, в которых есть этот статус
            task_type_codes = TaskTypeModel.objects.all().values_list('code', flat=True)
            for task_type_code in task_type_codes:
                cache.set('CachedTaskStatusTypeModelSerializer_' + str(task_type_code) + '__' + str(self.code), None)
        super().save(*args, **kwargs)

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort', 'name', 'created_at')

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_order_param(cls):
        return ['sort', 'name', ]

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TaskStatusModelSerializer, TaskStatusModelNotifySerializer
        if action == 'notify':
            return TaskStatusModelNotifySerializer
        return TaskStatusModelSerializer

    @property
    def hex_color(self):
        colors = {
            'geekblue': '#597ef7',
            'purple': '#9254de',
            'orange': '#ffa940',
            'red': '#ff4d4f',
            'green': '#73d13d',
            'pink': '#FFC0CB',
            'cyan': '#36cfc9',
        }
        return colors.get(self.color, '#f5f5f5')


class TaskStatusTypeModel(BaseAbstractModel):
    task_type = common_fields.CustomForeignKey(
        to='tasks.TaskTypeModel',
        to_field='code',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Тип задачи'),
        related_name='task_statuses',
    )
    task_status = common_fields.CustomForeignKey(
        to='tasks.TaskStatusModel',
        to_field='code',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Статус'),
        related_name='task_status_type'
    )
    is_complete = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Завершает'),
    )
    is_open = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Открывает'),
    )
    show_btn = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Показывать кнопку'),
    )
    can_shipment = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Возможность отгрузки заказа'),
    )

    next_status = common_fields.CustomForeignKey(
        to='self',
        null=True,
        blank=True,
        related_name='previous_status_types',
        on_delete=CUSTOM_PROTECT,
    )

    @property
    def depends(self):
        return list(self.depends_statuses.all().values_list('task_status_id', flat=True, ))  # noqa

    def __str__(self):
        return f"{self.task_type} {self.task_status}"

    class Meta:
        verbose_name = _('Статус типа задач')
        verbose_name_plural = _('Статусы типов задач')
        unique_together = (('task_type', 'task_status',),)

    def save(self, *args, **kwargs):
        if self.pk:
            # cache.set('CachedTaskStatusTypeModelSerializer_' + str(self.task_type_id) + '__' + str(self.task_status_id), None)
            # cache.set('task_status_type_model_cache', None)
            cache.delete(
                'CachedTaskStatusTypeModelSerializer_' + str(self.task_type_id) + '__' + str(self.task_status_id))
            cache.delete('task_status_type_model_cache')
        super().save(*args, **kwargs)


class TaskStatusTypeDependsModel(BaseAbstractModel):
    task_status_type = common_fields.CustomForeignKey(
        to='tasks.TaskStatusTypeModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Статус-тип задачи'),
        related_name='depends_statuses'
    )
    task_status = common_fields.CustomForeignKey(
        to='tasks.TaskStatusModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Статус задачи'),
    )

    class Meta:
        verbose_name = _('Зависимость статуса')
        verbose_name_plural = _('Зависимости статусов')
        unique_together = (('task_status_type', 'task_status',),)


class TaskVisor(models.Model):
    class Meta:
        unique_together = (('user', 'task'),)
        verbose_name = _('Наблюдатель задачи')
        verbose_name_plural = _('Наблюдатели задачи')

    log_target_field = 'visors'
    user = models.ForeignKey('users.ProfileModel',
                             null=True,
                             on_delete=CUSTOM_CASCADE, )
    task = models.ForeignKey(TaskModel,
                             null=True,
                             on_delete=CUSTOM_CASCADE,
                             related_name='visor_tasks')

    @classmethod
    def get_label(cls):
        return cls._meta.label

    def __str__(self):
        return f'{self.user.full_name} {self.task.name}'


# m2m_changed.connect(journal_m2m_handler, sender=TaskVisor)


class TaskCooperator(models.Model):
    class Meta:
        unique_together = (('user', 'task'),)
        verbose_name = _('Соисполнитель задачи')
        verbose_name_plural = _('Соисполнители задачи')

    log_target_field = 'сooperators'
    user = models.ForeignKey('users.ProfileModel',
                             null=True,
                             on_delete=CUSTOM_CASCADE, )
    task = models.ForeignKey(TaskModel,
                             null=True,
                             on_delete=CUSTOM_CASCADE,
                             related_name='cooperator_tasks')
    status = common_fields.CustomForeignKey(
        'tasks.TaskStatusModel',
        to_field='code',
        null=False,
        default='new',
        verbose_name=_('Status'),
        on_delete=CUSTOM_PROTECT,
        related_name='cooperator_tasks',
    )

    @classmethod
    def get_label(cls):
        return cls._meta.label

    def __str__(self):
        return f'{self.user.full_name} {self.task.name}'


class TaskPrerequisite(BaseAbstractModel):
    class Meta:
        unique_together = (('task', 'prerequisite'),)
        verbose_name = _('Предшествующая задача')
        verbose_name_plural = _('Предшествующие задачи')

    log_target_field = 'prerequisites'
    task = models.ForeignKey(TaskModel,
                             null=True,
                             on_delete=CUSTOM_CASCADE
                             )
    prerequisite = models.ForeignKey(TaskModel,
                                     null=True,
                                     on_delete=CUSTOM_CASCADE,
                                     related_name='tasks')


# m2m_changed.connect(journal_m2m_handler, sender=TaskPrerequisite)


# m2m_changed.connect(journal_m2m_handler, sender=TaskAttachment)


class TaskOverdue(BaseAbstractModel):
    task = models.ForeignKey(TaskModel,
                             on_delete=CUSTOM_CASCADE,
                             related_name='overdue',
                             verbose_name=_('Просроченная задача'))
    operator = models.ForeignKey('users.ProfileModel',
                                 on_delete=CUSTOM_SET_NULL,
                                 null=True,
                                 related_name='task_overdue',
                                 verbose_name=_('Ответственный'))
    reason = models.ManyToManyField('self',
                                    related_name='reasons',
                                    verbose_name=_('Причина'))
    overdue_date = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name=_('Дата просрочки'),
                                        )

    def __str__(self):
        return '{} {} {}'.format(self.pk, self.task, self.operator)

    class Meta:
        verbose_name = _("Просроченная задача")
        verbose_name_plural = _("Просроченные задачи")


# pre_save.connect(pre_save_handler, sender=Task)
# post_save.connect(journal_save_handler, sender=Task)
# post_delete.connect(journal_delete_handler, sender=Task)


class HistoryOperator(BaseAbstractModel):
    operator = models.ForeignKey('users.ProfileModel',
                                 null=True,
                                 related_name='history_operator_task',
                                 on_delete=CUSTOM_SET_NULL)
    task = models.ForeignKey(TaskModel,
                             null=True,
                             on_delete=CUSTOM_CASCADE)


class TaskWorkTypeModel(BaseCatalog, BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'code', 'name', 'created_at', 'mentions', 'ct', 'icon', 'hex_color',]

    icon = common_fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=50,
        verbose_name=_('Icon')
    )
    hex_color = common_fields.CustomCharField(
        null=False,
        default='#ffffff',
        blank=True,
        max_length=7,
        verbose_name=_('Код цвета'),
        help_text='начинается с #: #ff00ff',
    )

    class Meta:
        verbose_name = _('Type of work in the task')
        verbose_name_plural = _('Types of work in the task')

    @classmethod
    def is_enum(cls):
        return True


class TaskWorkTypeTaskTypeModel(BaseAbstractModel):
    task_type = common_fields.CustomForeignKey(
        to='tasks.TaskTypeModel',
        to_field='code',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Тип задачи'),
        related_name='task_work_types',
    )
    work_type = common_fields.CustomForeignKey(
        to='tasks.TaskWorkTypeModel',
        to_field='code',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Вид работ'),
        related_name='work_type_task_type'
    )

    class Meta:
        verbose_name = _('Вид работ от типа задач')
        verbose_name_plural = _('Виды работ типа задач')
        unique_together = (('task_type', 'work_type',),)


def _get_default_work_type():
    obj, created = TaskWorkTypeModel.objects.get_or_create(
        code='default', defaults={'name': 'По умолчанию', 'is_predefined': True})
    return obj.code


class TaskExecutionTimeModel(BaseModel):
    tps = []
    meta_exclude_fields = ['is_checked', 'measure_unit', 'is_demo', 'created_at', 'event_calendar', 'meeting_section',
                            'mentions', 'ct', 'is_current', ]
    # Переопределение verbose_name для унаследованных полей
    field_verbose_names = {
        'author': _('Автор трудозатрат'),
        'user': _('Сотрудник'),
        }

    tracker = FieldTracker(
        fields=(
            'is_active',
            'date',
            'work_type',
            'hours',
            'description',
            'user_id',
        )
    )
    is_current = common_fields.CustomBooleanField(
        default=False,
    )
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Задача'),
        related_name='execution_time'
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='execution_time',
        verbose_name=_('Пользователь')
    )
    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        to_field='code',
        null=True,
        default='hours',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Единица измерения'),
    )
    date = common_fields.CustomDateField(
        null=False,
        blank=True,
        default=timezone.localdate,
        verbose_name=_('Дата'),
    )
    work_type = common_fields.CustomForeignKey(
        to='tasks.TaskWorkTypeModel',
        to_field='code',
        null=False,
        default=_get_default_work_type,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тип работ'),
    )
    hours = common_fields.CustomDecimalField(
        default=0,
        max_digits=4,
        decimal_places=2,
        verbose_name=_('Затраченные часы'),
        validators=(MinValueValidator(0, message=_('The value can only be positive or 0')),)
    )
    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Продолжительность, сек'),
        help_text='в секундах'
    )
    # Новое поле
    hours_to_client = common_fields.CustomDecimalField(
        default=0,
        max_digits=4,
        decimal_places=2,
        verbose_name=_('Часы в зачёт'),
        validators=(MinValueValidator(0, message=_('The value can only be positive or 0')),)
    )
    description = common_fields.CustomCharField(
        max_length=4096,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание работы'),
    )
    is_checked = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Confirmed')
    )
    is_result = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Не брать в зачёт')
    )
    sprint = common_fields.CustomForeignKey(
        to='tasks.TaskSprintModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='execution_time',
        verbose_name=_('Спринт')
    )
    is_demo = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Демо-данные'
        )
    event_calendar = common_fields.CustomForeignKey(
        to='event_calendar.EventCalendarModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='execution_times',
        verbose_name=_('Событие календаря'),
    )
    meeting_section = common_fields.CustomForeignKey(
        to='meetings.MeetingSectionModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='execution_times',
        verbose_name=_('Сессия собрания'),
    )
    organization_filter = fields.OrganizationTimeExecutionField()
    user_filter = fields.UserTimeExecutionField()
    project_filter = fields.ProjectTimeExecutionField()

    class Meta:
        verbose_name = _('Время на выполнение задачи')
        verbose_name_plural = _('Время на выполнение задачи')

    @classmethod
    def get_table_columns(cls):
        return 'organization_filter', 'user_filter', 'project_filter', 'date'

    def __str__(self):
        return f"{self.task} | {self.author} | {self.hours}"

    @classmethod
    def get_report_annotations(cls, request, requested_computed):
        """
        Возвращает SQL-аннотации для отчётов.
        Вычисляемые поля:
        - report_day/report_week/report_month: даты оси отчета по полю date
        - work_duration: duration (секунды) как IntegerField
        - last_execution_time_date: дата последнего внесения трудозатрат по задаче (MAX(date) по той же задаче)
        - user_project_execution_time_percent: рассчитывается в pandas после SQL (см. apply_report_pandas_aggregates)
        """
        annotations = {}
        names = set(requested_computed or [])
        if 'report_day' in names:
            annotations['report_day'] = TruncDate('date')
        if 'report_week' in names:
            annotations['report_week'] = TruncWeek('date')
        if 'report_month' in names:
            annotations['report_month'] = TruncMonth('date')
        if 'work_duration' in names:
            annotations['work_duration'] = ExpressionWrapper(
                F('duration'),
                output_field=models.IntegerField()
            )
        if 'last_execution_time_date' in names:
            latest_per_task = TaskExecutionTimeModel.objects.filter(
                task_id=OuterRef('task_id'),
                is_active=True
            ).values('task_id').annotate(m=Max('date')).values('m')[:1]
            annotations['last_execution_time_date'] = Subquery(
                latest_per_task,
                output_field=models.DateField()
            )
        return annotations

    @classmethod
    def apply_report_pandas_aggregates(cls, df, aggregate_fields, pandas_computed_fields, request=None, base_queryset=None):
        """
        Применяет pandas-вычисления computed-полей для отчётов.
        """
        import pandas as pd

        if 'user_project_execution_time_percent' in pandas_computed_fields:
            required_groups = {'user', 'task__project'}
            if not required_groups.issubset(set(df.columns)):
                return df

            duration_alias = None
            target_aggregate_names = []
            for aggregate_config in aggregate_fields or []:
                aggregate_name = aggregate_config.get("name")
                if not aggregate_name:
                    continue

                if duration_alias is None and aggregate_config.get("sum") == "work_duration":
                    duration_alias = aggregate_name

                if 'user_project_execution_time_percent' in set(aggregate_config.values()):
                    target_aggregate_names.append(aggregate_name)

            if not duration_alias or not target_aggregate_names or duration_alias not in df.columns:
                return df

            group_user_field = "user"
            numerator = pd.to_numeric(df[duration_alias], errors='coerce')
            denominator = numerator.groupby(df[group_user_field]).transform("sum")
            denominator_nonzero = denominator.where(denominator != 0)
            percent_values = numerator.multiply(100).divide(denominator_nonzero).fillna(0).round(3)
            for aggregate_name in target_aggregate_names:
                df[aggregate_name] = percent_values

        return df

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                "name": "report_day",
                "type": "DateField",
                "verbose_name": _("Дата отчета"),
                "date_axis": True,
                "axis_granularity": "day",
                "axis_freq": "D",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "date",
                    "end_field": "date",
                },
            },
            {
                "name": "report_week",
                "type": "DateField",
                "verbose_name": _("Неделя отчета"),
                "date_axis": True,
                "axis_granularity": "week",
                "axis_freq": "W-MON",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "date",
                    "end_field": "date",
                },
            },
            {
                "name": "report_month",
                "type": "DateField",
                "verbose_name": _("Месяц отчета"),
                "date_axis": True,
                "axis_granularity": "month",
                "axis_freq": "MS",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "date",
                    "end_field": "date",
                },
            },
            {
                "name": "work_duration",
                "type": "DurationField",
                "verbose_name": _("Трудозатраты"),
            },
            {
                "name": "last_execution_time_date",
                "type": "DateField",
                "verbose_name": _("Дата последнего внесения трудозатрат"),
                "order_by_field": "last_execution_time_date",
            },
            {
                "name": "user_project_execution_time_percent",
                "type": "DecimalField",
                "verbose_name": _("Доля занятости, %"),
                "order_by_field": "user_project_execution_time_percent",
            },
        ]

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        related_object_id = self.task.pk
        object_property_id = 'task__execution_time'
        obj_user = self.user
        if obj_user:
            user_full_name = obj_user.full_name
        else:
            user_full_name = ''
        after = f'<li>Вид работы: {self.work_type.name} </li>' \
                f'<li>Описание: {self.description} </li>' \
                f'<li>Автор: {self.author.full_name} \n</li>' \
                f'<li>Пользователь: {user_full_name} \n</li>'\
                f'<li>Потрачено: {self.hours} \n</li>' \
                f'<li>Дата: {self.date.strftime("%d.%m.%Y")}</li>'
        if created:
            change_history_utils.create_add_m2m(
                related_object_id, action_date, object_property_id, after, [self.pk, ]
            )
        elif 'is_active' in changed_fields:
            if not self.is_active:
                change_history_utils.create_delete_m2m(
                    related_object_id, action_date, object_property_id, after, [self.pk, ]
                )
        else:
            before_work_type_id = changed_fields.get('work_type')
            if before_work_type_id:
                before_work_type = TaskWorkTypeModel.objects.get(code=before_work_type_id)
            else:
                before_work_type = self.work_type
            before_description = changed_fields.get('description')
            if not before_description:
                before_description = self.description
            before_hours = changed_fields.get('hours')
            if not before_hours:
                before_hours = self.hours
            before_date = changed_fields.get('date')
            if not before_date:
                before_date = self.date
            before_user_id = changed_fields.get('user_id')
            if before_user_id:
                before_user = ProfileModel.objects.get(pk=before_user_id)
            else:
                before_user = self.user
            before = f"<li>Вид работы: {before_work_type.name}</li>" \
                     f"<li>Описание: {before_description} \n</li>" \
                     f"<li>Автор: {self.author.full_name} \n</li>" \
                     f"<li>Пользователь: {before_user.full_name} \n</li>" \
                     f"<li>Потрачено: {before_hours} \n</li>" \
                     f"<li>Дата: {before_date.strftime('%d.%m.%Y')}</li>"
            change_history_utils.create_update_m2m(
                related_object_id, action_date, object_property_id, before, after, [self.pk, ]
            )

    @classmethod
    def get_queryset(cls, request=None):
        tasks_qs = TaskModel.objects.filter(is_active=True)
        user = request.user.profile
        from .utils import filter_by_permissions
        my_tasks_list = filter_by_permissions(tasks_qs, user)
        my_tasks_ids = list(my_tasks_list.values_list('id', flat=True))
        queryset = cls.objects.filter(
            task__in=my_tasks_ids,
            is_active=True
        )
        return queryset

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TaskExecutionTimeModelCreateSerializer, TaskExecutionTimeModelUpdateSerializer, \
            TaskExecutionTimeModelListSerializer
        if action == 'create':
            return TaskExecutionTimeModelCreateSerializer
        elif action in ['update', 'partial_update']:
            return TaskExecutionTimeModelUpdateSerializer
        else:
            return TaskExecutionTimeModelListSerializer

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if user == self.author:
            return True
        else:
            task = self.task
            if task:
                project = task.project
                if project and project.get_update_permission(request):
                    return True
                else:
                    return False
            else:
                return False

    @property
    def status(self):
        return self.task.status

    def set_sprint(self):
        if not self.sprint:
            task = self.task
            if task:
                sprint = task.sprint
                if sprint:
                    self.sprint = sprint

    def build_register_entry(self, created: bool) -> None:
        if not created:
            AccumulationRegister.objects.filter(registrar_row_uuid=self.pk).delete()
        if self.is_active:
            organization = self.task.project.organization if self.task.project else None
            if not organization and self.user:
                organization = self.user.current_contractor
            AccumulationRegister.objects.create(
                calc_object=self.task.project,
                organization=organization,
                doc_fact=self.task,
                registrar=self.task,
                section_id='work_costs',
                base_measure_unit=self.measure_unit,
                measure_unit=self.measure_unit,
                work_type=self.work_type,
                quantity_fact=self.hours,
                amount_fact=self.hours*10000,  # TODO потом изменить логику расчета amount
                period=timezone.make_aware(
                    datetime.datetime.combine(self.date, datetime.time.min),
                    timezone.utc
                ),
                registrar_row_uuid=self.pk,
                user=self.user,
                description=self.description,
            )
        if self.task and self.task.contract:
            self.task.contract.recalculate_hours_fact()

    def save(self, *args, **kwargs):
        created = self.pk is None
        if self.task and self.task.project and self.task.project.is_finished:
            raise ValidationError(_('Нельзя добавлять трудозатраты в задачи завершённого проекта'))
        hours = self.hours
        duration = self.duration
        if hours and not duration:
            self.duration = int(Decimal(hours) * 3600)
        elif duration and not hours:
            self.hours = (Decimal(duration) / 3600).quantize(Decimal('0.01'), rounding=ROUND_UP)

        self.hours_to_client = self.hours if not self.is_result else 0
        self.set_sprint()
        if self.measure_unit is None:
            self.measure_unit_id = 'hours'
        if not self.user:
            self.user = self.author

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.build_register_entry(created=created)

        target_status = self.work_type.taskstatusworktypeconnectmodel_set.first()
        task = self.task
        if target_status:
            task.status = target_status.status
            task.save()
            from .notifications import notify_about_new_status
            transaction.on_commit(
                lambda: async_task(notify_about_new_status, str(task.pk), task.status.code, str(self.author.pk))
            )
        elif created and task.status_id == 'new' and task.task_type_id == 'task' and self.author == task.operator:
            task.status_id = 'in_work'
            task.save()
            from .notifications import notify_about_new_status
            transaction.on_commit(
                lambda: async_task(notify_about_new_status, str(task.pk), task.status_id, str(self.author.pk))
            )
        else:
            cooperator = task.cooperator_tasks.filter(user_id=self.author.pk).first()
            if cooperator and cooperator.status_id == 'new':
                cooperator.status_id = 'in_work'
                cooperator.save()
                set_task_status = False
                if task.status_id == 'new':
                    task.status_id = 'in_work'
                    task.save()
                    set_task_status = True
                from .notifications import notify_about_new_cooperator_status
                transaction.on_commit(
                    lambda: async_task(
                        notify_about_new_cooperator_status,
                        str(cooperator.pk),
                        'in_work',
                        str(self.author.pk),
                        set_task_status
                    )
                )


class TaskRating(BaseAbstractModel):
    TASK_RATE_CHOICES = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5)
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    user = models.ForeignKey('users.ProfileModel',
                             on_delete=CUSTOM_CASCADE,
                             related_name='task_rating',
                             verbose_name=_('Пользователь'))
    task = models.ForeignKey(TaskModel,
                             on_delete=CUSTOM_CASCADE,
                             verbose_name=_('Задача'))
    rating = models.PositiveIntegerField(choices=TASK_RATE_CHOICES,
                                         blank=False,
                                         null=False,
                                         default=5,
                                         verbose_name=_('Оценка выполнения задачи'))
    comment = models.TextField(null=False,
                               blank=True,
                               default="",
                               max_length=1000)

    class Meta:
        verbose_name = _('Оценка выполнения задачи')
        verbose_name_plural = _('Оценки выполнения задачи')

    def save(self, *args, **kwargs):
        super(TaskRating, self).save(*args, **kwargs)
        if self.is_active is True:
            TaskRating.objects.filter(
                task=self.task,
                user=self.user,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)


class TaskDifficulty(BaseModel):
    criterion = common_fields.CustomForeignKey(
        to='tasks.TaskDifficultyCriterion',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Критерий'),
    )
    score = common_fields.CustomPositiveIntegerField(
        null=False,
        default=1,
        blank=True,
        verbose_name=_('Оценка'),
        validators=(MaxValueValidator(limit_value=10),)
    )
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=False,
        on_delete=CUSTOM_CASCADE,
        blank=False,
        verbose_name=_('Задача'),
        related_name='difficulty'
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TaskDifficultyCreateSerializer, TaskDifficultyListSerializer, \
            TaskDifficultyUpdateSerializer
        if action == 'create':
            return TaskDifficultyCreateSerializer
        elif action in ['update', 'partial_update']:
            return TaskDifficultyUpdateSerializer
        else:
            return TaskDifficultyListSerializer

    class Meta:
        verbose_name = _('Сложность задачи')
        verbose_name_plural = _('Сложность задач')


class TaskDifficultyCriterion(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = _('Критерий сложности задачи')
        verbose_name_plural = _('Критерии сложности задачи')


class UserTaskSort(BaseAbstractModel):
    user = models.ForeignKey('users.ProfileModel',
                             on_delete=CUSTOM_CASCADE,
                             related_name='user_task_sort',
                             verbose_name=_('Пользователь'))
    task = models.ForeignKey(TaskModel,
                             on_delete=CUSTOM_CASCADE,
                             verbose_name=_('Задача'))
    sort = models.FloatField(null=False,
                             blank=True,
                             default=0,
                             verbose_name=_('сортировка'))

    class Meta:
        unique_together = (('user', 'task'),)
        verbose_name = _('Пользовательская сортировка задачи')
        verbose_name_plural = _('Пользовательские сортировки задач')


class TaskBudgetModel(BaseModel):
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Задача'),
        related_name='task_budgets'
    )
    cost_item = common_fields.CustomForeignKey(
        to='tasks.CostItemTaskModel',
        null=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статья затрат'),
        related_name='task_budgets',
        blank=False,
    )
    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        to_field='code',
        null=False,
        default='pieces',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Единица измерения'),
        related_name='task_budgets',
        blank=False,
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Количество'),
        validators=(MinValueValidator(1, message=_('The value can only be positive or 1')),)
    )

    amount = common_fields.CustomDecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        verbose_name=_('Сумма'),
        null=False,
        blank=False,
        validators=(MinValueValidator(0, message=_('The value can only positive or 0')),)
    )

    description = common_fields.CustomCharField(
        max_length=511,
        null=False,
        blank=True,
        default='',
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TaskBudgetModelCreateSerializer, TaskBudgetModelListSerializer, \
            TaskBudgetModelUpdateSerializer
        if action == 'create':
            return TaskBudgetModelCreateSerializer
        elif action in ('update', 'partial_update'):
            return TaskBudgetModelUpdateSerializer
        else:
            return TaskBudgetModelListSerializer

    class Meta:
        verbose_name = _('Затраты')
        verbose_name_plural = _('Затраты')

    def __str__(self):
        return f"{self.task} | {self.author} | {self.cost_item}"


class TaskInterestNeedModel(BaseModel):
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Интерес'),
        related_name='interest_needs'
    )
    goods = common_fields.CustomForeignKey(
        to='catalogs.NomenclatureModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='task_interest_needs',
        verbose_name=_('Товар или услуга')
    )
    name = common_fields.CustomCharField(
        verbose_name=_('Название'),
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    name_short = common_fields.CustomCharField(
        max_length=127,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Краткое наименование'),
    )
    article_number = common_fields.CustomCharField(
        max_length=255,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Артикул')
    )
    base_measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_('Базовая ед. изм.'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_interest_needs_base_measure_unit',
    )
    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_('Единица измерения'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_interest_needs_measure_unit',
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        blank=False,
        default=1,
        verbose_name=_('Количество'),
        validators=(MinValueValidator(0),)
    )
    price = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=False,
        default=0,
        verbose_name=_('Цена/оценка'),
        validators=(MinValueValidator(0),)
    )
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=False,
        default=0,
        verbose_name=_('Сумма'),
        validators=(MinValueValidator(0),)
    )
    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.TaskInterestNeedCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.TaskInterestNeedUpdateSerializer
        return serializers.TaskInterestNeedListSerializer

    def save(self, *args, **kwargs):
        goods = self.goods
        if goods:
            self.name = goods.name
            self.name_short = goods.name_short
            self.article_number = goods.article_number
            self.base_measure_unit = goods.base_measure_unit
            self.measure_unit = goods.base_measure_unit
        self.amount = (self.quantity or Decimal('0')) * (self.price or Decimal('0'))
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Потребность интереса')
        verbose_name_plural = _('Потребности интереса')
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.task} | {self.goods} | {self.quantity}"


class FastNumerator(models.Model):
    pass


class TaskLoadingGoodsModel(BaseModel):
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        blank=True,
        verbose_name=_('Рейс'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_loading_goods',
    )
    goods = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        null=True,
        blank=False,
        verbose_name=_('Товар'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_loading_goods',
    )
    warehouse = common_fields.CustomForeignKey(
        to='catalogs.WarehouseModel',
        null=True,
        blank=True,
        verbose_name=_('Склад'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_loading_goods',
    )
    driver = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        verbose_name=_('Водитель'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_loading_goods',
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        default=0,
        verbose_name=_('Количество'),
    )
    amount_paid = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Оплачено поставщику сумма'),
    )
    number = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.number == 0:
            some_obj = FastNumerator()
            some_obj.save()
            self.number = some_obj.id
            some_obj.delete()

        super(TaskLoadingGoodsModel, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Погрузка товара со склада")
        verbose_name_plural = _("Погрузки товаров со склада")


class CostItemTaskModel(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = _('Статья затрат')
        verbose_name_plural = _('Статьи затрат')

    # @classmethod
    # def get_serializer_class(cls, action=None):
    #     from .serializers import TaskExecutionTimeModelCreateSerializer, TaskExecutionTimeModelUpdateSerializer, \
    #         TaskExecutionTimeModelListSerializer
    #     if action == 'create':
    #         return TaskExecutionTimeModelCreateSerializer
    #     elif action in ['update', 'partial_update']:
    #         return TaskExecutionTimeModelUpdateSerializer
    #     else:
    #         return TaskExecutionTimeModelListSerializer
    # @property
    # def status(self):
    #     return self.task.status
    #
    # def save(self, *args, **kwargs):
    #     super(TaskExecutionTimeModel, self).save(*args, **kwargs)
    #     target_status = self.work_type.taskstatusworktypeconnectmodel_set.first()
    #     if target_status:
    #         self.task.status = target_status.status
    #         self.task.save()
    #         from .notifications import notify_about_new_status
    #         async_task(notify_about_new_status, self, self.task.status.code, self.author)


class TaskDeliveryPointModel(BaseModel):
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        blank=False,
        verbose_name=_('Задача'),
        on_delete=CUSTOM_PROTECT,
        related_name='task_delivery_points',
    )
    delivery_point = common_fields.CustomForeignKey(
        to='catalogs.DeliveryPointModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_("Точка доставки"),
        related_name='task_delivery_points',
        null=True,
        blank=False,
    )
    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        default=1,
        blank=False,
        verbose_name=_('Время доставки'),
    )
    is_start = common_fields.CustomBooleanField(
        default=False,
        null=False,
        verbose_name=_("Стартовая точка")
    )
    need_amount_pay = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Необходимо оплатить за закупку'),
    )
    delivery_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата доставки'),
    )
    front_id = models.UUIDField(null=True, blank=True)

    class Meta:
        verbose_name = _('Точка доставки для задачи')
        verbose_name_plural = _('Точки доставки для задачи')


class TaskDeliveryModel(BaseAbstractModel):
    attachments = models.ManyToManyField(
        'common.File',
        blank=True,
        verbose_name=_('Прикрепленные файлы'),
    )
    owner = models.ForeignKey(
        to='tasks.TaskDeliveryPointModel',
        on_delete=CUSTOM_CASCADE,
        related_name='delivery_table',
        verbose_name=_('Задача'),
        null=True,
        blank=False,
    )
    good = models.ForeignKey('catalogs.GoodsModel', on_delete=CUSTOM_PROTECT, )
    contractor = models.ForeignKey('catalogs.ContractorModel',
                                   on_delete=CUSTOM_PROTECT)
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Стоимость')
    )
    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Количество товаров')
    )
    quantity_success = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Количество принятых товаров')
    )
    success_date = models.DateTimeField(null=True, blank=True)
    comment = models.CharField(max_length=500, default='', blank=True)

    class Meta:
        verbose_name = _('Доставка товара')
        verbose_name_plural = _('Доставка товара')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        owner = self.owner
        if owner and not self.owner.delivery_table.filter(success_date__isnull=True).exists():
            owner.delivery_date = timezone.now()
            owner.save(update_fields=('delivery_date',))


# модели для временных таблиц при формировании списка задач

class TmpSortedTableByPermissionStep1(models.Model):
    task = models.OneToOneField(TaskModel,
                                db_column='task_id',
                                primary_key=True,
                                related_name='tmp_my_task_by_permission_step1',
                                on_delete=CUSTOM_CASCADE)
    tree_id = models.PositiveBigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'task_temporary_table_by_permissions_step1'


class TmpSortedTableByPermission(models.Model):
    task = models.OneToOneField(TaskModel,
                                primary_key=True,
                                related_name='tmp_my_task_by_permission',
                                on_delete=CUSTOM_CASCADE)

    class Meta:
        managed = False
        db_table = 'task_temporary_table_by_permissions'


class TaskPointModel(BaseAbstractModel):
    name = common_fields.CustomCharField(
        verbose_name=_('Название'),
        max_length=255,
        null=False,
        default='',
        blank=True,
        table_info=DefaultTableColumn(width=300)
    )
    lat = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=13,
        db_index=True,
        default=0,
        verbose_name=_('Широта')
    )
    lon = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=13,
        db_index=True,
        default=0,
        verbose_name=_('Долгота')
    )
    address = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Адрес')
    )
    task = common_fields.CustomForeignKey(
        'TaskModel',
        on_delete=CUSTOM_CASCADE,
        null=False,
        verbose_name=_('Задача'),
        related_name='task_points'
    )

    class Meta:
        verbose_name = _('Точка задачи')
        verbose_name_plural = _('Точки задач')

    @classmethod
    def is_enum(cls):
        return True


class TaskPinnedModel(BaseAbstractModel):
    user = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        related_name='pinned_tasks'
    )
    task = common_fields.CustomForeignKey(
        TaskModel,
        on_delete=CUSTOM_CASCADE,
        related_name='pinned_by',
    )

    class Meta:
        verbose_name = 'Закреплённая задача'
        verbose_name_plural = 'Закреплённые задачи'
