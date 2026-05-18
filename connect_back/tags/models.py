from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from bkz3.settings import CUSTOM_CASCADE

from common import models as common_models
from common import fields as common_fields


class TagModel(common_models.BaseModel):
    meta_exclude_fields = ['author', 'name', 'created_at', 'mentions', 'ct', 'contractors', 'related_objects',]

    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        unique=True,
        verbose_name=_('Наименование'),
        help_text='Уникальное значение',
    )
    contractors = models.ManyToManyField(
        to='catalogs.ContractorModel',
        related_name='contractor_tags',
        through='TagContractorThrough',
        through_fields=('tag', 'contractor',)
    )
    related_objects = models.ManyToManyField(
        to='common.BaseModel',
        related_name='object_tags',
        through='TagRelatedObjectThrough',
        through_fields=('tag', 'related_object',)
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.TagModelCreateSerializer
        return serializers.TagModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.all()
        if request:
            related_object_id = request.query_params.get('related_object')
            if related_object_id:
                try:
                    related_object = common_models.BaseModel.objects.super_get(related_object_id)
                except (ValidationError, ObjectDoesNotExist):
                    return qs.none()
                if not related_object.get_detail_permission(request):
                    return qs.none()
                qs = qs.filter(related_objects=related_object)
            model = request.query_params.get('model')
            if model:
                app_label, model_name = model.lower().split('.')
                try:
                    ct = ContentType.objects.get_by_natural_key(app_label, model_name)
                except ObjectDoesNotExist:
                    return qs.none()
                qs = qs.filter(related_objects__ct=ct)
            search = request.query_params.get('search')
            if search:
                qs = qs.filter(name__icontains=search)
        return qs.distinct().order_by('name',)

    @classmethod
    def get_select_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).order_by('name',)
        return qs

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        qs = cls.get_select_queryset(request)
        qs = qs.filter(name__icontains=text)
        return qs

    def set_is_active(self, value: bool, request):
        return

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Тэг')
        verbose_name_plural = _('Тэги')


class TagContractorThrough(common_models.BaseAbstractModel):
    tag = common_fields.CustomForeignKey(
        to='TagModel',
        null=True,
        blank=False,
        related_name='tag_contractors',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Тэг'),
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        verbose_name=_('Организация'),
        on_delete=CUSTOM_CASCADE,
        related_name='tag_contractors'
    )

    class Meta:
        verbose_name = _('Тэг организации')
        verbose_name_plural = _('Тэги организации')
        unique_together = (('tag', 'contractor',),)


class TagRelatedObjectThrough(common_models.BaseAbstractModel):
    tag = common_fields.CustomForeignKey(
        to='TagModel',
        null=True,
        blank=False,
        related_name='tag_object_through',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Тэг'),
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        verbose_name=_('Связанны объект'),
        on_delete=CUSTOM_CASCADE,
        related_name='object_tag_through',
    )
    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='default',
        verbose_name=_('Цвет')
    )

    class Meta:
        verbose_name = _('Тэг объекта')
        verbose_name_plural = _('Тэги объекта')
        unique_together = (('tag', 'related_object',),)
