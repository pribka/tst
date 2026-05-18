from django.db import transaction, IntegrityError
from django.db.models import Count
from django.core.exceptions import ValidationError
from rest_framework import serializers, exceptions as drf_exceptions


from users.serializers import CachedAppUserSerializer
from users.models import ProfileModel
from bpms.tasks.serializers import TaskWorkTypeModelSerializer, ShortTaskSerializer
from bpms.tasks.models import TaskModel

from . import models, utils


class PersonalPlaneStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PersonalPlaneStatusModel
        fields = (
            'id',
            'name',
            'code',
        )


class PlaneItemTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskModel
        fields = (
            'id',
            'name',
            'counter',
        )


class PersonalPlaneItemListSerializer(serializers.ModelSerializer):
    work_type = TaskWorkTypeModelSerializer()
    task = PlaneItemTaskSerializer()

    class Meta:
        model = models.PersonalPlaneItemModel
        fields = (
            'id',
            'task',
            'description',
            'work_type',
            'duration_plane',
            'duration_fact',
            'is_result',
        )


class PersonalPlaneItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PersonalPlaneItemModel
        fields = (
            'id',
            'plane',
            'task',
            'description',
            'work_type',
            'duration_plane',
            'duration_fact',
            'is_result',
        )

    def validate_task(self, task):
        request = self.context.get('request')
        return utils.validate_task(task, request)

    def to_representation(self, instance):
        return PersonalPlaneItemListSerializer(instance, context=self.context).data


class PersonalPlaneItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PersonalPlaneItemModel
        fields = (
            'id',
            'task',
            'description',
            'work_type',
            'duration_plane',
            'duration_fact',
            'is_result',
        )

    def validate_task(self, task):
        request = self.context.get('request')
        return utils.validate_task(task, request)

    def to_representation(self, instance):
        return PersonalPlaneItemListSerializer(instance, context=self.context).data


class MyPersonalPlaneModelListSerializer(serializers.ModelSerializer):
    status = PersonalPlaneStatusSerializer()

    class Meta:
        model = models.PersonalPlaneModel
        fields = (
            'id',
            'status',
            'description',
            'plane_date',
            'created_at',
            'updated_at',
        )


class MyPersonalPlaneModelSerializer(serializers.ModelSerializer):
    status = PersonalPlaneStatusSerializer()
    plane_items = PersonalPlaneItemListSerializer(many=True)

    class Meta:
        model = models.PersonalPlaneModel
        fields = (
            'id',
            'status',
            'description',
            'plane_date',
            'created_at',
            'updated_at',
            'plane_items',
        )


class PersonalPlaneModelListSerializer(serializers.ModelSerializer):
    author = CachedAppUserSerializer(source='author_id')
    status = PersonalPlaneStatusSerializer()

    class Meta:
        model = models.PersonalPlaneModel
        fields = (
            'id',
            'status',
            'description',
            'plane_date',
            'author',
            'created_at',
            'updated_at',
        )


class PersonalPlaneModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PersonalPlaneModel
        fields = (
            'id',
            'plane_date',
            'description',

        )

    def create(self, validated_data):
        plane_items = self.initial_data.get('plane_items', None)
        with transaction.atomic():
            try:
                instance = super().create(validated_data)
            except IntegrityError:
                raise drf_exceptions.ValidationError(f'План на эту дату уже существует.')
            if isinstance(plane_items, list):
                for item in plane_items:
                    item['plane'] = instance.pk
                    item_serializer = PersonalPlaneItemCreateSerializer(data=item, context=self.context)
                    item_serializer.is_valid(raise_exception=True)
                    item_serializer.save()
            if models.PersonalPlaneModel.objects.filter(
                    is_active=True,
                    author=instance.author,
                    status_id='in_work',
            ).count() > 1:
                raise drf_exceptions.ValidationError('У Вас уже есть дейлик в работе')

        return instance

    def to_representation(self, instance):
        return MyPersonalPlaneModelSerializer(instance, context=self.context).data


class PersonalPlaneModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PersonalPlaneModel
        fields = (
            'id',
            'description',
        )

    def update(self, instance, validated_data):
        plane_items = self.initial_data.get('plane_items', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if isinstance(plane_items, list):
                instance.plane_items.all().delete()
                for item in plane_items:
                    item['plane'] = instance.pk
                    item_serializer = PersonalPlaneItemCreateSerializer(data=item, context=self.context)
                    item_serializer.is_valid(raise_exception=True)
                    item_serializer.save()
        return instance

    def to_representation(self, instance):
        return MyPersonalPlaneModelSerializer(instance, context=self.context).data


class PlanForUserSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField()
    date = serializers.DateField(source='plane_date')

    class Meta:
        model = models.PersonalPlaneModel
        fields = (
            'id',
            'date',
            'count',
        )


class UserPlanListSerializer(serializers.ModelSerializer):
    plans = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = ProfileModel
        fields = (
            'id',
            'full_name',
            'avatar',
            'is_support',
            'plans',
        )

    def get_avatar(self, instance):
        return {"path": instance.avatar.avatar_url} if instance.avatar else None

    def get_plans(self, instance):
        query_params = self.context.get('request').query_params
        plane_date_gte = query_params.get('plane_date_gte')
        plane_date_lte = query_params.get('plane_date_lte')
        if not plane_date_gte or not plane_date_lte:
            return []
        try:
            plans = models.PersonalPlaneModel.objects.filter(
                author=instance,
                plane_date__gte=plane_date_gte,
                plane_date__lte=plane_date_lte
            ).annotate(
                items_count=Count('plane_items')
            ).order_by('plane_date')
        except ValidationError:
            return []
        plans_data = PlanForUserSerializer(plans, many=True,).data
        return plans_data


class PersonalPlanAccessProfileMetadataModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PersonalPlanAccessProfileMetadataModel
        fields = (
            'metadata',
        )
