from django.db import transaction
from django_q.tasks import async_task

from rest_framework import serializers, exceptions as drf_exceptions

from common.models import BaseModel
from common.catalogs.models import ContractorModel

from . import models, notifications
from .utils import create_tag_history


class TagModelListSerializer(serializers.ModelSerializer):
    """Оптимизированная версия TagModelListSerializer для избежания N+1 запросов."""
    class Meta:
        model = models.TagModel
        fields = (
            'id',
            'name',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        related_object_id = self.context.get('related_object')
        if related_object_id:
            # Проверяем, есть ли prefetched данные
            if hasattr(instance, '_prefetched_objects_cache') and 'tag_object_through' in instance._prefetched_objects_cache:
                # Используем prefetched данные
                for through in instance.tag_object_through.all():
                    if str(through.related_object_id) == str(related_object_id):
                        data['color'] = through.color
                        break
            else:
                # Если prefetch не сработал, делаем fallback к оригинальному запросу
                color = list(
                    instance.tag_object_through.filter(related_object_id=related_object_id).values_list('color', flat=True)
                )
                if color:
                    data['color'] = color[0]
        return data


class TagModelCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        allow_null=False,
        required=True,
        max_length=255,
    )
    related_object = serializers.PrimaryKeyRelatedField(
        queryset=BaseModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )
    contractor = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )
    color = serializers.CharField(
        allow_null=False,
        allow_blank=True,
        required=False,
        default='default',
        max_length=31,
    )

    class Meta:
        model = models.TagModel
        fields = (
            'id',
            'name',
            'color',
            'related_object',
            'contractor',
        )

    def create(self, validated_data):
        related_object = validated_data.pop('related_object', None)
        contractor = validated_data.pop('contractor', None)
        color = validated_data.pop('color', None)
        if not color:
            color = 'default'
        name = validated_data.get('name', '').lower().strip()
        with transaction.atomic():
            instance, created = models.TagModel.objects.get_or_create(name=name)
            if contractor:
                models.TagContractorThrough.objects.get_or_create(
                    tag=instance,
                    contractor=contractor
                )
            if related_object:
                models.TagRelatedObjectThrough.objects.update_or_create(
                    related_object=related_object,
                    tag=instance,
                    defaults={'color': color}
                )
                self.context['related_object'] = related_object.pk
                
                create_tag_history(related_object.pk, instance, 'added')
                request = self.context.get('request')
                if request:
                    transaction.on_commit(
                        lambda: async_task(notifications.notify_about_new_tag, related_object.pk, instance.pk, request.user.profile.pk)
                        )
        return instance

    def to_representation(self, instance):
        return TagModelListSerializer(instance, context=self.context).data


class TagModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TagRelatedObjectThrough
        fields = (
            'color',
        )


class TagDiscardSerializer(serializers.ModelSerializer):
    related_object = serializers.PrimaryKeyRelatedField(
        queryset=BaseModel.objects.filter(is_active=True),
        required=True,
        allow_null=False,
    )

    class Meta:
        model = models.TagModel
        fields = (
            'id',
            'related_object',
        )

    def validate_related_object(self, related_object):
        request = self.context.get('request')
        original_object = BaseModel.objects.super_get(related_object.pk)
        if not original_object.get_update_tag_permission(request):
            raise drf_exceptions.PermissionDenied('У вас нет прав на удаление тэга')
        return related_object

    def update(self, instance, validated_data):
        related_object = validated_data.get('related_object')
        with transaction.atomic():
            if related_object:
                instance.related_objects.remove(related_object)

                create_tag_history(related_object.pk, instance, 'removed')
                request = self.context.get('request')
                if request:
                    transaction.on_commit(
                        lambda: async_task(notifications.notify_about_remove_tag, related_object.pk, instance.pk, request.user.profile.pk)
                        )
        return instance
