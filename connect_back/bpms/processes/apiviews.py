from functools import partial
from django_q.tasks import async_task

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.paginators import CustomPagination
from common import utils as common_utils
from common.views import BaseModelViewSet, BaseCatalogViewSet
from common.catalogs.models import ContractorProfileModel

from bpms.comments.models import CommentModel

from users.utils import get_ancestor_departments_related_organizations

from . import permissions
from . import serializers
from . import models
from . import notifications
from . import paginators
from . import utils

from rest_framework.decorators import action


class WorkflowRequestViewSet(BaseModelViewSet):
    model = models.WorkflowRequestModel
    permissions = (IsAuthenticated, permissions.WorkflowRequestPermission)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        page_ids = [_.pk for _ in page]
        if page is not None:
            # Вычисляем заявки с непросмотренными комментариями для текущего пользователя
            profile_id = request.user.profile.pk
            unviewed_comments = list(CommentModel.objects.filter(
                related_object_id__in=page_ids,
                is_active=True
            ).exclude(
                object_viewer_relations__profile_id=profile_id
            ).values_list("related_object_id", flat=True).distinct())

            serializer = self.get_serializer(
                page,
                many=True,
                context={'request': request, 'view': self, 'unviewed_comments': unviewed_comments}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='form_info')
    def get_form_info(self, request, *args, **kwargs):
        request_type_code = request.query_params.get('request_type',)
        if not request_type_code:
            raise drf_exceptions.ValidationError('request_type is required.')
        try:
            request_type = models.WorkflowRequestTypeModel.objects.get(is_active=True, code=request_type_code)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('request_type not found')
        return Response(request_type.metadata)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        user = request.user.profile
        instance = self.get_object()
        status_code = instance.status_id
        author = instance.author
        completed = instance.completed
        if not completed:
            if author == user and status_code in ('draft', 'on_rework',):
                actions = {
                    'update': {'availability': True},
                    'delete': {'availability': True},
                    'start': {'availability': True},
                }
            if author == user and not (status_code in ('draft', 'completed', 'paid', 'rejected',) or completed):
                actions['reject'] = {'availability': True}
            current_request_routes = list(
                instance.request_routes.filter(
                    status_id='under_approval'
                ).exclude(
                    workflow_position_id='paymaster'
                )
            )
            if current_request_routes:
                for current_request_route in current_request_routes:
                    request_route_user_through = current_request_route.request_route_user_through.filter(
                        status_id='under_approval',
                        user=user
                    ).first()
                    if request_route_user_through:
                        actions['approve'] = {'availability': True}
                        actions['reject'] = {'availability': True}
                        actions['on_rework'] = {'availability': True}
            if instance.get_advance_report_write_permission(user):
                actions['create_advance_report'] = {'availability': True}
                actions['update_advance_report'] = {'availability': True}
                actions['delete_advance_report'] = {'availability': True}
            if instance.get_advance_report_approve_permission(user):
                actions['approve_advance_report'] = {'availability': True}
            contractor = instance.organization
            contractors = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
            contractor_profiles = ContractorProfileModel.objects.filter(contractor_id__in=list(contractors), user=user)
            if not contractor_profiles.exists():
                pass
            else:
                is_finance_service = models.WorkflowPositionUserModel.objects.filter(
                    contractor_profile_id__in=contractor_profiles,
                    workflow_position_id='finance_service',
                ).exists()
                if is_finance_service:
                    actions['money_under_report'] = {'availability': True}
                if instance.request_routes.filter(workflow_position_id='paymaster', status_id='under_approval',
                                                  ).exists() and models.WorkflowPositionUserModel.objects.filter(
                        contractor_profile_id__in=contractor_profiles,
                        workflow_position_id='paymaster',
                ).exists():
                    actions['give_money'] = {'availability': True}
            if instance.get_notify_fin_service_permission(user):
                actions['notify_fin_service'] = {'availability': True}
        return Response({'actions': actions})

    @action(methods=('post',), detail=True, url_path='start',)
    def start_workflow_request(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user.profile
        old_status_code = instance.status_id
        if old_status_code not in ('draft', 'on_rework',):
            raise drf_exceptions.ValidationError('Заявка уже запущена.')
        if not instance.author == user:
            raise drf_exceptions.ValidationError('У вас нет прав на запуск заявки.')
        if old_status_code == 'draft':
            next_route = instance.request_routes.all().order_by('sort').first()
        else:
            # Если статус На доработке:
            next_route = instance.request_routes.filter(status_id='on_rework').order_by('sort').first()

        if old_status_code == 'draft':
            instance.date_start = timezone.now()
        with transaction.atomic():
            # Смотрим, есть ли автор в след. этапе:
            request_route = None
            for each in instance.request_routes.filter(sort__gte=next_route.sort).order_by('sort'):
                next_route_users = each.request_route_user_through.all()
                if each.workflow_position_id == 'paymaster':
                    next_route_users.update(status_id='under_approval')
                    each.status_id = 'under_approval'
                    each.save()
                    request_route = each
                    break
                next_route_users.filter(user=user).update(status_id='approved')
                next_route_users.exclude(Q(user=user) | Q(status_id='approved')).update(status_id='under_approval')
                if next_route_users.exclude(status_id='approved').exists():
                    # если в этапе не только автор, статус этапа under_approval и выходим из цикла
                    each.status_id = 'under_approval'
                    each.save()
                    request_route = each
                    if each.not_require_approval:
                        pass
                    else:
                        break
                else:
                    # Если в этапе только автор - статус этапа approved и переходим к следующему
                    each.status_id = 'approved'
                    request_route = each
                    each.save()
            approved_route_through = request_route and not request_route.request_route_user_through.all().exclude(
                status_id='approved',
            ).exists()
            if approved_route_through:
                request_route.status_id = 'approved'
                request_route.save()
                approved_routes = not instance.request_routes.all().exclude(status_id='approved').exists()
                if approved_routes:
                    instance.status_id = 'approved'
                    instance.save()
                else:
                    next_routes = list(request_route.children.all().order_by('sort'))
                    if not next_routes and request_route.workflow_position_id == 'director':
                        notifications.notify_about_approve_lpr(str(instance.pk))
                    for next_route in next_routes:
                        next_position = next_route.workflow_position
                        next_status = next_position.status
                        if next_status:
                            instance.status = next_status
                            instance.save()
                            instance.refresh_from_db()
                        next_route.status_id = 'under_approval'
                        next_route.save()
                        transaction.on_commit(
                            partial(
                                notifications.notify_change_workflow_status,
                                str(instance.pk),
                                old_status_code,
                                str(instance.status_id),
                                str(user.pk)
                            )
                        )
                        next_route.request_route_user_through.all().update(status_id='under_approval')

            else:
                instance.status = request_route.workflow_position.status
                instance.save()
                instance.refresh_from_db()
                transaction.on_commit(
                    partial(
                        notifications.notify_change_workflow_status,
                        str(instance.pk),
                        old_status_code,
                        instance.status_id,
                        str(user.pk)

                    )
                )
            if not instance.number:
                counter = instance.get_counter_instance()
                instance.number = counter.number_formatted
                instance.counter = counter.number
                instance.save()
        async_task(utils.send_socketio_about_create_workflow_request, str(instance.pk))
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='approve')
    def approve_workflow_request(self, request, *args, **kwargs):
        instance = self.get_object()
        author = instance.author
        old_status_code = instance.status_id
        user = request.user.profile
        if instance.status_id == 'rejected':
            raise drf_exceptions.ValidationError('Вы не можете одобрить заявку: заявка отклонена.')
        if instance.status_id == 'draft':
            raise drf_exceptions.ValidationError('Вы не можете одобрить заявку: заявка в статусе "Черновик".')
        if instance.completed:
            raise drf_exceptions.ValidationError('Вы не можете одобрить заявку: заявка уже завершена.')
        request_routes = list(
            instance.request_routes.filter(
                status_id='under_approval'
            ).exclude(
                workflow_position_id='paymaster'
            )
        )
        if request_routes:
            request_route_user_through = models.RequestRouteUserThrough.objects.filter(
                status_id='under_approval',
                user=user,
                request_route__in=request_routes
            ).order_by('request_route__sort').first()
            if not request_route_user_through:
                raise drf_exceptions.ValidationError('Вы не можете согласовывать заявку')
        else:
            raise drf_exceptions.ValidationError('Заявку нельзя согласовать')
        request_route_user_through.status_id = 'approved'
        request_route = request_route_user_through.request_route
        with transaction.atomic():
            request_route_user_through.save()
            approved_route_through = not request_route.request_route_user_through.all().exclude(
                status_id='approved',
            ).exists()
            if approved_route_through:
                # Если все на этом этапе одобрили:
                request_route.status_id = 'approved'
                request_route.save()
                approved_routes = not instance.request_routes.all().exclude(status_id='approved').exists()
                if approved_routes:
                    # Если все этапы одобрены:
                    instance.status_id = 'approved'
                    instance.save()
                else:
                    # Если остались неодобренные этапы:
                    next_routes = list(request_route.children.all().order_by('sort'))
                    if not next_routes and request_route.workflow_position_id == 'director':
                        notifications.notify_about_approve_lpr(str(instance.pk))
                    for next_route in next_routes:
                        next_position = next_route.workflow_position
                        next_status = next_position.status
                        if next_status:
                            instance.status = next_status
                            instance.save()
                        next_route.status_id = 'under_approval'
                        next_route.save()
                        request_route_user_through = next_route.request_route_user_through.all()
                        if request_route_user_through.filter(user=author).exists():
                            # Если в следующем есть автор:
                            current_route = None
                            for each in instance.request_routes.filter(sort__gte=next_route.sort).order_by('sort'):
                                next_route_users = each.request_route_user_through.all()
                                if each.workflow_position_id == 'paymaster':
                                    next_route_users.update(status_id='under_approval')
                                    each.status_id = 'under_approval'
                                    each.save()
                                    current_route = each
                                    break
                                next_route_users.filter(user=author).update(status_id='approved')
                                next_route_users.exclude(Q(user=author) | Q(status_id='approved')).update(
                                    status_id='under_approval')
                                if next_route_users.exclude(status_id='approved').exists():
                                    # если в этапе не только автор, статус этапа under_approval и выходим из цикла
                                    each.status_id = 'under_approval'
                                    each.save()
                                    current_route = each
                                    if each.not_require_approval:
                                        pass
                                    else:
                                        break
                                else:
                                    # Если в этапе только автор - статус этапа approved и переходим к следующему
                                    each.status_id = 'approved'
                                    current_route = each
                                    each.save()
                            current_approved_route_through = current_route and not current_route.request_route_user_through.all().exclude(
                                status_id='approved',
                            ).exists()
                            if current_approved_route_through:
                                current_route.status_id = 'approved'
                                current_route.save()
                                current_approved_routes = not instance.request_routes.all().exclude(
                                    status_id='approved').exists()
                                if current_approved_routes:
                                    instance.status_id = 'approved'
                                    instance.save()
                                else:
                                    current_next_routes = list(current_route.children.all().order_by('sort'))
                                    if not current_next_routes and current_route.workflow_position_id == 'director':
                                        notifications.notify_about_approve_lpr(str(instance.pk))
                                    for current_next_route in current_next_routes:
                                        current_next_position = current_next_route.workflow_position
                                        current_next_status = current_next_position.status
                                        if current_next_status:
                                            instance.status = current_next_status
                                            instance.save()
                                            instance.refresh_from_db()
                                        current_next_route.status_id = 'under_approval'
                                        current_next_route.save()
                                        transaction.on_commit(
                                            partial(
                                                notifications.notify_change_workflow_status,
                                                str(instance.pk),
                                                old_status_code,
                                                str(instance.status_id),
                                                str(author.pk)
                                            )
                                        )
                                        current_next_route.request_route_user_through.all().update(
                                            status_id='under_approval'
                                        )

                            else:
                                instance.status = current_route.workflow_position.status
                                instance.save()
                                instance.refresh_from_db()
                                transaction.on_commit(
                                    partial(
                                        notifications.notify_change_workflow_status,
                                        str(instance.pk),
                                        old_status_code,
                                        instance.status_id,
                                        str(author.pk)
                                    )
                                )
                        else:
                            next_route.request_route_user_through.all().update(status_id='under_approval')
                            instance.refresh_from_db()
                            notifications.notify_change_workflow_status(
                                str(instance.pk),
                                old_status_code,
                                str(instance.status_id),
                                str(user.pk)
                            )
        utils.send_socketio_about_update_workflow_request(instance)
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='on_rework')
    def on_rework_workflow_request(self, request, *args, **kwargs):
        instance = self.get_object()
        old_status_code = instance.status_id
        if instance.status_id == 'rejected':
            raise drf_exceptions.ValidationError('Заявка отменена.')
        if instance.status_id == 'draft':
            raise drf_exceptions.ValidationError(
                'Вы не можете отправить на доработку заявку: заявка в статусе "Черновик".'
            )
        if instance.status_id == 'on_rework':
            raise drf_exceptions.ValidationError(
                'Заявка уже на доработке'
            )
        if instance.completed:
            raise drf_exceptions.ValidationError('Вы не можете отправить на доработку заявку: заявка завершена.')
        user = request.user.profile
        request_routes = list(
            instance.request_routes.filter(
                status_id='under_approval'
            ).exclude(
                workflow_position_id='paymaster'
            )
        )
        if request_routes:
            request_route_user_through = models.RequestRouteUserThrough.objects.filter(
                status_id='under_approval',
                user=user,
                request_route__in=request_routes
            ).order_by('request_route__sort').first()

            if not request_route_user_through:
                raise drf_exceptions.ValidationError('Вы не можете отправлять на доработку заявку')
        else:
            raise drf_exceptions.ValidationError('Заявку нельзя отправить на доработку')

        request_route_user_through.status_id = 'on_rework'
        request_route = request_route_user_through.request_route
        request_route.status_id = 'on_rework'
        instance.status_id = 'on_rework'

        with transaction.atomic():
            request_route_user_through.save()
            request_route.save()
            instance.save()
        notifications.notify_change_workflow_status(str(instance.pk), old_status_code, 'rejected', str(user.pk))
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='reject')
    def reject_workflow_request(self, request, *args, **kwargs):
        instance = self.get_object()
        old_status_code = instance.status_id
        if instance.status_id == 'rejected':
            raise drf_exceptions.ValidationError('Заявка уже отменена.')
        if instance.status_id == 'draft':
            raise drf_exceptions.ValidationError('Вы не можете отменить заявку: заявка в статусе "Черновик".')
        if instance.status_id == 'paid':
            raise drf_exceptions.ValidationError('Вы не можете отменить заявку: заявка оплачена')
        if instance.completed:
            raise drf_exceptions.ValidationError('Вы не можете отменить заявку: заявка завершена.')

        user = request.user.profile
        if user == instance.author:
            instance.status_id = 'rejected'
            instance.rejection_reason = str(request.data.get('rejection_reason', ''))
            instance.save()
        else:
            request_routes = list(
                instance.request_routes.filter(
                    status_id='under_approval'
                ).exclude(
                    workflow_position_id='paymaster'
                )
            )
            if request_routes:
                request_route_user_through = models.RequestRouteUserThrough.objects.filter(
                    status_id='under_approval',
                    user=user,
                    request_route__in=request_routes
                ).order_by('request_route__sort').first()

                if not request_route_user_through:
                    raise drf_exceptions.ValidationError('Вы не можете согласовывать заявку')
            else:
                raise drf_exceptions.ValidationError('Заявку нельзя согласовать')
            request_route_user_through.status_id = 'rejected'
            request_route = request_route_user_through.request_route
            request_route.status_id = 'rejected'
            instance.status_id = 'rejected'
            instance.rejection_reason = str(request.data.get('rejection_reason', ''))
            with transaction.atomic():
                request_route_user_through.save()
                request_route.save()
                instance.save()
        notifications.notify_change_workflow_status(str(instance.pk), old_status_code, 'rejected', str(user.pk))
        return Response('ok')

    @action(methods=('get',), detail=True, url_path='advance_report/list')
    def get_advance_report_list(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = models.AdvanceReportModel.objects.filter(owner=instance).order_by('-created_at')
        if not instance.money_under_report:
            qs = qs.none()
        amount_sum = qs.aggregate(amount_sum=Sum('amount'))['amount_sum']
        paginator = paginators.AdvanceReportPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.AdvanceReportModelListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        )

        data = {'amount_sum': amount_sum, 'results': serializer.data}
        return paginator.get_paginated_response(data)

    @action(methods=('post',), detail=True, url_path='advance_report/create')
    def create_advance_report(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.completed:
            raise drf_exceptions.ValidationError('Заявка завершена')
        user = request.user.profile
        if not instance.get_advance_report_write_permission(user):
            raise drf_exceptions.ValidationError('Вы не можете создавать авансовый отчет')
        data = request.data
        data['owner'] = instance.pk
        serializer = serializers.AdvanceReportModelCreateSerializer(
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        advance_report = serializer.save()
        if not instance.notify_fin_service:
            instance.notify_fin_service = True
            instance.save()
        return_data = serializers.AdvanceReportModelListSerializer(
            advance_report,
            context={'request': request, 'view': self}
        ).data
        return Response(return_data)

    @action(methods=('put',), detail=False, url_path='advance_report/(?P<pk>[^/.]+)/update')
    def update_advance_report(self, request, *args, **kwargs):
        advance_report_id = kwargs.get('pk')
        try:
            advance_report = models.AdvanceReportModel.objects.get(pk=advance_report_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('Запись не найдена')
        user = request.user.profile
        workflow_request = advance_report.owner
        if not workflow_request.get_advance_report_write_permission(user):
            raise drf_exceptions.ValidationError('Вы не можете изменять авансовые отчеты')
        data = request.data
        serializer = serializers.AdvanceReportModelUpdateSerializer(
            advance_report,
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        advance_report = serializer.save()
        if not workflow_request.notify_fin_service:
            workflow_request.notify_fin_service = True
            workflow_request.save()
        return_data = serializers.AdvanceReportModelListSerializer(
            advance_report,
            context={'request': request, 'view': self}
        ).data
        return Response(return_data)

    @action(methods=('post',), detail=False, url_path='advance_report/(?P<pk>[^/.]+)/delete')
    def delete_advance_report(self, request, *args, **kwargs):
        advance_report_id = kwargs.get('pk')
        try:
            advance_report = models.AdvanceReportModel.objects.get(pk=advance_report_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('Запись не найдена')
        workflow_request = advance_report.owner
        user = request.user.profile
        if not workflow_request.get_advance_report_write_permission(user):
            raise drf_exceptions.ValidationError('Вы не можете удалять авансовые отчеты')
        with transaction.atomic():
            advance_report.delete()
            workflow_request.recalculate_amounts()
        if workflow_request.advance_reports.all().exists() and not workflow_request.notify_fin_service:
            workflow_request.notify_fin_service = True
            workflow_request.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('post',), detail=True, url_path='money_under_report')
    def demand_report(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.completed:
            raise drf_exceptions.ValidationError('Заявка завершена')
        user = request.user.profile
        contractor = instance.organization
        contractors = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        contractor_profiles = ContractorProfileModel.objects.filter(contractor_id__in=list(contractors), user=user)
        if not contractor_profiles.exists():
            raise drf_exceptions.PermissionDenied('Вы не являетесь участником организации')
        is_finance_service = models.WorkflowPositionUserModel.objects.filter(
            contractor_profile_id__in=contractor_profiles.values_list('pk', flat=True),
            workflow_position_id='finance_service',
        ).exists()
        if not is_finance_service:
            raise drf_exceptions.PermissionDenied('Требовать авансовый отчет может только финслужба')
        serializer = serializers.DemandReportUpdateSerializer(
            instance=instance,
            data=request.data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.recalculate_amounts()
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='advance_report/approve')
    def approve_advance_report(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user.profile
        if not instance.get_advance_report_approve_permission(user):
            raise drf_exceptions.ValidationError('Вы не можете утверждить авансовый отчет')
        instance.advance_report_approved = True
        instance.notify_fin_service = False
        instance.save()
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='advance_report/notify_fin_service')
    def notify_fin_service(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user.profile
        if not instance.get_notify_fin_service_permission(user):
            raise drf_exceptions.ValidationError('Вы не можете оповещать финансовую службу')
        instance.notify_fin_service = False
        instance.save()
        notifications.notify_finance_service_approve_ar(str(instance.pk))
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='give_money')
    def give_money(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.completed:
            raise drf_exceptions.ValidationError('Заявка завершена')
        paymaster_route = instance.request_routes.filter(
            status_id='under_approval', workflow_position_id='paymaster'
        ).first()
        if not paymaster_route:
            raise drf_exceptions.PermissionDenied('Заявка не на этапе выдачи денежных средств.')
        user = request.user.profile
        contractor = instance.organization
        contractors = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        contractor_profiles = ContractorProfileModel.objects.filter(contractor_id__in=list(contractors), user=user)
        if not contractor_profiles.exists():
            raise drf_exceptions.PermissionDenied('Вы не являетесь участником организации')
        if not models.WorkflowPositionUserModel.objects.filter(
                contractor_profile__in=contractor_profiles.values_list('pk', flat=True),
                workflow_position_id='paymaster',
        ).exists():
            raise drf_exceptions.PermissionDenied('Выдавать деньги может только казначей')
        serializer = serializers.WorkflowRequestGiveMoneySerializer(
            instance=instance,
            data=request.data,
            context={'request': request, 'view': self},
        )
        serializer.is_valid(raise_exception=True)
        old_status_code = instance.status_id
        with transaction.atomic():
            instance = serializer.save()
            instance.status_id = 'paid'
            instance.save()
            instance.recalculate_amounts()
            paymaster_route.status_id = 'approved'
            paymaster_route.save()
            paymaster_route.request_route_user_through.all().update(status_id='approved')
        notifications.notify_change_workflow_status(str(instance.pk), old_status_code, 'paid', str(user.pk))
        utils.send_socketio_about_update_workflow_request(instance)
        return Response('ok')

    @action(methods=('get',), detail=True, url_path='stage_info')
    def get_stage_info(self, request, *args, **kwargs):
        instance = self.get_object()
        request = request
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        stages = []
        number = 1
        instance_status = instance.status
        status_serializer_class = serializers.WorkflowRequestRouteStatusListSerializer
        approved_status = models.WorkflowRequestRouteStatusModel.objects.get(code='approved')
        awaits_status = models.WorkflowRequestRouteStatusModel.objects.get(code='awaits')
        under_approval_status = models.WorkflowRequestRouteStatusModel.objects.get(code='under_approval')
        if instance_status.code == 'draft':
            under_approval_status = models.WorkflowRequestRouteStatusModel.objects.get(code='under_approval')
            stages.append(
                {
                    'number': number,
                    'title': _('Создано'),
                    'status': status_serializer_class(under_approval_status).data,
                }
            )
        else:
            stages.append(
                {
                    'number': number,
                    'title': _('Создано'),
                    'status': status_serializer_class(approved_status).data,
                }
            )
        routes = instance.request_routes.all().order_by('sort')
        for route in routes:
            if route.not_require_approval:
                continue
            number += 1
            stages.append(
                {
                    'number': number,
                    'title': route.workflow_position.name,
                    'status': status_serializer_class(route.status).data,
                }
            )

        number += 1
        # if instance.request_type.completion_status_id == 'paid':
        #     if instance.status_id in ('paid', 'closed',):
        #         stages.append(
        #             {
        #                 'number': number,
        #                 'title': _('Казначей'),
        #                 'status': status_serializer_class(approved_status).data,
        #             }
        #         )
        #     elif instance.status_id == 'approved':
        #         stages.append(
        #             {
        #                 'number': number,
        #                 'title': _('Казначей'),
        #                 'status': status_serializer_class(under_approval_status).data
        #             }
        #         )
        #     else:
        #         stages.append(
        #             {
        #                 'number': number,
        #                 'title': _('Казначей'),
        #                 'status': status_serializer_class(awaits_status).data
        #             }
        #         )
        # number += 1
        if instance.money_under_report:
            if instance.advance_report_approved:
                stages.append(
                    {
                        'number': number,
                        'title': _('Отчет'),
                        'status': status_serializer_class(approved_status).data
                    }
                )
            elif instance_status.code == 'paid':
                stages.append(
                    {
                        'number': number,
                        'title': _('Отчет'),
                        'status': status_serializer_class(under_approval_status).data
                    }
                )
            else:
                stages.append(
                    {
                        'number': number,
                        'title': _('Отчет'),
                        'status': status_serializer_class(awaits_status).data
                    }
                )
        number += 1
        if instance.completed:
            stages.append(
                {
                    'number': number,
                    'title': _('Закрыта'),
                    'status': status_serializer_class(approved_status).data
                }
            )
        elif instance.status_id == 'rejected':
            rejected_status = models.WorkflowRequestRouteStatusModel.objects.get(code='rejected')
            stages.append(
                {
                    'number': number,
                    'title': _('Закрыта'),
                    'status': status_serializer_class(rejected_status).data
                }
            )
        else:
            stages.append(
                {
                    'number': number,
                    'title': _('Закрыта'),
                    'status': status_serializer_class(awaits_status).data
                }
            )
        return Response(stages)


class RequestTypeViewSet(BaseCatalogViewSet):
    model = models.WorkflowRequestTypeModel
    permissions = (IsAuthenticated, permissions.RequestTypePermission)



class RouteTemplateView(APIView):
    def get(self, request, *args, **kwargs):
        request_type_code = request.query_params.get('request_type')
        contractor_id = request.query_params.get('contractor')
        contractors = get_ancestor_departments_related_organizations((contractor_id,), include_self=True,)
        if not request_type_code:
            raise drf_exceptions.ValidationError('request_type is required')
        try:
            qs = models.WorkflowRequestRouteTemplateModel.objects.filter(request_type_id=request_type_code).order_by(
                'sort'
            )
        except ValidationError:
            raise drf_exceptions.ValidationError('Invalid request_type')
        serializer = serializers.WorkflowRequestRouteTemplateListSerializer(
            qs,
            many=True,
            context={'request': request, 'view': self, 'contractors': list(contractors)}
        )

        return Response(serializer.data)
