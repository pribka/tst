from datetime import date
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_q.tasks import async_task

from common.views import BaseModelViewSet
from common.utils import get_datetime_param
from analytics.models import ActivitySummaryModel
from analytics.utils.analyze_data import generate_activity_summary

from .models import DaySummaryNoteModel, DaySummaryNoteCategoryModel
from . import serializers


def _parse_date_param(value):
    """Parse YYYY-MM-DD from query or body. Returns date or None."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return timezone.datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


class DaySummaryNoteCategoryListView(APIView):
    """Список категорий заметок за день (справочник)."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = DaySummaryNoteCategoryModel.objects.filter(is_active=True).order_by("sort")
        return Response(serializers.DaySummaryNoteCategorySerializer(queryset, many=True).data)


class DaySummaryNoteViewSet(BaseModelViewSet):
    """Заметка за день. model = DaySummaryNoteModel. list по ?date= или ?start=&end= (дата из ISO без учёта часового пояса). generate — action POST."""
    model = DaySummaryNoteModel

    def apply_user_filter(self, queryset):
        user_param = self.request.query_params.get("user")
        if user_param:
            profile_ids = [p.strip() for p in user_param.split(",") if p.strip()]
            if profile_ids:
                queryset = queryset.filter(author__pk__in=profile_ids)
        else:
            queryset = queryset.filter(author=self.request.user.profile)
        return queryset

    def apply_date_filter(self, queryset):
        start = get_datetime_param(self.request, "start")
        end = get_datetime_param(self.request, "end")
        if start and end:
            start_date = parse_date(start.split("T")[0])
            end_date = parse_date(end.split("T")[0])
            queryset = queryset.filter(date__gte=start_date, date__lte=end_date)
        else:
            queryset = queryset.filter(date=timezone.localdate())
        return queryset

    def get_queryset(self):
        qs = self.model.get_queryset(self.request)
        if self.action in ("list", "list_latest"):
            if self.action == "list":
                qs = self.apply_user_filter(qs)
            qs = self.apply_date_filter(qs)
            qs = qs.order_by("-date", "author",)
            qs = self.filter_queryset(qs)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="list_latest")
    def list_latest(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = qs.order_by("author_id", "-date", "-created_at").distinct("author_id", "date")

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        target_date = request.query_params.get("date")
        if not target_date:
            raise ValidationError("date обязателен (YYYY-MM-DD).")

        user = request.user.profile
        related_object_id = str(user.pk)
        scope = "user_day_summary"
        sources = "tasks,meetings,helpdesk"

        existing_pending = ActivitySummaryModel.objects.filter(
            related_object_id=related_object_id,
            user=user,
            start_date=target_date,
            end_date=target_date,
            scope=scope,
            status="pending",
            is_active=True,
        ).first()

        if existing_pending:
            return Response(
                {
                    "status": "pending",
                    "activity_summary_id": str(existing_pending.pk),
                    "date": target_date,
                },
                status=200,
            )

        activity_summary = ActivitySummaryModel.objects.create(
            related_object_id=related_object_id,
            user=user,
            start_date=target_date,
            end_date=target_date,
            scope=scope,
            sources=sources,
            status="pending",
            started_at=timezone.now(),
        )
        # Запуск в LLM будет осуществляться через task_klass.py
        # async_task(generate_activity_summary, str(activity_summary.pk))
        # generate_activity_summary(str(activity_summary.pk))

        return Response(
            {
                "status": "pending",
                "activity_summary_id": str(activity_summary.pk),
                "date": target_date,
            },
            status=202,
        )

    @action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request):
        """
        Показывает, есть ли у пользователя ожидающие анализа саммари (очередь generate).
        Принимает date (YYYY-MM-DD) или start/end (как в list).
        """
        user = request.user.profile
        related_object_id = str(user.pk)
        scope = "user_day_summary"

        target_date = request.query_params.get("date")
        if target_date:
            start_date = end_date = target_date
        else:
            start = get_datetime_param(request, "start")
            end = get_datetime_param(request, "end")
            if not (start and end):
                raise ValidationError("Укажите date или start/end.")
            start_date = parse_date(start.split("T")[0]) if start else None
            end_date = parse_date(end.split("T")[0]) if end else None
            if not (start_date and end_date):
                raise ValidationError("Некорректные start/end.")

        qs = ActivitySummaryModel.objects.filter(
            related_object_id=related_object_id,
            user=user,
            scope=scope,
            status="pending",
            is_active=True,
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).order_by("start_date")

        items = [
            {
                "date": obj.end_date.isoformat(),
                "start_date": obj.start_date.isoformat(),
                "end_date": obj.end_date.isoformat(),
                "activity_summary_id": str(obj.pk),
            }
            for obj in qs
        ]
        return Response(
            {
                "has_pending": len(items) > 0,
                "pending": items,
            }
        )

    @action(detail=False, methods=["get"], url_path="is_published")
    def is_published(self, request):
        """GET ?date=YYYY-MM-DD → is_published: True если все активные заметки за день опубликованы, иначе False."""
        target_date = request.query_params.get("date")
        if not target_date:
            raise ValidationError("date обязателен (YYYY-MM-DD).")
        profile = request.user.profile
        active_notes = DaySummaryNoteModel.objects.filter(
            author=profile, date=target_date, is_active=True
        )
        has_unpublished = active_notes.exclude(status_id="published").exists()
        return Response({"is_published": active_notes.exists() and not has_unpublished})

    @action(detail=False, methods=["put"], url_path="publish")
    def publish(self, request):
        target_date = _parse_date_param(
            request.data.get("date") if request.data else request.query_params.get("date")
        )
        if target_date is None:
            raise ValidationError("date обязателен (YYYY-MM-DD).")
        profile = request.user.profile
        DaySummaryNoteModel.objects.filter(
            author=profile, date=target_date, is_active=True
        ).update(status_id="published")
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"], url_path="unpublish")
    def unpublish(self, request):
        target_date = _parse_date_param(
            request.data.get("date") if request.data else request.query_params.get("date")
        )
        if target_date is None:
            raise ValidationError("date обязателен (YYYY-MM-DD).")
        profile = request.user.profile
        DaySummaryNoteModel.objects.filter(
            author=profile, date=target_date, is_active=True
        ).update(status_id="draft")
        return Response(status=status.HTTP_200_OK)

    @action(methods=("put",), detail=True, url_path="update_visors")
    def update_visors(self, request, *args, **kwargs):
        """Обновляет наблюдателей итога дня."""
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise PermissionDenied("Только автор может назначать наблюдателей итога дня")
        serializer = serializers.DaySummaryNoteVisorsUpdateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
