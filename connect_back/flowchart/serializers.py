from rest_framework import serializers
from . import models
from common import serializers as common_serializers


class FlowchartListSerializer(common_serializers.BaseCatalogListSerializer):
    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.FlowchartModel
        fields = (
            'id',
            'name',
        )


class FlowchartDetailSerializer(common_serializers.BaseCatalogRetrieveSerializer):
    class Meta(common_serializers.BaseCatalogRetrieveSerializer.Meta):
        model = models.FlowchartModel
        fields = (
            'id',
            'name',
        )


class FlowchartCRUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.FlowchartModel
        fields = (
            # 'id',
            'name',
        )
