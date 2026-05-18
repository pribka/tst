import json

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.cache import cache

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from common import fields as common_fields
from common.validators import validate_text_to_json


class TariffModel(BaseCatalog, BaseAbstractCatalog):
    contractors = models.ManyToManyField(
        'catalogs.ContractorModel',
        through='billing.ContractorTariffModel',
        through_fields=('tariff', 'contractor')
    )
    description = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name='Описание',
        help_text='с html',
    )
    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        default=1,
        blank=False,
        verbose_name='Продолжительность',
        help_text='в днях'
    )
    max_users = common_fields.CustomPositiveIntegerField(
        null=False,
        default=1,
        blank=False,
        verbose_name='Макс. кол-во пользователей'
    )
    price = common_fields.CustomDecimalField(
        decimal_places=2,
        max_digits=10,
        verbose_name='Цена',
        null=False,
        default=0,
        blank=False,
    )

    _route = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )

    @property
    def route(self):
        return json.loads(self._route)

    @route.setter
    def route(self, value):
        self._route = value

    @property
    def modules(self):

        modules = [value.get('name', '') for key, value in self.route.items()]

        return modules

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
        ordering = ('sort', 'name',)

    def save(self, *args, **kwargs):
        if self.pk:
            # Инвалидируем кэш tariffs_id_by_contractors, в том числе у всех нижестоящих организаций
            from users.utils import get_descendants_departments_related_organizations
            contractor_ids = self.contractors.values_list('id', flat=True)
            descendants = get_descendants_departments_related_organizations(contractor_ids, include_self=True,)
            for descendant in descendants:
                cache_key = f'tariffs_id_by_contractor_{str(descendant)}'
                cache.delete(cache_key)
        super().save(*args, **kwargs)


class TariffDiscountModel(BaseAbstractModel):
    tariff = common_fields.CustomForeignKey(
        to='billing.TariffModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Тариф',
        null=True,
        blank=False,
        related_name='discounts',
    )
    value = common_fields.CustomDecimalField(
        null=False,
        max_digits=4,
        decimal_places=3,
        default=0,
        blank=False,
        verbose_name='Значение',
        help_text='В %, от 0 до 100',
        validators=(MinValueValidator(limit_value=0), MaxValueValidator(limit_value=100))
    )
    date_start = common_fields.CustomDateTimeField(
        null=True,
        verbose_name='Дата начала',
    )
    date_end = common_fields.CustomDateTimeField(
        null=True,
        verbose_name='Дата окончания',
    )

    class Meta:
        verbose_name = 'Скидка тарифа'
        verbose_name_plural = 'Скидки тарифа'


class ContractorTariffModel(BaseAbstractModel):
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Организация',
        related_name='contractor_tariffs'
    )
    tariff = common_fields.CustomForeignKey(
        to='billing.TariffModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Тариф',
        related_name='contractor_tariffs'
    )
    date_start = common_fields.CustomDateTimeField(
        null=True,
        blank=False,
        verbose_name='Дата начала',
    )
    date_end = common_fields.CustomDateTimeField(
        null=True,
        blank=False,
        verbose_name='Дата окончания',
    )

    class Meta:
        verbose_name = 'Тариф организации'
        verbose_name_plural = 'Тарифы организации'
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        if self.pk:
            # Инвалидируем кэш tariffs_id_by_contractors, в том числе у всех нижестоящих организаций
            from users.utils import get_descendants_departments_related_organizations
            descendants = get_descendants_departments_related_organizations((self.contractor_id,), include_self=True,)
            for descendant in descendants:
                cache_key = f'tariffs_id_by_contractor_{str(descendant)}'
                cache.delete(cache_key)
        super().save(*args, **kwargs)


class ContractorTariffNotificationLog(BaseAbstractModel):
    """Лог отправленных уведомлений по тарифам"""
    contractor_tariff = common_fields.CustomForeignKey(
        to='billing.ContractorTariffModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Тариф организации',
        related_name='notification_logs'
    )
    notification_type = models.CharField(
        max_length=50,
        verbose_name='Тип уведомления',
        choices=[
            ('demo_started', 'Демо началось'),
            ('demo_ending_3days', 'До окончания демо 3 дня'),
            ('demo_ended', 'Демо закончилось'),
        ]
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата отправки'
    )
    
    class Meta:
        verbose_name = 'Лог уведомления по тарифу'
        verbose_name_plural = 'Логи уведомлений по тарифам'
        unique_together = [
            ('contractor_tariff', 'notification_type')
        ]