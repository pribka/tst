import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django_q.tasks import async_task
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app_info.models import AppInfo
from bpms.tasks.models import TaskStatusModel
from common.paginators import CustomPagination
from common.utils import get_filter_queryset, order_queryset_from_get_param

from . import models, notifications, permissions, serializers, utils


class TicketDetailView(generics.RetrieveAPIView):
    permission_classes = (
        IsAuthenticated,
        permissions.IsAuthorOrAdministrator1C
    )
    serializer_class = serializers.TicketDetailSerializer

    def get_queryset(self):
        return models.TicketModel.objects.filter(
            is_active=True
            ).select_related(
                'author',
                'author__user',
                'admin_status',
                'user_status',
                'connection_option',
                'ticket_type',
                'tarif',
            ).prefetch_related(
                Prefetch(
                    'config_1c',
                    queryset=models.Configuration1cModel.objects.filter(
                        is_active=True
                    )
                )
            )


class TicketTypeOptionsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.TicketTypeOptionSerializer

    def get_queryset(self):
        ticket_type = self.request.query_params.get(
            'ticket_type',
            'base_1c'
        )
        queryset = models.TicketTypeOptionModel.objects.filter(
            is_active=True,
            ticket_type__code=ticket_type
        )
        return queryset


class Config1CListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.Configuration1cSerializer
    queryset = models.Configuration1cModel.objects.filter(
        is_active=True
    ).order_by('sort')


class Tariff1CListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.Tariff1CSerializer
    queryset = models.Tariff1CModel.objects.filter(is_active=True)


class TicketListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.TicketListSerializer
    pagination_class = CustomPagination
    model = models.TicketModel

    def filter_queryset(self, queryset, request):
        user = request.user.profile
        ordering = request.query_params.get('ordering')
        if ordering and ordering.endswith('status'):
            prefix = '-' if ordering.startswith('-') else ''
            field_name = ('admin_status'
                          if user.check_profile_types({"administrator_1c"})
                          else 'user_status')
            qs = order_queryset_from_get_param(
                self.request,
                self.model,
                get_filter_queryset(
                    self.request,
                    self.model,
                    queryset
                )
            ).order_by(
                f'{prefix}{field_name}'
            )
        else:
            qs = order_queryset_from_get_param(
                self.request,
                self.model,
                get_filter_queryset(
                    self.request,
                    self.model,
                    queryset
                )
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset(), request)
        page = self.paginate_queryset(queryset)
        user = self.request.user.profile
        serializer = serializers.TicketListSerializer(
            page,
            many=True,
            context={
                'is_administrator_1c': user.check_profile_types(
                    {"administrator_1c"}
                )
            }
        )
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        user = self.request.user.profile
        ticket_type = self.request.query_params.get('ticket_type', 'base_1c')
        if user.check_profile_types({"administrator_1c"}):
            return models.TicketModel.objects.filter(
                is_active=True,
                ticket_type__code=ticket_type
            ).select_related(
                'author',
                'author__user',
                'admin_status',
                'user_status',
                'connection_option',
                'ticket_type',
                'tarif',
                'processed_by',
                'config_1c'
            ).order_by(
                '-created_at'
            )
        else:
            return models.TicketModel.objects.filter(
                is_active=True,
                author=user
            ).select_related(
                'author',
                'author__user',
                'admin_status',
                'user_status',
                'connection_option',
                'ticket_type',
                'tarif',
                'processed_by',
                'config_1c'
            ).order_by(
                '-created_at'
            )


class CreateTicketView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CreateTicketSerializer
    queryset = models.TicketModel.objects.filter(is_active=True)


class UpdateTicketView(generics.UpdateAPIView):
    permission_classes = (
        IsAuthenticated,
        permissions.UpdateTicketPermission,
    )
    serializer_class = serializers.UpdateTicketSerializer
    queryset = models.TicketModel.objects.filter(is_active=True)


class TicketFormInfoView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(
                is_active=True,
                code='tickets_form_info'
            ).metadata
        except AppInfo.DoesNotExist:

            data = {
                "drawerTitle": "Подать заявку",
                "config_1c": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Конфигурация",
                    "rules": [
                    ]
                },
                "user_count": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Количество пользователей",
                    "rules": [
                        {
                            "required": True,
                            "message": 'Обязательно для заполнения',
                            "trigger": 'blur'
                        },
                    ]
                },
                "phone": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Контактный телефон",
                    "rules": [
                        {
                            "required": True,
                            "message": 'Обязательно для заполнения',
                            "trigger": 'blur'
                        },
                        {
                            "max": 255,
                            "message": 'Максимум 255 символов',
                            "trigger": 'blur'
                        }
                    ]
                },
                "company": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Организация",
                    "rules": [
                        {
                            "max": 255,
                            "message": 'Максимум 255 символов',
                            "trigger": 'blur'
                        }
                    ]
                },
                "email": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Электронная почта",
                    "rules": [
                        {
                            "max": 255,
                            "message": 'Максимум 255 символов',
                            "trigger": 'blur'
                        },
                        {
                            "type": "email",
                            "message": "Необходимо ввести email",
                            "trigger": "blur"
                        }
                    ]
                },
                "activity_type": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Вид деятельности",
                    "rules": [
                        {
                            "required": True,
                            "message": 'Обязательно для заполнения',
                            "trigger": 'blur'
                        },
                        {
                            "max": 255,
                            "message": 'Максимум 255 символов',
                            "trigger": 'blur'
                        }
                    ]
                },
                "description": {
                    "label-col": {"span": 6},
                    "wrapper-col": {"span": 12},
                    "title": "Дополнительная информация",
                    "rules": [
                        {
                            "max": 255,
                            "message": 'Максимум 255 символов',
                            "trigger": 'blur'
                        }
                    ]
                },
            }
        return Response(data)


class SetTicketStatusView(APIView):
    permission_classes = (
        IsAuthenticated,
        permissions.IsAdministrator1C
    )

    def post(self, request, *args, **kwargs):
        data = request.data
        approved = data.get('approved')
        user = request.user.profile
        pk = kwargs.get('pk')

        if not isinstance(approved, bool):
            raise ValidationError('Неправильный статус')
        if not isinstance(pk, uuid.UUID):
            raise ValidationError('Неправильный id заявки')

        try:
            ticket = models.TicketModel.objects.get(
                pk=pk,
                is_active=True
            )
        except ObjectDoesNotExist:
            raise ValidationError('Не удалось найти заявку')

        # if ticket.is_closed:
        #     raise ValidationError('Заявка закрыта')

        try:
            ticket_is_approved = TaskStatusModel.objects.get(
                is_active=True,
                code='ticket_is_approved'
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                'Проверьте что статус ticket_is_approved существует'
            )

        try:
            ticket_is_done = TaskStatusModel.objects.get(
                is_active=True,
                code='ticket_is_done'
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                'Проверьте что статус ticket_is_done существует'
            )

        try:
            ticket_is_rejected = TaskStatusModel.objects.get(
                is_active=True,
                code='ticket_is_rejected'
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                'Проверьте что статус ticket_is_rejected существует'
            )

        if approved:
            ticket.admin_status = ticket_is_approved
            ticket.user_status = ticket_is_done
            async_task(
                notifications.notify_ticket_has_approved,
                ticket,
                request.user.profile,
                ticket.author
            )
            if ticket.email:
                async_task(
                    utils.send_ticket_approved_email,
                    ticket=ticket,
                    manager=user
                )

        else:
            ticket.is_rejected = True
            ticket.admin_status = ticket_is_rejected
            ticket.user_status = ticket_is_rejected
            async_task(
                notifications.notify_ticket_has_rejected,
                ticket,
                user,
                ticket.author
            )
            if ticket.email:
                async_task(
                    utils.send_ticket_rejected_email,
                    ticket=ticket,
                    manager=user
                )

        ticket.is_closed = True
        ticket.processed_by = user
        ticket.save()

        return Response(
            serializers.TicketDetailSerializer(
                ticket,
                context={'request': request}
            ).data
        )


class ActionsInfoView(generics.RetrieveAPIView):
    permission_classes = (
        IsAuthenticated,
        permissions.IsAuthorOrAdministrator1C
    )
    queryset = models.TicketModel.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user.profile
        author = ticket.author
        is_author = user == author
        is_administrator_1c = user.check_profile_types({"administrator_1c"})
        actions = dict()
        if is_administrator_1c:
            actions['set_status'] = {"availability": True}
            try:
                from bkz3.settings import ALLOW_ADMINISTRATOR_EDIT_TICKETS
                admin_permission = ALLOW_ADMINISTRATOR_EDIT_TICKETS
            except ImportError:
                admin_permission = False
            actions['edit'] = {"availability": admin_permission}
        elif is_author:
            allow_edit = not ticket.is_closed
            actions['edit'] = {"availability": allow_edit}
        data = {"actions": actions}
        return Response(data)
