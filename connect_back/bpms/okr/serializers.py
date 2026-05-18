import uuid
from datetime import datetime

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from django.db import transaction
from django.utils import timezone

from common.catalogs.serializers import ContractorDepartmentShortListSerializer, ContractorModelByINNSerializer
from users.serializers import CachedAppUserSerializer, CachedAppUserPreviewSerializer
from users.models import ProfileModel
from bpms.workgroups.models import WorkgroupModel
from bpms.tasks.serializers import CreateTaskSerializer, TaskSprintCreateSerializer, KeyResultTaskSerializer
from . import models
from .utils import calculate_next_notification_run


# Сериализаторы вспомогательных моделей
class ValueEffortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ValueEffortsModel
        fields = (
            'id',
            'name',
            'code',
            'color',
            'hex_color',
        )


class ObjectiveStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ObjectiveStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
            'hex_color',
            'is_closed',
        )


class NotificationFrequencySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NotificationFrequencyModel
        fields = (
            'id',
            'name',
            'code',
            'description',
            'cron',)


class InitiativesRelatedObjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InitiativesRelatedObjectType
        fields = (
            'id',
            'name',
            'code',
            'model_label',
            )


class KeyResultMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KeyResultMetricsModel
        fields = (
            'id',
            'name',
            'description',
            'contractor',
            )

# Сериализаторы модели MissionModel
class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MissionModel
        fields = (
            'id',
            'updated_at',
            'mission',
            'organization',
            )

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            try:
                mission = models.MissionModel.objects.get(is_active=True, organization=instance.organization)
            except models.MissionModel.MultipleObjectsReturned:
                raise drf_exceptions.ValidationError('У компании может быть только одна миссия.')
        return instance


# Сериализаторы модели ObjectivesModel
class ObjectivesModelCreateSerializer(serializers.ModelSerializer):
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ObjectivesModel
        fields = (
            'id',
            'parent',
            'organization',
            'department',
            'owner',
            'operator',
            'objective',
            'date_start',
            'date_end',
            'is_public',
            'visors',
            'value_efforts',
            'status',
            'notification',
            'metadata',
        )

    def update_key_results(self, objective, key_results):
        for key_result in key_results:
            key_result['objective'] = objective
            serializer = KeyResultsModelCreateSerializer(data=key_result)
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def create(self, validated_data):
        key_results = self.initial_data.pop('key_results', None)
        visors = validated_data.pop('visors', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            instance.notify_at = calculate_next_notification_run(
                instance.notification.code,
                instance.notification.cron,
                instance.date_start,
                instance.date_end)
            instance.save(update_fields=('notify_at',))
            if visors:
                instance.visors.set(visors)
            if key_results:
                self.update_key_results(instance, key_results)
        return instance
    
    def to_representation(self, instance):
        return ObjectivesModelListSerializer(instance, context={'request': self.context.get('request')}).data


class ObjectivesModelUpdateSerializer(serializers.ModelSerializer):
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ObjectivesModel
        fields = (
            'id',
            'parent',
            'organization',
            'department',
            'owner',
            'operator',
            'objective',
            'date_start',
            'date_end',
            'is_public',
            'visors',
            'value_efforts',
            'status',
            'notification',
            'notify_at',
            'metadata',
        )

    def update_key_results(self, objective, key_results):
        existing_key_result_ids = objective.key_results.filter(is_active=True).values_list('id', flat=True)
        current_key_result_ids = [uuid.UUID(item["id"]) for item in key_results if "id" in item]
        deleted_key_result_ids = list(set(existing_key_result_ids) - set(current_key_result_ids))
        if deleted_key_result_ids:
            models.KeyResultsModel.objects.filter(pk__in=deleted_key_result_ids).update(is_active=False, deleted_at=timezone.now())
        for key_result in key_results:
            # Если id есть, то обновляем ключевой результат
            if 'id' in key_result.keys():
                instance = models.KeyResultsModel.objects.get(pk=key_result['id'])
                serializer = KeyResultsModelUpdateSerializer(instance=instance, data=key_result)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            # Если id еще нет, то создаем ключевой результат
            else:
                key_result['objective'] = objective
                serializer = KeyResultsModelCreateSerializer(data=key_result)
                serializer.is_valid(raise_exception=True)
                serializer.save()

    def adjust_key_result_dates(self, objective: models.ObjectivesModel):
        """Если были указаны даты в ключевом результате, при смене дат периода 
        цели меняет даты периодов ключевых результатов"""
        key_results = objective.key_results.filter(is_active=True)

        for key_result in key_results:
            if key_result.date_start and objective.date_start:
                key_result.date_start = objective.date_start
            if key_result.date_end and objective.date_end:
                key_result.date_end = objective.date_end

        models.KeyResultsModel.objects.bulk_update(
            key_results,
            ('date_start', 'date_end')
        )
        return

    def update(self, instance, validated_data):
        key_results = self.initial_data.pop('key_results', None)
        visors = validated_data.pop('visors', None)
        with transaction.atomic():
            old_notification_id = instance.notification_id
            old_date_start = instance.date_start
            old_date_end = instance.date_end
            instance = super().update(instance, validated_data)
            new_notification_id = instance.notification_id
            new_date_start = instance.date_start
            new_date_end = instance.date_end
            validateDates = (new_date_start != old_date_start or old_date_end != new_date_end)
            if (new_notification_id != old_notification_id
                or new_date_start != old_date_start
                or old_date_end != new_date_end):
                instance.notify_at = calculate_next_notification_run(
                    instance.notification.code,
                    instance.notification.cron,
                    instance.date_start,
                    instance.date_end)
                instance.save(update_fields=('notify_at',))
            if visors is not None:
                instance.visors.set(visors)
            if key_results is not None:
                self.update_key_results(instance, key_results)
            if validateDates:
                self.adjust_key_result_dates(instance)
        return instance

    def to_representation(self, instance):
        return ObjectivesModelListSerializer(instance, context={'request': self.context.get('request')}).data


class ObjectivesModelListSerializer(serializers.ModelSerializer):
    department = ContractorDepartmentShortListSerializer()
    has_retrospective = serializers.SerializerMethodField()
    notification = NotificationFrequencySerializer()
    operator = CachedAppUserSerializer(source='operator_id')
    organization = ContractorModelByINNSerializer()
    owner = CachedAppUserSerializer(source='owner_id')
    progress = serializers.SerializerMethodField()
    quarter = serializers.IntegerField(source='date_end_quarter', read_only=True)
    status = ObjectiveStatusSerializer()
    value_efforts = ValueEffortSerializer()
    visors = CachedAppUserPreviewSerializer(many=True)

    class Meta:
        model = models.ObjectivesModel
        fields = (
            'id',
            'date_end',
            'date_start',
            'department',
            'has_retrospective',
            'is_public',
            'notification',
            'notify_at',
            'objective',
            'operator',
            'organization',
            'owner',
            'parent',
            'progress',
            'quarter',
            'status',
            'value_efforts',
            'visors',
        )

    def get_has_retrospective(self, obj):
        return obj.related_retrospectives.filter(is_active=True).exists()

    def get_progress(self, obj):
        """Возвращает прогресс как число от 0 до 1."""
        if obj.progress is not None:
            return obj.progress / 100
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        actions = dict()
        request = self.context.get('request')
        user_id = request.user.profile.pk
        if request:
            if 'create_okr_contractors' in self.context:
                create_okr_contractors = self.context.get('create_okr_contractors')
                check_contractor_permission = instance.organization_id in create_okr_contractors
                update_permission = ((instance.is_public and check_contractor_permission) or
                                    (not instance.is_public and check_contractor_permission and instance.author_id==user_id))
            else:
                update_permission = instance.get_update_permission(request)
            if update_permission:
                actions['edit'] = True
                has_active_children = any(child.is_active for child in instance.children.all())
                actions['delete'] = not has_active_children
            actions['update_key_results'] = (update_permission or
                                             (instance.is_public and instance.owner_id==user_id) or
                                             (instance.is_public and instance.operator_id==user_id))
        data['actions'] = actions
        return data


class ObjectivesModelNotifySerializer(serializers.ModelSerializer):
    """Сериализатор цели для создания уведомлений о необходимости обновить цель.
    Нужны только поля id и название цели."""

    class Meta:
        model = models.ObjectivesModel
        fields = (
            'id',
            'objective',
        )


class ObjectivesModelShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор целей. Для выпадающего списка."""

    class Meta:
        model = models.ObjectivesModel
        fields = (
            'id',
            'objective',
        )


class ObjectivesModelDetailSerializer(serializers.ModelSerializer):
    department = ContractorDepartmentShortListSerializer()
    owner = CachedAppUserSerializer(source='owner_id')
    operator = CachedAppUserSerializer(source='operator_id')
    visors = CachedAppUserPreviewSerializer(many=True)
    value_efforts = ValueEffortSerializer()
    status = ObjectiveStatusSerializer()
    notification = NotificationFrequencySerializer()
    parent = ObjectivesModelShortSerializer()
    organization = ContractorModelByINNSerializer()
    quarter = serializers.IntegerField(source='date_end_quarter', read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = models.ObjectivesModel
        fields = (
            'id',
            'parent',
            'organization',
            'department',
            'owner',
            'operator',
            'objective',
            'date_start',
            'date_end',
            'is_public',
            'visors',
            'value_efforts',
            'status',
            'notification',
            'notify_at',
            'metadata',
            'progress',
            'quarter',
        )

    def get_progress(self, obj):
        """Возвращает прогресс как число от 0 до 1."""
        if obj.progress is not None:
            return obj.progress / 100
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        actions = dict()
        request = self.context.get('request')
        if request:
            update_permission = instance.get_update_permission(request)
            if update_permission:
                actions['edit'] = True
                has_active_children = any(child.is_active for child in instance.children.all())
                actions['delete'] = not has_active_children

            user_id = request.user.profile.pk
            actions['update_key_results'] = (update_permission or
                                             (instance.is_public and instance.owner_id==user_id) or
                                             (instance.is_public and instance.operator_id==user_id))

            key_results = instance.key_results.filter(is_active=True).select_related('metrics')
            data['key_results'] = KeyResultsModelDetailSerializer(key_results, many=True, context={
                'request': self.context.get('request'),
                'update_permission': actions['update_key_results']
                }).data
        data['actions'] = actions
        return data


# Сериализаторы модели KeyResultsModel
class KeyResultsModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KeyResultsModel
        fields = (
            'id',
            'objective',
            'description',
            'operator',
            'metrics',
            'base',
            'plan',
            'fact',
            'date_start',
            'date_end',
        )

    def to_representation(self, instance):
        request = self.context.get('request')
        update_permission = instance.get_update_permission(request)
        user_id = request.user.profile.pk
        return KeyResultsModelDetailSerializer(instance, context={
                'request': request,
                'update_permission': (update_permission or
                                      (instance.is_public and instance.owner_id == user_id) or
                                      (instance.is_public and instance.operator_id == user_id))
                }).data


class KeyResultsModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KeyResultsModel
        fields = (
            'id',
            'description',
            'operator',
            'metrics',
            'base',
            'plan',
            'fact',
            'date_start',
            'date_end',
        )

    def to_representation(self, instance):
        return KeyResultsModelListSerializer(instance, context={'request': self.context.get('request')}).data



class KeyResultsShortSerializer(serializers.ModelSerializer):
    objective = ObjectivesModelShortSerializer()
    
    class Meta:
        model = models.KeyResultsModel
        fields = (
            'id',
            'description',
            'objective'
        )


class KeyResultsModelListSerializer(serializers.ModelSerializer):
    operator = CachedAppUserSerializer(source='operator_id')
    metrics = KeyResultMetricsSerializer()
    quarter = serializers.IntegerField(source='date_end_quarter', read_only=True)
    progress = serializers.SerializerMethodField()
    tasks = KeyResultTaskSerializer(many=True, read_only=True)

    class Meta:
        model = models.KeyResultsModel
        fields = (
            'id',
            'base',
            'date_end',
            'date_start',
            'description',
            'fact',
            'metrics',
            'objective',
            'operator',
            'plan',
            'progress',
            'quarter',
            'tasks'
        )

    def get_progress(self, obj):
        """Возвращает прогресс как число от 0 до 1."""
        if obj.progress is not None:
            return obj.progress / 100
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        actions = dict()
        request = self.context.get('request')
        if request:
            if 'update_permission' in self.context:
                update_permission = self.context['update_permission']
            else:
                update_permission = instance.get_update_permission(request)
            if update_permission:
                actions['edit'] = True
                actions['delete'] = True
            user_id = request.user.profile.pk
            actions['update_initiatives'] = update_permission or instance.operator_id==user_id

            # initiatives = instance.initiatives.filter(is_active=True)
            # data['initiatives'] = InitiativesModelDetailSerializer(initiatives, many=True, context={
            #     'request': self.context.get('request'),
            #     'update_permission': actions['update_initiatives']
            #     }).data

        data['actions'] = actions
        return data


class KeyResultsModelDetailSerializer(serializers.ModelSerializer):
    operator = CachedAppUserSerializer(source='operator_id')
    metrics = KeyResultMetricsSerializer()
    quarter = serializers.IntegerField(source='date_end_quarter', read_only=True)
    progress = serializers.SerializerMethodField()
    tasks = KeyResultTaskSerializer(many=True, read_only=True)

    class Meta:
        model = models.KeyResultsModel
        fields = (
            'id',
            'objective',
            'description',
            'operator',
            'metrics',
            'base',
            'plan',
            'fact',
            'date_start',
            'date_end',
            'progress',
            'quarter',
            'tasks',
        )

    def get_progress(self, obj):
        """Возвращает прогресс как число от 0 до 1."""
        if obj.progress is not None:
            return obj.progress / 100
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        actions = dict()
        request = self.context.get('request')
        if request:
            if 'update_permission' in self.context:
                update_permission = self.context['update_permission']
            else:
                update_permission = instance.get_update_permission(request)
            if update_permission:
                actions['edit'] = update_permission
                actions['delete'] = update_permission
            user_id = request.user.profile.pk
            actions['update_initiatives'] = update_permission or instance.operator_id==user_id
        data['actions'] = actions
        return data


class RelatedObjectCreateMixin:
    """
    Миксин с методами для создания связанных объектов
    (задача, этап, веха, спринт) в сериализаторах InitiativesModel.
    """
    def get_key_result(self, validated_data, instance=None):
        # Пытаемся взять key_result из validated_data, иначе из instance
        key_result = validated_data.get('key_result')
        if not key_result and instance:
            key_result = getattr(instance, 'key_result', None)
        if not key_result:
            raise drf_exceptions.ValidationError("key_result не найден в данных или экземпляре.")
        return key_result

    def create_task(self, validated_data, instance=None):
        key_result = self.get_key_result(validated_data, instance)
        data = {}
        date_start = validated_data.get('date_start')
        date_end = validated_data.get('date_end')
        data['date_start_plan'] = datetime.combine(date_start, datetime.min.time()) if date_start else None
        data['dead_line'] = datetime.combine(date_end, datetime.min.time()) if date_end else None
        data['organization'] = key_result.objective.organization_id
        data['name'] = validated_data.get('title')
        data['description'] = validated_data.get('description', None)
        data['task_type'] = self.initial_data.get('related_object_type')
        data['operator'] = validated_data.get('operator', None)
        data['project'] = validated_data.get('project', None)
        serializer = CreateTaskSerializer(data=data, context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def create_stage(self, validated_data, instance=None):
        if not validated_data.get('project', None):
            raise drf_exceptions.ValidationError('Для создания этапа необходимо указать проект.')
        key_result = self.get_key_result(validated_data, instance)
        data = {}
        date_start = validated_data.get('date_start')
        date_end = validated_data.get('date_end')
        data['date_start_plan'] = datetime.combine(date_start, datetime.min.time()) if date_start else None
        data['dead_line'] = datetime.combine(date_end, datetime.min.time()) if date_end else None
        data['organization'] = key_result.objective.organization_id
        data['name'] = validated_data.get('title')
        data['description'] = validated_data.get('description', None)
        data['task_type'] = self.initial_data.get('related_object_type')
        data['operator'] = validated_data.get('operator', None)
        data['project'] = validated_data.get('project')
        serializer = CreateTaskSerializer(data=data, context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def create_milestone(self, validated_data, instance=None):
        if not validated_data.get('project', None):
            raise drf_exceptions.ValidationError('Для создания вехи необходимо указать проект.')
        key_result = self.get_key_result(validated_data, instance)
        data = {}
        date_end = validated_data.get('date_end')
        data['date_start_plan'] = datetime.combine(date_end, datetime.min.time()) if date_end else None
        data['dead_line'] = datetime.combine(date_end, datetime.min.time()) if date_end else None
        data['organization'] = key_result.objective.organization_id
        data['name'] = validated_data.get('title')
        data['description'] = validated_data.get('description', None)
        data['task_type'] = self.initial_data.get('related_object_type')
        data['operator'] = validated_data.get('operator', None)
        data['project'] = validated_data.get('project')
        serializer = CreateTaskSerializer(data=data, context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def create_sprint(self, validated_data, instance=None):
        if not validated_data.get('projects', None):
            raise drf_exceptions.ValidationError('Для создания спринта необходимо указать список проектов.')
        data = {}
        data['name'] = validated_data.get('title')
        data['target'] = validated_data.get('description', None)
        data['projects'] = validated_data.get('projects', None)
        serializer = TaskSprintCreateSerializer(
            data=data,
            context=self.context
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()


# Сериализаторы модели InitiativesModel
class InitiativesModelCreateSerializer(RelatedObjectCreateMixin, serializers.ModelSerializer):
    date_start = serializers.DateField(required=False, allow_null=True)
    date_end = serializers.DateField(required=False, allow_null=True)
    create_related_object = serializers.BooleanField(required=False, write_only=True)
    project = serializers.PrimaryKeyRelatedField(
        many=False,
        required=False,
        write_only=True,
        queryset=WorkgroupModel.objects.filter(is_active=True, is_project=True)
    )
    projects = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        write_only=True,
        queryset=WorkgroupModel.objects.filter(is_active=True, is_project=True)
    )

    class Meta:
        model = models.InitiativesModel
        fields = (
            'id',
            'key_result',
            'related_object_type',
            'related_object',
            'title',
            'description',
            'operator',
            'date_start',
            'date_end',
            # поля для создание связанного объекта
            'create_related_object',
            'project',
            'projects'
        )

    # def validate(self, attrs):
    #     related_object_type = self.initial_data.get('related_object_type')

    #     # Только если related_object_type передан и не равен 'sprint'
    #     if related_object_type and related_object_type != 'sprint':
    #         if not attrs.get('date_start'):
    #             raise serializers.ValidationError({
    #                 'date_start': 'Это поле обязательно для выбранного типа объекта.'
    #             })
    #         if not attrs.get('date_end'):
    #             raise serializers.ValidationError({
    #                 'date_end': 'Это поле обязательно для выбранного типа объекта.'
    #             })
    #     return super().validate(attrs)


    def create(self, validated_data):
        create_related_object = validated_data.pop('create_related_object', False)
        with transaction.atomic():
            if create_related_object:
                create_methods = {
                    'task': self.create_task,
                    'stage': self.create_stage,
                    'milestone': self.create_milestone,
                    'sprint': self.create_sprint,
                }
                related_object_type = self.initial_data.get('related_object_type')
                create_method = create_methods.get(related_object_type)
                if create_method:
                    related_object = create_method(validated_data)
                else:
                    raise ValueError(f"Неизвестный related_object_type: {related_object_type}")
                validated_data['related_object'] = related_object # Связываем инициативу с только что созданным объектом
                validated_data.pop('project', None) # убираем из validated_data поля, которые не относятся к InitiativesModel
                validated_data.pop('projects', None)
            instance = super().create(validated_data)
        return instance


class InitiativesModelUpdateSerializer(RelatedObjectCreateMixin, serializers.ModelSerializer):
    date_start = serializers.DateField(required=False, allow_null=True)
    date_end = serializers.DateField(required=False, allow_null=True)
    create_related_object = serializers.BooleanField(required=False, write_only=True)
    project = serializers.PrimaryKeyRelatedField(
        many=False,
        required=False,
        write_only=True,
        queryset=WorkgroupModel.objects.filter(is_active=True, is_project=True)
    )
    projects = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        write_only=True,
        queryset=WorkgroupModel.objects.filter(is_active=True, is_project=True)
    )

    class Meta:
        model = models.InitiativesModel
        fields = (
            'id',
            'key_result',
            'related_object_type',
            'related_object',
            'title',
            'description',
            'operator',
            'date_start',
            'date_end',
            # поля для создание связанного объекта
            'create_related_object',
            'project',
            'projects'
        )
        read_only_fields = ('id', 'key_result')

    def validate(self, attrs):
        related_object_type = self.initial_data.get('related_object_type')

        # Только если related_object_type передан и не равен 'sprint'
        if related_object_type and related_object_type != 'sprint':
            if not attrs.get('date_start'):
                raise serializers.ValidationError({
                    'date_start': 'Это поле обязательно для выбранного типа объекта.'
                })
            if not attrs.get('date_end'):
                raise serializers.ValidationError({
                    'date_end': 'Это поле обязательно для выбранного типа объекта.'
                })
        return super().validate(attrs)
    
    def update(self, instance, validated_data):
        create_related_object = validated_data.pop('create_related_object', False)
        with transaction.atomic():
            if create_related_object:
                create_methods = {
                    'task': self.create_task,
                    'stage': self.create_stage,
                    'milestone': self.create_milestone,
                    'sprint': self.create_sprint,
                }
                related_object_type = self.initial_data.get('related_object_type')
                create_method = create_methods.get(related_object_type)
                if create_method:
                    related_object = create_method(validated_data, instance=instance)
                else:
                    raise ValueError(f"Неизвестный related_object_type: {related_object_type}")
                validated_data['related_object'] = related_object
                validated_data.pop('project', None)
                validated_data.pop('projects', None)
            return super().update(instance, validated_data)


class InitiativesModelListSerializer(serializers.ModelSerializer):
    operator = CachedAppUserSerializer(source='operator_id', read_only=True)
    related_object_type = InitiativesRelatedObjectTypeSerializer(read_only=True)

    class Meta:
        model = models.InitiativesModel
        fields = (
            'id',
            'key_result',
            'related_object_type',
            'related_object',
            'title',
            'description',
            'operator',
            'date_start',
            'date_end',
            'is_completed',
        )
        read_only_fields = fields


class InitiativesModelDetailSerializer(serializers.ModelSerializer):
    operator = CachedAppUserSerializer(source='operator_id', read_only=True)
    related_object_type = InitiativesRelatedObjectTypeSerializer(read_only=True)

    class Meta:
        model = models.InitiativesModel
        fields = (
            'id',
            'key_result',
            'related_object_type',
            'related_object',
            'title',
            'description',
            'operator',
            'date_start',
            'date_end',
            'is_completed',
        )
        read_only_fields = fields 

    def to_representation(self, instance):
        data = super().to_representation(instance)

        actions = dict()
        request = self.context.get('request')
        update_permission = self.context.get('update_permission')
        if request and update_permission:
            actions['edit'] = True
            actions['delete'] = True
        data['actions'] = actions
        return data


class InitiativesModelCompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InitiativesModel
        fields = (
            'id',
            'is_completed',
        )