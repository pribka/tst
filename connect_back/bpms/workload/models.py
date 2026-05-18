from datetime import time

from django.db import models
from django.utils.translation import gettext_lazy as _

from bpms.tasks import models as t_models
from common import models as c_models
from users import models as u_models

from . import utils

"""Календарь ресурса"""


class WorkScheduleModel(c_models.BaseCatalog, c_models.BaseAbstractCatalog):
    """Рабочий график."""

    profile = models.OneToOneField(
        u_models.ProfileModel,
        on_delete=models.PROTECT,
        related_name='schedule',
        blank=False,
        null=True,
        verbose_name=_('Профиль')
    )
    work_days = models.JSONField(
        default=utils.set_default_work_days,
        verbose_name=_('Рабочие дни')
    )
    start_hour = models.TimeField(
        blank=True,
        null=True,
        default=time(9, 0),
        verbose_name=_('Начало дня')
    )
    end_hour = models.TimeField(
        blank=True,
        null=True,
        default=time(18, 0),
        verbose_name=_('Конец дня')
    )
    break_exist = models.BooleanField(
        blank=True,
        null=True,
        default=True,
        verbose_name=_('Обед')
    )
    break_start = models.TimeField(
        blank=True,
        null=True,
        default=time(13, 0),
        verbose_name=_('Начало обеда')
    )
    break_end = models.TimeField(
        blank=True,
        null=True,
        default=time(14, 0),
        verbose_name=_('Конец обеда')
    )
    color = models.CharField(
        max_length=31,
        null=False,
        blank=True,
        default=u_models._get_default_profile_color,
        verbose_name=_('Цвет в загруженности')
    )

    class Meta:
        verbose_name = _('рабочий график')
        verbose_name_plural = _('Рабочие графики')

    def __str__(self):
        return getattr(self.profile.user, 'full_name')

    @property
    def work_hours(self):
        """Количество рабочих часов."""
        work_time = utils.calc_duration(self.start_hour, self.end_hour)
        if self.break_exist:
            break_time = utils.calc_duration(self.break_start, self.break_end)
            work_time -= break_time
        hours, remainder = divmod(work_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return time(hours, minutes, seconds)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import WorkScheduleSerializer
        serializer_class = WorkScheduleSerializer
        serializer_class.Meta.model = cls
        return serializer_class


class ExceptionTypeModel(c_models.BaseCatalog, c_models.BaseAbstractCatalog):
    """Тип исключения."""

    alias = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        default='',
        verbose_name=_('Алиас')
    )

    class Meta:
        verbose_name = _('тип исключения')
        verbose_name_plural = _('Исключения: типы')

    def __str__(self):
        return getattr(self, 'name')


class ExceptionModel(c_models.BaseCatalog, c_models.BaseAbstractCatalog):
    """Исключения."""

    REPEAT_FREQUENCY_CHOICES = [
        ('weekly', 'Каждую неделю'),
        ('monthly', 'Каждый месяц'),
        ('yearly', 'Каждый год'),
    ]

    profile = models.ForeignKey(
        u_models.ProfileModel,
        on_delete=models.CASCADE,
        related_name='exception_dates',
        blank=False,
        null=True,
        verbose_name=_('Профиль')
    )
    exception_type = models.ForeignKey(
        ExceptionTypeModel,
        to_field='alias',
        on_delete=models.CASCADE,
        related_name='dates',
        blank=False,
        null=True,
        default='',
        verbose_name=_('Тип исключения')
    )
    start_date = models.DateField(
        blank=False,
        null=False,
        verbose_name=_('Начальная дата')
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Конечная дата')
    )
    is_repeatable = models.BooleanField(
        default=False,
        verbose_name=_('Повторяемое')
    )
    repeat_frequency = models.CharField(
        max_length=255,
        blank=True,
        null=False,
        default='',
        choices=REPEAT_FREQUENCY_CHOICES,
        verbose_name=_('Частота повторения')
    )
    repeat_end = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Конец повторения')
    )
    start_hour = models.TimeField(
        blank=True,
        null=True,
        default=time(9, 0),
        verbose_name=_('Время начала')
    )
    end_hour = models.TimeField(
        blank=True,
        null=True,
        default=time(18, 0),
        verbose_name=_('Время конца')
    )

    class Meta:
        verbose_name = _('событие')
        verbose_name_plural = _('Исключения: события')

    def __str__(self):
        return getattr(self, 'name')


class ExceptionDatesModel(c_models.BaseCatalog, c_models.BaseAbstractCatalog):
    """Даты исключений."""

    exception = models.ForeignKey(
        ExceptionModel,
        on_delete=models.CASCADE,
        related_name='dates',
        blank=False,
        null=True,
        default='',
        verbose_name=_('Исключение')
    )
    start_date = models.DateField(
        blank=False,
        null=False,
        verbose_name=_('Начальная дата')
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Конечная дата')
    )

    class Meta:
        verbose_name = _('дата')
        verbose_name_plural = _('Исключения: даты')

    def __str__(self):
        return getattr(self.exception, 'name')


"""Загруженность ресурса"""


class MembersListModel(c_models.BaseCatalog, c_models.BaseAbstractCatalog):
    """Участники."""

    related_object = models.OneToOneField(
        c_models.BaseModel,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        unique=True,
        related_name='members_list',
        verbose_name=_('Связанный объект')
    )
    members = models.JSONField(
        blank=False,
        null=False,
        default=list,
        verbose_name=_('Участники')
    )

    class Meta:
        verbose_name = _('список участников')
        verbose_name_plural = _('Загруженность: списки участников')

    def __str__(self):
        return self.related_object.__str__()


class WorkLoadModel(c_models.BaseCatalog, c_models.BaseAbstractCatalog):
    """Загруженность."""

    date = models.DateField(
        verbose_name=_('Дата')
    )
    profile = models.ForeignKey(
        u_models.ProfileModel,
        on_delete=models.CASCADE,
        related_name='workload',
        blank=False,
        null=True,
        verbose_name=_('Профиль пользователя')
    )
    tasks = models.ManyToManyField(
        t_models.TaskModel,
        related_name='workload',
        blank=True,
        verbose_name=_('Задачи')
    )
    tasks_num = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        default=0,
        verbose_name=_('Кол-во задач')
    )
    total_duration = models.TimeField(
        blank=True,
        null=True,
        default='00:00:00',
        verbose_name=_('Общая загруженность')
    )
    percents = models.FloatField(
        blank=True,
        null=True,
        default=0.0,
        verbose_name=_('Процент загруженности')
    )

    class Meta:
        verbose_name = _('Загруженность дня')
        verbose_name_plural = _('Загруженность дней')
        unique_together = ('date', 'profile')

    def __str__(self):
        return getattr(self.profile.user, 'full_name')

    @property
    def overload(self):
        return self.percents > 100.0


class TaskDurationModel(c_models.BaseModel):
    """Загруженность задачи."""

    task = models.ForeignKey(
        t_models.TaskModel,
        on_delete=models.CASCADE,
        related_name='duration',
        blank=True,
        null=True,
        verbose_name=_('Задача')
    )
    is_distributed = models.BooleanField(
        blank=True,
        null=True,
        default=False,
        verbose_name=_('Распределение')
    )
    durations = models.JSONField(
        blank=True,
        null=True,
        default=list,
        verbose_name=_('Загруженность')
    )

    class Meta:
        verbose_name = _('дневная загруженность задачи')
        verbose_name_plural = _('Дневные загруженности задач')

    def __str__(self):
        return getattr(self.task, 'name', '')
