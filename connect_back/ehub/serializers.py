import json

from django.contrib.auth import password_validation

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from users.utils import check_confirm_token

from . import models


class IntegerListField(serializers.ListField):
    child = serializers.IntegerField(allow_null=False, min_value=1)


class EhubRegisterSerializer(serializers.Serializer):
    confirm_token = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    region = serializers.CharField(max_length=255, required=True, allow_null=False)
    email = serializers.EmailField(required=True, allow_null=False)
    iin = serializers.CharField(max_length=255, required=True, allow_null=False)
    phone = serializers.CharField(max_length=255, required=True, allow_null=False)
    password = serializers.CharField(max_length=128, required=True, allow_null=False)
    password1 = serializers.CharField(max_length=128, required=True, allow_null=False)
    confirm_personal_data = serializers.BooleanField(default=False)
    first_name = serializers.CharField(max_length=150, required=True, allow_null=False)
    last_name = serializers.CharField(max_length=150, required=True, allow_null=False)
    patronymic_name = serializers.CharField(max_length=150, required=True, allow_null=False)
    birthday = serializers.DateField(required=True, allow_null=False)
    sex = serializers.IntegerField(required=True, allow_null=False, min_value=1)
    view_in_dat_pad = serializers.CharField(max_length=500, required=True, allow_null=False)
    view_in_dat_pad_kaz = serializers.CharField(max_length=500, required=True, allow_null=False)
    date = serializers.DateField(required=True, allow_null=False)
    avatar = serializers.FileField(required=True, allow_empty_file=False)
    school = serializers.IntegerField(required=True, allow_null=False, min_value=1)
    positions = serializers.IntegerField(required=True, allow_null=False, min_value=1)
    teacher_languages = IntegerListField(required=True, allow_empty=False, allow_null=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['avatar'] = instance['avatar'].name
        return data

    def validate_password(self, attr):
        password_validation.validate_password(attr)
        return attr

    def validate_pd_confirm(self, attr):
        if not attr:
            raise drf_exceptions.ValidationError('Подтвердите согласие на обработку персональных данныхх')
        return attr

    def validate_region(self, attr):
        try:
            region = models.EhubRegionModel.objects.get(is_active=True, code=attr)
        except models.EhubRegionModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Область не найдена')
        return region

    def validate(self, attrs):
        if not attrs.get('password') == attrs.get('password1'):
            raise drf_exceptions.ValidationError({"password": "Введенные пароли не совпадают."})
        confirm_token = attrs.get('confirm_token')
        if not confirm_token or not check_confirm_token(attrs.get('email'), 'email', confirm_token):
            raise drf_exceptions.ValidationError({"message": f"Код подтверждения устарел. Подтвердите email еще раз."})
        return attrs


class EhubServerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EhubServerModel
        fields = (
            'id',
            'name',
            'code',
            'url',
        )


class EhubRegionModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EhubRegionModel
        fields = (
            'code',
            'name',
        )
