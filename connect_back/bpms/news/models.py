import json

from django.db import models
from common.models import BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from common.validators import  validate_text_to_json
from common import fields as common_fields
from common.page_config.filter_fields import ChoiceFilterField, ForeignKeyFilterField, ProfileFilterField
from bkz3.settings import CUSTOM_CASCADE


class CheckedNewsCategoryModel(BaseAbstractModel):
    user = models.OneToOneField(
        to='users.ProfileModel',
        verbose_name='Пользователь',
        on_delete=CUSTOM_CASCADE,
        related_name='checked_news',
    )

    _data = models.TextField(
        null=False,
        blank=False,
        default='{"categories":[],"workgroups":[]}',
        validators=(validate_text_to_json,),
    )

    @property
    def data(self) -> dict:
        return json.loads(self._data)

    @data.setter
    def data(self, value):
        self._data = value

    class Meta:
        verbose_name = 'Выбранная категория'
        verbose_name_plural = 'Выбранные категории'
