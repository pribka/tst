import os
import zipfile
import uuid
from urllib.parse import quote

from django.apps import apps
from django.db.models import Q
from django.core.cache import cache

from bkz3.settings import ZIPFILES_ROOT, MEDIA_URL, BACKEND_URL, ZIPFILES_EXPIRE, DOWNLOADER_PATH

from common.models import BaseModel, FolderModel
from common import utils as common_utils


def get_actual_staff_records(organization, unit):
    StaffHistory = apps.get_model('smartkadry', 'StaffHistory')
    lookup = Q()
    if organization:
        lookup &= Q(organization=organization)
    if unit:
        lookup &= Q(unit=unit)
    history = StaffHistory.objects.filter(lookup,
                                          is_active=True).order_by(
        'organization',
        'position',
        'person',
        # 'unit',
        '-date_registration',
        '-created',
    ).distinct('organization',
               'position',
               # 'unit',
               'person')
    return history


def get_serialized_image(instance):
    from common.serializers import AppFileSerializer
    if instance is None or not instance.image_id or not instance.image.is_active:
        return ""
    image_data = AppFileSerializer(instance=instance.image).data
    if image_data and DOWNLOADER_PATH is not None:
        image_data['path'] = image_data['path'] + quote(f"&target=image&obj={instance.pk}")
    return image_data
