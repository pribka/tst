from django.db import models

from bkz3.settings import CUSTOM_CASCADE
from common import fields as common_fields
from common.models import BaseAbstractModel


class UserVotesModel(BaseAbstractModel):
    related_object = common_fields.CustomForeignKey(
        'common.BaseModel',
        null=True,
        on_delete=CUSTOM_CASCADE,
        related_name='votes'
    )
    vote = common_fields.CustomBooleanField(
        default=False,
        verbose_name="Оценка"
    )

    class Meta:
        unique_together = (('author', 'related_object'),)
        verbose_name = 'Голосование пользователя'
        verbose_name_plural = 'Голосования пользователей'


class UserRatingModel(BaseAbstractModel):
    related_object = common_fields.CustomForeignKey(
        'common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='ratings',
    )
    rating = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        verbose_name="Оценка"
    )
    description = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name='Комментарий',
    )

    class Meta:
        unique_together = (('author', 'related_object',),)
        verbose_name = 'Оценка пользователя'
        verbose_name_plural = 'Оценки пользователей'
