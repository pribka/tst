from rest_framework import serializers

from common.current_profile.middleware import get_current_authenticated_profile
from common.models import BaseModel

from . import models


class RelatedObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        original_object = instance.original_object
        serializer_class = original_object.get_serializer_class(action='list')
        data = serializer_class(original_object, context=self.context).data
        data['obj_type'] = original_object.get_label()
        return data


class FavoriteModelListSerializer(serializers.ModelSerializer):
    related_object = RelatedObjectSerializer()

    class Meta:
        model = models.FavoriteModel
        fields = (
            'id',
            'related_object',
            'created_at',
        )


class FavoriteModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FavoriteModel
        fields = (
            'related_object',
        )

    def create(self, validated_data):
        user = get_current_authenticated_profile()
        validated_data['user'] = user
        instance = super().create(validated_data)
        return instance


# class FavoritesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = f_models.FavoritesModel
#         fields = (
#             'id',
#             'profile',
#             'favorites',
#         )
