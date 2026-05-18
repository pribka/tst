from urllib.parse import quote

from django.db.models import Q
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bkz3.settings import DOWNLOADER_PATH, BACKEND_URL
from users.models import ProfileModel
from users.serializers import CachedAppUserSerializer
from common.models import File, BaseModel
from common.serializers import AppFileSerializer
from . import models


class ChatListSerializer(serializers.ModelSerializer):
    chat_author = CachedAppUserSerializer()

    class Meta:
        model = models.AIChatModel
        fields = (
            'id',
            'created_at',
            'name',
            'chat_author',
            'last_sent',
            'is_active',
        )

    def to_representation(self, instance):
        user = self.context.get('request').user.profile
        data = super().to_representation(instance)
        return data


class MessageCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AIMessageModel
        fields = (
            'id',
            'message_author',
            'chat',
            'reply_to',
            'text',
            'status',
        )

class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AIMessageModel
        fields = (
            'id',
            'created_at',
            'status',
        )

class MessageListSerializer(serializers.ModelSerializer):
    message_author = CachedAppUserSerializer()

    class Meta:
        model = models.AIMessageModel
        fields = (
            'id',
            'created_at',
            'message_author',
            'chat',
            'reply_to',
            'text',
            'status',
            'is_bot',
            'is_intent',
        )
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Получаем все намерения
        all_intents = instance.intents.all()
        
        # Сериализуем все намерения, но с разным уровнем детализации
        intents_data = []
        for intent in all_intents:
            if intent.is_active:
                # Полная сериализация для активных
                intent_serializer = IntentListSerializer(intent)
                intents_data.append(intent_serializer.data)
            else:
                # Минимальная сериализация для неактивных
                intents_data.append({
                    'id': intent.id,
                    'is_active': intent.is_active
                })
        
        data['intents'] = intents_data
        
        return data


class IntentTypeSerializer(serializers.ModelSerializer):
    """Сериализатор IntentTypeModel. Для отображения в списке намерений."""
    class Meta:
        model = models.IntentTypeModel
        fields = (
            'code',
            'name',
            'btn_title_create',
            'btn_title_open',
            'btn_title_delete',
            'success_message',
            'metadata',
        )


class IntentListSerializer(serializers.ModelSerializer):
    intent_type = IntentTypeSerializer()
    
    class Meta:
        model = models.IntentModel
        fields = (
            'id',
            'is_active',
            'created_at',
            'intent_type',
            'status',
            'related_object',
            'resolutions',
        )


class IntentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания IntentModel с автоматической обработкой"""
    
    class Meta:
        model = models.IntentModel
        fields = (
            'source_object',
            'intent_type',
            'raw_data',
        )
    
    def create(self, validated_data):
        from .utils.intents import build_resolutions
        
        request = self.context.get('request')
        instance = models.IntentModel(**validated_data)
        instance.status_id = 'resolving'  # Устанавливаем начальный статус
        instance.save()
        build_resolutions(instance, request)
        instance.save()
        return instance
