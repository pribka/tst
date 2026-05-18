from rest_framework import serializers

from . import models


class CatalogInfoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CatalogInfoModel
        fields = (
            'id',
            'name',
            'model',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['count'] = 0
        return data


class CatalogInfoSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CatalogSectionModel
        fields = (
            'id',
            'name',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        catalogs_qs = self.context.get('catalog_qs')
        catalogs = catalogs_qs.filter(section=instance).order_by('sort', 'name',).distinct()
        data['catalogs'] = CatalogInfoListSerializer(catalogs, many=True,).data
        return data
