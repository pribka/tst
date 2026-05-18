from django.db import models
from common.models import BaseCatalog, BaseAbstractCatalog


class StaticPageModel(BaseCatalog, BaseAbstractCatalog):
    html_data = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Данные html',
    )
    json_data = models.JSONField(
        null=False,
        blank=True,
        default=dict,
        verbose_name='Данные json',
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import StaticPageModelSerializer
        return StaticPageModelSerializer

    class Meta:
        verbose_name = 'Статическая страница'
        verbose_name_plural = 'Статические страницы'
