import copy
import json

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext, gettext_lazy as _, override

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT, CUSTOM_SET_NULL
from common.models import BaseAbstractCatalog, BaseAbstractModel, BaseCatalog
from common.validators import validate_text_to_json
from common import fields as common_fields


def _report_aggregate_i18n_markers():
    """Итоговые поля отчетов, которые надо перевести на казахский."""
    gettext('Трудозатраты (факт), чч:мм:сс')
    gettext('Трудозатраты (факт), ч')
    gettext('Трудозатраты (план), ч')
    gettext('Выполненные работы')
    gettext('Трудозатраты.Сумма')
    gettext('Время до взятия в работу.Среднее')
    gettext('Время от создания до закрытия.Среднее')
    gettext('Количество обращений')


class ReportCategoryModel(BaseCatalog, BaseAbstractCatalog):

    class Meta:
        verbose_name = _('Категория отчета')
        verbose_name_plural = _('Категории отчетов')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ReportCategorySerializer
        return ReportCategorySerializer


class ReportSettingsModel(BaseCatalog, BaseAbstractCatalog):
    """Общие шаблоны отчетов."""
    AGGREGATE_TRANSLATABLE_KEYS = ('verbose_name', 'title', 'defaultTitle')

    _metadata = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )
    app_section_code = common_fields.CustomCharField(
        max_length=100,
        null=True,
        blank=True,
        default='',
        verbose_name='Относится к разделу приложения'
        )
    category = common_fields.CustomForeignKey(
        to='reports.ReportCategoryModel',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Категория'),
        help_text='В каком разделе отображать отчёт',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name=_("Описание"),
    )
    template_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('Путь к шаблону в report_templates'),
        help_text=_('Заполняется при загрузке файла в админке (относительно MEDIA_ROOT).'),
    )
    usage_scope = models.CharField(
        max_length=64,
        default='public',
        verbose_name='Область использования',
        help_text='Область использования отчёта: public, chat_ai, dashboard и т.д.',
    )
    filter_presets = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Пресеты фильтров',
        help_text='Набор пресетов фильтров по ключам для модификации базовых фильтров отчёта.',
    )

    class Meta:
        verbose_name = 'Общая настройка отчёта'
        verbose_name_plural = 'Общие настройки отчётов'
    
    @property
    def metadata(self):
        if not self._metadata:
            return {}
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        if isinstance(value, str):
            self._metadata = value
        else:
            self._metadata = json.dumps(value, ensure_ascii=False)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.ReportSettingsDetailSerializer
        else:
            return serializers.ReportSettingsListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        from common import utils as common_utils
        from common.utils import get_tariff_section_codes
        qs = cls.objects.filter(is_active=True, usage_scope='public')
        if not request:
            return qs.none()

        user = request.user.profile
        tariff_section_codes = get_tariff_section_codes(user)
        qs = qs.filter(app_section_code__in=tariff_section_codes)

        search = request.query_params.get('search')
        if isinstance(search, str) and len(search.strip()) >= 3:
            search = search.strip()
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        qs = common_utils.get_filter_queryset(request, cls, qs)
        if not qs.query.order_by:
            qs = qs.order_by('category__sort', 'app_section_code', 'name',)
        return qs

    def _build_metadata_kk_from_ru(self, metadata):
        aggregate_fields = metadata.get('availableAggregateFields', [])

        with override('kk'):
            for aggregate_field in aggregate_fields:
                for translatable_key in self.AGGREGATE_TRANSLATABLE_KEYS:
                    value = aggregate_field.get(translatable_key)
                    if isinstance(value, str) and value:
                        aggregate_field[translatable_key] = gettext(value)
        return metadata

    def save(self, *args, **kwargs):
        metadata_kk = self._build_metadata_kk_from_ru(copy.deepcopy(json.loads(self._metadata)))
        self._metadata_kk = json.dumps(metadata_kk, ensure_ascii=False)
        return super().save(*args, **kwargs)

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if user.is_support:
            return True
        else:
            return False

    def get_detail_permission(self, request) -> bool:
        from common.utils import get_tariff_section_codes
        user = request.user.profile
        tariff_section_codes = get_tariff_section_codes(user)
        if self.app_section_code in tariff_section_codes:
            return True
        return False


class UserReportSettingsModel(BaseAbstractModel):
    """Пользовательские шаблоны отчетов."""
    _metadata = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )
    app_section_code = common_fields.CustomCharField(
        max_length=100,
        null=True,
        blank=True,
        default='',
        verbose_name='Относится к разделу приложения'
        )
    name = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Название')
        )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name=_("Описание"),
    )
    base_report = common_fields.CustomForeignKey(
        to='reports.ReportSettingsModel',
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Исходный отчёт'),
        related_name='user_reports',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Пользовательская настройка отчёта'
        verbose_name_plural = 'Пользовательские настройки отчётов'

    @property
    def metadata(self):
        if not self._metadata:
            return {}
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        if isinstance(value, str):
            self._metadata = value
        else:
            self._metadata = json.dumps(value, ensure_ascii=False)

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.UserReportSettingsCreateSerializer
        elif action == 'retrieve':
            return serializers.UserReportSettingsDetailSerializer
        elif action in ('update', 'partial_update',):
            return serializers.UserReportSettingsUpdateSerializer
        else:
            return serializers.UserReportSettingsListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        from common import utils as common_utils
        from common.utils import get_tariff_section_codes
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs.none()

        user = request.user.profile
        tariff_section_codes = get_tariff_section_codes(user)
        qs = qs.filter(base_report__app_section_code__in=tariff_section_codes, author_id=user.pk)

        base_report_id = request.query_params.get('base_report')
        if base_report_id:
            qs = qs.filter(base_report_id=base_report_id)

        search = request.query_params.get('search')
        if isinstance(search, str) and len(search.strip()) >= 3:
            search = search.strip()
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        qs = common_utils.get_filter_queryset(request, cls, qs)
        if not qs.query.order_by:
            qs = qs.order_by('name',)
        return qs.select_related('base_report', 'base_report__category')

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if self.author_id==user.pk:
            return True
        else:
            return False

    def get_detail_permission(self, request) -> bool:
        return self.get_update_permission(request)

