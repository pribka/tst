from rest_framework import serializers
from django.db.models import Count

from .models import GoodsOrderModel
from .serializers import GoodsOrderModelListSerializer
from help_desk.models import CustomerCardModel, HelpDeskTicketModel
from help_desk.serializers import HelpDeskTicketShortSerializer
from bpms.meetings.models import PlannedMeetingModel
from bpms.meetings.serializers import PlannedMeetingListSerializer
from bpms.tasks.models import TaskModel
from bpms.tasks.serializers import OptimizedListTaskSerializer
from users.models import ProfileModel
from users.serializers import CachedAppUserPreviewSerializer

from . import models


class DealStageSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.DealStageModel
        fields = ('id', 'name', 'code', 'color', 'sort', 'is_final', 'is_success')

    def get_name(self, instance):
        return (
            getattr(instance, 'name', None)
            or getattr(instance, 'name_ru', None)
            or getattr(instance, 'name_kk', None)
            or getattr(instance, 'name_en', None)
            or instance.__dict__.get('name')
            or instance.code
        )


class DealListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    stage = DealStageSerializer(read_only=True)
    responsible = serializers.SerializerMethodField()
    customer_card = serializers.SerializerMethodField()
    customer_contract = serializers.SerializerMethodField()
    customer_contracts_count = serializers.SerializerMethodField()
    margin = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    meetings_count = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()

    class Meta:
        model = models.DealModel
        fields = (
            'id',
            'name',
            'stage',
            'responsible',
            'customer_card',
            'customer_contract',
            'customer_contracts_count',
            'expected_amount',
            'internal_budget',
            'margin',
            'probability',
            'planned_close_date',
            'updated_at',
            'tasks_count',
            'files_count',
            'meetings_count',
            'orders_count',
            'frontend_route',
        )

    def _request(self):
        return self.context.get('request')

    def get_name(self, instance):
        if instance.name and str(instance.name).strip():
            return instance.name.strip()
        if instance.customer_card_id:
            customer_card_name = getattr(instance.customer_card, 'full_name', None) or getattr(instance.customer_card, 'name', None)
            if customer_card_name:
                return f'Сделка: {customer_card_name}'
        if instance.source_ticket_id:
            ticket_name = getattr(instance.source_ticket, 'name', None)
            if ticket_name:
                return f'Сделка: {ticket_name}'
        return f'Сделка {instance.pk}'

    def get_responsible(self, instance):
        if not instance.responsible_id:
            return None
        return CachedAppUserPreviewSerializer(instance.responsible_id, context=self.context).data

    def get_customer_card(self, instance):
        if not instance.customer_card_id:
            return None
        return {
            'id': instance.customer_card.pk,
            'name': instance.customer_card.name,
            'full_name': instance.customer_card.full_name,
        }

    def _get_primary_customer_contract(self, instance):
        contracts = getattr(instance, '_prefetched_objects_cache', {}).get('customer_contracts')
        if contracts is None:
            contracts = list(instance.customer_contracts.filter(is_active=True).select_related(
                'status',
                'organization',
                'customer_card',
            ).order_by('-contract_date', '-created_at'))
        if not contracts:
            return None
        return contracts[0]

    def get_customer_contract(self, instance):
        contract = self._get_primary_customer_contract(instance)
        if not contract:
            return None
        status = contract.status
        status_name = (
            getattr(status, 'name', None)
            or getattr(status, 'name_ru', None)
            or getattr(status, 'name_kk', None)
            or getattr(status, 'name_en', None)
            or getattr(status, 'code', None)
        ) if status else None
        customer_card_name = (
            getattr(contract.customer_card, 'full_name', None)
            or getattr(contract.customer_card, 'name', None)
        ) if contract.customer_card_id else None
        return {
            'id': contract.pk,
            'number': contract.number,
            'contract_date': contract.contract_date,
            'date_start': contract.date_start,
            'date_end': contract.date_end,
            'amount': contract.amount,
            'hours_plan': contract.hours_plan,
            'hours_fact': contract.hours_fact,
            'is_signed': contract.is_signed,
            'is_exists': contract.is_exists,
            'status': {
                'id': status.pk,
                'code': status.code,
                'name': status_name,
            } if status else None,
            'organization': {
                'id': contract.organization_id,
                'name': getattr(contract.organization, 'name', None),
            } if contract.organization_id else None,
            'customer_card': {
                'id': contract.customer_card_id,
                'name': getattr(contract.customer_card, 'name', None),
                'full_name': customer_card_name,
            } if contract.customer_card_id else None,
        }

    def get_customer_contracts_count(self, instance):
        contracts = getattr(instance, '_prefetched_objects_cache', {}).get('customer_contracts')
        if contracts is not None:
            return len([contract for contract in contracts if contract.is_active])
        return instance.customer_contracts.filter(is_active=True).count()

    def get_margin(self, instance):
        expected_amount = instance.expected_amount or 0
        internal_budget = instance.internal_budget or 0
        return expected_amount - internal_budget

    def get_tasks_count(self, instance):
        request = self._request()
        if not request:
            return 0
        return TaskModel.get_queryset(request).filter(reason=str(instance.pk)).count()

    def get_files_count(self, instance):
        return instance.attachments.filter(is_active=True).count()

    def get_meetings_count(self, instance):
        request = self._request()
        if not request:
            return 0
        return PlannedMeetingModel.get_queryset(request).filter(related_object_id=instance.pk).count()

    def get_orders_count(self, instance):
        request = self._request()
        if not request:
            return 0
        return GoodsOrderModel.get_queryset(request).filter(reason_id=instance.pk).count()


class DealDetailSerializer(DealListSerializer):
    author = serializers.SerializerMethodField()
    source_ticket = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    observers = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    meetings = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()

    class Meta(DealListSerializer.Meta):
        fields = DealListSerializer.Meta.fields + (
            'author',
            'description',
            'source_ticket',
            'members',
            'observers',
            'tasks',
            'meetings',
            'orders',
            'created_at',
        )

    def get_author(self, instance):
        if not instance.author_id:
            return None
        return CachedAppUserPreviewSerializer(instance.author_id, context=self.context).data

    def get_source_ticket(self, instance):
        if not instance.source_ticket_id:
            return None
        return HelpDeskTicketShortSerializer(instance.source_ticket, context=self.context).data

    def get_members(self, instance):
        return CachedAppUserPreviewSerializer(instance.members.all(), many=True, context=self.context).data

    def get_observers(self, instance):
        return CachedAppUserPreviewSerializer(instance.observers.all(), many=True, context=self.context).data

    def get_tasks(self, instance):
        request = self._request()
        if not request:
            return []
        queryset = TaskModel.get_queryset(request).filter(reason=str(instance.pk)).order_by('-updated_at', '-created_at')[:30]
        return OptimizedListTaskSerializer(queryset, many=True, context=self.context).data

    def get_meetings(self, instance):
        request = self._request()
        if not request:
            return []
        queryset = PlannedMeetingModel.get_queryset(request).filter(
            related_object_id=instance.pk
        ).annotate(
            members_count=Count('members', distinct=True)
        ).order_by('-date_begin', '-created_at')[:30]
        return PlannedMeetingListSerializer(queryset, many=True, context=self.context).data

    def get_orders(self, instance):
        request = self._request()
        if not request:
            return []
        queryset = GoodsOrderModel.get_queryset(request).filter(reason_id=instance.pk).order_by('-created_at')[:30]
        return GoodsOrderModelListSerializer(queryset, many=True, context=self.context).data


class DealCreateUpdateSerializer(serializers.ModelSerializer):
    responsible = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )
    stage = serializers.PrimaryKeyRelatedField(
        queryset=models.DealStageModel.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )
    customer_card = serializers.PrimaryKeyRelatedField(
        queryset=CustomerCardModel.objects.none(),
        allow_null=True,
        required=False,
    )
    source_ticket = serializers.PrimaryKeyRelatedField(
        queryset=HelpDeskTicketModel.objects.none(),
        allow_null=True,
        required=False,
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProfileModel.objects.filter(is_active=True),
        required=False,
    )
    observers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProfileModel.objects.filter(is_active=True),
        required=False,
    )

    class Meta:
        model = models.DealModel
        fields = (
            'id',
            'name',
            'description',
            'stage',
            'responsible',
            'customer_card',
            'source_ticket',
            'expected_amount',
            'internal_budget',
            'probability',
            'planned_close_date',
            'members',
            'observers',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            self.fields['customer_card'].queryset = CustomerCardModel.get_queryset(request)
            self.fields['source_ticket'].queryset = HelpDeskTicketModel.get_queryset(request)

    def validate_probability(self, value):
        if value is None:
            return 0
        if value < 0 or value > 100:
            raise serializers.ValidationError('Вероятность должна быть в диапазоне от 0 до 100.')
        return value

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Укажите название сделки.')
        return value

    def _default_stage(self):
        return models.DealStageModel.objects.filter(is_active=True).order_by('sort', 'created_at').first()

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        observers = validated_data.pop('observers', [])
        request = self.context.get('request')
        if request and not validated_data.get('responsible'):
            validated_data['responsible'] = request.user.profile
        if not validated_data.get('stage'):
            validated_data['stage'] = self._default_stage()
        instance = super().create(validated_data)
        if members:
            instance.members.set(members)
        if observers:
            instance.observers.set(observers)
        return instance

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        observers = validated_data.pop('observers', None)
        instance = super().update(instance, validated_data)
        if members is not None:
            instance.members.set(members)
        if observers is not None:
            instance.observers.set(observers)
        return instance

    def to_representation(self, instance):
        return DealDetailSerializer(instance, context=self.context).data
