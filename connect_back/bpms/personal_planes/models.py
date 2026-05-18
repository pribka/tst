import uuid
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT

from common import models as common_models
from common import fields as common_fields


class PersonalPlaneStatusModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    class Meta:
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')


class PersonalPlaneModel(common_models.BaseModel):
    meta_exclude_fields = ['author_uid', 'author', 'description', 'created_at', 'mentions', 'ct']

    status = common_fields.CustomForeignKey(
        to='personal_planes.PersonalPlaneStatusModel',
        to_field='code',
        null=False,
        default='in_work',
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус')
    )
    plane_date = common_fields.CustomDateField(
        null=False,
        default=timezone.localdate,
        blank=False,
        verbose_name=_('Дата плана')
    )
    description = common_fields.CustomCharField(
        max_length=500,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание')
    )
    author_uid = models.UUIDField(
        null=True,
    )

    class Meta:
        verbose_name = _('Персональный план')
        verbose_name_plural = _('Персональные планы')
        ordering = ('-plane_date', '-created_at',)
        unique_together = (('author_uid', 'plane_date',),)

    def save(self, *args, **kwargs):
        self.author_uid = self.author.pk
        super().save(*args, **kwargs)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.PersonalPlaneModelCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.PersonalPlaneModelUpdateSerializer
        return serializers.PersonalPlaneModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import get_access_users
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()
        user_id = request.query_params.get('user')
        access_users = get_access_users(request)
        if user_id:
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return qs.none()
            if user_id in access_users:
                qs = qs.filter(author_id=user_id)
            else:
                return qs.none()
        else:
            qs = qs.filter(author__in=access_users)
        return qs.order_by('plane_date',)

    def get_update_permission(self, request) -> bool:
        if request.user.profile == self.author:
            return True
        return False

    def get_detail_permission(self, request) -> bool:
        # TODO прописать когда добавлю конфиг видимости
        if request.user.profile == self.author:
            return True
        return False

    def set_is_active(self, value: bool, request):
        return


class PersonalPlaneItemModel(common_models.BaseModel):
    tps = []
    field_verbose_names = {'author': _('Автор записи в план дня'),}
    plane = common_fields.CustomForeignKey(
        to='PersonalPlaneModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Персональный план'),
        related_name='plane_items',
    )
    task = common_fields.CustomForeignKey(
        to='tasks.TaskModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Задача')
    )
    description = common_fields.CustomCharField(
        max_length=1024,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание')
    )

    work_type = common_fields.CustomForeignKey(
        to='tasks.TaskWorkTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тип работы')
    )

    duration_plane = common_fields.CustomDecimalField(
        max_digits=4,
        decimal_places=2,
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Планируемое время')
    )

    duration_fact = common_fields.CustomDecimalField(
        max_digits=4,
        decimal_places=2,
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Фактическое время')
    )

    is_result = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Результат')
    )

    class Meta:
        verbose_name = _('Пункт персонального плана')
        verbose_name_plural = _('Пункты персонального плана')
        ordering = ('created_at',)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.PersonalPlaneItemCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.PersonalPlaneItemUpdateSerializer
        else:
            return serializers.PersonalPlaneItemListSerializer

    def get_update_permission(self, request) -> bool:
        return self.plane.get_update_permission(request)

    def get_detail_permission(self, request) -> bool:
        return self.plane.get_detail_permission(request)

    def set_is_active(self, value: bool, request):
        return


class PersonalPlaneAccessOrganizationModel(common_models.BaseAbstractModel):
    owner = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='personal_plane_access_org',
        verbose_name=_('Профиль хозяина'),
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='personal_plane_access_org',
        verbose_name=_('Организация'),
        help_text='Контрагент'
    )

    class Meta:
        verbose_name = _('Доступ организации к дейлику')
        verbose_name_plural = _('Доступы организаций к дейлику')
        ordering = ('-created_at',)
        unique_together = (('owner', 'organization'),)


class PersonalPlaneAccessProfileModel(common_models.BaseAbstractModel):
    owner = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='personal_plane_access_profiles',
        verbose_name=_('Профиль пользователя'),
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='personal_plane_access_owners',
        verbose_name=_('Пользователь, которому открывается доступ'),
    )

    class Meta:
        verbose_name = _('Доступ профиля к дейлику')
        verbose_name_plural = _('Доступы профилей к дейлику')
        ordering = ('-created_at',)
        unique_together = (('owner', 'user'),)


class PersonalPlanAccessProfileMetadataModel(common_models.MetadataAbstractModel):
    user = models.OneToOneField(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
    )

    class Meta:
        verbose_name = 'Метадата для доступа профиля'
        verbose_name_plural = 'Метадаты для доступа профиля'

    def __str__(self):
        return f"{self.user.user.last_name} {self.user.user.first_name} {self.user.user.email}"
