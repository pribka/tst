import datetime

from django.db import models
from django.db.models import Q, Prefetch, Count
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from rest_framework import exceptions as drf_exceptions

from mptt.models import MPTTModel, TreeForeignKey, TreeManager

from model_utils import FieldTracker

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from common import models as common_models
from common import fields as common_fields
from common import validators as common_validators

from common.accounting_catalogs.fields import LocationFilterFakeField

from change_history import utils as change_history_utils

from gallery.models import GalleryModel

from contractor_permissions.utils import contractors_where_user_has_permission, \
    users_that_have_permission_in_contractors
from users.utils import get_descendants_departments_related_organizations, \
    get_ancestor_departments_related_organizations

from . import fields


class SportFacilityInfoModel(common_models.BaseModel):
    tracker = FieldTracker(
        fields=(
            'name',
            'status_id',
            'facility_type_id',
            'is_countryside',
            'location_id',
            'organization_id',
            'owner_name',
            'owner_bin',
            'purpose_id',
            'ownership_form_id',
            'building_year',
            'area',
            'bandwidth',
            'storeys_number',
            'update_requested',
        )
    )
    m2m_track_fields = ('attachments', 'gallery', 'location_points')
    track_prefix = 'sport_facility_info'

    status = common_fields.CustomForeignKey(
        to='SportFacilityStatusModel',
        to_field='code',
        null=False,
        default='draft',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус')
    )
    name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Название'),
    )
    facility_type = common_fields.CustomForeignKey(
        to='SportFacilityTypeModel',
        to_field='code',
        null=True,
        blank=False,
        related_name='sports_facilities_info',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тип объекта'),
    )

    is_countryside = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Сельская местность'),
    )

    location = common_fields.CustomForeignKey(
        to='accounting_catalogs.KATOCodesModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Местоположение'),
        related_name='sports_facilities_info'
    )

    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация')
    )

    owner_name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Наименование организации собственника')
    )

    owner_bin = common_fields.CustomCharField(
        max_length=12,
        null=False,
        blank=True,
        default='',
        verbose_name=_('БИН организации собственника'),
        validators=(common_validators.iin_validator,)
    )

    purpose = common_fields.CustomForeignKey(
        to='SportFacilityPurposeModel',
        to_field='code',
        null=True,
        blank=True,
        related_name='sports_facilities_info',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Назначение'),
    )

    ownership_form = common_fields.CustomForeignKey(
        to='SportFacilityOwnershipFormModel',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='sports_facilities_info',
        verbose_name=_('Форма собственности')
    )

    building_year = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        validators=(
            common_validators.MinValueOrNoneValidator(1800, _('Минимальный год постройки 1800')),
            common_validators.MaxCurrentYearValidator(3000),
        ),
        verbose_name=_('Год постройки'),
    )

    heating_type = common_fields.CustomForeignKey(
        to='SportFacilityHeatingTypeModel',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='sports_facilities_info',
        verbose_name=_('Система отопления')
    )

    staff_quantity = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Численность обслуживающего персонала')
    )

    # Доступность лиц с ограниченными возможностями
    has_ramp = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Наличие пандуса')
    )
    has_access_to_all_floors = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Наличие доступности на все этажи сооружения')
    )
    has_access_elevator = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Доступность лифтов')
    )
    has_equipped_bathrooms = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Наличие оборудованных санузлов')
    )

    area = common_fields.CustomDecimalField(
        decimal_places=1,
        max_digits=12,
        null=True,
        blank=True,
        verbose_name=_('Площадь'),
        validators=(common_validators.MinValueOrNoneValidator(0, _('Площадь не может быть ниже или равна нулю')),)
    )

    bandwidth = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Пропускная способность')
    )

    storeys_number = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Этажность'),
        validators=(
            common_validators.MinValueOrNoneValidator(1, _('Этажность не может быть ниже единицы')),
            common_validators.MaxValueOrNoneValidator(100, 'Этажность не может быть выше ста'),
        )
    )

    update_requested = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Запрошено изменение')
    )

    sport_types = models.ManyToManyField(
        to='SportTypeModel',
        through='SportFacilityInfoM2MSportTypeModel',
        through_fields=('sport_facility_info', 'sport_type'),
        verbose_name=_('Культивируемые виды спорта')
    )

    location_filter = LocationFilterFakeField()

    repub_comp_filter = fields.RepubCompFilterField()

    class Meta:
        verbose_name = _('Спортивный объект')
        verbose_name_plural = _('Спортивные объекты')

    def save(self, *args, **kwargs):
        if self.status and self.status.code in ('on_rework', 'draft'):
            self.update_requested = False
        return super().save(*args, **kwargs)

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        if 'name' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__name',
                changed_fields['name'],
                self.name,
            )
        if 'status_id' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['status_id'],
                SportFacilityStatusModel,
                'status',
                'sport_facility_info',
                action_date,
            )
        if 'facility_type_id' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['facility_type_id'],
                SportFacilityTypeModel,
                'facility_type',
                'sport_facility_info',
                action_date,
            )

        if 'is_countryside' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'sport_facility_info__is_countryside',
                self.is_countryside,
            )
        if 'location_id' in changed_fields:
            location_after = self.location
            if location_after:
                location_id_after = location_after.pk
            else:
                location_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'sport_facility_info__location',
                changed_fields['location_id'],
                location_id_after,
            )
        if 'organization_id' in changed_fields:
            organization_after = self.organization
            if organization_after:
                organization_id_after = organization_after.pk
            else:
                organization_id_after = None
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'sport_facility_info__organization',
                changed_fields['organization_id'],
                organization_id_after,
            )
        if 'owner_name' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__owner_name',
                changed_fields['owner_name'],
                self.owner_name,
            )
        if 'owner_bin' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__owner_bin',
                changed_fields['owner_bin'],
                self.owner_bin,
            )
        if 'purpose_id' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['purpose_id'],
                SportFacilityPurposeModel,
                'purpose',
                'sport_facility_info',
                action_date,
            )
        if 'ownership_form_id' in changed_fields:
            change_history_utils.create_update_catalog_code(
                self,
                changed_fields['ownership_form_id'],
                SportFacilityOwnershipFormModel,
                'ownership_form',
                'sport_facility_info',
                action_date,
            )
        if 'building_year' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__building_year',
                changed_fields['building_year'],
                self.building_year,
            )
        if 'area' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__area',
                changed_fields['area'],
                self.area,
            )
        if 'bandwidth' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__bandwidth',
                changed_fields['bandwidth'],
                self.bandwidth,
            )
        if 'storeys_number' in changed_fields:
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'sport_facility_info__storeys_number',
                changed_fields['storeys_number'],
                self.storeys_number,
            )
        if 'update_requested' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'sport_facility_info__update_requested',
                self.update_requested,
            )

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_sport_buildings': TPSportFacilityBuildingModel,
        }

    @classmethod
    def get_table_columns(cls):
        return ('organization',
                'status',
                'facility_type',
                'purpose',
                'ownership_form',
                'building_year',
                'location_filter',
                'area',
                'bandwidth',
                'storeys_number',
                'is_countryside',
                'repub_comp_filter',
                )

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (SportFacilityInfoModelListSerializer,
                                  SportFacilityInfoModelDetailSerializer,
                                  SportFacilityInfoModelCreateSerializer,
                                  SportFacilityInfoModelUpdateSerializer,
                                  TPSportBuildingWriteSerializer,
                                  TPSportBuildingListSerializer,
                                  TPSportSectionListSerializer,
                                  TPSportSectionWriteSerializer)
        if action == 'list':
            return SportFacilityInfoModelListSerializer
        elif action == 'retrieve':
            return SportFacilityInfoModelDetailSerializer
        elif action == 'create':
            return SportFacilityInfoModelCreateSerializer
        elif action in ('update', 'partial_update',):
            return SportFacilityInfoModelUpdateSerializer
        elif action in ('create_building', 'update_building'):
            return TPSportBuildingWriteSerializer
        elif action == 'get_building':
            return TPSportBuildingListSerializer
        elif action in ('create_section', 'update_section',):
            return TPSportSectionWriteSerializer
        elif action == 'get_section':
            return TPSportSectionListSerializer
        else:
            return SportFacilityInfoModelListSerializer

    def get_update_permission(self, request):
        if self.status.code not in ('draft', 'on_rework',):
            return False
        return self.im_creator(request.user.profile.pk)

    def get_detail_permission(self, request) -> bool:
        profile = request.user.profile
        if profile.is_support:
            return True
        status_code = self.status.code
        if status_code == 'approved':
            return True
        ancestors = get_ancestor_departments_related_organizations((self.organization.pk,), include_self=True,)
        if self.im_creator(profile.pk, ancestors):
            return True
        if status_code not in ('draft',):
            return self.im_admin(profile.pk, ancestors)
        else:
            return False

    STATUS_TRANSITION_MATRIX = {
        'create_sport_facility': {
            'draft': ('on_check',),
            'on_rework': ('on_check', 'draft',),
        },
        'admin_sport_facility': {
            'on_check': ('on_rework', 'approved',),
            'approved': ('on_rework', 'archive',),
            'on_rework': ('approved', 'archive',),
        }
    }

    def get_update_status_permission(self, request) -> bool:
        new_status_code = request.data.get('status')
        if not new_status_code:
            return False
        if new_status_code in self.get_available_statuses(request):
            return True
        else:
            return False

    def get_available_statuses(self, request):
        available_statuses = list()
        current_status_code = self.status.code
        profile_id = request.user.profile.pk
        ancestors = get_ancestor_departments_related_organizations((self.organization.pk,), include_self=True, )
        if self.im_creator(profile_id, ancestors=ancestors):
            available_statuses = available_statuses + list(
                self.STATUS_TRANSITION_MATRIX.get('create_sport_facility', dict()).get(current_status_code, list())
            )
        if self.im_admin(profile_id, ancestors=ancestors):
            available_statuses = available_statuses + list(
                self.STATUS_TRANSITION_MATRIX.get('admin_sport_facility', dict()).get(current_status_code, list())
            )
        return set(available_statuses)

    def get_delete_permission(self, request) -> bool:
        profile = request.user.profile
        if profile.is_support:
            return True
        return self.status.code == 'draft' and self.im_creator(profile.pk)

    def get_request_update_permission(self, request) -> bool:
        if self.update_requested:
            return False
        if self.status.code == 'approved' and self.im_creator(request.user.profile.pk):
            return True
        return False

    def im_creator(self, profile_id, ancestors=None):
        if ancestors is None:
            contractor_id = self.organization.pk
            ancestors = get_ancestor_departments_related_organizations((contractor_id,), include_self=True, )
        return not ancestors.isdisjoint(
            set(
                contractors_where_user_has_permission(
                    profile_id,
                    ('create_sport_facility', 'admin_sport_facility'),
                    None
                )
            )
        )

    def get_creators(self):
        contractor_id = self.organization.pk
        ancestors = get_ancestor_departments_related_organizations((contractor_id,), include_self=True)
        return users_that_have_permission_in_contractors(
            ancestors,
            ('create_sport_facility', 'admin_sport_facility'),
            None
        )

    def im_admin(self, profile_id, ancestors=None):
        if ancestors is None:
            contractor_id = self.organization.pk
            ancestors = get_ancestor_departments_related_organizations((contractor_id,), include_self=True, )
        return not ancestors.isdisjoint(
            set(contractors_where_user_has_permission(profile_id, 'admin_sport_facility', None))
        )

    def get_admins(self):
        contractor_id = self.organization.pk
        ancestors = get_ancestor_departments_related_organizations((contractor_id,), include_self=True)
        return users_that_have_permission_in_contractors(ancestors, 'admin_sport_facility', None)

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(
            is_active=True,
        ).select_related(
            'organization',
        ).prefetch_related(
            'location_points',
            Prefetch('gallery', queryset=GalleryModel.objects.filter(is_main=True).select_related('file')),
        ).order_by('-created_at')

        if request:
            profile = request.user.profile
            if profile.is_support:
                return qs
            organizations_create = contractors_where_user_has_permission(
                profile.pk,
                ('create_sport_facility', 'admin_sport_facility',),
                None
            )
            organizations_descendants_create = get_descendants_departments_related_organizations(
                organizations_create,
                include_self=True
            )
            organizations_admin = contractors_where_user_has_permission(profile.pk, 'admin_sport_facility', None)
            organizations_descendants_admin = get_descendants_departments_related_organizations(
                organizations_admin,
                include_self=True
            )
            qs = qs.filter(
                Q(
                    organization_id__in=organizations_descendants_create,
                    status_id__in=('draft', 'on_check', 'on_rework', 'archive')
                ) |
                Q(
                    organization_id__in=organizations_descendants_admin,
                    status_id__in=('on_check', 'on_rework', 'archive')
                ) |
                Q(status_id='approved', )
            ).distinct()
        else:
            qs = qs.filter(status_id='approved')
        return qs

    @property
    def location_point(self):
        point_list = list(self.location_points.all())
        if point_list:
            return point_list[0]
        else:
            return None
    @property
    def admin_area(self):
        return getattr(self.location_point, 'admin_area', '')


class TPSportFacilityBuildingModel(common_models.BaseModel, common_models.BaseAbstractTabularPart):
    owner = common_fields.CustomForeignKey(
        to='SportFacilityInfoModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Спортивный объект'),
        related_name='tp_sport_buildings',
    )
    purpose_type = common_fields.CustomForeignKey(
        to='SportBuildingPurposeTypeThroughModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Назначение тип'),
        null=True,
        blank=False,
        related_name='tp_sport_buildings',
    )
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        verbose_name=_('Наименование')
    )

    class Meta:
        verbose_name = _('Строение/помещение')
        verbose_name_plural = _('Строения/помещения')

    def __str__(self):
        return f'{self.purpose_type} {self.name}'

    @property
    def purpose(self):
        return self.purpose_type.purpose

    @property
    def building_type(self):
        return self.purpose_type.building_type

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPSportBuildingWriteSerializer, TPSportBuildingListSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPSportBuildingWriteSerializer
        elif action in ['list', 'retrieve']:
            return TPSportBuildingListSerializer
        else:
            return TPSportBuildingListSerializer


class SportBuildingTechnicalConditionModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Техническое состояние помещения')
        verbose_name_plural = _('Технические состояния помещения')
        ordering = ('sort', 'name',)


class SportFacilityInfoM2MSportTypeModel(common_models.BaseAbstractModel):
    sport_facility_info = common_fields.CustomForeignKey(
        to='SportFacilityInfoModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Паспорт спортивного объекта',
        related_name='sport_facility_m2m_sport_types'
    )
    sport_type = common_fields.CustomForeignKey(
        to='SportTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Вид спорта',
        related_name='sport_facility_m2m_sport_types'
    )
    repub_comp = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Соответствует для проведения республиканских соревнований'
    )

    class Meta:
        verbose_name = _('Культивируемый вид спорта')
        verbose_name_plural = _('Культивируемые виды спорта')
        unique_together = (('sport_facility_info', 'sport_type',),)


class SportFacilityStatusModel(common_models.BaseAbstractCatalog, common_models.BaseCatalog):
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )
    hex_color = common_fields.CustomCharField(
        null=False,
        default='#ffffff',
        blank=True,
        max_length=7,
        verbose_name=_('Код цвета'),
        help_text='начинается с #: #ff00ff',
    )
    btn_title = common_fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=31,
        verbose_name=_('Название кнопки'),
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SportFacilityStatusSerializer
        return SportFacilityStatusSerializer

    class Meta:
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')


class SportFacilityTypeModel(common_models.BaseAbstractCatalog, common_models.BaseCatalog):
    parent = common_fields.CustomForeignKey(
        to='self',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='children',
        verbose_name=_('Родительский тип')
    )
    full_name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное наименование',
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        return qs.order_by('name',)

    class Meta:
        verbose_name = _('Тип спортивного объекта')
        verbose_name_plural = _('Типы спортивного объекта')


class SportFacilityPurposeModel(common_models.BaseAbstractCatalog, common_models.BaseCatalog):
    parent = common_fields.CustomForeignKey(
        to='self',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='children',
        verbose_name=_('Родительское назначение')
    )
    full_name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное наименование',
    )

    class Meta:
        verbose_name = _('Назначение спортивного объекта')
        verbose_name_plural = _('Назначения спортивного объекта')

    @classmethod
    def is_enum(cls):
        return True


class SportFacilityOwnershipFormModel(common_models.BaseAbstractCatalog, common_models.BaseCatalog):

    class Meta:
        verbose_name = _('Форма собственности')
        verbose_name_plural = _('Формы собственности')

    @classmethod
    def is_enum(cls):
        return True


class SportFacilityHeatingTypeModel(common_models.BaseAbstractCatalog, common_models.BaseCatalog):
    class Meta:
        verbose_name = _('Тип отопления')
        verbose_name_plural = _('Типы отопления')
        ordering = ('sort', 'name',)

    @classmethod
    def is_enum(cls):
        return True


class SportTypeCategoryModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog, MPTTModel):
    parent = TreeForeignKey(
        'self',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        related_name='children',
    )
    level = models.IntegerField(default=0)
    lft = models.IntegerField(default=0)
    rght = models.IntegerField(default=0)
    tree_id = models.IntegerField(default=0)
    full_name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное наименование'
    )
    objects = TreeManager()

    class Meta:
        verbose_name = _('Категория видов спорта')
        verbose_name_plural = _('Категории видов спорта')

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).order_by('sort', 'name', )
        if request:
            parent = request.query_params.get('parent')
            if parent:
                qs = qs.filter(parent_id=parent)
            else:
                qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.none()
        return qs

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SportTypeCategorySerializer, SportTypeCategoryDetailSerializer
        if action == 'retrieve':
            return SportTypeCategoryDetailSerializer
        return SportTypeCategorySerializer


class SportTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    category = common_fields.CustomForeignKey(
        to='SportTypeCategoryModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Категория'),
    )
    full_name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name='Полное наименование',
    )

    class Meta:
        verbose_name = _('Вид спорта')
        verbose_name_plural = _('Виды спорта')

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).order_by('sort', 'name', )
        if request:
            category_code = request.query_params.get('category')
            if category_code:
                try:
                    category = SportTypeCategoryModel.objects.get(code=category_code, is_active=True)
                except (SportTypeCategoryModel.DoesNotExist, ValidationError):
                    return qs
                category_descendants = category.get_descendants(include_self=True).values_list('code', flat=True)
                qs = qs.filter(category_id__in=category_descendants)
        return qs

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SportTypeSerializer, SportTypeDetailSerializer
        if action == 'retrieve':
            return SportTypeDetailSerializer
        return SportTypeSerializer


#  Информация о ремонте
class SportFacilityRenovationInfoModel(common_models.BaseModel):
    sport_facility = common_fields.CustomForeignKey(
        to='SportFacilityInfoModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='renovation_info',
        verbose_name=_('Спортивный объект')
    )
    renovation_type = common_fields.CustomForeignKey(
        to='SportFacilityRenovationTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='renovation_info',
        verbose_name=_('Вид ремонта')
    )
    renovation_date = common_fields.CustomDateField(
        null=True,
        blank=False,
        verbose_name=_('Дата ремонта')
    )
    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )
    amount = common_fields.CustomDecimalField(
        null=False,
        blank=False,
        default=0,
        decimal_places=2,
        max_digits=18,
        verbose_name=_('Стоимость'),
        validators=(MinValueValidator(0),)
    )

    works = models.ManyToManyField(
        'SportFacilityRenovationWorkTypeModel',
        through='SportFacilityRenovationWorkModel',
        through_fields=('renovation_info', 'work_type'),
        verbose_name=_('Виды ремонта'),
    )

    class Meta:
        verbose_name = _('Информация о ремонте')
        verbose_name_plural = _('Информация о ремонте')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SportFacilityRenovationInfoCreateSerializer, \
            SportFacilityRenovationInfoUpdateSerializer, SportFacilityRenovationInfoListSerializer, \
            SportFacilityRenovationInfoDetailSerializer
        if action == 'retrieve':
            return SportFacilityRenovationInfoDetailSerializer
        elif action == 'create':
            return SportFacilityRenovationInfoCreateSerializer
        elif action in ('update', 'partial_update',):
            return SportFacilityRenovationInfoUpdateSerializer
        else:
            return SportFacilityRenovationInfoListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        if request:
            sport_facility_qs = SportFacilityInfoModel.get_queryset(request).values_list('pk', flat=True)
            qs = cls.objects.filter(
                is_active=True,
                sport_facility_id__in=sport_facility_qs
            ).select_related(
                'renovation_type',
            ).prefetch_related(
                'renovation_works',
                'attachments__mime_type',
            ).order_by('-renovation_date')
            sport_facility_id = request.query_params.get('sport_facility')
            if sport_facility_id:
                qs = qs.filter(sport_facility_id=sport_facility_id)
        else:
            qs = cls.objects.none()
        return qs

    def get_detail_permission(self, request) -> bool:
        return self.sport_facility.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        return self.sport_facility.get_update_permission(request)

    def get_delete_permission(self, request) -> bool:
        return self.sport_facility.get_update_permission(request)


class SportFacilityRenovationTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    class Meta:
        verbose_name = _('Вид ремонта')
        verbose_name_plural = _('Виды ремонта')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SportFacilityRenovationSerializer
        return SportFacilityRenovationSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True,).order_by('sort', 'name',)


class SportFacilityRenovationWorkModel(common_models.BaseAbstractModel):
    renovation_info = common_fields.CustomForeignKey(
        to='SportFacilityRenovationInfoModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='renovation_works',
        verbose_name=_('Информация о ремонте'),
    )
    work_type = common_fields.CustomForeignKey(
        to='SportFacilityRenovationWorkTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='renovation_works',
        verbose_name=_('Вид работы')
    )

    class Meta:
        verbose_name = _('Работа по ремонту')
        verbose_name_plural = _('Работы по ремонту')
        unique_together = (('renovation_info', 'work_type',),)


class SportFacilityRenovationWorkTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    parent = common_fields.CustomForeignKey(
        to='self',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='children',
    )
    renovation_type = common_fields.CustomForeignKey(
        to='SportFacilityRenovationTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Вид ремонта'),
        related_name='renovation_types',
    )
    full_name = common_fields.CustomCharField(
        max_length=1024,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Наименование')
    )

    class Meta:
        verbose_name = _('Вид работы')
        verbose_name_plural = _('Виды работ')

    def __str__(self):
        return self.full_name[:100]

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import SportFacilityRenovationWorkTypeListSerializer, \
            SportFacilityRenovationWorkTypeDetailSerializer
        if action == 'retrieve':
            return SportFacilityRenovationWorkTypeDetailSerializer
        else:
            return SportFacilityRenovationWorkTypeListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True).order_by('sort', 'name',)
        if request:
            renovation_type = request.query_params.get('renovation_type')
            parent = request.query_params.get('parent')
            if not renovation_type and not parent:
                qs = qs.none()
            if renovation_type and not parent:
                qs = qs.filter(renovation_type_id=renovation_type, parent__isnull=True)
            if not renovation_type and parent:
                qs = qs.filter(parent_id=parent)
            if renovation_type and parent:
                qs = qs.filter(renovation_type_id=renovation_type, parent_id=parent)
        return qs


class SportBuildingPurposeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    building_types = models.ManyToManyField(
        to='SportBuildingTypeModel',
        through='SportBuildingPurposeTypeThroughModel',
        through_fields=('purpose', 'building_type'),
        verbose_name=_('Тип помещения'),
        related_name='purposes',
    )

    class Meta:
        verbose_name = _('Назначение помещения')
        verbose_name_plural = _('Назначения помещения')
        ordering = ('sort', 'name',)


class SportBuildingTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Тип помещения')
        verbose_name_plural = _('Типы помещения')
        ordering = ('sort', 'name',)

    @classmethod
    def get_select_queryset(cls, request=None):
        qs = cls.get_queryset(request)
        if request:
            purpose = request.query_params.get('purpose')
            if purpose:
                qs = qs.filter(purposes=purpose)
        return qs


class SportBuildingPurposeTypeThroughModel(common_models.BaseAbstractModel):
    purpose = common_fields.CustomForeignKey(
        to='SportBuildingPurposeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Назначение'),
        related_name='purpose_type_through'
    )
    building_type = common_fields.CustomForeignKey(
        to='SportBuildingTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тип помещения'),
        related_name='purpose_type_through'
    )

    class Meta:
        verbose_name = _('Связь назначение и тип помещения')
        verbose_name_plural = _('Связи назначение и тип помещения')
        unique_together = (('purpose', 'building_type',),)

    def __str__(self):
        return f'{self.purpose} {self.building_type}'


class SportBuildingFloorCoveringTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    class Meta:
        verbose_name = _('Тип покрытия пола')
        verbose_name_plural = _('Типы покрытия пола')
        ordering = ('sort', 'name',)


# Кружки/секции
class TPSportSectionModel(common_models.BaseModel, common_models.BaseAbstractTabularPart):
    owner = common_fields.CustomForeignKey(
        to='SportFacilityInfoModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Спортивный объект'),
        related_name='tp_sport_sections',
    )

    sport_type = common_fields.CustomForeignKey(
        to='SportTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Вид спорта',
        related_name='sport_section'
    )
    sections_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество секций')
    )
    members_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество занимающихся')
    )
    coaches_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество тренеров')
    )

    class Meta:
        verbose_name = _('Кружок/секция')
        verbose_name_plural = _('Кружки/секции')

    def __str__(self):
        return f'{self.owner} {self.sport_type}'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPSportSectionWriteSerializer, TPSportSectionListSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPSportSectionWriteSerializer
        elif action in ['list', 'retrieve']:
            return TPSportSectionListSerializer
        else:
            return TPSportSectionListSerializer


class SportGroupTypeCatalog(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    name_plural = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Наименование во множественном числе')
    )

    class Meta:
        verbose_name = _('Тип группы')
        verbose_name_plural = _('Типы групп')
        ordering = ('sort', 'name',)


class SportSectionGroupsModel(common_models.BaseAbstractModel):
    owner = common_fields.CustomForeignKey(
        to='TPSportSectionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='sport_sections',
        verbose_name=_('Кружок/секция спортивного объекта')
    )
    sport_group_type = common_fields.CustomForeignKey(
        to='SportGroupTypeCatalog',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='sport_sections',
        verbose_name=_('Тип группы')
    )
    sections_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество секций')
    )
    members_variable_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Занимающихся переменного состава')
    )
    members_constant_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Занимающихся постоянного состава')
    )
    members_constant_female = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Лиц женского пола')
    )
    members_constant_before_17 = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('До 17 лет')
    )
    members_constant_before_18_19 = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('В возрасте 18-20')
    )
    members_first_category = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество спортсменов первого спортивного разряда')
    )
    members_kms = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество кандидатов в мастера спорта')
    )
    members_ms = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Количество мастеров спорта')
    )

    class Meta:
        verbose_name = _('Тип группы секции')
        verbose_name_plural = _('Типы групп секции')
        unique_together = (('owner', 'sport_group_type',),)


class SportCoachTypeCatalog(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    name_plural = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Наименование во множественном числе')
    )

    class Meta:
        verbose_name = _('Тип тренеров/преподавателей')
        verbose_name_plural = _('Типы тренеров/преподавателей')
        ordering = ('sort', 'name',)


class SportSectionCoachesModel(common_models.BaseAbstractModel):
    owner = common_fields.CustomForeignKey(
        to='TPSportSectionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='sport_coaches',
        verbose_name=_('Кружок/секция спортивного объекта')
    )
    sport_coach_type = common_fields.CustomForeignKey(
        to='SportCoachTypeCatalog',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='sport_coaches',
        verbose_name=_('Тип тренеров/преподавателей')
    )
    coaches_quantity = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Всего')
    )
    coaches_female = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Женщин')
    )
    coaches_higher_education = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('С высшим образованием')
    )
    coaches_middle_education = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Со средне-специальным образованием')
    )

    class Meta:
        verbose_name = _('Тип тренеров/преподавателей секции')
        verbose_name_plural = _('Тип тренеров/преподавателей секции')
        unique_together = (('owner', 'sport_coach_type',),)
