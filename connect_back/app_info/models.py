import json

from django.db import models

from rest_framework import exceptions as drf_exceptions

from common.models import BaseAbstractCatalog, BaseAbstractModel, BaseCatalog
from common.validators import validate_text_to_json


class AppInfo(BaseCatalog, BaseAbstractCatalog):
    @classmethod
    def is_enum(cls):
        return True

    _metadata = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )

    @property
    def metadata(self):
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    class Meta:
        verbose_name = "Метаданные"
        verbose_name_plural = "Метаданные"


class CustomRoutesModel(BaseAbstractModel):
    @classmethod
    def is_enum(cls):
        return True

    _metadata = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )

    @property
    def metadata(self):
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, dict):
            return
        for key, val in value.items():
            val.pop('pageWidget', None)
            val.pop('title', None)
            val.pop('icon', None)
            val.pop('path', None)
        value_str = json.dumps(value)
        self._metadata = value_str

    class Meta:
        verbose_name = "Кастомный роут"
        verbose_name_plural = "Кастомные роуты"
