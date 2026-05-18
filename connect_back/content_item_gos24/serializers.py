from rest_framework import serializers

from users.serializers import AppCustomUserSerializer, ProfileFilterSerializer
from . import models
from common import serializers as common_serializers, models as common_models, utils as common_utils
from django.utils import timezone
from django.utils.html import strip_tags


class OfficialClarificationOrganSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OfficialClarificationOrgan
        fields = (
            'id',
            'title',
            'title_kk',
        )


class PartitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Partition
        fields = (
            'id',
            'name',
            'name_kk',
            'code'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = (
            'id',
            'name',
            'name_kk',
        )


class ArticleListViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            'id',
            'title',
            'title_kk',
            'publication_date',
            'body',
            'body_kk',
            'description',
            'description_kk',
            'partition',
            'anchor_links',
            'tags',
            'kind',
            'only_subscribed',
            'draft',
            'main_in_week',
            'sent_gos',   # <-- добавили
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['partition'] = PartitionSerializer(instance.partition).data if instance.partition else None
        data['tags'] = TagSerializer(instance.tags, many=True).data
        return data

    def create(self, validated_data):
        validated_data['description_clean'] = strip_tags(validated_data.get('description', '')).strip()
        validated_data['description_clean_kk'] = strip_tags(validated_data.get('description_kk', '')).strip()
        validated_data['body_clean'] = strip_tags(validated_data.get('body', '')).strip()
        validated_data['body_clean_kk'] = strip_tags(validated_data.get('body_kk', '')).strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'description' in validated_data:
            validated_data['description_clean'] = strip_tags(validated_data['description']).strip()
        if 'body' in validated_data:
            validated_data['body_clean'] = strip_tags(validated_data['body']).strip()
        if 'description_kk' in validated_data:
            validated_data['description_clean_kk'] = strip_tags(validated_data['description_kk']).strip()
        if 'body' in validated_data:
            validated_data['body_clean_kk'] = strip_tags(validated_data['body_kk']).strip()
        return super().update(instance, validated_data)


class NewsPublicationsListViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            'id',
            'title',
            'title_kk',
            'publication_date',
            'body',
            'body_kk',
            'description',
            'description_kk',
            'partition',
            'anchor_links',
            'tags',
            'kind',
            'only_subscribed',
            'draft',
            'main_in_week',
            'image',
            'sent_gos',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['partition'] = PartitionSerializer(instance.partition).data if instance.partition else None
        data['tags'] = TagSerializer(instance.tags, many=True).data
        return data

    def create(self, validated_data):
        validated_data['description_clean'] = strip_tags(validated_data.get('description', '')).strip()
        validated_data['description_clean_kk'] = strip_tags(validated_data.get('description_kk', '')).strip()
        validated_data['body_clean'] = strip_tags(validated_data.get('body', '')).strip()
        validated_data['body_clean_kk'] = strip_tags(validated_data.get('body_kk', '')).strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'description' in validated_data:
            validated_data['description_clean'] = strip_tags(validated_data['description']).strip()
        if 'description_kk' in validated_data:
            validated_data['description_clean_kk'] = strip_tags(validated_data['description_kk']).strip()
        if 'body' in validated_data:
            validated_data['body_clean'] = strip_tags(validated_data['body']).strip()
        if 'body_kk' in validated_data:
            validated_data['body_clean_kk'] = strip_tags(validated_data['body_kk']).strip()
        return super().update(instance, validated_data)

class OfficialListViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            'id',
            'title',
            'title_kk',
            'publication_date',
            'body',            # работаем с body
            'body_kk',
            'description',
            'description_kk',
            'partition',
            'organ',
            'anchor_links',
            'kind',
            'only_subscribed',
            'draft',
            'main_in_week',
            'tags',            # добавили теги
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['partition'] = PartitionSerializer(instance.partition).data if instance.partition else None
        data['organ'] = OfficialClarificationOrganSerializer(instance.organ).data if instance.organ else None
        data['tags'] = TagSerializer(instance.tags, many=True).data
        return data

    def create(self, validated_data):
        description = validated_data.get('description') or ''
        description_kk = validated_data.get('description_kk') or ''
        body = validated_data.get('body') or ''
        body_kk = validated_data.get('body_kk') or ''
        validated_data['description_clean'] = strip_tags(description).strip()
        validated_data['description_clean_kk'] = strip_tags(description_kk).strip()
        validated_data['body_clean'] = strip_tags(body).strip()
        validated_data['body_clean_kk'] = strip_tags(body_kk).strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'description' in validated_data:
            validated_data['description_clean'] = strip_tags(validated_data.get('description') or '').strip()
        if 'description_kk' in validated_data:
            validated_data['description_clean_kk'] = strip_tags(validated_data['description_kk']).strip()
        if 'body' in validated_data:
            validated_data['body_clean'] = strip_tags(validated_data.get('body') or '').strip()
        if 'body_kk' in validated_data:
            validated_data['body_clean_kk'] = strip_tags(validated_data['body_kk']).strip()
        return super().update(instance, validated_data)


class WebinarListViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            'id',
            'title',
            'title_kk',
            'summary',
            'lecturer',
            'partition',
            'content_type',
            'planned_date',
            'start_live_time',
            'end_live_time',
            'youtube_url',
            'broadcast',
            'body',
            'body_kk',
            'webinar_date',
            'lecturer_full_name',
            'spend',
            'webinar_active',
            'only_subscribed',
            'draft',
            'is_active',
            'kind',
            'tags',   # добавили теги
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['partition'] = PartitionSerializer(instance.partition).data if instance.partition else None
        data['lecturer'] = ProfileFilterSerializer(instance.lecturer).data if instance.lecturer else None
        data['tags'] = TagSerializer(instance.tags, many=True).data  # отдаем теги
        return data

    def create(self, validated_data):
        # чистые поля для поиска
        description = validated_data.get('description') or ''
        description_kk = validated_data.get('description_kk') or ''
        validated_data['description_clean'] = strip_tags(description).strip()
        validated_data['description_clean_kk'] = strip_tags(description_kk).strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'description' in validated_data:
            validated_data['description_clean'] = strip_tags(validated_data.get('description') or '').strip()
        if 'description_kk' in validated_data:
            validated_data['description_clean_kk'] = strip_tags(validated_data.get('description_kk') or '').strip()
        return super().update(instance, validated_data)

class QuestionListView(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            'id',
            'title',
            'title_kk',
            'created_at',
            'partition',
            'tags',
            'question_html',
            'question_html_kk',
            'answer_html',
            'answer_html_kk',
            'main_in_week',
            'draft',
            'kind',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['partition'] = PartitionSerializer(instance.partition).data if instance.partition else None
        data['tags'] = TagSerializer(instance.tags, many=True).data
        return data


class KnowledgebaseViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            'id',
            'title',
            'title_kk',
            'body',            # <-- было description
            'body_kk',
            'content_type',
            'tutorial_id',
            'section_id',
            'youtube_url',
            'anchor_links',
            'kind',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def create(self, validated_data):
        # поддержим body_clean для поиска
        validated_data['body_clean'] = strip_tags(validated_data.get('body', '') or '').strip()
        validated_data['body_clean_kk'] = strip_tags(validated_data.get('body_kk', '') or '').strip()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'body' in validated_data:
            validated_data['body_clean'] = strip_tags(validated_data.get('body') or '').strip()
        return super().update(instance, validated_data)


class ContentItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            "title",
            "publication_date",
            "main_in_week",
            "organ",
            "anchor_links",
            "only_subscribed",
            "body_html",
            "description",
            "draft",
            "spend",
            "free",
            "planned_date",
            "start_live_time",
            "end_live_time",
            "lecturer",
            "content_type",
            "youtube_url",
            "summary",
            "broadcast",
            "kind",
        )


class CalendarItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContentItem
        fields = (
            "id", "kind", "common_date", "content_type",  # ключевые
            "title", "description", "common_date", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if kind != models.ContentItem.KIND_CALENDAR:
            raise serializers.ValidationError({"kind": "Этот сериализатор используется только для kind=calendar"})
        ct = attrs.get("content_type", getattr(self.instance, "content_type", None))
        if ct not in ("holiday", "workday"):
            raise serializers.ValidationError({"content_type": "Допустимо только 'holiday' или 'workday'"})
        if not attrs.get("common_date", getattr(self.instance, "common_date", None)):
            raise serializers.ValidationError({"common_date": "Обязательное поле"})
        return attrs

