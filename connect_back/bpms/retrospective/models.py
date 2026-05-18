from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from common import models as common_models
from common import fields as common_fields


class RetrospectiveTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Тип ретроспективы')
        verbose_name_plural = _('Типы ретроспективы')


class RetrospectiveModel(common_models.BaseModel):
    retrospective_type = common_fields.CustomForeignKey(
        to='RetrospectiveTypeModel',
        to_field='code',
        null=False,
        default='minuses',
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тип')
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Ссылка на объект'),
        related_name='related_retrospectives',
        null=True,
        blank=True,
    )
    content = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        default='',
        blank=False,
        verbose_name=_('Содержание')
    )

    class Meta:
        verbose_name = _('Ретроспектива')
        verbose_name_plural = _('Ретроспективы')

    def get_detail_permission(self, request) -> bool:
        original_related_object = self.related_object.original_object
        return original_related_object.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        return request.user.profile == self.author

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.RetrospectiveDetailSerializer
        elif action in ('update', 'partial_update'):
            return serializers.RetrospectiveUpdateSerializer
        elif action == 'create':
            return serializers.RetrospectiveCreateSerializer
        else:
            return serializers.RetrospectiveListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()

        # Пытаемся извлечь объект, если pk есть в URL
        pk = getattr(request.resolver_match, 'kwargs', {}).get('pk')
        if pk:
            try:
                obj = cls.objects.get(pk=pk)
            except (ObjectDoesNotExist, ValidationError):
                return qs.none()
            related_object = obj.related_object
            if related_object:
                original_related_object = related_object.original_object
                if not original_related_object.get_detail_permission(request):
                    return qs.none()
            return cls.objects.filter(pk=pk)

        # Фильтрация для списка (list)
        retrospective_type = request.query_params.get('retrospective_type')
        if retrospective_type:
            qs = qs.filter(retrospective_type_id=retrospective_type)
        related_object_id = request.query_params.get('related_object')
        # TODO После исправления на фронте (переименовать sprint в related_object) можно будет удалить эту замену.
        sprint_id = request.query_params.get('sprint')
        if not related_object_id and sprint_id:
            related_object_id = sprint_id
        if related_object_id:
            from common.models import BaseModel
            try:
                related_object = BaseModel.objects.get(pk=related_object_id)
            except (ObjectDoesNotExist, ValidationError):
                return qs.none()
            original_related_object = related_object.original_object
            if not original_related_object.get_detail_permission(request):
                return qs.none()
            qs = qs.filter(related_object=related_object)
        return qs.order_by('-created_at',)
