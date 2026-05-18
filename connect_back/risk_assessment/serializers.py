from django.db import transaction
from django.db.models import Sum
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers

from common.catalogs.models import ContractorModel, LocationPointModel
from common.catalogs.serializers import ContractorModelShortSerializer, LocationPointSerializer
from common.catalogs.utils import get_admin_area_for_point

from common.serializers import BaseCatalogRetrieveSerializer
from contractor_permissions.utils import check_contractor_permission
from users.serializers import AppUserSerializer

from . import models


class IssueCategoryModelDetailSerializer(serializers.ModelSerializer):
    """Сериализатор категории обращения. Рекурсивно выводит родительские категории,
    начиная с непосредственного родителя."""

    class Meta:
        model = models.IssueCategoryModel
        fields = (
            'id',
            'code',
            'name',
            'metadata',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        if instance.is_child_node():
            parent = instance.get_ancestors(ascending=True, include_self=False).first()
            data['issue_category'] = IssueCategoryModelDetailSerializer(parent).data
        return data


class IssueCategoryModelListSerializer(serializers.ModelSerializer):
    """Сериализатор списка категорий обращений."""
    is_leaf = serializers.SerializerMethodField()

    class Meta:
        model = models.IssueCategoryModel
        fields = (
            'id',
            'name',
            'is_leaf'
        )

    def get_is_leaf(self, instance):
        return instance.is_leaf_node()


class CitizensSocialStatusModelSerializer(serializers.ModelSerializer):
    """Сериализатор социальных статусов граждан."""

    class Meta:
        model = models.CitizensSocialStatusModel
        fields = (
            'id',
            'name',
            'code'
        )


class PersonalReceptionStatusModelSerializer(serializers.ModelSerializer):
    """Статусы обращений при личном приеме."""

    class Meta:
        model = models.PersonalReceptionStatusModel
        fields = (
            'id',
            'name',
            'color',
            'code'
        )


class PersonalReceptionSerializer(serializers.ModelSerializer):
    """Данные указанные при личном приеме."""
    class Meta:
        model = models.PersonalReceptionModel
        fields = (
            'social_status',
            'status'
        )


class PersonalReceptionDetailSerializer(serializers.ModelSerializer):
    """Данные указанные при личном приеме."""
    social_status = CitizensSocialStatusModelSerializer()
    status = PersonalReceptionStatusModelSerializer()

    class Meta:
        model = models.PersonalReceptionModel
        fields = (
            'social_status',
            'status'
        )


class PersonalReceptionReportUploadSerializer(serializers.ModelSerializer):
    """Данные указанные при личном приеме."""
    status = serializers.CharField(source='status.name')
    status_code = serializers.CharField(source='status.code')
    status_name = serializers.CharField(source='status.name')
    social_status_code = serializers.CharField(source='social_status.code')

    class Meta:
        model = models.PersonalReceptionModel
        fields = (
            'id',
            'status',
            'status_code',
            'status_name',
            'social_status_code',
            'days_in_queue'
        )


class IssueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueModel
        fields = (
            'id',
            'issue_type',
            'issue_category',
            'number',
            'summary',
            'text',
            'issue_date',
        )


class IssueModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueModel
        fields = (
            'id',
            'issue_type',
            'issue_category',
            'number',
            'summary',
            'text',
            'issue_date',
        )


class IssueModelListSerializer(serializers.ModelSerializer):
    issue_type = BaseCatalogRetrieveSerializer()
    issue_category = BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.IssueModel
        fields = (
            'id',
            'number',
            'summary',
            'issue_date',
            'issue_type',
            'issue_category',
        )


class IssueModelDetailSerializer(serializers.ModelSerializer):
    issue_type = BaseCatalogRetrieveSerializer()
    issue_category = IssueCategoryModelDetailSerializer()

    class Meta:
        model = models.IssueModel
        fields = (
            'id',
            'number',
            'summary',
            'text',
            'issue_date',
            'issue_type',
            'issue_category',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        personal_reception = getattr(instance, 'personal_reception', None)
        if personal_reception is not None:
            data['personal_reception'] = PersonalReceptionDetailSerializer(personal_reception).data
        return data


class IssueModelReportUploadSerializer(serializers.ModelSerializer):
    personal_reception = PersonalReceptionReportUploadSerializer()

    class Meta:
        model = models.IssueModel
        fields = (
            'id',
            'number',
            'issue_date',
            'personal_reception'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sent_for'] = instance.risk_assessments.first().sent_for
        return data


class RiskAssessmentCriteriaSerializer(serializers.ModelSerializer):
    criteria = BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.RiskAssessmentCriteriaModel
        fields = (
            'criteria',
            'value',
        )


class RiskAssessmentStatusModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RiskAssessmentStatusModel
        fields = (
            'id',
            'code',
            'name',
            'color',
        )


class RiskAssessmentModelDetailSerializer(serializers.ModelSerializer):
    assessment_type = BaseCatalogRetrieveSerializer()
    author = AppUserSerializer()
    issue = IssueModelDetailSerializer()
    organization = ContractorModelShortSerializer()
    risk_assessment_criteria = RiskAssessmentCriteriaSerializer(many=True)
    status = RiskAssessmentStatusModelSerializer()
    location_points = serializers.SerializerMethodField()

    class Meta:
        model = models.RiskAssessmentModel
        fields = (
            'id',
            'assessment_type',
            'author',
            'issue',
            'organization',
            'risk_assessment_criteria',
            'sent_for',
            'status',
            'location_points',
            'total_value',
        )

    def get_location_points(self, instance):
        points = instance.location_points.filter(is_active=True)
        if points:
            return LocationPointSerializer(points, many=True).data
        return []


class RiskAssessmentModelListSerializer(serializers.ModelSerializer):
    assessment_type = BaseCatalogRetrieveSerializer()
    issue = IssueModelListSerializer()
    organization = ContractorModelShortSerializer()
    status = RiskAssessmentStatusModelSerializer()
    location_points = serializers.SerializerMethodField()

    class Meta:
        model = models.RiskAssessmentModel
        fields = (
            'id',
            'assessment_type',
            'issue',
            'organization',
            'sent_for',
            'status',
            'location_points',
            'total_value',
        )

    def get_location_points(self, instance):
        points = instance.location_points.all()
        if points:
            return LocationPointSerializer(points, many=True).data
        return []


class RiskAssessmentModelMapSerializer(serializers.ModelSerializer):
    location_points = serializers.SerializerMethodField()
    issue_number = serializers.CharField(source='issue.number')

    class Meta:
        model = models.RiskAssessmentModel
        fields = (
            'id',
            'sent_for',
            'location_points',
            'total_value',
            'issue_number'
        )

    def get_location_points(self, instance):
        points = instance.location_points.all()
        if points:
            return LocationPointSerializer(points, many=True).data
        return []


class RiskAssessmentCriteriaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RiskAssessmentCriteriaModel
        fields = (
            'id',
            'criteria',
            'value',
            'risk_assessment',
        )


class RiskAssessmentCriteriaUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RiskAssessmentCriteriaModel
        fields = (
            'id',
            'value',
        )


class RiskAssessmentModelCreateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True), required=True
    )
    location_points = LocationPointSerializer(required=False, many=True)
    personal_reception = PersonalReceptionSerializer(required=False)

    class Meta:
        model = models.RiskAssessmentModel
        fields = (
            'id',
            'assessment_type',
            'location_points',
            'organization',
            'personal_reception',
            'sent_for',
        )

    def validate(self, attrs):
        user = self.context.get('request').user.profile
        organization = attrs.get('organization')
        assessment_type = attrs.get('assessment_type')
        check_contractor_permission(user.pk, organization.pk, 'create_risk_assessment', assessment_type.pk)
        return attrs

    def create(self, validated_data):
        issue_data = self.initial_data.pop('issue', None)
        location_points = validated_data.pop('location_points', None)
        personal_reception = validated_data.pop('personal_reception', None)
        if not issue_data:
            raise drf_exceptions.ValidationError({"message": "Issue not found."})
        criteria_data = self.initial_data.pop('risk_assessment_criteria', None)
        if not criteria_data:
            raise drf_exceptions.ValidationError({"message": "Criteria not found."})
        with transaction.atomic():
            issue_serializer = IssueCreateSerializer(data=issue_data)
            issue_serializer.is_valid(raise_exception=True)
            issue = issue_serializer.save()
            instance = models.RiskAssessmentModel.objects.create(issue=issue, **validated_data)
            for each in criteria_data:
                each['risk_assessment'] = instance.pk
                criteria_serializer = RiskAssessmentCriteriaCreateSerializer(data=each)
                criteria_serializer.is_valid(raise_exception=True)
                criteria = criteria_serializer.save()
            instance.total_value = instance.risk_assessment_criteria.all().aggregate(Sum('value'))['value__sum']
            instance.save(update_fields=('total_value',))

            if location_points:
                for point in location_points:
                    admin_area = get_admin_area_for_point((point.get('lon'), point.get('lat')))
                    LocationPointModel.objects.create(
                        related_object_id=instance.pk,
                        admin_area=admin_area,
                        **point,
                    )
            if personal_reception:
                models.PersonalReceptionModel.objects.create(
                    issue=issue,
                    **personal_reception
                )
        return instance

    def to_representation(self, instance):
        return RiskAssessmentModelDetailSerializer(instance).data


class RiskAssessmentModelUpdateSerializer(serializers.ModelSerializer):
    location_points = LocationPointSerializer(required=False, many=True)
    personal_reception = PersonalReceptionSerializer(required=False)

    class Meta:
        model = models.RiskAssessmentModel
        fields = (
            'id',
            'sent_for',
            'location_points',
            'personal_reception',
        )

    def update(self, instance, validated_data):
        issue_data = self.initial_data.pop('issue', None)
        criteria_data = self.initial_data.pop('risk_assessment_criteria', None)
        personal_reception = validated_data.pop('personal_reception', None)
        location_points = validated_data.pop('location_points', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if issue_data:
                issue_serializer = IssueModelUpdateSerializer(instance=instance.issue, data=issue_data, partial=True)
                issue_serializer.is_valid(raise_exception=True)
                issue_serializer.save()
            if criteria_data:
                for each in criteria_data:
                    try:
                        criteria_instance = models.RiskAssessmentCriteriaModel.objects.get(
                            risk_assessment_id=instance.pk, criteria_id=each.get('criteria')
                        )
                    except models.RiskAssessmentCriteriaModel.DoesNotExist:
                        raise drf_exceptions.ValidationError({'message': 'Incorrect criteria.'})
                    criteria_serializer = RiskAssessmentCriteriaUpdateSerializer(
                        instance=criteria_instance,
                        data=each,
                        partial=True
                    )
                    criteria_serializer.is_valid(raise_exception=True)
                    criteria_serializer.save()
            instance.total_value = instance.risk_assessment_criteria.all().aggregate(Sum('value'))['value__sum']
            instance.save(update_fields=('total_value',))

            instance.location_points.all().delete()
            if location_points:
                for point in location_points:
                    admin_area = get_admin_area_for_point((point.get('lon'), point.get('lat')))
                    LocationPointModel.objects.create(
                        related_object_id=instance.pk,
                        admin_area=admin_area,
                        **point,
                    )
            if personal_reception is not None:
                models.PersonalReceptionModel.objects.update_or_create(
                    issue=instance.issue,
                    defaults=personal_reception
                )
            else:
                if hasattr(instance.issue, 'personal_reception'):
                    instance.issue.personal_reception.delete()
        return instance

    def to_representation(self, instance):
        return RiskAssessmentModelDetailSerializer(instance).data
