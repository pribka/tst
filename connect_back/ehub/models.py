from django.db import models
from common.models import BaseAbstractModel

from bkz3.settings import BACKEND_URL, CUSTOM_CASCADE, CUSTOM_PROTECT


class EhubServerGroupModel(BaseAbstractModel):
    name = models.CharField(
        max_length=1023,
        null=False,
        default='',
        blank=False,
        verbose_name='Наименование'
    )
    code = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        unique=True,
        verbose_name='Код',
    )

    class Meta:
        verbose_name = 'Группа серверов'
        verbose_name_plural = 'Группы серверов'
        ordering = ('sort', 'name',)

    def __str__(self):
        return f'{self.code} {self.name}'


class EhubRegionModel(BaseAbstractModel):
    name = models.CharField(
        max_length=1023,
        null=False,
        default='',
        blank=False,
        verbose_name='Наименование'
    )
    code = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        unique=True,
        verbose_name='Код',
    )
    internal_url = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        verbose_name='Внутренний урл',
        help_text='Полный путь без слэша: http://host:port'
    )

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'

    def __str__(self):
        return self.code


class EhubServerModel(BaseAbstractModel):
    server_group = models.ForeignKey(
        'ehub.EhubServerGroupModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Группа серверов',
    )
    name = models.CharField(
        max_length=1023,
        null=False,
        default='',
        blank=False,
        verbose_name='Наименование',
    )
    code = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        unique=True,
        verbose_name='Код',
    )
    internal_url = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        verbose_name='Внутренний урл',
        help_text='Полный путь без слэша: http://host:port'
    )
    frontend_url = models.CharField(
        max_length=255,
        null=False,
        default='',
        blank=False,
        verbose_name='Урл до бэкенда',
        help_text='Полный путь без слэша: http://host'
    )
    users = models.ManyToManyField(
        'users.ProfileModel',
        through='ehub.EhubServerUserModel',
        verbose_name='Пользователи сервера',
        related_name='ehub_servers',
        through_fields=('server', 'user')
    )

    @property
    def user_url(self):
        return f'{self.internal_url}/api/e-hub/user/'

    @property
    def token_url(self):
        return f'{self.internal_url}/api/e-hub/token/'

    @property
    def url(self):
        return f'{BACKEND_URL}/api/v1/ehub/redirect/{self.code}/'

    @property
    def check_password_url(self):
        return f'{self.internal_url}/api/e-hub/check_password/'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Сервер'
        verbose_name_plural = 'Серверы'


class EhubServerUserModel(BaseAbstractModel):
    server = models.ForeignKey(
        'ehub.EhubServerModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Сервер',
        related_name='ehub_user_servers',
    )
    user = models.ForeignKey(
        'users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Профиль пользователя',
        related_name='ehub_user_servers',
    )

    class Meta:
        verbose_name = 'Пользователь сервера'
        verbose_name_plural = 'Пользователи сервера'
