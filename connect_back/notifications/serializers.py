from . import models
from rest_framework import serializers


class WebNotificationSerializer(serializers.ModelSerializer):
    read_at = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    group_total = serializers.SerializerMethodField()
    group_unread = serializers.SerializerMethodField()

    class Meta:
        model = models.WebNotificationModel
        fields = (
            'id',
            'created_at',
            'read_at',
            'message',
            'icon',
            'icon_name',
            'color',
            'is_read',
            'object_id',
            'group_total',
            'group_unread',
        )

    def get_read_at(self, instance):
        return getattr(instance, 'read_at', None)

    def get_is_read(self, instance):
        return getattr(instance, 'is_read', False)

    def get_group_total(self, instance):
        return getattr(instance, 'group_total', None)

    def get_group_unread(self, instance):
        return getattr(instance, 'group_unread', None)

    def _build_group_info(self, instance):
        if not instance.object_id:
            return None

        content_type = getattr(instance, 'content_type', None)
        object_type = None
        model_class = None
        if content_type is not None:
            model_class = content_type.model_class()
            if model_class is not None:
                object_type = str(model_class._meta.verbose_name)

        title = None
        if model_class is not None:
            try:
                object_instance = model_class.objects.get(pk=instance.object_id)
            except model_class.DoesNotExist:
                object_instance = None
            if object_instance is not None:
                title = str(object_instance).strip() or None

        return {
            'object_type': object_type,
            'title': title,
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        event_type = instance.event_type
        category = event_type.category
        data['category'] = {'name': category.name, 'code': category.code}
        data['is_mention'] = event_type.is_mention
        if self.context.get('grouped_mode'):
            data['group_info'] = self._build_group_info(instance)
        return data


class EventTypeSettingsSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    enabled = serializers.BooleanField()


class NotificationSettingsCategorySerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    enabled = serializers.BooleanField()
    events = EventTypeSettingsSerializer(many=True)


class EventTypePreferenceUpdateSerializer(serializers.Serializer):
    event_type_code = serializers.CharField(required=True)
    is_enabled = serializers.BooleanField(required=True)


class CategoryPreferenceUpdateSerializer(serializers.Serializer):
    category = serializers.CharField(required=True)
    is_enabled = serializers.BooleanField(required=True)


class CategoryOrderUpdateSerializer(serializers.Serializer):
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=True,
    )

    def validate_categories(self, value):
        seen_codes = set()
        duplicate_codes = []
        for category_code in value:
            if category_code in seen_codes:
                duplicate_codes.append(category_code)
                continue
            seen_codes.add(category_code)

        if duplicate_codes:
            raise serializers.ValidationError(
                f'Повторяющиеся категории: {", ".join(sorted(set(duplicate_codes)))}'
            )

        return value


class NotificationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NotificationCategoryModel
        fields = (
            'code',
            'name',
        )


class WebPushSubscriptionSerializer(serializers.Serializer):
    endpoint = serializers.CharField(required=True, allow_blank=False)
    keys = serializers.DictField(required=True)
    platform = serializers.CharField(required=False, allow_blank=True, max_length=64)
    browser = serializers.CharField(required=False, allow_blank=True, max_length=64)
    metadata = serializers.DictField(required=False)

    def validate(self, attrs):
        keys = attrs.get('keys', {})
        auth = str(keys.get('auth', '')).strip()
        p256dh = str(keys.get('p256dh', '')).strip()
        if not auth:
            raise serializers.ValidationError({'keys': {'auth': 'This field is required.'}})
        if not p256dh:
            raise serializers.ValidationError({'keys': {'p256dh': 'This field is required.'}})
        attrs['auth'] = auth
        attrs['p256dh'] = p256dh
        if not isinstance(attrs.get('metadata', {}), dict):
            raise serializers.ValidationError({'metadata': 'Must be an object.'})
        return attrs


class WebPushRegisterSerializer(serializers.Serializer):
    subscription = WebPushSubscriptionSerializer(required=True)


class WebPushUpdateSerializer(serializers.Serializer):
    auth = serializers.CharField(required=True, allow_blank=False, max_length=255)
    subscription = WebPushSubscriptionSerializer(required=True)


class WebPushUnregisterSerializer(serializers.Serializer):
    auth = serializers.CharField(required=True, allow_blank=False, max_length=255)


class WebPushStatusSubscriptionSerializer(serializers.Serializer):
    endpoint = serializers.CharField(required=True, allow_blank=False)
    keys = serializers.DictField(required=True)

    def validate(self, attrs):
        keys = attrs.get('keys', {})
        auth = str(keys.get('auth', '')).strip()
        if not auth:
            raise serializers.ValidationError({'keys': {'auth': 'This field is required.'}})
        attrs['auth'] = auth
        return attrs


class WebPushStatusSerializer(serializers.Serializer):
    subscription = WebPushStatusSubscriptionSerializer(required=True)
