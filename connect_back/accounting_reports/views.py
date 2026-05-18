import os
from tempfile import NamedTemporaryFile

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse
from rest_framework import exceptions as drf_exceptions
from rest_framework import generics
from rest_framework import status as http_status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.auth_classes import CsrfExemptSessionAuthentication
from common.catalogs.models import ContractorModel
from common.models import BaseModel, File
from common.serializers import AppFileSerializer
from common.views import BaseModelViewSet
from contractor_permissions.models import ContractorPermissionModel
from users.serializers import AppOrganizationSerializer

from . import models, serializers, utils
from .report_types.classes import get_report_type_instance


class AccountingReportsViewSet(BaseModelViewSet):
    model = models.AccountingReportBaseModel
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        instance_id = self.kwargs.get('pk')
        if not instance_id:
            raise drf_exceptions.NotFound()
        obj = BaseModel.objects.super_get(pk=instance_id)
        if obj is None:
            raise drf_exceptions.NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        model = instance._meta.model
        data = model.get_serializer_class(action='retrieve')(instance).data
        return Response(data)

    def create(self, request, *args, **kwargs):
        report_type_code = request.data.get('type')
        if not report_type_code:
            raise drf_exceptions.ValidationError(
                {
                    'error': ['Не указана форма отчётности.', ]
                }
            )
        try:
            report_type_obj = models.AccountingReportTypeModel.objects.get(
                is_active=True,
                code=report_type_code
            )
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError(
                {
                    'error': [f'Не удалось получить форму отчётности \"{report_type_code}\".', ]
                }
            )
        model = apps.get_model(
            'accounting_reports',
            report_type_obj.model_label
        )
        serializer = model.get_serializer_class(action='create')(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        headers = self.get_success_headers(serializer.data)
        data = self.get_serializer(report).data
        return Response(data, status=http_status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'Редактирование запрещено'
            )
        model = instance._meta.model
        serializer = model.get_serializer_class(action='update')(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        data = self.get_serializer(report).data

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(data)

    @action(
            methods=('get',),
            url_path='get_report_types',
            detail=False
    )
    def get_report_types(self, request, *args, **kwargs):
        model = models.AccountingReportTypeModel
        organization = request.query_params.get('organization')
        if not organization:
            return model.objects.none()
        queryset = model.get_queryset()
        user = request.user.profile
        aux_conditions_ids = ContractorPermissionModel.objects.filter(
                contractor_permission_role__contractor=organization,
                contractor_permission_role__is_active=True,
                contractor_permission_role__contractor_profiles__user=user,
                permission_type_id='add_accounting_report',
            ).values_list('aux_conditions', flat=True)
        if not aux_conditions_ids:
            return Response([])
        if None in aux_conditions_ids:
            qs = queryset.filter(
                is_active=True
            )
        else:
            qs = queryset.filter(
                is_active=True,
                id__in=aux_conditions_ids
            )
        data = serializers.AccountingReportTypeModelSerializer(
            qs,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_specificities'
    )
    def get_specificities(self, request, *args, **kwargs):
        queryset = models.SpecificityStructureModel.objects.filter(
            is_active=True
        ).order_by('code')
        data = serializers.SpecificityStructureModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_report_subtypes'
    )
    def get_report_subtypes(self, request, *args, **kwargs):
        queryset = models.AccountingReportSubtypeModel.objects.filter(
            is_active=True
        ).order_by('code')
        data = serializers.AccountingReportSubtypeModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_rationales'
    )
    def get_rationales(self, request, *args, **kwargs):
        queryset = models.RationaleModel.objects.filter(
            is_active=True
        )
        data = serializers.RationaleModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(methods=('get',),
            detail=True,
            url_path='action_info',
            permission_classes=(IsAuthenticated,))
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            Response(status=http_status.HTTP_404_NOT_FOUND)
        actions = dict()

        if instance.get_detail_permission(request):
            actions['open'] = {'availability': True}
            if instance.type_id == 'finance_plan_change':
                actions['export_to_1c'] = {'availability': True}

        if instance.get_update_permission(request):
            actions['edit'] = {'availability': True}
            actions['delete'] = {'availability': True}

        return Response({'actions': actions})

    @action(methods=('get',),
            detail=False,
            url_path='get_reports',
            permission_classes=(IsAuthenticated,))
    def get_reports(self, request, *args, **kwargs):
        report_type_code = request.query_params.get('report_type')
        if not report_type_code:
            raise drf_exceptions.NotFound()
        report_type_class = get_report_type_instance(report_type_code)
        if report_type_class is None:
            raise drf_exceptions.ValidationError(
                f'Не удалось найти класс формы отчётности {report_type_code}'
            )
        data = report_type_class.get_reports_for_consolidation(request)
        return Response(data)

    @action(methods=('post',),
            detail=True,
            url_path='delete',
            permission_classes=(IsAuthenticated,))
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'Этот отчет удалить нельзя.'
            )

        proposals = instance.proposal_items.all()
        with transaction.atomic():
            instance.is_active = False
            instance.save(update_fields=('is_active',))
            if proposals:
                for proposal in proposals:
                    proposal.is_active = False
                    proposal.save(update_fields=('is_active', ))

        return Response(status=http_status.HTTP_204_NO_CONTENT)

    @action(methods=('get',),
            detail=True,
            url_path='get_upload_for_1C',
            permission_classes=(IsAuthenticated,))
    def get_upload_for_1C(self, request, *args, **kwargs):
        instance = self.get_object()
        workbook = utils.get_upload_for_1C([instance,])
        with NamedTemporaryFile(delete=False) as tmp:
            workbook.save(tmp.name)
        with open(tmp.name, 'rb') as tmp_f:
            response = FileResponse(ContentFile(tmp_f.read()))
        os.remove(tmp.name)
        return response


class GetOrganizationsViewSet(generics.ListAPIView):
    serializer_class = AppOrganizationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user.profile
        return user.contractors.filter(is_active=True)


class UploadExpenseReportView(APIView):
    permission_classes = (
        IsAuthenticated,
    )
    authentication_classes = (
        JWTAuthentication,
        BasicAuthentication,
        CsrfExemptSessionAuthentication,
    )

    def post(self, request, *args, **kwargs):
        contractor_id = request.data.get('contractor')
        try:
            contractor = ContractorModel.objects.get(pk=contractor_id, is_active=True)
        except (ContractorModel.DoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError("Contractor not found.")
        budget_program_admin = contractor.budget_program_administrator
        if not budget_program_admin:
            raise drf_exceptions.ValidationError("Contractor does not have a budget program administrator.")
        files = request.FILES.getlist('upload')
        if not files:
            raise drf_exceptions.ValidationError('File not found')
        data = utils.parse_expense_report_from_pdf(files[0], budget_program_admin)
        if data:
            obj = File.objects.create(
                is_confined=True,
                upload=files[0]
            )
            file = AppFileSerializer(obj).data
        else:
            file = None
        result = {
            'file': file,
            'file_data': data
        }
        return Response(result)
