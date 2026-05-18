import pytz
import datetime

from bs4 import BeautifulSoup

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from bkz3.settings import TIME_ZONE

from common.serializers import BaseCatalogRetrieveSerializer
from common.humanize import get_humanized_timezone

from users.serializers import AppUserSerializer

from . import models


class ChangeHistoryModelListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    action = BaseCatalogRetrieveSerializer()
    object_property = BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.ChangeHistoryModel
        fields = (
            'id',
            'author',
            'action',
            'object_property',
            'before',
            'after',
            'action_date',
            'description'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            is_html = getattr(instance.object_property, 'is_html', True)
        except AttributeError:
            is_html = True
        if is_html:
            before = BeautifulSoup(instance.before, 'lxml').get_text(separator=" ").strip()
            data['before'] = before if len(before) <= 240 else before[:237] + '...'
            after = BeautifulSoup(instance.after, 'lxml').get_text(separator=" ").strip()
            data['after'] = after if len(after) <= 240 else after[:237] + '...'
        try:
            before = datetime.datetime.fromisoformat(instance.before)
        except (TypeError, ValueError):
            pass
        else:
            data['before'] = f"{before.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')} {get_humanized_timezone()}"
        try:
            after = datetime.datetime.fromisoformat(instance.after)
        except (TypeError, ValueError):
            pass
        else:
            data['after'] = f"{after.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')} {get_humanized_timezone()}"
        return data


class ChangeHistoryModelDetailSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    action = BaseCatalogRetrieveSerializer()
    object_property = BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.ChangeHistoryModel
        fields = (
            'id',
            'author',
            'action',
            'object_property',
            'before',
            'after',
            'action_date',
            'description'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            is_html = getattr(instance.object_property, 'is_html', True)
        except AttributeError:
            is_html = True
        if is_html:
            before = BeautifulSoup(instance.before, 'lxml').get_text(separator=" ").strip()
            after = BeautifulSoup(instance.after, 'lxml').get_text(separator=" ").strip()
        else:
            before = instance.before
            after = instance.after
        data['before_clean'] = before if len(before) <= 240 else before[:237] + '...'
        data['after_clean'] = after if len(after) <= 240 else after[:237] + '...'
        try:
            before = datetime.datetime.fromisoformat(instance.before)
        except ValueError:
            pass
        else:
            data['before'] = f"{before.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')} {get_humanized_timezone()}"
        try:
            after = datetime.datetime.fromisoformat(instance.after)
        except ValueError:
            pass
        else:
            data['after'] = f"{after.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')} {get_humanized_timezone()}"
        return data
