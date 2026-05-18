import datetime
import json
import uuid
import telebot
from django_q.tasks import async_task

from django.forms import inlineformset_factory
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.db import transaction, IntegrityError
from django.db.models import (
    Count,
    Q,
    Avg,
    Prefetch,
    Subquery,
    OuterRef,
    Exists,
    Sum,
    Case,
    When,
    Value,
    BooleanField,
    CharField,
    IntegerField,
)
from django.db.models.functions import Concat, Coalesce
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, FileResponse
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder


from rest_framework import status, exceptions as drf_exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework import generics

from haystack.query import RelatedSearchQuerySet

from bkz3.settings import BACKEND_URL, FRONTEND_URL, SOCKETIO_SYSTEM_CHANNEL, TG_MINI_APP_URL

from users.utils import get_invite_url, get_tree_departments_related_organizations

from customer_contracts.models import CustomerContractModel

from common.views import BaseModelViewSet, BaseCatalogViewSet
from common.paginators import CustomPagination
from common.auth_classes import CsrfExemptSessionAuthentication
from common.catalogs.models import ContractorModel, ContractorProfileModel, ExternalCustomerModel

from common.utils import get_filter_queryset, order_queryset_from_get_param, get_search_result, get_datetime_param
from common.redis import socketio_redis

from contractor_permissions.utils import contractors_where_user_has_permission, contractors_where_im_director
from contractor_permissions.utils import check_contractor_permission

from tags.models import TagModel

from users.models import ProfileModel
from users.serializers import CachedAppUserSerializer
from users.utils import get_ancestor_departments_related_organizations

from . import serializers, models, permissions, utils, paginators, notifications, forms
from .utils_my_day import build_my_day_ticket_analytics, get_my_day_tickets_queryset
from bpms.meetings.apiviews import MeetingConnectMixin


class CustomerCardModelViewSet(BaseModelViewSet):
    permission_classes = (IsAuthenticated, permissions.CustomerCartModelPermission)
    model = models.CustomerCardModel

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset().exclude(unknown=True))
        local_date = timezone.localdate()
        qs = qs.prefetch_related(
            Prefetch( #
                'customer_support_specialists',
                queryset=models.CustomerSupportSpecialistModel.objects.filter(
                    Q(start_date__lte=local_date, end_date__gte=local_date, ) |
                    Q(start_date__isnull=True, end_date__gte=local_date) |
                    Q(start_date__lte=local_date, end_date__isnull=True) |
                    Q(start_date__isnull=True, end_date__isnull=True)
                ).exclude(
                    vacation_dates__start_date__lte=local_date,
                    vacation_dates__end_date__gte=local_date,
                ).order_by(
                    'user__user__last_name',
                    'user__user__first_name',
                    'user__user__middle_name',
                ),
                to_attr='pref_actual_specialists'
            ),
            'object_tag_through__tag',
            'admins',
        )
        qs = qs.select_related('main_contact_person__post_inst')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.CustomerCardModelListSerializer(
            page,
            many=True,
            context={"request": request, "view": self}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                "edit": {"availability": True},
                "create_contact_person": {"availability": True},
                "edit_contact_person": {"availability": True},
                "delete_contact_person": {"availability": True},
            }
        if instance.get_delete_permission(request):
            actions['delete'] = {'availability': True}
        if instance.get_specialist_update_permission(request):
            actions["edit_specialist"] = {"availability": True}
        if instance.get_note_permission(request):
            actions['edit_notes'] = {"availability": True}
            actions['create_notes'] = {"availability": True}
            actions['delete_notes'] = {"availability": True}
        return Response({'actions': actions})

    @action(methods=('get',), detail=True, url_path='customer_card_detail')
    def customer_card_detail(self, request, *args, **kwargs):
        instance = models.CustomerCardModel.objects.get(pk=kwargs['pk'])
        serializer = serializers.CustomerCardModelListSerializer(
            instance,
            context={"request": request, "view": self}
        )
        return Response(serializer.data)

    @action(methods=('get',), detail=True, url_path='summary')
    def get_summary(self, request, *args, **kwargs):
        """Сводка по карточке клиента."""
        instance = self.get_object()
        tickets_qs = models.HelpDeskTicketModel.objects.filter(
            is_active=True,
            ticket_type_id='issue',
            customer_card=instance,
            contact_person__customer_card=instance,
        )
        complete_statuses = utils.get_completed_statuses_id()
        data = {
            'total': tickets_qs.count(),
            'active': tickets_qs.exclude(status_id__in=complete_statuses).count(),
            'completed': tickets_qs.filter(status_id__in=complete_statuses).count(),
        }
        return Response(data)

    @action(methods=('post',), detail=True, url_path='status')
    def update_status(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        serializer = serializers.CustomerCardStatusUpdateSerializer(
            instance=instance,
            data=request.data,
            context={'request': request, 'view': self},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('ok')

    @action(methods=('get',), detail=True, url_path='specialists')
    def get_specialists(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = models.CustomerSupportSpecialistModel.objects.filter(customer_card=instance)
        work_logs_sub = models.HelpDeskWorkLogModel.objects.filter(
            user=OuterRef('user'),
            ticket__customer_card=instance,
            is_active=True
        ).values_list('pk', flat=True)
        qs = qs.annotate(
            duration_fact=Sum(
                'user__work_logs__duration',
                filter=Q(user__work_logs__in=Subquery(work_logs_sub))
            ),
        )

        prev_exists_qs = models.CustomerSupportSpecialistModel.objects.filter(
            customer_card=instance,
            is_active=True,
            is_reserve=OuterRef('is_reserve'),
            call_priority__lt=OuterRef('call_priority'),
        )
        next_exists_qs = models.CustomerSupportSpecialistModel.objects.filter(
            customer_card=instance,
            is_active=True,
            is_reserve=OuterRef('is_reserve'),
            call_priority__gt=OuterRef('call_priority'),
        )
        qs = qs.annotate(
            can_move_up=Exists(prev_exists_qs),
            can_move_down=Exists(next_exists_qs),
        )
        qs = order_queryset_from_get_param(
            request,
            models.CustomerSupportSpecialistModel,
            get_filter_queryset(request, models.CustomerSupportSpecialistModel, qs)
        )
        if not qs.ordered:
            qs = qs.order_by(
                'call_priority',
            )
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = serializers.CustomerSpecialistListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        ).data
        response = paginator.get_paginated_response(s_data)
        return response

    @action(methods=('get',), detail=True, url_path='specialists/actual')
    def get_actual_specialists(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.actual_specialists

        text = request.query_params.get('text')
        if text:
            user_ids = qs.values_list('user_id', flat=True)
            search_queryset = RelatedSearchQuerySet().filter(
                content=text,
                profile_id__in=user_ids,
            ).models(ProfileModel).load_all()
            found_profile_ids = search_queryset.values_list('profile_id', flat=True)
            qs = qs.filter(user_id__in=found_profile_ids)

        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = serializers.CustomerSpecialistListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        ).data
        response = paginator.get_paginated_response(s_data)
        return response

    @action(methods=('post',), detail=True, url_path='specialists/add')
    def add_specialist(self, request, *args, **kwargs):
        datas = request.data
        return_data = list()
        with transaction.atomic():
            for data in datas:
                data['customer_card'] = kwargs.get('pk')
                serializer = serializers.CustomerSpecialistCreateSerializer(
                    data=data,
                    context={'request': request, 'view': self}
                )
                serializer.is_valid(raise_exception=True)
                customer_specialist = serializer.save()
                return_data.append(serializers.CustomerSpecialistListSerializer(
                    customer_specialist,
                    context={'request': request, 'view': self}
                ).data)
        return Response(return_data)

    @action(methods=('post',), detail=True, url_path='specialists/remove')
    def remove_specialist(self, request, *args, **kwargs):
        customer_specialists_id = request.data.get('specialists')
        instance = self.get_object()
        if not instance.get_specialist_update_permission(request):
            raise drf_exceptions.ValidationError('У вас нет прав удалять специалистов этой карточки клиентов')
        if customer_specialists_id:
            with transaction.atomic():
                for specialist_id in customer_specialists_id:
                    try:
                        customer_specialist = models.CustomerSupportSpecialistModel.objects.get(
                            customer_card=instance,
                            pk=specialist_id,
                        )
                    except (ValidationError, ObjectDoesNotExist):
                        raise drf_exceptions.ValidationError(f'customer_specialist {specialist_id} not found')
                    customer_specialist.delete()
        return Response('ok')

    @action(methods=('put',), detail=True, url_path='specialists/up')
    def specialist_up(self, request, *args, **kwargs):
        """Поднимает специалиста на 1 позицию в рамках своей группы (main/reserve)."""
        instance = self.get_object()
        if not instance.get_specialist_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение специалистов этой карточки клиента')

        specialist_id = request.data.get('id')
        if not specialist_id:
            raise drf_exceptions.ValidationError({'id': ['This field is required.']})

        with transaction.atomic():
            try:
                specialist = models.CustomerSupportSpecialistModel.objects.select_for_update().get(
                    customer_card=instance,
                    pk=specialist_id,
                    is_active=True,
                )
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.ValidationError('Запись не найдена')

            previous_specialist = models.CustomerSupportSpecialistModel.objects.select_for_update().filter(
                customer_card=instance,
                is_active=True,
                is_reserve=specialist.is_reserve,
                call_priority__lt=specialist.call_priority,
            ).order_by('-call_priority').first()

            if not previous_specialist:
                return Response(
                    {'detail': 'Нельзя переместить выше: достигнута граница группы.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            specialist_priority = specialist.call_priority
            previous_priority = previous_specialist.call_priority
            models.CustomerSupportSpecialistModel.objects.filter(pk=specialist.pk).update(call_priority=previous_priority)
            models.CustomerSupportSpecialistModel.objects.filter(pk=previous_specialist.pk).update(call_priority=specialist_priority)

        return Response(status=status.HTTP_200_OK)

    @action(methods=('put',), detail=True, url_path='specialists/down')
    def specialist_down(self, request, *args, **kwargs):
        """Опускает специалиста на 1 позицию в рамках своей группы (main/reserve)."""
        instance = self.get_object()
        if not instance.get_specialist_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение специалистов этой карточки клиента')

        specialist_id = request.data.get('id')
        if not specialist_id:
            raise drf_exceptions.ValidationError({'id': ['This field is required.']})

        with transaction.atomic():
            try:
                specialist = models.CustomerSupportSpecialistModel.objects.select_for_update().get(
                    customer_card=instance,
                    pk=specialist_id,
                    is_active=True,
                )
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.ValidationError('Запись не найдена')

            next_specialist = models.CustomerSupportSpecialistModel.objects.select_for_update().filter(
                customer_card=instance,
                is_active=True,
                is_reserve=specialist.is_reserve,
                call_priority__gt=specialist.call_priority,
            ).order_by('call_priority').first()

            if not next_specialist:
                return Response(
                    {'detail': 'Нельзя переместить ниже: достигнута граница группы.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            specialist_priority = specialist.call_priority
            next_priority = next_specialist.call_priority
            models.CustomerSupportSpecialistModel.objects.filter(pk=specialist.pk).update(call_priority=next_priority)
            models.CustomerSupportSpecialistModel.objects.filter(pk=next_specialist.pk).update(call_priority=specialist_priority)

        return Response(status=status.HTTP_200_OK)

    @action(methods=('PUT',), detail=True, url_path='specialists/update')
    def update_specialist(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_specialist_update_permission(request):
            raise drf_exceptions.PermissionDenied('У Вас нет прав на изменение специалиста в этой организации')
        customer_specialist_id = request.data.get('id')
        try:
            customer_specialist = models.CustomerSupportSpecialistModel.objects.get(pk=customer_specialist_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Запись не найдена')
        if not customer_specialist.get_update_permission(request):
            raise drf_exceptions.ValidationError('Вы не можете изменять специалиста этой карточки клиента')
        serializer = serializers.CustomerSpecialistUpdateSerializer(
            instance=customer_specialist,
            data=request.data,
            context={
                'request': request,
                'view': self,
            }
        )
        serializer.is_valid(raise_exception=True)
        customer_specialist = serializer.save()
        data = serializers.CustomerSpecialistListSerializer(
            customer_specialist,
            context={'request': request, 'view': self}
        ).data
        return Response(data)

    def get_contact_person(self):
        instance = self.get_object()
        # if not instance.get_detail_permission(self.request):
        #     raise drf_exceptions.PermissionDenied('У вас нет прав на получение контактного лица')
        contact_person_id = self.request.data.get('contact_person')
        if not contact_person_id:
            raise drf_exceptions.ValidationError('contact_person is required')
        try:
            contact_person = models.ContactPersonModel.objects.get(
                customer_card=instance,
                pk=contact_person_id,
                is_active=True,
            )
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('contact_person not found')
        return contact_person

    @action(methods=('get', ), detail=True, url_path='contact_persons')
    def get_contact_persons(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав просмотра карточки клиента')
        qs = models.ContactPersonModel.objects.filter(customer_card=instance, is_active=True).select_related(
            'post_inst',
            'customer_card',
        ).order_by(
            'name',
        )
        main_contact = instance.main_contact_person
        if not main_contact:
            qs = qs.annotate(
                is_main=Value(False)
            )
        else:
            main_contact_id = str(main_contact.pk)
            qs = qs.annotate(
                is_main=Case(
                    When(pk=main_contact_id, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
        qs = order_queryset_from_get_param(
            request,
            models.ContactPersonModel,
            get_filter_queryset(request, models.ContactPersonModel, qs,)
        )
        search = request.query_params.get('search')
        if search:
            search_result = get_search_result(models.ContactPersonModel, search)
            search_result_ids = [item['id'] for item in search_result]
            qs = qs.filter(pk__in=search_result_ids)
        exclude_id = request.query_params.get('exclude')
        if exclude_id:
            try:
                qs = qs.exclude(pk=exclude_id)
            except ValidationError:
                pass
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        can_update_customer_card = instance.get_update_permission(request)
        serializer = serializers.ContactPersonModelListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self, 'can_update_customer_card': can_update_customer_card},
        )
        response = paginator.get_paginated_response(serializer.data)
        return response

    @action(methods=('get',), detail=False, url_path='contact_persons/invite')
    def get_invite_url(self, request, *args, **kwargs):
        contact_person_id = request.query_params.get('contact_person')
        data = {
            'url': '',
            'invite_token': ''
        }
        if not contact_person_id:
            return Response(data)
        try:
            contact_person = models.ContactPersonModel.objects.get(pk=contact_person_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response(data)
        customer_card = contact_person.customer_card
        if not customer_card.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на приглашение контактного лица')
        if not contact_person.user:
            token = contact_person.invite_token
            url = f"{get_invite_url(token)}&mode=invite_to_helpdesk"
            data = {
                'url': url,
                'invite_token': token
            }
        return Response(data)

    @action(methods=('post',), detail=False, url_path='contact_persons/email_invite')
    def send_email_invite(self, request, *args, **kwargs):
        contact_person_id = request.data.get('contact_person',)
        try:
            contact_person = models.ContactPersonModel.objects.get(pk=contact_person_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Контактное лицо не найдено')
        if not contact_person.customer_card.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на приглашение контактного лица')
        if contact_person.user:
            raise drf_exceptions.ValidationError('Пользователь уже привязан к контактному лицу')
        if not contact_person.email:
            raise drf_exceptions.ValidationError('Отсутствует адрес электронной почты')
        notifications.send_email_invite(contact_person)
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='contact_persons/add')
    def add_contact_person(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на добавление контактного лица')
        data = request.data
        data['customer_card'] = kwargs.get('pk')
        serializer = serializers.ContactPersonModelCreateSerializer(
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        contact_person = serializer.save()
        can_update_customer_card = instance.get_update_permission(request)
        resp_data = serializers.ContactPersonModelListSerializer(
            contact_person,
            context={'request': request, 'view': self, 'can_update_customer_card': can_update_customer_card}
        ).data
        return Response(resp_data)

    @action(methods=('put', ), detail=True, url_path='contact_persons/update')
    def update_contact_person(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение контактного лица')
        contact_person = self.get_contact_person()
        serializer = serializers.ContactPersonModelUpdateSerializer(
            instance=contact_person,
            data=request.data,
            context={'request': request, 'view': self, }
        )
        serializer.is_valid(raise_exception=True)
        contact_person = serializer.save()
        can_update_customer_card = instance.get_update_permission(request)
        resp_data = serializers.ContactPersonModelListSerializer(
            contact_person,
            context={'request': request, 'view': self, 'can_update_customer_card': can_update_customer_card}
        ).data
        return Response(resp_data)

    @action(methods=('post',), detail=True, url_path='contact_persons/remove')
    def remove_contact_person(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на удаление контактного лица')
        contact_person = self.get_contact_person()
        contact_person.is_active = False
        contact_person.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('get',), detail=False, url_path='unrelated',)
    def get_unrelated_counterparties(self, request, *args, **kwargs):
        org_admin_id = request.query_params.get('org_admin')
        if not org_admin_id:
            raise drf_exceptions.ValidationError('org_admin required')
        try:
            org_admin = ContractorModel.objects.get(is_active=True, pk=org_admin_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('org_admin not found')
        user = request.user.profile
        ancestors = get_ancestor_departments_related_organizations((org_admin_id,), include_self=True)
        admin_contractors = set(contractors_where_user_has_permission(user.pk, 'admin', None))
        if admin_contractors.isdisjoint(ancestors):
            raise drf_exceptions.PermissionDenied()
        qs = ExternalCustomerModel.objects.filter(
            customer_contracts__organization=org_admin,
            is_active=True,
        ).exclude(customer_cards__org_admin=org_admin)
        qs = qs.order_by('-created_at',)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.UnrelatedExternalCustomerSerializer(
            page,
            many=True,
            context={"request": request, "view": self}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('get',), detail=False, url_path='suggestions')
    def get_suggestion(self, request, *args, **kwargs):
        external_customer_id = request.query_params.get('external_customer')
        if not external_customer_id:
            raise drf_exceptions.ValidationError('external_customer required')
        try:
            external_customer_card = ExternalCustomerModel.objects.get(is_active=True, pk=external_customer_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('unrelated not found')
        org_admin = external_customer_card.org_admin
        user = request.user.profile
        ancestors = get_ancestor_departments_related_organizations((org_admin.pk,), include_self=True)
        admin_contractors = set(contractors_where_user_has_permission(user.pk, 'admin', None))
        if admin_contractors.isdisjoint(ancestors):
            raise drf_exceptions.PermissionDenied()
        ext_bin = external_customer_card.inn
        ext_name = external_customer_card.name
        qs = models.CustomerCardModel.objects.filter(
            is_active=True,
            org_admin=org_admin,
            external_customer__isnull=True,
        ).annotate(
            match_priority=Case(
                # Приоритет 1: Совпадение по БИН (самое точное)
                When(inn=ext_bin, then=Value(1)),

                # Приоритет 2: Полное совпадение имени (без учета регистра)
                When(name__iexact=ext_name, then=Value(2)),

                # Приоритет 3: Имя содержит название из внешней системы
                When(name__icontains=ext_name, then=Value(3)),

                # Приоритет 4: Все остальные
                default=Value(4),
                output_field=IntegerField(),
            )
        )
        qs = qs.order_by('match_priority', 'name')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.CustomerCardModelShortSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('post',), detail=False, url_path='external_customer/bind')
    def bind_external_customer(self, request, *args, **kwargs):
        data = request.data
        customer_card_id = data.get('customer_card')
        if not customer_card_id:
            raise drf_exceptions.ValidationError('customer_card required')
        external_customer_id = data.get('external_customer')
        if not external_customer_id:
            raise drf_exceptions.ValidationError('external_customer required')
        try:
            customer_card = models.CustomerCardModel.objects.get(
                pk=customer_card_id,
                is_active=True
            )
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('customer_card not found')
        if customer_card.external_customer:
            raise drf_exceptions.ValidationError('Контрагент уже связан.')
        org_admin = customer_card.org_admin
        user = request.user.profile
        ancestors = get_ancestor_departments_related_organizations((org_admin.pk,), include_self=True)
        admin_contractors = set(contractors_where_user_has_permission(user.pk, 'admin', None))
        if admin_contractors.isdisjoint(ancestors):
            raise drf_exceptions.PermissionDenied()
        try:
            external_customer = ExternalCustomerModel.objects.get(
                pk=external_customer_id,
                is_active=True
            )
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('external_customer not found')

        if external_customer.org_admin_id not in get_ancestor_departments_related_organizations(
                (customer_card.org_admin_id,),
                include_self=True
        ):
            raise drf_exceptions.ValidationError('Контрагенты из разных организаций')

        if not CustomerContractModel.objects.filter(
                external_customer=external_customer,
                organization=customer_card.org_admin,
                is_active=True
        ).exists():
            raise drf_exceptions.ValidationError('Контрагент не имеет связь с контрактами')
        customer_card.external_customer = external_customer
        with transaction.atomic():
            customer_card.save()
            if models.CustomerCardModel.objects.filter(
                    is_active=True,
                    org_admin=org_admin,
                    external_customer=external_customer,
            ).count() > 1:
                raise drf_exceptions.ValidationError('Контрагент уже связан с карточкой клиента')
        return Response('ok')


class HelpDeskConfigViewSet(ModelViewSet):
    queryset = ContractorModel.objects.filter(is_active=True)
    serializer_class = serializers.HelpDeskConfigModelSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение конфигурации')
        try:
            config = instance.help_desk_config
        except ObjectDoesNotExist:
            config = models.HelpDeskConfigModel.objects.create(contractor=instance)
        serializer = self.get_serializer(config, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на просмотр конфигурации')
        try:
            config = instance.help_desk_config
        except ObjectDoesNotExist:
            config = models.HelpDeskConfigModel.objects.create(contractor=instance)
        serializer = self.get_serializer(config, context={'request': request, 'view': self})
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=('post',), detail=True, url_path='telegram/set_webhook')
    def set_telegram_hook(self, request, *args, **kwargs):
        contractor = self.get_object()
        if not contractor.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на установку веб-хука')
        try:
            config = contractor.help_desk_config
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('config not found')
        telegram_token = config.telegram_token
        bot = telebot.TeleBot(telegram_token)
        bot.remove_webhook()
        config.telegram_webhook_token = utils.generate_telegram_webhook_token()
        config.save()
        host = request.data.get('host')
        if host:
            resp = bot.set_webhook(
                url=f'{host}/api/v1/help_desk/telegram/bot/{config.pk}/',
                secret_token=config.telegram_webhook_token,
            )
        else:
            resp = bot.set_webhook(
                url=f'{BACKEND_URL}/api/v1/help_desk/telegram/bot/{config.pk}/',
                secret_token=config.telegram_webhook_token,
            )
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='telegram/remove_webhook')
    def remove_telegram_hook(self, request, *args, **kwargs):
        contractor = self.get_object()
        if not contractor.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на удаление веб-хука')
        try:
            config = contractor.help_desk_config
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('config not found')
        telegram_token = config.telegram_token
        bot = telebot.TeleBot(telegram_token)
        bot.remove_webhook()
        return Response('ok')


class HelpdeskTelegramHandlerView(APIView):
    queryset = models.HelpDeskConfigModel.objects.filter(is_active=True)
    serializer_class = serializers.HelpDeskConfigModelSerializer
    permission_classes = ()
    authentication_classes = (CsrfExemptSessionAuthentication,)

    def post(self, request, *args, **kwargs):
        config_id = kwargs.get('pk')
        if not config_id:
            return Response('ok')
        try:
            config = models.HelpDeskConfigModel.objects.get(pk=config_id)
        except ObjectDoesNotExist:
            return Response('ok')
        received_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if not received_secret or not config.telegram_webhook_token or received_secret != config.telegram_webhook_token:
            return Response('ok')
        bot = telebot.TeleBot(config.telegram_token)
        data = request.data
        message_dict = data.get('message')
        if not isinstance(message_dict, dict):
            return Response('ok')
        try:
            message = telebot.types.Message.de_json(message_dict)
        except Exception:
            return Response('ok')
        message_date = utils.get_tg_message_date(message)
        if message:
            # запуск
            telegram_id = message.from_user.id
            if message.text and message.text.startswith('/start'):
                return utils.handle_command_start(message, bot)
            else:
                try:
                    org_admin = ContractorModel.objects.get(help_desk_config__telegram_token=bot.token)
                except (ValidationError, ObjectDoesNotExist):
                    # Ответить что мы вас не знаем
                    return Response("ne ok")
                contact_person = models.ContactPersonModel.objects.filter(
                    customer_card__org_admin=org_admin,
                    telegram_id=telegram_id,
                ).order_by('created_at').first()
                if not contact_person:
                    bot.send_message(
                        chat_id=telegram_id,
                        text=f'❗️ Возникла ошибка при запуске бота.\n'
                             f'Пожалуйста, повторите попытку через несколько минут.\n'
                             f'Мы уже уведомили техническую команду и работаем над устранением проблемы.\n'
                             f'🔁 Чтобы перезапустить — нажмите /start'
                    )
                    return Response('contact person not found')
                if contact_person.spam:
                    return Response('ok')
                message_text = message.text if message.text is not None else ''
                reply_to_message = message.reply_to_message
                if reply_to_message:
                    reply_to_message_id = reply_to_message.id
                    reply_instance = models.ContactPersonMessageModel.objects.filter(
                        contact_person=contact_person,
                        channel_id='telegram',
                        message_id=str(reply_to_message_id)
                    ).order_by('-message_date').first()
                else:
                    reply_instance = None
                content_type = message.content_type
                file_dict = []
                file_string = None
                file_name = None
                if not content_type == 'text':
                    file_obj = getattr(message, content_type, None)
                    if file_obj:
                        if isinstance(file_obj, list):
                            file_obj.sort(key=lambda x: x.file_size)
                            file_instance = file_obj[-1]
                        else:
                            file_instance = file_obj
                        file_name = getattr(file_instance, 'file_name', None)
                        get_file_result = bot.get_file(file_instance.file_id)
                        file_path = get_file_result.file_path
                        if not file_name:
                            file_name = f"{uuid.uuid4()}.{get_file_result.file_path.split('.')[-1]}"
                        file_string = bot.download_file(file_path)

                with transaction.atomic():
                    cp_message = models.ContactPersonMessageModel.objects.create(
                        channel_id='telegram',
                        contact_person=contact_person,
                        text=message_text,
                        source_message=data,
                        message_date=message_date,
                        message_id=str(message.id),
                        reply=reply_instance,
                        files_message=file_dict
                        # author?
                    )
                    if file_string and file_name:
                        utils.save_telegram_file(file_string, file_name, cp_message)
        return Response('ok')


class ContactPersonViewSet(BaseModelViewSet):
    model = models.ContactPersonModel
    permission_classes = (IsAuthenticated, permissions.ContactPersonPermission)

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.ContactPersonModelListSerializer(
            page,
            many=True,
            context={"request": request, "view": self}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('post',), detail=True, url_path='mark_as_spam')
    def mark_as_spam(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение контактного лица')
        instance.spam = True
        instance.save(update_fields=('spam',))
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='unmark_as_spam')
    def unmark_as_spam_contact_person(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение контактного лица')
        instance.spam = False
        instance.save(update_fields=('spam',))
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='set_customer_card')
    def set_customer_card(self, request, *args, **kwargs):
        instance = self.get_object()
        org_admin = instance.customer_card.org_admin
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на изменение контактного лица')
        data = request.data
        customer_card_data = data.get('customer_card')
        if not customer_card_data:
            raise drf_exceptions.ValidationError('Укажите карточку клиента')
        if isinstance(customer_card_data, dict):
            serializer = serializers.CustomerCardModelCreateSerializer(
                data=data.get('customer_card'),
                context={'request': request, 'view': self}
            )
            serializer.is_valid(raise_exception=True)
            customer_card = serializer.save()
        elif isinstance(customer_card_data, str):
            try:
                customer_card = models.CustomerCardModel.objects.get(org_admin=org_admin, pk=customer_card_data)
            except (ObjectDoesNotExist, ValidationError):
                raise drf_exceptions.ValidationError('Карточка клиента не найдена')
        else:
            raise drf_exceptions.ValidationError('Некорректная карточка клиента')
        instance.customer_card = customer_card
        instance.unknown = False
        instance.save()
        org_admin = customer_card.org_admin
        unknown_customer_card = utils.get_or_create_unknown_customer_card(org_admin)
        models.HelpDeskTicketModel.objects.filter(
            customer_card=unknown_customer_card,
            contact_person=instance,
        ).update(
            customer_card=customer_card,
        )
        return Response('ok')


class ContactPersonMessageViewSet(BaseModelViewSet):
    model = models.ContactPersonMessageModel

    @action(methods=('get',), detail=False, url_path='get_emails')
    def get_emails(self, request, *args, **kwargs):
        org_admin_id = request.query_params.get('org_admin')
        if not org_admin_id:
            raise drf_exceptions.ValidationError('org_admin is required')
        with transaction.atomic():
            try:
                config = models.HelpDeskConfigModel.objects.select_for_update(nowait=True).get(contractor=org_admin_id)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.ValidationError('config not found')
            letter_count = utils.get_emails(config)
        return Response({'count': letter_count})

    def get_queryset(self):
        return self.model.get_queryset(self.request)

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        user = request.user.profile
        contact_person_id = request.query_params.get('contact_person')
        if contact_person_id:
            try:
                qs = qs.filter(contact_person_id=contact_person_id)
            except ValidationError:
                qs = qs.none()
        ticket_id = request.query_params.get('ticket')
        if ticket_id:
            try:
                qs = qs.filter(tickets=ticket_id)
            except ValidationError:
                qs = qs.none()
            else:
                last_viewed_obj = models.ContactPersonMessageModel.objects.filter(
                    tickets=ticket_id,
                    viewers=user
                ).order_by('-created_at').first()
                if last_viewed_obj:
                    qs = qs.annotate(
                        is_new=Case(
                            When(created_at__gt=last_viewed_obj.created_at, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        )
                    )
                else:
                    qs = qs.annotate(
                        is_new=Value(True)
                    )
        qs = qs.order_by('-created_at',)
        paginator = paginators.ContactPersonMessagePaginator()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.ContactPersonMessageListSerializer(
            page,
            many=True,
            context={"request": request, "view": self}
        )
        return paginator.get_paginated_response(serializer.data)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        data = request.data
        data['is_help_desk'] = True
        with transaction.atomic():
            serializer = serializers.ContactPersonMessageCreateSerializer(
                data=data,
                context={'request': request, 'view': self},
            )
            serializer.is_valid(raise_exception=True)
            message = serializer.save()
            contact_person = message.contact_person
            if message.channel_id == 'internal':
                return Response(serializer.data)
            if message.channel_id == 'internal_chat':
                # from bpms.chat.models import ChatModel, MessageModel
                # from bpms.chat.serializers import MessageListSerializer
                # user = request.user.profile
                # contact_person_user = contact_person.user
                # if not contact_person_user:
                #     return Response(serializer.data)
                # chat = ChatModel.objects.filter(
                #     member__user__in=[user],
                #     is_public=False
                # ).filter(
                #     member__user__in=[contact_person_user]
                # ).first()
                # if not chat:
                #     return Response(serializer.data)
                # if chat.is_public:
                #     raise drf_exceptions.ValidationError('Нельзя писать в групповой чат.')
                # internal_message = MessageModel()
                # internal_message.message_author = user
                # internal_message.text = message.text
                # internal_message.created = timezone.now()
                # internal_message.chat = chat
                # internal_message_reply = None
                # if message.reply:
                #     message_reply = message.reply
                #     reply_uid = message_reply.message_id
                #     if reply_uid:
                #         try:
                #             internal_message_reply = MessageModel.objects.get(message_uid=reply_uid, chat=chat)
                #         except (ValidationError, ObjectDoesNotExist):
                #             pass
                # internal_message.message_reply = internal_message_reply
                # internal_message.save()
                # message.message_id = internal_message.message_uid
                # message.save(update_fields=('message_id',))
                # internal_message.attachments.set(list(message.attachments.all()))
                # internal_message_data = MessageListSerializer(internal_message).data
                # internal_message_data['chat_uid'] = str(chat.chat_uid)
                # internal_message_data['chat_name'] = chat.name
                # internal_message_data['is_public'] = chat.is_public
                # internal_message_data['is_new'] = True
                # data = json.dumps(
                #     {
                #         "event": "chat_message",
                #         "data": internal_message_data,
                #     },
                #     cls=DjangoJSONEncoder,
                # )
                # transaction.on_commit(lambda: socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data))
                return Response(serializer.data)
            try:
                config = contact_person.customer_card.org_admin.help_desk_config
            except AttributeError:
                pass
            else:
                if message.is_help_desk:
                    # Отправка в telegram:
                    if message.channel_id == 'telegram':
                        telegram_id = contact_person.telegram_id
                        if not contact_person.telegram_id:
                            raise drf_exceptions.ValidationError('Контакт не имеет телеграм.')
                        transaction.on_commit(lambda: utils.send_tg_message(config, telegram_id, message))
                    # Отправка в email:
                    elif message.channel_id == 'email':
                        email_address = contact_person.email
                        if not email_address:
                            raise drf_exceptions.ValidationError('Контакт не имеет email-адреса')
                        transaction.on_commit(lambda: utils.send_email(config, email_address, message))
                    else:
                        # TODO отправка напрямую
                        return Response()
        return Response(serializer.data)

    @action(methods=('post',), detail=False, url_path='client/create')
    def create_client_message(self, request, *args, **kwargs):
        data = request.data
        ticket_id = data.get('ticket')
        try:
            ticket = models.HelpDeskTicketModel.objects.get(is_active=True, pk=ticket_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Обращение не найдено')
        if not utils.get_create_message_for_client_permission(ticket):
            raise drf_exceptions.ValidationError('Вы не можете отправлять сообщение через эту форму')
        serializer = serializers.ContactPersonMessageClientCreateSerializer(
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('ok')

    @action(methods=('get',), detail=False, url_path='client/list')
    def list_client_messages(self, request, *args, **kwargs):
        query_params = request.query_params
        qs = self.model.objects.filter(is_active=True,)
        org_admin_id = query_params.get('org_admin')
        if org_admin_id:
            qs = qs.filter(contact_person__customer_card__org_admin=org_admin_id)
        ticket_id = request.query_params.get('ticket')
        if ticket_id:
            qs = qs.filter(tickets=ticket_id)
        user = request.user.profile
        lookup = Q(
            contact_person__user=user,
            contact_person__user__is_active=True,
            contact_person__customer_card__is_active=True
        )
        director_contractors = get_ancestor_departments_related_organizations(
            contractors_where_im_director(user),
            include_self=True
        )
        customer_card_customers = get_ancestor_departments_related_organizations(
                contractors_where_user_has_permission(
                    user.pk,
                    ('help_desk_client_supervisor', 'help_desk_client_admin',),
                    None
                ),
                include_self=True,
            )
        permission_contractors = director_contractors | customer_card_customers
        if permission_contractors:
            lookup = lookup | Q(contact_person__customer_card__customer_id__in=permission_contractors)
        qs = qs.filter(lookup)
        qs = self.filter_queryset(qs)
        qs = qs.order_by('-created_at')
        paginator = paginators.ContactPersonMessagePaginator()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = serializers.ContactPersonMessageClientListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        ).data
        return paginator.get_paginated_response(s_data)


class HelpDeskTicketViewSet(BaseModelViewSet, MeetingConnectMixin):
    model = models.HelpDeskTicketModel

    def perform_update(self, serializer):
        instance = self.get_object()
        if not instance.get_update_permission(self.request):
            raise drf_exceptions.PermissionDenied('Вы не можете изменить это обращение')
        return super().perform_update(serializer)

    def get_data_from_chat(self, data, user):
        from bpms.chat.models import MessageModel
        message_uid = data.get('message_uid')
        cache_key = f'ticket_from_chat_message_{message_uid}_user_{user.pk}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        else:
            if not message_uid:
                raise drf_exceptions.ValidationError('message_uid is required')
            try:
                message = MessageModel.objects.get(
                    message_uid=message_uid,
                    is_system=False,
                    is_deleted=False,
                    # chat__is_public=False,
                )
            except (ObjectDoesNotExist, ValidationError):
                raise drf_exceptions.ValidationError('message not found')
            chat = message.chat
            chat_members = chat.members.all()
            if not chat_members.filter(user=user).exists():
                raise drf_exceptions.PermissionDenied('You are not member in this chat')
            from contractor_permissions.utils import contractors_where_user_has_permission

            # Организации, где пользователь может создавать тикеты:
            help_desk_admin_contractors = contractors_where_user_has_permission(
                user.pk,
                ('help_desk_admin',),
                None
            )
            help_desk_coordinator_contractors = get_ancestor_departments_related_organizations(
                contractors_where_user_has_permission(
                    user.pk,
                    ('help_desk_client_admin',),
                    None
                ),
                include_self=True
            )

            help_desk_manager_contractors = set(
                contractors_where_user_has_permission(user.pk, ('help_desk_manager',), None))
            specialist_customer_cards = models.CustomerCardModel.get_qs_customer_cards_from_specialist(
                user.pk
            ).filter(
                org_admin_id__in=help_desk_manager_contractors
            ).values_list('pk', flat=True)
            if not help_desk_admin_contractors and not help_desk_manager_contractors and not help_desk_coordinator_contractors:
                raise drf_exceptions.ValidationError('Вы не можете создавать обращение для этого клиента')
            if chat.is_public:
                client_user = message.message_author
                # находим customer_card:

                # Находим контактное лицо:
                client_contact_person = models.ContactPersonModel.objects.filter(
                    Q(customer_card__org_admin_id__in=help_desk_admin_contractors) |
                    Q(customer_card__customer_id__in=help_desk_coordinator_contractors) |
                    Q(customer_card_id__in=specialist_customer_cards),
                    is_active=True,
                    customer_card__is_active=True,
                    user=client_user,
                ).order_by('-created_at').first()
                customer_card = client_contact_person.customer_card
                can_update_customer_card = customer_card.get_update_permission(self.request)
                return_data = {
                    'customer_card': serializers.CustomerCardForTicketSerializer(customer_card).data,
                    'contact_person': serializers.ContactPersonModelListSerializer(
                        client_contact_person,
                        context={'request': self.request, 'can_update_customer_card': can_update_customer_card},
                    ).data,
                    'specialist': None,
                }
            else:
                client_member = chat_members.exclude(user=user).order_by('-created_at').first()
                client_user = client_member.user

                # карточки клиентов, где пользователь является актуальным специалистом:
                actual_specialists = utils.get_actual_specialist_from_user(client_user, user)
                if not actual_specialists.exists():
                    raise drf_exceptions.ValidationError('Вы не являетесь специалистом поддержки этого клиента')
                actual_specialist = actual_specialists.order_by('-created_at').first()
                customer_card = actual_specialist.customer_card

                # Находим контактное лицо:
                client_contact_person = models.ContactPersonModel.objects.filter(
                    is_active=True,
                    customer_card__is_active=True,
                    user=client_user,
                    customer_card=customer_card,
                ).order_by('-created_at').first()
                can_update_customer_card = customer_card.get_update_permission(self.request)
                return_data = {
                    'customer_card': serializers.CustomerCardForTicketSerializer(customer_card).data,
                    'contact_person': serializers.ContactPersonModelListSerializer(
                        client_contact_person,
                        context={'request': self.request, 'can_update_customer_card': can_update_customer_card}
                    ).data,
                    'specialist': CachedAppUserSerializer(str(user.pk)).data
                }
                cache.set(cache_key, return_data, timeout=1800)
            return return_data

    @action(methods=('post',), detail=False, url_path='test_tg')
    def test_tg(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            raise drf_exceptions.PermissionDenied('Нет доступа')
        data = request.data
        email = data.get('email')
        try:
            target_user = ProfileModel.objects.get(user__email=email)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('user not found')
        telegram_id = target_user.telegram_id
        if not telegram_id:
            raise drf_exceptions.ValidationError('У пользователя не привязан телеграм')
        from telegram_bot.base import base_bot
        from telebot import types
        redirect_to = data.get('redirect_to', '')
        web_app_info = types.WebAppInfo(url=f'{TG_MINI_APP_URL}?redirect_to={redirect_to}')
        button = types.InlineKeyboardButton(
            text="Тестовая ссылка тыц",
            web_app=web_app_info
        )
        keyboard = types.InlineKeyboardMarkup([[button]])
        base_bot.send_message(
            telegram_id,
            text="тестовое сообщение",
            reply_markup=keyboard,
        )
        return Response('ok')

    @action(methods=('post',), detail=False, url_path='sla')
    def get_sla(self, request, *args, **kwargs):
        return_data = models.HelpDeskTicketModel.get_sla(request.data)
        return Response(return_data)

    @action(methods=('post',), detail=True, url_path='create_interest')
    def create_interest(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not ticket.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете просматривать этот лид')
        from bpms.tasks.crm_lead_interest import create_interest_from_lead

        force_create = request.data.get('force_create', True)
        result = create_interest_from_lead(ticket, request, force_create=force_create)
        return Response(result)

    @action(methods=('get', 'post',), detail=False, url_path='create_from_chat')
    def create_from_chat(self, request, *args, **kwargs):
        user = request.user.profile
        if request.method == 'GET':
            data = request.query_params
            return_data = self.get_data_from_chat(data, user)
            return Response(return_data)
        else:
            data = request.data

            from bpms.chat.models import MessageModel
            try:
                message = MessageModel.objects.get(message_uid=data.get('message_uid'))
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.ValidationError('Сообщение не найдено')
            with transaction.atomic():
                chat = message.chat
                data['channel'] = 'internal_chat'
                data['created_from_messages'] = True
                serializer = serializers.HelpDeskTicketCreateSerializer(
                    data=data,
                    context={'request': request, 'view': self},
                )
                serializer.is_valid(raise_exception=True)
                ticket = serializer.save()

                # Создаем сообщение тикета:
                cp_message = models.ContactPersonMessageModel()
                cp_message.channel_id = 'internal_chat'
                cp_message.contact_person = ticket.contact_person
                cp_message.text = message.text
                cp_message.source_message = dict()
                cp_message.message_date = message.created
                cp_message.message_id = str(message.message_uid)
                cp_message.author = None
                if chat.is_public:
                    cp_message.save(ticket=ticket)
                else:
                    cp_message.save(ticket=ticket)
                attachments = list(message.attachments.all())
                cp_message.attachments.set(attachments)
                ticket.attachments.set(attachments)
                # Тикет с сообщением свяжутся в save() ContactPersonMessageModel
            return Response('ok')

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                "edit": {"availability": True},
                "create_task": {"availability": True},
                "create_nomenclature": {"availability": True},
                "edit_nomenclature": {"availability": True},
                "delete_nomenclature": {"availability": True},
            }
        if instance.get_delete_permission(request):
            actions['delete'] = {'availability': True}
        user = request.user.profile
        available_statuses = instance.get_available_statuses(user)
        if available_statuses:
            available_status_data = models.HelpDeskTicketStatusModel.objects.filter(code__in=available_statuses).values(
                'code',
                'name',
                'color',
            ).order_by('sort', 'name')
            actions['change_status'] = actions['change_status'] = {
                "availability": True,
                "available_statuses": available_status_data
            }
        if user == instance.specialist:
            actions['can_use_timer'] = {'availability': True}
        if instance.create_work_log_permission(request):
            actions['create_cost'] = {'availability': True}
            if instance.edit_work_log_user_permission(request):
                actions['create_cost']['edit_user'] = True
                actions['update_cost'] = {'availability': True, 'edit_user': True}
        if instance.get_take_permission(request):
            actions['take'] = {'availability': True}
        if instance.get_create_message_permission(request):
            actions['create_message'] = {'availability': True}
        if instance.update_execution_result_permission(request):
            actions['edit_execution_result'] = {'availability': True}
        return Response({'actions': actions})

    @action(methods=('post',), detail=True, url_path='take')
    def take_ticket(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_take_permission(request):
            raise drf_exceptions.ValidationError('Вы не можете взять это обращение')
        user = request.user.profile
        instance.specialist = user
        instance.save(update_fields=('specialist',))
        serializer = serializers.HelpDeskTicketListSerializer(instance, context={'request': request, 'view': self})
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='my_tickets_count')
    def get_my_tickets_count(self, request, *args, **kwargs):
        qs = self.get_tickets_queryset(request)
        user = request.user.profile
        statuses = set(models.HelpDeskTicketStatusModel.objects.filter(is_active=True).values_list('code', flat=True))
        completed_statuses = set(utils.get_completed_statuses_id())
        not_completed_statuses = statuses - completed_statuses

        data = qs.aggregate(
            specialist=Count('pk', filter=Q(specialist=user), distinct=True),
            author=Count('pk', filter=Q(author=user), distinct=True),
            is_overdue=Count(
                'pk',
                filter=Q(
                    dead_line__isnull=False,
                    dead_line__lt=timezone.now(),
                    status_id__in=list(not_completed_statuses)
                ),
                distinct=True
            )
        )
        data['visors'] = qs.filter(visors=user).values('pk').distinct().count()
        return Response(data)

    @action(methods=('get',), detail=True, url_path='count')
    def get_count(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user.profile
        messages_qs = models.ContactPersonMessageModel.objects.filter(
                is_active=True,
                tickets=instance,
            ).order_by('-created_at')
        last_viewed_obj = messages_qs.filter(
            viewers=user
        ).first()
        if last_viewed_obj:
            new_message_count = messages_qs.filter(
                created_at__gt=last_viewed_obj.created_at
            ).count()
        else:
            new_message_count = messages_qs.count()
        return Response({'new_message_count': new_message_count})

    @action(methods=('put',), detail=True, url_path='status')
    def update_status(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user.profile
        available_statuses = instance.get_available_statuses(user)
        new_status_code = request.data.get('status')
        if new_status_code not in available_statuses:
            raise drf_exceptions.PermissionDenied('Вы не можете изменять статус этого обращения')
        serializer = serializers.UpdateTicketStatusSerializer(
            instance=instance,
            data=request.data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        is_contact_person = False
        contact_person = instance.contact_person
        if contact_person:
            contact_person_user = contact_person.user
            if contact_person_user == user:
                is_contact_person = True
        if is_contact_person:
            ticket.status_from_client = True
            ticket.save(update_fields=('status_from_client',))
        transaction.on_commit(
            lambda: async_task(notifications.notify_about_new_status, str(user.pk), str(instance.pk), str(instance.status_id))
        )
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='execution_result',)
    def update_execution_result(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.update_execution_result_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете изменять результат выполнения')
        data = request.data
        serializer = serializers.UpdateTicketExecutionResultSerializer(
            instance,
            data=data,
            context={'request': request, 'view': self},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        customer_card = instance.customer_card
        org_admin = customer_card.org_admin
        user = request.user.profile
        has_permission = False

        try:
            check_contractor_permission(
                user.pk,
                org_admin.pk,
                ('help_desk_admin', 'help_desk_supervisor'),
                None
            )
        except drf_exceptions.PermissionDenied:
            try:
                check_contractor_permission(
                    user.pk,
                    org_admin.pk,
                    ('help_desk_manager',),
                    None
                )
            except drf_exceptions.PermissionDenied:
                pass
            else:
                if customer_card.actual_specialists.filter(user=user).exists():
                    has_permission = True
                else:
                    if instance.visors.filter(pk=user.pk).exists() or instance.members.filter(pk=user.pk).exists():
                        org_admin_tree = get_tree_departments_related_organizations((org_admin.pk,))
                        if not user.my_organizations.isdisjoint(org_admin_tree):
                            has_permission = True
        else:
            has_permission = True
        if not has_permission:
            raise drf_exceptions.PermissionDenied()
        return super().retrieve(request, *args, **kwargs)

    def get_tickets_queryset(self, request):
        """Только фильтрации/права/сортировка. Без select_related и annotate (для пагинации по id)."""
        queryset = self.model.get_queryset(self.request, queryset_params={'view_type': 'contractor'})
        queryset = queryset.order_by('-created_at')
        queryset = self.filter_queryset(queryset)

        contract = request.query_params.get('contract')
        if contract:
            try:
                queryset = queryset.filter(analytics_key__customer_contract_id=contract)
            except ValidationError:
                pass
        project = request.query_params.get('project')
        if project:
            try:
                queryset = queryset.filter(analytics_key__project_id=project)
            except ValidationError:
                pass

        customer_card = request.query_params.get('customer_card')
        if customer_card:
            try:
                queryset = queryset.filter(customer_card_id=customer_card)
            except ValidationError:
                pass
        else:
            display = request.query_params.get('display', '')
            if display == 'leads':
                queryset = queryset.filter(ticket_type_id='lead')
            else:
                queryset = queryset.exclude(ticket_type_id='lead')
        search = request.query_params.get('search')
        if search:
            search_result = get_search_result(self.model, search)
            search_result_ids = [item['id'] for item in search_result]
            queryset = queryset.filter(pk__in=list(search_result_ids))
        exclude_id = request.query_params.get('exclude')
        if exclude_id:
            try:
                queryset = queryset.exclude(pk=exclude_id)
            except ValidationError:
                pass
        return queryset

    def prepare_tickets_queryset(self, queryset):
        """
        select_related, annotate, загрузка related_tasks по pk тикетов.
        Возвращает список тикетов с заполненным related_tasks.
        """
        from bpms.tasks.models import TaskModel

        qs = queryset.select_related(
            'sla_value__sla',
            'customer_card',
            'contact_person',
        ).annotate(avg_rating=Avg('ratings__rating'))
        tickets = list(qs)
        related_tasks_by_ticket = {}
        if tickets:
            ticket_ids_str = [str(ticket.pk) for ticket in tickets]
            related_tasks = TaskModel.objects.filter(
                reason__in=ticket_ids_str,
                is_active=True
            ).only('id', 'counter', 'reason')
            for task in related_tasks:
                tid = task.reason
                if tid not in related_tasks_by_ticket:
                    related_tasks_by_ticket[tid] = []
                related_tasks_by_ticket[tid].append(task)
        for ticket in tickets:
            ticket.related_tasks = related_tasks_by_ticket.get(str(ticket.pk), [])
        return tickets

    def list(self, request, *args, **kwargs):
        base_queryset = self.get_tickets_queryset(request)
        order_by = base_queryset.query.order_by

        ids_queryset = base_queryset.values_list('pk', flat=True)
        page_ids = self.paginate_queryset(ids_queryset)
        if page_ids is None:
            return Response([])

        ticket_ids = list(page_ids)

        page_queryset = self.model.objects.filter(pk__in=ticket_ids)
        if order_by:
            page_queryset = page_queryset.order_by(*order_by)
        tickets_to_process = self.prepare_tickets_queryset(page_queryset)

        serializer = self.get_serializer(tickets_to_process, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my_day', url_name='my-day')
    def my_day(self, request, *args, **kwargs):
        """Список тикетов пользователя для 'Моего дня'."""
        def get_empty_paginated_response():
            queryset = self.model.objects.none()
            page = self.paginate_queryset(queryset)
            serializer = serializers.HelpDeskTicketMyDaySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        group = request.query_params.get('group')
        if not group or group not in ('activity', 'other'):
            # group обязателен, если не передан id тикета (получение одного тикета по id)
            if not request.query_params.get('id'):
                raise drf_exceptions.ValidationError('Обязательный параметр group должен быть "activity" или "other"')

        base_queryset = get_my_day_tickets_queryset(request)

        start = get_datetime_param(request, 'start')
        end = get_datetime_param(request, 'end')
        if not start and not end:
            current_date = timezone.localdate()
            start_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.min))
            end_of_day = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time.max))
            start = start_of_day.isoformat()
            end = end_of_day.isoformat()
        start_date = parse_date(start.split('T')[0]) if start else None
        end_date = parse_date(end.split('T')[0]) if end else None

        order_by = base_queryset.query.order_by
        ids_queryset = base_queryset.values_list('pk', flat=True)
        page_ids = self.paginate_queryset(ids_queryset)
        page_ticket_ids = list(page_ids)

        if not page_ticket_ids:
            return get_empty_paginated_response()

        page_queryset = self.model.objects.filter(pk__in=page_ticket_ids)
        if order_by:
            page_queryset = page_queryset.order_by(*order_by)
        tickets_to_process = self.prepare_tickets_queryset(page_queryset)

        analytics_data_map = build_my_day_ticket_analytics(
            ticket_ids=page_ticket_ids,
            request=request,
            start_date=start_date,
            end_date=end_date,
        )

        serializer = serializers.HelpDeskTicketMyDaySerializer(
            tickets_to_process,
            many=True,
            context={'analytics_data_map': analytics_data_map},
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=('get',), detail=False, url_path='short_list')
    def short_list(self, request, *args, **kwargs):
        queryset = self.get_tickets_queryset(request).select_related(
            'sla_value__sla',
            'customer_card',
            'contact_person',
        ).annotate(avg_rating=Avg('ratings__rating'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('post',), detail=False, url_path='assign_analytics_key')
    def assign_analytics_key(self, request, *args, **kwargs):
        payload = request.data if isinstance(request.data, dict) else {}
        raw_ticket_ids = payload.get('ticket_ids')
        analytics_key_id = payload.get('analytics_key')

        if not isinstance(raw_ticket_ids, list) or not raw_ticket_ids:
            raise drf_exceptions.ValidationError({'ticket_ids': 'ticket_ids must be a non-empty list.'})
        if not analytics_key_id:
            raise drf_exceptions.ValidationError({'analytics_key': 'analytics_key is required.'})

        ticket_ids = [str(ticket_id).strip() for ticket_id in raw_ticket_ids if str(ticket_id).strip()]
        ticket_ids = list(dict.fromkeys(ticket_ids))
        if not ticket_ids:
            raise drf_exceptions.ValidationError({'ticket_ids': 'ticket_ids must contain valid ids.'})

        from customer_contracts.models import CustomerContractProjectModel

        try:
            analytics_key = CustomerContractProjectModel.get_queryset(request).select_related(
                'customer_contract',
            ).get(pk=analytics_key_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError({'analytics_key': 'Analytics key not found or unavailable.'})

        if not analytics_key.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied('No access to selected analytics key.')

        contract = analytics_key.customer_contract
        if not contract:
            raise drf_exceptions.ValidationError({'analytics_key': 'Analytics key contract is invalid.'})
        served_customer_ids = set(contract.serviced_cards_relations.filter(
            is_active=True
        ).values_list('customer_card_id', flat=True))

        tickets_qs = self.model.get_queryset(
            request,
            queryset_params={'view_type': 'contractor'}
        ).filter(
            is_active=True,
            pk__in=ticket_ids,
        ).select_related('customer_card')
        tickets = list(tickets_qs)
        if len(tickets) != len(ticket_ids):
            raise drf_exceptions.PermissionDenied('Some selected tickets are unavailable.')

        with transaction.atomic():
            for ticket in tickets:
                if not ticket.get_update_permission(request):
                    raise drf_exceptions.PermissionDenied('No permission to update one or more selected tickets.')
                if ticket.customer_card_id not in served_customer_ids:
                    raise drf_exceptions.ValidationError(
                        'Selected ticket customer is not served by analytics key contract.'
                    )
                serializer = serializers.HelpDeskTicketUpdateSerializer(
                    instance=ticket,
                    data={'analytics_key': analytics_key.pk},
                    partial=True,
                    context={'request': request, 'view': self},
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

        return Response({'updated': len(tickets)}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='for_client/list')
    def get_client_list(self, request, *args, **kwargs):
        user = request.user.profile
        qs = self.model.objects.filter(is_active=True,).exclude(ticket_type_id='lead')
        chat_id = request.query_params.get('chat')
        if not chat_id:
            qs = self.model.filter_by_permissions(qs, request, view_type='client')
        else:
            from bpms.chat.models import ChatModel
            try:
                chat = ChatModel.objects.get(is_active=True, chat_uid=chat_id)
            except (ValidationError, ObjectDoesNotExist):
                qs = qs.none()
            else:
                if user.pk not in list(chat.members.all().values_list('user', flat=True)):
                    qs = qs.none()
                else:
                    qs = qs.filter(message_share__chat=chat).distinct()
        org_admin_id = request.query_params.get('org_admin')
        if org_admin_id:
            qs = qs.filter(cutomer_card__org_admin=org_admin_id)
        qs = qs.order_by('-created_at')
        qs = self.filter_queryset(qs)
        qs = qs.annotate(avg_rating=Avg('ratings__rating'))

        # Аннотируем для сортировки
        qs = qs.annotate(
            contact_person_user=Concat(
                Coalesce('contact_person__user__user__last_name', Value('')),
                Value(' '),
                Coalesce('contact_person__user__user__first_name', Value('')),
                output_field=CharField()
            )
        )
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.TicketForClientListSerializer(
            page, many=True, context={'request': request, 'view': self}
        )
        s_data = serializer.data
        return paginator.get_paginated_response(s_data)

    @action(methods=('get',), detail=True, url_path='for_client/detail')
    def get_client_detail(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            return Response(
                data={
                    'detail': 'Обращение создано другим пользователем. У вас недостаточно прав для просмотра'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = serializers.TicketForClientDetailSerializer(
            instance,
            context={'request': request, 'view': self}
        )
        s_data = serializer.data
        return Response(s_data)

    @action(methods=('get',), detail=True, url_path='for_client/action_info')
    def get_client_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        contact_person = instance.contact_person
        if contact_person:
            contact_person_user = contact_person.user
            if contact_person_user:
                user = request.user.profile
                if contact_person_user == user:
                    actions["rate"] = {"availability": True}
                    if utils.get_create_message_for_client_permission(instance):
                        actions["create_message"] = {"availability": True}
        available_statuses = instance.get_available_statuses(request.user.profile)
        if available_statuses:
            available_status_data = models.HelpDeskTicketStatusModel.objects.filter(code__in=available_statuses).values(
                'code',
                'name',
                'color',
            ).order_by('sort', 'name')
            actions['change_status'] = {
                "availability": True,
                "available_statuses": available_status_data
            }
        return Response({'actions': actions})

    @action(methods=('post',), detail=False, url_path='for_client/create')
    def create_for_client(self, request, *args, **kwargs):
        serializer = serializers.TicketForClientCreateSerializer(
            data=request.data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=('get',), detail=True, url_path='work_log/duration')
    def get_work_log_duration(self, request, *args, **kwargs):
        user = request.user.profile
        ticket = self.get_object()
        if not ticket.get_detail_permission(request):
            raise drf_exceptions.NotFound()
        duration, is_current, incomplete_duration = utils.get_work_log_duration(user, ticket)
        return Response({'duration': duration, 'duration_incomplete': incomplete_duration, 'is_current': is_current})

    @action(methods=('post',), detail=True, url_path='work_log/start')
    def start_work_log(self, request, *args, **kwargs):
        user = request.user.profile
        ticket = self.get_object()

        duration, is_current = utils.start_work_log_timer(user, ticket)
        return Response({'duration': duration, 'is_current': is_current})

    @action(methods=('post',), detail=True, url_path='work_log/stop')
    def stop_work_log(self, request, *args, **kwargs):
        user = request.user.profile
        ticket = self.get_object()

        # фронт шлёт {"duration_incomplete": <секунды>}
        provided = request.data.get('duration_incomplete')
        description = request.data.get('description')
        is_result = request.data.get('is_result', False)
        duration, is_current = utils.stop_work_log_timer(
            user,
            ticket,
            provided_duration=provided,
            description=description,
            is_result=is_result,
        )
        return Response({'duration': duration, 'is_current': is_current})

    @action(methods=('get',), detail=True, url_path='work_log/list')
    def list_work_log(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not ticket.get_detail_permission(request):
            return Response()
        qs = ticket.work_logs.filter(is_active=True).order_by('-is_current', '-date', '-created_at')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = serializers.WorkLogListSerializer(page, many=True, context={'request': request, 'view': self}).data
        return paginator.get_paginated_response(s_data)

    @action(methods=('get',), detail=False, url_path='work_log/(?P<pk>[^/.]+)/action_info')
    def get_work_log_action_info(self, request, *args, **kwargs):
        actions = dict()
        work_log_id = kwargs.get('pk')
        try:
            work_log = models.HelpDeskWorkLogModel.objects.get(is_active=True, pk=work_log_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'actions': actions})
        if work_log.get_update_permission(request):
            actions = {
                'edit': {'availability': True},
                'delete': {'availability': True}
            }
            if work_log.ticket.edit_work_log_user_permission(request):
                actions['edit']['edit_user'] = True
        return Response({'actions': actions})

    @action(methods=('put', 'patch'), detail=True, url_path='work_log/update')
    def update_work_log(self, request, *args, **kwargs):
        partial = request.method == 'PATCH'
        ticket = self.get_object()
        work_log_id = request.data.get('id')
        try:
            work_log = ticket.work_logs.get(pk=work_log_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Запись не найдена')
        if not work_log.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете редактировать эту запись')
        serializer = serializers.WorkLogUpdateSerializer(
            instance=work_log,
            data=request.data,
            partial=partial,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='work_log/create')
    def create_work_log(self, request, *args, **kwargs):
        user = request.user.profile
        ticket = self.get_object()
        if not ticket.create_work_log_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете создать запись для этого тикета')
        data = request.data
        data['ticket'] = ticket.pk
        data['user'] = user
        serializer = serializers.WorkLogCreateSerializer(
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='work_log/delete')
    def delete_work_log(self, request, *args, **kwargs):
        ticket = self.get_object()
        data = request.data
        work_log_id = data['id']
        try:
            work_log = ticket.work_logs.get(pk=work_log_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Запись не найдена')
        if not work_log.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете удалять эту запись')
        work_log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HelpDeskTicketStatusListView(generics.ListAPIView):
    serializer_class = serializers.HelpDeskTicketStatusSerializer
    queryset = models.HelpDeskTicketStatusModel.objects.filter(is_active=True).order_by('sort', 'name',)
    permission_classes = (IsAuthenticated,)


class CustomerCardAdminViewSet(BaseCatalogViewSet):
    model = models.CustomerCardAdminModel

    def list(self, request, *args, **kwargs):
        org_admin = request.query_params.get('org_admin')
        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        if not org_admin:
            qs = qs.none()
        else:
            try:
                qs = qs.filter(org_admin_id=org_admin)
            except ValidationError:
                qs = qs.none()
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(Q(bin__icontains=search) | Q(name__icontains=search))
        qs = qs.order_by('name', 'bin',)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='delete')
    def delete_admin(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        instance.delete()
        return Response(status.HTTP_204_NO_CONTENT)


class ClientOrgAdminView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user.profile
        org_admins_id = models.ContactPersonModel.objects.filter(
            user=user,
            is_active=True,
            customer_card__is_active=True,
            customer_card__org_admin__is_active=True,
        ).distinct('customer_card__org_admin').values_list('customer_card__org_admin', flat=True)
        org_admins = ContractorModel.objects.filter(pk__in=org_admins_id)
        serializer = serializers.MyOrgAdminSerializer(org_admins, many=True, context={'request': request, 'view': self})
        return Response(serializer.data)


class SelectedOrgAdminView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user.profile
        key = self.get_cache_key(user)
        contractor_id = cache.get(key, None)
        if not contractor_id:
           return Response()
        org_admins_id = models.ContactPersonModel.objects.filter(
            user=user,
            is_active=True,
            customer_card__is_active=True,
            customer_card__org_admin__is_active=True,
        ).distinct('customer_card__org_admin').values_list('customer_card__org_admin', flat=True)
        org_admins = ContractorModel.objects.filter(pk__in=org_admins_id)
        org_admin = org_admins.filter(pk=contractor_id).first()
        if not org_admin:
            return Response()
        s_data = serializers.MyOrgAdminSerializer(org_admin, context={'request': request, 'view': self}).data
        return Response(s_data)

    def post(self, request, *args, **kwargs):
        key = self.get_cache_key(request.user.profile)
        org_admin_id = request.data.get('id')
        if not org_admin_id:
            cache.delete(key)
            return Response('ok')
        try:
            contractor = ContractorModel.objects.get(pk=org_admin_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('invalid id')
        value = str(contractor.pk)
        cache.set(key, value, timeout=None)
        return Response('ok')

    def get_cache_key(self, profile):
        return f"help_desk_selected_org_admin_{profile.pk}"


@csrf_exempt
def upload_customer_cards(request):
    if request.user.is_anonymous:
        return JsonResponse(data={"result": "ne_ok"}, status=status.HTTP_401_UNAUTHORIZED, )
    if not request.user.is_superuser:
        return JsonResponse(data={"result": "ne_ok"}, status=status.HTTP_403_FORBIDDEN,)
    if not (request.method == 'POST' and request.FILES):
        return HttpResponse('not_ok')
    org_admin_id = request.POST.get('org_admin')
    if not org_admin_id:
        raise drf_exceptions.ValidationError('org_admin is required')
    try:
        org_admin = ContractorModel.objects.get(pk=org_admin_id)
    except (ValidationError, ObjectDoesNotExist):
        raise drf_exceptions.ValidationError('org_admin not found')
    file = request.FILES.getlist('upload')
    if not file:
        raise drf_exceptions.ValidationError('file is required')

    try:
        utils.handle_upload_customer_cards(org_admin, file[0])
    except ValidationError as ex:
        return JsonResponse({"result": ex.message})
    return JsonResponse({"result": "ok"})


class HelpDeskTicketCategoryViewSet(BaseCatalogViewSet):
    model = models.HelpDeskTicketCategoryModel
    permission_classes = (IsAuthenticated, permissions.HelpDeskTicketCategoryPermission,)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions['edit'] = {'availability': True}
            actions['delete'] = {'availability': True}
        return Response({'actions': actions})

    @action(methods=('get', ), detail=False, url_path='action_info_from_contractor',)
    def get_action_info_from_contractor(self, request, *args, **kwargs):
        actions = dict()
        contractor_id = request.query_params.get('contractor')
        if not contractor_id:
            return Response({'actions': actions})
        user = request.user.profile
        if not utils.check_ticket_category_create_permission(user, uuid.UUID(contractor_id)):
            return Response({'actions': actions})
        actions = {
            'create': {'availability': True},
            'edit': {'availability': True},
            'delete': {'availability': True},
        }
        return Response({'actions': actions})

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        search = request.query_params.get('search')
        if search:
            search_result = get_search_result(self.model, search)
            search_result_ids = [item['id'] for item in search_result]
            queryset = queryset.filter(pk__in=list(search_result_ids))
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ContactPersonPostViewSet(BaseCatalogViewSet):
    model = models.ContactPersonPostModel
    permission_classes = (IsAuthenticated, permissions.ContactPersonPostPermission,)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions['edit'] = {'availability': True}
            actions['delete'] = {'availability': True}
        return Response({'actions': actions})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        contractor_id = request.query_params.get('contractor')
        search = request.query_params.get('search')
        if search:
            search_result = get_search_result(self.model, search)
            search_result_ids = [item['id'] for item in search_result]
            queryset = queryset.filter(pk__in=list(search_result_ids))
        from users.utils import get_tree_departments_related_organizations
        if contractor_id:
            contractors_id = get_tree_departments_related_organizations((contractor_id,))
            queryset = queryset.filter(Q(contractor__isnull=True) | Q(contractor_id__in=contractors_id))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class HelpDeskOrgAdminActionInfo(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        org_admin_id = kwargs.get('pk')
        actions = dict()
        if not org_admin_id:
            return Response(actions)
        try:
            org_admin = ContractorModel.objects.get(is_active=True, pk=org_admin_id)
        except (ObjectDoesNotExist, ValidationError):
            return Response(actions)
        # Может создавать категорию тикета:
        user = request.user.profile
        if utils.check_ticket_category_create_permission(user, org_admin.pk):
            actions['create_category'] = {"availability": True}
            actions['edit_category'] = {"availability": True}
            actions['delete_category'] = {"availability": True}
        # Может создавать контактное лицо:
        if utils.check_contact_person_create_permission(user, org_admin.pk):
            actions['create_contact_person'] = {"availability": True}
        return Response(actions)


class DefaultTicketVisorView(APIView):

    def post(self, request, *args, **kwargs):
        """"
        Устанавливает участнику организации, является ли он наблюдателем обращения по умолчанию (default_ticket_visor).
        """
        data = request.data
        contractor_id = data.get('contractor')
        try:
            contractor = ContractorModel.objects.get(is_active=True, pk=contractor_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Организация не найдена')
        from contractor_permissions.utils import check_contractor_permission
        user = request.user.profile
        check_contractor_permission(user.pk, contractor.pk, ('help_desk_admin', 'help_desk_manager',), None)
        profile_id = data.get('user')
        try:
            profile = ProfileModel.objects.get(
                is_active=True,
                pk=profile_id
            )
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Пользователь не найден')
        contractor_profile = ContractorProfileModel.objects.get(
            user=profile,
            contractor=contractor,
        )
        default_ticket_visor = bool(data.get('default_ticket_visor'))
        contractor_profile.default_ticket_visor = default_ticket_visor
        contractor_profile.save(update_fields=('default_ticket_visor',),)
        return Response({'default_ticket_visor': default_ticket_visor})

    def get(self, request, *args, **kwargs):
        """
        Список наблюдателей обращений по умолчанию для организации contractor
        """
        contractor_id = request.query_params.get('contractor')
        if not contractor_id:
            raise drf_exceptions.ValidationError('contractor is required.')
        user = request.user.profile
        user_organizations = user.my_organizations
        if uuid.UUID(contractor_id) not in user_organizations:
            raise drf_exceptions.PermissionDenied()
        default_visors = list(ContractorProfileModel.objects.filter(
            contractor_id=contractor_id,
            default_ticket_visor=True,
        ).order_by(
            'user__user__last_name',
            'user__user__first_name',
        ).values_list('user', flat=True))
        data = CachedAppUserSerializer(default_visors, many=True).data
        return Response(data)


class HelpDeskCostViewSet(BaseModelViewSet):
    model = models.HelpDeskCostModel
    permission_classes = (IsAuthenticated, permissions.HelpDeskCostPermission)


def hep_desk_costs(request, ticket_id):
    if request.user.is_anonymous:
        return HttpResponse('<h2>Авторизуйтесь для доступа к странице</h2>', status=status.HTTP_401_UNAUTHORIZED)
    try:
        ticket = models.HelpDeskTicketModel.objects.get(pk=ticket_id)
    except (ValidationError, ObjectDoesNotExist):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
    if not ticket.get_update_permission(request):
        return HttpResponse('<h2>У вас нет доступа к данной странице</h2>', status=status.HTTP_403_FORBIDDEN)
    cost_form_set = inlineformset_factory(
        models.HelpDeskTicketModel,
        models.HelpDeskCostModel,
        forms.HelpDeskCostForm,
        # fields=('goods', 'quantity',),
        fk_name='owner',
        extra=0,
        can_delete=True,
    )

    if request.method == 'GET':
        formset = cost_form_set(instance=ticket, form_kwargs={'ticket_instance': ticket})
        context = {'request': request, 'formset': formset, 'parent': ticket, 'parent_number': ticket.number}
        return render(request, 'help_desk_costs.html', context)
    elif request.method == 'POST':
        formset = cost_form_set(request.POST, instance=ticket, form_kwargs={'ticket_instance': ticket})
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Данные успешно сохранены!')
            return redirect(request.path)
        else:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content=formset.errors)
    else:
        return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class SetSpecialistsInAllCustomers(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = request.data
        org_admin_id = data.get('org_admin')
        if not org_admin_id:
            raise drf_exceptions.ValidationError('org_admin required')
        try:
            org_admin = ContractorModel.objects.get(pk=org_admin_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('org admin not found')
        specialist_id_list = data.get('specialists')
        if not specialist_id_list:
            raise drf_exceptions.ValidationError('specialists required')
        from contractor_permissions.utils import users_that_have_permission_in_contractors
        help_desk_manager_user_id_list = users_that_have_permission_in_contractors(
            (org_admin.pk,),
            'help_desk_manager',
            None
        )
        specialists = list(ProfileModel.objects.filter(pk__in=specialist_id_list))
        for specialist in specialists:
            if specialist.pk not in help_desk_manager_user_id_list:
                raise drf_exceptions.ValidationError(f"{specialist.pk} is not help desk manager")
        customer_cards = models.CustomerCardModel.objects.filter(
            is_active=True,
            unknown=False,
            org_admin=org_admin,
        )
        is_reserve = bool(data.get('is_reserve'))
        for customer_card in customer_cards:
            for specialist in specialists:
                try:
                    models.CustomerSupportSpecialistModel.objects.create(
                        customer_card=customer_card,
                        user=specialist,
                        is_reserve=is_reserve,
                    )
                except IntegrityError:
                    pass
        return Response('ok')
