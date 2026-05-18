import datetime
from django.db import models, transaction

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Case, When, Value, IntegerField

from rest_framework import exceptions as drf_exceptions

from mptt.models import MPTTModel, TreeForeignKey
from model_utils import FieldTracker

from django_q.tasks import async_task

from common.models import (BaseAbstractCatalog, BaseAbstractModel, BaseCatalog,
                           BaseModel, MetadataAbstractModel)
from common import fields as common_fields
from common.current_profile.middleware import get_current_authenticated_profile

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT, CUSTOM_SET_NULL

from contractor_permissions.utils import check_contractor_permission

from users.utils import get_descendants_departments_related_organizations

from change_history import utils as change_history_utils

from . import fields
from .change_history_utils import create_update_criteria_value


class AssessmentCriteriaModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = _('Критерий оценки')
        verbose_name_plural = _('Критерии оценки')

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(
            is_active=True
        ).order_by(
            'sort',
            'name',
            'created_at',
        )


class AssessmentTypeCriteriaModel(BaseAbstractModel):
    criteria = common_fields.CustomForeignKey(
        to='risk_assessment.AssessmentCriteriaModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='assessment_type_criteria',
        verbose_name=_('Критерий оценки'),
    )
    assessment_type = common_fields.CustomForeignKey(
        to='risk_assessment.RiskAssessmentTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='assessment_type_criteria',
        verbose_name=_('Тип оценки'),
    )
    max_value = common_fields.CustomPositiveIntegerField(
        null=False,
        default=1,
        blank=True,
        verbose_name=_('Максимальное значение'),
    )

    class Meta:
        verbose_name = _('Критерий типа оценки')
        verbose_name_plural = _('Критерии типа оценки')


class RiskAssessmentTypeModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = _('Тип оценки')
        verbose_name_plural = _('Типы оценок')


class IssueCategoryModel(MPTTModel, BaseCatalog, BaseAbstractCatalog, MetadataAbstractModel):
    parent = TreeForeignKey('self', on_delete=CUSTOM_PROTECT, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name = _('Категория обращения')
        verbose_name_plural = _('Категории обращений')

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        return qs

    @classmethod
    def get_select_queryset(cls, request=None):
        if request:
            text = request.query_params.get('text')
            if text:
                queryset = cls.objects.filter(is_active=True, name__icontains=text)
            else:
                parent = request.query_params.get('parent', 'root')
                if parent == 'root':
                    queryset = cls.objects.filter(
                        is_active=True,
                        parent__isnull=True)
                else:
                    queryset = cls.objects.filter(
                        is_active=True,
                        parent=parent)
        else:
            return cls.objects.none()
        return queryset.annotate(
            priority=Case(
                When(code="not_specified", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("priority", "name")


class IssueTypeModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = _('Вид обращения')
        verbose_name_plural = _('Виды обращений')


class CitizensSocialStatusModel(BaseCatalog, BaseAbstractCatalog):
    pass

    class Meta:
        verbose_name = _('Социальный статус гражданина')
        verbose_name_plural = _('Социальные статусы граждан')


class PersonalReceptionStatusModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        max_length=31,
        null=True,
        default='',
        blank=False,
        verbose_name=_('Цвет')
    )

    class Meta:
        verbose_name = _('Статус обращения при личном приеме')
        verbose_name_plural = _('Статусы обращений при личном приеме')


class PersonalReceptionModel(BaseCatalog):
    issue = common_fields.CustomOneToOneField(
        to='risk_assessment.IssueModel',
        null=False,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Обращение'),
        related_name='personal_reception',
    )
    social_status = common_fields.CustomForeignKey(
        to='risk_assessment.CitizensSocialStatusModel',
        to_field='code',
        null=False,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Социальный статус'),
        related_name='personal_receptions',
    )
    status = common_fields.CustomForeignKey(
        to='risk_assessment.PersonalReceptionStatusModel',
        to_field='code',
        null=False,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус обращения'),
        related_name='personal_receptions',
    )
    days_in_queue = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Количество дней в очереди'),
    )

    class Meta:
        verbose_name = _('Личный прием')
        verbose_name_plural = _('Личные приемы')


class IssueModel(BaseModel):
    issue_type = common_fields.CustomForeignKey(
        to='risk_assessment.IssueTypeModel',
        to_field='code',
        null=True,
        blank=False,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Вид обращения'),
        related_name='issues',
    )
    issue_category = common_fields.CustomForeignKey(
        to='risk_assessment.IssueCategoryModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Категория обращения'),
        related_name='issues',
    )
    number = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='',
        blank=False,
        verbose_name=_('Номер'),
    )
    # TODO в будущем удалить, т.к. заменен issue_category. 2024-11-27
    summary = common_fields.CustomCharField(
        max_length=511,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Характер вопроса'),
    )
    text = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name=_('Текст обращения')
    )
    issue_date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата обращения'),
    )

    tracker = FieldTracker(
        fields=(
            'issue_type_id',
            'number',
            'summary',
            'text',
            'issue_date',
        )
    )

    class Meta:
        verbose_name = _('Обращение')
        verbose_name_plural = _('Обращения')

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        risk_assessments = self.risk_assessments.filter(is_active=True) # noqa
        if 'issue_type_id' in changed_fields:
            issue_type_code_before = changed_fields['issue_type_id']
            if issue_type_code_before:
                issue_type_id_before = IssueTypeModel.objects.get(code=issue_type_code_before).pk
            else:
                issue_type_id_before = None
            issue_type_id_after = self.issue_type.pk
            for each in risk_assessments:
                change_history_utils.create_update_catalog_fk(
                    each.pk,
                    action_date,
                    'risk_assessment__issue__issue_type',
                    issue_type_id_before,
                    issue_type_id_after,
                )
        if 'number' in changed_fields:
            before = changed_fields['number']
            after = self.number
            for each in risk_assessments:
                change_history_utils.create_update_str(
                    each.pk,
                    action_date,
                    'risk_assessment__issue__number',
                    before,
                    after,
                )
        if 'summary' in changed_fields:
            before = changed_fields['summary']
            after = self.number
            for each in risk_assessments:
                change_history_utils.create_update_str(
                    each.pk,
                    action_date,
                    'risk_assessment__issue__summary',
                    before,
                    after,
                )
        if 'text' in changed_fields:
            before = changed_fields['text']
            after = self.number
            for each in risk_assessments:
                change_history_utils.create_update_str(
                    each.pk,
                    action_date,
                    'risk_assessment__issue__text',
                    before,
                    after,
                )
        if 'issue_date' in changed_fields:
            issue_date_before = changed_fields['issue_date']
            issue_date_after = self.issue_date
            for each in risk_assessments:
                change_history_utils.create_update_datetime(
                    each.pk,
                    action_date,
                    'risk_assessment__issue__issue_date',
                    issue_date_before,
                    issue_date_after,
                )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # from .utils import index_risk_assessment_model
        # transaction.on_commit(lambda: async_task(index_risk_assessment_model, self))


class RiskAssessmentStatusModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        max_length=31,
        null=True,
        default='',
        blank=False,
        verbose_name=_('Цвет')
    )

    class Meta:
        verbose_name = _('Статус оценки риска')
        verbose_name_plural = _('Статусы оценки риска')


class RiskAssessmentModel(BaseModel):
    status = common_fields.CustomForeignKey(
        to='risk_assessment.RiskAssessmentStatusModel',
        to_field='code',
        null=False,
        default='new',
        verbose_name=_('Статус'),
        on_delete=CUSTOM_PROTECT,
    )
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        verbose_name=_('Организация'),
        related_name='risk_assessments',
        on_delete=CUSTOM_PROTECT,
    )
    assessment_type = common_fields.CustomForeignKey(
        to='risk_assessment.RiskAssessmentTypeModel',
        to_field='code',
        null=False,
        blank=False,
        default='primary',
        verbose_name=_('Тип оценки'),
        related_name='risk_assessments',
        on_delete=CUSTOM_PROTECT,
    )

    issue = common_fields.CustomForeignKey(
        to='risk_assessment.IssueModel',
        null=True,
        blank=False,
        verbose_name=_('Обращение'),
        related_name='risk_assessments',
        on_delete=CUSTOM_PROTECT,
    )
    total_value = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Итоговое значение')
    )
    sent_for = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Направлено для рассмотрения'),
        help_text='0 - Первый руководитель, 1 - Руководитель аппарата, 2 - Заместитель первого руководителя'
    )
    issue_date_filter = fields.IssueDateFilterField()
    issue_number_filter = fields.IssueNumberFilterField()
    total_value_filter = fields.TotalValueFilterField()
    organizations_filter = fields.OrganizationsFilterField()
    category_filter = fields.CategoryFilterField()

    tracker = FieldTracker(
        fields=('status_id', 'sent_for')
    )

    class Meta:
        verbose_name = _('Оценка риска')
        verbose_name_plural = _('Оценки риска')
        unique_together = (('issue', 'assessment_type',),)

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        if 'sent_for' in changed_fields:
            before = changed_fields['sent_for']
            after = self.sent_for
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'risk_assessment__sent_for',
                before,
                after,
            )
        # if 'status_id' in changed_fields:
        #     status_code_before = changed_fields['status_id']
        #     if status_code_before:
        #         status_id_before = RiskAssessmentStatusModel.objects.get(code=status_code_before).pk
        #     else:
        #         status_id_before = None
        #     status_id_after = self.status.pk
        #     change_history_utils.create_update_catalog_fk(
        #         self.pk,
        #         action_date,
        #         'risk_assessment__status',
        #         status_id_before,
        #         status_id_after,
        #     )

    @property
    def name(self):
        return f'{getattr(self.assessment_type, "name", "")} {getattr(self.issue, "number", "")}'

    def __str__(self):
        return self.name

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if user.is_support:
            return True
        if self.author != user and self.status.code == 'processed':
            return False
        try:
            check_contractor_permission(
                user.pk, self.organization.pk, 'create_risk_assessment', self.assessment_type.pk
            )
        except drf_exceptions.PermissionDenied:
            return False
        return True

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        organizations = get_descendants_departments_related_organizations(user.my_organizations)
        if self.organization.pk in organizations:
            return True
        return False

    def set_is_active(self, value: bool, request):
        if not self.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.RiskAssessmentModelDetailSerializer
        elif action == 'create':
            return serializers.RiskAssessmentModelCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.RiskAssessmentModelUpdateSerializer
        else:
            return serializers.RiskAssessmentModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        user = request.user.profile
        organizations = get_descendants_departments_related_organizations(user.my_organizations)
        qs = cls.objects.prefetch_related(
            # 'location_points__admin_area'
        ).select_related(
            'issue',
            'organization',
            'assessment_type',
            'status',
        ).filter(is_active=True, organization_id__in=organizations)
        return qs.order_by('-created_at',)

    @classmethod
    def search_input(cls):
        return False

    @classmethod
    def get_table_columns(cls):
        return [
            'organization',
            'issue_number_filter',
            'category_filter',
            'filter_total_value',
            'issue_date_filter',
            'status'
        ]

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        data = super().get_filter_fields(exclude=exclude, request=request)
        data = list(
            filter(
                lambda x: x.get('name', '') not in (
                    'issue_date_filter',
                    'issue_date_filter__exclude',
                    'status',
                    'status__exclude'
                ),
                data
            )
        )
        return data


class RiskAssessmentCriteriaModel(BaseAbstractModel):
    risk_assessment = common_fields.CustomForeignKey(
        to='risk_assessment.RiskAssessmentModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        verbose_name=_('Оценка риска'),
        related_name='risk_assessment_criteria',
    )
    criteria = common_fields.CustomForeignKey(
        to='risk_assessment.AssessmentCriteriaModel',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=False,
        verbose_name=_('Критерий'),
        related_name='risk_assessment_criteria',
    )
    value = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Значение'),
    )

    tracker = FieldTracker(
        fields=('value',)
    )

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False, deleted: bool = False):
        if not changed_fields:
            return

        if 'value' in changed_fields:
            before = changed_fields['value']
            after = self.value
            author = get_current_authenticated_profile()
            transaction.on_commit(
                lambda: async_task(create_update_criteria_value, self.pk, action_date, before, after, author)
            )

    class Meta:
        verbose_name = _('Критерий оценки риска')
        verbose_name_plural = _('Критерии оценки риска')
