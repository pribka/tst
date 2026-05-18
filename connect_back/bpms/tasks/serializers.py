import json
import hashlib
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP

from collections import Counter
from randomcolor import RandomColor

from drf_haystack.serializers import HaystackSerializer

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q
from django.db.models import Count, Sum, F, Value, BooleanField, Avg
from django.utils import timezone
from django.utils.translation import get_language

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied

from django_q.tasks import async_task

from crm.models import TPGoodsOrderModel, GoodsOrderModel
from crm.serializers import GoodsOrderModelListSerializer

from common.models import File
from common.serializers import BaseCatalogListSerializer, BaseCatalogRetrieveSerializer, CachedBaseModelSerializer
from common.utils import get_serialized_attachments, is_mobile_app

from common.catalogs.serializers import (AppCurrencySerializer,
                                          MeasureUnitListSerializer,
                                          ContractorModelShortSerializer,
                                          InterestPotentialContractorModelSerializer,
                                          ContractorModelByIdSerializer,
                                          AppNomenclatureSerializer)
from common.catalogs.models import (get_default_currency_object,
                                    DeliveryPointModel,
                                    PotentialContractorModel,
                                    ContractorModel)

from common.current_profile.middleware import get_current_authenticated_profile

from customer_contracts.serializers import CustomerContractShortSerializer
from customer_contracts.models import CustomerContractServicedCardModel
from help_desk.models import CustomerCardModel
from help_desk.serializers import CustomerCardModelShortSerializer

from bpms.okr.models import KeyResultsModel

from users.models import ProfileModel
from users.utils import get_tree_departments_related_organizations

from tags.serializers import TagModelListSerializer

from bpms.workgroups.serializers import WorkgroupNameSerializer, WorkgroupNameLogoSerializer
from bpms.bpms_common.serializers import AppUserSerializer
from bpms.voting.utils import get_vote_info

from users.serializers import CachedAppUserSerializer, CachedAppUserPreviewSerializer
from bpms.event_calendar.serializers import EventCalendarModelListSerializer

from bpms.workgroups.models import WorkgroupModel
from bpms.favorites.utils import get_in_favorites

from app_info.models import AppInfo

from crm.models import GoodsOrderModel

from . import utils
from . import notifications
from . import search_indexes
from . import models
from django.core.cache import cache
from bpms.workload import models as wl_models


def validate_task_customer_card(contract, customer_card):
    if not customer_card:
        return customer_card
    if not contract:
        raise ValidationError({'customer_card': 'Клиент доступен только вместе с контрактом.'})

    relation_exists = CustomerContractServicedCardModel.objects.filter(
        customer_contract=contract,
        customer_card=customer_card,
        is_active=True,
    ).exists()
    if not relation_exists:
        raise ValidationError({'customer_card': 'Выбранный клиент не привязан к указанному контракту.'})
    return customer_card

from bkz3.settings import DID_SALT

class LeadSourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LeadSourceModel
        fields = (
            'id',
            'name',
            'color',
        )


class RejectionReasonModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RejectionReasonModel
        fields = (
            'id',
            'name',
            'color',
        )


class TaskSprintShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
            'name',
            'author',
        )


class AddDeliveryPointSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=DeliveryPointModel.objects.filter(
        is_active=True,), required=True)
    sort = serializers.IntegerField(required=True)


class AddOrderSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=GoodsOrderModel.objects.filter(
            is_active=True,
            task_delivery_point__isnull=True,
            start_task_delivery_point__isnull=True,
        ),
        required=True
    )
    delivery_point = AddDeliveryPointSerializer(required=True)
    start_delivery_point = AddDeliveryPointSerializer(required=True)


class TaskPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskPointModel
        fields = [
            'id',
            'lat',
            'lon',
            'name',
            'address',
        ]


class CreateTaskSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    priority = serializers.IntegerField(min_value=0, default=2, max_value=4, allow_null=True)
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    cooperators = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=models.TaskModel.objects.filter(is_active=True)
    )
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    orders = AddOrderSerializer(required=False, many=True)
    task_points = TaskPointSerializer(required=False, many=True)
    p_contractor_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    p_contractor_company = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    email = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    customer_card = serializers.PrimaryKeyRelatedField(
        queryset=CustomerCardModel.objects.none(),
        required=False,
        allow_null=True,
    )
    secret = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True,
        default=None,
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    pinned = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'parent',
            'project',
            'contract',
            'customer_card',
            'workgroup',
            'operator',
            'owner',
            'visors',
            'cooperators',
            'prerequisites',
            'attachments',
            'date_start_plan',
            'dead_line',
            'name',
            'result',
            'description',
            'priority',
            'funds',
            'execution_time_plan',
            'is_indefinite',
            'is_auction',
            'reason',
            'with_chat',
            'linked_chat',
            'task_type',
            'tmp_phone',
            'orders',
            'task_points',
            'lead_source',
            'contractor',
            'p_contractor_name',
            'p_contractor_company',
            'phone',
            'email',
            'is_need_to_make_event',
            'organization',
            'secret',
            'metadata',
            'is_sign_task',
            'pinned',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if request and getattr(user, 'is_authenticated', False):
            self.fields['customer_card'].queryset = CustomerCardModel.get_queryset(request)

    def validate(self, data):
        contractor = data.get('contractor', None)
        p_contractor_name = data.get('p_contractor_name', None)
        task_type = data.get('task_type', None)
        organization = data.get('organization')
        contract = data.get('contract')
        customer_card = data.get('customer_card')
        if organization:
            has_secret = False
            if 'secret' in self.initial_data:
                secret = self.initial_data.pop('secret', '')
                if secret == hashlib.md5((json.dumps(self.initial_data) + DID_SALT).encode('utf-8')).hexdigest():
                    self.initial_data['secret'] = secret
                    has_secret = True
            if not has_secret:
                user = get_current_authenticated_profile()
                dead_line = data.get('dead_line')
                if not dead_line:
                    raise ValidationError({"message": "Крайний срок обязателен."})
                if organization.pk not in get_tree_departments_related_organizations(user.my_organizations):
                    project = data.get('project', None)
                    if project and project.organization == organization:
                        is_member_project = project.workgroupmembersmodel_set.filter(
                            is_active=True,
                            member=user,
                            membership_request_status__code='APPROVED',
                        ).exists()
                        if not is_member_project:
                            raise ValidationError({"message": "Вы не можете указывать эту организацию: нет доступа."})
                    else:
                        raise ValidationError({"message": "Вы не можете указывать эту организацию: нет доступа."})

        if task_type.code == 'interest':
            if not customer_card and (bool(contractor) is bool(p_contractor_name)):
                raise ValidationError(
                    'Должно быть заполнено одно из полей - '
                    'карточка клиента, старый клиент или потенциальный клиент.'
                )
        # Устанавливаем организацию по умолчанию, если она не передана
        if not organization:
            request = self.context.get('request')
            profile = request.user.profile
            data['organization'] = profile.current_contractor
        if task_type.code != 'interest' or contract:
            validate_task_customer_card(contract, customer_card)
        return data

    def validate_parent(self, data):
        if getattr(data, 'level', 0) >= 3:
            raise ValidationError('Нельзя создать подзадачу для этой задачи.')
        return data

    def valildate_orders(self, data):
        if not data:
            return data
        user = get_current_authenticated_profile()
        if user.can_create_logistic_task:
            return data
        for each in data:
            order = each.get('id')
            logistic_manager = order.logistic_manager
            is_logistic_manager = logistic_manager is not None and user == logistic_manager
            if is_logistic_manager:
                raise PermissionDenied()
        return data

    def create(self, validated_data):
        pinned = validated_data.pop('pinned', False)
        linked_chat = validated_data.pop('linked_chat', None)
        visors = validated_data.pop('visors', None)
        cooperators = validated_data.pop('cooperators', None)
        prerequisites = validated_data.pop('prerequisites', None)
        attachments = validated_data.pop('attachments', None)
        with_chat = validated_data.get('with_chat', False)
        operator = validated_data.get('operator')
        owner = validated_data.get('owner')
        orders = validated_data.pop('orders', None)
        task_points = validated_data.pop('task_points', None)
        user = get_current_authenticated_profile()
        lead_source = validated_data.pop('lead_source', None)
        potential_contractor = None
        contractor = validated_data.pop('contractor', None)
        p_contractor_name = validated_data.pop('p_contractor_name', None)
        p_contractor_company = validated_data.pop('p_contractor_company', None)
        phone = validated_data.pop('phone', None)
        email = validated_data.pop('email', None)
        durations = validated_data.pop('durations', None)
        secret = validated_data.pop('secret', '')
        if secret:
            validated_data['author'] = validated_data['owner']

        with transaction.atomic():
            if validated_data['task_type'].code == 'interest' and p_contractor_name:
                raw_potential_contractor = {
                    'name': p_contractor_name,
                    'company_name': p_contractor_company,
                    'phone': phone,
                    'email': email
                }
                potential_contractor_serializer = InterestPotentialContractorModelSerializer(
                    data=raw_potential_contractor
                )
                potential_contractor_serializer.is_valid(raise_exception=True)
                potential_contractor = potential_contractor_serializer.save()

            if validated_data['task_type'].code == 'interest' and contractor:
                contractor.phone = phone
                contractor.email = email
                contractor.save(update_fields=('phone', 'email'))

            task = models.TaskModel.objects.create(
                color=RandomColor().generate()[0],
                potential_contractor=potential_contractor,
                contractor=contractor,
                lead_source=lead_source,
                **validated_data,
            )
            if task_points:
                for point in task_points:
                    models.TaskPointModel.objects.create(
                        task=task,
                        **point
                    )
            if visors:
                task.visors.set(visors)
            if cooperators:
                task.cooperators.set(cooperators)
            if prerequisites:
                task.prerequisites.set(prerequisites)
            if attachments:
                task.attachments.set(attachments)
            if with_chat:
                members = []
                if isinstance(visors, list):
                    members = members + [each for each in visors]
                if isinstance(cooperators, list):
                    members = members.extend(cooperators)
                if owner:
                    members.append(owner)
                if operator:
                    members.append(operator)
                members.append(task.author)
                members = list(set(members))
                task.create_chat(members, linked_chat)
            if task.task_type_id == 'logistic' and orders:
                for order_dict in orders:
                    order = order_dict.get('id')
                    start_delivery_point = order_dict.get('start_delivery_point')
                    delivery_point = order_dict.get('delivery_point')
                    # Создаем стартовую точку
                    start_task_delivery_point = models.TaskDeliveryPointModel()
                    start_task_delivery_point.task = task
                    start_task_delivery_point.is_start = True
                    start_task_delivery_point.delivery_point = start_delivery_point.get('id')
                    start_task_delivery_point.sort = start_delivery_point.get('sort')
                    start_task_delivery_point.save()
                    # Создаем конечную точку
                    task_delivery_point = models.TaskDeliveryPointModel()
                    task_delivery_point.task = task
                    task_delivery_point.delivery_point = delivery_point.get('id')
                    task_delivery_point.sort = delivery_point.get('sort')
                    task_delivery_point.save()
                    # Привязываем точки к заказу:
                    order.start_task_delivery_point = start_task_delivery_point
                    order.task_delivery_point = task_delivery_point
                    order.operator = task.operator
                    order.save(update_fields=('start_task_delivery_point', 'task_delivery_point', 'operator'))
                    transaction.on_commit(
                        lambda: async_task(notifications.notify_driver_about_start_order, task, order, user)
                    )
                    transaction.on_commit(
                        lambda: async_task(notifications.notify_order_user_about_start_order, task, order, user)
                    )
            if durations is not None and durations['is_distributed']:
                task_dur_id = durations['id']
                task_dur = wl_models.TaskDurationModel.objects.get(
                    id=task_dur_id
                )
                task_dur.task = task
                task_dur.save()
        async_task(utils.create_chat_message_about_task_reason, task)
        async_task(utils.send_socketio_about_new_task, task)
        if not task.operator_id == task.author_id:
            async_task(notifications.notify_about_assign_operator_task, task, task.author)
        if not task.owner_id == task.author_id:
            async_task(notifications.notify_about_assign_owner_task, task, task.author)
        if visors:
            async_task(notifications.notify_about_assign_visor_task, task, task.author)
        if cooperators:
            async_task(notifications.notify_about_assign_cooperator_task, task, task.author)
        if task.project_id or task.workgroup_id:
            async_task(notifications.notify_about_new_workgroup_task, task, task.author)
        if pinned:
            request = self.context.get('request')
            if request:
                user_profile = request.user.profile
                models.TaskPinnedModel.objects.create(
                    user=user_profile,
                    task=task,
                )
                utils.clear_my_day_grouped_cache(user_profile.pk)
        return task

    def to_representation(self, instance):
        instance.children_count = 0
        data = DetailTaskSerializer(instance).data
        return data


class UpdateTaskSerializer(serializers.ModelSerializer):
    priority = serializers.IntegerField(min_value=0, default=2, max_value=4, allow_null=True)
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    cooperators = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=models.TaskModel.objects.filter(is_active=True)
    )
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    task_points = TaskPointSerializer(required=False,
                                      many=True)
    #potential_contractor = InterestPotentialContractorModelSerializer(read_only=True, required=False)
    p_contractor_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    p_contractor_company = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    email = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=None,
    )
    customer_card = serializers.PrimaryKeyRelatedField(
        queryset=CustomerCardModel.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'parent',
            'project',
            'contract',
            'customer_card',
            'workgroup',
            'operator',
            'owner',
            'visors',
            'cooperators',
            'prerequisites',
            'attachments',
            'date_start_plan',
            'dead_line',
            'name',
            'result',
            'description',
            'priority',
            'funds',
            'execution_time_plan',
            'is_indefinite',
            'is_auction',
            'task_points',
            #'potential_contractor',
            'lead_source',
            'contractor',
            'p_contractor_name',
            'p_contractor_company',
            'phone',
            'email',
            'is_need_to_make_event',
            'organization',
            'metadata',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if request and getattr(user, 'is_authenticated', False):
            self.fields['customer_card'].queryset = CustomerCardModel.get_queryset(request)

    def validate_parent(self, data):
        if getattr(data, 'level', 0) >= 3:
            raise ValidationError('Нельзя создать подзадачу для этой задачи.')
        return data

    def validate(self, data):
        if 'dead_line' in data:
            dead_line = data['dead_line']
            if not dead_line:
                raise ValidationError({"message": "Крайний срок обязателен."})
        organization = data.get('organization')
        contract = data.get('contract', self.instance.contract)
        customer_card = data.get('customer_card', self.instance.customer_card)
        if organization:
            old_organization = self.instance.organization
            if not organization == old_organization:
                user = get_current_authenticated_profile()
                if organization.pk not in get_tree_departments_related_organizations(user.my_organizations):
                    project = data.get('project',)
                    if project and project.organization == organization:
                        is_member_project = project.workgroupmembersmodel_set.filter(
                            is_active=True,
                            member=user,
                            membership_request_status__code='APPROVED',
                        ).exists()
                        if not is_member_project:
                            raise ValidationError({"message": "Вы не можете указывать эту организацию: нет доступа."})
                    else:
                        raise ValidationError({"message": "Вы не можете указывать эту организацию: нет доступа."})
        if self.instance.task_type.code != 'interest' or contract:
            validate_task_customer_card(contract, customer_card)
        return data

    def update(self, instance, validated_data):
        task_type = instance.task_type
        if task_type.code == 'interest':
            customer_card = validated_data.get('customer_card', instance.customer_card)
            contractor = validated_data.get('contractor', instance.contractor)
            p_contractor_name = validated_data.get('p_contractor_name', None)
            raw_potential_contractor = self.initial_data.get('potential_contractor')
            potential_contractor = instance.potential_contractor
            if not customer_card and (bool(contractor) is bool(
                    p_contractor_name or raw_potential_contractor or potential_contractor
            )):
                raise ValidationError(
                    'Должно быть заполнено одно из полей - '
                    'карточка клиента, старый клиент или потенциальный клиент.'
                )

        # Извлекаем точки из initial_data
        raw_task_points = self.initial_data.pop('task_points', [])
        existing_points, new_points = [], []
        # Если у объекта точки есть поле id, заносим его в список
        # уже существующих точек existing_points, иначе
        # добавляем точку в список на создание новых точек
        for point in raw_task_points:
            id = point.get('id', None)
            if id:
                existing_points.append(id)
            else:
                new_points.append(point)

        # Сериализуем и валидируем данные для новых точек
        task_points_serializer = TaskPointSerializer(
            data=new_points,
            many=True
        )
        task_points_serializer.is_valid(raise_exception=True)
        # Если данные прошли валидацию создаем новые точки
        # для текщей задачи, id созданных точек добавляем
        # в список существующих
        for point in task_points_serializer.data:
            new_point = models.TaskPointModel.objects.create(
                            task=instance,
                            **point
                        )
            existing_points.append(str(new_point.id))
        # Получаем все точки текущей задачи
        task_points = models.TaskPointModel.objects.filter(
            is_active=True,
            task=instance
        )

        # Если id точки нет в списке existing_points удаляем ее
        for point in task_points:
            if str(point.id) not in existing_points:
                point.is_active = False
                point.save()

        # Удаляем данные о точках из словаря validated_data
        task_points = validated_data.pop('task_points', None)

        contractor = validated_data.get('contractor', None)
        p_contractor_name = validated_data.pop('p_contractor_name', None)
        p_contractor_company = validated_data.pop('p_contractor_company', None)
        phone = validated_data.pop('phone', None)
        email = validated_data.pop('email', None)
        raw_potential_contractor = self.initial_data.pop('potential_contractor', None)

        if contractor is not None:
            instance.potential_contractor = None
        elif raw_potential_contractor:
            try:
                p_contractor = PotentialContractorModel.objects.get(
                    id=raw_potential_contractor['id']
                )
            except ObjectDoesNotExist:
                raise ValidationError(
                    'Не удалось найти потенциального клиента')
            p_contractor.name = p_contractor_name
            p_contractor.company_name = p_contractor_company
            p_contractor.phone = phone
            p_contractor.email = email
            p_contractor.save()
        elif p_contractor_name:
            potential_contractor_data = {
                'name': p_contractor_name,
                'company_name': p_contractor_company,
                'phone': phone,
                'email': email
            }
            potential_contractor_serializer = InterestPotentialContractorModelSerializer(
                data=potential_contractor_data
            )
            potential_contractor_serializer.is_valid(raise_exception=True)
            potential_contractor = potential_contractor_serializer.save()
            instance.potential_contractor = potential_contractor

        initiator = self.context.get('request').user.profile
        initiator_id = initiator.pk
        old_operator_id = instance.operator_id
        old_owner_id = instance.owner_id
        old_visors_id: set = set(instance.visors.all().values_list('pk', flat=True))
        old_cooperators_id: set = set(instance.cooperators.all().values_list('pk', flat=True))
        old_description = instance.description
        old_members_id = {old_operator_id} | {old_owner_id} | old_visors_id | old_cooperators_id
        updated_instance = super().update(instance, validated_data)

        updated_visors_id = set(instance.visors.all().values_list('pk', flat=True))
        updated_cooperators_id = set(instance.cooperators.all().values_list('pk', flat=True))
        updated_owner_id = instance.owner_id
        updated_operator_id = instance.operator_id
        updated_members_id = {updated_operator_id} | {updated_owner_id} | updated_visors_id | updated_cooperators_id
        kicked_members_id = old_members_id - updated_members_id
        if kicked_members_id:
            kicked_members = ProfileModel.objects.filter(pk__in=kicked_members_id)
            for kicked_member in kicked_members:
                utils.stop_work_log_timer(kicked_member, updated_instance)
        if updated_instance.operator_id not in (old_operator_id, initiator_id):
            async_task(notifications.notify_about_assign_operator_task, updated_instance, initiator)
        if updated_instance.owner_id not in (old_owner_id, initiator_id):
            async_task(notifications.notify_about_assign_owner_task, updated_instance, initiator)
        new_visors_id: set = updated_visors_id - old_visors_id - {initiator_id}
        if new_visors_id:
            async_task(notifications.notify_about_assign_visor_task, updated_instance, initiator, tuple(new_visors_id))
        # уведомление новых соисполнителей
        new_cooperators_id: set = updated_cooperators_id - old_cooperators_id - {initiator_id}
        if new_cooperators_id:
            async_task(notifications.notify_about_assign_cooperator_task, updated_instance, initiator, tuple(new_cooperators_id))
        # уведомление наблюдателей о новых соисполнителях
        new_cooperators_id: set = updated_cooperators_id - old_cooperators_id
        if new_cooperators_id:
            recipients = updated_visors_id
            recipients.add(updated_instance.owner_id)
            recipients.discard(initiator_id)
            recipients.difference_update(new_cooperators_id)
            if recipients:
                for new_cooperator_id in new_cooperators_id:
                    async_task(
                        notifications.notify_visors_about_assign_cooperator_task,
                        updated_instance,
                        initiator,
                        ProfileModel.objects.get(pk=new_cooperator_id),
                        tuple(recipients)
                    )
        # уведомление наблюдателей о новом исполнителе
        if not updated_instance.operator_id == old_operator_id:
            recipients = updated_visors_id
            recipients.add(updated_instance.owner_id)
            recipients.discard(initiator_id)
            recipients.discard(updated_instance.operator_id)
            if recipients:
                async_task(
                    notifications.notify_visors_about_assign_operator_task,
                    updated_instance,
                    initiator,
                    updated_instance.operator,
                    tuple(recipients)
                )
        # уведомление всех об изменении описания задачи
        if not old_description == updated_instance.description:
            async_task(notifications.notify_about_new_description, instance, initiator)
        return updated_instance

    def to_representation(self, instance):
        data = DetailTaskSerializer(instance).data
        return data


class TakeAuctionTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'operator',
        )

    def update(self, instance, validated_data):
        initiator = self.context.get('request').user.profile
        initiator_id = initiator.id
        old_operator_id = instance.operator_id
        instance.operator = initiator
        instance.is_auction = False
        instance.save()
        cache.set('CachedAppUserSerializer_' + str(instance.operator.pk), None)
        if instance.operator_id != instance.owner_id:
            # async_task(notifications.notify_about_take_auction, instance, initiator_id)
            async_task(notifications.notify_about_take_auction, instance, initiator)
            # notifications.notify_about_take_auction(instance, initiator)
        return instance

    def to_representation(self, instance):
        data = DetailTaskSerializer(instance).data
        return data


class UpdateOwnerTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskModel
        fields = (
            'owner',
        )

    def update(self, instance, validated_data):
        initiator = self.context.get('request').user.profile
        initiator_id = initiator.pk
        old_owner_id = instance.owner_id
        updated_instance = super().update(instance, validated_data)
        if not old_owner_id == updated_instance.owner_id:
            updated_instance.visors.add(old_owner_id)
        if updated_instance.owner_id not in (old_owner_id, initiator_id):
            async_task(notifications.notify_about_assign_owner_task, updated_instance, initiator)
        return updated_instance

    def to_representation(self, instance):
        return {"owner": AppUserSerializer(instance.owner).data}


class UpdateOperatorTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskModel
        fields = (
            'operator',
        )

    def update(self, instance, validated_data):
        initiator = self.context.get('request').user.profile
        initiator_id = initiator.pk
        old_operator_id = instance.operator_id
        old_operator = instance.operator
        updated_instance = super().update(instance, validated_data)
        if updated_instance.operator_id not in (old_operator_id, initiator_id):
            async_task(notifications.notify_about_assign_operator_task, updated_instance, initiator)
        if not updated_instance.operator_id == old_operator_id:
            roles = set(updated_instance.get_task_roles(old_operator_id))
            roles.discard('project_moderator')
            if not roles:
                utils.stop_work_log_timer(old_operator, instance,)
        return updated_instance

    def to_representation(self, instance):
        return {'operator': AppUserSerializer(instance.operator).data}


class UpdateDeadlineTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskModel
        fields = (
            'dead_line',
        )


class SprintExpectedResultListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SprintExpectedResultModel
        fields = (
            'id',
            'comment',
            'approved',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        task = instance.task
        if task:
            data['operator'] = CachedAppUserPreviewSerializer(task.operator).data
            data['dead_line'] = serializers.DateTimeField().to_representation(task.dead_line)
            data['status'] = get_status_data(task)
            data['result'] = task.result
            data['task'] = {'id': task.id, 'counter': task.counter}
            if task.sprint == instance.sprint:
                data['excluded'] = False
            else:
                data['excluded'] = True
        return data


class SprintExpectedResultUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SprintExpectedResultModel
        fields = (
            'id',
            'comment',
            'approved',
        )

    def to_representation(self, instance):
        return SprintExpectedResultListSerializer(instance, context=self.context).data


class SprintMemberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # сотрудник:
        data['user'] = CachedAppUserPreviewSerializer(instance, context=self.context).data
        # роль в спринте:
        sprint = self.context.get('sprint')
        scrum_masters_id = self.context.get('scrum_masters_id')
        data['is_scrum_master'] = instance.pk in scrum_masters_id
        # кол-во задач
        included_tasks_id = self.context.get('included_tasks_id')
        has_urgent_task = False
        user_tasks = models.TaskModel.objects.filter(
            Q(operator=instance) |
            Q(cooperators=instance),
            pk__in=included_tasks_id
        ).distinct()
        if user_tasks.filter(priority=4).exists():
            has_urgent_task = True
        sprint_history = models.TaskSprintHistoryModel.objects.filter(
            Q(task__operator=instance) |
            Q(task__cooperators=instance),
            for_completed=True,
            sprint=sprint,
        ).distinct()

        if has_urgent_task is False and sprint_history.filter(task__priority=4).exists():
            has_urgent_task = True
        data['has_urgent_task'] = has_urgent_task
        data['task_count'] = user_tasks.count() + sprint_history.count()
        # выполнено (кол-во, проценты):
        data['completed_count'] = user_tasks.filter(status_id='completed').count()
        try:
            data['completed_percent'] = (data['completed_count'] * 100) / data['task_count']
        except ZeroDivisionError:
            data['completed_percent'] = 0
        # трудозатраты (в ч):
        execution_time = self.context.get('execution_time')
        data['hours'] = sum(x['hours_sum'] if x['user'] == instance.pk else 0 for x in execution_time)

        # Последняя активность:
        data['last_activity'] = serializers.DateTimeField().to_representation(instance.last_activity)
        # нужна помощь:

        user_tasks_id = set(user_tasks.values_list('pk', flat=True))
        sprint_history_tasks_id = set(sprint_history.values_list('task', flat=True))
        common_tasks_id = user_tasks_id | sprint_history_tasks_id
        need_help_tasks = models.TaskModel.objects.filter(
            status_id='need_help',
            pk__in=common_tasks_id
        ).values('id', 'counter')

        data['need_help_tasks'] = need_help_tasks

        # Блокеры:
        tasks_with_blockers = user_tasks.filter(object_tags__isnull=False)
        blocked_tasks_data = TaskWithBlockersSerializer(tasks_with_blockers, many=True).data
        sprint_history_blockers = sprint_history.filter(blockers__isnull=False)
        sprint_history_blockers_data = SprintHistoryBlockersSerializer(sprint_history_blockers, many=True).data
        blocked_tasks_data = blocked_tasks_data + sprint_history_blockers_data
        data['blocked_tasks'] = blocked_tasks_data
        return data


class SprintHistoryBlockersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskSprintHistoryModel
        fields = (
            'id'
        )

    def to_representation(self, instance):
        task = instance.task
        data = {
            'id': task.id,
            'counter': task.counter,
            'blockers': instance.blockers
        }
        return data


class TaskWithBlockersSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'counter',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['blockers'] = TagModelListSerializer(
            instance.object_tags.all().order_by('name'),
            context={'related_object': instance.pk},
            many=True
        ).data
        return data


class SetSprintTaskSerializer(serializers.ModelSerializer):
    dead_line = serializers.ReadOnlyField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'sprint',
            'dead_line',
        )

    def validate_sprint(self, sprint):
        if sprint:
            sprint_checked = self.context.get('sprint_checked', False)
            if not sprint_checked:
                request = self.context.get('request')
                if sprint.status == 'completed':
                    raise ValidationError({"sprint": "Спринт уже завершен"})
                if not sprint.get_update_permission(request):
                    raise ValidationError({"sprint": "У вас нет прав на добавления в этот спринт"})
                self.context['sprint_checked'] = True
        return sprint

    def update(self, instance, validated_data):
        old_sprint = instance.sprint
        new_sprint = validated_data.get('sprint')
        if old_sprint == new_sprint:
            return instance
        # Устанавливаем оба поля и сохраняем одним вызовом, чтобы избежать двойной записи в историю изменений
        instance.sprint = new_sprint
        instance.add_sprint_date = timezone.now()
        instance.save(update_fields=('sprint', 'add_sprint_date'))
        if new_sprint:
            date_begin = new_sprint.begin_date
            date_end = new_sprint.dead_line
            if date_begin and date_end:
                task_time_qs = instance.execution_time.filter(
                    is_active=True,
                    sprint__isnull=True,
                    date__gte=date_begin,
                    date__lte=date_end,
                )
                task_time_qs.update(sprint=new_sprint)
            user = self.context.get('request').user.profile
            instance.task_sprint_history.filter(
                task=instance,
                sprint=new_sprint
            ).delete()
            with transaction.atomic():
                try:
                    instance.sprint_expected_results.create(
                        task=instance,
                        sprint=new_sprint,
                    )
                except IntegrityError:
                    pass
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_about_set_sprint,
                    instance,
                    instance.sprint,
                    user
                )
            )
        if old_sprint and new_sprint:
            with transaction.atomic():
                try:
                    instance.task_sprint_history.create(
                        task=instance,
                        sprint=old_sprint,
                        moved_to='sprint',
                        moved_to_sprint=new_sprint,
                        status=instance.status
                    )
                except IntegrityError:
                    pass
        if old_sprint and not new_sprint:
            with transaction.atomic():
                try:
                    instance.task_sprint_history.create(
                        task=instance,
                        sprint=old_sprint,
                        moved_to='backlog',
                        status=instance.status
                    )
                except IntegrityError:
                    pass
        return instance


class DeleteTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class UpdateStatusTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'status',

        )

    def update(self, instance, validated_data):
        old_status_code = instance.status_id
        new_status_code = validated_data.get('status').code
        if not old_status_code == new_status_code:
            instance.status = validated_data.get('status')
            new_status = models.TaskStatusTypeModel.objects.get(task_type_id=instance.task_type_id,
                                                                task_status_id=new_status_code)
            now = timezone.now()
            if new_status.is_complete:
                instance.finished_date = now
            if instance.task_type_id == 'logistic' and old_status_code == 'new' and not new_status.is_complete:
                instance.date_start_fact = now
            instance.save()
            if old_status_code == 'new' and new_status_code == 'in_work':
                reason_id = instance.reason
                if reason_id:
                    reason_object = utils.get_reason_object(reason_id)
                    if reason_object.get_label() == 'help_desk.HelpDeskTicketModel':
                        ticket_status_code = reason_object.status_id
                        if ticket_status_code == 'new':
                            reason_object.status_id = 'in_work'
                            reason_object.start_date = now
                            reason_object.save()
                            reason_object.refresh_from_db()
                            from help_desk.notifications import notify_about_new_status
                            user = get_current_authenticated_profile()
                            if user:
                                user_pk = user.pk
                            else:
                                user_pk = None
                            transaction.on_commit(
                                lambda: async_task(notify_about_new_status, str(user_pk),
                                                   str(reason_object.pk), str(reason_object.status_id))
                            )
            if instance.task_type_id == 'logistic' and new_status_code == 'in_transit':
                utils.set_delivery_status_in_orders(instance)
            try:
                initiator = self.context.get('request').user.profile
            except AttributeError:
                # Для биометрии. Если нет пользователя, инициатором будет ответственный
                initiator = instance.operator
            async_task(notifications.notify_about_new_status, str(instance.pk), new_status_code, str(initiator.pk))
        return instance


class TaskPinSerializer(serializers.Serializer):
    pinned = serializers.BooleanField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        task_status_type = instance.status.task_status_type.all().first()
        data['can_shipment'] = False

        if task_status_type:
            data['can_shipment'] = task_status_type.can_shipment

        if instance.task_type_id == 'logistic' and instance.date_start_fact:
            data['update_fields'] = {
                'date_start_fact': serializers.DateTimeField().to_representation(instance.date_start_fact)
            }
        return data


class UpdateCooperatorStatusTaskSerializer(serializers.ModelSerializer):
    """Сериализатор изменения статуса задачи соисполнителя."""

    class Meta:
        model = models.TaskCooperator
        fields = (
            'id',
            'status',
        )

    def update(self, instance, validated_data):
        old_status_code = instance.status_id
        new_status_code = validated_data.get('status').code
        initiator = self.context.get('request').user.profile
        if not old_status_code == new_status_code:
            set_task_status = False
            with transaction.atomic():
                instance.status_id = new_status_code
                instance.save()

                task = instance.task
                if not new_status_code == 'new' and task.status_id == 'new':
                    task.status_id = 'in_work'
                    task.save(update_fields=('status_id',))
                    set_task_status = True
            async_task(
                notifications.notify_about_new_cooperator_status,
                str(instance.pk), new_status_code, str(initiator.pk), set_task_status
            )
        return instance


class UpdateRejectionReasonTasSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'rejection_reason',
        )

    def update(self, instance, validated_data):
        rejection_reason = validated_data.get('rejection_reason')
        instance.rejection_reason = rejection_reason
        instance.save()
        return instance


class UpdateReasonTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskModel
        fields = (
            'reason',
        )

    def to_representation(self, instance):
        reason_obj = utils.get_reason_object(instance.reason)
        if reason_obj:
            s_data = reason_obj.get_serializer_class(action='chat_share')(instance=reason_obj).data
            s_data['type'] = reason_obj.get_label()
            return {'reason': s_data}
        else:
            return {'reason': None}


class KanbanExtraFieldSerializer(serializers.RelatedField):
    def to_representation(self, instance):
        return instance.pk

    def to_internal_value(self, data):
        obj_id = data
        try:
            obj = models.TaskModel.objects.get(pk=obj_id)
        except ObjectDoesNotExist:
            raise ValidationError('Object does not exist')
        return obj


class UpdateKanbanStatusTaskSerializer(serializers.ModelSerializer):
    previous = KanbanExtraFieldSerializer(queryset=models.TaskModel.objects.filter(is_active=True), allow_null=True)
    next = KanbanExtraFieldSerializer(queryset=models.TaskModel.objects.filter(is_active=True), allow_null=True)

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'status',
            'previous',
            'next'
        )

    def update(self, instance, validated_data):
        user = self.context.get('request').user.profile
        old_status_code = instance.status_id
        instance.status = validated_data.get('status')
        instance.save()
        new_status_code = validated_data.get('status').code
        if not old_status_code == new_status_code:
            async_task(notifications.notify_about_new_status, str(instance.pk), new_status_code, str(user.pk))
            if new_status_code == 'in_transit' and instance.task_type_id == 'logistic':
                utils.set_delivery_status_in_orders(instance)
        previous_sort = self.get_sort(validated_data.get('previous'))
        next_sort = self.get_sort(validated_data.get('next'))
        if not (previous_sort is None and next_sort is None):
            user_task_sort, created = models.UserTaskSort.objects.get_or_create(user=user, task=instance)
            if previous_sort is None:
                user_task_sort.sort = next_sort - 0.5
            elif next_sort is None:
                user_task_sort.sort = previous_sort + 0.5
            else:
                user_task_sort.sort = (previous_sort + next_sort) / 2
            user_task_sort.save()
        return instance

    def get_sort(self, instance):
        if instance is None:
            return None
        try:
            sort = models.UserTaskSort.objects.get(user=self.context.get('request').user.profile, task=instance).sort
        except ObjectDoesNotExist:
            sort = instance.number_from_counter
        return sort

    def to_representation(self, instance):
        return {'id': instance.id,
                'status': instance.status_id,
                'previous': self.context.get('request').data.get('previous'),
                'next': self.context.get('request').data.get('next')}


class ShortTaskSerializer(serializers.ModelSerializer):
    # author = AppUserSerializer()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'name',
            'counter',
            # 'author',
            'date_start_plan',
            'date_start_fact',
            'dead_line',
        )


class ShortFireTaskSerializer(serializers.ModelSerializer):
    owner = CachedAppUserPreviewSerializer(source='owner_id')
    operator = CachedAppUserPreviewSerializer(source='operator_id')
    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'name',
            'counter',
            'owner',
            'operator',
        )


class ShortTaskInSprintSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'name',
            'author',
            'status'
        )


class TaskStatusModelSerializer(serializers.ModelSerializer):
    """Сериализатор статуса задачи."""
    class Meta:
        model = models.TaskStatusModel
        fields = (
            'code',
            'name',
            'color',
            'progress',
            'hex_color'
        )


class TaskStatusModelNotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskStatusModel
        fields = (
            'code',
            'name_ru',
            'name_kk',
            'name_en',
        )


class TaskDeliveryPointSerializer(serializers.ModelSerializer):
    point = '1'
    orders = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskDeliveryPointModel
        fields = (
            'id',
            'front_id',
            'duration',
            'delivery_date',
            'orders',
            'is_start',
            'need_amount_pay',
        )

    def get_orders(self, instance):
        if instance.is_start:
            return GoodsOrderModelListSerializer(instance.start_goods_orders.all(), many=True).data
        else:
            return GoodsOrderModelListSerializer(instance.goods_orders.all(), many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        point = instance.delivery_point
        data['lat'] = point.lat if point else None
        data['lon'] = point.lon if point else None
        data['name'] = point.name if point else None
        data['point'] = self.point
        self.point = str(int(self.point) + 1)
        return data


class TaskDeliveryPointSetNeedPayAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskDeliveryPointModel
        fields = (
            "id",
            "need_amount_pay",
        )


class TaskDeliveryPointCreateFromOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskDeliveryPointModel
        fields = (
            'id',
            'duration',
        )


class ListTaskSerializer(serializers.ModelSerializer):
    """Общий сериализатор для задач всех типов (logistic, interest, task)."""
    # TODO Для обычных задач уже выделен OptimizedListTaskSerializer. Надо выделить специализированные сериализаторы для logistic и interest.
    children_count = serializers.SerializerMethodField()
    owner = CachedAppUserSerializer(source='owner_id')
    operator = CachedAppUserSerializer(source='operator_id')
    author = CachedAppUserSerializer(source='author_id')
    visors = CachedAppUserPreviewSerializer(many=True)
    status = serializers.SerializerMethodField()
    sprint = TaskSprintShortSerializer()
    task_type = serializers.SerializerMethodField()
    parent = ShortTaskSerializer()
    next_delivery_point = serializers.SerializerMethodField()
    workgroup = CachedBaseModelSerializer(source='workgroup_id', serializer_class=WorkgroupNameLogoSerializer)
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)
    contract = serializers.UUIDField(source='contract_id', read_only=True)
    contractor = CachedBaseModelSerializer(source='contractor_id', serializer_class=ContractorModelShortSerializer)
    organization = CachedBaseModelSerializer(source='organization_id', serializer_class=ContractorModelShortSerializer)
    customer_card = CustomerCardModelShortSerializer()
    customer_name = serializers.SerializerMethodField()
    contractor_name = serializers.SerializerMethodField()
    business_region_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    completed_children_count = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    task_points = TaskPointSerializer(many=True)
    rejection_reason = RejectionReasonModelSerializer()
    lead_source = LeadSourceModelSerializer()
    potential_contractor = InterestPotentialContractorModelSerializer(read_only=True, required=False)
    nearest_event = serializers.SerializerMethodField()
    last_execution_time = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'author',
            'children_count',
            'color',
            'counter',
            'created_at',
            'date_start_fact',
            'date_start_plan',
            'dead_line',
            'finished_date',
            'is_auction',
            'is_indefinite',
            'is_overdue',
            'level',
            'name',
            'result',
            'next_delivery_point',
            'operator',
            'parent',
            'priority',
            'project',
            'contract',
            'status',
            'sprint',
            'visors',
            'task_type',
            'owner',
            'updated_at',
            'workgroup',
            'contractor',
            'organization',
            'customer_card',
            'customer_name',
            'contractor_name',
            'business_region_name',
            'task_points',
            'rejection_reason',
            'lead_source',
            'potential_contractor',
            'phone',
            'email',
            'frontend_route',
            'last_execution_time',
            'nearest_event',
            'completed_children_count',
            'participants_count',
            'is_sign_task',
        )

    def get_has_description(self, instance):
        try:
            return instance.has_description
        except AttributeError:
            return None

    def get_participants_count(self, instance):

        return -1 # Убрано 26.06.2025 совместно с Приб К.

        try:
            return instance.participants_count
        except AttributeError:
            return None

    def get_attachments_count(self, instance):
        try:
            return instance.attachments_count
        except AttributeError:
            return None

    def get_comments_count(self, instance):
        try:
            return instance.comments_count
        except AttributeError:
            return None

    def get_completed_children_count(self, instance):
        try:
            return instance.completed_children_count
        except AttributeError:
            return None

    def get_business_region_name(self, instance):
        if instance.potential_contractor:
            return instance.potential_contractor.business_region_name
        return None

    def get_phone(self, instance):
        if instance.contractor:
            return instance.contractor.phone
        elif instance.potential_contractor:
            return instance.potential_contractor.phone
        else:
            return None

    def get_email(self, instance):
        if instance.contractor:
            return instance.contractor.email
        elif instance.potential_contractor:
            return instance.potential_contractor.email
        else:
            return None

    def get_contractor_name(self, instance):
        if instance.potential_contractor:
            return instance.potential_contractor.company_name
        return None

    def get_customer_name(self, instance):
        if instance.customer_card:
            return instance.customer_card.name
        if instance.potential_contractor:
            return instance.potential_contractor.company_name or instance.potential_contractor.name
        if instance.contractor:
            return instance.contractor.name
        return None

    def get_children_count(self, instance):
        return utils.get_children_count(instance)

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def get_task_type(self, instance):
        return instance.task_type_id

    def get_next_delivery_point(self, instance):
        task_type = getattr(self.context.get('request', None), 'query_params', dict()).get('task_type', 'task')
        if not task_type == 'logistic':
            return None
        try:
            next_delivery_point = instance.next_delivery_point[0]
        except IndexError:
            return None
        return TaskDeliveryPointSerializer(next_delivery_point).data if next_delivery_point else None

    def get_nearest_event(self, obj):

        return None  # Убрано 26.06.2025 совместно с Приб К.
    
        # nearest_start = None
        #
        # for calendar in obj.event_calendars.all():
        #     events = getattr(calendar, 'prefetched_future_events', [])
        #     for event in events:
        #         if nearest_event is None or event.start_at < nearest_start:
        #             nearest_event = event
        #             nearest_start = event.start_at
        #
        # if nearest_event:
        #     return EventCalendarModelListSerializer(nearest_event).data
        # return None

    def get_last_execution_time(self, instance):

        return 'Выключили 26.06.2025'  # 26.06.2025 совместно с Приб К.
    
        # if hasattr(instance, 'prefetched_exec_times') and instance.prefetched_exec_times:
        #     return instance.prefetched_exec_times[0].work_type.name
        # else:
        #     return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        task_sort = getattr(instance, 'sort_field', None)
        data['sort_field'] = task_sort
        data['comments_count'] = getattr(instance, 'comments_count', 0)
        data['attachments_count'] = getattr(instance, 'attachments_count', 0)
        data['has_description'] = getattr(instance, 'attachments_count', False)
        data['vote'] = get_vote_info(instance)
        try:
            data['has_order'] = bool(instance.annotate_order_exists)
        except AttributeError:
            pass
        cooperators = instance.cooperator_tasks.all()
        data['cooperators'] = TaskCooperatorShortSerializer(cooperators, many=True).data
        request = self.context.get('request')
        if request:
            user = request.user
            if user:
                profile = user.profile
                if profile:
                    data['can_update_owner'] = profile.pk == instance.owner_id
                    data['can_update_operator'] = profile.pk in (instance.owner_id, instance.operator_id)
                    data['can_update_status'] = utils.can_update_status(profile.pk, instance)
        data['blockers'] = TagModelListSerializer(
            instance.object_tags.all(),
            many=True,
            context={'related_object': instance.pk}
        ).data
        data['in_favorites'] = get_in_favorites(instance)
        return data


class OptimizedListTaskSerializer(serializers.ModelSerializer):
    """Сериализатор с минимально необходимым количеством полей для отображения обычных задач"""
    children_count = serializers.SerializerMethodField()
    owner = CachedAppUserPreviewSerializer(source='owner_id')
    operator = CachedAppUserPreviewSerializer(source='operator_id')
    visors = CachedAppUserPreviewSerializer(many=True)
    status = serializers.SerializerMethodField()
    sprint = TaskSprintShortSerializer()
    task_type = serializers.SerializerMethodField()
    parent = ShortTaskSerializer()
    workgroup = CachedBaseModelSerializer(source='workgroup_id', serializer_class=WorkgroupNameLogoSerializer)
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)
    contract = serializers.UUIDField(source='contract_id', read_only=True)
    organization = CachedBaseModelSerializer(source='organization_id', serializer_class=ContractorModelShortSerializer)

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'children_count',
            'counter',
            'created_at',
            'date_start_fact',
            'date_start_plan',
            'dead_line',
            'finished_date',
            'level',
            'name',
            'operator',
            'parent',
            'priority',
            'project',
            'contract',
            'status',
            'sprint',
            'visors',
            'task_type',
            'owner',
            'workgroup',
            'contractor',
            'organization',
            'frontend_route',
            'is_sign_task',
        )

    def get_children_count(self, instance):
        return utils.get_children_count(instance)

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def get_task_type(self, instance):
        return instance.task_type_id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        cooperators = instance.cooperator_tasks.all()
        data['cooperators'] = TaskCooperatorShortSerializer(cooperators, many=True).data
        request = self.context.get('request')
        if request:
            user = request.user
            if user:
                profile = user.profile
                if profile:
                    data['can_update_owner'] = profile.pk == instance.owner_id
                    data['can_update_operator'] = profile.pk in (instance.owner_id, instance.operator_id)
                    data['can_update_status'] = utils.can_update_status(profile.pk, instance)
        data['blockers'] = TagModelListSerializer(
            instance.object_tags.all(),
            many=True,
            context={'related_object': instance.pk}
        ).data
        data['in_favorites'] = get_in_favorites(instance)
        return data


class MyDayTaskSerializer(serializers.Serializer):
    """Сериализатор для аналитики задач по истории изменений."""
    id = serializers.UUIDField()
    counter = serializers.CharField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    status = serializers.SerializerMethodField()
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)
    workgroup = CachedBaseModelSerializer(source='workgroup_id', serializer_class=WorkgroupNameLogoSerializer)
    # organization_id = serializers.UUIDField(allow_null=True)
    date_start_plan = serializers.DateTimeField(allow_null=True)
    dead_line = serializers.DateTimeField(allow_null=True)
    priority = serializers.CharField(allow_null=True)
    # author = serializers.SerializerMethodField()
    # operator = serializers.SerializerMethodField()
    # owner = serializers.SerializerMethodField()
    # visors = serializers.SerializerMethodField()
    # cooperators = serializers.SerializerMethodField()
    hours_total_all = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    hours_total_range = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    duration_total_all = serializers.IntegerField(read_only=True)
    duration_total_range = serializers.IntegerField(read_only=True)
    actual_duration_days = serializers.IntegerField(allow_null=True, read_only=True)
    is_executor = serializers.BooleanField(read_only=True)
    is_owner = serializers.BooleanField(read_only=True)
    is_visor = serializers.BooleanField(read_only=True)
    has_new_comments = serializers.BooleanField(read_only=True)
    pinned = serializers.BooleanField(read_only=True)

    def get_status(self, instance):
        return utils.get_status_data(instance)

    # def get_author(self, instance):
    #     if instance.author_id:
    #         return CachedAppUserPreviewSerializer(instance.author_id).data
    #     return None

    # def get_operator(self, instance):
    #     if instance.operator_id:
    #         return CachedAppUserPreviewSerializer(instance.operator_id).data
    #     return None

    # def get_owner(self, instance):
    #     if instance.owner_id:
    #         return CachedAppUserPreviewSerializer(instance.owner_id).data
    #     return None

    # def get_visors(self, instance):
    #     visors = instance.visors.all()
    #     return [CachedAppUserPreviewSerializer(visor).data for visor in visors]

    # def get_cooperators(self, instance):
    #     cooperators = instance.cooperators.all()
    #     return [CachedAppUserPreviewSerializer(cooperator).data for cooperator in cooperators]

    def to_representation(self, instance):
        analytics_data_map = self.context.get('analytics_data_map', {})
        action_info_map = self.context.get('action_info_map', {})
        data = analytics_data_map.get(str(instance.id), {})

        representation = super().to_representation(instance)
        representation['hours_total_all'] = data.get('hours_total_all', 0)
        representation['hours_total_range'] = data.get('hours_total_range', 0)
        representation['duration_total_all'] = data.get('duration_total_all', 0)
        representation['duration_total_range'] = data.get('duration_total_range', 0)
        representation['actual_duration_days'] = data.get('actual_duration_days')
        representation['has_new_comments'] = data.get('has_new_comments', False)
        representation['pinned'] = bool(instance.pinned_by.all())
        representation['blockers'] = TagModelListSerializer(
            instance.object_tags.all(),
            many=True,
            context={'related_object': instance.pk}
        ).data
        
        # Сериализуем связанных пользователей (те profile_ids, благодаря которым задача попала в список)
        related_profile_ids = data.get('related_profile_ids', [])
        representation['related_users'] = CachedAppUserPreviewSerializer(
            related_profile_ids,
            many=True,
            context=self.context
        ).data if related_profile_ids else []

        representation['is_current'] = data.get('is_current', False)
        representation['duration_incomplete'] = data.get('duration_incomplete', 0)
        if action_info_map:
            representation['action_info'] = action_info_map.get(str(instance.id), {})
        return representation


class ListTasksBySprintListSerializer(serializers.ModelSerializer):
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)
    organization = CachedBaseModelSerializer(source='organization_id', serializer_class=ContractorModelShortSerializer)
    workgroup = CachedBaseModelSerializer(source='workgroup_id', serializer_class=WorkgroupNameLogoSerializer)
    owner = CachedAppUserSerializer(source='owner_id')
    operator = CachedAppUserSerializer(source='operator_id')
    status = serializers.SerializerMethodField()
    task_type = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'counter',
            'name',
            'project',
            'organization',
            'workgroup',
            'operator',
            'owner',
            'status',
            'task_type',
        )

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def get_task_type(self, instance):
        return instance.task_type_id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        display = self.context.get('request').query_params.get('display')
        data['moved_to_sprint'] = None
        if display and display == 'moved_to_sprint':
            sprint = self.context.get('sprint')
            sprint_history = instance.task_sprint_history.filter(sprint=sprint).order_by('-created_at').first()
            if sprint_history:
                moved_to_sprint = sprint_history.moved_to_sprint
                if moved_to_sprint:
                    data['moved_to_sprint'] = {"id": moved_to_sprint.pk, "name": moved_to_sprint.name}
        data['blockers'] = TagModelListSerializer(
            instance.object_tags.all(), many=True, context={'related_object': instance.pk}
        ).data
        data['in_favorites'] = get_in_favorites(instance)
        return data


class KanbanListTaskSerializer(serializers.ModelSerializer):
    """Сериализатор списка задач для канбана (короткий сериализатор, только необходимые для отображения поля)."""
    owner = CachedAppUserSerializer(source='owner_id')
    operator = CachedAppUserSerializer(source='operator_id')
    status = serializers.SerializerMethodField()
    task_type = serializers.SerializerMethodField()
    parent = ShortTaskSerializer()
    project = CachedBaseModelSerializer(source='project_id', serializer_class=WorkgroupNameLogoSerializer)

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'counter',
            'date_start_plan',
            'dead_line',
            'is_indefinite',
            'is_overdue',
            'name',
            'operator',
            'parent',
            'priority',
            'project',
            'status',
            'task_type',
            'owner',
            'frontend_route',
            'is_sign_task',
        )

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def get_task_type(self, instance):
        return instance.task_type_id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        task_sort = getattr(instance, 'sort_field', None)
        data['sort_field'] = task_sort
        request = self.context.get('request')
        if request:
            user = request.user
            if user:
                profile = user.profile
                if profile:
                    data['can_update_owner'] = profile.pk == instance.owner_id
                    data['can_update_operator'] = profile.pk in (instance.owner_id, instance.operator_id)
                    data['can_update_status'] = utils.can_update_status(profile.pk, instance)
        data['blockers'] = TagModelListSerializer(
            instance.object_tags.all(), many=True, context={'related_object': instance.pk},
        ).data
        data['in_favorites'] = get_in_favorites(instance)
        return data


class ListGanttTaskSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    operator = AppUserSerializer()
    owner = AppUserSerializer()
    project = WorkgroupNameSerializer()
    status = serializers.SerializerMethodField()
    subtasks = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'author',
            'counter',
            'created_at',
            'date_start_fact',
            'date_start_plan',
            'dead_line',
            'description',
            'finished_date',
            'is_auction',
            'is_indefinite',
            'name',
            'operator',
            'owner',
            'parent_id',
            'priority',
            'project',
            'rejected',
            'status',
            'task_type',
            'updated_at',
            'subtasks',
        )

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def get_subtasks(self, instance):
        return ListGanttTaskSerializer(
            instance.get_children().select_related(
                'author__user',
                'owner__user',
                'operator__user',
                'workgroup',
                'project',
            ).filter(
                is_active=True,
                date_start_plan__isnull=False,
                dead_line__isnull=False
            ).order_by('date_start_plan'),
            many=True
        ).data


class ListGanttTaskSerializer_v2(serializers.ModelSerializer):
    text = serializers.CharField(source='name')
    start_date = serializers.DateTimeField(source='date_start_plan', read_only=True, format="%d-%m-%Y %H:%M")
    end_date = serializers.DateTimeField(source='dead_line', read_only=True, format="%d-%m-%Y %H:%M")
    duration = serializers.IntegerField(source='duration_minutes')
    type = serializers.CharField(source='task_type_id')
    status = serializers.SerializerMethodField()
    has_child = serializers.SerializerMethodField()
    operator = CachedAppUserSerializer(source='operator_id')
    owner = CachedAppUserSerializer(source='owner_id')
    workgroup = WorkgroupNameLogoSerializer()
    project = WorkgroupNameLogoSerializer()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'counter',
            'text',
            'result',
            'start_date',
            'end_date',
            'duration',
            'type',
            'parent',
            'has_child',
            'status',
            'operator',
            'owner',
            'workgroup',
            'project',
            'progress',
        )

    def get_status(self, instance):
        return utils.get_status_data(instance)
    
    def get_has_child(self, instance):
        return instance.get_children().filter(is_active=True).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['in_favorites'] = get_in_favorites(instance)
        return data


class ListCalendarTaskSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    operator = AppUserSerializer()
    owner = AppUserSerializer()
    prerequisites = ShortTaskSerializer(many=True)
    status = serializers.SerializerMethodField()
    project = WorkgroupNameSerializer()
    parent = ShortTaskSerializer()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'author',
            'counter',
            'created_at',
            'date_start_fact',
            'date_start_plan',
            'dead_line',
            'description',
            'finished_date',
            'is_auction',
            'is_indefinite',
            'is_overdue',
            'name',
            'result',
            'operator',
            'owner',
            'parent',
            'potential_contractor',
            'prerequisites',
            'priority',
            'project',
            'rejected',
            'status',
            'task_type',
            'updated_at',
        )

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['in_favorites'] = get_in_favorites(instance)
        return data


class ListLeadTaskSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y%m%d%H%M%S')
    updated_at = serializers.DateTimeField(format='%Y%m%d%H%M%S')

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'name',
            'created_at',
            'updated_at',
            'operator',
            'owner',
            'contractor',
            'potential_contractor',
            'scenario',
            'is_auction',
        )


# class DeliveryTableSerializer(serializers.ModelSerializer):
#     delivery_point = TaskDeliveryPointSerializer(source='owner')
#     good = BaseCatalogRetrieveSerializer()
#     contractor = ContractorModelShortSerializer()
#     attachments = serializers.SerializerMethodField()
#
#     def get_attachments(self, instance):
#         return get_serialized_attachments(instance)
#
#     def update(self, instance, validated_data):
#         instance.quantity_success = validated_data['quantity_success']
#         instance.comment = validated_data['comment']
#         instance.success_date = timezone.now()
#         instance.attachments.clear()
#         attachments = self.context['request'].data.get('attachments', [])
#         instance.attachments.set(attachments)
#         instance.save()
#
#         return instance
#
#     class Meta:
#         model = models.TaskDeliveryModel
#         fields = [
#             'id',
#             'good',
#             'delivery_point',
#             'contractor',
#             'quantity',
#             'amount',
#             'quantity_success',
#             'comment',
#             'attachments'
#         ]


class DeliveryTableSerializer(serializers.ModelSerializer):
    delivery_point = serializers.SerializerMethodField()
    good = BaseCatalogRetrieveSerializer(source='goods')
    contractor = ContractorModelShortSerializer(source='owner.contractor')
    attachments = serializers.SerializerMethodField()  # TODO заглушка
    comment = serializers.CharField(source='delivery_comment')  # TODO заглушка

    class Meta:
        model = TPGoodsOrderModel
        fields = (
            'id',
            'delivery_point',
            'good',
            'contractor',
            'attachments',
            'quantity',
            'amount',
            'quantity_success',
            'comment',
        )

    def get_delivery_point(self, instance):
        return TaskDeliveryPointSerializer(instance.owner.task_delivery_point).data

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)  # TODO добавить аттачи


class DetailTaskSerializer(serializers.ModelSerializer):
    prerequisites = serializers.SerializerMethodField()
    project = WorkgroupNameLogoSerializer()
    workgroup = WorkgroupNameLogoSerializer()
    owner = AppUserSerializer()
    operator = serializers.SerializerMethodField()
    author = AppUserSerializer()
    visors = AppUserSerializer(many=True)
    attachments = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    parent = ShortTaskSerializer()
    reason = serializers.SerializerMethodField()
    hours = serializers.SerializerMethodField()
    sprint = TaskSprintShortSerializer()
    sprint_history = TaskSprintShortSerializer(many=True)
    contract = CustomerContractShortSerializer()
    customer_card = CustomerCardModelShortSerializer()
    contractor = CachedBaseModelSerializer(source='contractor_id', serializer_class=ContractorModelShortSerializer)
    potential_contractor = InterestPotentialContractorModelSerializer()
    status = serializers.SerializerMethodField()
    show_step = serializers.SerializerMethodField()
    contractor_name = serializers.SerializerMethodField()
    business_region_name = serializers.SerializerMethodField()
    contact_person = serializers.SerializerMethodField()
    can_update_status = serializers.SerializerMethodField()
    task_points = serializers.SerializerMethodField()
    lead_source = LeadSourceModelSerializer()
    rejection_reason = RejectionReasonModelSerializer()
    phone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    p_contractor_name = serializers.SerializerMethodField()
    p_contractor_company = serializers.SerializerMethodField()
    organization = ContractorModelByIdSerializer()
    duration = serializers.IntegerField(source='duration_minutes')
    meeting = serializers.SerializerMethodField()

    def get_p_contractor_name(self, instance):
        if instance.potential_contractor:
            return instance.potential_contractor.name
        return ''

    def get_p_contractor_company(self, instance):
        if instance.potential_contractor:
            return instance.potential_contractor.company_name
        return ''

    def get_phone(self, instance):
        if instance.contractor:
            return instance.contractor.phone
        elif instance.potential_contractor:
            return instance.potential_contractor.phone
        else:
            return ''

    def get_email(self, instance):
        if instance.contractor:
            return instance.contractor.email
        elif instance.potential_contractor:
            return instance.potential_contractor.email
        else:
            return ''

    def get_task_points(self, instance):
        points = instance.task_points.filter(is_active=True)
        if points:
            return TaskPointSerializer(points, many=True).data
        return []

    def get_business_region_name(self, instance):
        if instance.potential_contractor:
            return instance.potential_contractor.business_region_name
        return None

    def get_contact_person(self, instance):
        if instance.contractor and instance.contractor.contact_person:
            return AppUserSerializer(instance.contractor.contact_person).data
        else:
            return None

    def get_contractor_name(self, instance):
        if instance.potential_contractor:
            return instance.potential_contractor.company_name
        return None

    def get_operator(self, instance):
        if instance.operator:
            return AppUserSerializer(instance.operator).data
        return AppUserSerializer(instance.owner).data

    def get_can_update_status(self, instance):
        user = get_current_authenticated_profile()
        if user:
            return utils.can_update_status(user.pk, instance)
        else:
            return None

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'attachments',
            'author',
            'business_region_name',
            'can_update_status',
            'children_count',
            'color',
            'contractor',
            'contractor_name',
            'counter',
            'created_at',
            'date_start_fact',
            'date_start_plan',
            'dead_line',
            'deleted_at',
            'description',
            'finished_date',
            'hours',
            'is_auction',
            'is_overdue',
            'level',
            'name',
            'result',
            'operator',
            'owner',
            'parent',
            'potential_contractor',
            'prerequisites',
            'priority',
            'funds',
            'execution_time_plan',
            'project',
            'contract',
            'customer_card',
            'reason',
            'rejected',
            'show_step',
            'sprint',
            'sprint_history',
            'status',
            'task_type',
            'tmp_phone',
            'updated_at',
            'visors',
            'workgroup',
            'task_points',
            'lead_source',
            'rejection_reason',
            'contact_person',
            'phone',
            'email',
            'p_contractor_name',
            'p_contractor_company',
            'is_need_to_make_event',
            'organization',
            'metadata',
            'duration',
            'is_sign_task',
            'meeting',
        )

    def to_representation(self, instance):
        from bpms.okr.serializers import KeyResultsShortSerializer

        data = super().to_representation(instance)
        instance.cluts()
        data['viewer_count'] = instance.viewers.count()
        data['sprint_history'].reverse()
        data['delivery_points'] = self.get_delivery_points(instance)
        cooperators = models.TaskCooperator.objects.filter(task=instance)
        data['cooperators'] = TaskCooperatorSerializer(cooperators, many=True).data

        key_results = KeyResultsModel.objects.filter(
            is_active=True,
            key_result_tasks__task=instance
        )
        data['key_results'] = KeyResultsShortSerializer(key_results, many=True).data
        current_user = get_current_authenticated_profile()
        if not current_user:
            return data
        is_driver = current_user.is_driver
        is_storekeeper = current_user.is_storekeeper
        task_type = instance.task_type_id
        request = self.context.get('request')
        if request:
            mobile_app = is_mobile_app(request)
        else:
            mobile_app = False
        if mobile_app:
            prefix = 'mobile_app_'
        else:
            prefix = ''
        try:
            metadata = AppInfo.objects.get(is_active=True, code=f"{prefix}tasks_{task_type}_detail_info").metadata
        except AppInfo.DoesNotExist:
            metadata = dict()
        data.update(metadata)
        if data['task_points']:
            data['tabs'] = data.get('tabs', list()) + [{
                "code": "addresses",
                "name": "Адреса",
                "counter": True,
                "component": "TaskAddresses",
                "showAside": True
            }]
        if request:
            is_mobile = request.query_params.get('ver', '') == 'mobile'
        else:
            is_mobile = False
        if is_mobile:
            data['tabs'] = data.get('tabs', list()) + [{
                "code": "about",
                "component": "TaskAbout",
                "counter": False,
                "name": "Подробнее",
                "showAside": False
            }]
        if task_type == 'logistic':
            if is_storekeeper or is_driver:
                data['logistic_tabs'].pop("route", None)
                data['route_points'] = False
            else:
                data['route_points'] = True
            if is_driver or is_storekeeper:
                data['tabs'] = filter(lambda x: not x["code"] == 'pvh', data['tabs'])
        if task_type == 'interest':
            tabs = list(data.get('tabs') or [])
            if not any(tab.get('code') == 'interest_needs' for tab in tabs):
                tabs.append({
                    "code": "interest_needs",
                    "name": "Потребности",
                    "component": "UniversalTab",
                    "showAside": False,
                })
            if not any(tab.get('code') == 'interest_contract' for tab in tabs):
                # CRM: договор выводим отдельной вкладкой интереса, чтобы
                # пользователь видел переход "интерес -> договор -> заказ".
                tabs.append({
                    "code": "interest_contract",
                    "name": "Договор",
                    "component": "InterestContract",
                    "showAside": False,
                })
            data['tabs'] = tabs
        data['in_favorites'] = get_in_favorites(instance)
        return data

    def get_prerequisites(self, instance):
        prerequisites = instance.prerequisites.filter(is_active=True).annotate(
            children_count=Count('children', filter=Q(children__is_active=True)))
        return ListTaskSerializer(prerequisites, many=True).data

    def get_children_count(self, instance):
        return utils.get_children_count(instance)

    def get_reason(self, instance):
        reason_obj = utils.get_reason_object(instance.reason)
        if reason_obj:
            s_data = reason_obj.get_serializer_class(action='chat_share')(instance=reason_obj).data
            s_data['type'] = reason_obj.get_label()
            return s_data
        else:
            return None

    def get_hours(self, instance):
        hours = instance.execution_time.filter(is_active=True).aggregate(Sum('hours'))
        return hours['hours__sum'] if hours['hours__sum'] else 0

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def get_status(self, instance):
        return utils.get_status_data(instance)

    def get_show_step(self, instance):
        return getattr(getattr(instance, 'task_type', None), 'show_step', False)

    def get_delivery_points(self, instance):
        points = instance.task_delivery_points.all().order_by('-is_start', 'sort', 'created_at')
        return TaskDeliveryPointSerializer(points, many=True).data


    def get_meeting(self, instance):
        """Возвращает данные для подключения к связанной встрече."""
        from bpms.meetings.utils import get_related_meeting
        meeting = get_related_meeting(instance)
        if not meeting:
            return None
        return meeting.get_connect_info()


class TaskSprintListSerializer(serializers.ModelSerializer):
    expected_result = serializers.ListField()
    author = CachedAppUserSerializer(read_only=True, source='author_id')
    projects = WorkgroupNameSerializer(many=True)

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
            'name',
            'author',
            'dead_line',
            'created_at',
            'status',
            'begin_date',
            'finished_date',
            'time_interval',
            'duration',
            'target',
            'expected_result',
            'projects'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status == 'completed' and instance.task_count_history:
            data.update(instance.task_count_history)
        else:
            data.update(utils.get_sprint_task_count_data(instance))
        data['task_count'] = data.get('new_task_count', 0) + data.get('completed_task_count', 0) + data.get(
            'in_work_task_count', 0)
        return data


class TaskSprintDetailSerializer(serializers.ModelSerializer):
    expected_result = serializers.ListField()
    author = CachedAppUserSerializer(read_only=True)
    members = CachedAppUserSerializer(many=True)
    projects = WorkgroupNameSerializer(many=True)

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
            'name',
            'author',
            'dead_line',
            'begin_date',
            'created_at',
            'status',
            'finished_date',
            'time_interval',
            'duration',
            'target',
            'expected_result',
            'members',
            'projects',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status == 'completed' and instance.task_count_history:
            data.update(instance.task_count_history)
        else:
            data.update(utils.get_sprint_task_count_data(instance))
        data['task_count'] = data.get('new_task_count', 0) + data.get('completed_task_count', 0) + data.get('in_work_task_count', 0)
        sprint_executed_time = utils.get_sprint_time_tracking(instance)
        sprint_executed_time_sum = sprint_executed_time.aggregate(ex_time_sum=Sum('hours'))['ex_time_sum']
        if sprint_executed_time_sum is None:
            sprint_executed_time_sum = 0
        data['wasted_time'] = sprint_executed_time_sum
        included_members, excluded_members = utils.get_sprint_members_set(instance)
        data['member_count'] = len(included_members | excluded_members)
        return data


class TaskCountSprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('id')
        if instance.status == 'completed' and instance.task_count_history:
            data.update(instance.task_count_history)
        else:
            data.update(utils.get_sprint_task_count_data(instance))
        return data


class TaskSprintReportSerializer(serializers.ModelSerializer):
    excluded = serializers.SerializerMethodField()
    status = TaskStatusModelSerializer()
    time_tracking = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'counter',
            'status',
            'excluded',
            'name',
            'time_tracking',
            # 'operator',
            # 'wasted_time',
        )

    def get_excluded(self, instance):
        sprint = self.context.get('sprint')
        instance_sprint = instance.sprint
        return not (instance_sprint and (instance_sprint == sprint))

    def get_time_tracking(self, instance):
        sprint = self.context.get('sprint',)
        user_id = self.context.get('user_id')
        time_tracking_qs = instance.execution_time.filter(
            is_active=True,
            sprint=sprint,
        )
        if user_id:
            time_tracking_qs = time_tracking_qs.filter(user_id=user_id)
        time_tracking = list(
            time_tracking_qs.values('user').annotate(hours_sum=Sum('hours')).values('user', 'hours_sum',)
        )
        for each in time_tracking:
            each['role'] = self.get_role(instance, each['user'])
            user_id = each['user']
            if user_id:
                user_data = CachedAppUserSerializer(user_id).data
                each['user'] = user_data
        self.context.pop('roles', None)
        return time_tracking

    def get_role(self, instance, user_id) -> str:
        """"Возвращает строку со списком ролей пользователя в задаче"""
        roles = self.context.get('roles')
        if not roles:
            owner = instance.owner_id
            operator = instance.operator_id
            cooperators = list(instance.cooperators.all().values_list('pk', flat=True))
            visors = list(instance.visors.all().values_list('pk', flat=True))
            roles = [
                {
                    'name': 'постановщик',
                    'users': [owner]
                },
                {
                    'name': 'исполнитель',
                    'users': [operator],
                },
                {
                    'name': 'соисполнитель',
                    'users': cooperators,
                },
                {
                    'name': 'наблюдатель',
                    'users': visors,
                },
            ]
            self.context['roles'] = roles
        role_list = []
        for each in roles:
            if user_id in each['users']:
                role_list.append(each['name'])
        role_str = ', '.join(role_list)
        return role_str

    def to_representation(self, instance):
        data = super().to_representation(instance)
        sprint = self.context.get('sprint',)
        hours = instance.execution_time.filter(
            is_active=True,
            sprint=sprint,
        ).aggregate(hours_sum=Sum('hours'))['hours_sum']
        if hours is None:
            hours = 0
        data['hours'] = hours
        return data


# DEPRECATED
class ReportSprintSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()

    # @staticmethod
    # def uncompleted_tasks(instance):
    #     return instance.not_completed_tasks.all().annotate(
    #         completed=Value(False, output_field=BooleanField()))
    #
    # @staticmethod
    # def completed_tasks(instance):
    #     return instance.tasks.all().annotate(completed=Value(True, output_field=BooleanField()))

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
            'name',
            'begin_date',
            'finished_date',
            'author',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # completed_tasks = self.completed_tasks(instance)
        # uncompleted_task = self.uncompleted_tasks(instance)
        # full_tasks_list = completed_tasks | uncompleted_task
        # operator_list = full_tasks_list.prefetch_related('operator__user').values('operator',
        #                                                                           'operator__user__first_name',
        #                                                                           'operator__user__last_name')
        # data_operator_info = []
        # for record in list({v['operator']: v for v in operator_list}.values()):
        #     operator_info = dict()
        #     operator_info['id'] = record['operator']
        #     operator_info['first_name'] = record['operator__user__first_name']
        #     operator_info['last_name'] = record['operator__user__last_name']
        #     operator_info['completed_task_count'] = completed_tasks.filter(operator_id=record['operator']).count()
        #     operator_info['uncompleted_task_count'] = uncompleted_task.filter(operator_id=record['operator']).count()
        #     data_operator_info.append(operator_info)
        # data['operator_list'] = data_operator_info
        # serialized_task_in_sprint = TaskSprintReportSerializer(completed_tasks, many=True).data
        # serialized_tasks_in_sprint_story = TaskSprintReportSerializer(uncompleted_task, many=True).data
        # data['tasks'] = serialized_task_in_sprint + serialized_tasks_in_sprint_story
        # total_time = sprint_tasks_time_executed.aggregate(Sum('hours'))
        # data['total_time'] = total_time['hours__sum']
        # data['completed_task_count'] = completed_tasks.count()
        # data['uncompleted_task_count'] = uncompleted_task.count()
        return data


class ReportTimeSprintSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()

    @staticmethod
    def uncompleted_tasks(instance):
        not_completed_tasks_id = instance.task_sprint_history.all().values_list('task', flat=True)
        not_completed_tasks = models.TaskModel.objects.filter(is_active=True, pk_in=not_completed_tasks_id).annotate(
            completed=Value(False, output_field=BooleanField())
        )
        return not_completed_tasks

    @staticmethod
    def completed_tasks(instance):
        return instance.tasks.all().annotate(completed=Value(True, output_field=BooleanField()))

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        localdate = timezone.localdate()
        datetime_begin = instance.begin_date
        if not datetime_begin:
            return {'execute_time': []}
        date_begin = datetime_begin
        datetime_end = instance.finished_date if instance.finished_date else localdate
        date_end = datetime_end

        all_tasks = utils.get_all_sprint_tasks(instance)
        sprint_tasks_time_executed = models.TaskExecutionTimeModel.objects.filter(is_active=True,
                                                                                  task_id__in=all_tasks,
                                                                                  sprint=instance,
                                                                                  date__gte=date_begin,
                                                                                  date__lte=date_end,
                                                                                  )
        execute_time = sprint_tasks_time_executed.annotate(first_name=F('user__user__first_name'),
                                                           last_name=F('user__user__last_name'),
                                                           )
        execute_time = execute_time.values('user', 'first_name', 'last_name').distinct().annotate(
            wasted_time=Sum('hours'), tasks_count=Count('task', distinct=True))
        data = {'execute_time': execute_time}
        return data


class TaskSprintUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    status = serializers.ReadOnlyField()
    finished_date = serializers.ReadOnlyField()
    expected_result = serializers.ListField(required=False)
    time_interval = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()
    author = AppUserSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    projects = serializers.PrimaryKeyRelatedField(
        many=True,
        required=True,
        allow_empty=False,
        allow_null=False,
        queryset=WorkgroupModel.objects.filter(is_active=True, is_project=True)
    )

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
            'name',
            'status',
            'author',
            'finished_date',
            'dead_line',
            'time_interval',
            'duration',
            'target',
            'expected_result',
            'members',
            'projects',
        )

    def validate_projects(self, projects):
        if projects:
            old_projects = set(self.instance.projects.all())
            new_projects = set(projects) - old_projects
            request = self.context.get('request')
            for each in new_projects:
                if each.is_finished:
                    raise ValidationError(f"Вы не можете добавить проект {each.name}: проект завершен")
                if not each.get_update_permission(request):
                    raise PermissionDenied(f'Вы не можете добавить проект {each.name}: нет доступа')
        return projects

    def to_representation(self, instance):
        return TaskSprintDetailSerializer(instance, context={"request": self.context['request']}).data

    def update(self, instance, validated_data):
        with transaction.atomic():
            sprint = super().update(instance, validated_data)

        return sprint


class TaskSprintUpdateStatusSerializer(serializers.ModelSerializer):
    dead_line = serializers.ReadOnlyField()
    move_tasks_to = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.TaskSprintModel.objects.filter(is_active=True,).exclude(status='completed',)
    )

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'status',
            'dead_line',
            'move_tasks_to',
        )

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status')
        move_tasks_to = validated_data.pop('move_tasks_to', None)
        with transaction.atomic():
            if not old_status == new_status:
                if new_status == 'in_process':
                    # установится в instance.save(), поэтому зануляем
                    instance.dead_line = None
                    instance.begin_date = None
                    instance.status = new_status
                    instance.save()
                if new_status == 'completed':
                    instance.status = new_status
                    instance.task_count_history = utils.get_sprint_task_count_data(instance)
                    instance.save()
                    sprint_tasks = list(instance.tasks.filter(
                        is_active=True
                    ).exclude(
                        status_id='completed'
                    ))
                    if sprint_tasks and move_tasks_to:
                        for each in sprint_tasks:
                            each.sprint = move_tasks_to
                            each.add_sprint_date = timezone.now()
                            each.save(update_fields=('sprint', 'add_sprint_date'),)
                            blockers = each.object_tags.all()
                            if blockers:
                                from tags.serializers import TagModelListSerializer
                                blockers_data = TagModelListSerializer(
                                    blockers,
                                    many=True,
                                    context={'related_object': each.pk}
                                ).data
                            else:
                                blockers_data = None
                            task_sprint_history, created = models.TaskSprintHistoryModel.objects.update_or_create(
                                task=each,
                                sprint=instance,
                                defaults={
                                'moved_to': 'sprint',
                                'moved_to_sprint': move_tasks_to,
                                'for_completed': True,
                                'status': each.status,
                                'add_sprint_date': each.add_sprint_date,
                                'blockers': blockers_data
                                }
                            )
                            models.SprintExpectedResultModel.objects.filter(
                                sprint=move_tasks_to,
                                task=each,
                            ).delete()
                            models.SprintExpectedResultModel.objects.create(
                                sprint=move_tasks_to,
                                task=each,
                            )

                    if sprint_tasks and not move_tasks_to:
                        for each in sprint_tasks:
                            each.sprint = None
                            each.add_sprint_date = None
                            each.save(update_fields=('sprint', 'add_sprint_date'),)
                            blockers = each.object_tags.all()
                            if blockers:
                                from tags.serializers import TagModelListSerializer
                                blockers_data = TagModelListSerializer(
                                    blockers,
                                    many=True,
                                    context={'related_object': each.pk}
                                ).data
                            else:
                                blockers_data = None
                            task_sprint_history, created = models.TaskSprintHistoryModel.objects.update_or_create(
                                task=each,
                                sprint=instance,
                                defaults={
                                    'moved_to': 'backlog',
                                    'for_completed': True,
                                    'status': each.status,
                                    'add_sprint_date': each.add_sprint_date,
                                    'blockers': blockers_data
                                }
                            )
                else:
                    instance.status = new_status
                    instance.save()
        return instance


class TaskSprintCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    status = serializers.ReadOnlyField()
    finished_date = serializers.ReadOnlyField()
    dead_line = serializers.ReadOnlyField()
    expected_result = serializers.ListField(required=False)
    author = AppUserSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    projects = serializers.PrimaryKeyRelatedField(
        many=True,
        required=True,
        allow_empty=False,
        allow_null=False,
        queryset=WorkgroupModel.objects.filter(is_active=True, is_project=True)
    )

    class Meta:
        model = models.TaskSprintModel
        fields = (
            'id',
            'name',
            'dead_line',
            'status',
            'finished_date',
            'duration',
            'target',
            'expected_result',
            'author',
            'members',
            'projects',
        )

    def to_representation(self, instance):
        return TaskSprintDetailSerializer(instance, context={"request": self.context['request']}).data

    def validate_projects(self, projects):
        if projects:
            request = self.context.get('request')
            for each in projects:
                if each.is_finished:
                    raise ValidationError(f"Вы не можете добавить проект {each.name}: проект завершен")
                if not each.get_update_permission(request):
                    raise PermissionDenied(f'Вы не можете добавить проект {each.name}: нет доступа')
        return projects

    def create(self, validated_data):
        members = validated_data.pop('members', None)
        projects = validated_data.pop('projects', None)
        with transaction.atomic():
            sprint = models.TaskSprintModel.objects.create(
                **validated_data,
            )
            if members:
                sprint.members.set(members)
            if projects:
                sprint.projects.set(projects)
        return sprint


class TaskExecutionTimeModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskExecutionTimeModel
        fields = (
            'id',
            'task',
            'user',
            'work_type',
            'description',
            'hours',
            'duration',
            'measure_unit',
            'date',
            'is_result',
            'event_calendar',
            'meeting_section',
        )

    def validate(self, attrs):
        hours_present = 'hours' in attrs
        duration_present = 'duration' in attrs
        if hours_present and duration_present:
            raise ValidationError('Нельзя передавать одновременно hours и duration')
        if hours_present:
            hours_value = attrs.get('hours')
            duration_value = int(Decimal(hours_value) * 3600)
            attrs['duration'] = duration_value
        elif duration_present:
            duration_value = attrs.get('duration')
            hours_value = (Decimal(duration_value) / 3600).quantize(Decimal('0.01'), rounding=ROUND_UP)
            attrs['hours'] = hours_value
        task = attrs.get('task')
        if not task:
            raise ValidationError('Task is required')

        # Если пришли event_calendar или meeting_section, но не указан work_type —
        # подставляем дефолтный вид работ "discussion"
        has_calendar_refs = attrs.get('event_calendar') or attrs.get('meeting_section')
        if has_calendar_refs and not attrs.get('work_type'):
            attrs['work_type'] = models.TaskWorkTypeModel.objects.get(code='discussion')

        obj_user = attrs.get('user')
        if obj_user:
            task_members_id = task.get_member_ids
            if obj_user.pk not in task_members_id:
                raise ValidationError("Пользователь не является участником задачи")
            request = self.context.get('request')
            if request:
                user = getattr(getattr(request, 'user', None), 'profile', None)
                if user and user == obj_user:
                    pass
                else:
                    project = task.project
                    if not project or not project.get_update_permission(request):
                        raise ValidationError('Вы не можете создавать запись для другого пользователя')
        return attrs

    def to_representation(self, instance):
        return TaskExecutionTimeModelListSerializer(instance).data


class TaskExecutionTimeModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskExecutionTimeModel
        fields = (
            'id',
            'user',
            'work_type',
            'description',
            'hours',
            'duration',
            'measure_unit',
            'date',
            'is_result',
            'event_calendar',
            'meeting_section',
        )

    def validate(self, attrs):
        hours_present = 'hours' in attrs
        duration_present = 'duration' in attrs
        if hours_present and duration_present:
            raise ValidationError('Нельзя передавать одновременно hours и duration')
        if hours_present:
            hours_value = attrs.get('hours')
            duration_value = int(Decimal(hours_value) * 3600)
            attrs['duration'] = duration_value
        elif duration_present:
            duration_value = attrs.get('duration')
            hours_value = (Decimal(duration_value) / 3600).quantize(Decimal('0.01'), rounding=ROUND_UP)
            attrs['hours'] = hours_value
        instance = self.instance
        task = instance.task
        if task:
            obj_user = attrs.get('user')
            old_obj_user = instance.user
            if obj_user and not obj_user == old_obj_user:
                task_members_id = task.get_member_ids
                if obj_user.pk not in task_members_id:
                    raise ValidationError("Пользователь не является участником задачи")
                request = self.context.get('request')
                if request:
                    user = getattr(getattr(request, 'user', None), 'profile', None)
                    if user and user == obj_user:
                        pass
                    else:
                        project = task.project
                        if not project or not project.get_update_permission(request):
                            raise ValidationError('Вы не можете создавать запись для другого пользователя')
        return attrs

    def to_representation(self, instance):
        return TaskExecutionTimeModelListSerializer(instance).data


from .utils import get_status_data


class TaskWorkTypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskWorkTypeModel
        fields = (
            'id',
            'code',
            'name',
        )


class TaskIdSerializer(serializers.ModelSerializer):
    """Сериализатор задачи: id, name, counter."""

    class Meta:
        model = models.TaskModel
        fields = ('id', 'name', 'counter')


class TaskExecutionTimeModelListSerializer(serializers.ModelSerializer):
    author = CachedAppUserPreviewSerializer(source='author_id')
    user = CachedAppUserPreviewSerializer(source='user_id')
    work_type = TaskWorkTypeModelSerializer()
    task = TaskIdSerializer()
    measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = models.TaskExecutionTimeModel
        fields = (
            'id',
            'author',
            'is_current',
            'user',
            'work_type',
            'description',
            'hours',
            'duration',
            'measure_unit',
            'date',
            'task',
            'is_result',
            'event_calendar',
            'meeting_section',
        )


class TaskModel1CListSerializer(serializers.ModelSerializer):
    project__name = serializers.SerializerMethodField()
    workgroup__name = serializers.SerializerMethodField()

    def get_project__name(self, instance):
        name = ''
        if instance.project:
            name = instance.project.name
        return name

    def get_workgroup__name(self, instance):
        name = ''
        if instance.workgroup:
            name = instance.workgroup.name
        return name

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'name',
            'project',
            'workgroup',
            'project__name',
            'workgroup__name',
        )


class TaskExecutionTimeModel1CListSerializer(serializers.ModelSerializer):
    task = TaskModel1CListSerializer()
    work_type = TaskWorkTypeModelSerializer()
    created_at = serializers.DateTimeField(format='%Y%m%d%H%M%S')

    class Meta:
        model = models.TaskExecutionTimeModel
        fields = (
            'id',
            'author',
            'user',
            'work_type',
            'description',
            'hours',
            'date',
            'created_at',
            'task',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        parent = instance.task.get_ancestors().filter(from_urv=True).first()

        if parent:
            data['alter_task'] = TaskModel1CListSerializer(parent).data
        else:
            data['alter_task'] = {}

        return data


class TaskStatusTypeModelSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    btn_title = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskStatusTypeModel
        fields = (
            'code',
            'name',
            'color',
            'btn_title',
            'is_open',
            'show_btn',
            'is_complete',
            'depends',
            'progress',
            'can_shipment',
        )

    def get_code(self, instance):
        return instance.task_status.code

    def get_name(self, instance):
        return instance.task_status.name

    def get_color(self, instance):
        return instance.task_status.color

    def get_btn_title(self, instance):
        return instance.task_status.btn_title

    def get_progress(self, instance):
        return instance.task_status.progress


class CachedTaskStatusTypeModelSerializer(serializers.Serializer):

    def to_representation(self, instance):
        lang = get_language()
        data = cache.get(f'CachedTaskStatusTypeModelSerializer_{lang}_{instance}')
        if not data:
            task_type_code, task_status_code = instance.split('__')
            instance_obj = models.TaskStatusTypeModel.objects.filter(task_type_id=task_type_code,
                                                                     task_status_id=task_status_code,).first()
            data = TaskStatusTypeModelSerializer(instance=instance_obj).data
            cache.set(f'CachedTaskStatusTypeModelSerializer_{lang}_{instance}', data)
        return data


class TaskModelSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [search_indexes.TaskIndex]
        fields = (
            'content'
        )

    def to_representation(self, instance):
        data = ListTaskSerializer(instance.object).data
        return data


class TaskBudgetModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskBudgetModel
        fields = (
            'id',
            'task',
            'cost_item',
            'measure_unit',
            'description',
            'amount',
            'quantity',
        )

    def validate(self, attr):
        task = attr.get('task')
        if not task:
            raise ValidationError()
        user = self.context['request'].user.profile
        if not user == task.owner:
            raise PermissionDenied("User is not task owner.")
        return attr

    def to_representation(self, instance):
        return TaskBudgetModelListSerializer(instance).data


class TaskBudgetModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskBudgetModel
        fields = (
            'id',
            'cost_item',
            'measure_unit',
            'description',
            'amount',
            'quantity',
        )

    def to_representation(self, instance):
        return TaskBudgetModelListSerializer(instance).data


class TaskBudgetModelListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    cost_item = BaseCatalogRetrieveSerializer()
    task = ShortTaskSerializer()
    measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = models.TaskBudgetModel
        fields = (
            'id',
            'author',
            'cost_item',
            'measure_unit',
            'description',
            'amount',
            'quantity',
            'task',
        )


def validate_interest_need(task, goods, request):
    if not task:
        raise ValidationError({'task': 'Интерес не указан.'})
    if task.task_type_id != 'interest':
        raise ValidationError({'task': 'Потребности можно добавлять только к интересу.'})
    if request and not task.get_update_permission(request):
        raise PermissionDenied('User cannot update this interest.')
    if goods and task.organization_id and goods.contractor_id != task.organization_id:
        raise ValidationError({'goods': 'Номенклатура должна относиться к организации интереса.'})
    return task


class TaskInterestNeedCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskInterestNeedModel
        fields = (
            'id',
            'task',
            'name',
            'goods',
            'quantity',
            'price',
            'comment',
        )
        extra_kwargs = {
            'goods': {'required': False, 'allow_null': True},
            'name': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        validate_interest_need(
            attrs.get('task'),
            attrs.get('goods'),
            self.context.get('request')
        )
        return attrs

    def to_representation(self, instance):
        return TaskInterestNeedListSerializer(instance, context=self.context).data


class TaskInterestNeedUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskInterestNeedModel
        fields = (
            'id',
            'name',
            'goods',
            'quantity',
            'price',
            'comment',
        )
        extra_kwargs = {
            'goods': {'required': False, 'allow_null': True},
            'name': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        validate_interest_need(
            self.instance.task,
            attrs.get('goods', self.instance.goods),
            self.context.get('request')
        )
        return attrs

    def to_representation(self, instance):
        return TaskInterestNeedListSerializer(instance, context=self.context).data


class TaskInterestNeedListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    goods = AppNomenclatureSerializer()
    measure_unit = MeasureUnitListSerializer()

    class Meta:
        model = models.TaskInterestNeedModel
        fields = (
            'id',
            'author',
            'goods',
            'name',
            'name_short',
            'article_number',
            'quantity',
            'price',
            'amount',
            'measure_unit',
            'comment',
            'task',
        )


class TaskDifficultyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskDifficulty
        fields = (
            'id',
            'task',
            'criterion',
            'score',
        )

    def validate(self, attr):
        task = attr.get('task')
        if not task:
            raise ValidationError()
        user = self.context['request'].user.profile
        if not user == task.owner:
            raise PermissionDenied()
        return attr

    def to_representation(self, instance):
        return TaskDifficultyListSerializer(instance).data


class TaskDifficultyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskDifficulty
        fields = (
            'id',
            'criterion',
            'score',
        )

    def to_representation(self, instance):
        return TaskDifficultyListSerializer(instance).data


class TaskDifficultyListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    criterion = BaseCatalogRetrieveSerializer()
    task = ShortTaskSerializer()

    class Meta:
        model = models.TaskDifficulty
        fields = (
            'id',
            'author',
            'criterion',
            'score',
            'task',
        )


class TaskAnalyticsSerializer(serializers.ModelSerializer):
    execution_time_sum = serializers.SerializerMethodField()
    budget_sum = serializers.SerializerMethodField()
    budget = serializers.SerializerMethodField()
    difficulty_avg = serializers.SerializerMethodField()
    operator = AppUserSerializer()
    owner = AppUserSerializer()
    description = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'counter',
            'name',
            'operator',
            'owner',
            'created_at',
            'finished_date',
            'execution_time_sum',
            'budget_sum',
            'budget',
            'difficulty_avg',
            'description',
        )

    def get_execution_time_sum(self, instance):
        value = serializers.DecimalField(max_digits=13, decimal_places=1).to_representation(
            instance.execution_time.filter(is_active=True).aggregate(Sum('hours'))['hours__sum'])
        if not value:
            value = '0.0'
        return value

    def get_budget_sum(self, instance):
        value = serializers.DecimalField(max_digits=13, decimal_places=2).to_representation(
            instance.task_budgets.filter(is_active=True).aggregate(Sum('amount'))['amount__sum'])
        if not value:
            value = '0.00'
        return value

    def get_budget(self, instance):
        data = {
            'sum': self.get_budget_sum(instance),
            'currency': AppCurrencySerializer(get_default_currency_object()).data
        }
        return data

    def get_difficulty_avg(self, instance):
        value = serializers.DecimalField(max_digits=13, decimal_places=3).to_representation(
            instance.difficulty.filter(is_active=True).aggregate(Avg('score'))['score__avg'])
        if not value:
            value = '0.000'
        return value

    def get_description(self, instance):
        return utils.get_description_text(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['in_favorites'] = get_in_favorites(instance)
        return data


class TaskSprintSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [search_indexes.TaskSprintIndex]
        fields = (
            'content'
        )

    def to_representation(self, instance):
        data = TaskSprintDetailSerializer(instance.object).data
        data['s_dead_line'] = instance.dead_line
        return data


class TaskDeliveryPointSortSerializer(serializers.ModelSerializer):
    delivery_points = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.TaskDeliveryPointModel.objects.all(),
        source='task_delivery_points'
    )

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'delivery_points'
        )

    def update(self, instance, validated_data):
        delivery_points = validated_data.get('task_delivery_points', [])
        sort = 10
        for each in delivery_points:
            each.sort = sort
            sort += 10
        instance.task_delivery_points.bulk_update(delivery_points, ('sort',))
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['update_fields'] = {
            'delivery_points': TaskDeliveryPointSerializer(
                instance.task_delivery_points.all().order_by('sort', 'created_at'),
                many=True,
            ).data
        }
        return data


class TaskDeliveryPointCreateSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=GoodsOrderModel.objects.filter(is_active=True),
        required=True,
        allow_null=True,
    )
    start_delivery_point = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryPointModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    start_front_id = serializers.UUIDField(allow_null=True, required=False)
    end_front_id = serializers.UUIDField(allow_null=True, required=False)

    class Meta:
        model = models.TaskDeliveryPointModel
        fields = (
            'id',
            'order',
            'start_delivery_point',
            'delivery_point',
            'start_front_id',
            'end_front_id',
        )

    def validate(self, attrs):
        order = attrs.get('order')
        if not order:
            raise ValidationError('Order does not exist.')
        delivery_point = attrs.get('delivery_point')
        if order.task_delivery_point or order.start_task_delivery_point:
            raise ValidationError('Order have a task delivery point.')
        order_delivery_point = order.delivery_point
        if not delivery_point and not order_delivery_point:
            raise ValidationError('No delivery point.')
        if not delivery_point and order_delivery_point:
            # Внимание! Меняем атрибут в валидаторе. Если не прописана точка доставки, берем из заказа.
            attrs['delivery_point'] = order_delivery_point
        start_delivery_point = attrs.get('start_delivery_point')
        start_order_delivery_point = getattr(getattr(order, 'warehouse', None), 'delivery_point', None)
        if not start_order_delivery_point and not start_delivery_point:
            raise ValidationError('No start delivery point.')
        if not start_delivery_point and start_order_delivery_point:
            # Тут тоже самое.
            attrs['start_delivery_point'] = start_order_delivery_point
        return attrs

    def create(self, validated_data):
        task = self.context.get('task')
        order = validated_data.pop('order', None)
        start_delivery_point = validated_data.pop('start_delivery_point', None)
        start_front_id = validated_data.pop('start_front_id', None)
        end_front_id = validated_data.pop('end_front_id', None)
        with transaction.atomic():
            task_delivery_point = models.TaskDeliveryPointModel.objects.create(
                task=task,
                front_id=end_front_id,
                sort=0,
                **validated_data)
            validated_data.pop('delivery_point')
            start_task_delivery_point = models.TaskDeliveryPointModel.objects.create(
                task=task,
                sort=0,
                is_start=True,
                delivery_point=start_delivery_point,
                front_id=start_front_id,
                **validated_data
            )
            if order:
                task_delivery_point.goods_orders.set((order,))
                start_task_delivery_point.start_goods_orders.set((order,))
            user = get_current_authenticated_profile()
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_order_user_about_start_order, task, order, user
                )
            )
            if task.status_id == 'in_transit':
                transaction.on_commit(
                    lambda: async_task(
                        notifications.notify_about_order_in_transit(task, order)
                    )
                )
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_driver_about_start_order, task, order, user
                )
            )
        return task_delivery_point

    def to_representation(self, instance):
        task = self.context.get('task')
        data = {
            "task": ListTaskSerializer(task).data,
            "delivery_points": TaskDeliveryPointSerializer(
                task.task_delivery_points.all().order_by('sort', 'created_at'),
                many=True
            ).data
        }
        return data


class TaskDeliveryPointDeleteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=models.TaskDeliveryPointModel.objects.filter(is_active=True),
                                            allow_null=False,
                                            required=True)

    def validate(self, attrs):
        instance = attrs.get('id')
        task = self.context.get('task')
        if not instance.task == task:
            raise ValidationError('Incorrect delivery_points.')
        return attrs

    def to_representation(self, instance):
        return dict()


class TaskDeliveryPointDeleteOrdersSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=GoodsOrderModel.objects.filter(is_active=True),
                                            allow_null=False,
                                            required=True)

    def validate(self, attrs):
        instance = attrs.get('id')
        task = self.context.get('task')
        if not (
                instance.task_delivery_point
                and instance.task_delivery_point.task
                and instance.task_delivery_point.task == task
        ):
            raise ValidationError('Incorrect order.')
        return attrs

    def to_representation(self, instance):
        return dict()


class TaskDeliveryPointUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskDeliveryPointModel
        fields = (
            'id',
            'sort',
        )


class DriverSerializer(AppUserSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.operator_tasks.all():
            data['work_status'] = {"name": "Занят", "code": "busy", "color": "purple"}
        else:
            data['work_status'] = {"name": "Свободен", "code": "not_busy", "color": "geekblue"}
        return data


class TaskLoadingGoodsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskLoadingGoodsModel
        fields = (
            'id',
            'task',
            'goods',
            'warehouse',
            'quantity',
            'amount_paid',
        )

    def validate_task(self, data):
        user = self.context.get('user')
        operator = data.operator
        if user and data.operator and (user == operator):
            return data
        else:
            raise ValidationError('User is not operator.')

    def create(self, validated_data):
        instance = models.TaskLoadingGoodsModel.objects.create(
            driver=self.context.get('user'),
            **validated_data,
        )
        return instance


class StageMilestoneAboutSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskModel
        fields = (
            'id',
            'name',
            'dead_line',
            'status'
        )

    def get_status(self, instance):
        return utils.get_status_data(instance)


class TaskCooperatorSerializer(serializers.ModelSerializer):
    """Сериализатор соисполнителей. Со статусом задачи соисполнителя."""
    user = AppUserSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = models.TaskCooperator
        fields = [
            'id',
            'user',
            'status',
        ]

    def get_status(self, instance):
        return utils.get_cooperator_status_data(instance)


class TaskCooperatorShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор вывода соисполнителей в списке задач.
    Без статуса задачи соисполнителя. Для пользователя использует кэширующий сериализатор."""
    user = CachedAppUserSerializer(read_only=True, source='user_id')

    class Meta:
        model = models.TaskCooperator
        fields = [
            'id',
            'user',
        ]


class KeyResultTaskSerializer(ListTaskSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        data['has_view_permission'] = instance.get_detail_permission(request) if request else False
        return data


