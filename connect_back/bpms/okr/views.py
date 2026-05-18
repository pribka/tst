from enum import IntEnum

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.paginators import CustomPagination
from common.views import BaseModelViewSet
from bpms.tasks.models import TaskModel
from bpms.tasks.serializers import KeyResultTaskSerializer
from contractor_permissions.utils import (
    check_contractor_permission, contractors_where_user_has_permission)

from . import models, permissions, serializers
from .utils import (get_objectives_status_count, get_okr_report_file,
                    get_quarter_dates)


class Quarter(IntEnum):
    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4


class MissionModelViewSet(BaseModelViewSet):
    """Вьюсет миссии компании."""
    permission_classes = (IsAuthenticated, permissions.MissionModelPermission)
    model = models.MissionModel

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                "edit": {"availability": True},
            }
        return Response({"actions": actions})


class ObjectivesModelViewSet(BaseModelViewSet):
    """Вьюсет целей ОКР."""
    permission_classes = (IsAuthenticated, permissions.ObjectivesModelPermission)
    model = models.ObjectivesModel

    def list(self, request, *args, **kwargs):
        user_id = request.user.profile.pk
        create_okr_contractors = contractors_where_user_has_permission(user_id, 'create_okr', None)

        queryset = self.filter_queryset(self.get_queryset().prefetch_related(
            'related_retrospectives'
        ))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True, context={
            'request': request,
            'create_okr_contractors': create_okr_contractors,
            })
        return self.get_paginated_response(serializer.data)

    @action(methods=('post',), detail=True, url_path='set_quarter',
            permission_classes=(IsAuthenticated,))
    def set_quarter(self, request, *args, **kwargs):
        obj = self.get_object()

        try:
            quarter = Quarter(request.data.get('quarter', None))
        except (ValueError, TypeError):
            raise drf_exceptions.ValidationError(
                'quarter должен быть числом от 1 до 4'
            )
        else:
            date_start, date_end = get_quarter_dates(quarter.value)
            with transaction.atomic():
                obj.date_start = date_start
                obj.date_end = date_end
                obj.date_end_quarter = quarter.value
                obj.save(update_fields=(
                    'date_start',
                    'date_end',
                    'date_end_quarter'
                ))
                key_results = obj.key_results.filter(is_active=True)
                for kr in key_results:
                    if kr.date_start or kr.date_end:
                        kr.date_start = date_start
                        kr.date_end = date_end
                        kr.date_end_quarter = quarter.value
                        kr.save(update_fields=(
                            'date_start',
                            'date_end',
                            'date_end_quarter'
                        ))

        return Response(
            serializers.ObjectivesModelListSerializer(
                obj,
                context={
                    'request': request,
                }
            ).data
        )

    @action(methods=("get",), detail=False, url_path='objectives_count',
            permission_classes=(IsAuthenticated,))
    def get_objectives_count(self, request, *args, **kwargs):
        """Статистика по целям ОКР организации: количество целей в каждом статусе."""
        qs = self.model.get_queryset(request)
        qs = self.filter_queryset(qs)
        qs = qs.select_related(None)
        qs = get_objectives_status_count(qs)
        return Response(qs)

    @action(methods=('get',), detail=False, url_path='objectives_select_list')
    def get_оbjectives_select_list(self, request, *args, **kwargs):
        """Список целей для выпадающего списка выбора родительской цели."""
        return Response({'results': serializers.ObjectivesModelShortSerializer(
                self.model.get_select_queryset(request),
                many=True
            ).data}
        )

    @action(methods=('get',), detail=False, url_path='objective_statuses')
    def get_objective_statuses(self, request, *args, **kwargs):
        """Список статусов целей."""
        data = serializers.ObjectiveStatusSerializer(
            models.ObjectiveStatusModel.objects.filter(is_active=True).order_by('sort'),
            many=True
        ).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='notification_frequencies')
    def get_notification_frequencies(self, request, *args, **kwargs):
        """Список вариантов для частоты уведомления о необходимости обновить цели и ключевые результаты."""
        data = serializers.NotificationFrequencySerializer(
            models.NotificationFrequencyModel.objects.filter(is_active=True).order_by('sort'),
            many=True
        ).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='section_info',)
    def get_section_info(self, request, *args, **kwargs):
        """Доступные действия для всего раздела ОКР в зависимости от организации по умолчанию."""
        actions = dict()
        user = request.user.profile
        try:
            check_contractor_permission(user.pk, user.current_contractor.pk, 'create_okr', None)
            contractor_permission = True
        except drf_exceptions.PermissionDenied:
            contractor_permission = False
        if contractor_permission:
            actions['create_mission'] = {'availability': True}
            actions['create_objectives'] = {'availability': True}
        return Response({"actions": actions})

    @action(methods=('post',), detail=False, url_path='action_info',)
    def get_bulk_action_info(self, request, *args, **kwargs):
        """Доступные действия для списка id целей."""
        objectives_id = request.data
        if not isinstance(objectives_id, list):
            raise drf_exceptions.ValidationError()
        objectives = models.ObjectivesModel.get_queryset(request).filter(pk__in=objectives_id)
        result = dict()

        for each in objectives:
            actions = dict()
            if each.get_update_permission(request):
                actions = {
                    "edit": {"availability": True},
                    "delete": {"availability": True},
                    }
                if each.children.filter(is_active=True).exists():
                    del actions['delete']
            if each.get_update_key_results_permission(request):
                actions['update_key_results'] = {'availability': True}
            result[str(each.pk)] = actions
        return Response(result)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        """Доступные действия для деталки цели."""
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions['edit'] = {'availability': True}
            actions['delete'] = {'availability': True}
            if instance.children.filter(is_active=True).exists():
                del actions['delete']
        if instance.get_update_key_results_permission(request):
            actions['update_key_results'] = {'availability': True}
        return Response({"actions": actions})

    @action(methods=('get',), detail=False, url_path='report_file',)
    def get_report_file(self, request, *args, **kwargs):
        from tempfile import NamedTemporaryFile
        queryset = self.model.get_queryset(request)
        wb = get_okr_report_file(request, queryset)
        with NamedTemporaryFile() as tmp_file:
            wb.save(tmp_file.name)
            return FileResponse(
                open(tmp_file.name, 'rb',),
                filename='report.xlsx',
                as_attachment=True,
            )


class KeyResultsModelViewSet(BaseModelViewSet):
    """Вьюсет ключевых результатов."""
    permission_classes = (IsAuthenticated, permissions.KeyResultsModelPermission)
    model = models.KeyResultsModel

    def list(self, request, *args, **kwargs):
        """Список ключевых результатов, относящихся к цели. В каждом ключевом результате выводится список его инициатив.
        def list нужен для передачи контекста в сериализатор."""

        objective_id = request.query_params.get('objective')
        if not objective_id:
            raise drf_exceptions.ValidationError('Передайте id цели в get-параметре objective')
        try:
            objective = models.ObjectivesModel.objects.get(pk=objective_id)
        except models.ObjectivesModel.DoesNotExist:
            return drf_exceptions.ValidationError('Не найдена цель с таким id')

        update_permission = objective.get_update_key_results_permission(request)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True, context={
            'request': request,
            'update_permission': update_permission,
            })
        return self.get_paginated_response(serializer.data)

    @action(methods=('post',), detail=False, url_path='action_info')
    def get_bulk_action_info(self, request, *args, **kwargs):
        """Доступные действия для списка id ключевых результатов."""
        key_results_id = request.data
        if not isinstance(key_results_id, list):
            raise drf_exceptions.ValidationError()
        key_results = models.KeyResultsModel.get_queryset(request).filter(pk__in=key_results_id)
        result = dict()

        for each in key_results:
            actions = dict()
            if each.get_update_permission(request):
                actions = {
                    "edit": {"availability": True},
                    "delete": {"availability": True},
                    }
            if each.get_update_initiatives_permission(request):
                actions['update_initiatives'] = {'availability': True}
            result[str(each.pk)] = actions
        return Response(result)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        """Доступные действия для деталки ключевого результата."""
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                "delete": {"availability": True},
                "edit": {"availability": True},
            }
        if instance.get_update_initiatives_permission(request):
            actions['update_initiatives'] = {'availability': True}
        return Response({"actions": actions})

    @action(methods=('post',), detail=True, url_path='add_task')
    def add_task(self, request, *args, **kwargs):
        """
        Привязывает задачу к ключевому результату.
        """

        key_result = self.get_object()
        # if not key_result.get_update_initiatives_permission(request):
        #     raise drf_exceptions.ValidationError(
        #         'Недостаточно прав для изменения объекта'
        #     )

        task_id = request.data.get('task')

        if not task_id:
            raise drf_exceptions.ValidationError('ID задачи не передан')

        task = get_object_or_404(TaskModel, pk=task_id)

        obj, created = models.KeyResultTasks.objects.get_or_create(
            key_result=key_result,
            task=task
        )

        if created:
            data = KeyResultTaskSerializer(
                task,
                context={'request': request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            raise drf_exceptions.ValidationError(
                'Нельзя повторно добавить задачу'
            )

    @action(methods=('post',), detail=True, url_path='remove_task')
    def remove_task(self, request, *args, **kwargs):
        """
        Удаляет связь задачи и ключевого результата.
        """

        key_result = self.get_object()
        if not key_result.get_update_initiatives_permission(request):
            raise drf_exceptions.ValidationError(
                'Недостаточно прав для изменения объекта'
            )

        task_id = request.data.get('task')

        if not task_id:
            raise drf_exceptions.ValidationError('ID задачи не передан')

        deleted_count, _ = models.KeyResultTasks.objects.filter(
            key_result=key_result,
            task_id=task_id
        ).delete()

        if deleted_count:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class InitiativesModelViewSet(BaseModelViewSet):
    """Вьюсет инициатив."""
    permission_classes = (IsAuthenticated, permissions.InitiativesModelPermission)
    model = models.InitiativesModel

    @action(methods=('PUT',), detail=True, url_path='complete')
    def set_complete(self, request, *args, **kwargs):
        """Завершить инициативу"""
        instance = self.get_object()
        serializer = serializers.InitiativesModelCompleteSerializer(
            instance=instance,
            data=request.data,)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                "delete": {"availability": True},
                "edit": {"availability": True},
            }
        return Response({"actions": actions})


class KeyResultMetricsModelViewSet(BaseModelViewSet):
    """Вьюсет метрик ключевых результатов."""
    permission_classes = (IsAuthenticated, permissions.KeyResultMetricsModelPermission)
    model = models.KeyResultMetricsModel


class ValueEffortsModelView(APIView):
    permission_classes = (IsAuthenticated,)
    model = models.ValueEffortsModel

    def get(self, request, *args, **kwargs):
        serializer = self.model.get_serializer_class()
        queryset = self.model.get_queryset()
        return Response(serializer(queryset, many=True).data)
