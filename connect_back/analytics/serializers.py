from rest_framework import serializers

from .models import ActivitySummaryModel, ActivityDigestModel, DashboardConfigModel
from users.serializers import CachedAppUserPreviewSerializer


class ActivityDigestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityDigestModel
        fields = (
            "id",
            "related_object",
            "date",
            "scope",
            "source",
            "summary",
            "is_active",
            "created_at",
            "updated_at",
        )


class ActivitySummarySerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(read_only=True)

    class Meta:
        model = ActivitySummaryModel
        fields = (
            'id',
            'related_object',
            'user',
            'start_date',
            'end_date',
            'sources',
            'scope',
            'summary',
            'status',
            'error_message',
            'started_at',
            'completed_at',
        )


class ActivitySummaryNotifySerializer(serializers.ModelSerializer):
    """Сериализатор для контекста уведомления ActivitySummaryReady: id, related_object, scope, даты."""
    class Meta:
        model = ActivitySummaryModel
        fields = ('id', 'related_object', 'start_date', 'end_date', 'scope')


class DashboardConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardConfigModel
        fields = (
            'id',
            'section',
            'config',
            'scopes',
            'min_days',
            'max_days',
            'is_active',
            'created_at',
            'updated_at',
        )
