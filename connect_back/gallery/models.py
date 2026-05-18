from urllib.parse import quote

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from bkz3.settings import BACKEND_URL, CUSTOM_CASCADE, CUSTOM_PROTECT
try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None

from common import fields as common_fields
from common.models import BaseModel, File
from common.current_profile.middleware import get_current_authenticated_profile


def validate_image(value):
    if value is None:
        raise ValidationError(message=_('File cannot be null.'))
    try:
        file = File.objects.get(pk=value)
    except ObjectDoesNotExist:
        raise ValidationError(message=_('File not found'))
    if not (file.is_image or file.is_video or file.is_audio):
        raise ValidationError(
            message=_('File is not media.'),
        )
    profile = get_current_authenticated_profile()
    if profile and not file.author == profile and not profile.user.is_superuser:
        raise ValidationError(
            message="Этот файл вам не принадлежит."
        )


def validate_related_object(value):
    if value is None:
        raise ValidationError(message=_('Related object cannot be null.'))
    try:
        obj = BaseModel.objects.get(pk=value)
    except ObjectDoesNotExist:
        raise ValidationError(message=_('Related object not found'))
    profile = get_current_authenticated_profile()
    if profile and not obj.author == profile and not profile.user.is_superuser:
        raise ValidationError(message=_('invalid related object'))


class GalleryModel(BaseModel):
    file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('File'),
        blank=False,
        null=True,
        validators=(validate_image,)
    )
    related_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        on_delete=CUSTOM_CASCADE,
        related_name='gallery',
        verbose_name=_('Related object'),
        blank=False,
        null=True,
        validators=(validate_related_object,)
    )
    is_main = common_fields.CustomBooleanField(verbose_name=_('Main image'), default=False)
    description = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Описание')
    )

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Gallery")

    def save(self, *args, **kwargs):
        if self.is_main:
            # Убираем is_main у остальных записей, если эта запись is_main:
            GalleryModel.objects.filter(related_object=self.related_object).update(is_main=False)
        else:
            if not GalleryModel.objects.filter(related_object=self.related_object, is_active=True).exists():
                # Первая запись связанного объекта всегда is_main:
                self.is_main = True
        super().save(*args, **kwargs)

    def get_detail_permission(self, request) -> bool:
        return self.related_object.get_detail_permission(request)

    @property
    def path(self):
        if DOWNLOADER_PATH is None:
            return self.file.absolute_url
        else:
            parent_path = quote(f"?obj={getattr(self, 'related_object_id', '')}&id={getattr(self, 'file_id', '')}&target=gallery")
            return f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'

    @property
    def name(self):
        return self.file.name

    @property
    def is_image(self):
        return self.file.is_image

    @property
    def is_video(self):
        return self.file.is_video

    @property
    def is_audio(self):
        return self.file.is_audio

