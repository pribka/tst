from rest_framework import serializers, exceptions as drf_exceptions

from users.serializers import CachedAppUserSerializer

from . import models
from bpms.tasks.models import TaskSprintModel


class RetrospectiveListSerializer(serializers.ModelSerializer):
    author = CachedAppUserSerializer(source='author_id')

    class Meta:
        model = models.RetrospectiveModel
        fields = (
            'id',
            'author',
            'content',
            'created_at',
        )


class RetrospectiveDetailSerializer(serializers.ModelSerializer):
    author = CachedAppUserSerializer(source='author_id')

    class Meta:
        model = models.RetrospectiveModel
        fields = (
            'id',
            'author',
            'content',
            'created_at',
        )


class RetrospectiveCreateSerializer(serializers.ModelSerializer):
    sprint = serializers.PrimaryKeyRelatedField(
        queryset=TaskSprintModel.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = models.RetrospectiveModel
        fields = (
            'id',
            'content',
            'retrospective_type',
            'related_object',
            'sprint',
        )

    def validate_related_object(self, related_object):
        request = self.context.get('request')
        original_related_object = related_object.original_object
        if not original_related_object.get_detail_permission(request):
            raise drf_exceptions.ValidationError('У вас нет доступа к объекту')
        return related_object

    def create(self, validated_data):
        # TODO После исправления на фронте (переименовать sprint в related_object) можно будет удалить def create.
        sprint = validated_data.pop('sprint', None)
        related_object = validated_data.get('related_object')
        if not related_object and sprint:
            validated_data['related_object'] = sprint
        return super().create(validated_data)

    def to_representation(self, instance):
        return RetrospectiveDetailSerializer(instance).data


class RetrospectiveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RetrospectiveModel
        fields = (
            'id',
            'content',
        )

    def to_representation(self, instance):
        return RetrospectiveDetailSerializer(instance).data
