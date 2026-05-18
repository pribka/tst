from django.db import models

from bkz3.settings import CUSTOM_PROTECT
from common import fields as common_fields
from common.models import BaseAbstractCatalog, BaseCatalog


class Configuration1cModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Конфигурация 1С'
        verbose_name_plural = 'Конфигурации 1С'

    def __str__(self):
        return f'{self.name}'


class Tariff1CModel(BaseCatalog, BaseAbstractCatalog):
    disk_space = common_fields.CustomIntegerField(
        verbose_name='Объем дискового пространства',
        blank=True,
        null=True
    )
    cpu_cores = common_fields.CustomIntegerField(
        verbose_name='Количество ядер процессора',
        blank=True,
        null=True
    )
    ram = common_fields.CustomIntegerField(
        verbose_name='Объем оперативной памяти',
        blank=True,
        null=True
    )
    subscribers = common_fields.CustomIntegerField(
        verbose_name='Количество подписчиков',
        blank=True,
        null=True
    )
    software = common_fields.CustomCharField(
        verbose_name='Програмное обеспечение',
        max_length=1023,
        blank=True,
        default=''
    )
    price = common_fields.CustomIntegerField(
        verbose_name='Стоимость',
        null=True,
        blank=True
    )
    additional_user_price = common_fields.CustomIntegerField(
        verbose_name='Стоимость подключения дополнительного пользователя',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'

    def __str__(self):
        return f"{self.name}"


class TicketTypeModel(BaseCatalog, BaseAbstractCatalog):

    class Meta:
        verbose_name = 'Тип обращения'
        verbose_name_plural = 'Типы обращений'


class TicketTypeOptionModel(BaseCatalog, BaseAbstractCatalog):
    ticket_type = models.ManyToManyField(
        TicketTypeModel,
        default='base_1c',
        verbose_name='Тип обращения'
    )

    class Meta:
        verbose_name = 'Вариант типа обращения'
        verbose_name_plural = 'Варианты типа обращения'

    def __str__(self):
        return f'{self.name}'


class TicketModel(BaseCatalog, BaseAbstractCatalog):
    ticket_type = common_fields.CustomForeignKey(
        TicketTypeModel,
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип обращения'
    )
    connection_option = common_fields.CustomForeignKey(
        TicketTypeOptionModel,
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        verbose_name='Вариант подключения'
    )
    config_1c = common_fields.CustomForeignKey(
        Configuration1cModel,
        on_delete=CUSTOM_PROTECT,
        blank=True,
        null=True,
        verbose_name='Конфигурация 1С'
    )
    tarif = common_fields.CustomForeignKey(
        Tariff1CModel,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Тарифный план',
        related_name='tickets',
        null=True,
        blank=True,
    )
    phone = common_fields.CustomCharField(
        verbose_name='Телефон',
        max_length=255,
        blank=True,
        default=''
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=255,
        blank=True,
        default=''
    )
    company = common_fields.CustomCharField(
        verbose_name='Организация',
        max_length=255,
        blank=True,
        default=''
    )
    activity_type = common_fields.CustomCharField(
        verbose_name='Вид деятельности',
        max_length=255,
        blank=True,
        default=''
    )
    description = common_fields.CustomCharField(
        verbose_name='Дополнительная информация',
        max_length=2047,
        blank=True,
        default=''
    )
    admin_status = common_fields.CustomForeignKey(
        'tasks.TaskStatusModel',
        to_field='code',
        null=True,
        verbose_name='Статус заявки для администратора',
        on_delete=CUSTOM_PROTECT,
        related_name='admin_tickets',
    )
    user_status = common_fields.CustomForeignKey(
        'tasks.TaskStatusModel',
        to_field='code',
        null=True,
        verbose_name='Статус заявки для пользователя',
        on_delete=CUSTOM_PROTECT,
        related_name='user_tickets',
    )
    user_count = common_fields.CustomIntegerField(
        verbose_name='Количество пользователей',
        null=True,
        blank=True
    )
    rental_period = common_fields.CustomIntegerField(
        verbose_name='Срок аренды, мес.',
        null=True,
        blank=True
    )
    start_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Начало периода использования'
    )
    end_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name='Окончание периода использования'
    )
    is_closed = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Закрыта'
    )
    is_rejected = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Отклонена'
    )
    processed_by = common_fields.CustomForeignKey(
        'users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name=('Заявку обработал'),
        related_name='processed_tickets'
    )

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def get_update_permission(self, request):
        user = request.user.profile
        return (self.author == user and
                not self.is_closed and
                not self.is_rejected)

    @classmethod
    def get_serializer_class(cls, action=None):
        from tickets.serializers import (NotificationTicketDetailSerializer,
                                         TicketDetailSerializer)
        if action == 'notify':
            return NotificationTicketDetailSerializer
        else:
            return TicketDetailSerializer

    @classmethod
    def get_table_columns(cls):
        return [
            'author',
            'config_1c',
            'user_status',
            'admin_status',
            'processed_by'
        ]

    @classmethod
    def get_filter_fields(cls, exclude=None, request=None):
        data = super().get_filter_fields(exclude, request)
        user = request.user.profile
        filtered_data = []
        user_ticket_status_codes = [
            'ticket_is_under_review',
            'ticket_is_done',
            'ticket_is_rejected'
        ]
        administrator_ticket_status_codes = [
            'ticket_is_under_review',
            'ticket_is_approved',
            'ticket_is_rejected'
        ]
        if user.check_profile_types({"administrator_1c"}):
            for each in data:
                if each['name'].startswith('user_'):
                    continue
                if each['name'].startswith('admin_'):
                    each['verbose_name'] = 'Статус'
                    each['widget']['filters'] = [
                        {
                            'type': 'defined',
                            'name': 'code__in',
                            'value': administrator_ticket_status_codes
                        },
                    ]
                if each['name'].startswith('config_1c'):
                    each['widget']['toField'] = 'id'
                if each['name'].startswith('processed_by'):
                    each['verbose_name'] = 'Менеджер'
                    each['widget']['filters'] = [
                        {
                            'type': 'defined',
                            'name': 'profile_type__code',
                            'value': 'administrator_1c'
                        },
                    ]
                filtered_data.append(each)
        else:
            for each in data:
                if (each['name'].startswith('admin_') or
                    each['name'].startswith('author')):
                    continue
                if each['name'].startswith('user_'):
                    each['verbose_name'] = 'Статус'
                    each['widget']['filters'] = [
                        {
                            'type': 'defined',
                            'name': 'code__in',
                            'value': user_ticket_status_codes
                        },
                    ]
                if each['name'].startswith('config_1c'):
                    each['widget']['toField'] = 'id'
                if each['name'].startswith('processed_by'):
                    each['verbose_name'] = 'Менеджер'
                    each['widget']['filters'] = [
                        {
                            'type': 'defined',
                            'name': 'profile_type__code',
                            'value': 'administrator_1c'
                        },
                    ]
                filtered_data.append(each)
        return filtered_data

    def __str__(self):
        return f"{self.author} {self.connection_option} {self.tarif}"
