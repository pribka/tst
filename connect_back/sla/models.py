from django.db import models

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from common import models as common_models
from common import fields as common_fields

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT


class SLAModel(common_models.BaseCatalog):
    level = common_fields.CustomPositiveIntegerField(
        null=False,
        default=1,
        blank=False,
        verbose_name=_('Уровень')
    )

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Цвет'),
    )

    contractor = models.ForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='org_sla',
        verbose_name=_('Организация')
    )

    first_reaction_time = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Время реагирования')
    )
    solve_time = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Время решения')
    )
    is_default = common_fields.CustomBooleanField(
        default=False,
    )

    class Meta:
        verbose_name = _('SLA')
        verbose_name_plural = _('SLA')

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.all()
        contractor = None
        if request:
            page_name = request.query_params.get('page_name')
            if page_name:
                prefix = "helpdesk_contact_person_by_"
                if page_name.startswith(prefix):
                    uid = page_name[len(prefix):]
                    if uid:
                        try:
                            customer_card = common_models.BaseModel.objects.super_get(pk=uid)
                        except (ObjectDoesNotExist, ValidationError):
                            pass
                        else:
                            contractor = customer_card.org_admin
                            qs = qs.filter(contractor=contractor)
        contractor_id = request.query_params.get('contractor')
        if not contractor_id and not contractor:
            return qs.none()
        if contractor_id:
            try:
                qs = qs.filter(contractor_id=contractor_id)
            except ValidationError:
                return qs.none()
        return qs.order_by('level')

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.SLADetailSerializer
        else:
            return serializers.SLAListSerializer

    def set_is_active(self, value: bool, request):
        return


class SLARelatedObjectModel(common_models.BaseAbstractModel):
    sla = common_fields.CustomForeignKey(
        to='sla.SLAModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='sla_related_objects',
        verbose_name=_('SLA'),
    )
    related_object = models.ForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='sla_rels',
        verbose_name=_('Связанный объект'),
    )

    class Meta:
        verbose_name = _('SLA объекта')
        verbose_name_plural = _('SLA объектов')
        unique_together = (('sla', 'related_object',),)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        SLARelatedObjectModel.objects.filter(
            related_object=self.related_object,
            sla__contractor=self.sla.contractor,
        ).exclude(pk=self.pk).delete()


class SLAValueModel(common_models.BaseModel):
    related_object = models.OneToOneField(
        to='common.BaseModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='sla_value',
        verbose_name=_('Связанный объект')
    )
    sla = common_fields.CustomForeignKey(
        to='sla.SLAModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        related_name='sla_vals',
        verbose_name='SLA'
    )
    first_reaction_time = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Время реагирования')
    )
    solve_time = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Время решения')
    )

    class Meta:
        verbose_name = _('Значение SLA')
        verbose_name_plural = _('Значения SLA')


class SLAValueSourceModel(common_models.BaseAbstractModel):
    owner = models.ForeignKey(
        to='sla.SLAValueModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='value_sources',
        verbose_name=_('Значение SLA')
    )
    related_object = models.ForeignKey(
        to='common.BaseModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='sla_sources_rel',
        verbose_name=_('Связанный объект')
    )
    sla = common_fields.CustomForeignKey(
        to='sla.SLAModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=True,
        related_name='sla_value_sources',
        verbose_name='SLA'
    )
    description = models.CharField(
        max_length=511,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Описание')
    )
    first_reaction_time = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Время реагирования')
    )
    solve_time = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Время решения')
    )

    class Meta:
        verbose_name = _('Источник значения SLA')
        verbose_name_plural = _('Источники значения SLA')
