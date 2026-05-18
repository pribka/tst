# serializers.py
from rest_framework import serializers
from content_item_gos24.models import Tag


class TransferConnectTagImportSerializer(serializers.ModelSerializer):
    # переименовываем входящее поле id -> id_gos24
    id_gos24 = serializers.IntegerField(source='id', required=False)

    class Meta:
        model = Tag
        fields = ('id_gos24', 'created', 'is_active', 'title', 'main')

    def create(self, validated_data):
        # validated_data['id'] здесь уже — это id_gos24
        id_gos24 = validated_data.pop('id')
        tag, _ = Tag.objects.update_or_create(
            id_gos24=id_gos24,
            defaults=validated_data
        )
        return tag
