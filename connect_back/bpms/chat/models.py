from uuid import uuid4
from randomcolor import RandomColor
from bs4 import BeautifulSoup

from django.db import models
from django.db.models import Case, When, Value, BooleanField
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from common import fields
from common.models import BaseModel, BaseAbstractModel, MetadataAbstractModel
from users.models import CustomUser as User
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT
from bpms.meetings.models import PlannedMeetingModel
from bpms.favorites.fields import InFavoritesFilterField


def _get_default_chat_color():
    return RandomColor().generate()[0]


class ChatModel(BaseModel, MetadataAbstractModel):
    meta_exclude_fields = [
        'uid', 'chat_author', 'name', 'last_sent', 'is_public', 'chat_uid', 'dealer',
        'color', 'meeting', 'is_support', 'in_favorites_filter',
        'author', 'created_at', 'ct', 'mentions',
    ]

    uid = models.UUIDField(
        verbose_name=_('Просто uid'),
        editable=False,
        default=uuid4,
        unique=True,
    )
    chat_author = models.ForeignKey('users.ProfileModel',
                                    null=True,
                                    on_delete=CUSTOM_SET_NULL,
                                    verbose_name=_('Автор')
                                    )
    name = models.CharField(max_length=255,
                            null=False,
                            default="",
                            blank=True)
    # Дату последнего сообщения не использовать в фильтрации выборки - это поле
    # носит ознакомительный характер для фронта:
    last_sent = models.DateTimeField(verbose_name=_('Время последнего сообщения'),
                                     null=False,
                                     default=timezone.now,
                                     blank=True
                                     )
    is_public = models.BooleanField(default=False,
                                    verbose_name=_('Групповой чат')
                                    )
    chat_uid = models.UUIDField(unique=True, null=False, default=uuid4, verbose_name=_('Уид чата'))
    dealer = models.OneToOneField('catalogs.ContractorModel',
                                  blank=True,
                                  null=True,
                                  verbose_name=_('Дилер'),
                                  related_name='chat',
                                  on_delete=CUSTOM_PROTECT)
    color = models.CharField(
        max_length=127,
        null=False,
        default=_get_default_chat_color,
        blank=True,
        verbose_name=_("Цвет")
    )
    meeting = models.ForeignKey(PlannedMeetingModel, null=True, blank=True,
                                on_delete=CUSTOM_PROTECT, verbose_name=_('Связанная конфа'))
    is_support = models.BooleanField(
        default=False,
        verbose_name=_('Чат техподдержки')
        )
    in_favorites_filter = InFavoritesFilterField()

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ChatListSerializer, ChatNotifySerializer
        if action == 'notify':
            return ChatNotifySerializer
        return ChatListSerializer

    @classmethod
    def get_table_columns(cls):
        return ['in_favorites_filter', ]

    @classmethod
    def get_queryset(cls, request):
        user = request.user.profile
        return cls.objects.filter(
            member__user=user,
            member__is_active=True,
        ).annotate(
            is_pinned=Case(
                When(member__user=user, member__is_pinned=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        ).order_by('-is_pinned', '-last_sent')

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.get_queryset(request)

    @classmethod
    def get_filtered_select_queryset(cls, text, request=None):
        from common.utils import get_filter_queryset
        return get_filter_queryset(request, cls, cls.get_select_queryset(request))

    @classmethod
    def search_input(cls):
        return True

    @property
    def get_member_ids(self):
        """Возвращает список ID ProfileModel участников чата."""
        return list(
            self.members.filter(is_active=True).values_list('user_id', flat=True)
        )

    def get_detail_permission(self, request) -> bool:
        return self.members.filter(
            is_active=True,
            user=request.user.profile).exists()

    def __str__(self):
        """Генерирует осмысленное название для чата на основе участников или использует имя для публичных чатов."""
        if self.is_public:
            return self.name
        
        members = self.members.filter(is_active=True).select_related('user__user')
        
        names = []
        for member in members:
            names.append(member.user.short_name)
        names.sort()
        
        if len(names) == 1:
            return f"{names[0]}"
        elif len(names) == 2:
            return f"{names[0]} и {names[1]}"
        else:
            return f"{names[0]}, {names[1]} +{len(names) - 2}"


class MessageModel(BaseModel):
    chat = models.ForeignKey(ChatModel,
                             to_field='chat_uid',
                             null=True,
                             blank=False,
                             on_delete=CUSTOM_CASCADE,
                             related_name='messages',
                             verbose_name=_('Чат'))
    message_author = models.ForeignKey('users.ProfileModel',
                                       null=True,
                                       on_delete=CUSTOM_PROTECT,
                                       verbose_name=_('Автор'))
    message_reply = models.ForeignKey('self',
                                      to_field='message_uid',
                                      null=True,
                                      blank=True,
                                      on_delete=CUSTOM_SET_NULL,
                                      verbose_name=_('Ответ на сообщение'))
    message_forwarded = models.ForeignKey(
        'self',
        to_field='message_uid',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Пересылаемое сообщение',),
        related_name='forwarded_messages'
    )
    forwarded = models.BooleanField(default=False,
                                    verbose_name=_('Пересланное сообщение'), )

    text = models.TextField(null=False,
                            default="",
                            blank=False,
                            verbose_name=_('Текст'),
                            max_length=4096,
                            )
    is_system = models.BooleanField(default=False,
                                    verbose_name=_('Системное сообщение'), )
    is_ai_message = models.BooleanField(default=False,
                                    verbose_name=_('Сообщение от ИИ'), )
    is_deleted = models.BooleanField(default=False,
                                     verbose_name=_('Текст сообщения был удален'))
    is_pinned = models.BooleanField(default=False,
                                    verbose_name=_('Закреплено'))
    pin_author = models.ForeignKey('users.ProfileModel',
                                   null=True,
                                   on_delete=CUSTOM_PROTECT,
                                   verbose_name=_('Закрепил'),
                                   blank=True,
                                   related_name='message_pin_authors')
    pin_date = models.DateTimeField(verbose_name=_('Дата закрепления'),
                                    null=True,
                                    blank=True,
                                    )
    message_uid = models.UUIDField(unique=True, null=False, default=uuid4, verbose_name=_('Уид сообщения'))
    created = models.DateTimeField(null=True, blank=False, verbose_name=_('Дата создания'))
    updated = models.DateTimeField(null=True, blank=True, verbose_name=_('Дата изменения'))
    is_updated = models.BooleanField(default=False, verbose_name=_('Изменено'))

    share = models.ForeignKey(to='common.BaseModel', on_delete=CUSTOM_SET_NULL, null=True, blank=True,
                              verbose_name=_('Поделиться'), related_name='message_share')

    def save(self, *args, **kwargs):
        from .utils import send_message_to_tg
        super().save(*args, **kwargs)
        transaction.on_commit(lambda: async_task(send_message_to_tg, str(self.pk)))

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MessageListSerializer, MessageNotifySerializer, MessageChatShareSerializer
        if action == 'notify':
            return MessageNotifySerializer
        elif action == 'chat_share':
            return MessageChatShareSerializer
        return MessageListSerializer

    def get_detail_permission(self, request) -> bool:
        return self.chat.get_detail_permission(request)

    @property
    def clear_text(self) -> str:
        return BeautifulSoup(self.text, 'lxml').get_text(separator=" ").strip()


# class MessageReadingHistorySimple(models.Model):
#     """  Таблица прочитанных сообщений """
#     chat = models.ForeignKey(ChatModel,
#                              to_field='chat_uid',
#                              on_delete=CUSTOM_CASCADE,
#                              related_name='readers',
#                              verbose_name='Чат')
#     profile = models.ForeignKey('users.ProfileModel',
#                                 on_delete=CUSTOM_CASCADE,
#                                 verbose_name='Читатель')
#     last_message_date = models.DateTimeField(verbose_name='Дата последнего прочитанного',
#                                              null=True,
#                                              blank=True,
#                                              )
#
#     class Meta:
#         unique_together = ['chat', 'profile']


class MemberModel(BaseModel):
    class Meta:
        unique_together = (('chat', 'user'),)

    chat = models.ForeignKey(ChatModel,
                             to_field='chat_uid',
                             null=True,
                             blank=False,
                             on_delete=CUSTOM_CASCADE,
                             related_name='members',
                             related_query_name='member'
                             )
    user = models.ForeignKey('users.ProfileModel',
                             null=True,
                             on_delete=CUSTOM_CASCADE,
                             verbose_name=_('Участник'),
                             related_query_name='chat_member',
                             )
    last_message_created = models.DateTimeField(
        null=False,
        default=timezone.now,
        editable=True,
        verbose_name=_('Дата последнего прочитанного сообщения')
    )
    is_moderator = models.BooleanField(
        default=False,
        verbose_name=_("Модератор группового чата")
    )

    member_uid = models.UUIDField(null=False, unique=True, default=uuid4, verbose_name=_('Уид участника'))
    is_pinned = models.BooleanField(
        default=False,
        verbose_name=_('Закрепленный чат')
        )


class SupportMessageTemplateModel(BaseModel):
    title = fields.CustomCharField(
        verbose_name=_('Название'),
        max_length=255,
        null=False,
        default='',
        blank=False
    )
    text = models.TextField(
        verbose_name=_('Текст'),
        max_length=1023,
        null=False,
        default='',
        blank=False
    )
    is_public = fields.CustomBooleanField(
        verbose_name=_('Публичные'),
        null=False,
        default=False,
        blank=True
    )

    class Meta:
        verbose_name = _('Шаблон сообщения техподдержки')
        verbose_name_plural = _('Шаблоны сообщений техподдержки')

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        return serializers.SupportMessageTemplateModelSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(
            models.Q(is_public=True) | models.Q(author=request.user.profile),
            is_active=True
        ).order_by('-created_at',)

    def get_detail_permission(self, request) -> bool:
        return self.is_public or self.author == request.user.profile

    def get_update_permission(self, request) -> bool:
        return self.author == request.user.profile


class ChatSummaryModel(BaseModel):
    """Модель для хранения сформировавшихся саммари чатов"""
    chat = fields.CustomForeignKey(
        ChatModel,
        to_field='chat_uid',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='chat_summary',
        )
    user = fields.CustomForeignKey(
        'users.ProfileModel',
        null=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Автор'),
        related_name='chat_summary',
        )
    start_date = fields.CustomDateField(
        verbose_name=_('Дата начала периода'),
        null=False,
        blank=False,
    )
    end_date = fields.CustomDateField(
        verbose_name=_('Дата конца периода'),
        null=False,
        blank=False,
    )
    summary = models.TextField(
        verbose_name=_('Саммари'),
        null=False,
        blank=False,
        default='',
    )
    
    STATUS_CHOICES = (
        ('pending', _('В процессе')),
        ('completed', _('Готово')),
        ('failed', _('Ошибка')),
    )
    
    status = fields.CustomCharField(
        verbose_name=_('Статус'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        null=False,
        blank=False,
    )
    error_message = models.TextField(
        verbose_name=_('Сообщение об ошибке'),
        null=True,
        blank=True,
        default='',
    )
    started_at = fields.CustomDateTimeField(
        verbose_name=_('Дата начала формирования'),
        null=True,
        blank=True,
    )
    completed_at = fields.CustomDateTimeField(
        verbose_name=_('Дата завершения формирования'),
        null=True,
        blank=True,
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ChatSummarySerializer, ChatSummaryNotifySerializer
        if action == 'notify':
            return ChatSummaryNotifySerializer
        return ChatSummarySerializer

    class Meta:
        verbose_name = _('AI cаммари чата')
        verbose_name_plural = _('AI cаммари чатов')