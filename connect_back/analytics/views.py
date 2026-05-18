import copy
import datetime
import json

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_q.tasks import async_task

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils import timezone
from common import models as common_models
from common.views import BaseModelViewSet
from common import serializers as common_serializers
from contractor_permissions.utils import check_user_app_section_role_permission
from users.serializers import CachedAppUserPreviewSerializer
from bpms.comments.models import CommentModel
from bpms.meetings.models import MeetingSectionModel, PlannedMeetingModel
from bpms.tasks.models import TaskExecutionTimeModel, TaskModel
from bpms.workgroups.models import WorkgroupModel
from bpms.workgroups.utils import get_workgroup_queryset
from bpms.tasks.utils import filter_by_permissions, get_cached_statuses
from common.estimates.models import AccumulationRegister
from help_desk.models import HelpDeskTicketModel, CustomerCardModel
from help_desk.utils import get_completed_statuses_id
from customer_contracts.models import CustomerContractModel
from bpms.processes.models import WorkflowRequestModel
from common.catalogs.models import ContractorProfileModel

from .models import ActivityDigestModel, ActivitySummaryModel
from .models import DashboardSectionModel, DashboardConfigModel


class IsSuperuser(IsAuthenticated):
    """Доступ только для суперпользователя (пока тестирование)."""
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.is_authenticated
            and request.user.is_superuser
        )


from .utils import collect_data as collect_data_utils
from .utils.collect_data import _to_date
from .utils.analyze_data import (
    analyze_digest_period,
    create_digest_data,
    process_activity_summary_queue,
    collect_raw_activity_context,
)


class ActivityViewSet(BaseModelViewSet):
    """
    Эндпоинты контекста деятельности за период (для анализа / LLM).
    GET list: сырые подготовленные данные за период до передачи в LLM (тестовый эндпоинт для визуального анализа).
    Параметры: start, end, related_object, scope (обязательны); sources (опционально — tasks,meetings,events,helpdesk,chats через запятую, по умолчанию tasks).
    """
    model = common_models.BaseModel
    permission_classes = (IsSuperuser,)

    def get_queryset(self):
        return self.model.objects.none()

    def list(self, request, *args, **kwargs):
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        related_object = request.query_params.get("related_object")
        scope = request.query_params.get("scope")
        sources_param = request.query_params.get("sources")
        date_from = _to_date(start)
        date_to = _to_date(end)
        if date_from is None or date_to is None:
            return Response(
                {"error": "Некорректный формат start или end."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sources = [s.strip() for s in (sources_param or "").split(",") if s.strip()]

        context = collect_raw_activity_context(
            related_object_id=related_object,
            scope_type=scope,
            date_from=date_from,
            date_to=date_to,
            sources=sources,
        )
        context_str = json.dumps(context, ensure_ascii=False)
        total_chars = len(context_str)
        print(f"analytics context: всего {total_chars} символов")
        for key in context:
            section_str = json.dumps(context[key], ensure_ascii=False)
            print(f"  {key}: {len(section_str)} символов")
        return Response(context)


class ActivityDigestViewSet(BaseModelViewSet):
    """CRUD по дайджестам активности (ActivityDigestModel)."""
    model = ActivityDigestModel
    permission_classes = (IsSuperuser,)

    @action(methods=["get", "post"], detail=False, url_path="create_digest")
    def create_digest(self, request, *args, **kwargs):
        """
        POST (или GET с query): start, end, related_object (UUID), scope (organization|project|workgroup|user) — обязательны;
        опционально sources — через запятую (по умолчанию tasks).
        """
        data = request.query_params if request.method == "GET" else (request.data or {})
        start_param = data.get("start")
        end_param = data.get("end")
        related_object_id = data.get("related_object")
        scope = data.get("scope")
        sources_param = data.get("sources")

        if not related_object_id or not scope:
            return Response(
                {"error": "Параметры related_object и scope обязательны (scope: organization, project, workgroup, user)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from = _to_date(start_param)
        date_to = _to_date(end_param)
        sources = [s.strip() for s in (sources_param or "").split(",") if s.strip()]

        create_digest_data(
            start=date_from,
            end=date_to,
            related_object_id=related_object_id,
            scope_type=scope,
            sources=sources,
        )
        return Response({"status": "ok", "start": str(date_from), "end": str(date_to), "sources": sources})

    @action(
        methods=["post"],
        detail=False,
        url_path="delete_digest_period",
        permission_classes=[IsSuperuser],
    )
    def delete_digest_period(self, request, *args, **kwargs):
        """
        POST: удаление дайджестов за период по scope и source.
        Параметры в body: start, end, scope (обязательные), source (опционально).
        source может быть строкой с одним источником или CSV-списком (tasks,meetings,...).
        """
        data = request.data or {}
        start_param = data.get("start")
        end_param = data.get("end")
        scope = data.get("scope")
        source_param = data.get("source", "")

        if not start_param or not end_param or not scope:
            return Response(
                {"error": "Параметры start, end и scope обязательны."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from = _to_date(start_param)
        date_to = _to_date(end_param)
        if date_from is None or date_to is None:
            return Response(
                {"error": "Некорректный формат start или end."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if date_from > date_to:
            return Response(
                {"error": "start не может быть больше end."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sources = [source_item.strip() for source_item in (source_param or "").split(",") if source_item.strip()]

        digest_queryset = ActivityDigestModel.objects.filter(
            scope=scope,
            date__gte=date_from,
            date__lte=date_to,
        )
        if sources:
            digest_queryset = digest_queryset.filter(source__in=sources)

        deleted_count, delete_details = digest_queryset.delete()

        return Response(
            {
                "status": "ok",
                "deleted": deleted_count,
                "details": delete_details,
                "start": str(date_from),
                "end": str(date_to),
                "scope": scope,
                "sources": sources,
            },
            status=status.HTTP_200_OK,
        )


class ActivitySummaryViewSet(BaseModelViewSet):
    """CRUD и действия по саммари активности (ActivitySummaryModel)."""
    model = ActivitySummaryModel

    @action(methods=["get"], detail=False, url_path="related_object_preview")
    def related_object_preview(self, request, *args, **kwargs):
        """
        GET: related_object (UUID). Объект берётся через BaseModel.super_get, тип по instance._meta.label_lower:
        users.profilemodel -> CachedAppUserPreviewSerializer, иначе SelectListSerializer.
        """
        related_object_id = request.query_params.get("related_object")
        instance = common_models.BaseModel.objects.super_get(pk=related_object_id)
        if not instance.get_detail_permission(request):
            raise PermissionDenied()
        if instance._meta.label_lower == "users.profilemodel":
            data = CachedAppUserPreviewSerializer(instance=instance).data
        else:
            data = common_serializers.SelectListSerializer(instance=instance).data
        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        POST: стартует асинхронную генерацию саммари и сразу возвращает ActivitySummaryModel со статусом pending.
        Параметры в body: start, end, related_object (UUID), scope (organization|project|workgroup|user); sources через запятую.
        """
        data = request.data or {}
        start_param = data.get("start")
        end_param = data.get("end")
        related_object_id = data.get("related_object")
        scope = data.get("scope")
        sources_param = data.get("sources", "")
        if not sources_param:
            if scope in ("organization", "project", "workgroup", "user_day_summary"):
                sources_param = "tasks,meetings,helpdesk"
            elif scope in ("user",):
                sources_param = "tasks,meetings,helpdesk" # day_summary - пока уберем

        if not start_param or not end_param:
            return Response(
                {"error": "Параметры start и end обязательны."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not related_object_id or not scope:
            return Response(
                {"error": "Параметры related_object и scope обязательны."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user.profile
        user_pk_str = str(user.pk)
        related_object_id_str = str(related_object_id)
        try:
            original_object = common_models.BaseModel.objects.super_get(pk=related_object_id)
        except (ObjectDoesNotExist, ValidationError):
            return Response(
                {"error": "Объект related_object не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        has_permission = False
        if scope == "organization":
            has_permission = (
                original_object._meta.label_lower == "catalogs.contractormodel"
                and original_object.get_update_permission(request)
            )
        elif scope in ("project", "workgroup"):
            has_permission = (
                original_object._meta.label_lower == "workgroups.workgroupmodel"
                and original_object.get_update_permission(request)
            )
        elif scope in ("user", "user_day_summary"):
            is_self_user_scope = related_object_id_str == user_pk_str
            if is_self_user_scope:
                has_permission = True
            elif original_object._meta.label_lower == "users.profilemodel":
                target_user_organizations = tuple(original_object.my_organizations)
                if target_user_organizations:
                    has_permission = check_user_app_section_role_permission(
                        profile_id=user.pk,
                        app_section_code="pulse",
                        contractor_ids=target_user_organizations,
                        role="worker",
                    )

        if not has_permission:
            return Response(
                {"error": "Недостаточно прав для запуска анализа по указанному объекту."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if start_param and "T" in start_param:
            start_param = start_param.split("T")[0]
        if end_param and "T" in end_param:
            end_param = end_param.split("T")[0]
        date_from = _to_date(start_param)
        date_to = _to_date(end_param)
        today = timezone.localdate()
        if date_to and date_to > today:
            date_to = today


        sources = [s.strip() for s in (sources_param or "").split(",") if s.strip()]
        sources_str = ",".join(sources)

        existing_pending = ActivitySummaryModel.objects.filter(
            related_object_id=related_object_id,
            user=user,
            scope=scope,
            start_date=date_from,
            end_date=date_to,
            status="pending",
            is_active=True,
        ).order_by("-created_at").first()
        if existing_pending:
            serializer = self.get_serializer(existing_pending)
            return Response(serializer.data, status=status.HTTP_200_OK)

        activity_summary = ActivitySummaryModel.objects.create(
            related_object_id=related_object_id,
            user=user,
            start_date=date_from,
            end_date=date_to,
            sources=sources_str,
            scope=scope,
            status="pending",
            started_at=timezone.now(),
        )

        serializer = self.get_serializer(activity_summary)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")
        if start_param and end_param:
            # Фронт может присылать ISO с временем (?start=2026-01-30T00:00:00.000+03:00) — берём только дату
            start_param = start_param.split("T")[0] if "T" in start_param else start_param
            end_param = end_param.split("T")[0] if "T" in end_param else end_param
            start_date = _to_date(start_param)
            end_date = _to_date(end_param)
        else:
            today = timezone.localdate()
            start_date = end_date = today

        user = request.user.profile
        qs = ActivitySummaryModel.objects.filter(
            user=user,
            is_active=True,
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).exclude(scope="user_day_summary")
        related_object_id = request.query_params.get("related_object")
        if related_object_id:
            qs = qs.filter(related_object_id=related_object_id)
        scope = request.query_params.get("scope")
        if scope:
            qs = qs.filter(scope=scope)
        status_param = request.query_params.get("status")
        if status_param:
            status_values = [s.strip() for s in status_param.split(",") if s.strip()]
            if status_values:
                qs = qs.filter(status__in=status_values)
        qs = qs.order_by("-created_at")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(methods=["get"], detail=False, url_path="pending")
    def pending(self, request, *args, **kwargs):
        """Ожидающие обработки ActivitySummaryModel, созданные текущим пользователем"""
        qs = ActivitySummaryModel.objects.filter(
            user=request.user.profile,
            status="pending",
            is_active=True,
        ).exclude(scope="user_day_summary").order_by("-created_at")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        methods=["get"],
        detail=False,
        url_path="process_queue",
        permission_classes=[IsSuperuser],
    )
    def process_queue(self, request, *args, **kwargs):
        run_sync = request.query_params.get("sync") == "true"

        if run_sync:
            process_activity_summary_queue()
            return Response({"status": "processed_sync"}, status=status.HTTP_200_OK)

        task_id = async_task(
            process_activity_summary_queue,
            q_options={"timeout": 600},
        )
        return Response({"status": "queued", "task_id": task_id}, status=status.HTTP_202_ACCEPTED)

    @action(
        methods=["get"],
        detail=False,
        url_path="collect_digests_for_period",
        permission_classes=[IsSuperuser],
    )
    def collect_digests_for_period(self, request, *args, **kwargs):
        """
        Собирает контекст по предсобранным дайджестам за период для передачи в LLM.
        Query: start, end, related_object, scope (обязательны); sources (опционально — tasks,meetings,events,helpdesk,chats через запятую).
        """
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        related_object = request.query_params.get("related_object")
        scope = request.query_params.get("scope")
        sources_param = request.query_params.get("sources")

        if not start or not end or not related_object or not scope:
            return Response(
                {"error": "Параметры start, end, related_object и scope обязательны."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        date_from = _to_date(start)
        date_to = _to_date(end)
        if date_from is None or date_to is None:
            return Response(
                {"error": "Некорректный формат start или end."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sources = [s.strip() for s in (sources_param or "").split(",") if s.strip()]

        context = collect_data_utils.collect_digests_for_period(
            date_from=date_from,
            date_to=date_to,
            related_object=related_object,
            sources=sources if sources else None,
            scope=scope,
        )
        return Response(context)


class DashboardConfigViewSet(BaseModelViewSet):
    """Выдача конфигураций секций руководительского дашборда."""
    model = DashboardConfigModel
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _merge_dashboard_configs(config_items):
        merged_config = {"groups": []}
        groups_by_code = {}

        for dashboard_config in config_items:
            config_data = dashboard_config.config if isinstance(dashboard_config.config, dict) else {}
            groups = config_data.get("groups")
            if not isinstance(groups, list):
                continue

            for group in groups:
                if not isinstance(group, dict):
                    continue
                group_code = group.get("group_code")
                if not isinstance(group_code, str) or not group_code.strip():
                    continue

                group_widgets = group.get("widgets")
                widgets_to_add = group_widgets if isinstance(group_widgets, list) else []

                existing_group = groups_by_code.get(group_code)
                if existing_group is None:
                    group_copy = copy.deepcopy(group)
                    group_copy["widgets"] = []
                    merged_config["groups"].append(group_copy)
                    groups_by_code[group_code] = group_copy
                    existing_group = group_copy

                existing_group["widgets"].extend(copy.deepcopy(widgets_to_add))

        return merged_config

    def _get_filtered_dashboard_configs(self, request, section=None):
        queryset = super().get_queryset().filter(is_active=True)
        resolved_section = section or request.query_params.get("section")
        if resolved_section:
            queryset = queryset.filter(section=resolved_section)

        scope = request.query_params.get("scope")
        if scope:
            queryset = queryset.filter(scopes__contains=[scope])

        start_date = _to_date(request.query_params.get("start"))
        end_date = _to_date(request.query_params.get("end"))
        if start_date and end_date:
            period_days = (end_date - start_date).days + 1
            queryset = queryset.filter(models.Q(min_days__isnull=True) | models.Q(min_days__lte=period_days))
            queryset = queryset.filter(models.Q(max_days__isnull=True) | models.Q(max_days__gte=period_days))
        return queryset.order_by("sort", "created_at")

    def list(self, request, *args, **kwargs):
        section_code = request.query_params.get("section")
        config_queryset = self._get_filtered_dashboard_configs(request)
        merged_config = self._merge_dashboard_configs(config_queryset)

        if not merged_config.get("groups"):
            return Response({})

        if section_code:
            section_name = DashboardSectionModel.objects.filter(
                code=section_code, is_active=True,
            ).values_list("name", flat=True).first()
            if section_name:
                merged_config["name"] = section_name
        return Response(merged_config)

    @staticmethod
    def _apply_task_scope_filters(queryset, request, include_contract=True, include_user=True):
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        project_id = request.query_params.get("project")
        contract_id = request.query_params.get("contract")
        user_ids = [
            value for value in (request.query_params.get("user") or "").split(",") if value
        ]

        if root_organization_id:
            root_annotations = TaskModel.get_report_annotations(
                request,
                requested_computed=["root_organization"],
            )
            queryset = queryset.annotate(**root_annotations).filter(root_organization=root_organization_id)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if include_contract and contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        if include_user and user_ids:
            queryset = queryset.filter(operator_id__in=user_ids)

        return queryset

    @staticmethod
    def _inject_kpi_values(config_data, kpi_values):
        enriched_data = copy.deepcopy(config_data or {})
        groups = enriched_data.get("groups", [])
        for group in groups:
            widgets = group.get("widgets", [])
            for widget in widgets:
                widget_code = widget.get("widget_code")
                widget["value"] = kpi_values.get(widget_code)
        return enriched_data

    @staticmethod
    def _apply_execution_time_scope_filters(queryset, request):
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        user_ids = [
            value for value in (request.query_params.get("user") or "").split(",") if value
        ]

        if root_organization_id:
            root_annotations = AccumulationRegister.get_report_annotations(
                request,
                requested_computed=["root_organization"],
            )
            queryset = queryset.annotate(**root_annotations).filter(root_organization=root_organization_id)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if user_ids:
            queryset = queryset.filter(user_id__in=user_ids)
        return queryset

    def _get_permitted_tasks_queryset(self, request):
        cached_queryset = getattr(self, "_cached_permitted_tasks_queryset", None)
        if cached_queryset is not None:
            return cached_queryset

        base_tasks_queryset = TaskModel.objects.filter(
            is_active=True,
            task_type_id="task",
        )
        cached_queryset = filter_by_permissions(base_tasks_queryset, request.user.profile)
        self._cached_permitted_tasks_queryset = cached_queryset
        return cached_queryset

    @staticmethod
    def _apply_ticket_execution_time_scope_filters(queryset, request):
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        project_id = request.query_params.get("project")
        contract_id = request.query_params.get("contract")
        user_ids = [
            value for value in (request.query_params.get("user") or "").split(",") if value
        ]

        if root_organization_id:
            root_annotations = CustomerCardModel.get_report_annotations(
                request,
                requested_computed=["root_org_admin"],
                outer_ref_column="customer_card_id",
            )
            queryset = queryset.annotate(
                **root_annotations
            ).filter(root_org_admin=root_organization_id)
        if organization_id:
            queryset = queryset.filter(customer_card__org_admin_id=organization_id)
        if project_id:
            queryset = queryset.filter(analytics_key__project_id=project_id)
        if contract_id:
            queryset = queryset.filter(analytics_key__customer_contract_id=contract_id)
        if user_ids:
            queryset = queryset.filter(specialist_id__in=user_ids)
        return queryset

    def _collect_task_kpi_values(self, request, start_date, end_date):
        cached_statuses = get_cached_statuses()
        not_completed_statuses = cached_statuses[1]
        completed_statuses = cached_statuses[2]
        now_at = timezone.now()
        stale_since_datetime = now_at - datetime.timedelta(days=30)
        stale_since_date = stale_since_datetime.date()

        tasks_queryset = self._get_permitted_tasks_queryset(request)
        tasks_queryset = self._apply_task_scope_filters(tasks_queryset, request)

        not_completed_queryset = tasks_queryset.filter(status_id__in=not_completed_statuses)
        created_in_period_count = tasks_queryset.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).values("pk").distinct().count()
        completed_in_period_count = tasks_queryset.filter(
            status_id__in=completed_statuses,
            finished_date__isnull=False,
            finished_date__date__gte=start_date,
            finished_date__date__lte=end_date,
        ).values("pk").distinct().count()
        overdue_count = not_completed_queryset.filter(
            dead_line__isnull=False,
            dead_line__lt=now_at,
        ).values("pk").distinct().count()

        has_recent_execution = TaskExecutionTimeModel.objects.filter(
            is_active=True,
            task_id=OuterRef("pk"),
            date__gte=stale_since_date,
        )
        has_recent_comments = CommentModel.objects.filter(
            is_active=True,
            related_object_id=OuterRef("pk"),
            created_at__gte=stale_since_datetime,
        )
        stalled_count = not_completed_queryset.annotate(
            has_recent_execution=Exists(has_recent_execution),
            has_recent_comments=Exists(has_recent_comments),
        ).filter(
            has_recent_execution=False,
            has_recent_comments=False,
        ).values("pk").distinct().count()
        return {
            "tasks_not_completed": not_completed_queryset.values("pk").distinct().count(),
            "new_tasks": created_in_period_count,
            "completed_tasks": completed_in_period_count,
            "overdue_tasks": overdue_count,
            "stalled_tasks": stalled_count,
        }

    def _collect_total_execution_time_kpi_values(self, request, start_date, end_date):
        start_datetime = timezone.make_aware(
            datetime.datetime.combine(start_date, datetime.time.min),
            timezone.utc,
        )
        end_datetime = timezone.make_aware(
            datetime.datetime.combine(end_date, datetime.time.max),
            timezone.utc,
        )

        execution_queryset = AccumulationRegister.objects.filter(
            is_active=True,
            section_id="work_costs",
        )
        execution_queryset = execution_queryset.filter(
            period__gte=start_datetime,
            period__lte=end_datetime,
        )
        execution_queryset = self._apply_execution_time_scope_filters(execution_queryset, request)
        execution_queryset = AccumulationRegister.filter_by_permissions(execution_queryset, request)
        aggregated_values = execution_queryset.aggregate(
            total_execution_time=models.Sum("quantity_fact"),
        )
        return {
            "total_execution_time": aggregated_values.get("total_execution_time") or 0,
        }

    def _collect_tasks_execution_time_kpi_values(self, request, start_date, end_date):
        tasks_execution_queryset = TaskExecutionTimeModel.objects.filter(
            is_active=True,
        )
        tasks_execution_queryset = tasks_execution_queryset.filter(
            date__gte=start_date,
            date__lte=end_date,
        )
        allowed_tasks_queryset = TaskModel.objects.filter(
            is_active=True,
            task_type_id="task",
        )
        allowed_tasks_queryset = self._apply_task_scope_filters(
            allowed_tasks_queryset,
            request,
            include_contract=False,
            include_user=False,
        )
        allowed_tasks_queryset = filter_by_permissions(allowed_tasks_queryset, request.user.profile)
        allowed_task_ids = list(allowed_tasks_queryset.values_list("pk", flat=True))
        if not allowed_task_ids:
            return {
                "tasks_execution_time": 0,
            }
        tasks_execution_queryset = tasks_execution_queryset.filter(task_id__in=allowed_task_ids)
        user_ids = [value for value in (request.query_params.get("user") or "").split(",") if value]
        if user_ids:
            tasks_execution_queryset = tasks_execution_queryset.filter(user_id__in=user_ids)
        aggregated_values = tasks_execution_queryset.aggregate(
            tasks_execution_time=models.Sum("hours"),
        )
        return {
            "tasks_execution_time": aggregated_values.get("tasks_execution_time") or 0,
        }

    def _collect_tickets_execution_time_kpi_values(self, request, start_date, end_date):
        tickets_execution_queryset = HelpDeskTicketModel.objects.filter(
            is_active=True,
            ticket_type="issue",
        )
        tickets_execution_queryset = self._apply_ticket_execution_time_scope_filters(tickets_execution_queryset, request)
        tickets_execution_queryset = HelpDeskTicketModel.filter_by_permissions(
            tickets_execution_queryset,
            request,
            view_type="contractor",
        )
        tickets_execution_queryset = tickets_execution_queryset.filter(
            receipt_date__date__gte=start_date,
            receipt_date__date__lte=end_date,
        )
        aggregated_values = tickets_execution_queryset.aggregate(
            tickets_execution_time=models.Sum(
                "work_logs__hours",
                filter=models.Q(work_logs__is_active=True),
            ),
        )
        return {
            "tickets_execution_time": aggregated_values.get("tickets_execution_time") or 0,
        }

    def _collect_ticket_kpi_values(self, request, start_date, end_date):
        completed_statuses = get_completed_statuses_id()
        now_at = timezone.now()

        tickets_queryset = HelpDeskTicketModel.objects.filter(
            is_active=True,
            ticket_type="issue",
        )
        tickets_queryset = self._apply_ticket_execution_time_scope_filters(tickets_queryset, request)
        tickets_queryset = HelpDeskTicketModel.filter_by_permissions(
            tickets_queryset,
            request,
            view_type="contractor",
        )

        not_completed_queryset = tickets_queryset.exclude(status_id__in=completed_statuses)

        new_tickets_queryset = tickets_queryset.filter(
            receipt_date__date__gte=start_date,
            receipt_date__date__lte=end_date,
        )
        completed_tickets_queryset = tickets_queryset.filter(
            status_id__in=completed_statuses,
            end_date__isnull=False,
            end_date__date__gte=start_date,
            end_date__date__lte=end_date,
        )

        overdue_tickets_count = not_completed_queryset.filter(
            dead_line__isnull=False,
            dead_line__lt=now_at,
        ).values("pk").distinct().count()

        return {
            "not_completed_tickets": not_completed_queryset.values("pk").distinct().count(),
            "new_tickets": new_tickets_queryset.values("pk").distinct().count(),
            "completed_tickets": completed_tickets_queryset.values("pk").distinct().count(),
            "overdue_tickets": overdue_tickets_count,
        }

    def _collect_meeting_sessions_kpi_values(self, request, start_date, end_date):
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        project_id = request.query_params.get("project")
        user_ids = [value for value in (request.query_params.get("user") or "").split(",") if value]

        meeting_sections_queryset = MeetingSectionModel.get_queryset(request).filter(
            meeting__project_id__isnull=False,
        )
        if start_date:
            meeting_sections_queryset = meeting_sections_queryset.filter(date_start__date__gte=start_date)
        if end_date:
            meeting_sections_queryset = meeting_sections_queryset.filter(date_start__date__lte=end_date)
        if project_id:
            meeting_sections_queryset = meeting_sections_queryset.filter(meeting__project_id=project_id)
        if organization_id:
            meeting_sections_queryset = meeting_sections_queryset.filter(meeting__project__organization_id=organization_id)
        if root_organization_id:
            root_annotations = PlannedMeetingModel.get_report_annotations(
                request,
                requested_computed=["root_organization"],
                outer_ref_column="meeting_id",
            )
            meeting_sections_queryset = meeting_sections_queryset.annotate(
                **root_annotations
            ).filter(root_organization=root_organization_id)
        if user_ids:
            meeting_sections_queryset = meeting_sections_queryset.filter(members__id__in=user_ids)

        return {
            "meeting_sessions": meeting_sections_queryset.values("pk").distinct().count(),
        }

    def _collect_unfinished_projects_kpi_values(self, request):
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        user_ids = [
            value for value in (request.query_params.get("user") or "").split(",") if value
        ]

        queryset = get_workgroup_queryset(request).filter(
            is_project=True,
            is_finished=False,
        )
        if root_organization_id:
            root_annotations = WorkgroupModel.get_report_annotations(
                request,
                requested_computed=["root_organization"],
            )
            queryset = queryset.annotate(**root_annotations).filter(
                root_organization=root_organization_id
            )
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if user_ids:
            queryset = queryset.filter(members__id__in=user_ids)

        return {
            "unfinished_projects": queryset.values("pk").distinct().count(),
        }

    def _collect_contracts_kpi_values(self, request):
        queryset = CustomerContractModel.get_queryset(request)
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        project_id = request.query_params.get("project")

        if root_organization_id:
            root_annotations = CustomerContractModel.get_report_annotations(
                request,
                requested_computed=["root_organization"],
            )
            queryset = queryset.annotate(**root_annotations).filter(root_organization=root_organization_id)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if project_id:
            queryset = queryset.filter(projects__pk=project_id)

        return {
            "contracts": queryset.values("pk").distinct().count(),
        }

    def _collect_request_approvals_kpi_values(self, request, start_date, end_date):
        queryset = WorkflowRequestModel.get_queryset(request)
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")
        project_id = request.query_params.get("project")
        user_ids = [
            value for value in (request.query_params.get("user") or "").split(",") if value
        ]

        if root_organization_id:
            root_annotations = WorkflowRequestModel.get_report_annotations(
                request,
                requested_computed=["root_organization"],
            )
            queryset = queryset.annotate(**root_annotations).filter(root_organization=root_organization_id)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if user_ids:
            queryset = queryset.filter(author_id__in=user_ids)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return {
            "request_approvals": queryset.values("pk").distinct().count(),
        }

    def _collect_contractor_profiles_kpi_values(self, request, start_date, end_date):
        queryset = ContractorProfileModel.get_queryset(request)
        root_organization_id = request.query_params.get("root_organization")
        organization_id = request.query_params.get("organization")

        if root_organization_id:
            root_annotations = ContractorProfileModel.get_report_annotations(
                request,
                requested_computed=["root_contractor"],
            )
            queryset = queryset.annotate(**root_annotations).filter(
                root_contractor=root_organization_id
            )
        if organization_id:
            queryset = queryset.filter(contractor_id=organization_id)

        if not start_date or not end_date:
            today = timezone.localdate()
            start_date = start_date or (today - datetime.timedelta(days=30))
            end_date = end_date or today
        queryset = queryset.filter(
            user__last_activity__date__gte=start_date,
            user__last_activity__date__lte=end_date,
        )

        return {
            "contractor_profiles": queryset.values("pk").distinct().count(),
        }

    @action(methods=["get"], detail=False, url_path="kpi")
    def kpi(self, request, *args, **kwargs):
        section = request.query_params.get("section") or "kpi"
        start_date = _to_date(request.query_params.get("start"))
        end_date = _to_date(request.query_params.get("end"))

        merged_config = self._merge_dashboard_configs(
            self._get_filtered_dashboard_configs(request, section=section)
        )
        if not merged_config.get("groups"):
            return Response({})

        widget_codes = set()
        for group in merged_config.get("groups", []):
            group_widgets = group.get("widgets", [])
            for widget in group_widgets:
                widget_code = widget.get("widget_code")
                if widget_code:
                    widget_codes.add(widget_code)

        kpi_values = {}
        if widget_codes.intersection(
            {"tasks_not_completed", "new_tasks", "completed_tasks", "overdue_tasks", "stalled_tasks"}
        ):
            kpi_values.update(self._collect_task_kpi_values(request, start_date, end_date))
        if widget_codes.intersection(
            {"not_completed_tickets", "new_tickets", "completed_tickets", "overdue_tickets"}
        ):
            kpi_values.update(self._collect_ticket_kpi_values(request, start_date, end_date))
        if "total_execution_time" in widget_codes:
            kpi_values.update(self._collect_total_execution_time_kpi_values(request, start_date, end_date))
        if "tasks_execution_time" in widget_codes:
            kpi_values.update(self._collect_tasks_execution_time_kpi_values(request, start_date, end_date))
        if "tickets_execution_time" in widget_codes:
            kpi_values.update(self._collect_tickets_execution_time_kpi_values(request, start_date, end_date))
        if "meeting_sessions" in widget_codes:
            kpi_values.update(self._collect_meeting_sessions_kpi_values(request, start_date, end_date))
        if "unfinished_projects" in widget_codes:
            kpi_values.update(self._collect_unfinished_projects_kpi_values(request))
        if "contracts" in widget_codes:
            kpi_values.update(self._collect_contracts_kpi_values(request))
        if "request_approvals" in widget_codes:
            kpi_values.update(self._collect_request_approvals_kpi_values(request, start_date, end_date))
        if "contractor_profiles" in widget_codes:
            kpi_values.update(self._collect_contractor_profiles_kpi_values(request, start_date, end_date))
        response_data = self._inject_kpi_values(merged_config, kpi_values)
        section_name = DashboardSectionModel.objects.filter(
            code=section, is_active=True,
        ).values_list("name", flat=True).first()
        if section_name:
            response_data["name"] = section_name
        return Response(response_data)
