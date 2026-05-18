from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from common.catalogs import models as catalogs_models

from contractor_permissions.utils import check_contractor_permission


class ContractorAccessTokenCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = catalogs_models.Contractor1CAccessTokenModel
        fields = (
            'id',
            'name',
            'contractor',
            'expires_at',
            )

    def validate(self, attrs):
        contractor = attrs.get('contractor')
        if not contractor:
            raise drf_exceptions.ValidationError('Contractor is required.')
        request = self.context.get('request')
        if not contractor.get_update_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете создавать токен доступа для этой организации')
        return attrs

    def create(self, validated_data):
        instance = catalogs_models.Contractor1CAccessTokenModel.create_for_service(
            name=validated_data.get('name'),
            contractor=validated_data.get('contractor'),
            expires_at=validated_data.get('expires_at')
        )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['token'] = instance._raw_token
        return data


class ContractorAccessTokenListSerializer(serializers.ModelSerializer):
    class Meta:
        model = catalogs_models.Contractor1CAccessTokenModel
        fields = (
            'id',
            'name',
            'contractor',
            'expires_at',
            'last_used_at',
            'is_expired',
        )
