from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers

from common.models import File
from common.utils import get_serialized_attachments
from common.serializers import CachedBaseCatalogSerializer
from common.catalogs.serializers import ContractorModelShortSerializer, CostItemModelListSerializer

from contractor_permissions.utils import check_contractor_permission

from users.models import ProfileModel
from users.serializers import CachedAppUserPreviewSerializer

from bpms.bpms_common.serializers import AppUserSerializer
from bpms.workgroups.serializers import WorkgroupNameSerializer
from bpms.workgroups.serializers import WorkgroupNameLogoSerializer

from . import models, utils


class WorkflowRequestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestTypeModel
        fields = (
            'id',
            'code',
            'name',
            'sort',
        )


class WorkflowRequestTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestTypeModel
        fields = (
            'id',
            'name',
            'contractor',
        )

    def validate(self, attrs):
        contractor = attrs.get('contractor')
        if not contractor:
            raise drf_exceptions.ValidationError('contractor is required')
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            routes = self.initial_data.get('routes')
            if routes:
                for each in routes:
                    each['request_type'] = instance.pk
                    route_serializer = WorkflowRequestRouteTemplateCreateSerializer(data=each)
                    route_serializer.is_valid(raise_exception=True)
                    route_serializer.save()
        return instance


class WorkflowRequestRouteTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestRouteTemplateModel
        fields = (
            'request_type',
            'name',
            'workflow_position',
            'not_require_approval',
            'parent',
        )


class WorkflowRequestTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestTypeModel
        fields = (
            'id',
            'name',
            'contractor',
        )

    def validate(self, attrs):
        contractor = attrs.get('contractor')
        if not contractor:
            raise drf_exceptions.ValidationError('contractor is required')
        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            routes = self.initial_data.get('routes')
            if routes is not None:
                models.WorkflowRequestRouteTemplateModel.objects.filter(request_type=instance).delete()
                for each in routes:
                    each['request_type'] = instance.pk
                    route_serializer = WorkflowRequestRouteTemplateCreateSerializer(data=each)
                    route_serializer.is_valid(raise_exception=True)
                    route_serializer.save()
        return instance


class WorkflowRequestTypeDetailSerializer(serializers.ModelSerializer):
    contractor = ContractorModelShortSerializer()

    class Meta:
        model = models.WorkflowRequestTypeModel
        fields = (
            'id',
            'name',
            'contractor',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        routes = list(models.WorkflowRequestRouteTemplateModel.objects.filter(request_type=instance))
        if routes:
            data['routes'] = WorkflowRequestRouteTemplateListSerializer(routes, many=True).data
        else:
            data['routes'] = []
        return data


class WorkflowRequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestStatusModel
        fields = (
            'id',
            'code',
            'name',
            'sort',
            'color',
        )


class WorkflowRequestRouteCreateSerializer(serializers.ModelSerializer):

    users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProfileModel.objects.filter(is_active=True),
    )

    class Meta:
        model = models.WorkflowRequestRouteModel
        fields = (
            'id',
            'workflow_request',
            'workflow_position',
            'sort',
            'template',
            'users',
            'parent',
            'not_require_approval',
        )

    def validate(self, attrs):

        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        users = validated_data.pop('users', None)
        if users:
            instance.users.set(users)
        return instance

    def to_representation(self, instance):
        return None


class WorkflowRequestCreateSerializer(serializers.ModelSerializer):
    dead_line = serializers.DateTimeField(required=True, allow_null=False)
    attachments = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.WorkflowRequestModel
        fields = (
            'id',
            'request_type',
            'organization',
            'project',
            'dead_line',
            'amount_requested',
            'event_date_start',
            'event_date_end',
            'description',
            'money_under_report',
            'attachments',
        )

    def validate(self, attrs):
        organization = attrs.get('organization')
        org_id = organization.pk
        user = self.context.get('request').user.profile
        check_contractor_permission(user.pk, org_id, ('request_approvals_manager', 'request_approvals_admin'), None)
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            attachments = validated_data.pop('attachments', None)
            instance = super().create(validated_data)
            route = self.initial_data.get('route')
            try:
                route_dict = {_['position']: _['users'] for _ in route}
            except KeyError:
                raise drf_exceptions.ValidationError('Некорректные данные в маршруте согласования')
            route_template = list(models.WorkflowRequestRouteTemplateModel.objects.filter(
                is_active=True,
                request_type=instance.request_type,
            ).order_by('sort'))
            if attachments:
                instance.attachments.set(attachments)
            for each in route_template:
                route_template_parent = each.parent
                if route_template_parent:
                    route_parent = models.WorkflowRequestRouteModel.objects.filter(
                        workflow_request=instance,
                        template=route_template_parent,
                    ).order_by('-created_at').first().pk
                else:
                    route_parent = None
                route_data = {
                    'workflow_request': instance.pk,
                    'workflow_position': each.workflow_position_id,
                    'sort': each.sort,
                    'template': each.pk,
                    'users': route_dict.get(each.workflow_position_id, []),
                    'parent': route_parent,
                    'not_require_approval': each.not_require_approval,
                }
                route_serializer = WorkflowRequestRouteCreateSerializer(data=route_data, context=self.context)
                route_serializer.is_valid(raise_exception=True)
                route_serializer.save()
        return instance


class WorkflowRequestUpdateSerializer(serializers.ModelSerializer):
    dead_line = serializers.DateTimeField(required=True, allow_null=False)
    attachments = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.WorkflowRequestModel
        fields = (
            'id',
            'request_type',
            'amount_requested',
            'organization',
            'description',
            'money_under_report',
            'project',
            'dead_line',
            'event_date_start',
            'event_date_end',
            'attachments',
        )

    def validate(self, attrs):
        instance = self.instance
        status_id = self.instance.status_id
        if not status_id == 'draft' and 'organization' in attrs:
            raise drf_exceptions.ValidationError(
                'Организацию можно изменять только если заявка находится в статусе "Черновик"'
            )
        if not status_id == 'draft' and 'request_type' in attrs:
            raise drf_exceptions.ValidationError(
                'Тип заявки можно изменять только если заявка находится в статусе "Черновик"'
            )
        if 'organization' in attrs:
            old_organization = instance.organization
            new_organization = attrs.get('organization')
            if not old_organization == new_organization:
                org_id = new_organization.pk
                user = self.context.get('request').user.profile
                check_contractor_permission(
                    user.pk, org_id, ('request_approvals_manager', 'request_approvals_admin'), None
                )
        return attrs

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', None)
        route = self.initial_data.get('route')
        if route is not None and instance.status_id == 'draft':
            try:
                route_dict = {_['position']: _['users'] for _ in route}
            except KeyError:
                raise drf_exceptions.ValidationError('Некорректные данные в маршруте согласования')
        else:
            route_dict = None

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if route_dict:
                models.WorkflowRequestRouteModel.objects.filter(workflow_request=instance).delete()
                route_template = list(models.WorkflowRequestRouteTemplateModel.objects.filter(
                    is_active=True,
                    request_type=instance.request_type,
                ).order_by('sort'))
                for each in route_template:
                    route_template_parent = each.parent
                    if route_template_parent:
                        route_parent = models.WorkflowRequestRouteModel.objects.filter(
                            workflow_request=instance,
                            template=route_template_parent,
                        ).order_by('-created_at').first().pk
                    else:
                        route_parent = None
                    route_data = {
                        'workflow_request': instance.pk,
                        'workflow_position': each.workflow_position_id,
                        'sort': each.sort,
                        'template': each.pk,
                        'users': route_dict.get(each.workflow_position_id, []),
                        'parent': route_parent,
                        'not_require_approval': each.not_require_approval,
                    }
                    route_serializer = WorkflowRequestRouteCreateSerializer(data=route_data, context=self.context)
                    route_serializer.is_valid(raise_exception=True)
                    route_serializer.save()
            if attachments is not None:
                instance.attachments.set(attachments)

        return instance


class WorkflowRequestRouteStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestRouteStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
        )


class WorkflowPositionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowPositionModel
        fields = (
            'id',
            'code',
            'name',
        )


class WorkflowRequestRouteUserSerializer(serializers.ModelSerializer):
    status = WorkflowRequestRouteStatusListSerializer()
    user = CachedAppUserPreviewSerializer(source='user_id')

    class Meta:
        model = models.RequestRouteUserThrough
        fields = (
            'id',
            'user',
            'status'
        )


class WorkflowRequestRouteListSerializer(serializers.ModelSerializer):
    status = WorkflowRequestRouteStatusListSerializer()
    workflow_position = WorkflowPositionListSerializer()
    request_route_user_through = WorkflowRequestRouteUserSerializer(many=True)

    class Meta:
        model = models.WorkflowRequestRouteModel
        fields = (
            'id',
            'workflow_position',
            'status',
            'request_route_user_through',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.workflow_position_id == 'paymaster':
            status_code = instance.status_id
            if status_code == 'under_approval':
                data['status']['name'] = _('Выдача денежных средств')
            elif status_code == 'approved':
                data['status']['name'] = _('Выдано')
            request_route_user_through = data.get('request_route_user_through')
            if request_route_user_through:
                for each in request_route_user_through:
                    status_code = each['status']['code']
                    if status_code == 'under_approval':
                        each['status']['name'] = _('Выдача денежных средств')
                    elif status_code == 'approved':
                        each['status']['name'] = _('Выдано')
        return data


class WorkflowRequestDetailSerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    request_type = CachedBaseCatalogSerializer(
        source='request_type_id',
        serializer_class=WorkflowRequestTypeSerializer,
        model=models.WorkflowRequestTypeModel,
    )
    status = CachedBaseCatalogSerializer(
        source='status_id',
        serializer_class=WorkflowRequestStatusSerializer,
        model=models.WorkflowRequestStatusModel,
    )
    project = WorkgroupNameLogoSerializer()
    organization = ContractorModelShortSerializer()

    class Meta:
        model = models.WorkflowRequestModel
        fields = (
            'id',
            'author',
            'number',
            'description',
            'rejection_reason',
            'request_type',
            'organization',
            'status',
            'advance_report_approved',
            'project',
            'money_under_report',
            'paid_before_lpr',
            'dead_line',
            'event_date_start',
            'event_date_end',
            'date_start',
            'date_end',
            'completed',
            'amount_paid',
            'amount_requested',
            'amount_reported',
            'balance',
            'created_at',
            'updated_at',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        routes = instance.request_routes.all().order_by('sort')
        routes_serializer = WorkflowRequestRouteListSerializer(routes, many=True)
        routes_data = routes_serializer.data
        data['routes'] = routes_data
        data['attachments'] = get_serialized_attachments(instance)
        return data


class WorkflowRequestListSerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    request_type = CachedBaseCatalogSerializer(
        source='request_type_id',
        serializer_class=WorkflowRequestTypeSerializer,
        model=models.WorkflowRequestTypeModel,
    )
    status = CachedBaseCatalogSerializer(
        source='status_id',
        serializer_class=WorkflowRequestStatusSerializer,
        model=models.WorkflowRequestStatusModel,
    )
    project = WorkgroupNameLogoSerializer()
    organization = ContractorModelShortSerializer()

    class Meta:
        model = models.WorkflowRequestModel
        fields = (
            'id',
            'author',
            'number',
            'request_type',
            'organization',
            'status',
            'project',
            'description',
            'money_under_report',
            'paid_before_lpr',
            'dead_line',
            'event_date_start',
            'event_date_end',
            'date_start',
            'date_end',
            'completed',
            'amount_paid',
            'amount_requested',
            'amount_reported',
            'advance_report_approved',
            'balance',
            'created_at',
            'updated_at',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['has_new_comments'] = instance.pk in self.context.get('unviewed_comments', [])
        return data


class AdvanceReportModelCreateSerializer(serializers.ModelSerializer):

    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.AdvanceReportModel
        fields = (
            'id',
            'owner',
            'date',
            'cost_item',
            'amount',
            'description',
            'attachments'
        )

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            if attachments:
                instance.attachments.set(attachments)
        return instance


class AdvanceReportModelUpdateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.AdvanceReportModel
        fields = (
            'id',
            'date',
            'cost_item',
            'amount',
            'description',
            'attachments',
        )

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if attachments is not None:
                instance.attachments.set(attachments)
        return instance


class AdvanceReportModelListSerializer(serializers.ModelSerializer):
    cost_item = CostItemModelListSerializer()

    class Meta:
        model = models.AdvanceReportModel
        fields = (
            'id',
            'date',
            'cost_item',
            'amount',
            'description',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['attachments'] = get_serialized_attachments(instance)
        return data


class DemandReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowRequestModel
        fields = (
            'id',
            'money_under_report'
        )


class WorkflowRequestGiveMoneySerializer(serializers.ModelSerializer):
    amount_paid = serializers.DecimalField(allow_null=False, required=True, decimal_places=2, max_digits=15)

    class Meta:
        model = models.WorkflowRequestModel
        fields = (
            'id',
            'amount_paid',
        )


class WorkflowRequestRouteTemplateListSerializer(serializers.ModelSerializer):
    workflow_position = WorkflowPositionListSerializer()

    class Meta:
        model = models.WorkflowRequestRouteTemplateModel
        fields = (
            'id',
            'workflow_position',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        position = instance.workflow_position
        contractors = self.context.get('contractors')
        if contractors:
            users = models.WorkflowPositionUserModel.objects.filter(
                workflow_position=position,
                contractor_profile__contractor_id__in=contractors,
            ).order_by(
                'contractor_profile__user__user__last_name',
                'contractor_profile__user__user__first_name',
            ).values_list(
                'contractor_profile__user',
                flat=True
            )
            data['users'] = CachedAppUserPreviewSerializer(users, many=True).data
        return data
