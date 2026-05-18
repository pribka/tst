from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, exceptions

from common.views import BaseModelViewSet
from common.utils import get_datetime_param
from . import models
from .utils import rebuild_execution_time_registers, cleanup_orphaned_helpdesk_work_log_registers
from bpms.tasks import models as tasks_models
from help_desk.models import HelpDeskTicketModel


class AccumulationRegisterViewSet(BaseModelViewSet):
    model = models.AccumulationRegister
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=('get',), detail=False, url_path='my_day_statistics')
    def my_day_statistics(self, request, *args, **kwargs):
        user_param = request.query_params.get('user')
        start = get_datetime_param(request, 'start')
        end = get_datetime_param(request, 'end')
        profile_id = request.user.profile.pk

        if user_param:
            user_ids = user_param.split(',')
        else:
            user_ids = [str(profile_id)]

        if not start or not end:
            current_date = timezone.localdate()
            start_date = current_date
            end_date = current_date
        else:
            start_date = parse_date(start.split('T')[0])
            end_date = parse_date(end.split('T')[0])
            if not start_date or not end_date:
                current_date = timezone.localdate()
                start_date = current_date
                end_date = current_date

        # Intentionally no permission filter here:
        # this endpoint returns pure aggregates from AccumulationRegister.
        qs = models.AccumulationRegister.objects.filter(
            is_active=True,
            section_id='work_costs',
            user_id__in=user_ids,
            period__date__gte=start_date,
            period__date__lte=end_date,
        )

        task_ct = ContentType.objects.get_for_model(tasks_models.TaskModel)
        helpdesk_ticket_ct = ContentType.objects.get_for_model(HelpDeskTicketModel)

        total_quantity_fact = float(
            qs.aggregate(total=Sum('quantity_fact'))['total'] or 0
        )
        total_quantity_fact_tasks = float(
            qs.filter(registrar__ct_id=task_ct.id).aggregate(
                total=Sum('quantity_fact')
            )['total'] or 0
        )
        total_quantity_fact_helpdesk = float(
            qs.filter(registrar__ct_id=helpdesk_ticket_ct.id).aggregate(
                total=Sum('quantity_fact')
            )['total'] or 0
        )

        total_duration = int(total_quantity_fact * 3600)
        total_duration_tasks = int(total_quantity_fact_tasks * 3600)
        total_duration_helpdesk = int(total_quantity_fact_helpdesk * 3600)

        work_type_stats = list(
            qs.values('work_type_id')
            .annotate(quantity_fact=Sum('quantity_fact'))
            .order_by('work_type__sort')
        )

        work_type_ids = [
            stat['work_type_id']
            for stat in work_type_stats
            if stat['work_type_id']
        ]
        work_type_objects = {}
        if work_type_ids:
            task_work_types = tasks_models.TaskWorkTypeModel.objects.filter(
                pk__in=work_type_ids,
                is_active=True,
            ).values('pk', 'name', 'icon', 'hex_color')
            work_type_objects = {wt['pk']: wt for wt in task_work_types}

        by_work_type = []
        for stat in work_type_stats:
            quantity = float(stat['quantity_fact'] or 0)
            quantity_percentage = (
                (quantity / total_quantity_fact * 100)
                if total_quantity_fact > 0 else 0
            )
            duration = int(quantity * 3600)
            duration_percentage = (
                (duration / total_duration * 100)
                if total_duration > 0 else 0
            )
            work_type_id = stat['work_type_id']
            work_type_data = work_type_objects.get(work_type_id, {})
            by_work_type.append({
                'work_type_name': work_type_data.get('name', ''),
                'work_type_icon': work_type_data.get('icon', ''),
                'work_type_color': work_type_data.get('hex_color', ''),
                'quantity_fact': quantity,
                'quantity_percentage': round(quantity_percentage, 2),
                'duration': duration,
                'duration_percentage': round(duration_percentage, 2),
            })

        response_data = {
            'total_quantity_fact': total_quantity_fact,
            'total_quantity_fact_tasks': total_quantity_fact_tasks,
            'total_quantity_fact_helpdesk': total_quantity_fact_helpdesk,
            'total_duration': total_duration,
            'total_duration_tasks': total_duration_tasks,
            'total_duration_helpdesk': total_duration_helpdesk,
            'by_work_type': by_work_type,
        }
        return Response(response_data)


class RebuildExecutionTimeRegistersView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')

        results = rebuild_execution_time_registers()
        return Response(results, status=status.HTTP_200_OK)


class CleanupOrphanedHelpDeskWorkLogRegistersView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')

        results = cleanup_orphaned_helpdesk_work_log_registers()
        return Response(results, status=status.HTTP_200_OK)
