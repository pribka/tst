from rest_framework import serializers

from common.models import BaseModel
from . import models


class GalleryModelListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.GalleryModel
        fields = (
            'id',
            'path',
            'name',
            'description',
            'is_image',
            'is_video',
            'is_audio',
            'name',
            'is_main',
            'sort',
        )


class GalleryModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GalleryModel
        fields = (
            'id',
            'is_main',
            'description',
            'sort',
        )

    def to_representation(self, instance):
        return GalleryModelListSerializer(instance).data


class GalleryModelCreateSerializer(serializers.ModelSerializer):
    related_object = serializers.PrimaryKeyRelatedField(queryset=BaseModel.objects.filter(is_active=True))

    class Meta:
        model = models.GalleryModel
        fields = (
            'id',
            'file',
            'description',
            'related_object',
            'is_main',
            'sort',
        )

    def to_representation(self, instance):
        return GalleryModelListSerializer(instance).data
