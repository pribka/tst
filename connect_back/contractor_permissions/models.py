import uuid
import json

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.utils import timezone


from rest_framework import exceptions as drf_exceptions

from common import fields as common_fields
from common.models import BaseAbstractCatalog, BaseCatalog, BaseModel, BaseAbstractModel
from common.catalogs.models import ContractorModel
from common.validators import validate_text_to_json

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT


class ContractorPermissionTypeModel(BaseCatalog, BaseAbstractCatalog):
    aux_condition_model = common_fields.CustomCharField(
        null=False,
        blank=True,
        default='',
        max_length=255,
        verbose_name='Модель дополнительного условия',
        help_text='пример: consolidation.ReportFormModel'
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorPermissionTypeListSerializer
        return ContractorPermissionTypeListSerializer

    class Meta:
        verbose_name = 'Вид разрешения'
        verbose_name_plural = 'Виды разрешений'


class ContractorPermissionAuxConditionModel(BaseModel):
    contractor_permission = common_fields.CustomForeignKey(
        to='contractor_permissions.ContractorPermissionModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Разрешение организации',
        null=True,
        blank=False,
        related_name='contractor_permission_aux_conditions'
    )
    aux_condition = common_fields.CustomForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Дополнительное условие',
        help_text='FK на BaseModel',
        null=True,
        blank=False,
        related_name='contractor_permissions_aux_conditions'
    )

    class Meta:
        verbose_name = 'Дополнительное условие'
        verbose_name_plural = 'Дополнительные условия'
        unique_together = (('contractor_permission', 'aux_condition',),)


class ContractorPermissionRoleProfileModel(BaseModel):
    contractor_permission_role = common_fields.CustomForeignKey(
        to='contractor_permissions.ContractorPermissionRoleModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Роль',
        null=True,
        blank=False,
        related_name='role_contractor_profiles'
    )

    contractor_profile = common_fields.CustomForeignKey(
        to='catalogs.ContractorProfileModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Участник организации',
        related_name='role_contractor_profiles',
        null=True,
        blank=False,
    )

    class Meta:
        verbose_name = 'Участник роли'
        verbose_name_plural = 'Участники роли'
        unique_together = (('contractor_permission_role', 'contractor_profile',),)


class ContractorPermissionRoleModel(BaseCatalog, BaseAbstractCatalog):
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Организация',
        null=True,
        blank=False,
        related_name='contractor_permissions_roles'
    )
    contractor_profiles = models.ManyToManyField(
        to='catalogs.ContractorProfileModel',
        verbose_name='Пользователи',
        through='contractor_permissions.ContractorPermissionRoleProfileModel',
    )

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

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
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorPermissionRoleModelCreateSerializer
        from .serializers import ContractorPermissionRoleModelListSerializer
        from .serializers import ContractorPermissionRoleModelDetailSerializer
        from .serializers import ContractorPermissionRoleModelUpdateSerializer
        if action == 'create':
            return ContractorPermissionRoleModelCreateSerializer
        elif action == 'retrieve':
            return ContractorPermissionRoleModelDetailSerializer
        elif action in ('update', 'partial_update'):
            return ContractorPermissionRoleModelUpdateSerializer
        else:
            return ContractorPermissionRoleModelListSerializer

    def get_detail_permission(self, request=None):
        from users.utils import check_update_organization_permission
        contractor = self.contractor
        user = request.user.profile
        try:
            check_update_organization_permission(contractor.pk, user)
        except drf_exceptions.PermissionDenied:
            return False
        return True

    def get_update_permission(self, request) -> bool:
        return self.get_detail_permission(request)

    @classmethod
    def get_queryset(cls, request=None):
        from users.utils import get_descendants_departments_related_organizations
        user = request.user.profile
        director_organizations = set(user.contractor_profile.filter(director=True).values_list('contractor', flat=True))
        admin_organizations = set(ContractorPermissionRoleModel.objects.filter(
            is_active=True,
            contractor_profiles__user=user,
            contractor_permissions__permission_type_id='admin',
        ).values_list('contractor', flat=True))
        if admin_organizations:
            director_organizations.update(admin_organizations)
        organizations = get_descendants_departments_related_organizations(director_organizations)

        from common.catalogs.models import ContractorProfileModel
        qs = cls.objects.filter(is_active=True, contractor_id__in=organizations).prefetch_related(
            models.Prefetch(
                'contractor_profiles',
                queryset=ContractorProfileModel.objects.filter(
                    user__is_active=True,
                    user__temporary_blocked=False
                ).select_related('user__user', 'user__avatar')
            ),
            models.Prefetch(
                'contractor_permissions',
                queryset=ContractorPermissionModel.objects.all().select_related('permission_type')
            )
        )
        return qs.order_by('name')


class ContractorPermissionModel(BaseModel):
    contractor_permission_role = common_fields.CustomForeignKey(
        to='contractor_permissions.ContractorPermissionRoleModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Роль',
        null=True,
        blank=False,
        related_name='contractor_permissions',
    )
    permission_type = common_fields.CustomForeignKey(
        to='contractor_permissions.ContractorPermissionTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Вид разрешения',
        null=True,
        blank=False,
        related_name='contractor_permissions'
    )

    aux_conditions = models.ManyToManyField(
        to='common.BaseModel',
        verbose_name='Доп. условия',
        blank=True,
        through='contractor_permissions.ContractorPermissionAuxConditionModel',
        through_fields=('contractor_permission', 'aux_condition'),
        related_name='aux_conditions_contractor_permissions'
    )

    def get_detail_permission(self, request) -> bool:
        return self.contractor_permission_role.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        return self.get_detail_permission(request)

    class Meta:
        verbose_name = 'Разрешение организации'
        verbose_name_plural = 'Разрешения организации'
        unique_together = (('contractor_permission_role', 'permission_type',),)


class AccessGroupModel(BaseCatalog, BaseAbstractCatalog):
    description = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Описание',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
    )
    tariffs = models.ManyToManyField(
        to='billing.TariffModel',
        blank=True,
        verbose_name=_('Тарифы'),
        through='contractor_permissions.TariffAccessGroupThrough',
        through_fields=('access_group', 'tariff'),
        related_name='access_groups',
    )
    app_section_roles = models.ManyToManyField(
        to='contractor_permissions.AppSectionRoleThroughModel',
        through='contractor_permissions.AccessGroupAppSectionRoleThrough',
        through_fields=('access_group', 'app_section_role',),
        related_name='access_groups',
        verbose_name=_('Разделы приложения'),
    )
    members = models.ManyToManyField(
        to='catalogs.ContractorProfileModel',
        through='contractor_permissions.AccessGroupMemberThroughModel',
        through_fields=('access_group', 'member'),
        related_name='access_groups',
        verbose_name=_('Сотрудники'),
    )

    class Meta:
        verbose_name = _('Группа доступа')
        verbose_name_plural = _('Группы доступа')

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'list':
            return serializers.AccessGroupListSerializer
        elif action == 'retrieve':
            return serializers.AccessGroupDetailSerializer
        elif action == 'create':
            return serializers.AccessGroupCreateSerializer
        elif action in ('update', 'partial_update'):
            return serializers.AccessGroupUpdateSerializer
        elif action == 'notify':
            return serializers.AccessGroupNotifySerializer
        return serializers.AccessGroupListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        from billing.models import TariffModel
        from .utils import get_tariffs_id_by_contractors
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()

        user = request.user.profile
        my_organizations = user.my_organizations
        contractor_id = request.query_params.get('contractor')
        if contractor_id:
            contractor_id = uuid.UUID(contractor_id)
            if contractor_id not in my_organizations and not user.is_support:
                return qs.none()
            contractor_tariffs = get_tariffs_id_by_contractors((contractor_id,))
            qs = qs.filter(
                Q(contractor_id=contractor_id) | Q(tariffs__in=contractor_tariffs)
            ).distinct()
        else:
            contractor_tariffs = get_tariffs_id_by_contractors(my_organizations)
            qs = qs.filter(
                Q(contractor_id__in=my_organizations) | Q(tariffs__in=contractor_tariffs)
            ).distinct()
        return qs.order_by('-is_predefined', 'name')

    def get_update_permission(self, request) -> bool:
        if self.is_predefined:
            return False
        user = request.user.profile
        if user.is_support:
            return True
        # TODO дописать условия
        return True

    def get_detail_permission(self, request) -> bool:
        from common.utils import get_my_access_groups
        my_access_groups = get_my_access_groups(request.user.profile).values_list('pk', flat=True)
        if self.pk in my_access_groups:
            return True
        return False


class AccessGroupMemberThroughModel(BaseAbstractModel):
    access_group = common_fields.CustomForeignKey(
        to='contractor_permissions.AccessGroupModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='access_group_members_through',
        verbose_name=_('Группа доступа')
    )
    member = common_fields.CustomForeignKey(
        to='catalogs.ContractorProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='access_group_members_through',
        verbose_name=_('Сотрудник'),
    )

    class Meta:
        verbose_name = _('Сотрудник группы доступа')
        verbose_name_plural = _('Сотрудники группы доступа')


class TariffAccessGroupThrough(BaseAbstractModel):
    tariff = common_fields.CustomForeignKey(
        to='billing.TariffModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='tariff_access_group_through',
        verbose_name=_('Тариф'),
    )
    access_group = common_fields.CustomForeignKey(
        to='contractor_permissions.AccessGroupModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='tariff_access_group_through',
        verbose_name=_('Группа доступа')
    )

    class Meta:
        verbose_name = _('Группа доступа тарифа')
        verbose_name_plural = _('Группы доступа тарифов')
        unique_together = (('tariff', 'access_group',),)


class AppSectionModel(BaseCatalog, BaseAbstractCatalog):
    backend_slug = models.CharField(
        max_length=31,
        null=False,
        default='',
        blank=True,

    )
    roles = models.ManyToManyField(
        to='contractor_permissions.AppSectionRoleModel',
        through='contractor_permissions.AppSectionRoleThroughModel',
        through_fields=('app_section', 'role',),
        related_name='app_sections',
        verbose_name=_('Роли'),
    )
    tariffs = models.ManyToManyField(
        to='billing.TariffModel',
        through='contractor_permissions.TariffAppSectionThrough',
        through_fields=('app_section', 'tariff',),
        related_name='app_sections',
        verbose_name=_('Тарифы')
    )
    is_main = models.BooleanField(
        default=True,
        verbose_name='Основной'
    )

    _routes = models.TextField(
        null=False,
        default='',
        blank=True,
        validators=(validate_text_to_json,),
    )

    @property
    def routes(self):
        return json.loads(self._routes)

    @routes.setter
    def routes(self, value):
        self._routes = value

    _mobile_routes = models.TextField(
        null=False,
        default='',
        blank=True,
        validators=(validate_text_to_json,),
    )

    @property
    def mobile_routes(self):
        return json.loads(self._mobile_routes)

    @mobile_routes.setter
    def mobile_routes(self, value):
        self._mobile_routes = value

    class Meta:
        verbose_name = _('Раздел приложения')
        verbose_name_plural = _('Разделы приложения')
        ordering = ('name',)


class TariffAppSectionThrough(BaseAbstractModel):
    tariff = common_fields.CustomForeignKey(
        to='billing.TariffModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='tariff_app_section_through',
        verbose_name=_('Тариф'),
    )
    app_section = common_fields.CustomForeignKey(
        to='contractor_permissions.AppSectionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='tariff_app_section_through',
        verbose_name=_('Раздел приложения')
    )

    class Meta:
        verbose_name = _('Раздел приложения тарифа')
        verbose_name_plural = _('Разделы приложения тарифа')
        unique_together = (('tariff', 'app_section',),)
        ordering = ('app_section__name',)


class AccessGroupAppSectionRoleThrough(BaseAbstractModel):
    """Связь группы доступа с ролью раздела."""
    access_group = common_fields.CustomForeignKey(
        to='contractor_permissions.AccessGroupModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='app_section_access_group_role_through',
        verbose_name=_('Группа доступа'),
    )
    app_section_role = common_fields.CustomForeignKey(
        to='contractor_permissions.AppSectionRoleThroughModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='app_section_access_group_role_through',
        verbose_name=_('Раздел'),
    )

    class Meta:
        verbose_name = _('Роль раздела группы доступа')
        verbose_name_plural = _('Роли раздела группы доступа')
        unique_together = (('access_group', 'app_section_role',),)
        ordering = (
            'app_section_role__app_section__name',
            'app_section_role__role__name',
        )


class AppSectionRoleModel(BaseCatalog, BaseAbstractCatalog):
    access_level = common_fields.CustomPositiveIntegerField(
        default=0,
        null=False,
        blank=False,
        verbose_name='Уровень доступа',
        help_text='0 - максимальный',
    )

    class Meta:
        verbose_name = _('Роль раздела')
        verbose_name_plural = _('Роли раздела')

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        return serializers.AppSectionRoleSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()
        app_section_code = request.query_params.get('app_section')
        if not app_section_code:
            return qs.none()
        qs = qs.filter(app_sections=app_section_code)
        return qs.order_by('sort', 'name',)


class AppSectionRoleThroughModel(BaseAbstractModel):
    app_section = common_fields.CustomForeignKey(
        to='contractor_permissions.AppSectionModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Секция приложения'),
        related_name='app_section_roles_through',
    )
    role = common_fields.CustomForeignKey(
        to='contractor_permissions.AppSectionRoleModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='app_section_roles_through',
        verbose_name=_('Роль'),
    )
    routes_meta = models.JSONField(
        default=dict,
        blank=True,
    )
    permission_type = common_fields.CustomForeignKey(
        to='contractor_permissions.ContractorPermissionTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Вид разрешения',
        null=True,
        blank=True,
        related_name='app_section_roles_through'
    )

    class Meta:
        verbose_name = _('Роль раздела')
        verbose_name_plural = _('Роли раздела')
        unique_together = (('app_section', 'role',),)

    def __str__(self):
        return f"{self.app_section.name} {self.role.name}"
