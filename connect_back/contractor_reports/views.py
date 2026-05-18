from tempfile import NamedTemporaryFile
import uuid
import pyexcelerate

from django.db.models import Sum, F
from django.utils import timezone
from django.http import FileResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import exceptions as drf_exceptions

from common.catalogs.models import ContractorModel
from common.catalogs.serializers import ContractorModelWithDirectorSerializer

from bpms.workgroups.models import WorkgroupModel

from bpms.tasks.models import TaskModel, TaskStatusTypeModel, TaskCooperator, TaskExecutionTimeModel

from . import utils


class ContractorTaskReportView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        root_contractor_id = request.query_params.get('organization')
        if not root_contractor_id:
            return Response()
        user = request.user.profile
        try:
            root_contractor_id = uuid.UUID(root_contractor_id)
        except (ValueError, TypeError):
            raise drf_exceptions.ValidationError('invalid organization id')
        if root_contractor_id not in user.my_organizations:
            return Response()
        try:
            root_contractor = ContractorModel.objects.get(is_active=True, pk=root_contractor_id)
        except ContractorModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Organization not found')
        tasks_qs = TaskModel.objects.filter(is_active=True, organization=root_contractor)
        contractors_id = set(root_contractor.contractor_relations_parent.filter(
            relation_type_id='structural_division',
            is_active=True,
        ).values_list('contractor', flat=True))
        contractors_id.add(root_contractor.pk)
        contractors = ContractorModel.objects.filter(is_active=True, pk__in=contractors_id).order_by('sort', 'name',)
        not_complete_statuses = TaskStatusTypeModel.objects.filter(
            is_active=True,
            task_type='task',
            is_complete=False
        ).values_list('task_status', flat=True)
        contractors_data = []
        now = timezone.now()
        total_tasks_count = 0
        total_overdue_tasks_count = 0
        for contractor in contractors:
            contractor_users_id = contractor.profiles.filter(is_active=True).values_list('pk', flat=True)
            contractor_tasks = tasks_qs.filter(operator__in=contractor_users_id)
            contractor_tasks_count = contractor_tasks.count()
            contractor_overdue_tasks_count = contractor_tasks.filter(
                dead_line__isnull=False,
                dead_line__lt=now,
                status_id__in=not_complete_statuses
            ).count()
            contractor_cooperators_qs = TaskCooperator.objects.filter(
                task__in=tasks_qs,
                user_id__in=contractor_users_id,
            )
            contractor_cooperators_count = contractor_cooperators_qs.count()
            contractor_cooperators_overdue_count = contractor_cooperators_qs.filter(
                task__dead_line__isnull=False,
                task__dead_line__lt=now,
                task__status_id__in=not_complete_statuses
            ).exclude(
                status_id='completed',
            ).count()
            contractor_tasks_count += contractor_cooperators_count
            contractor_overdue_tasks_count += contractor_cooperators_overdue_count

            total_tasks_count += contractor_tasks_count
            total_overdue_tasks_count += contractor_overdue_tasks_count

            contractor_data = ContractorModelWithDirectorSerializer(contractor).data
            contractor_data['tasks_count'] = contractor_tasks_count
            contractor_data['tasks_overdue_count'] = contractor_overdue_tasks_count
            contractors_data.append(contractor_data)
        data = {
            'tasks_count': total_tasks_count,
            'tasks_overdue_count': total_overdue_tasks_count,
            'organizations': contractors_data,
        }
        return Response(data)


class ContractorProjectsReportView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        root_contractor_id = request.query_params.get('organization')
        if not root_contractor_id:
            return Response()
        user = request.user.profile
        try:
            root_contractor_id = uuid.UUID(root_contractor_id)
        except (ValueError, TypeError):
            raise drf_exceptions.ValidationError('invalid organization id')
        if root_contractor_id not in user.my_organizations:
            return Response()
        try:
            root_contractor = ContractorModel.objects.get(is_active=True, pk=root_contractor_id)
        except ContractorModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Organization not found')
        contractors_id = set(root_contractor.contractor_relations_parent.filter(
            relation_type_id='structural_division',
            is_active=True,
        ).values_list('contractor', flat=True))
        contractors_id.add(root_contractor.pk)
        contractors = ContractorModel.objects.filter(is_active=True, pk__in=contractors_id).order_by('sort', 'name', )
        total_projects_count = 0
        contractors_data = []
        for contractor in contractors:
            contractor_projects_qs = contractor.workgroups.filter(is_active=True, is_project=True)
            contractor_projects_count = contractor_projects_qs.count()
            total_projects_count += contractor_projects_count
            contractor_data = ContractorModelWithDirectorSerializer(contractor).data
            contractor_data['projects_count'] = contractor_projects_count
            contractors_data.append(contractor_data)
        data = {
            'projects_count': total_projects_count,
            'organizations': contractors_data,
        }
        return Response(data)


class WorkListFileView(APIView):
    def get(self, request, *args, **kwargs):
        wb = utils.get_project_work_list_wb(request)

        with NamedTemporaryFile() as tmp_file:
            wb.save(tmp_file.name)
            return FileResponse(
                open(tmp_file.name, 'rb', ),
                filename=f'Отчет.xlsx',  # TODO
                as_attachment=True,
            )
