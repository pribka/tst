from django.core.cache import cache
from django.utils.translation import get_language

from rest_framework import serializers
from django.conf import settings

from . import models


class BudgetFunctionalGroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BudgetFunctionalGroupModel
        fields = [
            'id',
            'code',
            'name',
        ]


class BudgetFunctionalSubgroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BudgetFunctionalSubgroupModel
        fields = [
            'id',
            'code',
            'name',
        ]


class BudgetProgramAdministratorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BudgetProgramAdministratorModel
        fields = [
            'id',
            'code',
            'name',
        ]


class BudgetProgramModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BudgetProgramModel
        fields = [
            'id',
            'code',
            'name',
        ]


class BudgetSubprogramModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BudgetSubprogramModel
        fields = [
            'id',
            'code',
            'name',
        ]


class KATOCodesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KATOCodesModel
        fields = [
            'id',
            'code',
            'name',
            'full_name',
        ]


class CachedKATOCodesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KATOCodesModel
        fields = (
            'id',
        )

    def to_representation(self, instance):
        lang_code = get_language()
        cache_key = f"CachedKATOCodesModelSerializer_{str(instance)}_{lang_code}"
        data = cache.get(cache_key)
        if data is None:
            instance_obj = models.BaseModel.objects.super_get(pk=instance)
            data = KATOCodesModelSerializer(instance=instance_obj).data
            cache.set(cache_key, data, timeout=None)
        return data
