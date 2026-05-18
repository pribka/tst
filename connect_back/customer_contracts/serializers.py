from decimal import Decimal

from django.db import transaction
from django.db import IntegrityError
from django.db.models import Sum, F, DecimalField

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from common.serializers import CachedBaseModelSerializer
from common.catalogs.models import ContractorModel, ExternalCustomerModel, NomenclatureModel
from common.catalogs.serializers import ContractorModelShortSerializer, AppNomenclatureSerializer, \
    MeasureUnitListSerializer
from common.current_profile.middleware import get_current_authenticated_profile

from contractor_permissions.utils import check_contractor_permission

from bpms.workgroups.models import WorkgroupModel
from bpms.workgroups.serializers import WorkgroupNameLogoSerializer
from help_desk.models import CustomerCardModel
from help_desk.serializers import CustomerCardModelShortSerializer

from users.utils import get_ancestor_departments_related_organizations

from . import models


class CustomerContractShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerContractModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['string_view'] = instance.get_display_name()
        return data


class CustomerContractStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerContractStatusModel
        fields = (
            'id',
            'name',
            'code',
        )


class ExternalCustomerShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalCustomerModel
        fields = (
            'id',
            'name',
            'full_name',
            # 'external_id',
            'inn',
        )


class CustomerContractSubjectListSerializer(serializers.ModelSerializer):
    """Предмет договора с прогрессом по заказам и отгрузкам."""
    goods = AppNomenclatureSerializer()
    measure_unit = MeasureUnitListSerializer()
    source_interest = serializers.SerializerMethodField()
    source_need = serializers.UUIDField(source='source_need_id', read_only=True)
    ordered_quantity = serializers.SerializerMethodField()
    delivered_quantity = serializers.SerializerMethodField()
    ordered_amount = serializers.SerializerMethodField()
    delivered_amount = serializers.SerializerMethodField()

    class Meta:
        model = models.CustomerContractSubjectModel
        fields = (
            'id',
            'customer_contract',
            'source_interest',
            'source_need',
            'goods',
            'name',
            'name_short',
            'article_number',
            'quantity',
            'price',
            'amount',
            'measure_unit',
            'comment',
            'ordered_quantity',
            'delivered_quantity',
            'ordered_amount',
            'delivered_amount',
            'created_at',
            'updated_at',
        )

    def _order_rows(self, instance):
        # CRM: прогресс считаем по заказам этого же договора и той же позиции
        # номенклатуры. Так видно, сколько уже заказано/отгружено по предмету.
        if not instance.customer_contract_id or not instance.goods_id:
            from crm.models import TPGoodsOrderModel
            return TPGoodsOrderModel.objects.none()
        from crm.models import TPGoodsOrderModel
        return TPGoodsOrderModel.objects.filter(
            is_active=True,
            owner__is_active=True,
            owner__customer_contract_id=instance.customer_contract_id,
            goods_id=instance.goods_id,
        )

    def _order_aggregate(self, instance):
        cache_name = '_crm_order_aggregate'
        if hasattr(instance, cache_name):
            return getattr(instance, cache_name)
        aggregate = self._order_rows(instance).aggregate(
            ordered_quantity=Sum('quantity'),
            delivered_quantity=Sum('quantity_success'),
            ordered_amount=Sum('amount'),
            delivered_amount=Sum(
                F('quantity_success') * F('price'),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        )
        setattr(instance, cache_name, aggregate)
        return aggregate

    def _format_decimal(self, value, max_digits=15, decimal_places=2):
        if value is None:
            value = Decimal('0')
        field = serializers.DecimalField(max_digits=max_digits, decimal_places=decimal_places)
        return field.to_representation(value)

    def get_source_interest(self, instance):
        if not instance.source_interest_id:
            return None
        interest = instance.source_interest
        return {
            'id': str(interest.pk),
            'counter': getattr(interest, 'counter', None),
            'name': getattr(interest, 'name', '') or str(interest),
        }

    def get_ordered_quantity(self, instance):
        return self._format_decimal(self._order_aggregate(instance).get('ordered_quantity'), decimal_places=3)

    def get_delivered_quantity(self, instance):
        return self._format_decimal(self._order_aggregate(instance).get('delivered_quantity'), decimal_places=3)

    def get_ordered_amount(self, instance):
        return self._format_decimal(self._order_aggregate(instance).get('ordered_amount'))

    def get_delivered_amount(self, instance):
        return self._format_decimal(self._order_aggregate(instance).get('delivered_amount'))


class CustomerContractSubjectCreateSerializer(serializers.ModelSerializer):
    """Создание строки предмета договора вручную или из потребности интереса."""
    customer_contract = serializers.PrimaryKeyRelatedField(
        queryset=models.CustomerContractModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )
    goods = serializers.PrimaryKeyRelatedField(
        queryset=NomenclatureModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.CustomerContractSubjectModel
        fields = (
            'id',
            'customer_contract',
            'source_interest',
            'source_need',
            'goods',
            'name',
            'quantity',
            'price',
            'comment',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        contract = attrs.get('customer_contract')
        if request and contract and not contract.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете изменять предмет этого договора.')
        interest = attrs.get('source_interest')
        if interest and interest.task_type_id != 'interest':
            raise drf_exceptions.ValidationError({'source_interest': 'Можно использовать только интерес.'})
        source_need = attrs.get('source_need')
        if source_need and interest and source_need.task_id != interest.pk:
            # CRM: нельзя перенести в договор потребность от другого интереса.
            raise drf_exceptions.ValidationError({'source_need': 'Потребность не относится к выбранному интересу.'})
        return attrs

    def to_representation(self, instance):
        return CustomerContractSubjectListSerializer(instance, context=self.context).data


class CustomerContractSubjectUpdateSerializer(serializers.ModelSerializer):
    """Редактирование согласованного предмета договора."""
    goods = serializers.PrimaryKeyRelatedField(
        queryset=NomenclatureModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.CustomerContractSubjectModel
        fields = (
            'id',
            'goods',
            'name',
            'quantity',
            'price',
            'comment',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        if request and not self.instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете изменять предмет этого договора.')
        return attrs

    def to_representation(self, instance):
        return CustomerContractSubjectListSerializer(instance, context=self.context).data


class CustomerContractListSerializer(serializers.ModelSerializer):
    status = CachedBaseModelSerializer(source='status_id', serializer_class=CustomerContractStatusListSerializer,)
    organization = ContractorModelShortSerializer()
    customer_card = CustomerCardModelShortSerializer()
    external_customer = ExternalCustomerShortSerializer()
    deal = serializers.IntegerField(source='deal_id', read_only=True)

    class Meta:
        model = models.CustomerContractModel
        fields = (
            'id',
            'number',
            'status',
            'organization',
            'customer_card',
            'external_customer',
            'deal',
            'contract_date',
            'date_start',
            'date_end',
            'amount',
            'hours_plan',
            'hours_fact',
            'is_signed',
            'is_exists',
            'created_at',
            'updated_at',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.external_customer and instance.customer_card:
            data['external_customer'] = data['customer_card']
        return data


class CustomerContractDetailSerializer(serializers.ModelSerializer):
    status = CachedBaseModelSerializer(source='status_id', serializer_class=CustomerContractStatusListSerializer, )
    organization = ContractorModelShortSerializer()
    customer_card = CustomerCardModelShortSerializer()
    external_customer = ExternalCustomerShortSerializer()
    projects = WorkgroupNameLogoSerializer(many=True)
    deal = serializers.IntegerField(source='deal_id', read_only=True)
    subject_items = serializers.SerializerMethodField()
    crm_orders_summary = serializers.SerializerMethodField()
    customer_cards = serializers.SerializerMethodField()

    class Meta:
        model = models.CustomerContractModel
        fields = (
            'id',
            'number',
            'status',
            'organization',
            'customer_card',
            'customer_cards',
            'external_customer',
            'deal',
            'projects',
            'subject_items',
            'crm_orders_summary',
            'contract_date',
            'date_start',
            'date_end',
            'amount',
            'hours_plan',
            'hours_fact',
            'is_signed',
            'is_exists',
            'created_at',
            'updated_at',
        )

    def _format_decimal(self, value, max_digits=15, decimal_places=2):
        if value is None:
            value = Decimal('0')
        field = serializers.DecimalField(max_digits=max_digits, decimal_places=decimal_places)
        return field.to_representation(value)

    def get_subject_items(self, instance):
        # CRM: карточка договора сразу отдает предмет договора, чтобы фронт мог
        # показать цепочку "интерес -> потребности -> договор -> заказ".
        qs = instance.subject_items.filter(is_active=True).select_related(
            'source_interest',
            'source_need',
            'goods',
            'measure_unit',
            'base_measure_unit',
        ).order_by('created_at')
        return CustomerContractSubjectListSerializer(qs, many=True, context=self.context).data

    def get_customer_cards(self, instance):
        # CRM: это список допустимых клиентов договора. Он нужен форме заказа
        # для выбора получателя отгрузки, но не подменяет order.customer_card.
        request = self.context.get('request')
        if request:
            qs = CustomerCardModel.get_queryset(request).filter(
                serviced_contracts_relations__customer_contract=instance,
                serviced_contracts_relations__is_active=True,
            ).distinct().order_by('name', '-created_at')
        else:
            qs = CustomerCardModel.objects.filter(
                serviced_contracts_relations__customer_contract=instance,
                serviced_contracts_relations__is_active=True,
                is_active=True,
            ).distinct().order_by('name', '-created_at')
        return CustomerCardModelShortSerializer(qs, many=True, context=self.context).data

    def get_crm_orders_summary(self, instance):
        # CRM: сводка по заказам договора нужна для контроля лимита:
        # сколько согласовано, заказано и фактически отгружено.
        from crm.models import GoodsOrderModel, TPGoodsOrderModel

        orders = GoodsOrderModel.objects.filter(is_active=True, customer_contract=instance)
        order_rows = TPGoodsOrderModel.objects.filter(is_active=True, owner__in=orders)
        subject_amount = instance.subject_items.filter(is_active=True).aggregate(value=Sum('amount'))['value']
        rows_aggregate = order_rows.aggregate(
            ordered_quantity=Sum('quantity'),
            delivered_quantity=Sum('quantity_success'),
            ordered_amount=Sum('amount'),
            delivered_amount=Sum(
                F('quantity_success') * F('price'),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        )
        orders_aggregate = orders.aggregate(value=Sum('amount'))
        return {
            'contract_amount': self._format_decimal(instance.amount),
            'subject_amount': self._format_decimal(subject_amount),
            'order_count': orders.count(),
            'ordered_quantity': self._format_decimal(rows_aggregate.get('ordered_quantity'), decimal_places=3),
            'delivered_quantity': self._format_decimal(rows_aggregate.get('delivered_quantity'), decimal_places=3),
            'ordered_amount': self._format_decimal(
                rows_aggregate.get('ordered_amount') or orders_aggregate.get('value')
            ),
            'delivered_amount': self._format_decimal(rows_aggregate.get('delivered_amount')),
        }


class CustomerContractUpdateSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField(
        queryset=models.CustomerContractStatusModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    # organization = serializers.PrimaryKeyRelatedField(
    #     queryset=ContractorModel.objects.filter(is_active=True),
    #     required=False,
    #     allow_null=True,
    # )
    # customer_card = serializers.PrimaryKeyRelatedField(
    #     queryset=CustomerCardModel.objects.none(),
    #     required=False,
    #     allow_null=True,
    # )
    customer_card = serializers.PrimaryKeyRelatedField(
        queryset=CustomerCardModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )
    projects = serializers.PrimaryKeyRelatedField(
        queryset=WorkgroupModel.objects.filter(is_active=True),
        many=True,
        required=False,
    )

    class Meta:
        model = models.CustomerContractModel
        fields = (
            'id',
            'number',
            'status',
            # 'organization',
            'customer_card',
            'projects',
            'contract_date',
            'date_start',
            'date_end',
            'amount',
            'hours_plan',
            # 'hours_fact',
            'is_signed',
            'is_exists',
        )

    def validate_customer_card(self, customer_card):
        instance = self.instance
        old_customer_card = instance.customer_card
        if old_customer_card and not old_customer_card == customer_card:
            if not customer_card.org_admin == instance.organization:
                raise drf_exceptions.ValidationError('invalid customer_card')
        return customer_card

    def update(self, instance, validated_data):
        with transaction.atomic():
            old_customer_card = instance.customer_card
            instance = super().update(instance, validated_data)
            new_customer_card = instance.customer_card
            if new_customer_card and not old_customer_card == new_customer_card:
                with transaction.atomic():
                    try:
                        models.CustomerContractServicedCardModel.objects.create(
                            customer_contract=instance,
                            customer_card=instance.customer_card
                        )
                    except IntegrityError:
                        pass
            instance.recalculate_hours_fact()
        return instance


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     request = self.context.get('request')
    #     if request is not None:
    #         self.fields['customer_card'].queryset = CustomerCardModel.get_queryset(request)


class CustomerContractCreateSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField(
        queryset=models.CustomerContractStatusModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )

    # external_customer = serializers.PrimaryKeyRelatedField(
    #     queryset=ExternalCustomerModel.objects.filter(is_active=True),
    #     required=False,
    #     allow_null=False
    # )

    customer_card = serializers.PrimaryKeyRelatedField(
        queryset=CustomerCardModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )

    projects = serializers.PrimaryKeyRelatedField(
        queryset=WorkgroupModel.objects.filter(is_active=True),
        many=True,
        required=False,
    )

    class Meta:
        model = models.CustomerContractModel
        fields = (
            'id',
            'number',
            'status',
            'organization',
            # 'external_customer',
            # 'legal_entity',
            'customer_card',
            'projects',
            'contract_date',
            'date_start',
            'date_end',
            'amount',
            'hours_plan',
            'is_signed',
            'is_exists',
        )

    def to_internal_value(self, data):
        if not data.get('hours_plan'):
            data['hours_plan'] = 0
        return super().to_internal_value(data)

    def validate(self, attrs):
        organization = attrs.get('organization')
        if not organization:
            raise drf_exceptions.ValidationError('organization required.')
        user = get_current_authenticated_profile()
        if user:
            check_contractor_permission(user.pk, organization.pk, ('admin', 'create_workgroup'), None)
        customer_card = attrs.get('customer_card',)
        if not customer_card:
            raise drf_exceptions.ValidationError('customer_card required')
        if not customer_card.org_admin == organization:
            raise drf_exceptions.ValidationError('invalid customer_card')
        # external_customer = attrs.get('external_customer')
        # if external_customer:
        #     ancestors = get_ancestor_departments_related_organizations((external_customer.org_admin_id,), include_self=True)
        #     if organization.pk not in ancestors:
        #         raise drf_exceptions.ValidationError(f'Контрагент не входит в контур организации {organization.name}')

        # legal_entity = attrs.get('legal_entity')
        # if legal_entity:
        #     ancestors = get_ancestor_departments_related_organizations((legal_entity.contractor_id,), include_self=True)
        #     if organization.pk not in ancestors:
        #         raise drf_exceptions.ValidationError(
        #             f'Юридическое лицо не входит в контур организации {organization.name}'
        #         )
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            if instance.customer_card:
                models.CustomerContractServicedCardModel.objects.create(
                    customer_contract=instance,
                    customer_card=instance.customer_card
                )
        return instance
