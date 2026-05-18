import json

from django.db.models import Count, Prefetch
from rest_framework import exceptions as drf_exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.catalogs.models import LocationPointModel
from common.utils import filter_queryset_from_get_param
from common.views import BaseModelViewSet
from users.utils import get_descendants_departments_related_organizations
from consolidation.models import ReportModel

from . import models, permissions, utils, serializers
from .fields import TotalValueFilterField


class RiskAssessmentViewSet(BaseModelViewSet):
    model = models.RiskAssessmentModel
    permission_classes = (permissions.CreateRiskAssessmentPermission, IsAuthenticated,)

    def get_queryset(self):
        queryset = self.model.get_queryset(self.request)
        queryset = queryset.select_related(
            'assessment_type',
            'issue__issue_type',
            'organization',
            'status',
            ).prefetch_related(Prefetch(
                'location_points',
                queryset=LocationPointModel.objects.filter(is_active=True)
                )
                )
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        response.data['summary'] = utils.get_summary(queryset)
        return response

    @action(methods=('post',), detail=False, url_path='action_info',)
    def get_bulk_action_info(self, request, *args, **kwargs):
        risk_assessments_id = request.data
        if not isinstance(risk_assessments_id, list):
            raise drf_exceptions.ValidationError()
        risk_assessments = models.RiskAssessmentModel.get_queryset(request).filter(pk__in=risk_assessments_id)
        result = dict()

        for each in risk_assessments:
            if each.get_update_permission(request):
                actions = {
                    "edit": {"availability": True},
                    "delete": {"availability": True},
                    }
                if each.status_id == 'processed':
                    is_support = request.user.profile.is_support
                    if not is_support:
                        del actions['delete']
            else:
                actions = dict()
            result[str(each.pk)] = actions
        return Response(result)

    @action(methods=('post',), detail=False, url_path='aggregate',)
    def aggregate(self, request, *args, **kwargs,):
        request_data = request.data
        organizations = request_data.get('organizations',)
        data = []
        qs = self.model.get_queryset(request)
        qs.query.clear_ordering(True)
        filters = request_data.get('filters')
        if filters:
            qs = filter_queryset_from_get_param(filters, qs)
        display = request.data.get('display', 'root')
        if display == 'descendants':
            for organization_id in organizations:
                qs = qs.filter(
                    organization_id__in=get_descendants_departments_related_organizations((organization_id,))
                ).values('total_value').annotate(
                    dcount=Count('pk')
                )
                data = data + [{'organization_id': organization_id, 'data': list(qs)}]
        else:
            for organization_id in organizations:
                qs = qs.filter(
                    organization_id=organization_id
                ).values('total_value').annotate(
                    dcount=Count('pk')
                )
                data = data + [{'organization_id': organization_id, 'data': list(qs)}]
        return Response(data)

    @action(methods=('get',), detail=False, url_path='count')
    def get_count(self, request, *args, **kwargs):
        organization_id = request.query_params.get('organization',)
        if not organization_id:
            return Response({'count': 0})
        qs = self.model.get_queryset(request)
        qs.query.clear_ordering(True)
        filters = request.query_params.get('filters')
        if filters:
            try:
                filters_dict = json.loads(request.query_params.get('filters'))
            except json.JSONDecodeError:
                filters_dict = dict()
            qs = filter_queryset_from_get_param(filters_dict, qs)
        display = request.query_params.get('display', 'root')
        if display == 'descendants':
            assessment_count = qs.filter(
                organization_id__in=get_descendants_departments_related_organizations((organization_id,))
            ).count()
        else:
            assessment_count = qs.filter(organization_id=organization_id).count()
        data = {'count': assessment_count}
        return Response(data)

    @action(methods=('get',), detail=False, url_path='summary')
    def summary(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        summary = utils.get_summary(queryset)
        return Response(summary)

    def filter_qs_from_param(self, queryset):
        if self.request.method == 'GET':
            query_params = self.request.query_params
        else:
            query_params = self.request.data
        issue_date_gte = query_params.get('issue_date_gte')
        if issue_date_gte:
            queryset = queryset.filter(issue__issue_date__gte=issue_date_gte)
        issue_date_lte = query_params.get('issue_date_lte')
        if issue_date_lte:
            queryset = queryset.filter(issue__issue_date__lte=issue_date_lte)
        categories = query_params.get('categories')
        if categories:
            if isinstance(categories, str):
                categories_list = categories.split(',')
            else:
                categories_list = categories
            queryset = queryset.filter(issue__issue_category__in=categories_list)
        total_value = query_params.get('total_value')
        if total_value:
            if isinstance(total_value, str):
                total_value_list = total_value.split(',')
            else:
                total_value_list = total_value
            lookup = TotalValueFilterField.get_lookup({'value': total_value_list})
            queryset = queryset.filter(lookup)
        region_id = query_params.get('region')
        if region_id:
            queryset = queryset.filter(location_points__admin_area__parent_id=region_id)
        district_id = query_params.get('district')
        if district_id:
            queryset = queryset.filter(location_points__admin_area_id=district_id)
        return queryset

    @action(methods=('get', 'post'), detail=False, url_path='locations/summary')
    def get_locations_summary(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.filter_qs_from_param(queryset)
        if request.method == 'GET':
            query_params = request.query_params
        else:
            query_params = request.data
        zoom = int(query_params.get('zoom', 13))
        if 'district' in query_params:
            data = utils.get_points_data(queryset, query_params)
            return Response(data)
        if 'region' in query_params and zoom <= 9:
            data = utils.get_regions_districts_data(queryset, query_params, districts=True)
            return Response(data)
        if zoom <= 6:
            data = utils.get_regions_districts_data(queryset, query_params, districts=False)
            return Response(data)
        if 7 <= zoom <= 9:
            data = utils.get_regions_districts_data(queryset, query_params, districts=True)
            return Response(data)
        data = utils.get_points_data(queryset, query_params)
        return Response(data)

    @action(methods=('get',), detail=False, url_path='personal_reception')
    def get_personal_reception(self, request, *args, **kwargs):
        report_id = request.query_params.get('report', None)
        try:
            report = ReportModel.objects.get(
                is_active=True,
                id=report_id
            )
        except ReportModel.DoesNotExist:
            raise drf_exceptions.ValidationError(
                'Ошибка получения отчета'
            )
        else:
            qs = models.IssueModel.objects.filter(
                is_active=True,
                risk_assessments__is_active=True,
                issue_category__code='personal_reception',
                risk_assessments__organization_id=report.contractor_id,
                issue_date__gte=report.parent.start,
                issue_date__lte=report.parent.end,
            ).select_related(
                'personal_reception',
                'personal_reception__status'
            ).order_by(
                '-personal_reception__status__code',
                '-created_at'
            )
            return Response(
                serializers.IssueModelReportUploadSerializer(
                    qs,
                    many=True
                ).data
            )


class IssueCategoriesViewSet(GenericViewSet):
    model = models.IssueCategoryModel
    queryset = model.get_queryset()
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response(
            serializers.IssueCategoryModelListSerializer(
                self.model.get_select_queryset(request),
                many=True
            ).data
        )

    def retrieve(self, request, pk=None):
        return Response(
            serializers.IssueCategoryModelDetailSerializer(
                self.get_object()
            ).data
        )

    @action(methods=('get',), detail=False, url_path='social_statuses')
    def get_social_statuses(self, request, *args, **kwargs):
        qs = models.CitizensSocialStatusModel.objects.filter(is_active=True)
        data = serializers.CitizensSocialStatusModelSerializer(qs, many=True).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='pr_statuses')
    def get_pr_statuses(self, request, *args, **kwargs):
        qs = models.PersonalReceptionStatusModel.objects.filter(is_active=True)
        data = serializers.PersonalReceptionStatusModelSerializer(qs, many=True).data
        return Response(data)
