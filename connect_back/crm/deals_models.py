from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from bkz3.settings import CUSTOM_SET_NULL
from common import fields as common_fields
from common import models as common_models
from help_desk.models import CustomerCardModel


class DealStageModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        max_length=32,
        null=False,
        blank=True,
        default='#FF9A01',
        verbose_name=_('Цвет'),
    )
    is_final = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Финальная стадия'),
    )
    is_success = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Успешный исход'),
    )

    class Meta:
        verbose_name = _('Стадия сделки')
        verbose_name_plural = _('Стадии сделки')
        ordering = ('sort', 'name')

    @classmethod
    def get_data_path(cls):
        return '/crm/deals/stages/'

    @classmethod
    def get_table_columns(cls):
        return ('name', 'code', 'color', 'sort', 'is_final', 'is_success')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .deals_serializers import DealStageSerializer
        return DealStageSerializer


class DealModel(common_models.BaseModel):
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Наименование сделки'),
    )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )
    stage = common_fields.CustomForeignKey(
        to='crm.DealStageModel',
        null=True,
        blank=True,
        related_name='deals',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Стадия'),
    )
    responsible = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=True,
        related_name='responsible_deals',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Ответственный'),
    )
    customer_card = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardModel',
        null=True,
        blank=True,
        related_name='deals',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Карточка клиента'),
    )
    source_ticket = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketModel',
        null=True,
        blank=True,
        related_name='deals',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Исходное обращение'),
    )
    expected_amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name=_('Сумма сделки'),
    )
    internal_budget = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name=_('Внутренняя смета'),
    )
    probability = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=0,
        verbose_name=_('Вероятность, %'),
    )
    planned_close_date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Плановая дата закрытия'),
    )
    members = models.ManyToManyField(
        to='users.ProfileModel',
        blank=True,
        related_name='deal_memberships',
        verbose_name=_('Участники сделки'),
    )
    observers = models.ManyToManyField(
        to='users.ProfileModel',
        blank=True,
        related_name='deal_observers',
        verbose_name=_('Наблюдатели'),
    )

    class Meta:
        verbose_name = _('Сделка')
        verbose_name_plural = _('Сделки')
        ordering = ('-updated_at', '-created_at')

    def __str__(self):
        if self.name:
            return self.name
        if self.customer_card_id:
            return f'Сделка: {self.customer_card.name}'
        return f'Сделка {self.pk}'

    @classmethod
    def get_data_path(cls):
        return '/crm/deals/deals/'

    @property
    def frontend_route(self):
        return f'/deals?deal={self.pk}'

    @property
    def get_member_ids(self):
        member_ids = set(self.members.values_list('pk', flat=True))
        observer_ids = set(self.observers.values_list('pk', flat=True))
        if self.author_id:
            member_ids.add(self.author_id)
        if self.responsible_id:
            member_ids.add(self.responsible_id)
        return list(member_ids | observer_ids)

    @classmethod
    def get_queryset(cls, request=None):
        queryset = cls.objects.filter(is_active=True).select_related(
            'stage',
            'responsible__user',
            'responsible__avatar',
            'customer_card',
            'source_ticket',
        ).prefetch_related(
            'customer_contracts__status',
            'customer_contracts__organization',
            'customer_contracts__customer_card',
            'members__user',
            'members__avatar',
            'observers__user',
            'observers__avatar',
        )
        if request is None:
            return queryset.order_by('-updated_at', '-created_at')
        user = request.user.profile
        check_profile_types = getattr(user, 'check_profile_types', None)
        if callable(check_profile_types) and user.check_profile_types({'superuser', 'admin'}):
            return queryset.order_by('-updated_at', '-created_at')
        accessible_customer_cards = CustomerCardModel.get_queryset(request).values_list('pk', flat=True)
        return queryset.filter(
            Q(author=user)
            | Q(responsible=user)
            | Q(members=user)
            | Q(observers=user)
            | Q(customer_card_id__in=accessible_customer_cards)
        ).distinct().order_by('-updated_at', '-created_at')

    @classmethod
    def get_table_columns(cls):
        return (
            'name',
            'stage',
            'customer_card',
            'responsible',
            'expected_amount',
            'internal_budget',
            'probability',
            'planned_close_date',
            'updated_at',
        )

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .deals_serializers import DealCreateUpdateSerializer, DealDetailSerializer, DealListSerializer
        if action in ('create', 'update', 'partial_update'):
            return DealCreateUpdateSerializer
        if action == 'retrieve':
            return DealDetailSerializer
        return DealListSerializer

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        if getattr(user, 'check_profile_types', None) and user.check_profile_types({'superuser', 'admin'}):
            return True
        if self.customer_card_id and self.customer_card and self.customer_card.get_detail_permission(request):
            return True
        return (
            user == self.author
            or user == self.responsible
            or self.members.filter(pk=user.pk).exists()
            or self.observers.filter(pk=user.pk).exists()
        )

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if getattr(user, 'check_profile_types', None) and user.check_profile_types({'superuser', 'admin'}):
            return True
        if self.customer_card_id and self.customer_card and self.customer_card.get_detail_permission(request):
            return True
        return (
            user == self.author
            or user == self.responsible
            or self.members.filter(pk=user.pk).exists()
        )
