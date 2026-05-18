from django.core.exceptions import ValidationError
from django_q.tasks import async_task
from rest_framework import exceptions as drf_exceptions
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.auth_classes import CsrfExemptSessionAuthentication
from common.catalogs.models import ContractorModel

from . import models, serializers, utils, utils_location


class ClassificationOfBudgetExpensesViewSet(ViewSet):
    @action(
        methods=('get',),
        detail=False,
        url_path='get_functional_groups'
    )
    def get_functional_groups(self, request, *args, **kwargs):
        queryset = models.BudgetFunctionalGroupModel.objects.filter(
            is_active=True
        ).order_by('code')
        data = serializers.BudgetFunctionalGroupModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_functional_subgroups'
    )
    def get_functional_subgroups(self, request, *args, **kwargs):
        functional_group = request.query_params.get('functional_group')
        if not functional_group:
            raise drf_exceptions.NotFound()
        queryset = models.BudgetFunctionalSubgroupModel.objects.filter(
            is_active=True,
            functional_group_id=functional_group
        ).order_by('code')
        data = serializers.BudgetFunctionalSubgroupModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_budget_program_administrators'
    )
    def get_budget_program_administrators(self, request, *args, **kwargs):
        functional_subgroup = request.query_params.get('functional_subgroup')
        if not functional_subgroup:
            raise drf_exceptions.NotFound()
        queryset = models.BudgetProgramAdministratorModel.objects.filter(
            is_active=True,
            functional_subgroup_id=functional_subgroup
        ).order_by('code')
        data = serializers.BudgetProgramAdministratorModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_programs'
    )
    def get_programs(self, request, *args, **kwargs):
        budget_program_administrator = request.query_params.get('budget_program_administrator')
        if not budget_program_administrator:
            raise drf_exceptions.NotFound()
        queryset = models.BudgetProgramModel.objects.filter(
            is_active=True,
            budget_program_administrator=budget_program_administrator
        ).order_by('code')
        data = serializers.BudgetProgramModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='get_subprograms'
    )
    def get_subprograms(self, request, *args, **kwargs):
        program = request.query_params.get('program')
        if not program:
            raise drf_exceptions.NotFound()
        queryset = models.BudgetSubprogramModel.objects.filter(
            is_active=True,
            program=program
        ).order_by('code')
        data = serializers.BudgetSubprogramModelSerializer(
            queryset,
            many=True
        ).data
        return Response(data)

    @action(
        methods=('get',),
        detail=False,
        url_path='budget_program_admin_by_contractor'
    )
    def get_budget_program_admin_by_contractor(self, request, *args, **kwargs):
        contractor_id = request.query_params.get('contractor')
        if not contractor_id:
            raise drf_exceptions.ValidationError('Contractor is required.')
        try:
            contractor = ContractorModel.objects.get(is_active=True, pk=contractor_id)
        except (ContractorModel.DoesNotExist, ValidationError):
            raise drf_exceptions.NotFound('Contractor not found.')
        budget_admin = contractor.budget_program_administrator
        if not budget_admin:
            return Response(dict())
        functional_subgroup = budget_admin.functional_subgroup
        if not functional_subgroup:
            return Response(dict())
        functional_group = functional_subgroup.functional_group
        if not functional_group:
            return Response(dict())
        data = {
            'functional_group': serializers.BudgetFunctionalGroupModelSerializer(functional_group).data,
            'functional_subgroup': serializers.BudgetFunctionalSubgroupModelSerializer(functional_subgroup).data,
            'budget_program_administrator': serializers.BudgetProgramAdministratorModelSerializer(budget_admin).data,
        }

        return Response(data)


class SetBudgetAdministrators(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JWTAuthentication,
        BasicAuthentication,
        CsrfExemptSessionAuthentication,
    )

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('upload')
        if not files:
            raise drf_exceptions.ValidationError('File not found.')
        utils.set_budget_administrators_from_xlsx(files[0])
        return Response('ok')


class SetKATOCodes(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        files = request.FILES.getlist('upload')
        if not files:
            raise drf_exceptions.ValidationError('File not found.')
        utils.set_kato_codes_from_xlsx(files[0])
        return Response('ok')


class LocationViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.KATOCodesModel.objects.filter(is_active=True)

    def get_serializer_class(self):
        return serializers.CachedKATOCodesModelSerializer

    def list(self, request, *args, **kwargs):
        parent = request.query_params.get('parent', None)
        if parent is None:
            return Response(data=[])

        queryset = utils_location.get_locations_queryset(parent).values_list('pk', flat=True)
        data = serializers.CachedKATOCodesModelSerializer(
            queryset,
            many=True,
            context={'request': request}
            ).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='structure')
    def get_location_structure(self, request, *args, **kwargs):
        location = request.query_params.get('location', None)
        if location is None:
            return Response(dict())

        return Response(utils_location.get_location_structure(location))

