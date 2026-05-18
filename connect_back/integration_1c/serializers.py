from rest_framework import serializers
from . import models


class Profile1CDocumentsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile1CDocumentsModel
        fields = (
            'name',
            'code',
            'contractor_is_required',
            'member_is_required',
            'contract_is_required',
            'start_date_is_required',
            'end_date_is_required',
        )

