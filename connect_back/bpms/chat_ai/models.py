from uuid import uuid4
from randomcolor import RandomColor
import json
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task
from django.db.models import Q
from django_cryptography.fields import encrypt
from django.core.exceptions import ValidationError
from rest_framework import exceptions as drf_exceptions

from common import fields
from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from common.validators import validate_text_to_json
from users.models import CustomUser as User
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT
from bpms.meetings.models import PlannedMeetingModel


class AIProvider(BaseCatalog, BaseAbstractCatalog):
    """Провайдер LLM + ключи"""
    api_key = encrypt(models.CharField(max_length=255, blank=True, null=True, default='', verbose_name='API-ключ'))
    base_url = models.URLField(blank=True, default='', verbose_name='Базовый URL API')


class AIChatRoleModel(BaseCatalog, BaseAbstractCatalog):
    """Роли чат-бота"""
    user_message = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name='Cообщение пользователя',
        )
    system_message = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name='Системное сообщение',
        )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Описание роли'
    )
    provider = fields.CustomForeignKey(
        to='chat_ai.AIProvider',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='configs',
        verbose_name='Провайдер LLM'
        )
    model_name = fields.CustomCharField(
        null=False,
        default='',
        blank=False,
        max_length=100,
        verbose_name='Модель'
    )
    temperature = fields.CustomDecimalField(max_digits=3, decimal_places=2, default=0.2)
    max_output_tokens = fields.CustomPositiveIntegerField(default=512)
    top_p = fields.CustomDecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        verbose_name='Top P (nucleus sampling)',
    )
    num_ctx = fields.CustomPositiveIntegerField(
        default=40000,
        verbose_name='Размер контекста (num_ctx)',
        help_text='Размер контекстного окна для Ollama (num_ctx). Используется только для провайдеров типа Ollama. Для OpenAI API не применяется.'
    )


class IntentTypeModel(BaseCatalog, BaseAbstractCatalog):
    """Каталог типов намерений"""
    _metadata = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
        verbose_name='Мета-описание полей',
        help_text='JSON схема с описанием полей для данного типа намерения',
    )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Описание мета-схемы'
    )
    btn_title_create = fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=31,
        verbose_name='Название кнопки создания',
    )
    btn_title_open = fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=31,
        verbose_name='Название кнопки открытия',
    )
    btn_title_delete = fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=31,
        verbose_name='Название кнопки удаления',
    )
    success_message = fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=50,
        verbose_name='Сообщение об успешном выполнении намерения',
    )
    def get_field_meta(self, field_name):
        """Получить мета-описание конкретного поля"""
        return self.metadata.get(field_name, {})

    @property
    def metadata(self):
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        self._metadata = value


class AIMessageStatusModel(BaseCatalog, BaseAbstractCatalog):
    """Каталог статусов обработки сообщений пользователя."""
    pass


class IntentStatusModel(BaseCatalog, BaseAbstractCatalog):
    """Каталог статусов намерений"""
    pass


class TokenUsage(BaseAbstractModel):
    model_name = fields.CustomCharField(max_length=100)
    prompt_tokens = fields.CustomIntegerField()
    completion_tokens = fields.CustomIntegerField()
    consumer = fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=True,
        verbose_name='Потребитель токенов',
        on_delete=CUSTOM_CASCADE,
        related_name='token_usage'
    )

    def __str__(self):
        return f"{self.model_name} [{self.prompt_tokens}/{self.completion_tokens}]"


class AIChatModel(BaseModel):
    chat_author = models.ForeignKey('users.ProfileModel',
                                    null=True,
                                    on_delete=CUSTOM_SET_NULL,
                                    verbose_name=_('Автор')
                                    )
    name = models.CharField(max_length=255,
                            null=False,
                            default='',
                            blank=True)
    last_sent = models.DateTimeField(verbose_name=_('Время последнего сообщения'),
                                     null=False,
                                     default=timezone.now,
                                     blank=True
                                     )

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return
        user = request.user.profile
        return cls.objects.filter(
            is_active=True,
            chat_author=user,
            )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ChatListSerializer
        return ChatListSerializer

    def get_detail_permission(self, request) -> bool:
        return self.author == request.user.profile

    def __str__(self):
        return str(self.pk) + ' ' + str(self.name)


class AIMessageModel(BaseModel):
    chat = fields.CustomForeignKey(AIChatModel,
                             null=True,
                             blank=False,
                             on_delete=CUSTOM_CASCADE,
                             related_name='messages',
                             verbose_name=_('Чат'))
    message_author = fields.CustomForeignKey('users.ProfileModel',
                                       null=True,
                                       on_delete=CUSTOM_PROTECT,
                                       verbose_name=_('Автор'))
    reply_to = fields.CustomForeignKey('self',
                                      null=True,
                                      blank=True,
                                      on_delete=CUSTOM_SET_NULL,
                                      verbose_name=_('Ответ на сообщение'))
    text = models.TextField(null=False,
                            default="",
                            blank=True,
                            verbose_name=_('Текст'),
                            )
    is_bot = fields.CustomBooleanField(
        default=False,
        verbose_name='Сообщение от бота',
        )
    openai_result = models.TextField(blank=True,
                                     null=False,
                                     default='',
                                     verbose_name="Результат анализа контекста через AI")
    intent_data = models.TextField(blank=True,
                                   null=False,
                                   default='',
                                   verbose_name="Результат анализа намерения через AI")
    is_intent = fields.CustomBooleanField(
        default=False,
        verbose_name='Сообщение содержит намерение',
        )
    status = fields.CustomForeignKey(
        to='chat_ai.AIMessageStatusModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        related_name='messages',
        verbose_name='Статус обработки сообщения',
        null=True,
    )


    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.MessageCreateSerializer
        # elif action == 'retrieve':
        #     return serializers.MessageListSerializer
        # elif action in ('update', 'partial_update',):
        #     return serializers.MessageListSerializer
        else:
            return serializers.MessageListSerializer


    def get_detail_permission(self, request) -> bool:
        return self.chat.get_detail_permission(request)


class IntentModel(BaseAbstractModel):
    source_object = fields.CustomForeignKey(
        'common.BaseModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='intents',
        verbose_name='Источник намерения'
    )
    intent_type = fields.CustomForeignKey(
        to='chat_ai.IntentTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        related_name='type_intents',
        verbose_name='Тип намерения'
    )
    raw_data = models.JSONField(
        default=dict,
        verbose_name='Исходные данные от AI',
        )
    resolutions = models.JSONField(
        default=dict,
        verbose_name='Карта сопоставлений',
        )
    resolved_data = models.JSONField(
        default=dict,
        verbose_name='Готовый payload к целевому сериализатору',
        )
    status = fields.CustomForeignKey(
        to='chat_ai.IntentStatusModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        related_name='status_intents',
        verbose_name='Статус намерения',
    )
    related_object = fields.CustomForeignKey(
        'common.BaseModel',
        null=True, blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='object_intents'
    )
    errors = models.JSONField(default=list, blank=True)

    def get_update_permission(self, request):
        """Проверяет права на редактирование намерения в зависимости от типа источника."""
        if not self.source_object:
            return False
        
        source = self.source_object.original_object
        if source._meta.label == "chat_ai.AIMessageModel":
            return source.chat.chat_author_id == request.user.profile.pk
        elif source._meta.label == "meetings.MeetingRecordsModel":
            return source.section.get_detail_permission(request)
        else:
            return source.author_id == request.user.profile.pk

    def set_is_active(self, value: bool, request):
        """Устанавливает is_active с проверкой прав доступа."""
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете удалить это намерение')
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.IntentCreateSerializer
        # elif action == 'retrieve':
        #     return serializers.MessageListSerializer
        # elif action in ('update', 'partial_update',):
        #     return serializers.MessageListSerializer
        else:
            return serializers.IntentListSerializer
