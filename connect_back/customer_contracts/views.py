import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status
from rest_framework import exceptions as drf_exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action

from common.views import BaseModelViewSet
from common.serializers import SelectListSerializer
from common.catalogs.serializers import LegalEntityCreateFrom1CSerializer
from common.catalogs.models import LegalEntityModel
from common.paginators import CustomPagination

from users.utils import get_ancestor_departments_related_organizations

from contractor_access_tokens.auth_classes import Contractor1CAccessTokenAuthentication
from contractor_access_tokens.permissions import Contractor1CAccessTokenPermission

from help_desk.models import CustomerCardModel
from help_desk.serializers import CustomerCardCreateFrom1CSerializer, CustomerCardModelShortSerializer

from . import models, serializers, permissions


class CustomerContractViewSet(BaseModelViewSet):
    model = models.CustomerContractModel
    permission_classes = (IsAuthenticated, permissions.CustomerContractPermission,)

    def _get_interest(self, request, interest_id=None):
        """Найти доступный пользователю TaskModel с task_type='interest'."""
        raw_id = interest_id or request.data.get('interest') or request.query_params.get('interest')
        if not raw_id:
            raise drf_exceptions.ValidationError({'interest': 'Укажите интерес.'})
        try:
            interest_uuid = uuid.UUID(str(raw_id))
        except (TypeError, ValueError):
            raise drf_exceptions.ValidationError({'interest': 'Некорректный идентификатор интереса.'})

        from bpms.tasks.models import TaskModel
        try:
            return TaskModel.get_queryset(request).get(pk=interest_uuid, task_type_id='interest', is_active=True)
        except TaskModel.DoesNotExist:
            raise drf_exceptions.NotFound('Интерес не найден или недоступен.')

    def _get_interest_needs(self, request, interest):
        """Получить потребности интереса для переноса в предмет договора."""
        from bpms.tasks.models import TaskInterestNeedModel

        need_ids = request.data.get('need_ids')
        qs = TaskInterestNeedModel.objects.filter(task=interest, is_active=True).select_related('goods')
        if need_ids in (None, ''):
            return list(qs)
        if not isinstance(need_ids, (list, tuple)):
            raise drf_exceptions.ValidationError({'need_ids': 'Передайте список потребностей.'})
        normalized_ids = []
        for raw_id in need_ids:
            try:
                normalized_ids.append(uuid.UUID(str(raw_id)))
            except (TypeError, ValueError):
                raise drf_exceptions.ValidationError({'need_ids': 'В списке есть некорректный id потребности.'})
        needs = list(qs.filter(pk__in=normalized_ids))
        found_ids = {need.pk for need in needs}
        missing_ids = [str(need_id) for need_id in normalized_ids if need_id not in found_ids]
        if missing_ids:
            raise drf_exceptions.ValidationError({
                'need_ids': f'Потребности не найдены или недоступны: {", ".join(missing_ids)}'
            })
        return needs

    def _copy_needs_to_contract(self, contract, interest, needs, replace=False):
        """Скопировать потребности интереса в предмет CRM-договора.

        При повторном переносе обновляем существующую строку по source_need,
        чтобы не плодить дубли одного и того же запроса клиента.
        """
        if replace:
            models.CustomerContractSubjectModel.objects.filter(
                customer_contract=contract,
                source_interest=interest,
                is_active=True,
            ).update(is_active=False, deleted_at=timezone.now())

        created_or_updated = []
        for need in needs:
            subject = models.CustomerContractSubjectModel.objects.filter(
                customer_contract=contract,
                source_need=need,
            ).order_by('-is_active', '-created_at').first()
            if subject is None:
                subject = models.CustomerContractSubjectModel(
                    customer_contract=contract,
                    source_interest=interest,
                    source_need=need,
                )
            subject.is_active = True
            subject.deleted_at = None
            subject.source_interest = interest
            subject.goods = need.goods
            subject.name = need.name
            subject.name_short = need.name_short
            subject.article_number = need.article_number
            subject.base_measure_unit = need.base_measure_unit
            subject.measure_unit = need.measure_unit
            subject.quantity = need.quantity
            subject.price = need.price or Decimal('0')
            if subject.goods_id and subject.price <= 0:
                subject.price = subject.goods.price_by_catalog or Decimal('0')
            subject.comment = need.comment
            subject.save()
            created_or_updated.append(subject)
        return created_or_updated

    def _estimate_needs_amount(self, needs):
        """Оценить сумму договора по потребностям, если пользователь не указал сумму."""
        amount = Decimal('0')
        for need in needs:
            price = need.price or Decimal('0')
            if need.goods_id and price <= 0:
                price = need.goods.price_by_catalog or Decimal('0')
            amount += (need.quantity or Decimal('0')) * price
        return amount.quantize(Decimal('0.01'))

    def _serialize_interest_contract_context(self, request, interest, contracts):
        """Собрать контекст для фронта: интерес, потребности и договоры клиента."""
        from bpms.tasks.serializers import TaskInterestNeedListSerializer

        needs_qs = interest.interest_needs.filter(is_active=True).select_related(
            'goods',
            'measure_unit',
            'base_measure_unit',
        ).order_by('created_at')
        interest_amount = sum((need.amount or Decimal('0')) for need in needs_qs)
        customer_card = None
        if interest.customer_card_id:
            customer_card = CustomerCardModelShortSerializer(interest.customer_card).data

        return {
            'interest': {
                'id': str(interest.pk),
                'counter': getattr(interest, 'counter', None),
                'name': getattr(interest, 'name', '') or str(interest),
                'customer_card': customer_card,
                'amount': str(interest_amount),
            },
            'needs': TaskInterestNeedListSerializer(
                needs_qs,
                many=True,
                context={'request': request, 'view': self},
            ).data,
            'contracts': serializers.CustomerContractDetailSerializer(
                contracts,
                many=True,
                context={'request': request, 'view': self},
            ).data,
        }

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        actions = dict()
        if instance.get_update_permission(request):
            actions['served_organizations_edit'] = {'availability': True}
            if not instance.external_id:
                actions['edit'] = {'availability': True}
                actions['delete'] = {'availability': True}
        return Response({'actions': actions})

    def perform_update(self, serializer):
        instance = self.get_object()
        if not instance.get_update_permission(self.request):
            raise drf_exceptions.PermissionDenied('Вы не можете изменить этот контракт')
        return super().perform_update(serializer)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(methods=('get',), detail=True, url_path='service_cards')
    def service_cards(self, request, *args, **kwargs):
        contract = self.get_object()
        if not contract.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied('No access to this contract')

        qs = CustomerCardModel.get_queryset(request).filter(
            serviced_contracts_relations__customer_contract=contract,
            serviced_contracts_relations__is_active=True,
        ).distinct().order_by('name', '-created_at')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = CustomerCardModelShortSerializer(
            page,
            many=True,
            context={'request': request, 'view': self}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=('post',), detail=True, url_path='service_cards/bind')
    def bind_service_cards(self, request, *args, **kwargs):
        contract = self.get_object()
        if not contract.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('No permission to update this contract')
        if not contract.organization_id:
            raise drf_exceptions.ValidationError({'organization': 'Contract organization is required'})

        customer_cards_raw = request.data.get('customer_cards')
        if customer_cards_raw is None:
            one_customer_card = request.data.get('customer_card')
            if one_customer_card is not None:
                customer_cards_raw = [one_customer_card]
        if not isinstance(customer_cards_raw, (list, tuple)) or not customer_cards_raw:
            raise drf_exceptions.ValidationError({'customer_cards': 'Provide at least one customer card id'})

        normalized_ids = []
        for card_id in customer_cards_raw:
            if card_id in (None, ''):
                continue
            normalized_ids.append(str(card_id))
        normalized_ids = list(dict.fromkeys(normalized_ids))
        if not normalized_ids:
            raise drf_exceptions.ValidationError({'customer_cards': 'Provide valid customer card ids'})

        customer_cards_qs = CustomerCardModel.get_queryset(request).filter(
            pk__in=normalized_ids,
            org_admin_id=contract.organization_id,
            is_active=True,
        )
        found_ids = {str(each) for each in customer_cards_qs.values_list('pk', flat=True)}
        missing_ids = [each for each in normalized_ids if each not in found_ids]
        if missing_ids:
            raise drf_exceptions.ValidationError({
                'customer_cards': f'Cards are unavailable for this contract organization: {", ".join(missing_ids)}'
            })

        created_count = 0
        reactivated_count = 0
        with transaction.atomic():
            for card in customer_cards_qs:
                relation = models.CustomerContractServicedCardModel.objects.filter(
                    customer_contract=contract,
                    customer_card=card,
                ).first()
                if relation is None:
                    models.CustomerContractServicedCardModel.objects.create(
                        customer_contract=contract,
                        customer_card=card,
                    )
                    created_count += 1
                    continue

                if not relation.is_active:
                    relation.is_active = True
                    relation.deleted_at = None
                    relation.save(update_fields=('is_active', 'deleted_at', 'updated_at'))
                    reactivated_count += 1

        return Response(
            {'created': created_count, 'reactivated': reactivated_count},
            status=status.HTTP_200_OK
        )

    @action(methods=('post',), detail=True, url_path='service_cards/unbind')
    def unbind_service_cards(self, request, *args, **kwargs):
        contract = self.get_object()
        if not contract.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('No permission to update this contract')
        if not contract.organization_id:
            raise drf_exceptions.ValidationError({'organization': 'Contract organization is required'})

        customer_cards_raw = request.data.get('customer_cards')
        if customer_cards_raw is None:
            one_customer_card = request.data.get('customer_card')
            if one_customer_card is not None:
                customer_cards_raw = [one_customer_card]
        if not isinstance(customer_cards_raw, (list, tuple)) or not customer_cards_raw:
            raise drf_exceptions.ValidationError({'customer_cards': 'Provide at least one customer card id'})

        normalized_ids = []
        for card_id in customer_cards_raw:
            if card_id in (None, ''):
                continue
            normalized_ids.append(str(card_id))
        normalized_ids = list(dict.fromkeys(normalized_ids))
        if not normalized_ids:
            raise drf_exceptions.ValidationError({'customer_cards': 'Provide valid customer card ids'})

        customer_cards_qs = CustomerCardModel.get_queryset(request).filter(
            pk__in=normalized_ids,
            org_admin_id=contract.organization_id,
            is_active=True,
        )
        found_ids = {str(each) for each in customer_cards_qs.values_list('pk', flat=True)}
        missing_ids = [each for each in normalized_ids if each not in found_ids]
        if missing_ids:
            raise drf_exceptions.ValidationError({
                'customer_cards': f'Cards are unavailable for this contract organization: {", ".join(missing_ids)}'
            })

        with transaction.atomic():
            deactivated_count = models.CustomerContractServicedCardModel.objects.filter(
                customer_contract=contract,
                customer_card_id__in=found_ids,
                is_active=True,
            ).update(
                is_active=False,
                deleted_at=timezone.now(),
            )

        return Response({'deactivated': deactivated_count}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='for_interest')
    def for_interest(self, request, *args, **kwargs):
        # CRM: форма заказа/договора открывается из интереса и должна знать,
        # какие договоры уже связаны с этим интересом или его клиентом.
        interest = self._get_interest(request)
        filters = Q(subject_items__source_interest=interest)
        if interest.customer_card_id:
            filters |= Q(customer_card=interest.customer_card)
            filters |= Q(serviced_cards_relations__customer_card=interest.customer_card)
        contracts = self.get_queryset().filter(filters).distinct().order_by('-updated_at', '-created_at')
        return Response(self._serialize_interest_contract_context(request, interest, contracts))

    @action(methods=('post',), detail=False, url_path='create_from_interest')
    def create_from_interest(self, request, *args, **kwargs):
        # CRM: договор создается не с интересом, а с клиентом из интереса.
        # Потребности интереса переносятся в предмет договора.
        interest = self._get_interest(request)
        if not interest.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете оформить договор из этого интереса.')
        if not interest.customer_card_id:
            raise drf_exceptions.ValidationError({
                'customer_card': 'Сначала укажите клиента в интересе, потом оформляйте договор.'
            })
        if not interest.organization_id:
            raise drf_exceptions.ValidationError({'organization': 'У интереса не указана организация.'})

        needs = self._get_interest_needs(request, interest)
        raw_amount = request.data.get('amount')
        try:
            amount = Decimal(str(raw_amount).replace(',', '.')) if raw_amount not in (None, '') else Decimal('0')
        except Exception:
            amount = Decimal('0')
        if amount <= 0:
            amount = self._estimate_needs_amount(needs)
        number = request.data.get('number') or f'CRM-{getattr(interest, "counter", "") or str(interest.pk)[:8]}'

        contract_payload = {
            'number': number,
            'organization': str(interest.organization_id),
            'customer_card': str(interest.customer_card_id),
            'contract_date': request.data.get('contract_date') or timezone.now().date(),
            'date_start': request.data.get('date_start') or timezone.now().date(),
            'date_end': request.data.get('date_end'),
            'amount': amount,
            'hours_plan': request.data.get('hours_plan') or 0,
            'is_signed': bool(request.data.get('is_signed', False)),
            'is_exists': bool(request.data.get('is_exists', True)),
        }
        if request.data.get('status'):
            contract_payload['status'] = request.data.get('status')

        with transaction.atomic():
            serializer = serializers.CustomerContractCreateSerializer(
                data=contract_payload,
                context={'request': request, 'view': self},
            )
            serializer.is_valid(raise_exception=True)
            contract = serializer.save()
            subjects = self._copy_needs_to_contract(contract, interest, needs, replace=False)
            subject_amount = sum((subject.amount or Decimal('0')) for subject in subjects).quantize(Decimal('0.01'))
            if subject_amount and (not contract.amount or contract.amount <= 0):
                contract.amount = subject_amount
                contract.save(update_fields=('amount', 'updated_at'))

        return Response(
            serializers.CustomerContractDetailSerializer(
                contract,
                context={'request': request, 'view': self},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=('post',), detail=True, url_path='subject/from_interest')
    def subject_from_interest(self, request, *args, **kwargs):
        # CRM: позволяет дозаполнить или заменить предмет существующего договора
        # потребностями выбранного интереса.
        contract = self.get_object()
        if not contract.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете изменять предмет этого договора.')
        interest = self._get_interest(request)
        needs = self._get_interest_needs(request, interest)
        replace = bool(request.data.get('replace', False))
        with transaction.atomic():
            self._copy_needs_to_contract(contract, interest, needs, replace=replace)
        return Response(serializers.CustomerContractDetailSerializer(
            contract,
            context={'request': request, 'view': self},
        ).data)


class CustomerContractAnalyticsKeysAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        customer_card_id = request.query_params.get('customer_card')
        if not customer_card_id:
            raise drf_exceptions.ValidationError({'customer_card': 'This query param is required.'})

        try:
            customer_card_uuid = uuid.UUID(str(customer_card_id))
        except (ValueError, TypeError):
            raise drf_exceptions.ValidationError({'customer_card': 'Invalid customer_card'})

        has_access = CustomerCardModel.get_queryset(request).filter(pk=customer_card_uuid).exists()
        if not has_access:
            raise drf_exceptions.PermissionDenied('No access to selected customer_card')

        contract_id = request.query_params.get('contract')
        contract_uuid = None
        if contract_id:
            try:
                contract_uuid = uuid.UUID(str(contract_id))
            except (ValueError, TypeError):
                raise drf_exceptions.ValidationError({'contract': 'Invalid contract'})

        project_id = request.query_params.get('project')
        project_uuid = None
        if project_id:
            try:
                project_uuid = uuid.UUID(str(project_id))
            except (ValueError, TypeError):
                raise drf_exceptions.ValidationError({'project': 'Invalid project'})

        queryset = models.CustomerContractProjectModel.get_select_queryset(request).filter(
            customer_contract__serviced_cards_relations__customer_card_id=customer_card_uuid,
            customer_contract__serviced_cards_relations__is_active=True,
        ).distinct()
        if contract_uuid:
            queryset = queryset.filter(customer_contract_id=contract_uuid)
        if project_uuid:
            queryset = queryset.filter(project_id=project_uuid)
        s_data = SelectListSerializer(queryset, many=True).data
        return Response({'filteredSelectList': s_data}, status=status.HTTP_200_OK)


class CustomerContractByProjectAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def _build_string_view(self, contract):
        return contract.get_display_name()

    def get(self, request, *args, **kwargs):
        project_id = request.query_params.get('project')
        if not project_id:
            raise drf_exceptions.ValidationError({'project': 'This query param is required.'})

        try:
            project_uuid = uuid.UUID(str(project_id))
        except (ValueError, TypeError):
            raise drf_exceptions.ValidationError({'project': 'Invalid project'})

        queryset = models.CustomerContractModel.get_queryset(request).filter(
            projects__id=project_uuid
        ).distinct()

        search_text = (request.query_params.get('search') or '').strip()
        if search_text:
            queryset = queryset.filter(
                Q(number__icontains=search_text) |
                Q(external_customer__name__icontains=search_text) |
                Q(external_customer__full_name__icontains=search_text)
            )

        data = [
            {
                'id': str(contract.pk),
                'string_view': self._build_string_view(contract),
            }
            for contract in queryset
        ]
        return Response({'filteredSelectList': data}, status=status.HTTP_200_OK)

