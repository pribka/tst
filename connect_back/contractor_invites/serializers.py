from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions
from common.catalogs.serializers import ContractorModelByIdSerializer, ContractorRelationTypeModelListSerializer
from . import models


class ContractorInviteStatusModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContractorInviteStatusModel
        fields = (
            'id',
            'name',
            'code',
            'color',
        )


class ContractorInviteModelListSerializer(serializers.ModelSerializer):
    contractor_owner = ContractorModelByIdSerializer()
    contractor_parent = ContractorModelByIdSerializer()
    contractor = ContractorModelByIdSerializer()
    relation_type = ContractorRelationTypeModelListSerializer()
    status = ContractorInviteStatusModelSerializer()

    class Meta:
        model = models.ContractorInviteModel
        fields = (
            'id',
            'contractor_owner',
            'contractor_parent',
            'contractor',
            'relation_type',
            'status',
        )


class ContractorInviteModelDetailSerializer(serializers.ModelSerializer):
    contractor_owner = ContractorModelByIdSerializer()
    contractor_parent = ContractorModelByIdSerializer()
    contractor = ContractorModelByIdSerializer()
    relation_type = ContractorRelationTypeModelListSerializer()
    status = ContractorInviteStatusModelSerializer()
    inviteMessage = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorInviteModel
        fields = (
            'id',
            'contractor_owner',
            'contractor_parent',
            'contractor',
            'relation_type',
            'status',
            'inviteMessage',
        )

    def get_inviteMessage(self, instance):
        owner_is_parent = instance.contractor_owner == instance.contractor_parent
        contractor_notify = instance.contractor if owner_is_parent else instance.contractor_parent
        relation_name = instance.relation_type.notify_name if owner_is_parent else instance.relation_type.notify_name_parent
        message = f"{instance.author.full_name} от лица организации \"{instance.contractor_owner.name}\" " \
                  f"приглашает Вашу организацию \"{contractor_notify.name}\" в качестве {relation_name}."
        return message


class ContractorInviteModelCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ContractorInviteModel
        fields = (
            'id',
            'contractor_parent',
            'contractor',
            'contractor_owner',
            'relation_type',
        )

    def validate(self, validated_data):
        user = self.context.get('request').user.profile
        contractor_owner = validated_data.get('contractor_owner')
        if not contractor_owner:
            raise drf_exceptions.ValidationError('contractor_owner не может быть пустым')
        contractor = validated_data.get('contractor')
        if not contractor:
            drf_exceptions.ValidationError('contractor не может быть пустым')
        contractor_parent = validated_data.get('contractor_parent')
        if not contractor_parent:
            drf_exceptions.ValidationError('contractor_parent не может быть пустым')
        if not contractor_owner.contractor_profile.filter(is_active=True, user=user, director=True).exists():
            raise drf_exceptions.PermissionDenied()
        if validated_data.get('contractor_owner') not in (
                validated_data.get('contractor'),
                validated_data.get('contractor_parent')
        ):
            raise drf_exceptions.ValidationError('Invalid contractor owner.')
        return validated_data


class ContractorInviteModelDeleteSerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=models.ContractorInviteModel.objects.filter(is_active=True),
        allow_null=False,
        required=True,
    )

    def validate(self, attrs):
        invite = attrs.get('id')
        contractor_owner = invite.contractor_owner
        user = self.context.get('request').user.profile
        if contractor_owner and not contractor_owner.contractor_profile.filter(
                is_active=True, user=user, director=True).exists():
            raise drf_exceptions.PermissionDenied()
        return attrs


class ContractorInviteNotify(serializers.ModelSerializer):
    contractor_owner = ContractorModelByIdSerializer()

    class Meta:
        model = models.ContractorInviteModel
        fields = (
            'id',
            'contractor_owner'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        owner_is_parent = instance.contractor_owner == instance.contractor_parent
        contractor_notify = instance.contractor if owner_is_parent else instance.contractor_parent
        data['contractor_notify'] = ContractorModelByIdSerializer(contractor_notify).data
        data['relation_notify'] = instance.relation_type.notify_name if owner_is_parent else instance.relation_type.notify_name_parent
        return data
