import os
import json
import html
from functools import cached_property
from collections import OrderedDict, defaultdict
from telebot.apihelper import ApiTelegramException

from django.db import models
from django.db.models import Count, F, Q
from django.core.exceptions import FieldError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, override
from django.core.serializers.json import DjangoJSONEncoder
from django.template import Template, Context
from django.contrib.postgres.indexes import GinIndex
from django.contrib.contenttypes.models import ContentType

from bs4 import BeautifulSoup

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE, CUSTOM_SET_NULL,SOCKETIO_SYSTEM_CHANNEL, LANGUAGES

from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from common import fields as common_fields
from common import page_config
from common.page_config.filter_fields import ChoiceFilterField
from common.redis import socketio_redis
import html2text
from telegram_bot.base import base_bot
from . import event_types
from common.utils import profile_is_online
from users.models import ProfileModel
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from common.models import TGMessageModel
from bkz3.settings import TG_BOT_NAME

class SMSNotificationModel(BaseModel):
    message = models.TextField(verbose_name='Текстовое сообщение',
                               null=False,
                               default='')
    sent = models.DateTimeField(
        'Дата отправки',
        null=True,
        default=None
    )
    recipient = models.CharField(
        max_length=63,
        null=False,
        blank=False,
        default='',
        verbose_name="Номер телефона"
    )

    class Meta:
        verbose_name = "SMS-сообщение"
        verbose_name_plural = "SMS-сообщения"

    def __str__(self):
        return f"{self.recipient} | {self.created_at} | {self.message}"


class SMSNotificationErrorLog(BaseModel):
    sms_notification = models.ForeignKey(
        SMSNotificationModel,
        on_delete=models.CASCADE,
        null=True,
        editable=False
    )
    phone = models.CharField(
        null=False,
        default='',
        max_length=100,
        editable=False,
    )
    description = models.TextField(null=False,
                                   default='',
                                   verbose_name='Описание ошибки',
                                   editable=False,
                                   )
    text = models.TextField(verbose_name='Текст ошибки',
                            null=False,
                            default='',
                            editable=False,
                            )

    def __str__(self):
        return f"{self.phone} | {self.created_at} | {self.description}"


TEMPLATE_CHOICES = sorted((
    (
        name.replace('.html', ''),
        name.replace('.html', '')
    ) for name in os.listdir(
        os.path.join(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'templates'
            ), 'email_templates'
        )
    )
))


class EmailTemplateModel(BaseCatalog, BaseAbstractCatalog):
    code = models.CharField(verbose_name=_('search code'),
                            choices=TEMPLATE_CHOICES,
                            unique=True,
                            null=False,
                            max_length=100,
                            blank=True)

    html = models.TextField(default='', null=False)
    subject = models.CharField(
        max_length=250,
        verbose_name='Тема',
        null=False,
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Шаблон для оповещения по email'
        verbose_name_plural = 'Шаблоны для оповещения по email'


class EmailNotificationModel(BaseModel):
    template = models.CharField(
        max_length=100,
        verbose_name='Шаблон',
        null=False,
        choices=TEMPLATE_CHOICES,
    )
    subject = models.CharField(
        max_length=250,
        verbose_name='Тема',
        null=False,
        blank=True,
        default=''
    )
    message = models.TextField(verbose_name='Текстовое сообщение',
                               null=False,
                               default='')
    context = models.JSONField()
    sent = models.DateTimeField('Дата отправки', null=True, default=None)

    @property
    def emails(self):
        return list(self.recipients.all().order_by('created_at').values_list('recipient', flat=True))

    class Meta:
        verbose_name = 'Уведомление по email'
        verbose_name_plural = 'Уведомления по email'


class EmailNotificationRecipientModel(BaseAbstractModel):
    email_notification = models.ForeignKey(
        'notifications.EmailNotificationModel',
        null=True,
        verbose_name='Уведомление',
        on_delete=models.CASCADE,
        related_name='recipients',
    )
    recipient = models.EmailField()
    sent = models.DateTimeField(default=None, null=True, verbose_name='Отправлено')

    class Meta:
        verbose_name = 'Адресат email-сообщения'
        verbose_name_plural = 'Адресаты email-сообщения'


class EmailNotificationAttachmentModel(BaseAbstractModel):
    email_notification = models.ForeignKey(
        'notifications.EmailNotificationModel',
        null=True,
        blank=False,
        verbose_name="Уведомление по email",
        related_name='email_attachments',
        on_delete=CUSTOM_CASCADE,
    )
    path = models.CharField(
        null=False,
        default='',
        max_length=255,
        blank=False,
    )

    class Meta:
        verbose_name = "Прикрепленный файл"
        verbose_name_plural = "Прикрепленные файлы"


class EmailNotificationErrorLog(BaseAbstractModel):
    email_notification = models.ForeignKey(EmailNotificationModel,
                                           on_delete=models.CASCADE,
                                           null=True)
    email = models.CharField(null=False,
                             default='',
                             max_length=100)
    description = models.TextField(null=False,
                                   default='',
                                   verbose_name='Описание ошибки')
    text = models.TextField(verbose_name='Текст ошибки',
                            null=False,
                            default='')


class NotificationCategoryModel(BaseCatalog, BaseAbstractCatalog):
    """
    Категории уведомлений для группировки в UI настроек.
    """
    class Meta:
        verbose_name = _('Категория уведомлений')
        verbose_name_plural = _('Категории уведомлений')


class EventTypeModel(BaseCatalog, BaseAbstractCatalog):
    ICON_CHOICES = (
        ('info', _('Информация')),
        ('project', _('Проекты')),
        ('team', _('Группы')),
        ('profile', _('Задачи')),
        ('ellipsis', _('Комментарии')),
        ('video-camera', _('Собрания')),
        ('sync', _('Бизнес процессы')),
        ('environment', _('Логистика')),
        ('file-zip', _('Файл')),
        ('schedule', _('Напоминание')),
        ('calendar', _('Событие')),
    )
    COLOR_CHOICES = (
        ('default', _('Обычное')),
        ('primary', _('Информация')),
        ('success', _('Успех')),
        ('warning', _('Предупреждение')),
        ('error', _('Ошибка')),
    )
    icon = common_fields.CustomCharField(
        null=False,
        blank=False,
        default='circle-info',
        choices=ICON_CHOICES,
        verbose_name=_('Категория'),
        max_length=127,
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'}
    )
    color = common_fields.CustomCharField(
        null=False,
        blank=False,
        default='default',
        choices=COLOR_CHOICES,
        max_length=127,
        verbose_name=_('Вид уведомления'),
        filter_info=ChoiceFilterField(),
        filter_lookup={'value': '__in'}
    )
    template_text = models.TextField(null=False, default='', verbose_name='Текстовый шаблон')
    template_html = models.TextField(null=False, default='', verbose_name='HTML-шаблон')
    url = models.CharField(null=False, default='', max_length=255)
    category = common_fields.CustomForeignKey(
        to='notifications.NotificationCategoryModel',
        to_field='code',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Категория'),
        null=True,
        blank=True,
    )
    show_in_settings = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Показывать в настройках'),
    )
    default_enabled = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Включено по умолчанию'),
    )
    is_mention = common_fields.CustomBooleanField(
        default=False
    )

    class Meta:
        verbose_name = _('Событие уведомлений')
        verbose_name_plural = _('События уведомлений')

    @cached_property
    def icon_choices_dict(self):
        return OrderedDict(self.ICON_CHOICES)

    @cached_property
    def color_choices_dict(self):
        return OrderedDict(self.COLOR_CHOICES)

    @property
    def icon_name(self):
        return self.icon_choices_dict.get(self.icon, '')

    @property
    def color_name(self):
        return self.color_choices_dict.get(self.icon, '')

    @classmethod
    def get_table_columns(cls):
        return 'icon', 'color',

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        from app_info.models import AppInfo
        data = super().get_filter_fields(exclude=exclude, request=request)
        try:
            app_info = AppInfo.objects.get(is_active=True, code='notifications_icon_choices')
        except AppInfo.DoesNotExist:
            pass
        else:
            for each in data:
                if each .get('name', '') in ('icon', 'icon__exclude'):
                    each['widget']['choices'] = app_info.metadata
        return data


def _get_default_event_type():
    obj, created = EventTypeModel.objects.get_or_create(
        code='test_signal',
        defaults={
            'color': event_types.TestSignal.color,
            'icon': event_types.TestSignal.icon,
            'template_html': event_types.TestSignal.template_html,
            'template_text': event_types.TestSignal.template_text,
            'name': event_types.TestSignal.verbose_name,
        }
    )
    return obj.code


class IsReadFakeField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'filter_is_read'
    verbose_name = 'Прочитано'
    default = None
    blank = True

    def to_filter(self, queryset, value):
        try:
            queryset = queryset.filter(is_read=value.get('value'))
        except FieldError:
            queryset = queryset.annotate(
                read_at=F('webnotificationrecipientmodel__read_at')
            ).annotate(
                is_read=F('webnotificationrecipientmodel__is_read')
            ).filter(is_read=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        try:
            queryset = queryset.exclude(is_read=value.get('value'))
        except FieldError:
            queryset = queryset.annotate(
                read_at=F('webnotificationrecipientmodel__read_at')
            ).annotate(
                is_read=F('webnotificationrecipientmodel__is_read')
            ).exclude(is_read=value.get('value'))
        return queryset


class WebNotificationModel(BaseModel):
    recipients = models.ManyToManyField(
        'users.ProfileModel',
        verbose_name=_('Адресаты'),
        related_name='notifications',
        through='notifications.WebNotificationRecipientModel',
        through_fields=('notification', 'recipient')
    )
    sent = models.DateTimeField(default=None, null=True, verbose_name=_('Дата отправки'), blank=True)
    event_type = common_fields.CustomForeignKey(
        to='notifications.EventTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тип события'),
        null=False,
        default=_get_default_event_type,
    )
    data = models.JSONField(encoder=DjangoJSONEncoder)
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Тип объекта',
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='ID объекта для группировки',
    )

    filter_is_read = IsReadFakeField()

    @classmethod
    def get_table_columns(cls):
        return 'filter_is_read', 'created_at', 'event_type__color', 'event_type__icon',

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        result = super().get_filter_fields(exclude, request)
        event_type_filter_fields = EventTypeModel.get_filter_fields(exclude=exclude, request=request)
        for each in event_type_filter_fields:
            each['name'] = f"event_type__{each['name']}"
        return result + event_type_filter_fields

    @property
    def data_with_urls(self):
        data = self.data
        data['urls'] = event_types.URLS
        return data

    @property
    def message(self) -> str:
        """
        Возвращает сообщение, исходя из event_type объекта.
        """
        template = Template(self.event_type.template_html)
        context = Context(self.data_with_urls)
        return template.render(context)

    @property
    def message_text(self) -> str:
        """Возвращает сообщение из template_text."""
        template = Template(self.event_type.template_text)
        context = Context(self.data_with_urls)
        return html.unescape(template.render(context))

    @property
    def url(self) -> str:
        return Template(self.event_type.url).render(Context(self.data_with_urls))

    @property
    def color(self) -> str:
        """
        Возвращает color события.
        """
        return self.event_type.color

    @property
    def icon(self) -> str:
        """
        Возвращает icon события.
        """
        return self.event_type.icon

    @property
    def icon_name(self) -> str:
        """
        Возвращаят имя иконки события.
        """
        return self.event_type.icon_name

    @property
    def title(self):
        return self.icon_name if len(self.icon_name) <= 30 else self.icon_name[:27] + '...'

    @property
    def body(self):
        body = self.message_text
        if len(body) >= 120:
            body = body[:117] + '...'
        return body

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import WebNotificationSerializer
        return WebNotificationSerializer

    def send_messages_to_tg(self) -> None:
        """
        Отправляем уведомление в телеграм (у кого привязан).
        Для ticket_new_for_specialists + наличия data.subj.id добавляем инлайн-кнопку "В работу".
        """
        recipient_with_tg = self.recipients.filter(telegram_id__isnull=False)

        # Условие "шлём всем" (без проверки онлайна)
        event_type_code = getattr(self.event_type, 'code', None)
        send_all = (
                hasattr(self, 'event_type')
                and self.event_type
                and event_type_code in (
                    'ticket_new_for_specialists',
                    'ticket_specialist_assign',
                    'ticket_new_status_specialist',
                )
        )

        # Пытаемся достать subj.id из JSONField self.data
        subj_id = None
        try:
            subj = (self.data or {}).get('subj') if isinstance(self.data, dict) else None
            if isinstance(subj, dict):
                subj_id = subj.get('id')
        except Exception:
            subj_id = None  # на случай неожиданных структур в JSON
            subj = dict()

        # Строим клавиатуру, только если нужный тип события и есть subj.id
        reply_markup = None
        if event_type_code in (
                'ticket_new_for_specialists',
                'ticket_specialist_assign',
                'ticket_new_status_specialist',
        ) and subj_id:
            from welcome_bot import get_costs_button
            reply_markup = InlineKeyboardMarkup()
            if event_type_code == 'ticket_new_for_specialists':
                reply_markup.add(InlineKeyboardButton(
                    text="В работу",
                    callback_data=f"newtick_{subj_id}"
                ))
            elif event_type_code == 'ticket_specialist_assign':
                reply_markup.add(InlineKeyboardButton(
                    text="В работу",
                    callback_data=f"assigntick_{subj_id}"
                ))
            has_specialist = subj.get('specialist') is not None
            if has_specialist:
                costs_button = get_costs_button(subj_id)
                if costs_button:
                    reply_markup.add(costs_button)

        for recipient in recipient_with_tg:
            if send_all or recipient.send_to_tg_always or not recipient.is_online:
                tg_id = recipient.telegram_id

                if tg_id:
                    try:
                        mess = base_bot.send_message(
                            chat_id=tg_id,
                            text=f"{self.message_text}\n{self.url}",
                            reply_markup=reply_markup,  # будет None, если условия не выполнены
                            disable_web_page_preview=True
                        )
                        TGMessageModel.objects.create(
                            message_id=mess.message_id,
                            bot_id=TG_BOT_NAME,
                            is_notify=True,
                            context=json.dumps(self.data, cls=DjangoJSONEncoder, ensure_ascii=False),
                            chat_id=tg_id
                        )
                    except ApiTelegramException as e:
                        if e.error_code == 403:
                            # Пользователь заблокировал бота — очищаем telegram_id
                            ProfileModel.objects.filter(telegram_id=tg_id).update(telegram_id=None)

    def send_message_about_new_notify(self):
        """Сокет о новом веб-уведомлении. При object_id: один запрос count по recipients,
        группировка адресатов с одинаковыми (group_total, group_unread) — меньше publish."""
        serializer_class = self.get_serializer_class(action='list')
        for language in LANGUAGES:
            lang_code = language[0]
            recipient_ids = list(self.recipients.filter(language=lang_code).values_list('pk', flat=True))
            if not recipient_ids:
                continue

            if self.object_id:
                stats_rows = (
                    WebNotificationRecipientModel.objects.filter(
                        recipient_id__in=recipient_ids,
                        notification__object_id=self.object_id,
                        notification__is_active=True,
                    )
                    .values('recipient_id')
                    .annotate(
                        total=Count('pk'),
                        unread=Count('pk', filter=Q(is_read=False)),
                    )
                )
                buckets = defaultdict(list)
                seen = set()
                for row in stats_rows:
                    buckets[(row['total'], row['unread'])].append(row['recipient_id'])
                    seen.add(row['recipient_id'])
                for rid in recipient_ids:
                    if rid not in seen:
                        buckets[(1, 1)].append(rid)
            else:
                buckets = {(1, 1): recipient_ids}

            with override(lang_code):
                for (total, unread), ids in buckets.items():
                    self.group_total = total
                    self.group_unread = unread
                    serialized_notification = serializer_class(
                        self,
                        context={'grouped_mode': True},
                    ).data
                    data = {
                        'event': 'notify',
                        'data': {
                            'message': {
                                'send': timezone.now().isoformat(),
                                'event_type': 'new_notification',
                                'obj': serialized_notification,
                            },
                            'recipients': ids,
                            'title': self.title,
                            'body': self.body,
                            'url': self.url,
                        }
                    }
                    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, json.dumps(data, cls=DjangoJSONEncoder))
                    try:
                        from .push import send_web_push_notifications_for_payload

                        send_web_push_notifications_for_payload(
                            recipients=ids,
                            notification_id=self.id,
                            title=self.title,
                            body=self.body,
                            url=self.url,
                        )
                    except Exception as error:  # noqa: BLE001
                        # Ошибки web-push не должны ломать существующий сокет-поток уведомлений.
                        error_text = f'Outer web-push error: {str(error)}'[:2000]
                        WebPushSubscriptionModel.objects.filter(
                            profile_id__in=ids,
                            is_active=True,
                        ).update(
                            last_error=error_text,
                            last_seen_at=timezone.now(),
                        )

    class Meta:
        verbose_name = _('Уведомление в приложении')
        verbose_name_plural = _('Уведомления в приложении')
        indexes = [GinIndex(fields=['data'], name='notification_data_gin')]


class MobilePushDeviceModel(BaseModel):
    PLATFORM_ANDROID = 'android'
    PLATFORM_IOS = 'ios'
    PLATFORM_CHOICES = (
        (PLATFORM_ANDROID, 'Android'),
        (PLATFORM_IOS, 'iOS'),
    )

    PROVIDER_FCM = 'fcm'
    PROVIDER_APNS_VOIP = 'apns_voip'
    PROVIDER_CHOICES = (
        (PROVIDER_FCM, 'FCM'),
        (PROVIDER_APNS_VOIP, 'APNs VoIP'),
    )

    profile = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        related_name='mobile_push_devices',
        verbose_name='Профиль',
    )
    platform = common_fields.CustomCharField(
        max_length=16,
        choices=PLATFORM_CHOICES,
        default=PLATFORM_ANDROID,
        verbose_name='Платформа',
    )
    push_provider = common_fields.CustomCharField(
        max_length=16,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_FCM,
        verbose_name='Провайдер push',
    )
    token = models.CharField(
        max_length=512,
        unique=True,
        db_index=True,
        verbose_name='Push token',
    )
    device_id = models.CharField(
        max_length=128,
        default='',
        blank=True,
        db_index=True,
        verbose_name='ID устройства',
    )
    app_version = models.CharField(
        max_length=64,
        default='',
        blank=True,
        verbose_name='Версия приложения',
    )
    locale = models.CharField(
        max_length=16,
        default='',
        blank=True,
        verbose_name='Локаль',
    )

    last_seen_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Последняя активность',
    )
    last_error = models.TextField(
        default='',
        blank=True,
        verbose_name='Последняя ошибка',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        verbose_name='Метаданные',
    )

    class Meta:
        verbose_name = 'Мобильное push-устройство'
        verbose_name_plural = 'Мобильные push-устройства'


class WebPushSubscriptionModel(BaseAbstractModel):
    profile = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        related_name='web_push_subscriptions',
        verbose_name='Профиль',
    )
    endpoint = models.TextField(
        default='',
        verbose_name='Push endpoint',
    )
    auth = models.CharField(
        max_length=255,
        db_index=True,
        unique=True,
        verbose_name='Auth key',
    )
    p256dh = models.CharField(
        max_length=512,
        default='',
        verbose_name='P256DH key',
    )
    platform = models.CharField(
        max_length=64,
        default='',
        blank=True,
        verbose_name='Платформа',
    )
    browser = models.CharField(
        max_length=64,
        default='',
        blank=True,
        verbose_name='Браузер',
    )
    user_agent = models.TextField(
        default='',
        blank=True,
        verbose_name='User-Agent',
    )
    last_seen_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Последняя активность',
    )
    last_error = models.TextField(
        default='',
        blank=True,
        verbose_name='Последняя ошибка',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        verbose_name='Метаданные',
    )

    class Meta:
        verbose_name = 'Web push-подписка'
        verbose_name_plural = 'Web push-подписки'


class WebNotificationRecipientModel(BaseAbstractModel):
    recipient = models.ForeignKey(
        'users.ProfileModel',
        on_delete=models.CASCADE,
        verbose_name=_('Адресат'),
        related_name='notification_recipient'
    )
    notification = models.ForeignKey(
        'notifications.WebNotificationModel',
        on_delete=models.CASCADE,
        verbose_name=_('Уведомление'),
    )
    read_at = models.DateTimeField(default=None, null=True, verbose_name=_('Дата прочтения'), blank=True)
    is_read = common_fields.CustomBooleanField(default=False, verbose_name=_("Прочитано"))

    class Meta:
        verbose_name = _('Адресат уведомления')
        verbose_name_plural = _('Адресаты уведомлений')
        unique_together = (('recipient', 'notification'),)

    @classmethod
    def get_table_columns(cls):
        return 'is_read',


class NotificationEventTypePreferenceModel(BaseAbstractModel):
    """
    Пользовательские настройки уведомлений для конкретных типов событий.
    """
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Пользователь'),
        related_name='notification_preferences',
    )
    event_type = common_fields.CustomForeignKey(
        to='notifications.EventTypeModel',
        to_field='code',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Тип события'),
        related_name='user_preferences',
    )
    is_enabled = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Включено'),
    )

    class Meta:
        verbose_name = _('Настройка уведомления')
        verbose_name_plural = _('Настройки уведомлений')
        unique_together = (('user', 'event_type'),)


class NotificationCategoryPreferenceModel(BaseAbstractModel):
    """
    Пользовательские настройки уведомлений для конкретных категорий.
    """
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Пользователь'),
        related_name='notification_category_preferences',
    )
    category = common_fields.CustomForeignKey(
        to='notifications.NotificationCategoryModel',
        to_field='code',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Категория'),
        related_name='user_preferences',
    )
    is_enabled = common_fields.CustomBooleanField(
        default=True,
        verbose_name='Включено',
    )
    sort_order = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Порядок сортировки',
    )

    class Meta:
        verbose_name = _('Настройка категории уведомлений')
        verbose_name_plural = _('Настройки категорий уведомлений')
        unique_together = (('user', 'category'),)
