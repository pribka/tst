import uuid
import json
import requests
import pytz

from uuid import uuid4

from django.db import models
from django.db.models.query import Q, F
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from randomcolor import RandomColor
from model_utils import FieldTracker

import common.models

from common.current_profile.middleware import get_current_authenticated_profile
from common.current_profile.db.models import CurrentProfileField
from common.fields import CustomCharField, CustomDateTimeField, CustomBooleanField, CustomForeignKey
from common.redis import socketio_redis

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_SET_NULL, CUSTOM_PROTECT, SOCKETIO_SYSTEM_CHANNEL, TIME_ZONE

from . import fields
from django.core.cache import cache


def _get_default_profile_color():
    return RandomColor().generate()[0]


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        email = username
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    tracker = FieldTracker(
        fields=(
            'first_name',
            'last_name',
            'middle_name',
        )
    )

    meta_exclude_fields = [
        'password', 'last_login', 'is_superuser', 'is_staff', 'is_active', 'date_joined',
        'username', 'email', 'confirm_id', 'confirm_created_at', 'password_generated', 'is_confirmed',
        'gos24_id', 'groups', 'user_permissions', 'created_at', 'mentions', 'ct',
    ]

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
        editable=True,
        default='')
    email = models.EmailField(_('email address'))
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    first_name = models.CharField(_('first name'), max_length=150, blank=False, default='')
    last_name = models.CharField(_('last name'), max_length=150, blank=False, default='')
    middle_name = models.CharField(_('patronymic'), max_length=150, null=False, blank=True, default='')
    confirm_id = models.CharField(_('registration id'), max_length=36, default='', editable=False)
    confirm_created_at = models.DateTimeField(
        _('confirm date'),
        null=True,
        blank=True,
    )
    password_generated = models.BooleanField(verbose_name="Пароль сгенерирован автоматически", default=False)
    is_confirmed = models.BooleanField(_('email is confirmed'), default=False)
    gos24_id = models.IntegerField(_('gos24.kz ID'), null=True, blank=True, )
    objects = CustomUserManager()
    is_loading = False

    def __str__(self):
        return f"{self.email} | {self.phone} | {self.full_name}"

    def get_full_name(self):
        full_name = '%s %s %s' % (self.last_name, self.first_name, self.middle_name)
        return full_name.strip()

    @property
    def full_name(self):
        return self.get_full_name()

    def get_short_name(self):
        short_name = '%s %s' % (self.last_name, self.first_name)
        return short_name.strip()

    @property
    def short_name(self):
        return self.get_short_name()

    @property
    def phone(self):
        return getattr(getattr(self, 'profile', None), 'phone', '')

    def save(self, *args, profile_kwargs=None, **kwargs):
        is_new = False if self.pk else True
        if self.email and not self.username:
            self.username = self.email
        changed_fields = self.tracker.changed()
        super().save(*args, **kwargs)
        if is_new and not self.is_loading:
            if profile_kwargs:
                ProfileModel.objects.create(user=self, **profile_kwargs)
            else:
                ProfileModel.objects.create(user=self)
        if not is_new:
            if {'first_name', 'last_name', 'middle_name'} & changed_fields.keys():
                self.profile.send_socketio_about_update()

    @classmethod
    def forms(self):
        return [
            {'list': [{'default': None}]},
            {'object': [{'default': None}]},
            {'select': [{'default': None}]}
        ]

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import filter_users_by_organizations
        if request:
            user = request.user.profile
        else:
            user = get_current_authenticated_profile()
        profile_qs = ProfileModel.objects.filter(is_active=True)
        profile_qs = filter_users_by_organizations(profile_qs, user)
        profile_ids = profile_qs.values_list('id', flat=True)
        qs = cls.objects.filter(profile__in=profile_ids)
        return qs.order_by(
            'last_name',
            'first_name',
            'middle_name'
        )

    @classmethod
    def get_label(cls) -> str:
        return cls._meta.label

    @classmethod
    def get_order_param(cls):
        return ['last_name', 'first_name', 'middle_name']

    @classmethod
    def get_protected_fields(cls):
        """Возвращает список полей, по которым нельзя фильтровать для защиты персональных данных."""
        return ['email', 'username']


class ProfileTypeModel(common.models.BaseCatalog, common.models.BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Тип профиля'
        verbose_name_plural = 'Типы профиля'

    def __str__(self):
        return self.name


class C1RoleModel(common.models.BaseCatalog):
    has_full_access_to_order_tp = models.BooleanField(
        default=False,
        verbose_name='Полный доступ к данным ТЧ заказа'
    )
    can_set_pay_sum = models.BooleanField(
        default=False,
        verbose_name='Может назначать сумму к оплате'
    )
    has_full_access_to_order_editing = models.BooleanField(
        default=False,
        verbose_name='Полный доступ к редактированию заказа'
    )
    can_create_logistic_task = models.BooleanField(
        default=False,
        verbose_name='Может создавать логистическую задачу',
    )
    me_logistic_manager_only = models.BooleanField(
        default=False,
        verbose_name='Признак только логистического менеджера'
    )
    can_edit_goods_price = models.BooleanField(
        default=False,
        verbose_name='Может изменять цену товаров (отправляется в 1С)'
    )
    is_driver = models.BooleanField(
        default=False,
        verbose_name='Водитель',
        help_text='Проставляем только роли Водитель'
    )

    is_storekeeper = models.BooleanField(
        default=False,
        verbose_name='Кладовщик',
        help_text='Проставляем только роли Кладовщик. Ограничивает интерфейс'
    )

    has_full_access_to_order_list = models.BooleanField(
        default=False,
        verbose_name='Доступ к полному списку заказов',
    )
    send_geodata = models.BooleanField(
        default=False,
        verbose_name='Отправлять геоданные в моб. приложении'
    )
    strict_work_schedule = models.BooleanField(
        default=False,
        verbose_name='Строгое рабочее расписание',
    )
    can_create_workgroups = models.BooleanField(
        default=False,
        verbose_name='Может создавать рабочие групы'
    )
    is_auto_role = models.BooleanField(
        default=False,
        verbose_name='Роль присваивается автоматически вновь создаваемым пользователям'
    )
    warehouse_select_is_available = models.BooleanField(default=False,
                                                        verbose_name='Доступен выбор склада')

    class Meta:
        verbose_name = 'Роль 1с'
        verbose_name_plural = 'Роли 1с'


class ProfileModel(common.models.BaseCatalog):
    tracker = FieldTracker(
        fields=('avatar_id',)
    )
    meta_exclude_fields = [
        'author', 'name', 'temporary_blocked', 'temp_organization', 'avatar', 'header_image',
        'avatar_path', 'default_chat', 'is_auctioneer', 'is_auction_moderator', 'telegram_connect_token', 'telegram_id',
        'is_online', 'phone', 'contact_phone', 'company', 'job_title', 'birthday',
        'is_make_events_in_task_automatically', 'write_me_about_events_in_my_chat', 'is_support', 'about_me',
        'color', 'language', 'profile_type', 'contractors', 'c1_roles', 'is_demo', 'user', 'use_ai_bot', 'created_at',
        'send_to_tg_always', 'mentions', 'ct', 'chat_ai_tooltip', 'current_work', 'hide_read_notifications', 'group_notifications',
        'timezone', 'timezone_auto_detect',
    ]

    current_contractor = models.ForeignKey(
        'catalogs.ContractorModel',
        null=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='profiles_current',
        verbose_name=_('Организация по умолчанию'),
    )
    current_work = models.ForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_SET_NULL,
        null=True,
        blank=True,
        related_name='current_work_profiles',
        verbose_name='Текущая работа',
        help_text='Задача или обращение',
    )
    temporary_blocked = models.BooleanField(default=False,
                                            verbose_name='Заблокирован')
    user = models.OneToOneField('users.CustomUser', on_delete=CUSTOM_PROTECT, related_name='profile',
                                verbose_name=_('User'))
    temp_organization = models.ForeignKey('common.Organization',
                                          null=True,
                                          blank=True,
                                          on_delete=CUSTOM_PROTECT,
                                          related_name='profiles',
                                          verbose_name='Временная организация')
    avatar = models.ForeignKey('common.File',
                               null=True,
                               blank=True,
                               on_delete=CUSTOM_PROTECT,
                               verbose_name='Аватар',
                               related_name='profile_avatars')

    header_image = models.ForeignKey('common.File',
                                     null=True,
                                     blank=True,
                                     on_delete=CUSTOM_PROTECT,
                                     verbose_name='Картинка в шапке',
                                     related_name='profile_header_images')

    avatar_path = models.CharField(max_length=255,
                                   default='',
                                   blank=True)
    # name = None
    default_chat = models.ForeignKey('chat.ChatModel',
                                     null=True,
                                     blank=True,
                                     on_delete=CUSTOM_PROTECT,
                                     related_name='profiles_with_default')
    profile_type = models.ManyToManyField('users.ProfileTypeModel', blank=True,
                                          verbose_name='тип профиля',
                                          related_name='profiles')
    is_auctioneer = models.BooleanField(default=False,
                                        verbose_name='Аукционер')
    is_auction_moderator = models.BooleanField(default=False,
                                               verbose_name='Модератор аукционов')
    contractors = models.ManyToManyField(
        to='catalogs.ContractorModel',
        through='catalogs.ContractorProfileModel',
        through_fields=('user', 'contractor'),
    )
    # telegram_connect_token = models.UUIDField(default=uuid4,
    #                                           unique=True)
    telegram_connect_token = CustomCharField(default=uuid4,
                                             verbose_name='Идентификатор пользователя для Telegramm',
                                             null=False,
                                             blank=True,
                                             max_length=36)
    telegram_id = models.BigIntegerField(null=True,
                                         blank=True,
                                         # unique=True,
                                         verbose_name='ID пользователя в Telegram')
    send_to_tg_always = models.BooleanField(default=False,
                                            verbose_name='Отправлять в ТГ даже когда в онлайн на коннекте')
    last_activity = models.DateTimeField(null=True,
                                         verbose_name='Дата последней активности',
                                         blank=True)
    is_online = models.BooleanField(default=False,
                                    verbose_name='Сейчас онлайн')
    phone = models.CharField(default='', null=False, blank=True, max_length=20)
    contact_phone = models.CharField(default='', null=False, blank=True, max_length=20)
    c1_roles = models.ManyToManyField(C1RoleModel,
                                      verbose_name='Роли 1с',
                                      blank=True)

    company = CustomCharField(default='',
                              verbose_name='Компания',
                              null=False,
                              blank=True,
                              max_length=255)

    job_title = CustomCharField(default='',
                                verbose_name='Должность',
                                null=False,
                                blank=True,
                                max_length=255)
    birthday = models.DateField(null=True,
                                verbose_name='Дата рождения',
                                blank=True)
    is_make_events_in_task_automatically = models.BooleanField(
        default=False,
        verbose_name='Для задач с дедлайном, в которых я участвую, создавать события автоматически'
    )
    write_me_about_events_in_my_chat = models.BooleanField(
        default=False,
        verbose_name='Писать мне в чат о событиях, происходящих в системе'
    )
    is_support = models.BooleanField(
        default=False,
        verbose_name='Сотрудник тех. поддержки',
        help_text='Виден всем пользователям'
    )
    hide_read_notifications = models.BooleanField(
        default=False,
        verbose_name='Скрывать прочитанные уведомления',
    )
    group_notifications = models.BooleanField(
        default=False,
        verbose_name='Группировать уведомления',
    )

    is_not_busy_filter = fields.IsNotBusyFilter()
    full_name_filter = fields.FullNameFilter()
    user_organization_filter = fields.UserOrganizationFilter()

    about_me = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name='Обо мне'
    )

    color = models.CharField(
        max_length=31,
        null=False,
        blank=True,
        default=_get_default_profile_color,
        verbose_name='Цвет'
    )
    LANGUAGE_CHOICES = (
        ('ru', _('Russian')),
        ('kk', _('Kazakh')),
        ('en', _('English')),
    )
    language = CustomCharField(
        choices=LANGUAGE_CHOICES,
        max_length=2,
        null=False,
        default='ru',
        verbose_name='Язык',
    )
    timezone = CustomCharField(
        max_length=64,
        null=False,
        blank=False,
        default='Asia/Almaty',
        verbose_name='Часовой пояс',
    )
    timezone_auto_detect = CustomBooleanField(
        default=True,
        verbose_name='Автоматический часовой пояс',
    )
    is_demo = CustomBooleanField(
        default=False,
        verbose_name='Демо-данные')
    use_ai_bot = CustomBooleanField(
        default=False,
        verbose_name='Использовать AI-бот',
        help_text='Пользователь может использовать AI-бот')
    chat_ai_tooltip = models.JSONField(
        null=False,
        blank=True,
        default=dict,
        verbose_name='Признаки показа подсказок AI-чата',
        help_text='Хранит, какие подсказки о возможностях AI-чата уже были показаны пользователю.',
    )

    profile_filter = fields.ProfileFilterField()

    def send_socketio_about_update(self):
        user = self.user
        from .serializers import AvatarSerializer
        avatar_data = AvatarSerializer(self.avatar).data
        s_data = {
            'id': str(self.pk),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'avatar': avatar_data
        }
        data = json.dumps(
            {
                'event': 'update_profile',
                'data': s_data,
            },
            cls=DjangoJSONEncoder
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)

    def set_default_chat(self) -> None:
        from bpms.chat.models import ChatModel
        if not self.default_chat:
            if self.profile_type.code == 'dealer':
                my_clients = ProfileModel.objects.filter(profile_type='customer')  # TODO фильтровать по моим клиентаам
                chat = ChatModel.objects.get_or_create(defaullt=True, is_active=True, default_chat_owner=self)
            elif self.profile_type.code == 'customer':
                my_dealer = ProfileModel.objects.filter(profile_type='dealer')
                chat = ChatModel.objects.get_or_create(defaullt=True, is_active=True, default_chat_owner=my_dealer)
            else:
                chat = None
            self.default_chat = chat
        # todo доработать  и протестировать, выолнить в миграции

    class Meta:
        verbose_name = _('User profile')
        verbose_name_plural = _('User profiles')

    @property
    def support_chat(self):
        """Возвращает uid чата техподдержки."""
        from bpms.chat.utils import get_support_chat
        return get_support_chat(self)

    @property
    def has_onboarding_tasks(self):
        """Возвращает True, если у пользователя есть хотя бы одна активная обучающая задача"""
        return self.owner_tasks.filter(
            is_onboarding=True,
            is_active=True
        ).exists()

    @property
    def has_demo_data(self):
        """Возвращает True, если хотя бы у одной организации, где пользователь является директором, есть свойство has_demo_data=True"""
        return self.contractor_profile.filter(
            director=True,
            contractor__has_demo_data=True,
            contractor__is_active=True
        ).exists()

    @property
    def last_name(self) -> str:
        return self.user.last_name if self.user else ''

    @property
    def first_name(self) -> str:
        return self.user.first_name if self.user else ''

    @property
    def middle_name(self) -> str:
        return self.user.middle_name if self.user else ''

    @property
    def full_name(self):
        if self.user:
            # c1_roles = list(role.name for role in self.c1_roles.all())
            # if c1_roles:
            #     return f"{self.user.get_full_name()} ({', '.join(c1_roles)})"
            return self.user.get_full_name()
        else:
            return ''

    @property
    def short_name(self):
        return self.user.get_short_name() if self.user else ''

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        page_name = request.query_params.get('page_name', '')
        data = super().get_filter_fields(exclude, request)
        if page_name == 'workplan_calendar':
            data = list(filter(
                lambda x: x.get('name', '') in (
                    'user_organization_filter',
                    'user_organization_filter__exclude',
                    'profile_filter',
                    'profile_filter__exclude',
                ),
                data
            ))
        else:
            data = list(filter(
                lambda x: x.get('name', '') not in (
                    'profile_filter',
                    'profile_filter__exclude',
                ),
                data
            ))
        return data

    @classmethod
    def get_table_columns(cls):
        return 'full_name_filter', 'is_not_busy_filter', 'user_organization_filter', 'profile_filter'

    @classmethod
    def search_input(cls):
        return True

    # # Убрано 30.10.2025 Теперь это только ухудшает релеватность поиска
    # @classmethod
    # def get_search_lookups(cls):
    #     return ['user__last_name__icontains', 'user__first_name__icontains', 'user__middle_name__icontains']

    @classmethod
    def get_order_param(cls):
        return ['user__last_name', 'user__first_name', 'user__middle_name']

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import AppUserSerializer
        return AppUserSerializer

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import filter_users_by_organizations
        if request:
            user = request.user.profile
        else:
            user = get_current_authenticated_profile()
        qs = cls.objects.filter(is_active=True)
        qs = filter_users_by_organizations(qs, user)
        return qs.order_by(
            'user__last_name',
            'user__first_name',
            'user__middle_name'
        )

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.get_queryset(request)

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        from common.utils import get_search_result, filter_queryset_by_search_score

        qs = cls.get_select_queryset(request)
        search_result = get_search_result(cls, text)

        return filter_queryset_by_search_score(qs, search_result, score_threshold_ratio=0.5)

    @classmethod
    def get_snapshot(cls, profile_pk):
        """Короткое стандартизированное описание объекта: id, текстовое представление, изображение.
        Данные будут хранится в намерении AI чат-бота (IntentModel) создать объект."""
        from .serializers import CachedAppUserSerializer, AppUserShortSerializer
        serializer_data = CachedAppUserSerializer().to_representation(profile_pk)
        snapshot = {
            "id": str(profile_pk),
            "repr": serializer_data.get("short_name", ""),
            "image": serializer_data.get("avatar")
        }
        return snapshot

    @property
    def warehouse_select_is_available(self):
        return self.c1_roles.filter(is_active=True, warehouse_select_is_available=True).exists()

    @property
    def has_full_access_to_order_tp(self):
        return self.c1_roles.filter(is_active=True, has_full_access_to_order_tp=True).exists()

    @property
    def can_set_pay_sum(self):
        return self.c1_roles.filter(is_active=True, can_set_pay_sum=True).exists()

    @property
    def has_full_access_to_order_editing(self):
        return self.c1_roles.filter(is_active=True, has_full_access_to_order_editing=True).exists()

    @property
    def me_logistic_manager_only(self):
        return self.c1_roles.filter(is_active=True, me_logistic_manager_only=True).exists()

    @property
    def can_create_logistic_task(self):
        return self.c1_roles.filter(is_active=True, can_create_logistic_task=True).exists()

    @property
    def can_edit_goods_price(self):
        return self.c1_roles.filter(is_active=True, can_edit_goods_price=True).exists()

    @property
    def is_driver(self):
        return self.c1_roles.filter(is_active=True, is_driver=True).exists()

    @property
    def is_storekeeper(self):
        return self.c1_roles.filter(is_active=True, is_storekeeper=True).exists()

    @property
    def has_full_access_to_order_list(self):
        return self.c1_roles.filter(is_active=True, has_full_access_to_order_list=True).exists()

    @property
    def send_geodata(self):
        return self.c1_roles.filter(is_active=True, send_geodata=True).exists()

    @property
    def strict_work_schedule(self):
        return self.c1_roles.filter(is_active=True, strict_work_schedule=True).exists()

    @property
    def can_create_workgroups(self):
        return self.c1_roles.filter(is_active=True, can_create_workgroups=True).exists()

    @property
    def profile_types(self) -> set:
        """Возвращает множество с кодами типов профиля пользователя."""
        return set(self.profile_type.all().values_list('code', flat=True))

    def check_profile_types(self, profile_type_codes: set) -> bool:
        """
        Возвращает True, если есть пересечение множества кодов типов профиля пользователя и
        кодов типов профиля входного параметра profile_type_codes
        """
        return not self.profile_types.isdisjoint(profile_type_codes)

    @property
    def current_work_status_code(self) -> str:
        """
        Возвращает текущий код статуса работы пользователя. Не использовать в списках!
        Если текущего статуса нет, возвращает пустую строку.
        """
        work_status = self.work_status_records.all().order_by('-created_at').first()  # noqa
        if work_status:
            return work_status.status_id
        else:
            return ''

    @property
    def my_organizations(self) -> tuple:
        """Возвращает кортеж id организаций, в которых состоит пользователь."""
        return tuple(self.contractors.filter(is_active=True).values_list('pk', flat=True))

    def get_or_set_current_contractor(self):
        current_contractor = self.current_contractor
        if not current_contractor:
            from common.catalogs.models import ContractorModel
            current_contractor = ContractorModel.objects.filter(
                pk__in=self.my_organizations, is_active=True
            ).order_by('name').first()
            if not current_contractor:
                return None
            else:
                self.current_contractor = current_contractor
                self.save(update_fields=('current_contractor',))
        return current_contractor

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        old_is_support = None
        is_new = self.pk is not None
        if is_new:
            old_instance = ProfileModel.objects.get(pk=self.pk)
            old_is_support = old_instance.is_support
            cache.set('CachedAppUserSerializer_' + str(self.pk), None)
            cache.set('CachedAppUserPreviewSerializer_' + str(self.pk), None)
        changed_fields = self.tracker.changed()
        super().save(*args, **kwargs)

        # Обрабатываем изменение is_support
        if old_is_support is not None and old_is_support != self.is_support:
            from django.db import transaction
            from .utils import handle_is_support_change
            transaction.on_commit(lambda: handle_is_support_change(self.pk, old_is_support, self.is_support))

        # Обновляем название чата техподдержки
        try:
            support_chat_uid = self.support_chat
            if support_chat_uid:
                from bpms.chat.models import ChatModel
                chat = ChatModel.objects.get(chat_uid=support_chat_uid)
                chat.name = f'Техподдержка {self.full_name}'
                chat.save(update_fields=('name',))
        except Exception:
            pass

        avatar = self.avatar
        if avatar:
            avatar.copy_to_avatar_path()
        header_image = self.header_image
        if header_image:
            header_image.copy_to_avatar_path()
        if not is_new and 'avatar_id' in changed_fields:
            self.send_socketio_about_update()


class ProfileModelOuterID(common.models.BaseModel):
    profile = models.ForeignKey(ProfileModel,
                                on_delete=CUSTOM_CASCADE,
                                related_name='external_ids')
    outer_id = models.CharField(default='',
                                blank=False,
                                max_length=255)

    @property
    def email(self) -> str:
        """Возвращает множество с кодами типов профиля пользователя."""
        return self.profile.user.email


class ProfileModelOuterLeadID(common.models.BaseModel):
    profile = models.ForeignKey(ProfileModel,
                                on_delete=CUSTOM_CASCADE,
                                )
    outer_id = models.CharField(default='',
                                blank=False,
                                max_length=255)


class MobileTokenModel(common.models.BaseModel):
    user = models.ForeignKey(
        CustomUser,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Пользователь',
    )
    token = models.CharField(default=uuid4, max_length=36)


class ResetPasswordModel(common.models.BaseModel):
    user = models.ForeignKey(
        CustomUser,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Пользователь',
    )
    uuid = models.UUIDField(
        default=uuid4,
        verbose_name='UUID',
    )
    changed = models.BooleanField(
        default=False,
        verbose_name='Изменен',
    )

    class Meta:
        verbose_name = 'Восстановление пароля'
        verbose_name_plural = 'Восстановления пароля'


class InviteModel(models.Model):
    author = CurrentProfileField(editable=False, verbose_name=_('Author'))
    contractor = models.ForeignKey(
        'catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name="Организация",
    )
    token = models.CharField(
        max_length=36,
        verbose_name="Токен",
        blank=False,
        null=False,
        default=uuid.uuid4,
        unique=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date of creation'),
    )
    deactivate_at = models.DateTimeField(
        verbose_name="Деактивировать в",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Active'),
    )
    workgroup = models.ForeignKey(
        to="workgroups.WorkgroupModel",
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name="Рабочая группа",
        related_name="invites",
    )
    is_create_new_contractor = models.BooleanField(
        default=False,
        verbose_name="Создать новую организацию",
        help_text="Если включено — при активации инвайта будет создана новая организация. "
                  "Если выключено — пользователь присоединится к существующей организации."
    )

    class Meta:
        verbose_name = "Приглашение"
        verbose_name_plural = "Приглашения"

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created:
            # Новый инвайт деактивирует предыдущие инвайты организации:
            contractor = self.contractor
            if contractor:
                self.__class__.objects.filter(
                    is_active=True,
                    contractor=contractor,
                    workgroup=self.workgroup,
                    is_create_new_contractor=self.is_create_new_contractor,
                ).exclude(pk=self.pk).update(is_active=False)
            else:
                self.__class__.objects.filter(
                    is_active=True,
                    contractor__isnull=True,
                    author=self.author
                ).exclude(pk=self.pk).update(is_active=False)


class EmailInviteModel(models.Model):
    author = CurrentProfileField(editable=False, verbose_name=_('Author'))
    contractor = models.ForeignKey(
        'catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name="Организация",
    )
    token = models.CharField(
        max_length=36,
        verbose_name="Токен",
        blank=False,
        null=False,
        default=uuid.uuid4,
        unique=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date of creation'),
    )
    deactivate_at = models.DateTimeField(
        verbose_name="Деактивировать в",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Active'),
    )
    email = models.EmailField()
    workgroup = models.ForeignKey(
        to="workgroups.WorkgroupModel",
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name="Рабочая группа",
        related_name="email_invites",
    )
    is_sent = models.BooleanField(
        default=False,
        verbose_name="Отправлено",
    )
    is_accepted = models.BooleanField(
        default=False,
        verbose_name="Принято",
    )
    accepted_user = models.ForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name="Принято пользователем",
        editable=False,
        related_name="email_invites"
    )
    is_create_new_contractor = models.BooleanField(
        default=False,
        verbose_name="Создать новую организацию",
        help_text="Если включено — при активации инвайта будет создана новая организация. "
                  "Если выключено — пользователь присоединится к существующей организации."
    )

    class Meta:
        verbose_name = "Приглашение"
        verbose_name_plural = "Приглашения"

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created:
            # Новый инвайт деактивирует предыдущие инвайты организации для того же емейла:
            self.__class__.objects.filter(
                is_active=True,
                contractor=self.contractor,
                email=self.email,
            ).exclude(pk=self.pk).update(is_active=False)


class GoogleTokenModel(common.models.BaseModel):
    class Meta:
        verbose_name = 'Токен Google'
        verbose_name_plural = 'Токены Google'

    """
    Модель хранения токенов от Google.
    По рекомендации Google токены нужно хранить в защищенном виде (например, в зашифрованном виде или под паролем).
    И не передавать токены открытым текстом.
    https://developers.google.com/identity/protocols/oauth2/resources/best-practices?hl=en

    Делаю ForeignKey на профиль из расчета, что может быть несколько разных приложений, которым пользователь дал доступ.
    
    
    Касательно устройства схожей таблицы в 1С:Управление небольшой фирмой
    РегистрыСведений.СеансовыеДанныеGoogle
    Измерения
    Пользователь - СправочникСсылка.Пользователи
    Область доступа - ПеречислениеСсылка.ОбластиДоступаGoogle
    УчетнаяЗаписьЭлектроннойПочты - СправочникСсылка.УчетныеЗаписиЭлектроннойПочты
    
    Ресурсы
    access_token строка 0
    token_type строка 0
    refresh_token строка 0
    disabled булево
    
    
    В целом, "магия" OAuth достигается использованием HTTP Redirections (https://datatracker.ietf.org/doc/html/rfc6749#section-1.7).
    То есть сервер говорит браузеру на какую страницу перейти.
    
    Что почитать по теме Google OAuth:
    Глава OAuth 2.0 flows - Common steps и When using the auth code flow
    https://developers.google.com/identity/oauth2/web/guides/how-user-authz-works

    Фронтовая часть.
    Импорт нужной библиотеки https://developers.google.com/identity/oauth2/web/guides/migration-to-gis#libraries_and_modules
    GIS Popup UX - https://developers.google.com/identity/oauth2/web/guides/migration-to-gis#the_new_way_2
    Как обрабатывать ошибки: https://developers.google.com/identity/oauth2/web/guides/error?hl=en

    Серверная часть
    Начиная с 4 шага - https://developers.google.com/identity/protocols/oauth2/web-server#handlingresponse
    Complete example (HTTP/REST) https://developers.google.com/identity/protocols/oauth2/web-server#example
    
    Дополнительно:
    1C Управление небольшой фирмой для выгрузки событий в Google использует https://www.googleapis.com/batch/calendar/v3
    Этот урл позволяет выгружать события пачками. 
    Более подробно: Batching Requests - https://developers.google.com/classroom/best-practices/batch

    Для локальной разработки в Google Console нужно указывать адреса localhost, например:
    Authorized JavaScript origins
    http://localhost:8085

    Authorized redirect URIs (не думаю, что пригодится для сценария Popup, но может пригодится для сценария redirect)
    http://localhost:8085/calendar
    И сама разработка должна вестись с localhost - фронтэнд и бекенд, если используется http.
    Google Console жаловалась на непубличный домен (localhost исключение).
    P.S. разрабатывать на https не пробовал, поэтому не могу сказать на что пожалуется Google Console.


    Реализация Google при получении authorization_code несколько отличается от спецификации
    (https://datatracker.ietf.org/doc/html/rfc6749#section-4.1).
    Из спецификации можно сделать вывод, что при использовании сценария с Popup, фронтенд должен отправлять redirect_uri,
    но этот параметр игнорируется (https://developers.google.com/identity/oauth2/web/reference/js-reference#CodeClientConfig).

    В последующем когда бекенд пытается обменять authorization_code на token, выводится ошибка
    redirect_uri_mismatch (https://developers.google.com/identity/protocols/oauth2/web-server#authorization-errors-redirect-uri-mismatch)
    несмотря на то, что при запросе отправляемый бекендом redirect_uri содержится в Authorized redirect URIs.

    В ходе разработки выяснилось, что если использовать Popup, то при отправке бекендом redirect_uri во время обменя authorization_code на token,
    нужно указывать origin, например:
    {  ...
      'redirect_uri': http://localhost:8085 # Это можно увидеть в строке браузера при переходе на страницу сайта.
      ...
    }

    Судя по документации, при получении от пользователя дополнительных разрешений для приложения, будет выдан новый токен,
    который включает все предыдущие разрешения и новое, но нужно отправлять предыдущие (granted scopes) c новым scope.
    (https://developers.google.com/identity/protocols/oauth2/web-server?hl=en#incrementalAuth)
    
    
    Пример запроса axios на Google API с использованием полученного токена.
        // После обмена authorization_code на токен, с Django сервера вернется текст с access_token и token_type, который нужно преобразовать в словарь.
        async handleDjangoResponse(response){ // response в данном примере это XMLHttpRequest.responseText  
            let parsedResponse = JSON.parse(response)
            const headers = {
                // Google рекомендует передавать токен в заголовке Authorization (https://developers.google.com/identity/protocols/oauth2?hl=en#4.-send-the-access-token-to-an-api.)
               'Authorization': `${parsedResponse.token_type} ${parsedResponse.access_token}`,
            }
            let resp = await this.$http.get('https://www.googleapis.com/calendar/v3/users/me/calendarList',
                {
                    headers:headers,
                    'withCredentials': false
                }
            )
        },
        
    Необходимо обратить внимание на параметр withCredentials. В настройках проекта он установлен в значение true (src/config/axios.js)
    
    Для совершения запроса библиотека axios использует XMLHttpRequest (node_modules/axios/lib/adapters/xhr.js).
    Но было неясно почему при использовании обычного XMLHttpRequest ответ с Google API приходил, 
    а при использовании axios выходила ошибка:
        Access to XMLHttpRequest at 'https://www.googleapis.com/calendar/v3/users/me/calendarList' 
        from origin 'http://localhost:8085' has been blocked by CORS policy: 
        Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
    
    При сравнении в console.log объекта XMLHttpRequest в axios и объекта XMLHttpRequest, созданного без axios, 
    первое, что бросилось в глаза, это значение withCredentials.
    
    Дело в том, что если withCredentials в значении true, axios добавляет в запрос заголовок X-CSRFToken, 
    значение которого берет из cookie:
        Accept 
        Accept-Language 
        Authorization 
        X-CSRFToken 
        
    Когда передается параметр 'withCredentials': false, настройка перезаписывается, и тогда заголовки получаются следующие:
        Accept 
        Accept-Language 
        Authorization 
    
    То есть, суда по всему, в Google отправлялся кастомный заголовок со значением, которое создал Django сервер.
    P.S. Чтобы посмотреть заголовки, нужно в библиотеке axios в файле node_modules/axios/lib/adapters/xhr.js поставить console.log(requestHeaders).
         
    """
    profile = models.ForeignKey(ProfileModel,
                                on_delete=CUSTOM_CASCADE,
                                related_name='google_tokens')

    access_token = models.TextField(
        default='',
        blank=True,
        verbose_name='access_token'
    )
    token_type = models.TextField(
        default='',
        blank=True,
        verbose_name='token_type'
    )
    refresh_token = models.TextField(
        default='',
        blank=True,
        verbose_name='refresh_token'
    )
    disabled = models.BooleanField(
        default=False,
        verbose_name='disabled'
    )
    expires_at = CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Истечение срока использование токена'
    )
    scope = models.TextField(
        default='',
        blank=True,
        verbose_name='scope'
    )
    oauth_client = models.ForeignKey(
        'users.GoogleOAuthClientIDsModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name='oauth_client',
        related_name='google_oauth_client_tokens'
    )

    @staticmethod
    def get_token_for_web_client(profile):
        google_token = GoogleTokenModel.objects.filter(
            profile=profile,
            oauth_client__name=GoogleOAuthClientIDsModel.WEB_CLIENT).first()
        return google_token

    def get_params_to_refresh_token(self):
        client_info = json.loads(self.oauth_client.client_info)
        client_info = client_info.get("web")
        client_id = client_info.get('client_id')
        client_secret = client_info.get('client_secret')
        refresh_token = self.refresh_token
        # params = f'?client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token&refresh_token={refresh_token}'
        result = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        return result

    @staticmethod
    def prepare_token_data_for_saving(token_data):
        # django_time_zone = getattr(settings, 'TIME_ZONE', 'Asia/Almaty')
        # tz = pytz.timezone(django_time_zone)
        expires_at = timezone.now() + timezone.timedelta(seconds=token_data['expires_in'])
        # expires_at = expires_at.replace(tzinfo=tz)
        # expires_at = tz.localize(expires_at)
        data = {
            'access_token': token_data['access_token'],
            'token_type': token_data['token_type'],
            'expires_at': expires_at,
            'scope': token_data['scope']
        }
        if token_data.get('refresh_token'):
            data['refresh_token'] = token_data['refresh_token']
        return data

    @staticmethod
    def update_google_access_token(google_token=None, profile=None):
        """
        Параметр google_token - объект типа GoogleTokenModel
        """

        # https://oauth2.googleapis.com/token
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        url = 'https://oauth2.googleapis.com/token'
        assert google_token or profile, 'Нужен профиль или запись из GoogleTokenModel'

        if google_token:
            params = google_token.get_params_to_refresh_token()
            r = requests.post(url, headers=headers, params=params)
            if r.status_code == 200:
                google_token.parse_content_and_update_token(r.content)
                return google_token
            else:
                # TODO посмотреть какие коды еще могут вернуться
                print(r.status_code)
        else:
            # TODO проверить работу
            google_token = GoogleTokenModel.get_token_for_web_client(profile)
            params = google_token.get_params_to_refresh_token()
            r = requests.post(url, headers=headers, params=params)
            if r.status_code == 200:
                google_token.parse_content_and_update_token(r.content)
                return google_token
            else:
                print(r.status_code)

    def parse_content_and_update_token(self, content):
        """
        Обработчик ответа от Google с новым токеном.
        """
        parsed_content = json.loads(content)
        data = GoogleTokenModel.prepare_token_data_for_saving(parsed_content)
        self.update_token_data(data)

    @staticmethod
    def parse_event_date_time(event):
        """
        Google может вернуть либо date либо dateTime
        https://developers.google.com/calendar/api/v3/reference/events
        """
        start = event.get('start')
        end = event.get('end')

        start_date = start.get('date', None)
        start_datetime = start.get('dateTime', None)
        end_date = end.get('date', None)
        end_datetime = end.get('dateTime', None)

        start_datetime_tz = start.get('timeZone', None)
        end_datetime_tz = start.get('timeZone', None)

        django_time_zone = getattr(settings, 'TIME_ZONE', 'Asia/Almaty')
        tz = pytz.timezone(django_time_zone)

        parsed_start = None
        parsed_end = None
        if start_date:
            parsed_start = parse_date(start_date)
            # parsed_start = datetime.combine(parsed_start, datetime.min.time())
            # parsed_start = tz.localize(parsed_start)
        if end_date:
            parsed_end = parse_date(end_date)
            # parsed_end = datetime.combine(parsed_end, datetime.min.time())
            # parsed_end = tz.localize(parsed_end)

        if start_datetime:
            parsed_start = parse_datetime(start_datetime)
        if end_datetime:
            parsed_end = parse_datetime(end_datetime)

        return parsed_start, parsed_end

    def update_token_data(self, data):
        for (key, value) in data.items():
            setattr(self, key, value)
        self.save()


class GoogleOAuthClientIDsModel(common.models.BaseCatalog, common.models.BaseAbstractCatalog):
    """
    Для хранения OAuth 2.0 Client IDs. Смотреть в Google Console - Credentials - OAuth 2.0 Client IDs.

    """

    class Meta:
        verbose_name = 'Google OAuth 2.0 Client ID'
        verbose_name_plural = 'Google OAuth 2.0 Client IDs'

    # Пока не вижу потребности хранить больше одной записи по каждому виду клиента (Desktop, Mobile, Web)
    WEB_CLIENT = 'web_client'

    client_info = models.TextField(
        null=False,
        blank=True,
        default="",
        verbose_name="OAuth Client",
    )


class DidAuthModel(common.models.BaseAbstractModel):
    profile = models.ForeignKey(
        'ProfileModel',
        null=True,
        blank=False,
        related_name='did_auth_tokens',
        on_delete=CUSTOM_CASCADE,
    )
    secret = models.CharField(
        max_length=36,
        null=False,
        blank=False,
        default='',
    )

    class Meta:
        verbose_name = 'Токен авторизации в DID'
        verbose_name_plural = 'Токены авторизации в DID'
        ordering = ('-created_at',)

    def __str__(self):
        return f"{getattr(getattr(self.profile, 'user'), 'email')} {self.created_at.isoformat()} {self.secret}"


class EntryInfoModel(common.models.BaseModel):
    user = models.OneToOneField(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        verbose_name='Профиль пользователя',
        related_name='entry_info',
    )
    contractor = models.OneToOneField(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        verbose_name="Организация",
        related_name='entry_info'
    )
    data = models.JSONField(
        null=False,
        default=dict,
        blank=True,
    )
    complete = models.BooleanField(
        null=False,
        default=False,
        blank=True,
        verbose_name='Завершен',
    )

    class Meta:
        verbose_name = 'Информация при регистрации'
        verbose_name_plural = 'Информация при регистрациях'


class RequestTypeModel(common.models.BaseCatalog, common.models.BaseAbstractCatalog):
    """Модель типа заявки от пользователя."""
    email = models.EmailField(
        verbose_name='email, куда отправлять заявки',
        max_length=255,
        blank=True,
        default=''
    )


class LeaveRequestModel(common.models.BaseAbstractModel):
    """Запросить демонстрацию. Оставьте свои контакты, и мы свяжемся с вами в ближайшее время.
    Сможете задать вопросы эксперту."""
    name = models.CharField(max_length=128, verbose_name='Имя', null=False)
    email = models.CharField(max_length=50, verbose_name='email', null=False)
    phone = models.CharField(max_length=20, verbose_name='Телефон', default='')
    privacy_policy_consent = models.BooleanField(
        verbose_name='Соглашаюсь с политикой конфиденциальности',
        null=True
    )
    marketing_consent = models.BooleanField(
        verbose_name='Соглашаюсь на получение рекламных материалов',
        null=True
    )
    data = models.JSONField(
        null=False,
        blank=True,
        default=dict,
        verbose_name='Дополнительная информация'
    )
    request_type = CustomForeignKey(
        to='users.RequestTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип заявки'
    )


class NewUserInfoModel(common.models.BaseAbstractModel):
    user = CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Профиль'),
        related_name='new_user_info',
    )
    contractor = CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
    )
    is_chat_welcome_sent = CustomBooleanField(
        default=False,
        verbose_name='Отправлено приветственное сообщение в чате'
    )
    tariff_filter = fields.TariffFilterField()

    class Meta:
        verbose_name = _('Информация о новом пользователе')
        verbose_name_plural = _('Информация о новых пользователях')
        ordering = ('-created_at',)

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).order_by('-created_at', )
        return qs

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import NewUserInfoListSerializer, NewUserInfoUpdateSerializer
        if action in ['update', 'partial_update']:
            return NewUserInfoUpdateSerializer
        return NewUserInfoListSerializer

    @classmethod
    def get_table_columns(cls):
        return ['contractor', 'tariff_filter', ]

    @classmethod
    def search_input(cls):
        return True


from datetime import timedelta


class DesktopAuthCode(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    state = models.UUIDField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='desktop_auth_codes')

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['state']),
            models.Index(fields=['expires_at']),
        ]

    @classmethod
    def create_for_user(cls, user, state, ttl_minutes: int = 2):
        return cls.objects.create(
            user=user,
            state=state,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    def is_valid(self) -> bool:
        if self.used_at is not None:
            return False
        return timezone.now() <= self.expires_at


class DesktopWebViewSecret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        "users.CustomUser",  # или settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name="desktop_webview_secrets",
    )

    secret = models.CharField(max_length=128, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self, ttl_seconds: int = 10) -> bool:
        if self.used_at is not None:
            return False
        age = (timezone.now() - self.created_at).total_seconds()
        return age <= ttl_seconds

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # до super().save()

        super().save(*args, **kwargs)

        # Чистим только при создании (чтобы не тёрлось на любом update)
        if is_new:
            cutoff = timezone.now() - timedelta(hours=12)
            self.__class__.objects.filter(created_at__lt=cutoff).delete()

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # до super().save()

        super().save(*args, **kwargs)

        # Чистим только при создании (чтобы не тёрлось на любом update)
        if is_new:
            cutoff = timezone.now() - timedelta(hours=12)
            self.__class__.objects.filter(created_at__lt=cutoff).delete()
