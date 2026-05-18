from rest_framework import serializers
from rest_framework.fields import ReadOnlyField

from . import models
from ..tasks.models import TaskModel


class WidgetSerializer(serializers.ModelSerializer):
    user_widget_id = ReadOnlyField()
    widget_catalog_sort = ReadOnlyField()
    user_widget_column = ReadOnlyField()
    user_widget_sort = ReadOnlyField()
    user_widget_category = ReadOnlyField()

    class Meta:
        model = models.WidgetCatalog
        fields = ['id', 'user_widget_id', 'component_name', 'widget_catalog_sort', 'code', 'icon_name', 'name',
                  'user_widget_sort', 'user_widget_column', 'is_active', 'user_widget_category']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.pk
        return data


class UserWidgetSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = models.UserWidgetModel
        fields = "__all__"


class MyTasksWidgetSerializer(serializers.ModelSerializer):
    watching = serializers.SerializerMethodField()
    doing = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    def get_watching(self, obj):
        return TaskModel.objects.filter(is_active=True, visors__in=[self.context['request'].user.profile]). \
            exclude(status="completed").count()

    def get_doing(self, obj):
        return TaskModel.objects.filter(is_active=True, operator=self.context['request'].user.profile). \
            exclude(status="completed").count()

    def get_owner(self, obj):
        return TaskModel.objects.filter(is_active=True, owner=self.context['request'].user.profile). \
            exclude(status="completed").count()

    class Meta:
        model = TaskModel
        fields = ["watching", "doing", "owner"]


from .models import WidgetCategoryModel, WidgetModel, DesktopTemplateModel, DesktopTemplateWidgetOnDesktopModel, \
    UserDesktopModel, UserWidgetOnDesktopModel


class WidgetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WidgetCategoryModel
        fields = ['id', 'name']


class WidgetModelReadSerializer(serializers.ModelSerializer):
    category = WidgetCategorySerializer()

    class Meta:
        model = WidgetModel
        fields = [
            'id', 'name',
            'category',
            'icon',
            'widget_component', 'setting_component', 'random_html', 'is_mobile',
            'is_desktop',
            'static',
            'w',
            'h', 'minW', 'minH', 'maxW', 'maxH'
        ]


class WidgetModelWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WidgetModel
        fields = [

            'category',
            'icon',
            'widget_component', 'setting_component', 'random_html', 'is_mobile',
            'is_desktop',
            'static',
            'w',
            'h', 'minW', 'minH', 'maxW', 'maxH'
        ]


class DesktopTemplateWidgetOnDesktopSerializer(serializers.ModelSerializer):
    widget = WidgetModelReadSerializer()

    class Meta:
        model = DesktopTemplateWidgetOnDesktopModel
        fields = ['id', 'static', 'widget', 'x', 'y', 'w', 'h', 'i']


class DesktopTemplateReadSerializer(serializers.ModelSerializer):
    # default_widgets = DesktopTemplateWidgetOnDesktopSerializer(many=True, allow_null=True)

    class Meta:
        model = DesktopTemplateModel
        fields = [
            'id',
            'name',
            # 'draggable',
            # 'resizable',
            # 'margin_x',
            # 'margin_y',
            # 'vertical_compact',
            # 'use_css_transforms',
            # 'default_widgets'
        ]


class DesktopTemplateWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesktopTemplateModel
        fields = [
            'draggable',
            'resizable',
            'margin_x',
            'margin_y',
            'vertical_compact',
            'use_css_transforms',
            'default_widgets'

        ]


class UserDesktopSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDesktopModel
        fields = [
            'id',
            'desktop_template',
            'name',
            'sort',
            'draggable',
            'resizable',
            'margin_x',
            'margin_y',
            'vertical_compact',
            'use_css_transforms'
        ]


class UserWidgetOnDesktopSerializer(serializers.ModelSerializer):
    widget = WidgetModelReadSerializer()

    class Meta:
        model = UserWidgetOnDesktopModel
        fields = [
            'id', 'name',
            'desktop', 'static', 'random_html', 'random_settings',
            'mobile_index',
            'is_mobile',
            'is_desktop',
            'widget',
            'x', 'y', 'w', 'h', 'i', 'sort'
        ]

    def to_representation(self, instance):
        if instance.name == '':
            instance.name = instance.widget.name
            instance.save()
        data = super().to_representation(instance)
        data['page_name'] = instance.page_name
        data['minH'] = instance.widget.minH
        data['minW'] = instance.widget.minW
        data['maxW'] = instance.widget.maxW
        data['maxH'] = instance.widget.maxH

        return data
