import json

from django.db import models
from django.utils.translation import gettext_lazy as _

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from common import models as common_models
from common import fields as common_fields
from common.validators import validate_text_to_json


class CatalogSectionModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    class Meta:
        verbose_name = _('Раздел')
        verbose_name_plural = _('Разделы')


class CatalogInfoModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    section = common_fields.CustomForeignKey(
        to='CatalogSectionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='catalog_info',
        verbose_name=_('Раздел')
    )

    model = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Модель')
    )

    _form_info = models.TextField(
        null=False,
        blank=False,
        default='{}',
        validators=(validate_text_to_json,),
    )

    app_section_roles = models.ManyToManyField(
        to='contractor_permissions.AppSectionRoleThroughModel',
        through='CatalogInfoAppSectionRoleThroughModel',
        through_fields=('catalog_info', 'app_section_role'),
        related_name='catalog_info',
    )

    @property
    def form_info(self):
        return json.loads(self._form_info)

    @form_info.setter
    def form_info(self, value):
        self._form_info = value

    class Meta:
        verbose_name = _('Справочник')
        verbose_name_plural = _('Справочники')


class CatalogInfoAppSectionRoleThroughModel(common_models.BaseAbstractModel):
    catalog_info = common_fields.CustomForeignKey(
        to='catalog_info.CatalogInfoModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='catalog_info_app_section_role'
    )
    app_section_role = common_fields.CustomForeignKey(
        to='contractor_permissions.AppSectionRoleThroughModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='catalog_info_app_section_role'
    )

    class Meta:
        verbose_name = _('Роль раздела для справочника')
        verbose_name_plural = _('Роли раздела для справочника')
