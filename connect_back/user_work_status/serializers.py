from rest_framework import serializers
from rest_framework import exceptions

from common.current_profile.middleware import get_current_authenticated_profile

from . import models


class UserWorkStatusReasonModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserWorkStatusReasonModel
        fields = (
            'id',
            'code',
            'name',
            'need_reason_text',
        )


class AppUserWorkStatusModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserWorkStatusModel
        fields = (
            'id',
            'code',
            'name',
            'need_reason',
            'redirect',
        )


class AppUserWorkStatusRecordingModelSerializer(serializers.ModelSerializer):
    status = AppUserWorkStatusModelSerializer()
    reason = UserWorkStatusReasonModelSerializer()

    class Meta:
        model = models.UserWorkStatusRecordingModel
        fields = (
            'id',
            'status',
            'reason',
            'reason_text',
            'created_at',
        )


class UserWorkStatusRecordingModelCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserWorkStatusRecordingModel
        fields = (
            'id',
            'status',
            'reason',
            'reason_text',
        )

    def validate(self, attrs):
        status = attrs.get('status')
        reason = attrs.get('reason')
        reason_text = attrs.get('reason_text')
        if status.need_reason:
            if not reason:
                raise exceptions.ValidationError('Требуется указать причину.')
            if reason.need_reason_text and not reason_text:
                raise exceptions.ValidationError('Требуется указать текст причины')
        else:
            attrs['reason'] = None
            attrs['reason_text'] = ''
        return attrs

    def create(self, validated_data):
        user = get_current_authenticated_profile()
        last_status = models.UserWorkStatusRecordingModel.objects.filter(user=user).order_by('-created_at').first()
        if last_status and last_status.status == validated_data.get('status'):
            return last_status
        instance = models.UserWorkStatusRecordingModel.objects.create(user=user, **validated_data)
        return instance

    def to_representation(self, instance):
        return AppUserWorkStatusRecordingModelSerializer(instance).data
