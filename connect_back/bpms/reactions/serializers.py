from django.core.cache import cache

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from common.serializers import CachedBaseCatalogSerializer
from users.serializers import CachedAppUserPreviewSerializer

from . import models, utils


class ReactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReactionModel
        fields = (
            'id',
            'code',
            'name',
            'icon',
            'sort',
        )


class CachedReactionSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = cache.get('ReactionListSerializer_' + str(instance))
        if not data:
            instance_obj = models.ReactionModel.objects.get(pk=instance)
            data = ReactionListSerializer(instance=instance_obj).data
            cache.set('ReactionListSerializer_' + str(instance), data)
        return data


class ReactionObjectWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ReactionObjectModel
        fields = (
            'id',
            'reaction',
        )


class ReactionObjectListSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')
    reaction = CachedReactionSerializer(source='reaction_id')

    class Meta:
        model = models.ReactionObjectModel
        fields = (
            'id',
            'user',
            'reaction',
        )
