from tempfile import NamedTemporaryFile

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import (Count, ExpressionWrapper, F,
                              FloatField, Q, Sum, Window)
from django.http.response import FileResponse, Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.views import BaseModelViewSet
from common.accounting_catalogs.utils_location import get_locations_queryset, get_location_structure

from . import models, permissions, serializers, utils


FUNDING_CODES = ['nf', 'rb', 'mb', 'other']
FUNDING_NAMES = {
    'nf': _('НФ'),
    'rb': _('РБ'),
    'mb': _('МБ'),
    'other': _('Другие')
}


class InvestProjectInfoModelViewSet(BaseModelViewSet):
    model = models.InvestProjectInfoModel
    permission_classes = (IsAuthenticated, permissions.InvestProjectModelPermission)

    @action(methods=('post',), detail=True, url_path='add_project',)
    def add_project(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request, is_add_project=True):
            raise drf_exceptions.ValidationError(
                {
                    'message': 'Внесение изменений в инвестиционный проект запрещено.'
                }
            )
        if instance.project:
            raise drf_exceptions.ValidationError(
                {
                    'message': 'К инвестиционному проекту уже привязан проект.'
                }
            )
        utils.add_project(instance, request)
        return Response(status=201, data=instance.project_id)

    @action(methods=('get',), detail=False, url_path='category_statistics',)
    def get_category_statistics(self, request, *args, **kwargs):
        """Статистика по количеству проектов в разбивке по категории"""
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset.values('category_id')
            .order_by()
            .distinct()
            .annotate(
                total_count=Window(
                    expression=Count('id')
                )
            )
            .annotate(
                category_count=Window(
                    expression=Count('id'),
                    partition_by=[F('category_id')]
                )
            )
            .annotate(
                category_percent=ExpressionWrapper(
                    F('category_count') * 100.0 / F('total_count'),
                    output_field=FloatField()
                )
            )
            .values(
                'category_id',
                'total_count',
                'category_count',
                'category_percent'
            )
        )
        return Response(serializers.InvestCategoryStatisticsSerializer(queryset, many=True).data)

    @action(methods=('get',), detail=False, url_path='funding_source_statistics',)
    def get_funding_source_statistics(self, request, *args, **kwargs):
        """Статистика по сумме финансирования в разбивке по источнику.
        Источники финансирования ограничены списком, остальные не учитываются."""
        qs = utils.get_funding_statistics(
            queryset=self.filter_queryset(self.get_queryset()),
            funding_codes=FUNDING_CODES
        )
        result = dict()
        result['grand_total'] = f'{qs["grand_total"]:,.2f}'.replace(',', ' ') if qs['grand_total'] else 0
        result['statistic'] = [{
            'source': FUNDING_NAMES[item],
            'value': f'{qs[item]:,.2f}'.replace(',', ' ') if qs[item] else '0.00',
            'percent': round((qs[item]/qs['grand_total'])*100, 1) if qs['grand_total'] else 0
        } for item in FUNDING_CODES]
        return Response(result)

    @action(methods=('get',), detail=False, url_path='(?P<reg_code>[^/.]+)/region_statistics')
    def get_region_statistics(self, request, reg_code='', *args, **kwargs):

        request_type = request.query_params.get('type', None)
        dateStart_start = request.query_params.get('dateStart_start', None)
        dateStart_end = request.query_params.get('dateStart_end', None)
        deadLine_start = request.query_params.get('deadLine_start', None)
        deadLine_end = request.query_params.get('deadLine_end', None)

        result = dict()
        lookup = Q(is_active=True)
        if reg_code[-2:] != '00':
            lookup &= Q(location__ab=reg_code[-2:])
        if dateStart_start is not None:
            lookup &= Q(date_start__gte=dateStart_start)
        if dateStart_end is not None:
            lookup &= Q(date_start__lte=dateStart_end)
        if deadLine_start is not None:
            lookup &= Q(dead_line__gte=deadLine_start)
        if deadLine_end is not None:
            lookup &= Q(dead_line__lte=deadLine_end)

        if request_type == 'funds':
            qs = utils.get_funding_statistics(
                queryset=self.model.objects.filter(lookup),
                funding_codes=FUNDING_CODES
            )
            result['grand_total'] = f'{qs["grand_total"]:,.2f}'.replace(',', ' ') if qs['grand_total'] else 0
            result['statistic'] = [{
                'name': FUNDING_NAMES[item],
                'value': f'{qs[item]:,.2f}'.replace(',', ' ') if qs[item] else '0.00',
                'percent': round((qs[item]/qs['grand_total'])*100, 1) if qs['grand_total'] else 0
            } for item in FUNDING_CODES if reg_code[-2:] == '00' or qs[item]]
        elif request_type == 'projects':
            qs = (
                self.model.objects
                .filter(lookup)
                .values('category__name')
                .annotate(total=Count('id'))
                .order_by()
            )
            grand_total = sum(item["total"] for item in qs)
            result['grand_total'] = grand_total
            result['statistic'] = [{
                'name': item['category__name'],
                'value': item['total'],
                'percent': round((item['total']/grand_total)*100, 1)
            } for item in qs]
        else:
            pass

        return Response(result)

    @action(methods=('get',), detail=False, url_path='statistics')
    def get_statistics(self, request, *args, **kwargs):
        request_type = request.query_params.get('type', None)
        dateStart_start = request.query_params.get('dateStart_start', None)
        dateStart_end = request.query_params.get('dateStart_end', None)
        deadLine_start = request.query_params.get('deadLine_start', None)
        deadLine_end = request.query_params.get('deadLine_end', None)

        lookup = Q(is_active=True)
        if dateStart_start is not None:
            lookup &= Q(date_start__gte=dateStart_start)
        if dateStart_end is not None:
            lookup &= Q(date_start__lte=dateStart_end)
        if deadLine_start is not None:
            lookup &= Q(dead_line__gte=deadLine_start)
        if deadLine_end is not None:
            lookup &= Q(dead_line__lte=deadLine_end)

        if request_type == 'funds':
            qs = (
                self.model.objects
                .filter(lookup)
                .values('location__ab')
                .annotate(total=Sum('funding_sources__amount'))
                .order_by()
            )
        elif request_type == 'projects':
            qs = (
                self.model.objects
                .filter(lookup)
                .values('location__ab')
                .annotate(total=Count('id'))
                .order_by()
            )
        else:
            qs = self.model.objects.none()
        result = {
            f'KZ{item["location__ab"]}': f'{item["total"]:,.2f}'.replace(',', ' ') if (request_type == 'funds') else item['total'] for item in qs if item['total']
        }
        return Response(result)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        edit = []  # список редактируемых полей
        actions = dict()  # словарь возможных действий с инвестпроектом

        if instance.get_update_permission(request):
            actions['edit'] = {"availability": True}
            edit = [
                'bank_funds',
                'borrowed_funds',
                'cadaster',
                'company_bin',
                'company_director_name',
                'company_name',
                'company_phone',
                'date_start',
                'dead_line',
                'documents',
                'fin_institute',
                'foreign_investor_info',
                'funding_sources',
                'funds',
                'has_documentation',
                'infrastructure_info',
                'installation_stage',
                'jobs_permanent',
                'jobs_temporary',
                'measure_unit',
                'organization',
                'own_funds',
                'pasture_quantity',
                'plowed_field_quantity',
                'project_capacity',
                'project_name',
                'questions',
                'stage',
                'types_of_products',
                'work_experience',
            ]
        if instance.get_update_status_permission(request):
            actions['change_status'] = {"availability": True}
        if instance.get_delete_permission(request):
            actions['delete'] = {"availability": True}
        if instance.project is None and instance.status_id == 'approved':
            actions['add_project'] = {"availability": True}
        actions['copy'] = {"availability": True}
        actions['share'] = {"availability": True}
        actions['view'] = {"availability": instance.get_detail_permission(request)}

        data = {"actions": actions}
        if edit:
            data['edit'] = edit
        return Response(data)

    @action(methods=('post', 'get'), detail=False, url_path='file')
    def get_file(self, request, *args, **kwargs):
        if request.method == 'POST':
            request.query_params._mutable = True
            import json
            for key, value in request.data.items():
                if isinstance(value, dict):
                    request.query_params[key] = json.dumps(value)
                else:
                    request.query_params[key] = value
            request.query_params._mutable = False
            exclude = request.data.get('exclude', [])
        else:
            exclude_str = request.query_params.get('exclude')
            if exclude_str:
                exclude = exclude_str.split(',')
            else:
                exclude = []
        from common.utils import get_filter_queryset
        file_type = request.query_params.get('file_type', '')
        try:
            invest_projects = get_filter_queryset(
                request,
                self.model,
                self.model.get_queryset(request).exclude(pk__in=exclude)
            )
        except ValidationError:
            raise drf_exceptions.ValidationError({"message": "Некорректные данные для выгрузки."})
        if file_type == 'roadmap':
            workbook = utils.get_file_roadmap_from_invest_projects_2(invest_projects)
            file_name = 'Дорожная_карта_по_инвест_проектам.xlsx'
        else:
            workbook = utils.get_file_from_invest_projects(invest_projects)
            file_name = 'Выгрузка_информации_по_инвестиционным_проектам.xlsx'
        with NamedTemporaryFile() as tmp:
            workbook.save(tmp.name)
            return FileResponse(open(tmp.name, 'rb'), filename=file_name)

    @action(methods=('put',), detail=True, url_path='update_status',
            permission_classes=(permissions.UpdateInvestProjectStatusPermission,),)
    def update_status(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        serializer = serializers.UpdateStatusInvestProjectSerializer(instance=instance, data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='status', permission_classes=(IsAuthenticated,))
    def get_status(self, request, *args, **kwargs):
        """Список статусов, которые текущий пользователь может присваивать инвестпроекту"""
        from contractor_permissions.utils import check_contractor_permission
        from .utils import get_invest_project_approver_organizations

        queryset = models.InvestProjectStatusModel.objects.filter(is_active=True).exclude(code='draft')
        user = request.user.profile
        instance = self.get_object()
        create_permission_id = models.InvestProjectPermissionTypeModel.objects.get(code='create')

        try:
            check_contractor_permission(user.pk, instance.organization.pk, 'create_invest_projects_info', create_permission_id)
        except drf_exceptions.PermissionDenied:
            create_permission = False
        else:
            create_permission = True

        approver_organizations = get_invest_project_approver_organizations(request)
        if instance.organization.pk in approver_organizations:
            approve_permission = True
        else:
            approve_permission = False

        creator_can_set_statuses = ['on_check', 'change_requested']
        approver_can_set_statuses = ['on_rework', 'approved', 'completed', 'archive']

        if create_permission and approve_permission:
            queryset = queryset # do nothing
        elif create_permission:
            queryset = queryset.filter(code__in=creator_can_set_statuses)
        elif approve_permission:
            queryset = queryset.filter(code__in=approver_can_set_statuses)
        else:
            return Response([])
        return Response(serializers.InvestProjectStatusWithDependsSerializer(queryset, many=True).data)

    @action(methods=('put',), detail=False, url_path='delete',
            permission_classes=(permissions.DeleteInvestProjectPermission,),)
    def delete(self, request, *args, **kwargs):
        serializer = serializers.DeleteInvestProjectSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invest_project = models.InvestProjectInfoModel.objects.get(is_active=True, pk=self.request.data.get('id'))
        except ObjectDoesNotExist:
            raise Http404
        self.check_object_permissions(self.request, invest_project)

        invest_project.is_active = False
        invest_project.deleted_at = timezone.now()
        invest_project.save(update_fields=('is_active', 'deleted_at',))
        return Response('ok', status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='status_statistics',)
    def get_status_statistics(self, request, *args, **kwargs):
        """Статистика по количеству проектов в каждом статусе."""
        queryset = self.filter_queryset(self.get_queryset())
        count_queryset = (
            queryset.values('status')
            .order_by()
            .annotate(count=Count('id'))
            .values(
                'status',
                'count',
            )
        )
        status_queryset = models.InvestProjectStatusModel.get_select_queryset(request)
        status_codes = status_queryset.values_list('code', flat=True)
        results_dict = {'total': queryset.count()}
        results_dict.update({status: 0 for status in status_codes})

        for entry in count_queryset:
            results_dict.update({entry['status']: entry['count']})
        results = [{'status': key, 'count': value} for key, value in results_dict.items()]
        return Response(serializers.InvestStatusStatisticsSerializer(results, many=True).data)
