from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseAbstractModel, BaseAbstractCatalog, BaseCatalog, BaseModel
from common import fields as common_fields
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT


class ActivityDigestModel(BaseModel):
    """
    Предсобранный дневной дайджест по одному срезу (организация, проект, команда, пользователь).
    Одна запись = одна дата + один scope + один источник (source). Текст дайджеста в summary.
    """
    related_object = common_fields.CustomForeignKey(
        "common.BaseModel",
        on_delete=CUSTOM_CASCADE,
        related_name="activity_digests",
        verbose_name=_("Объект среза"),
    )
    date = common_fields.CustomDateField(
        verbose_name=_("Дата"),
    )
    scope = common_fields.CustomCharField(
        max_length=32,
        verbose_name=_("Охват среза"),
        help_text=_("organization | project | workgroup | user | user_day_summary"),
    )
    source = common_fields.CustomCharField(
        max_length=32,
        verbose_name=_("Источник данных"),
        help_text=_("tasks | meetings | events | helpdesk | chats"),
        default="",
    )
    summary = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Дайджест"),
    )

    class Meta:
        verbose_name = _("Дайджест активности за день")
        verbose_name_plural = _("Дайджесты активности за день")
        ordering = ("-date", "related_object", "source")
        unique_together = [
            ("related_object", "date", "scope", "source"),
        ]

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ActivityDigestSerializer
        return ActivityDigestSerializer

    def get_detail_permission(self, request) -> bool:
        if not request or not request.user.is_authenticated:
            return False
        try:
            obj = self.related_object.original_object
        except ObjectDoesNotExist:
            return False
        profile = request.user.profile

        from common.catalogs.models import ContractorModel
        from bpms.workgroups.models import WorkgroupModel
        from users.models import ProfileModel

        if isinstance(obj, ContractorModel):
            return any(str(org_pk) == str(obj.pk) for org_pk in profile.my_organizations)
        if isinstance(obj, WorkgroupModel):
            return obj.get_detail_permission(request)
        if isinstance(obj, ProfileModel):
            return ProfileModel.get_queryset(request).filter(pk=obj.pk).exists()
        return False


# Допустимые источники дайджеста. Добавление нового источника (например day_summary) — без миграции полей.
DIGEST_SOURCE_KEYS = ("tasks", "meetings", "events", "helpdesk", "chats", "day_summary")


class ActivitySummaryModel(BaseModel):
    """Модель для хранения сформировавшихся саммари по активности за период."""
    related_object = common_fields.CustomForeignKey(
        "common.BaseModel",
        on_delete=CUSTOM_CASCADE,
        related_name="activity_summary",
        verbose_name=_("Объект среза"),
    )
    user = common_fields.CustomForeignKey(
        'users.ProfileModel',
        null=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Автор'),
        related_name='created_activity_summaries',
        )
    start_date = common_fields.CustomDateField(
        verbose_name=_('Дата начала периода'),
        null=False,
        blank=False,
    )
    end_date = common_fields.CustomDateField(
        verbose_name=_('Дата конца периода'),
        null=False,
        blank=False,
    )
    sources = common_fields.CustomCharField(
        verbose_name=_('Источники'),
        max_length=64,
        blank=True,
        default='',
    )
    scope = common_fields.CustomCharField(
        verbose_name=_('Охват среза'),
        max_length=32,
        blank=False,
        default='organization',
        help_text=_('organization | project | workgroup | user'),
    )
    summary = models.TextField(
        verbose_name=_('Саммари'),
        null=False,
        blank=False,
        default='',
    )
    
    STATUS_CHOICES = (
        ('pending', _('В процессе')),
        ('completed', _('Готово')),
        ('failed', _('Ошибка')),
    )
    
    status = common_fields.CustomCharField(
        verbose_name=_('Статус'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        null=False,
        blank=False,
    )
    error_message = models.TextField(
        verbose_name=_('Сообщение об ошибке'),
        null=True,
        blank=True,
        default='',
    )
    started_at = common_fields.CustomDateTimeField(
        verbose_name=_('Дата начала формирования'),
        null=True,
        blank=True,
    )
    completed_at = common_fields.CustomDateTimeField(
        verbose_name=_('Дата завершения формирования'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Саммари активности')
        verbose_name_plural = _('Саммари активности')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            ActivitySummarySerializer,
            ActivitySummaryNotifySerializer,
        )
        if action == 'notify':
            return ActivitySummaryNotifySerializer
        return ActivitySummarySerializer


    def get_detail_permission(self, request) -> bool:
        if not request or not request.user.is_authenticated:
            return False
        try:
            obj = self.related_object.original_object
        except ObjectDoesNotExist:
            return False
        profile = request.user.profile

        from common.catalogs.models import ContractorModel
        from bpms.workgroups.models import WorkgroupModel
        from users.models import ProfileModel

        if isinstance(obj, ContractorModel):
            return any(str(org_pk) == str(obj.pk) for org_pk in profile.my_organizations)
        if isinstance(obj, WorkgroupModel):
            return obj.get_detail_permission(request)
        if isinstance(obj, ProfileModel):
            return ProfileModel.get_queryset(request).filter(pk=obj.pk).exists()
        return False


class DashboardSectionModel(BaseCatalog, BaseAbstractCatalog):
    """Справочник секций руководительского дашборда."""

    class Meta:
        verbose_name = _("Секция дашборда")
        verbose_name_plural = _("Секции дашборда")


class DashboardConfigModel(BaseAbstractModel):
    """Конфигурация секции руководительского дашборда."""

    section = common_fields.CustomForeignKey(
        to='analytics.DashboardSectionModel',
        to_field='code',
        null=True,
        blank=True,
        default='',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_("Секция"),
        related_name='dashboard_configs',
    )
    config = models.JSONField(
        default=dict,
        verbose_name=_("Конфигурация секции"),
        help_text=_("JSON-структура секции: groups -> widgets -> drilldown"),
    )
    scopes = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Поддерживаемые scope"),
        help_text=_("Список scope, для которых применим этот конфиг"),
    )
    description = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Описание"),
        help_text=_("Короткое описание назначения конфигурации."),
    )
    min_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Минимальная длина периода (дней)"),
    )
    max_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Максимальная длина периода (дней)"),
    )

    class Meta:
        verbose_name = _("Конфигурация секции дашборда")
        verbose_name_plural = _("Конфигурации секций дашборда")

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import DashboardConfigSerializer
        return DashboardConfigSerializer

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('section', '-created_at')

