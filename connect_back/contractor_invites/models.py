from django.db import models
from common.models import BaseAbstractModel
from common import fields as common_fields
from common.catalogs.models import ContractorModel

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT


class ContractorInviteStatusModel(BaseAbstractModel):
    name = common_fields.CustomCharField(
        max_length=127,
        null=False,
        default='',
        blank=False,
        verbose_name="Название",
    )
    code = common_fields.CustomCharField(
        max_length=20,
        null=False,
        default='',
        blank=False,
        verbose_name="Код",
        unique=True,
    )
    color = common_fields.CustomCharField(
        max_length=20,
        null=False,
        default='',
        blank=False,
        verbose_name="Цвет",
    )

    def __str__(self):
        return f"{self.code} {self.name}"

    class Meta:
        verbose_name = "Статус приглашений"
        verbose_name_plural = "Статусы приглашений"


class ContractorInviteModel(BaseAbstractModel):
    contractor_parent = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Родительский контрагент',
        null=True,
        blank=False,
        related_name='invite_relations_parent',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Контрагент',
        null=True,
        blank=False,
        related_name='invite_relations',
    )
    contractor_owner = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='invite_relations_owners'
    )

    status = common_fields.CustomForeignKey(
        to='contractor_invites.ContractorInviteStatusModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        default='new',
        blank=True,
    )
    relation_type = common_fields.CustomForeignKey(
        to='catalogs.ContractorRelationTypeModel',
        to_field='code',
        null=False,
        default='structural_division',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Тип отношения',
        related_name='invite_relations'
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorInviteModelListSerializer, ContractorInviteModelCreateSerializer, \
            ContractorInviteNotify
        if action:
            if action == 'list':
                return ContractorInviteModelListSerializer
            elif action == 'create':
                return ContractorInviteModelCreateSerializer
            elif action == 'notify':
                return ContractorInviteNotify
            else:
                return ContractorInviteModelListSerializer
        return ContractorInviteModelListSerializer





    class Meta:
        verbose_name = 'Приглашение связи клиентов'
        verbose_name_plural = 'Приглашения связи клиентов'

