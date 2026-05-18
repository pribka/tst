import re
from urllib.parse import urlparse, parse_qs, urlencode, quote, unquote

from django.db import IntegrityError, transaction
from django.dispatch import receiver
from django.db.models import TextField
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.core.management import call_command
from django.core.cache import cache
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from bs4 import BeautifulSoup

from bkz3.settings import BACKEND_URL, LANGUAGES
try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None
from app_info.models import AppInfo
from common.current_profile.middleware import get_current_authenticated_profile
from common.serializers import CachedBaseModelSerializer

from .models import BaseModel, File, CKEditorFileModel


# @receiver(m2m_changed, sender=BaseModel.attachments.through)
# def attach_pre_add_handler(sender, instance, action, reverse, model, pk_set, using, **kwargs):
#     profile = get_current_authenticated_profile()
#     if not profile:
#         return
#     if action == 'pre_add' and not profile.user.is_superuser and not File.objects.filter(
#             author=profile,
#             pk__in=pk_set,
#             is_active=True
#     ).count() == len(pk_set):
#         raise ValidationError('attachments is not valid.')


@receiver(post_save)
def update_ckeditor_fields(sender, instance, created, raw, using, update_fields, **kwargs):
    if DOWNLOADER_PATH is None or isinstance(instance, AppInfo) or not isinstance(instance, BaseModel):
        return

    fields = instance._meta.local_fields
    new_values = dict()
    base_download_url = BACKEND_URL + DOWNLOADER_PATH

    for field in fields:
        if isinstance(field, TextField):
            value = getattr(instance, field.name, '')
            if not value or not value.strip():
                continue

            soup = BeautifulSoup(value, 'lxml')
            # Ищем и картинки, и ссылки
            tags_to_check = soup.find_all(['img', 'a'])
            changed = False

            for tag in tags_to_check:
                # Определяем, какой атрибут проверять
                attr_name = 'src' if tag.name == 'img' else 'href'
                url = tag.get(attr_name, '')

                # Проверяем, что это наша ссылка на скачивание
                if not url or not url.startswith(base_download_url):
                    continue

                # 1. Разбираем URL
                parsed_url = urlparse(url)
                outer_params = parse_qs(parsed_url.query)
                path_content = outer_params.get('path', [None])[0]

                if not path_content:
                    continue

                # 2. Извлекаем внутренний ID файла
                inner_query = path_content.lstrip('?')
                inner_params = parse_qs(inner_query)
                file_id_list = inner_params.get('id', [])

                if not file_id_list:
                    continue

                file_id = file_id_list[0]

                # 3. Привязка к объекту (делаем один раз для каждого найденного ID)
                try:
                    with transaction.atomic():
                        CKEditorFileModel.objects.get_or_create(
                            file_id=file_id,
                            related_object=instance,
                            field_name=field.name
                        )
                except Exception:
                    pass

                # 4. Формируем новый унифицированный URL
                # Мы принудительно меняем target на ckeditor и добавляем obj
                new_inner_params = {
                    'id': file_id,
                    'target': 'ckeditor',
                    'obj': str(instance.pk)
                }

                new_path = "?" + urlencode(new_inner_params)
                new_url = f"{base_download_url}/?path={quote(new_path)}"

                # Если URL изменился — обновляем тег
                if url != new_url:
                    tag[attr_name] = new_url
                    changed = True

            if changed:
                # Сохраняем результат обработки HTML
                new_values[field.name] = soup.decode_contents()

    if new_values:
        instance.__class__.objects.filter(pk=instance.pk).update(**new_values)


@receiver(post_save)
def track_fields(sender, instance, created, raw, using, update_fields, **kwargs):
    if hasattr(instance, 'track_fields'):
        changed_fields = instance.tracker.changed()
        action_date = timezone.now()
        instance.track_fields(changed_fields, action_date, created)


@receiver(post_delete)
def track_delete(sender, instance, using, **kwargs):
    if hasattr(instance, 'track_fields'):
        action_date = timezone.now()
        instance.track_fields(changed_fields=dict(), action_date=action_date, created=False, deleted=True)


@receiver(m2m_changed)
def track_m2m_fields(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action in ('post_add', 'post_remove') and hasattr(instance, 'tracker') and hasattr(instance, 'track_m2m_fields'):
        instance.track_m2m_fields(sender=sender, model=model, pk_set=pk_set, action=action, action_date=timezone.now())


CACHED_BASE_MODEL_SERIALIZER_NAMES = (
    'WorkgroupNameLogoSerializer',
    'ContractorModelShortSerializer',
    'HelpDeskTicketCategorySerializer',
    'CustomerContractStatusListSerializer',
    'BaseCatalogRetrieveSerializer',
    'InvestProjectFundingSourceSerializer',
)


def invalidate_cached_base_model_serializers(instance):
    instance_pk = str(instance.pk)
    for serializer_name in CACHED_BASE_MODEL_SERIALIZER_NAMES:
        for language_code, language_name in LANGUAGES:
            cache_key = CachedBaseModelSerializer.build_cache_key(
                serializer_name,
                instance_pk,
                language_code,
            )
            cache.delete(cache_key)


@receiver(post_save)
def invalidate_cached_base_model_after_save(sender, instance, **kwargs):
    if not isinstance(instance, BaseModel):
        return
    invalidate_cached_base_model_serializers(instance)


@receiver(post_delete)
def invalidate_cached_base_model_after_delete(sender, instance, **kwargs):
    if not isinstance(instance, BaseModel):
        return
    invalidate_cached_base_model_serializers(instance)
