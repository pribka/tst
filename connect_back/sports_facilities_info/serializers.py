from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.cache import cache
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from common import validators as common_validators
from common.models import File
from common.utils import get_serialized_attachments
from common.catalogs import serializers as catalog_serializers
from common.accounting_catalogs.serializers import CachedKATOCodesModelSerializer
from common.serializers import CachedBaseModelSerializer, CachedBaseCatalogSerializer

from users.serializers import CachedAppUserSerializer

from gallery.serializers import GalleryModelListSerializer

from pvh.serializers import PVHWriteMixin, PVHReadMixin
from . import models


class SportFacilityTypeModelParentSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityTypeModel
        fields = (
            'id',
            'name',
            'code',
            'full_name',
            'parent'
        )

    def get_parent(self, instance):
        if instance.parent:
            return SportFacilityTypeModelParentSerializer(instance.parent).data
        else:
            return None


class SportFacilityTypeModelSerializer(serializers.ModelSerializer):
    is_leaf = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityTypeModel
        fields = (
            'id',
            'name',
            'code',
            'full_name',
            'is_leaf',
        )

    def get_is_leaf(self, instance):
        try:
            is_leaf = instance.is_leaf
        except AttributeError:
            is_leaf = not instance.children.all().exists()
        return is_leaf


class OwnershipFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityOwnershipFormModel
        fields = (
            'id',
            'name',
            'code',
        )


class HeatingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityHeatingTypeModel
        fields = (
            'id',
            'name',
            'code',
        )


class SportFacilityStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
            'hex_color',
            'btn_title'
        )


class SportFacilityPurposeModelParentSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityPurposeModel
        fields = (
            'id',
            'name',
            'code',
            'full_name',
            'parent',
        )

    def get_parent(self, instance):
        if instance.parent:
            return SportFacilityPurposeModelParentSerializer(instance.parent).data
        else:
            return None


class SportFacilityPurposeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityPurposeModel
        fields = (
            'id',
            'name',
            'code',
            'full_name'
        )


class SportFacilityInfoForPointsSerializer(serializers.ModelSerializer):
    location_point = catalog_serializers.LocationPointSerializer()
    image = serializers.SerializerMethodField()
    facility_type = SportFacilityTypeModelSerializer()

    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
            'name',
            'location_point',
            'image',
            'facility_type',
        )

    def get_image(self, instance):
        image = list(instance.gallery.all())
        if image:
            return GalleryModelListSerializer(image[0]).data
        return None


class SportFacilityInfoModelListSerializer(serializers.ModelSerializer):
    status = CachedBaseCatalogSerializer(
        serializer_class=SportFacilityStatusSerializer,
        model=models.SportFacilityStatusModel,
        source='status_id'
    )
    facility_type = CachedBaseCatalogSerializer(
        serializer_class=SportFacilityTypeModelSerializer,
        model=models.SportFacilityTypeModel,
        source='facility_type_id'
    )
    purpose = CachedBaseCatalogSerializer(
        serializer_class=SportFacilityPurposeModelSerializer,
        model=models.SportFacilityPurposeModel,
        source='purpose_id'
    )
    ownership_form = CachedBaseCatalogSerializer(
        serializer_class=OwnershipFormSerializer,
        model=models.SportFacilityOwnershipFormModel,
        source='ownership_form_id'
    )
    organization = catalog_serializers.ContractorModelByIdSerializer()
    location = CachedKATOCodesModelSerializer(source='location_id')
    location_point = catalog_serializers.LocationPointSerializer()
    author = CachedAppUserSerializer(source='author_id')
    image = serializers.SerializerMethodField()
    repub_comp = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
            'author',
            'image',
            'status',
            'name',
            'facility_type',
            'purpose',
            'location',
            'organization',
            'building_year',
            'ownership_form',
            'owner_name',
            'owner_bin',
            'bandwidth',
            'area',
            'storeys_number',
            'is_countryside',
            'location_point',
            'repub_comp',
        )

    def get_image(self, instance):
        image = list(instance.gallery.all())
        if image:
            return GalleryModelListSerializer(image[0]).data
        return None

    def get_repub_comp(self, instance):
        repub_comp = instance.sport_facility_m2m_sport_types.filter(repub_comp=True).exists()
        return repub_comp


class SportFacilityInfoModelDetailSerializer(serializers.ModelSerializer):
    status = SportFacilityStatusSerializer()
    facility_type = SportFacilityTypeModelParentSerializer()
    purpose = SportFacilityPurposeModelParentSerializer()
    ownership_form = OwnershipFormSerializer()
    heating_type = HeatingTypeSerializer()
    organization = catalog_serializers.ContractorModelByIdSerializer()
    location = CachedKATOCodesModelSerializer(source='location_id')
    location_point = catalog_serializers.LocationPointSerializer()
    author = CachedAppUserSerializer(source='author_id')
    sport_types = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    repub_comp = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
            'author',
            'image',
            'status',
            'name',
            'facility_type',
            'purpose',
            'location',
            'organization',
            'building_year',
            'ownership_form',
            'heating_type',
            'staff_quantity',
            'has_ramp',
            'has_access_to_all_floors',
            'has_access_elevator',
            'has_equipped_bathrooms',
            'owner_name',
            'owner_bin',
            'bandwidth',
            'area',
            'storeys_number',
            'is_countryside',
            'location_point',
            'sport_types',
            'repub_comp',
        )

    def get_sport_types(self, instance):
        sport_types = instance.sport_facility_m2m_sport_types.all()
        if sport_types:
            return SportFacilityInfoM2MSportTypeModelListSerializer(sport_types, many=True).data
        else:
            return None

    def get_image(self, instance):
        image = list(instance.gallery.all())
        if image:
            return GalleryModelListSerializer(image[0]).data
        return None

    def get_repub_comp(self, instance):
        try:
            repub_comp = bool(instance.repub_comp)
        except AttributeError:
            repub_comp = instance.sport_facility_m2m_sport_types.filter(repub_comp=True).exists()
        return repub_comp


class SportFacilityInfoModelCreateSerializer(serializers.ModelSerializer):
    area = serializers.DecimalField(
        allow_null=True,
        decimal_places=1,
        max_digits=12,
        required=False,
        validators=(common_validators.MinValueOrNoneValidator(0),)
    )
    bandwidth = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=(common_validators.MinValueOrNoneValidator(0),)
    )
    storeys_number = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=(common_validators.MinValueOrNoneValidator(0),)
    )
    building_year = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=(
            common_validators.MinValueOrNoneValidator(1800),
            common_validators.MaxCurrentYearValidator(3000),
        )
    )

    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
            'name',
            'facility_type',
            'purpose',
            'location',
            'organization',
            'building_year',
            'ownership_form',
            'heating_type',
            'staff_quantity',
            'has_ramp',
            'has_access_to_all_floors',
            'has_access_elevator',
            'has_equipped_bathrooms',
            'owner_name',
            'owner_bin',
            'bandwidth',
            'area',
            'storeys_number',
            'is_countryside',
        )

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            location_point_dict = self.initial_data.get('location_point')
            if location_point_dict:
                location_point_dict['related_object'] = str(instance.pk)
                location_point_serializer = catalog_serializers.LocationPointCreateSerializer(
                    data=location_point_dict,
                    context=self.context
                )
                location_point_serializer.is_valid(raise_exception=True)
                location_point_serializer.save()
            sport_types = self.initial_data.get('sport_types')
            if sport_types:
                for each in sport_types:
                    each['sport_facility_info'] = str(instance.pk)
                    m2m_serializer = SportFacilityInfoM2MSportTypeModelCreateSerializer(data=each)
                    m2m_serializer.is_valid(raise_exception=True)
                    m2m_serializer.save()
        return instance


class SportFacilityInfoModelUpdateSerializer(serializers.ModelSerializer):
    area = serializers.DecimalField(
        allow_null=True,
        decimal_places=1,
        max_digits=12,
        required=False,
        validators=(common_validators.MinValueOrNoneValidator(0),)
    )
    bandwidth = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=(common_validators.MinValueOrNoneValidator(0),)
    )
    storeys_number = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=(common_validators.MinValueOrNoneValidator(0),)
    )
    building_year = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=(
            common_validators.MinValueOrNoneValidator(1800),
            common_validators.MaxCurrentYearValidator(3000),
        )
    )

    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
            'name',
            'facility_type',
            'purpose',
            'location',
            'organization',
            'building_year',
            'ownership_form',
            'heating_type',
            'staff_quantity',
            'has_ramp',
            'has_access_to_all_floors',
            'has_access_elevator',
            'has_equipped_bathrooms',
            'owner_name',
            'owner_bin',
            'bandwidth',
            'area',
            'storeys_number',
            'is_countryside',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if 'location_point' in self.initial_data:
                location_point_dict = self.initial_data.get('location_point')
                old_location_point = instance.location_point
                if location_point_dict:
                    location_point_dict['related_object'] = str(instance.pk)
                    location_point_serializer = catalog_serializers.LocationPointCreateSerializer(
                        data=location_point_dict,
                        context=self.context
                    )
                    location_point_serializer.is_valid(raise_exception=True)
                    location_point_serializer.save()
                if old_location_point:
                    old_location_point.delete()
            sport_types = self.initial_data.get('sport_types')
            new_sport_types = list()
            if sport_types is not None:
                old_sport_types = set(instance.sport_facility_m2m_sport_types.all().values_list('sport_type_id', flat=True))
                for each in sport_types:
                    try:
                        sport_type_m2m = instance.sport_facility_m2m_sport_types.get(
                            sport_type_id=each.get('sport_type'),
                            sport_facility_info=instance
                        )
                    except (ObjectDoesNotExist, ValidationError):
                        each['sport_facility_info'] = str(instance.pk)
                        sport_type_serializer = SportFacilityInfoM2MSportTypeModelCreateSerializer(data=each)
                        sport_type_serializer.is_valid(raise_exception=True)
                        sport_type_serializer.save()
                    else:
                        sport_type_serializer = SportFacilityInfoM2MSportTypeModelUpdateSerializer(
                            instance=sport_type_m2m,
                            data=each
                        )
                        sport_type_serializer.is_valid(raise_exception=True)
                        sport_type_serializer.save()
                    new_sport_types.append(each['sport_type'])
                different_sport_types = old_sport_types.difference(set(new_sport_types))
                delete_sport_types = instance.sport_facility_m2m_sport_types.filter(
                    sport_type_id__in=different_sport_types
                )
                for each in delete_sport_types:
                    each.delete()
        return instance


class SportFacilityStatusStatisticsSerializer(serializers.Serializer):
    status = serializers.SerializerMethodField()
    count = serializers.IntegerField()

    def get_status(self, instance):
        if instance['status'] == 'total':
            result = {
                'code': 'total',
                'name': _('Все объекты')}
        else:
            status = models.SportFacilityStatusModel.objects.get(code=instance['status'])
            result = SportFacilityStatusSerializer(status).data
        return result


class SportFacilityUpdateStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
            'status',
        )

    def update(self, instance, validated_data):
        old_status_code = instance.status_id
        new_status_code = validated_data.get('status').code
        if not old_status_code == new_status_code:
            instance.status = validated_data.get('status')
            instance.save()
        return instance


class SportTypeCategorySerializer(serializers.ModelSerializer):
    is_leaf = serializers.SerializerMethodField()

    class Meta:
        model = models.SportTypeCategoryModel
        fields = (
            'id',
            'code',
            'name',
            'is_leaf'
        )

    def get_is_leaf(self, instance):
        return instance.is_leaf_node()


class SportTypeCategoryDetailSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = models.SportTypeCategoryModel
        fields = (
            'id',
            'code',
            'name',
            'parent',
        )

    def get_parent(self, instance):
        if instance.parent:
            return SportTypeCategoryDetailSerializer(instance.parent).data
        else:
            return None


class SportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportTypeModel
        fields = (
            'id',
            'name',
            'code',
        )


class SportTypeDetailSerializer(serializers.ModelSerializer):
    category = SportTypeCategoryDetailSerializer()

    class Meta:
        model = models.SportTypeModel
        fields = (
            'id',
            'name',
            'code',
            'category',
        )


class SportFacilityInfoM2MSportTypeModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityInfoM2MSportTypeModel
        fields = (
            'id',
            'sport_facility_info',
            'sport_type',
            'repub_comp'
        )


class SportFacilityInfoM2MSportTypeModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityInfoM2MSportTypeModel
        fields = (
            'id',
            'repub_comp'
        )


class SportFacilityInfoM2MSportTypeModelListSerializer(serializers.ModelSerializer):
    sport_type = SportTypeDetailSerializer()

    class Meta:
        model = models.SportFacilityInfoM2MSportTypeModel
        fields = (
            'id',
            'sport_type',
            'repub_comp'
        )


# Табличная часть Строения/помещения
class SportFacilityBuildingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityInfoModel
        fields = (
            'id',
        )

    def update(self, instance, validated_data):
        from common.utils import set_tabular_parts
        instance = super().update(instance, validated_data)
        set_tabular_parts(self, instance)
        return instance

    def to_representation(self, instance):
        from common.utils import to_representation_tabular_parts
        data = super().to_representation(instance)
        data = to_representation_tabular_parts(self, instance, data)
        return data


class TPSportBuildingWriteSerializer(PVHWriteMixin, serializers.ModelSerializer):
    class Meta:
        model = models.TPSportFacilityBuildingModel
        fields = (
            'id',
            'owner',
            'name',
            'purpose_type'
            # 'purpose',
            # 'building_type',
        )

    def to_internal_value(self, data):
        try:
            purpose_type = models.SportBuildingPurposeTypeThroughModel.objects.get(
                purpose_id=self.initial_data.get('purpose'),
                building_type_id=self.initial_data.get('building_type', None)
            )
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError(detail='Пара Назначение и Тип не существует.')
        data = super().to_internal_value(data)
        data['purpose_type'] = purpose_type
        return data


class SportPurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportBuildingPurposeModel
        fields = (
            'id',
            'name',
            'code',
            'sort',
        )


class SportBuildingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportBuildingTypeModel
        fields = (
            'id',
            'name',
            'code',
        )


class PurposeTypeSerializer(serializers.ModelSerializer):
    purpose = SportFacilityPurposeModelSerializer()
    building_type = SportBuildingTypeSerializer()

    class Meta:
        model = models.SportBuildingPurposeTypeThroughModel
        fields = (
            'purpose',
            'building_type',
        )


class TPSportBuildingListSerializer(PVHReadMixin, serializers.ModelSerializer):
    purpose_type = PurposeTypeSerializer()

    class Meta:
        model = models.TPSportFacilityBuildingModel
        fields = (
            'id',
            'name',
            'purpose_type',
        )


# Кружки/секции
class TPSportSectionListSerializer(serializers.ModelSerializer):
    sport_type = SportTypeDetailSerializer()

    class Meta:
        model = models.TPSportSectionModel
        fields = (
            'id',
            'sport_type',
            'sections_quantity',
            'members_quantity',
            'coaches_quantity'
        )


class TPSportSectionWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TPSportSectionModel
        fields = (
            'id',
            'owner',
            'sport_type',
        )


# группы секции
class SportGroupTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportGroupTypeCatalog
        fields = (
            'id',
            'code',
            'name',
            'name_plural',
        )


class SportSectionGroupsListSerializer(serializers.ModelSerializer):
    sport_group_type = SportGroupTypeSerializer()

    class Meta:
        model = models.SportSectionGroupsModel
        fields = (
            'sport_group_type',
            'sections_quantity',
            'members_variable_quantity',
            'members_constant_quantity',
            'members_constant_female',
            'members_constant_before_17',
            'members_constant_before_18_19',
            'members_first_category',
            'members_kms',
            'members_ms',
        )


class SportSectionGroupsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportSectionGroupsModel
        fields = (
            'sections_quantity',
            'members_variable_quantity',
            'members_constant_quantity',
            'members_constant_female',
            'members_constant_before_17',
            'members_constant_before_18_19',
            'members_first_category',
            'members_kms',
            'members_ms',
        )


# Тренеры секции
class SportCoachTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportCoachTypeCatalog
        fields = (
            'id',
            'code',
            'name',
            'name_plural',
        )


class SportSectionCoachListSerializer(serializers.ModelSerializer):

    sport_coach_type = SportCoachTypeSerializer()

    class Meta:
        model = models.SportSectionCoachesModel
        fields = (
            'sport_coach_type',
            'coaches_quantity',
            'coaches_female',
            'coaches_higher_education',
            'coaches_middle_education',
        )


class SportSectionCoachUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportSectionCoachesModel
        fields = (
            'coaches_quantity',
            'coaches_female',
            'coaches_higher_education',
            'coaches_middle_education',
        )


# Информация о ремонте
class SportFacilityRenovationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityRenovationTypeModel
        fields = (
            'id',
            'name',
            'code',
        )


class SportFacilityRenovationWorkTypeListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SportFacilityRenovationWorkTypeModel
        fields = (
            'id',
            'code',
            'full_name',
        )


class SportFacilityRenovationWorkTypeDetailSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityRenovationWorkTypeModel
        fields = (
            'id',
            'code',
            'parent',
            'full_name',
        )

    def get_parent(self, instance):
        parent = instance.parent
        if parent:
            return SportFacilityRenovationWorkTypeDetailSerializer(parent).data
        else:
            return None


class SportFacilityRenovationWorkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityRenovationWorkModel
        fields = (
            'id',
            'work_type',
            'renovation_info',
        )


class SportFacilityRenovationWorkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SportFacilityRenovationWorkModel
        fields = (
            'id',
            'work_type',
        )


class SportFacilityRenovationWorkDetailSerializer(serializers.ModelSerializer):
    work_type = SportFacilityRenovationWorkTypeDetailSerializer()

    class Meta:
        model = models.SportFacilityRenovationWorkModel
        fields = (
            'id',
            'work_type',
        )


class SportFacilityRenovationWorkListSerializer(serializers.ModelSerializer):
    work_type = SportFacilityRenovationWorkTypeListSerializer()

    class Meta:
        model = models.SportFacilityRenovationWorkModel
        fields = (
            'id',
            'work_type',
        )


class SportFacilityRenovationInfoCreateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=False, required=True)
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.SportFacilityRenovationInfoModel
        fields = (
            'id',
            'sport_facility',
            'renovation_type',
            'renovation_date',
            'amount',
            'comment',
            'attachments',
        )

    def create(self, validated_data):
        with transaction.atomic():
            attachments = validated_data.pop('attachments', None)
            instance = super().create(validated_data)
            works = self.initial_data.get('works')
            if works:
                for each in works:
                    each['renovation_info'] = str(instance.pk)
                    serializer = SportFacilityRenovationWorkCreateSerializer(data=each)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
            if attachments:
                instance.attachments.set(attachments)
        return instance


class SportFacilityRenovationInfoUpdateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=False, required=True)
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.SportFacilityRenovationInfoModel
        fields = (
            'id',
            'renovation_type',
            'renovation_date',
            'amount',
            'comment',
            'attachments',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            attachments = validated_data.pop('attachments', None)
            works = self.initial_data.get('works')
            if works is not None:
                old_works = set(
                    instance.renovation_works.all().values_list('work_type', flat=True)
                )
                new_works = []
                for each in works:
                    try:
                        work = instance.renovation_works.get(
                            work_type_id=each.get('work_type'),
                            renovation_info=instance,
                        )
                    except (ObjectDoesNotExist, ValidationError):
                        each['renovation_info'] = str(instance.pk)
                        work_serializer = SportFacilityRenovationWorkCreateSerializer(data=each)
                        work_serializer.is_valid(raise_exception=True)
                        work_serializer.save()
                    else:
                        work_serializer = SportFacilityRenovationWorkUpdateSerializer(
                            instance=work,
                            data=each
                        )
                        work_serializer.is_valid(raise_exception=True)
                        work_serializer.save()
                    new_works.append(each['work_type'])
                different_works = old_works.difference(set(new_works))
                delete_works = instance.renovation_works.filter(
                    work_type_id__in=different_works
                )
                for each in delete_works:
                    each.delete()
            if attachments is not None:
                old_attachments = instance.files.all()
                new_attachments = []
                for each in attachments:
                    if each in old_attachments:
                        pass
                    else:
                        new_attachment = instance.files.create(file=each)
                        new_attachments.append(new_attachment)
                delete_attachments = set(old_attachments).difference(set(new_attachments))
                for each in delete_attachments:
                    each.delete()
        return instance


class SportFacilityRenovationInfoListSerializer(serializers.ModelSerializer):
    renovation_type = SportFacilityRenovationSerializer()
    works = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityRenovationInfoModel
        fields = (
            'id',
            'renovation_type',
            'renovation_date',
            'comment',
            'amount',
            'works',
            'attachments',
        )

    def get_works(self, instance):
        works = instance.renovation_works.all()
        if works:
            return SportFacilityRenovationWorkDetailSerializer(works, many=True).data
        else:
            return None

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class SportFacilityRenovationInfoDetailSerializer(serializers.ModelSerializer):
    renovation_type = SportFacilityRenovationSerializer()
    works = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = models.SportFacilityRenovationInfoModel
        fields = (
            'id',
            'renovation_type',
            'renovation_date',
            'comment',
            'amount',
            'works',
            'attachments',
        )

    def get_works(self, instance):
        works = instance.renovation_works.all()
        if works:
            return SportFacilityRenovationWorkDetailSerializer(works, many=True).data
        else:
            return None

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)
