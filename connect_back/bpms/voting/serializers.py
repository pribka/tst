from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from users.serializers import CachedAppUserSerializer

from . import models


class RatingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserRatingModel
        fields = (
            'id',
            'rating',
            'related_object',
            'description',
        )


class RatingReadSerializer(serializers.ModelSerializer):
    author = CachedAppUserSerializer(source='author_id')

    class Meta:
        model = models.UserRatingModel
        fields = (
            'id',
            'author',
            'rating',
            'description',
        )
