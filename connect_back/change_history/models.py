import json

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from common import fields as common_fields
from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE, CUSTOM_SET_NULL, SOCKETIO_SYSTEM_CHANNEL

from common.redis import socketio_redis


class ChangeHistoryActionModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = 'Действие изменений'
        verbose_name_plural = 'Действия изменений'


class ChangeHistoryObjectPropertyModel(BaseCatalog, BaseAbstractCatalog):
    prefix = common_fields.CustomCharField(
        max_length=63,
        null=False,
        default='',
        blank=True,
        verbose_name='Префикс',
        help_text='Если у одной модели несколько интерпретаций: task, logistic_task, interest, etc.'
    )
    model_label = common_fields.CustomCharField(
        max_length=63,
        null=False,
        default='',
        blank=False,
        verbose_name='Имя модели',
        help_text='имя_модуля.ИмяМодели: tasks.TaskModel'
    )
    is_html = common_fields.CustomBooleanField(
        null=False,
        default=False,
    )
    is_m2m = common_fields.CustomBooleanField(
        null=False,
        default=False,
    )

    class Meta:
        verbose_name = 'Свойство объекта'
        verbose_name_plural = 'Свойства объекта'

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        related_object_id = request.query_params.get('related_object', None)
        if related_object_id:
            try:
                related_object = BaseModel.objects.super_get(related_object_id)
            except BaseModel.DoesNotExist:
                return qs
            if not related_object:
                return qs
            model_label = related_object.get_label()
            prefix = ''
            if model_label == 'tasks.TaskModel':
                prefix = related_object.task_type_id
            qs = qs.filter(model_label=model_label, prefix=prefix)
        return qs.order_by('name', 'created_at')


class ChangeHistoryModel(BaseAbstractModel):
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Связанный объект',
        related_name='related_change_histories',
        null=True,
        blank=False,
    )
    action = common_fields.CustomForeignKey(
        to='change_history.ChangeHistoryActionModel',
        to_field='code',
        on_delete=CUSTOM_SET_NULL,
        verbose_name='Действие',
        related_name='change_histories',
        null=True,
        blank=False,
    )
    object_property = common_fields.CustomForeignKey(
        to='change_history.ChangeHistoryObjectPropertyModel',
        to_field='code',
        on_delete=CUSTOM_SET_NULL,
        verbose_name='Свойство',
        related_name='change_histories',
        null=True,
        blank=True,
    )

    before = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Было'
    )
    after = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Стало'
    )
    before_data = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    after_data = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    action_date = common_fields.CustomDateTimeField(
        null=True,
        blank=False,
        verbose_name='Дата действия'
    )
    description = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Описание',
    )

    class Meta:
        verbose_name = 'История изменения'
        verbose_name_plural = 'История изменений'

    def save(self, *args, **kwargs):
        created = bool(self.pk)
        super().save(*args, **kwargs)
        if created:
            s_data = self.get_serializer_class()(self).data
            data = json.dumps({
                'event': 'send_to_room',
                'event_type': 'create_change_history',
                'room_name': f"detail_{self.related_object.id}",
                'data': s_data,
            }, cls=DjangoJSONEncoder)
            socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ChangeHistoryModelListSerializer, ChangeHistoryModelDetailSerializer
        if action == 'retrieve':
            return ChangeHistoryModelDetailSerializer
        return ChangeHistoryModelListSerializer

    def get_detail_permission(self, request):
        related_object = BaseModel.objects.super_get(pk=self.related_object.pk)
        return related_object.get_detail_permission(request)

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True,).select_related('action', 'object_property').order_by(
            '-action_date', '-created_at',)

    @classmethod
    def get_table_columns(cls):
        return ['author', 'action', 'object_property', 'action_date', 'description']
