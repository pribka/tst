import datetime
import json

from django.db import models, transaction
from django.db.models import Case, Count, IntegerField, Prefetch, Q, Sum, When
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions as drf_exceptions

from django_q.tasks import async_task
from model_utils import FieldTracker



from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT
from change_history import utils as change_history_utils
from common import fields as common_fields
from common.catalogs.models import ContractorModel
from common.current_profile.middleware import get_current_authenticated_profile
from common.models import (BaseAbstractCatalog, BaseAbstractModel, BaseCatalog,
                           BaseModel)
from common.validators import validate_text_to_json
from contractor_permissions.models import ContractorPermissionModel

from . import utils
from .change_history_utils import (create_update_report_file,
                                   create_update_report_status)
from .report_forms.classes import ReportFormBaseClass
from .utils import check_need_set_calendar_event_by_consolidation


class ReportFormModel(BaseCatalog, BaseAbstractCatalog):
    '''
    TODO Актуализировать информацию!!!!

    Словарь 'report_form_info'. Ключ - значение поля code формы отчетности,
    значение - словарь с ключами:
        'all_reports_validate' - ссылка на функцию валидации всех файлов в
                                 отчетах (перекрестная валидация);
        'consolidation_validate' - ссылка на функцию валидации
                                   консолидированного отчета;
        'create_consolidated_report' - ссылка на функцию создания
                                       консолидированного отчета;
        'single_report_validate' - ссылка на функцию валидации файла отчета. - УБРАТЬ (НЕ ИСПОЛЬЗУЕТСЯ)
        'before_approve' - запускается перед присвоением статуса "Утвержден"
        'file_count' - количество файлов в отчете (None - не ограничено).
        'files_info' - список с информацией о файлах в отчете:
                       code - уникальный идентификатор файла в рамках отчета
                       name - название файла
                       description - краткое описание файла
                       validate - функция для валидации, если None проводиться не будет
    '''

    report_form_info = {
        'f2go': {
            'all_reports_validate': None,
            # 'all_uploaded_files_validate': utils.f2go_all_uploaded_files_validate,
            'consolidation_validate': None,
            'create_consolidated_report': utils.f2go_m_create_consolidated_report,
            'send_documents': utils.f2go_send_documents,
            'before_approve': utils.f2go_before_approve,
            'files_info': [
                {
                    'code': 'f2go',
                    'name': 'Ф2ГО',
                    'description': 'Файл в формате xlsx с отчетом по количеству обращений граждан',
                    'widget': 'CommonFile',
                    'validate': utils.f2go_validate,
                    'save_data': utils.save_f2go_report,
                    'sort': 100,
                },
                {
                    'code': 'disintegration',
                    'name': 'Дезинтеграция',
                    'widget': 'Disintegration',
                    'description': 'Обращения отозванные без маршрутизации или перенесенные в другую систему',
                    'validate': None,
                    'sort': 200,
                },
                {
                    'code': 'risk_matrix',
                    'name': 'Карта рисков',
                    'description': 'Файл, заполненный на основе шаблона',
                    'widget': 'RiskMatrixFile',
                    'validate': utils.risk_matrix_validate,
                    'sort': 300,
                },
            ],
        },
        'f2go_with_verification_act': {
            'all_reports_validate': None,
            # 'all_uploaded_files_validate': utils.f2go_with_verification_act_all_uploaded_files_validate,
            'consolidation_validate': None,
            'create_consolidated_report': utils.f2go_with_verification_act_create_consolidated_report,
            'send_documents': utils.f2go_with_verification_act_send_documents,
            'before_approve': utils.f2go_before_approve,
            'files_info': [
                {
                    'code': 'f2go',
                    'name': 'Отчет Ф2ГО',
                    'widget': 'CommonFile',
                    'description': 'Файл в формате xlsx с отчетом по количеству обращений граждан',
                    'validate': utils.f2go_validate,
                    'sort': 100,
                },
                {
                    'code': 'disintegration',
                    'name': 'Дезинтеграция',
                    'widget': 'Disintegration',
                    'description': 'Обращения отозванные без маршрутизации или перенесенные в другую систему',
                    'validate': None,
                    'sort': 200,
                },
            ],
        },
        'risk_map_with_personal_reception': {
            'all_reports_validate': None,
            # 'all_uploaded_files_validate': utils.f2go_all_uploaded_files_validate,
            'consolidation_validate': None,
            'create_consolidated_report': utils.rmwpr_create_consolidated_report,
            'send_documents': utils.rmwpr_send_documents,
            'before_approve': utils.f2go_before_approve,
            'files_info': [
                {
                    'code': 'f2go',
                    'name': 'Ф2ГО',
                    'description': 'Файл в формате xlsx с отчетом по количеству обращений граждан',
                    'widget': 'CommonFile',
                    'validate': utils.f2go_validate,
                    'save_data': utils.save_f2go_report,
                    'sort': 100,
                },
                {
                    'code': 'disintegration',
                    'name': 'Дезинтеграция',
                    'widget': 'Disintegration',
                    'description': 'Обращения отозванные без маршрутизации или перенесенные в другую систему',
                    'validate': None,
                    'sort': 200,
                },
                {
                    'code': 'risk_matrix',
                    'name': 'Карта рисков',
                    'description': 'Файл, заполненный на основе шаблона',
                    'widget': 'RiskMatrixFile',
                    'validate': utils.risk_matrix_validate,
                    'sort': 300,
                },
                {
                    'code': 'personal_reception',
                    'name': 'Личный прием',
                    'description': 'Личные приемы граждан',
                    'widget': 'PersonalReception',
                    'validate': None,
                    'sort': 400,
                },
            ],
        },
        'ipf_proposal': {
            'all_reports_validate': None,
            'consolidation_validate': None,
            'create_consolidated_report': utils.ipf_create_consolidated_report,
            'send_documents': None,
            'files_info': [
                {
                    'code': 'ipf_proposal',
                    'name': 'Заявка на ИПФ',
                    'widget': 'IpfProposal',
                    'description': 'Файл в формате xlsx с отчетом по количеству обращений граждан',
                    'validate': None,
                },
            ],
        },
        'change_calculation': {
            'all_reports_validate': None,
            'consolidation_validate': None,
            'create_consolidated_report': utils.create_calculation_of_changes_consolidation,
            'send_documents': None,
            'files_info': [
                {
                    'code': 'change_calculation',
                    'name': 'Расчет на внесение изменений в ИПФ',
                    'widget': 'ChangeCalculation',
                    'description': 'Форма отчетности "Расчет на внесение '
                                   'изменений в индивидуальный план '
                                   'финансирования по платежам"',
                    'validate': None,
                },
            ],
        },
        'document_request': {
            'all_reports_validate': None,
            'consolidation_validate': None,
            'create_consolidated_report': None,
            'files_info': [
                {
                    'code': 'file_1',
                    'name': 'Скан паспорта',
                    'description': 'Скан страницы с фотографией',
                    'validate': None,
                },
                {
                    'code': 'file_2',
                    'name': 'Скан паспорта',
                    'description': 'Скан страницы с пропиской',
                    'validate': None,
                },
                {
                    'code': 'file_3',
                    'name': '',
                    'description': '',
                    'validate': None,
                },
                {
                    'code': 'file_4',
                    'name': 'Фото 3х4',
                    'description': '6 фотографий 3х4 с уголком',
                    'validate': None,
                },
            ],
        }
    }
    description = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )
    form_info = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )

    class Meta:
        verbose_name = _('Форма отчета')
        verbose_name_plural = _('Форма отчетов')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ReportFormModelSerializer
        return ReportFormModelSerializer

    def report_form_instance(self):
        return ReportFormBaseClass._subclasses.get(self.code, ReportFormBaseClass)()


class ConsolidationStatusModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Статус консолидации')
        verbose_name_plural = _('Статусы консолидации')

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Цвет'),
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(
            is_active=True
        ).order_by(
            'sort',
            'name',
            'created_at',
        )


class ReportStatusModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Статус отчета')
        verbose_name_plural = _('Статусы отчетов')

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Цвет'),
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(
            is_active=True
        ).order_by(
            'sort',
            'name',
            'created_at',
        )


class ConsolidationFileTypeModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Тип консолидированного файла')
        verbose_name_plural = _('Типы консолидированных файлов')

    description = common_fields.CustomCharField(
        verbose_name=_('Описание'),
        help_text='Краткое описание консолидированного файла',
        max_length=511,
        null=False,
        default='',
        blank=True
    )


class ConsolidationFileModel(BaseCatalog):
    original_file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Файл'),
        related_name='original_consolidation_files',
        null=True,
        blank=True,
    )
    pdf_file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('PDF-файл для просмотра'),
        related_name='pdf_consolidation_files',
        null=True,
        blank=True,
    )
    file_type = common_fields.CustomForeignKey(
        verbose_name=_('Тип консолидированного файла'),
        help_text='Информация о консолидированном файле',
        to='consolidation.ConsolidationFileTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=False,
        default='default'
    )

    class Meta:
        verbose_name = _('Консолидированный отчет')
        verbose_name_plural = _('Консолидированные отчеты')
        ordering = ['sort', 'name', ]

    def get_serializer_class(cls, action=None):
        from .serializers import ConsolidationFileModelSerializer
        return ConsolidationFileModelSerializer

    def get_detail_permission(self, request):
        consolidations = self.consolidations.filter(is_active=True)
        for each in consolidations:
            if each.get_detail_permission(request):
                return True
        return False


class FileTypeModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Тип загружаемого файла')
        verbose_name_plural = _('Типы загружаемых файлов')

    description = common_fields.CustomCharField(
        verbose_name=_('Описание'),
        help_text='Краткое описание загружаемого файла',
        max_length=511,
        null=False,
        default='',
        blank=True
    )
    widget = common_fields.CustomCharField(
        verbose_name=_('Виджет'),
        null=False,
        default='CommonFile',
        max_length=100,
        blank=True
    )


class ReportTypeInfoModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = _('Тип отчета')
        verbose_name_plural = _('Типы отчетов')

    info = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )


class ReportFileModel(BaseCatalog):
    class Meta:
        verbose_name = _('Файл отчета')
        verbose_name_plural = _('Файлы отчетов')
        ordering = ['sort', 'name', ]

    original_file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Файл'),
        related_name='original_files',
        null=True,
        blank=True,
    )
    pdf_file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('PDF-файл для просмотра'),
        related_name='pdf_report_files',
        null=True,
        blank=True,
    )
    file_type = common_fields.CustomForeignKey(
        verbose_name=_('Тип загружаемого файла'),
        help_text='Информация о загружаемом файле',
        to='consolidation.FileTypeModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=False,
        default='default'
    )
    upload_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время загрузки файла'),
    )
    uploaded_by = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Файл загрузил'),
        null=True,
        blank=True,
        related_name='uploaded_files',
    )
    is_generated = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Сгенерирован')
    )

    tracker = FieldTracker(
        fields=(
            'original_file_id',
        )
    )

    # def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
    #     if 'original_file_id' in changed_fields:
    #         user = get_current_authenticated_profile()
    #         after_file_id = getattr(self.original_file, 'pk', None)
    #         transaction.on_commit(
    #             lambda: async_task(
    #                 create_update_report_file,
    #                 self, action_date, changed_fields['original_file_id'], after_file_id, user
    #             )
    #         )

    def get_serializer_class(cls, action=None):
        from .serializers import ReportFileModelSerializer
        return ReportFileModelSerializer

    def get_detail_permission(self, request):
        reports = self.reports.all()
        for each in reports:
            if each.get_detail_permission(request):
                return True
        return False

    @property
    def report(self):
        return self.reports.all().order_by('-created_at').first()


class ReportFileThroughModel(BaseAbstractModel):
    """M2M связь файлов и отчетов."""
    report = models.ForeignKey(
        to='consolidation.ReportModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Отчет'),
        null=True
    )
    file = models.ForeignKey(
        to='consolidation.ReportFileModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Файл'),
        null=True
    )

    class Meta:
        unique_together = (('file', 'report'),)


class ReportModel(BaseCatalog, BaseAbstractCatalog):
    report_files = models.ManyToManyField(
        to='consolidation.ReportFileModel',
        blank=True,
        related_name='reports',
        verbose_name=_('Прикрепленные файлы'),
        through=ReportFileThroughModel,
    )
    consolidator = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Консолидатор'),
        null=True,
        blank=True,
        related_name='consolidated_reports',
    )
    parent = common_fields.CustomForeignKey(
        to='ConsolidationModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='source_reports',
        verbose_name=_('Консолидация, целевой отчет'),
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация'),
        related_name='reports'
    )
    status = common_fields.CustomForeignKey(
        to='consolidation.ReportStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='new',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус'),
    )
    no_inquiries = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Нет обращений'),
        help_text='Для формы отчетности с кодом f2go. True если за период обращений не было.',
    )
    report_type = common_fields.CustomForeignKey(
        verbose_name=_('Тип отчета'),
        to='consolidation.ReportTypeInfoModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        blank=False,
        default='default'
    )
    tracker = FieldTracker(
        fields=(
            'status_id',
        )
    )
    without_attachments = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Отчет без прикрепленных объектов'),
        help_text='True если в отчет нечего загрузить'
    )

    # def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
    #     if 'status_id' in changed_fields:
    #         status_code_before = changed_fields['status_id']
    #         status_code_after = self.status.code
    #         user = get_current_authenticated_profile()
    #         transaction.on_commit(lambda: async_task(
    #             create_update_report_status,
    #             self, action_date, status_code_before, status_code_after, user
    #             )
    #         )

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return cls.objects.none()
        return cls.objects.filter(
            is_active=True
        ).select_related(
            'consolidator',
            'contractor',
            'report_type',
            'status',
        ).prefetch_related(
            Prefetch(
                'report_files',
                queryset=ReportFileModel.objects.filter(
                    is_active=True
                ).select_related(
                    'original_file',
                    'pdf_file',
                    'uploaded_by',
                ).prefetch_related(
                    'file_type',
                )
            )
        ).order_by(
            'contractor__name',
            'sort'
        )

    def __str__(self):
        return f'{self.parent.__str__()} от {self.contractor.name}'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (ReportModelDetailSerializer,
                                  ReportModelNotifySerializer)
        if action == 'retrieve':
            return ReportModelDetailSerializer
        elif action == 'notify':
            return ReportModelNotifySerializer
        else:
            return ReportModelDetailSerializer

    def get_update_is_disabled(self) -> bool:
        parent = self.parent
        report_form_instance = parent.report_form.report_form_instance()
        is_disabled, message = report_form_instance.report_update_is_disabled(
            consolidation=parent,
            report=self
        )
        return is_disabled, message

    def get_update_permission(self, request=None) -> bool:
        if not request:
            return False
        user = request.user.profile
        parent = self.parent
        if parent.is_scheduled:
            return False
        permissive_status_list = [
            'new',
            'on_review',
            'rejected',
            'not_loaded']
        if parent.auto_approve:
            permissive_status_list.append('approved')
        if self.status.code not in permissive_status_list:
            return False
        from common.utils import use_access_groups
        if use_access_groups(user.pk):
            from contractor_permissions.utils import check_contractor_permission
            try:
                check_contractor_permission(user.pk, self.contractor_id, 'send_report', None)
            except drf_exceptions.PermissionDenied:
                try:
                    check_contractor_permission(user.pk, self.contractor_id, 'create_consolidation', None)
                except drf_exceptions.PermissionDenied:
                    return False
                else:
                    return True
            else:
                return True
        else:
            return ContractorPermissionModel.objects.filter(
                        Q(aux_conditions=parent.report_form) | Q(
                            aux_conditions__isnull=True),
                        is_active=True,
                        contractor_permission_role__is_active=True,
                        permission_type_id='send_report',
                        contractor_permission_role__contractor_profiles__user=user,
                        contractor_permission_role__contractor_id=self.contractor
                    ).exists()

    def get_detail_permission(self, request=None):
        if not request:
            return False
        user = request.user.profile
        parent = self.parent
        from common.utils import use_access_groups
        if use_access_groups(user.pk):
            from contractor_permissions.utils import check_contractor_permission
            try:
                check_contractor_permission(user.pk, parent.org_administrator_id, 'create_consolidation', None)
            except drf_exceptions.PermissionDenied:
                try:
                    check_contractor_permission(user.pk, self.contractor_id, 'send_report', None)
                except drf_exceptions.PermissionDenied:
                    return False
                else:
                    return True
            else:
                return True
        else:
            return ContractorPermissionModel.objects.filter(
                (Q(
                    # Есть право на создать консолидацию
                    permission_type_id='create_consolidation',
                    contractor_permission_role__contractor_profiles__user=user,
                    contractor_permission_role__contractor_id=parent.org_administrator,
                    contractor_permission_role__is_active=True,
                ) | Q(
                    # или есть право загрузить в нее отчет
                    permission_type_id='send_report',
                    contractor_permission_role__contractor_profiles__user=user,
                    contractor_permission_role__contractor_id=self.contractor,
                    contractor_permission_role__is_active=True,
                )),
                (Q(
                    aux_conditions=parent.report_form
                ) | Q(
                    aux_conditions__isnull=True
                ))).exists()

    @classmethod
    def get_table_columns(cls):
        return ['type',
                'status',
                'contractor',
                'start',
                'end']

    class Meta:
        verbose_name = _('Отчет')
        verbose_name_plural = _('Отчеты')


class ConsolidationMemberModel(BaseModel):
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
        related_name='consolidations'
    )
    consolidation = common_fields.CustomForeignKey(
        to='consolidation.ConsolidationModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Консолидация'),
        related_name='consolidation_members',
    )
    tracker = FieldTracker(
        fields=(
            'consolidation',
            'organization',
        )
    )

    class Meta:
        verbose_name = _('Организация консолидации')
        verbose_name_plural = _('Организация консолидации')
        unique_together = (('organization', 'consolidation',),)

    # def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
    #     if created:
    #         change_history_utils.create_add_m2m(
    #             self.consolidation.pk,
    #             action_date,
    #             'consolidation__members',
    #             self.organization.name,
    #             {self.pk}
    #         )
    #         return
    #     if deleted:
    #         change_history_utils.create_remove_m2m(
    #             self.consolidation.pk,
    #             action_date,
    #             'consolidation__members',
    #             self.organization.name,
    #             {self.pk}
    #         )


class ConsolidationModel(BaseCatalog, BaseAbstractCatalog):
    REPEAT_PERIOD_CHOICES = (
        ('WEEKLY', 'Еженедельно'),
        ('MONTHLY', 'Ежемесячно'),
        ('YEARLY', 'Ежегодно'),
    )
    consolidation_files = models.ManyToManyField(
        to='consolidation.ConsolidationFileModel',
        blank=True,
        related_name='consolidations',
        verbose_name=_('Итоговые отчеты')
    )
    consolidated_at = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата и время создания консолидированного отчета'),
    )
    org_administrator = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация администратор'),
        related_name='own_consolidations'
    )
    members = models.ManyToManyField(
        'catalogs.ContractorModel',
        through='consolidation.ConsolidationMemberModel',
        verbose_name=_('Организации'),
        through_fields=('consolidation', 'organization')
    )
    report_form = common_fields.CustomForeignKey(
        to='consolidation.ReportFormModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Форма отчета'),
    )
    status = common_fields.CustomForeignKey(
        to='consolidation.ConsolidationStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='new',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус'),
    )
    dead_line = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Крайний срок подачи отчетов'),
    )
    start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Начало периода'),
    )
    end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Конец периода'),
    )
    consolidator = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Ответственный за консолидацию'),
        null=True,
        blank=True,
        related_name='consolidations',
    )
    auto_approve = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Автоматическое утверждение'),
        help_text='Присваивать отчету статус "Утвержден" после успешной проверки файла',
    )
    add_org_administrator_in_members = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Добавить организацию-администратора'),
        help_text='Добавить организацию-администратора в список организаций-участников',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )
    is_scheduled = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Периодическая задача'),
        help_text='Автоматическое создание консолидации в заданной периодичностью',
    )
    is_template_on = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Состояние шаблона'),
        help_text='Находится ли данный шаблон в активном состоянии',
    )
    next_creation_date = common_fields.CustomDateTimeField(
        verbose_name=_('Дата и время следующего создания'),
        null=True,
        blank=True,
    )
    repeat_period = common_fields.CustomCharField(
        choices=REPEAT_PERIOD_CHOICES,
        max_length=10,
        verbose_name=_('Периодичность'),
        null=True,
        default='',
        blank=True
    )
    repeat_to = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Повторять до'),
        help_text='Поле используется в шаблонах консолидаций',
    )
    next_dead_line = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Следующий крайний срок подачи отчетов'),
        help_text='Поле используется в шаблонах консолидаций',
    )
    next_start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Следующее начало периода'),
        help_text='Поле используется в шаблонах консолидаций',
    )
    next_end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Следующий конец периода'),
        help_text='Поле используется в шаблонах консолидаций',
    )
    template = common_fields.CustomForeignKey(
        'self',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Созданный шаблон'),
        null=True,
        blank=True,
        related_name='source_consolidations',
        help_text='Шаблона созданный на основе данной консолидаций',
    )

    generate_report_files = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Генерировать файлы отчетов из базы данных'),
    )

    tracker = FieldTracker(
        fields=(
            'name',
            'description',
            'dead_line',
            'org_administrator_id',
            'report_form_id',
            'status_id',
            'start',
            'end',
            'auto_approve',
            'add_org_administrator_in_members',
            'is_scheduled',
            'repeat_period',
            'repeat_to',
            'generate_report_files',
        )
    )

    def track_m2m_fields(self, sender, model, pk_set, action, action_date):
        sender_label = sender._meta.label
        if sender_label == 'common.FileBaseModel':
            object_property_id = 'consolidation__attachments'
            str_view = ','.join([each.full_name for each in list(model.objects.filter(pk__in=pk_set))])
        else:
            return
        if action == 'post_add':
            change_history_utils.create_add_m2m(
                self.pk,
                action_date,
                object_property_id,
                str_view,
                pk_set,
            )
        elif action == 'post_remove':
            change_history_utils.create_remove_m2m(
                self.pk,
                action_date,
                object_property_id,
                str_view,
                pk_set,
            )

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        if 'name' in changed_fields:
            before = changed_fields['name'],
            after = self.name,
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'consolidation__name',
                before,
                after,
            )
        if 'description' in changed_fields:
            before = changed_fields['description']
            after = self.description
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'consolidation__description',
                before,
                after,
            )
        if 'dead_line' in changed_fields:
            dead_line_before = changed_fields['dead_line']
            dead_line_after = self.dead_line
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'consolidation__dead_line',
                dead_line_before,
                dead_line_after,
            )
        if 'org_administrator_id' in changed_fields:
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'consolidation__org_administrator',
                changed_fields['org_administrator_id'],
                self.org_administrator.pk,
            )
        if 'report_form_id' in changed_fields:
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'consolidation__report_form',
                changed_fields['report_form_id'],
                self.report_form.pk
            )
        if 'status_id' in changed_fields:
            status_code_before = changed_fields['status_id']
            if status_code_before:
                status_id_before = ConsolidationStatusModel.objects.get(code=status_code_before).pk
            else:
                status_id_before = None
            status_id_after = self.status.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'consolidation__status',
                status_id_before,
                status_id_after,
            )
        if 'start' in changed_fields:
            start_before = changed_fields['start']
            start_after = self.start
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'consolidation__start',
                start_before,
                start_after,
            )
        if 'end' in changed_fields:
            end_before = changed_fields['end']
            end_after = self.end
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'consolidation__end',
                end_before,
                end_after,
            )
        if 'auto_approve' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'consolidation__auto_approve',
                self.auto_approve,
            )
        if 'add_org_administrator_in_members' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'consolidation__add_org_administrator_in_members',
                self.add_org_administrator_in_members,
            )
        if 'is_scheduled' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'consolidation__is_scheduled',
                self.is_scheduled,
            )
        if 'repeat_period' in changed_fields:
            repeat_period_choices_dict = dict(self.REPEAT_PERIOD_CHOICES)
            repeat_period_before = repeat_period_choices_dict.get(changed_fields['repeat_period'], '')
            repeat_period_after = repeat_period_choices_dict.get(self.repeat_period, '')
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'consolidation__repeat_period',
                repeat_period_before,
                repeat_period_after,
            )
        if 'repeat_to' in changed_fields:
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'consolidation__repeat_to',
                changed_fields['repeat_to'],
                self.repeat_to,
            )
        if 'generate_report_files' in changed_fields:
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'consolidation__generate_report_files',
                self.generate_report_files,
            )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (ConsolidationModelCreateSerializer,
                                  ConsolidationModelDetailSerializer,
                                  ConsolidationModelListSerializer,
                                  ConsolidationModelUpdateSerializer)
        if not action:
            return ConsolidationModelListSerializer
        if action == 'list':
            return ConsolidationModelListSerializer
        elif action == 'retrieve':
            return ConsolidationModelDetailSerializer
        elif action in ('update', 'partial_update'):
            return ConsolidationModelUpdateSerializer
        elif action == 'create':
            return ConsolidationModelCreateSerializer
        else:
            return ConsolidationModelListSerializer

    def get_update_permission(self, request=None) -> bool:
        if not request:
            return False
        user = request.user.profile
        from common.utils import use_access_groups
        if use_access_groups(user.pk):
            from contractor_permissions.utils import check_contractor_permission
            try:
                check_contractor_permission(user.pk, self.org_administrator.pk, 'create_consolidation', None)
            except drf_exceptions.PermissionDenied:
                return False
            else:
                return True
        else:
            return ContractorPermissionModel.objects.filter(
                Q(aux_conditions=self.report_form) | Q(
                    aux_conditions__isnull=True),
                permission_type_id='create_consolidation',
                contractor_permission_role__contractor_profiles__user=user,
                contractor_permission_role__contractor_id=self.org_administrator,
                contractor_permission_role__is_active=True,
            ).exists()

    def get_detail_permission(self, request=None):
        if not request:
            return False
        user = request.user.profile
        if user.is_support:
            return True
        from common.utils import use_access_groups
        from contractor_permissions.utils import contractors_where_user_has_permission
        members = self.members.all().values_list('pk', flat=True)

        if use_access_groups(user.pk):
            create_consolidation_contractors = set(
                contractors_where_user_has_permission(user.pk, 'create_consolidation', None)
            )
            send_report_contractors = set(
                contractors_where_user_has_permission(user.pk, 'send_report', None)
            )
            return (self.org_administrator.pk in create_consolidation_contractors) or not send_report_contractors.isdisjoint(set(members))
        else:
            members = self.members.all()
            return ContractorPermissionModel.objects.filter(
                (Q(
                    # Есть право на создать консолидацию
                    permission_type_id='create_consolidation',
                    contractor_permission_role__contractor_profiles__user=user,
                    contractor_permission_role__contractor_id=self.org_administrator,
                    contractor_permission_role__is_active=True,
                ) | Q(
                    # или есть право загрузить в нее отчет
                    permission_type_id='send_report',
                    contractor_permission_role__contractor_profiles__user=user,
                    contractor_permission_role__contractor_id__in=members,
                    contractor_permission_role__is_active=True,
                )),
                (Q(
                    aux_conditions=self.report_form
                ) | Q(
                    aux_conditions__isnull=True
                ))).exists()

    def get_delete_permission(self, request=None) -> bool:
        if not request:
            return False
        return (self.get_update_permission(request) and
                self.status.code in ('new', 'in_progress', 'ready_to_consolidate'))

    def all_reports_is_approved(self) -> bool:
        return not self.source_reports.filter(
            is_active=True
        ).exclude(
            status__code='approved'
        ).exists()

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return cls.objects.none()
        user = request.user.profile
        if user.is_support:
            return cls.objects.filter(
                is_active=True
            ).select_related(
            ).prefetch_related(
                'consolidation_files',
                'consolidation_files__original_file',
                'consolidation_files__pdf_file',
                'report_form',
                'source_reports',
                'source_reports__contractor',
                'status',
                Prefetch(
                    'members',
                    queryset=ContractorModel.objects.filter(is_active=True)
                )
            ).order_by('-created_at').distinct()
        my_organizations = user.my_organizations
        all_report_forms = ReportFormModel.objects.filter(
            is_active=True
        ).values_list('id', flat=True)
        lookup = Q()
        from common.utils import use_access_groups
        from contractor_permissions.utils import contractors_where_user_has_permission
        if use_access_groups(user.pk):
            contractors_create = contractors_where_user_has_permission(user.pk, 'create_consolidation', None)
            contractors_report = contractors_where_user_has_permission(user.pk, 'send_report', None)
            lookup = Q(org_administrator__in=contractors_create) | Q(source_reports__contractor__in=contractors_report)
        else:
            for org in my_organizations:
                report_form_ids = ContractorPermissionModel.objects.filter(
                    contractor_permission_role__is_active=True,
                    contractor_permission_role__contractor=org,
                    contractor_permission_role__contractor_profiles__user=user,
                    permission_type_id='create_consolidation'
                ).values_list('aux_conditions', flat=True)
                if None in report_form_ids:
                    report_form_ids = all_report_forms
                if report_form_ids:
                    lookup |= Q(
                        org_administrator=org,
                        report_form_id__in=report_form_ids
                    )
                report_form_ids = ContractorPermissionModel.objects.filter(
                    contractor_permission_role__is_active=True,
                    contractor_permission_role__contractor=org,
                    contractor_permission_role__contractor_profiles__user=user,
                    permission_type_id='send_report'
                ).values_list('aux_conditions', flat=True)
                if None in report_form_ids:
                    report_form_ids = all_report_forms
                if report_form_ids:
                    lookup |= Q(
                        source_reports__contractor=org,
                        report_form_id__in=report_form_ids
                    )
        if lookup:
            return cls.objects.filter(
                lookup,
                is_active=True
            ).select_related(
            ).prefetch_related(
                'consolidation_files',
                'consolidation_files__original_file',
                'consolidation_files__pdf_file',
                'report_form',
                'source_reports',
                'source_reports__contractor',
                'status',
                Prefetch(
                    'members',
                    queryset=ContractorModel.objects.filter(is_active=True)
                )
            ).order_by('-created_at').distinct()
        else:
            return cls.objects.none()

    @classmethod
    def get_table_columns(cls):
        return [
            'auto_approve',
            'end',
            'org_administrator',
            'report_form',
            'start',
            'status'
        ]

    def summary(self):
        return self.source_reports.filter(
            is_active=True
        ).aggregate(
            total=Count('id'),
            approved=Sum(
                Case(
                    When(status_id='approved', then=1),
                    output_field=IntegerField(),
                    default=0
                )
            ),
            not_loaded=Sum(
                Case(
                    When(status_id='not_loaded', then=1),
                    output_field=IntegerField(),
                    default=0
                )
            ),
            rejected=Sum(
                Case(
                    When(status_id='rejected', then=1),
                    output_field=IntegerField(),
                    default=0
                )
            ),
            on_review=Sum(
                Case(
                    When(status_id='on_review', then=1),
                    output_field=IntegerField(),
                    default=0
                )
            )
        )

    def __str__(self):
        return f'{self.report_form.name} для {self.org_administrator} {self.start.strftime("%d.%m.%Y")} - {self.end.strftime("%d.%m.%Y")}'

    @property
    def frontend_route(self):
        # переопределяем в целевой модели
        return '/consolidation?consolidation=' + str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        transaction.on_commit(lambda: async_task(
            check_need_set_calendar_event_by_consolidation,
            str(self.id),
            timeout=10
        ))

    def get_report_form_instance(self):
        return self.report_form.report_form_instance()

    class Meta:
        verbose_name = _('Консолидация')
        verbose_name_plural = _('Консолидации')


class F2GOReportModel(BaseModel):
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
        related_name='f2go_reports'
    )
    report_form = common_fields.CustomForeignKey(
        to='consolidation.ReportFormModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Форма отчета'),
    )
    start = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Начало периода'),
    )
    end = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Конец периода'),
    )
    data = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
    )

    class Meta:
        verbose_name = _('Отчет Ф2ГО')
        verbose_name_plural = _('Отчеты Ф2ГО')


class AnalyticReportModel(BaseCatalog, BaseAbstractCatalog):
    report_form = common_fields.CustomForeignKey(
        to='consolidation.ReportFormModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Форма отчета'),
    )
    report_info = models.TextField(
        null=False,
        blank=False,
        default='',
        validators=(validate_text_to_json,),
        verbose_name=_('Данные для создания отчета'),
    )

    class Meta:
        verbose_name = _('Аналитический отчет')
        verbose_name_plural = _('Аналитические отчеты')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import AnalyticReportModelSerializer
        return AnalyticReportModelSerializer

    def get_report_info(self):
        if not self.report_info:
            return None, None
        report_info = json.loads(self.report_info)
        data = report_info.get('data', None)
        utility = report_info.get('utility', None)
        if not utility:
            return None, data
        try:
            get_analytic_function = import_string(utility)
        except ImportError:
            return None, data
        else:
            return get_analytic_function, data


class ContractorBalanceModel(BaseAbstractModel):
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=False,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
        related_name='balance'
    )
    year = common_fields.CustomPositiveIntegerField(
        null=False,
        blank=True,
        default=2023,
        verbose_name=_('Год'),
    )
    balance = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Остаток обращений на начало года')
    )

    class Meta:
        verbose_name = _('Остатки обращений')
        verbose_name_plural = _('Остатки обращений')
        unique_together = (('contractor', 'year',),)


class DisintegrationModel(BaseModel):
    report = common_fields.CustomOneToOneField(
        to='consolidation.ReportModel',
        blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='disintegration'
    )
    revoked_without_routing = common_fields.CustomPositiveIntegerField(
        blank=True,
        null=False,
        default=0,
        verbose_name=_('Отозвано без маршрутизации')
    )
    transferring_to_another_system = common_fields.CustomPositiveIntegerField(
        blank=True,
        null=False,
        default=0,
        verbose_name=_('Перенос в другую систему')
    )

    class Meta:
        verbose_name = _('Дезинтеграция')
        verbose_name_plural = _('Дезинтеграции')


class ReportPersonalReceptionModel(BaseModel):
    report = common_fields.CustomOneToOneField(
        to='consolidation.ReportModel',
        blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='personal_reception'
    )
    quantity = common_fields.CustomPositiveIntegerField(
        blank=True,
        null=False,
        default=0,
        verbose_name=_('Количество приемов за период')
    )
    no_personal_reception = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Личный приём не проводился')
    )
    issues = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Обращения')
    )

    class Meta:
        verbose_name = _('Личный прием граждан')
        verbose_name_plural = _('Личные приемы граждан')
