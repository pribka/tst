from django.db import transaction
from django_q.tasks import async_task
from rest_framework import serializers

from bkz3.settings import DEALERS_EMAIL_NEWS_NOTIFICATION
from bpms.bpms_common import models as common_models
from bpms.bpms_common.serializers import AppUserSerializer
from bpms.tasks.serializers import (ReportSprintSerializer,
                                    TaskSprintShortSerializer)
from common.models import File
from common.serializers import AppFileSerializer
from common.utils import get_serialized_attachments
from notifications.utils import send_email

from bpms.workgroups.models import WorkgroupModel
from bpms.workgroups.serializers import WorkgroupNameLogoSerializer

from bpms.bpms_common.models import NewsCategoryModel
from bpms.bpms_common.utils import get_serialized_image

from . import notifications, utils, models


class NewsCategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsCategoryModel
        fields = (
            'id',
            'code',
            'name',
        )


class NewsListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    image = serializers.SerializerMethodField()
    sprint = TaskSprintShortSerializer()
    category = NewsCategoryModelSerializer()
    work_groups = WorkgroupNameLogoSerializer(many=True)

    class Meta:
        model = common_models.NewsModel
        fields = (
            'id',
            'title',
            'is_banner',
            'created_at',
            'is_important',
            'image',
            'author',
            'sprint',
            'content',
            'category',
            'work_groups',
        )

    def get_image(self, instance):
        return get_serialized_image(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['short_content'] = utils.get_news_short_content(instance.content)
        data['has_read'] = instance.viewers.filter(user=self.context['request'].user).exists()

        return data


class NewsDetailSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    attachments = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    sprint = ReportSprintSerializer()
    category = NewsCategoryModelSerializer()
    work_groups = WorkgroupNameLogoSerializer(many=True)

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    class Meta:
        model = common_models.NewsModel
        fields = (
            'id',
            'title',
            'is_banner',
            'content',
            'created_at',
            'sprint',
            'is_important',
            'image',
            'author',
            'attachments',
            'related_object',
            'work_groups',
            'category'
        )

    def get_image(self, instance):
        return get_serialized_image(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            user = self.context.get('request').user.profile
        except AttributeError:
            return data
        data['viewed'] = instance.viewers.filter(pk=user.pk).exists()
        instance.cluts()
        data['viewer_count'] = instance.viewers.count()
        return data


class NewsCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = common_models.NewsModel
        fields = (
            'id',
            'title',
            'content',
            'is_banner',
            'is_important',
            'image',
            'sprint',
            'attachments',
            'related_object',
            'category',
        )

    def create(self, validated_data):

        validated_data['is_independent'] = validated_data['related_object'] is None

        with transaction.atomic():
            attachments = validated_data.pop('attachments', [])
            news = common_models.NewsModel.objects.create(
                **validated_data,
            )
            if attachments:
                news.attachments.set(attachments)

            if news.is_banner:
                common_models.NewsModel.objects.filter(is_banner=True).exclude(pk=news.pk).update(
                    is_banner=False
                )

        async_task(utils.send_socketio_about_new_news, news)

        if DEALERS_EMAIL_NEWS_NOTIFICATION:
            async_task(utils.send_dealers_email_news_notification, news)

        if news.is_important:
            async_task(notifications.notify_about_new_news, news, news.author)
        return news

    def to_representation(self, instance):
        data = NewsDetailSerializer(instance).data
        data['short_content'] = utils.get_news_short_content(instance.content)
        return data


class NewsUpdateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = common_models.NewsModel
        fields = (
            'title',
            'content',
            'attachments',
            'category',
            'is_important',
            'is_banner',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if instance.is_banner:
                common_models.NewsModel.objects.filter(is_banner=True).exclude(pk=instance.pk).update(
                    is_banner=False
                )
        return instance

    def to_representation(self, instance):
        data = NewsDetailSerializer(instance).data
        data['short_content'] = utils.get_news_short_content(instance.content)
        return data


class NewsFilterCategoryModelSerializer(serializers.ModelSerializer):
    checked = serializers.SerializerMethodField()

    class Meta:
        model = common_models.NewsCategoryModel
        fields = (
            'id',
            'name',
            'checked',
        )

    def get_checked(self, instance):
        return instance.code in self.context.get('checked_categories', [])

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.code
        data['type'] = 'categories'
        return data


class NewsCategoryWorkgroupSerializer(serializers.ModelSerializer):
    checked = serializers.SerializerMethodField()

    class Meta:
        model = WorkgroupModel
        fields = (
            'id',
            'name',
            'checked',
        )

    def get_checked(self, instance):
        return str(instance.pk) in self.context.get('checked_workgroups', [])

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['type'] = 'workgroups'
        return data
