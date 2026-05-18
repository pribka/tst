from django.db import models
from django.utils.translation import gettext_lazy as _

from bkz3.settings import CUSTOM_CASCADE

from common import models as common_models
from common import fields as common_fields


class ReactionModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    icon = common_fields.CustomCharField(
        max_length=7,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Иконка')
    )

    class Meta:
        verbose_name = _('Реакция')
        verbose_name_plural = _('Реакции')
        ordering = ('sort',)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        return serializers.ReactionListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort', 'name',)


class ReactionObjectModel(common_models.BaseAbstractModel):
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='reactions',
        verbose_name=_('Связанный объект')
    )

    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='object_reactions',
        verbose_name=_('Пользователь'),
    )

    reaction = common_fields.CustomForeignKey(
        to='reactions.ReactionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='object_reactions',
        verbose_name=_('Реакция')
    )

    class Meta:
        verbose_name = _('Реакция на объект')
        verbose_name_plural = _('Реакции на объект')
        unique_together = (('related_object', 'user',),)

