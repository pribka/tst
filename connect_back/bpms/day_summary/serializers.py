from rest_framework import serializers

from django.utils.html import strip_tags

from django.db import transaction

from users.models import ProfileModel
from users.serializers import CachedAppUserPreviewSerializer

from .models import DaySummaryNoteModel, DaySummaryNoteStatusModel, DaySummaryNoteCategoryModel


class DaySummaryNoteStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaySummaryNoteStatusModel
        fields = ["code", "name", "color"]


class DaySummaryNoteCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DaySummaryNoteCategoryModel
        fields = ["code", "name", "icon", "hex_color"]


class DaySummaryNoteListSerializer(serializers.ModelSerializer):
    status = DaySummaryNoteStatusSerializer(read_only=True)
    category = DaySummaryNoteCategorySerializer(read_only=True)
    author = CachedAppUserPreviewSerializer(source="author_id", read_only=True)
    visors = CachedAppUserPreviewSerializer(many=True, read_only=True)

    class Meta:
        model = DaySummaryNoteModel
        fields = ["id", "date", "content", "status", "category", "author", "visors", "is_ai_summary", "created_at", "updated_at"]


class DaySummaryNoteListPlainSerializer(DaySummaryNoteListSerializer):
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        return strip_tags(obj.content or "")


class DaySummaryNoteDetailSerializer(serializers.ModelSerializer):
    status = DaySummaryNoteStatusSerializer(read_only=True)
    category = DaySummaryNoteCategorySerializer(read_only=True)
    author = CachedAppUserPreviewSerializer(source="author_id", read_only=True)
    visors = CachedAppUserPreviewSerializer(many=True, read_only=True)

    class Meta:
        model = DaySummaryNoteModel
        fields = ["id", "date", "content", "status", "category", "author", "visors", "is_ai_summary", "created_at", "updated_at"]


class DaySummaryNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaySummaryNoteModel
        fields = ["date", "content", "status", "category"]

    def to_representation(self, instance):
        return DaySummaryNoteDetailSerializer(instance, context=self.context).data


class DaySummaryNoteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaySummaryNoteModel
        fields = ["content", "status", "category", "is_ai_summary"]

    def to_representation(self, instance):
        return DaySummaryNoteDetailSerializer(instance, context=self.context).data


class DaySummaryNoteVisorsUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления наблюдателей итога дня."""
    visors = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )

    class Meta:
        model = DaySummaryNoteModel
        fields = ("id", "visors")

    def update(self, instance, validated_data):
        visors = validated_data.pop("visors", None)
        with transaction.atomic():
            if visors is not None:
                instance.visors.clear()
                instance.visors.set(visors)
        return instance

    def to_representation(self, instance):
        return {
            "visors": CachedAppUserPreviewSerializer(
                instance.visors.all(),
                many=True,
                context=self.context
            ).data
        }
