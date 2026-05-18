from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import exceptions as drf_exceptions

from bkz3.settings import CUSTOM_SET_DEFAULT, CUSTOM_CASCADE

from common import fields as common_fields, models as common_models


class NoteModel(common_models.BaseModel):
    color = common_fields.CustomForeignKey(
        to='ColorNoteModel',
        to_field='code',
        null=False,
        blank=False,
        default='#ffffff',
        on_delete=CUSTOM_SET_DEFAULT,
        verbose_name=_('Цвет'),
        related_name='color_notes'
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Связанный объект'),
        related_name='notes'
    )
    title = common_fields.CustomCharField(
        max_length=1024,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Заголовок')
    )
    content = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Содержимое')
    )

    class Meta:
        verbose_name = _('Заметка')
        verbose_name_plural = _('Заметки')

    def __str__(self):
        return self.title

    def get_update_permission(self, request) -> bool:
        related_object = self.related_object
        if related_object:
            original_object = related_object.original_object
            try:
                result = original_object.get_note_permission(request)
            except AttributeError:
                result = original_object.get_update_permission(request)
            return result
        else:
            return self.author == request.user.profile

    def get_detail_permission(self, request) -> bool:
        related_object = self.related_object
        if related_object:
            original_object = related_object.original_object
            return original_object.get_detail_permission(request)
        else:
            return self.author == request.user.profile

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    @classmethod
    def get_table_columns(cls):
        return 'color', 'title'

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if request:
            related_object_id = request.query_params.get('related_object')
            if related_object_id:
                try:
                    related_object = common_models.BaseModel.objects.super_get(related_object_id)
                except (ValidationError, ObjectDoesNotExist,):
                    return qs.none()
                if not related_object.get_detail_permission(request):
                    return qs.none()
                qs = qs.filter(related_object_id=related_object_id)

        return qs.order_by('-created_at',)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.NoteModelListSerializer
        if action in ('update', 'partial_update',):
            return serializers.NoteModelUpdateSerializer
        if action == 'create':
            return serializers.NoteModelCreateSerializer
        else:
            return serializers.NoteModelListSerializer


class ColorNoteModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    o_color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=False,
        default='',
        verbose_name=_('Код цвета')
    )

    class Meta:
        verbose_name = _('Цвет')
        verbose_name_plural = _('Цвета')
        ordering = ('sort', 'created_at',)

    def __str__(self):
        return self.code

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ColorNoteSerializer
        return ColorNoteSerializer

    @property
    def color(self):
        return self.code

    @property
    def oColor(self):
        return self.o_color
