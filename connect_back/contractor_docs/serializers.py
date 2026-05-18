from django.db import transaction

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from common.catalogs.serializers import ContractorMemberModelSerializer
from common.catalogs.models import ContractorMemberModel

from users.serializers import AppUserSerializer
from users.models import ProfileModel
from . import models, utils


class ContractorDocStatusSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    color = serializers.CharField()
    created_at = serializers.DateTimeField()
    code = serializers.CharField()


class ContractorDocTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContractorDocTypeModel
        fields = (
            'id',
            'code',
            'name',
        )


class ContractorDocTemplateModelSerializer(serializers.ModelSerializer):
    doc_type = ContractorDocTypeSerializer()

    class Meta:
        model = models.ContractorDocTemplateModel
        fields = (
            'id',
            'name',
            'description',
            'code',
            'doc_type',
        )


class ContractorDocModelDetailSerializer(serializers.ModelSerializer):
    contractor = ContractorMemberModelSerializer()
    customer = ContractorMemberModelSerializer()
    template = ContractorDocTemplateModelSerializer()
    approval_status = ContractorDocStatusSerializer()
    delivery_status = ContractorDocStatusSerializer()
    author = AppUserSerializer()
    members = AppUserSerializer(many=True)
    doc_file = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorDocModel
        fields = (
            'id',
            'name',
            'approval_status',
            'delivery_status',
            'author',
            'contractor',
            'customer',
            'content',
            'created_at',
            'template',
            'members',
            'locked',
            'doc_file',
        )

    def get_doc_file(self, instance):
        return utils.get_serialized_doc_file(instance)


class ContractorDocModelListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    contractor = ContractorMemberModelSerializer()
    customer = ContractorMemberModelSerializer()
    template = ContractorDocTemplateModelSerializer()
    approval_status = ContractorDocStatusSerializer()
    delivery_status = ContractorDocStatusSerializer()

    class Meta:
        model = models.ContractorDocModel
        fields = (
            'id',
            'name',
            'approval_status',
            'delivery_status',
            'doc_file',
            'author',
            'contractor',
            'customer',
            'created_at',
            'template',
            'locked',
        )


class ContractorDocModelCreateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True, )
    )

    class Meta:
        model = models.ContractorDocModel
        fields = (
            'id',
            'name',
            'contractor',
            'customer',
            'content',
            'members',
            'template',
            'doc_file',
        )

    def validate_doc_file(self, doc_file):
        request = self.context.get('request')
        return utils.validate_doc_file(doc_file, request)

    def create(self, validated_data):
        members = validated_data.pop('members', None)
        doc_file = validated_data.pop('doc_file', None)
        with transaction.atomic():
            instance = models.ContractorDocModel.objects.create(**validated_data)
            if doc_file:
                instance.locked = True
                instance.doc_file = doc_file
            else:
                doc_file = utils.create_doc_file(instance)
                instance.doc_file = doc_file
            instance.save()
            if members:
                instance.contractor_doc_members.add(
                    *[models.ContractorDocMemberModel(user=each, contractor_doc=instance) for each in members],
                    bulk=False
                )
        return instance


class ContractorDocModelUpdateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True, )
    )

    class Meta:
        model = models.ContractorDocModel
        fields = (
            'id',
            'name',
            'content',
            'members',
            'doc_file',
        )

    def validate_doc_file(self, doc_file):
        request = self.context.get('request')
        return utils.validate_doc_file(doc_file, request)

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        old_doc_file = instance.doc_file
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if old_doc_file and instance.doc_file and not (old_doc_file == instance.doc_file):
                instance.locked = True
                instance.save(update_fields=('locked',))
            else:
                utils.update_doc_file(instance)
            if members is not None:
                instance.contractor_doc_members.clear()
                if members:
                    instance.contractor_doc_members.add(
                        *[models.ContractorDocMemberModel(user=each, contractor_doc=instance) for each in members],
                        bulk=False,
                    )

        return instance


class ContractorDocContentSerializer(serializers.Serializer):
    contractor = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        allow_empty=False,
        queryset=ContractorMemberModel.objects.filter(is_active=True),
    )
    customer = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        allow_empty=False,
        queryset=ContractorMemberModel.objects.filter(is_active=True),
    )
    template = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        allow_empty=False,
        queryset=models.ContractorDocTemplateModel.objects.filter(is_active=True),
    )



