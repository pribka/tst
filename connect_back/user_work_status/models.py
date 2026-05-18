from django.db import models
from common import models as common_models
from common import fields as common_fields
from bkz3.settings import CUSTOM_PROTECT


class UserWorkStatusModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    need_reason = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name='Требуется указать причину'
    )
    redirect = common_fields.CustomCharField(
        max_length=100,
        null=False,
        default='',
        blank=True,
        verbose_name="Редирект"
    )

    class Meta:
        verbose_name = "Статус работы пользователя"
        verbose_name_plural = "Статусы работы пользователя"


class UserWorkStatusReasonModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    need_reason_text = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name='Требуется указать текст'
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import UserWorkStatusReasonModelSerializer
        return UserWorkStatusReasonModelSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort', '-created_at')

    class Meta:
        verbose_name = "Причина статусов работы пользователя"
        verbose_name_plural = "Причины статусов работы пользователя"


class UserWorkStatusRecordingModel(common_models.BaseModel):
    status = common_fields.CustomForeignKey(
        to='user_work_status.UserWorkStatusModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        default='completed',
        verbose_name='Статус работы'
    )
    reason = common_fields.CustomForeignKey(
        to='user_work_status.UserWorkStatusReasonModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
        verbose_name='Причина статуса'
    )
    reason_text = common_fields.CustomCharField(
        max_length=253,
        null=False,
        blank=True,
        default='',
        verbose_name='Причина статуса (текст)'
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name='Пользователь',
        related_name='work_status_records'
    )

    class Meta:
        verbose_name = "История статусов работы пользователей"
        verbose_name_plural = "Истории статусов работы пользователей"
