from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.core.serializers.json import DjangoJSONEncoder

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT, SOCKETIO_SYSTEM_CHANNEL

from common import fields as common_fields
from common.page_config.filter_fields import ChoiceFilterField, ForeignKeyFilterField, ProfileFilterField, \
    CharFilterField
from common.redis import socketio_redis
from common.utils import UUIDEncoder

from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from users.models import CustomUser


class FlowchartModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Блок-схема'
        verbose_name_plural = 'Блок-схемы'

    chart_json_text = models.TextField(null=False,
                                       default='',
                                       blank=True)
    chart_json = models.JSONField(encoder=DjangoJSONEncoder,
                                  null=True,
                                  blank=True)
    project = models.ManyToManyField(
        'workgroups.WorkgroupModel',
        verbose_name=_('Project'),
        related_name='project_flowcharts',
        through='FlowchartProjects',
        blank=True,
    )

    tasks = models.ManyToManyField(
        'tasks.TaskModel',
        related_name='flowcharts',
        through='FlowchartTasks',
        verbose_name='Задачи в схеме',
    )

    #
    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import FlowchartDetailSerializer, FlowchartListSerializer, FlowchartCRUDSerializer
        if action in ['create', 'update', 'partial_update']:
            return FlowchartCRUDSerializer
        elif action == 'retrieve':
            return FlowchartDetailSerializer
        elif action == 'list':
            return FlowchartListSerializer
        else:
            return FlowchartListSerializer

    @classmethod
    def get_table_columns(cls):
        data = []
        data.insert(1, 'name')
        return data

    @classmethod
    def get_data_path(cls):
        return '/flowchart/'


class FlowchartBlockModel(BaseModel):
    class Meta:
        verbose_name = 'Блок блок-схемы'
        verbose_name_plural = 'Блоки блок-схемы'

    chart = common_fields.CustomForeignKey('flowchart.FlowchartModel',
                                           on_delete=CUSTOM_CASCADE,
                                           verbose_name='Блок-схема')


class FlowchartTasks(models.Model):
    class Meta:
        unique_together = (('chart', 'task'),)
        verbose_name = 'Задача в блок-схеме'
        verbose_name_plural = 'Задачи в блок-схеме'

    log_target_field = 'chart'
    chart = models.ForeignKey('flowchart.FlowchartModel',
                              null=True,
                              on_delete=CUSTOM_CASCADE, )
    task = models.ForeignKey('tasks.TaskModel',
                             null=True,
                             on_delete=CUSTOM_CASCADE,
                             related_name='visor_flowcharts')

    def __str__(self):
        return f'{self.chart.name} {self.task.name}'


class FlowchartProjects(models.Model):
    class Meta:
        unique_together = (('chart', 'project'),)

    log_target_fields = 'chart'
    chart = models.ForeignKey('flowchart.FlowchartModel',
                              null=True,
                              on_delete=CUSTOM_CASCADE, )
    project = models.ForeignKey('workgroups.WorkgroupModel',
                                null=True,
                                on_delete=CUSTOM_CASCADE,
                                related_name='flowchart')
