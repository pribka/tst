from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers

from django_q.tasks import async_task

from common.accounting_catalogs.models import KATOCodesModel
from common.accounting_catalogs.serializers import CachedKATOCodesModelSerializer
from common.catalogs.models import ContractorModel
from common.catalogs.serializers import ContractorModelByIdSerializer
from common.models import File
from common.serializers import (
    CachedBaseCatalogSerializer,
    CachedBaseModelSerializer,
    BaseCatalogRetrieveSerializer
)
from common.utils import get_serialized_attachments
from contractor_permissions.utils import check_contractor_permission
from users.serializers import AppUserSerializer

from . import models, utils, notifications


class InvestProjectInfoMeasureUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InvestProjectMeasureUnitModel
        fields = (
            'id',
            'code',
            'name',
            'name_short',
            'name_plural',
        )


class InvestProjectFundingSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InvestProjectFundingSourceModel
        fields = (
            'id',
            'code',
            'name',
            'short_name'
        )


class FundingSourceAndAmountModelListSerializer(serializers.ModelSerializer):
    funding_source = CachedBaseModelSerializer(
        serializer_class=InvestProjectFundingSourceSerializer,
        source='funding_source_id',
    )

    class Meta:
        model = models.FundingSourceAndAmountModel
        fields = (
            'id',
            'amount',
            'comment',
            'funding_source'
        )


class InvestProjectStatusModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InvestProjectStatusModel
        fields = (
            'code',
            'name',
            'color',
            'hex_color'
        )


class InvestProjectInfoModelListSerializer(serializers.ModelSerializer):
    organization = ContractorModelByIdSerializer()
    location = CachedKATOCodesModelSerializer(source='location_id')
    author = AppUserSerializer()
    measure_unit = InvestProjectInfoMeasureUnitSerializer()
    stage = CachedBaseModelSerializer(serializer_class=BaseCatalogRetrieveSerializer, source='stage_id')
    category = CachedBaseModelSerializer(serializer_class=BaseCatalogRetrieveSerializer, source='category_id')
    subcategory = CachedBaseModelSerializer(
        serializer_class=BaseCatalogRetrieveSerializer,
        source='subcategory_id'
    )
    funding_sources = FundingSourceAndAmountModelListSerializer(many=True)
    status = InvestProjectStatusModelSerializer()

    class Meta:
        model = models.InvestProjectInfoModel
        fields = (
            'id',
            'author',
            'bank_funds',
            'borrowed_funds',
            'cadaster',
            'category',
            'comment',
            'company_bin',
            'company_director_name',
            'company_name',
            'company_phone',
            'date_start',
            'dead_line',
            'fin_institute',
            'foreign_investor_info',
            'funding_sources',
            'funds',
            'has_documentation',
            'infrastructure_info',
            'installation_stage',
            'jobs_permanent',
            'jobs_temporary',
            'land_plot',
            'land_plot_is_allocated',
            'location',
            'measure_unit',
            'organization',
            'own_funds',
            'pasture_quantity',
            'plowed_field_quantity',
            'project_capacity',
            'project_name',
            'questions',
            'stage',
            'subcategory',
            'types_of_products',
            'work_experience',
            'status',
        )


class InvestProjectInfoModelDetailSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    author = AppUserSerializer()
    category = CachedBaseModelSerializer(
        serializer_class=BaseCatalogRetrieveSerializer,
        source='category_id',
    )
    funding_sources = FundingSourceAndAmountModelListSerializer(many=True)
    location = CachedKATOCodesModelSerializer(source='location_id')
    measure_unit = InvestProjectInfoMeasureUnitSerializer()
    organization = ContractorModelByIdSerializer()
    stage = CachedBaseModelSerializer(serializer_class=BaseCatalogRetrieveSerializer, source='stage_id')
    status = InvestProjectStatusModelSerializer()
    subcategory = CachedBaseModelSerializer(serializer_class=BaseCatalogRetrieveSerializer, source='subcategory_id')

    class Meta:
        model = models.InvestProjectInfoModel
        fields = (
            'id',
            'attachments',
            'author',
            'bank_funds',
            'borrowed_funds',
            'cadaster',
            'category',
            'comment',
            'company_bin',
            'company_director_name',
            'company_name',
            'company_phone',
            'date_start',
            'dead_line',
            'fin_institute',
            'foreign_investor_info',
            'funding_sources',
            'funds',
            'has_documentation',
            'infrastructure_info',
            'installation_stage',
            'jobs_permanent',
            'jobs_temporary',
            'land_plot',
            'land_plot_is_allocated',
            'location',
            'measure_unit',
            'organization',
            'own_funds',
            'pasture_quantity',
            'plowed_field_quantity',
            'project',
            'project_capacity',
            'project_name',
            'questions',
            'stage',
            'status',
            'subcategory',
            'types_of_products',
            'work_experience'
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class FundingSourceAndAmountModelCreateSerializer(serializers.ModelSerializer):
    funding_source = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectFundingSourceModel.objects.filter(is_active=True),
        allow_null=False, required=True,
    )

    class Meta:
        model = models.FundingSourceAndAmountModel
        fields = (
            'id',
            'amount',
            'comment',
            'funding_source',
            'invest_project_info'
        )


class InvestProjectInfoModelCreateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True),
        allow_null=False, required=True,
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=KATOCodesModel.objects.filter(is_active=True),
        allow_null=False, required=True,
    )
    stage = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectStageModel.objects.filter(is_active=True),
        allow_null=True, required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectCategoryModel.objects.filter(is_active=True),
        allow_null=False,
        required=True
    )
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectSubcategoryModel.objects.filter(is_active=True),
        allow_null=True,
        required=False
    )
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.InvestProjectInfoModel
        fields = (
            'id',
            'attachments',
            'bank_funds',
            'borrowed_funds',
            'cadaster',
            'category',
            'comment',
            'company_bin',
            'company_director_name',
            'company_name',
            'company_phone',
            'date_start',
            'dead_line',
            'fin_institute',
            'foreign_investor_info',
            'funds',
            'has_documentation',
            'infrastructure_info',
            'installation_stage',
            'jobs_permanent',
            'jobs_temporary',
            'land_plot',
            'land_plot_is_allocated',
            'location',
            'measure_unit',
            'organization',
            'own_funds',
            'pasture_quantity',
            'plowed_field_quantity',
            'project_capacity',
            'project_name',
            'questions',
            'stage',
            'subcategory',
            'types_of_products',
            'work_experience',
        )

    def validate(self, attrs):
        user = self.context.get('request').user.profile
        organization = attrs.get('organization')
        create_permission_id = models.InvestProjectPermissionTypeModel.objects.get(code='create')
        check_contractor_permission(user.pk, organization.pk, 'create_invest_projects_info', create_permission_id)
        return attrs

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            funding_sources = self.initial_data.get('funding_sources', None)
            add_project = self.initial_data.get('add_project', False)
            if funding_sources and isinstance(funding_sources, list):
                serializer = FundingSourceAndAmountModelCreateSerializer
                for each in funding_sources:
                    each['invest_project_info'] = instance.pk
                    source_serializer = serializer(data=each)
                    source_serializer.is_valid(raise_exception=True)
                    source_serializer.save()
            if attachments:
                instance.attachments.set(attachments)
            if add_project:
                utils.add_project(
                    instance=instance,
                    request=self.context.get('request')
                )
        return instance

    def to_representation(self, instance):
        return InvestProjectInfoModelDetailSerializer(instance).data


class InvestProjectInfoModelUpdateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True),
        allow_null=False, required=True,
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=KATOCodesModel.objects.filter(is_active=True),
        allow_null=False, required=True,
    )
    stage = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectStageModel.objects.filter(is_active=True),
        allow_null=True, required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectCategoryModel.objects.filter(is_active=True),
        allow_null=False, required=True
    )
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=models.InvestProjectSubcategoryModel.objects.filter(is_active=True),
        allow_null=True, required=True
    )

    class Meta:
        model = models.InvestProjectInfoModel
        fields = (
            'id',
            'bank_funds',
            'borrowed_funds',
            'cadaster',
            'category',
            'comment',
            'company_bin',
            'company_director_name',
            'company_name',
            'company_phone',
            'date_start',
            'dead_line',
            'fin_institute',
            'foreign_investor_info',
            'funds',
            'has_documentation',
            'infrastructure_info',
            'installation_stage',
            'jobs_permanent',
            'jobs_temporary',
            'land_plot',
            'land_plot_is_allocated',
            'location',
            'measure_unit',
            'organization',
            'own_funds',
            'pasture_quantity',
            'plowed_field_quantity',
            'project_capacity',
            'project_name',
            'questions',
            'stage',
            'subcategory',
            'types_of_products',
            'work_experience',
        )

    def update(self, instance, validated_data):
        add_project = self.initial_data.get('add_project', False)
        attachments = self.initial_data.get('attachments', None)
        funding_sources_data = self.initial_data.get('funding_sources')
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if isinstance(funding_sources_data, list):
                funding_sources_id = []
                for each in funding_sources_data:
                    if 'id' in each:
                        funding_sources_id.append(each['id'])
                funding_sources_delete = instance.funding_sources.all().exclude(pk__in=funding_sources_id)
                for each in funding_sources_delete:
                    each.delete()
                for each in funding_sources_data:
                    if 'id' in each:
                        try:
                            source = instance.funding_sources.get(pk=each['id'])
                        except ObjectDoesNotExist:
                            raise drf_exceptions.ValidationError({'message': 'Источник финансирования не найден'})
                        source_serializer = FundingSourceAndAmountModelCreateSerializer(instance=source, data=each)
                        source_serializer.is_valid(raise_exception=True)
                        source_serializer.save()
                    else:
                        each['invest_project_info'] = instance.pk
                        source_serializer = FundingSourceAndAmountModelCreateSerializer(data=each)
                        source_serializer.is_valid(raise_exception=True)
                        source_serializer.save()
            if add_project and instance.project is None:
                utils.add_project(
                    instance=instance,
                    request=self.context.get('request')
                )
            if attachments:
                instance.attachments.set(attachments)
        return instance

    def to_representation(self, instance):
        return InvestProjectInfoModelDetailSerializer(instance).data


class InvestCategoryStatisticsSerializer(serializers.Serializer):
    category = CachedBaseModelSerializer(serializer_class=BaseCatalogRetrieveSerializer, source='category_id')
    total_count = serializers.IntegerField()
    category_count = serializers.IntegerField()
    category_percent = serializers.DecimalField(max_digits=4, decimal_places=1)


class InvestStatusStatisticsSerializer(serializers.Serializer):
    status = serializers.SerializerMethodField()
    count = serializers.IntegerField()

    def get_status(self, instance):
        if instance['status']=='total':
            result = {
                'code': 'total',
                'name': 'Все проекты'}
        else:
            status = models.InvestProjectStatusModel.objects.get(code=instance['status'])
            result = InvestProjectStatusModelSerializer(status).data
        return result


class InvestFundingSourceStatisticsSerializer(serializers.Serializer):
    source = CachedBaseModelSerializer(serializer_class=InvestProjectFundingSourceSerializer, source='source_id')
    total_sum = serializers.IntegerField()
    source_sum = serializers.IntegerField()
    source_percent = serializers.DecimalField(max_digits=4, decimal_places=1)


class InvestProjectStatusWithDependsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InvestProjectStatusModel
        fields = (
            'code',
            'name',
            'color',
            'hex_color',
            'btn_title',
            'depends',
        )


class UpdateStatusInvestProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.InvestProjectInfoModel
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
            if new_status_code in ['on_check', 'on_rework', 'approved', 'change_requested',]:
                initiator = self.context.get('request').user.profile
                # notifications.notify_about_new_status(instance, new_status_code, initiator) # не асинхронно, для отладки
                async_task(notifications.notify_about_new_status, instance, new_status_code, initiator)
        return instance


class DeleteInvestProjectSerializer(serializers.Serializer):
    id = serializers.UUIDField()
