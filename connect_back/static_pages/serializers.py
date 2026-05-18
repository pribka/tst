from rest_framework import serializers

from . import models


class StaticPageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StaticPageModel
        fields = (
            'name',
            'html_data',
            'json_data',
        )
