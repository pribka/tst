import json
import datetime

from django_q.tasks import async_task

from django.db import transaction
from django.db import models, IntegrityError
from django.db.models import Q, F, OuterRef, Subquery, Value
from django.db.models.expressions import Func
from django.db.models.functions import Cast, Coalesce, Concat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from rest_framework import exceptions as drf_exceptions

from model_utils import FieldTracker

from common import fields as common_fields
from common.models import BaseModel, BaseAbstractModel, BaseCatalog, BaseAbstractCatalog
from common.validators import validate_text_to_json

from change_history import utils as change_history_utils

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT, URLS


class WorkflowRequestTypeModel(BaseCatalog, BaseAbstractCatalog):
    
    meta_exclude_fields = ['author', 'name', 'code', 'mentions', 'ct', 'created_at',
                            'completion_status', 'visors', '_metadata', ]

    completion_status = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestStatusModel',
        to_field='code',
        null=False,
        default='paid',
        on_delete=CUSTOM_PROTECT,
        related_name='workflow_request_types',
        verbose_name=_('Статус завершения')
    )

    visors = models.ManyToManyField(
        to='catalogs.ContractorProfileModel',
        through='processes.WorkflowRequestTypeVisorModel',
        through_fields=('request_type', 'contractor_profile',),
        related_name='workflow_request_types',
    )

    _metadata = models.TextField(
        null=False,
        blank=False,
        default='{}',
        validators=(validate_text_to_json,),
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        related_name='request_types',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Организация',
    )

    class Meta:
        verbose_name = _('Тип заявки')
        verbose_name_plural = _('Типы заявки')

    @property
    def metadata(self):
        return json.loads(self._metadata)

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            WorkflowRequestTypeSerializer,
            WorkflowRequestTypeCreateSerializer,
            WorkflowRequestTypeUpdateSerializer,
            WorkflowRequestTypeDetailSerializer,
        )
        if action == 'create':
            return WorkflowRequestTypeCreateSerializer
        elif action in ('update', 'partial_update',):
            return WorkflowRequestTypeUpdateSerializer
        elif action == 'retrieve':
            return WorkflowRequestTypeDetailSerializer
        return WorkflowRequestTypeSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        if not request:
            return qs
        if request.user.is_anonymous:
            return qs.none()
        user = request.user.profile
        from users.utils import get_ancestor_departments_related_organizations
        contractors = user.my_organizations
        if not contractors:
            return qs.none()
        allowed_contractors = get_ancestor_departments_related_organizations(contractors, include_self=True)
        qs = qs.filter(Q(contractor__isnull=True) | Q(contractor_id__in=allowed_contractors))
        return qs.order_by('sort', 'name',)

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

    def get_update_permission(self, request=None):
        if not request:
            return False
        user = request.user
        if user.is_anonymous:
            return False
        profile = user.profile
        contractor = self.contractor
        from users.utils import get_ancestor_departments_related_organizations
        from contractor_permissions.utils import contractors_where_user_has_permission
        ancestors = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        admin_contractors = set(contractors_where_user_has_permission(profile.pk, 'admin', None))
        return not ancestors.isdisjoint(admin_contractors)



class WorkflowRequestTypeVisorModel(BaseAbstractModel):
    request_type = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestTypeModel',
        to_field='code',
        null=False,
        default='finance',
        on_delete=CUSTOM_PROTECT,
        related_name='request_type_visors',
        verbose_name=_('Тип заявки')
    )
    contractor_profile = common_fields.CustomForeignKey(
        to='catalogs.ContractorProfileModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='request_type_visors',
        verbose_name=_('Сотрудник организации')
    )

    class Meta:
        verbose_name = _('Наблюдатель типа заявки')
        verbose_name_plural = _('Наблюдатели типа заявки')
        unique_together = (('request_type', 'contractor_profile',),)


class WorkflowRequestStatusModel(BaseCatalog, BaseAbstractCatalog):
    
    meta_exclude_fields = ['author', 'name', 'code', 'created_at', 'mentions', 'ct',
                            'color', ]

    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )

    class Meta:
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import WorkflowRequestStatusSerializer
        return WorkflowRequestStatusSerializer


class WorkflowRequestCounterModel(models.Model):
    contractor = models.ForeignKey(
        'catalogs.ContractorModel',
        null=True,
        blank=False,
        verbose_name=_('Организация для нумерации'),
        on_delete=CUSTOM_CASCADE
    )
    number = models.IntegerField(
        default=0,
        verbose_name=_('Числовой инкрементальный номер')
    )
    number_formatted = models.CharField(
        default='',
        verbose_name=_('Строковый номер с префиксом'),
        max_length=31,
        db_index=True
    )

    def __str__(self):
        return self.number_formatted

    def save(self, *args, **kwargs):

        with transaction.atomic():
            for_lock = self.__class__.objects.filter(contractor_id=self.contractor_id).select_for_update(nowait=False)
            max_number = for_lock.aggregate(number=models.Max('number'))
            numb = max_number['number']
            if not numb:
                numb = 0
            self.number = numb + 1
            self.number_formatted = "{:05d}".format(self.number)
            super().save(*args, **kwargs)


class WorkflowRequestModel(BaseModel):

    meta_exclude_fields = ['mentions', 'ct', 'counter',]
    field_verbose_names = {'description': _('Обоснование / Цель'),
    'amount_requested': _('Запрошено'),
    'amount_paid': _('Выдано в подотчет'),
    'amount_reported': _('Расход'),
    'balance': _('Остаток/Перерасход'),
    
    }
    

    tracker = FieldTracker(
        fields=(
            'request_type_id',
            'status_id',
            'organization_id',
            'project_id',
            'description',
            'rejection_reason',
            'dead_line',
            'event_date_start',
            'event_date_end',
            'amount_requested',
            'amount_paid',
            'amount_reported',
            'money_under_report',
            'completed',
        )
    )

    number = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='',
        blank=False,
        verbose_name=_('Номер')
    )
    description = common_fields.CustomCharField(
        max_length=4096,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Текст обоснования')
    )
    rejection_reason = common_fields.CustomCharField(
        max_length=1024,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Причина отказа')
    )
    counter = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Номер (число)')
    )
    request_type = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestTypeModel',
        to_field='code',
        null=False,
        default='finance',
        on_delete=CUSTOM_PROTECT,
        related_name='workflow_requests',
        verbose_name=_('Тип заявки')
    )

    status = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestStatusModel',
        to_field='code',
        null=False,
        default='draft',
        on_delete=CUSTOM_PROTECT,
        related_name='workflow_requests',
        verbose_name=_('Статус')
    )

    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='workflow_requests',
        verbose_name=_('Организация'),
    )
    project = common_fields.CustomForeignKey(
        to='workgroups.WorkgroupModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='workflow_requests',
        verbose_name=_('Проект')
    )
    money_under_report = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Деньги под отчет')
    )
    paid_before_lpr = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Ранняя оплата визы')
    )

    dead_line = common_fields.CustomDateTimeField(
        null=True,
        blank=False,
        verbose_name=_('Крайний срок')
    )
    date_start = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала')
    )
    date_end = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата завершения')
    )

    event_date_start = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала события')
    )

    event_date_end = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата завершения события')
    )

    amount_requested = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name=_('Запрашиваемая сумма')
    )

    amount_paid = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Выданная сумма'),
    )

    amount_reported = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Сумма отчет'),
    )

    balance = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Баланс'),
        help_text='amount_paid - amount_reported'
    )

    completed = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Завершена')
    )

    advance_report_approved = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Авансовый отчет одобрен')
    )

    notify_fin_service = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Можно уведомить финслужбу')
    )

    class Meta:
        verbose_name = _('Заявка')
        verbose_name_plural = _('Заявки')

    def __str__(self):
        request_number = str(self.number or '').strip()
        request_type_name = str(getattr(self.request_type, 'name', '') or '').strip()
        author_full_name = str(getattr(self.author, 'full_name', '') or '').strip()
        return f'{request_number} {request_type_name}. {author_full_name}'.strip()

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.WorkflowRequestCreateSerializer
        elif action == 'retrieve':
            return serializers.WorkflowRequestDetailSerializer
        elif action in ('update', 'partial_update',):
            return serializers.WorkflowRequestUpdateSerializer
        elif action == 'create_advance_report':
            return serializers.AdvanceReportModelCreateSerializer
        elif action == 'update_advance_report':
            return serializers.AdvanceReportModelUpdateSerializer
        elif action == 'get_advance_report_list':
            return serializers.AdvanceReportModelListSerializer
        return serializers.WorkflowRequestListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        from contractor_permissions.utils import contractors_where_user_has_permission
        from users.utils import get_descendants_departments_related_organizations
        user = request.user.profile
        qs = cls.objects.filter(is_active=True)
        permission_contractors = get_descendants_departments_related_organizations(
            contractors_where_user_has_permission(user.pk, 'request_approvals_manager', None),
            include_self=True
        )
        paymaster_contractors = get_descendants_departments_related_organizations(
            set(WorkflowPositionUserModel.objects.filter(
                contractor_profile__user=user,
                workflow_position_id='paymaster',
            ).values_list('contractor_profile__contractor', flat=True)),
            include_self=True
        )
        qs = qs.filter(organization_id__in=permission_contractors)
        visors_lookup = Q()
        request_visors = WorkflowRequestTypeVisorModel.objects.filter(contractor_profile__user=user)
        for each in request_visors:
            contractors_id = get_descendants_departments_related_organizations(
                (each.contractor_profile.contractor_id,), include_self=True
            )
            request_type = each.request_type
            visors_lookup = visors_lookup | Q(organization_id__in=contractors_id, request_type=request_type)
        qs = qs.filter(
            (
                    Q(request_routes__users=user,)
                    | Q(organization_id__in=paymaster_contractors, request_type__completion_status_id='paid')
                    | visors_lookup
            ) & ~Q(status_id='draft')
            | Q(author=user)
        )
        qs = qs.annotate(
            draft_order=models.Case(
                models.When(status_id='draft', then=models.Value(1)),
                default=models.Value(0),
                output_field=models.IntegerField(),
            )
        )
        return qs.distinct().order_by('-draft_order', '-created_at')

    def get_update_permission(self, request):
        if self.completed:
            return False
        if self.author == request.user and self.status_id in ('draft', 'on_rework'):
            return True
        else:
            return False

    def get_detail_permission(self, request):
        return self.get_queryset(request).filter(pk=self.pk).exists()

    def get_advance_report_write_permission(self, user):
        if user == self.author and \
                self.request_type.completion_status_id == 'paid' and \
                self.money_under_report and \
                not self.completed and \
                not self.status_id == 'draft' and \
                not self.advance_report_approved:
            return True
        return False

    def get_advance_report_approve_permission(self, user):
        from users.utils import get_ancestor_departments_related_organizations
        from common.catalogs.models import ContractorProfileModel
        if self.advance_report_approved:
            return False
        contractor = self.organization
        contractors = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        contractor_profiles = ContractorProfileModel.objects.filter(contractor_id__in=contractors, user=user)
        if not contractor_profiles.exists():
            return False
        is_finance_service = WorkflowPositionUserModel.objects.filter(
            contractor_profile_id__in=contractor_profiles.values_list('pk', flat=True),
            workflow_position_id='finance_service',
        ).exists()
        if is_finance_service:
            return self.request_routes.filter(
                workflow_position_id='finance_service',
                users=user,
            ).exists()
        return False

    def get_notify_fin_service_permission(self, user):
        if self.author == user and self.notify_fin_service and not self.completed and not self.status_id == 'draft':
            return True
        return False

    def set_is_active(self, value: bool, request):
        if self.completed:
            return drf_exceptions.PermissionDenied()
        if not self.author == request.user.profile:
            raise drf_exceptions.PermissionDenied()
        if value is not self.is_active:
            if value is False and self.is_active is True:
                self.deleted_at = timezone.now()
            elif value is True and self.is_active is False:
                self.deleted_at = None
            try:
                self.is_active = value
            except drf_exceptions.ValidationError:
                raise drf_exceptions.ValidationError()
        else:
            pass

    def recalculate_amounts(self):
        if self.money_under_report:
            amount_reported = self.advance_reports.all().aggregate(
                models.Sum('amount')
            )['amount__sum']
        else:
            amount_reported = self.amount_requested
        if amount_reported is None:
            self.amount_reported = 0
            self.balance = None
        else:
            self.amount_reported = amount_reported
            self.balance = self.amount_paid - amount_reported
            # if self.balance <= 0:
            #     self.status_id = 'closed'
        self.save()

    def complete(self):
        if self.completed:
            return
        request_type = self.request_type
        now = timezone.now()
        status_id = self.status_id # noqa
        is_complete = False
        if status_id == 'rejected':
            is_complete = True
        else:
            if request_type.completion_status_id == 'paid':
                money_under_report = self.money_under_report
                if money_under_report is True:
                    if status_id == 'paid' and self.advance_report_approved:
                        is_complete = True
                else:
                    if status_id == 'paid':
                        is_complete = True
            else:
                if status_id == request_type.completion_status_id:
                    is_complete = True
        if is_complete:
            self.completed = True
            self.notify_fin_service = False
            self.date_end = now
            from .notifications import notify_about_complete
            transaction.on_commit(lambda: async_task(notify_about_complete, str(self.pk)))

    def get_counter_instance(self):
        from users.utils import get_roots_departments_related_organizations
        root = list(get_roots_departments_related_organizations((self.organization_id,)))[0]
        counter = WorkflowRequestCounterModel.objects.create(contractor_id=root)
        return counter

    def save(self, *args, **kwargs):
        is_created = self.pk is None

        if not self.completed:
            self.complete()
        super().save(*args, **kwargs)
        if not is_created:
            from .utils import send_socketio_about_update_workflow_request
            send_socketio_about_update_workflow_request(self)

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_table_columns(cls):
        return ['organization', 'project', 'request_type', 'status', 'author', 'created_at',]

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        annotations = {}
        names = set(requested_computed or [])
        outer_ref_column = kwargs.get('outer_ref_column')

        if 'root_organization' in names:
            from common.catalogs.models import ContractorRelationModel

            organization_pk_field = cls._meta.get_field('organization').target_field
            if outer_ref_column:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                request_root_subquery = cls.objects.filter(
                    pk=OuterRef(outer_ref_column),
                ).annotate(
                    resolved_root_organization=Coalesce(
                        Subquery(root_organization_subquery),
                        F('organization_id'),
                        output_field=organization_pk_field,
                    )
                ).values('resolved_root_organization')[:1]
                annotations['root_organization'] = Subquery(
                    request_root_subquery,
                    output_field=organization_pk_field,
                )
            else:
                root_organization_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('organization_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                annotations['root_organization'] = Coalesce(
                    Subquery(root_organization_subquery),
                    F('organization_id'),
                    output_field=organization_pk_field,
                )

        if 'request_link' in names:
            base_url = URLS['request_approvals']
            url_expr = Concat(
                Value(base_url),
                Value('?approvals='),
                Cast(F('id'), models.CharField()),
            )
            repr_expr = Concat(
                Value('#'),
                F('number'),
                Value(' '),
                F('request_type__name'),
            )
            annotations['request_link'] = Func(
                Value('repr'),
                repr_expr,
                Value('url'),
                url_expr,
                function='jsonb_build_object',
                output_field=models.JSONField(),
            )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                'name': 'root_organization',
                'type': 'ForeignKey',
                'related_model': 'catalogs.ContractorModel',
                'verbose_name': _('Головная организация'),
            },
            {
                'name': 'request_link',
                'type': 'CharField',
                'verbose_name': _('Ссылка на заявку'),
                'order_by_field': 'number',
            },
        ]

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        if created:
            change_history_utils.create_initial(
                self.pk,
                action_date,
            )
            return
        if not changed_fields:
            return
        if 'request_type_id' in changed_fields:
            request_type_code_before = changed_fields['request_type_id']
            if request_type_code_before:
                request_type_id_before = WorkflowRequestTypeModel.objects.get(code=request_type_code_before).pk
            else:
                request_type_id_before = None
            request_type_id_after = self.request_type.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'workflowrequestmodel__request_type',
                request_type_id_before,
                request_type_id_after,
            )
        if 'status_id' in changed_fields:
            status_code_before = changed_fields['status_id']
            if status_code_before:
                status_id_before = WorkflowRequestStatusModel.objects.get(code=status_code_before).pk
            else:
                status_id_before = None
            status_id_after = self.status.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'workflowrequestmodel__status',
                status_id_before,
                status_id_after,
            )
        if 'organization_id' in changed_fields:
            organization_id_before = changed_fields['organization_id']
            organization_id_after = self.organization.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'workflowrequestmodel__organization',
                organization_id_before,
                organization_id_after,
            )
        if 'project_id' in changed_fields:
            project_id_before = changed_fields['project_id']
            project_id_after = self.project.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'workflowrequestmodel__project',
                project_id_before,
                project_id_after,
            )
        if 'description' in changed_fields:
            before = changed_fields['description']
            after = self.description,
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'workflowrequestmodel__description',
                before,
                after,
            )

        if 'rejection_reason' in changed_fields:
            before = changed_fields['rejection_reason']
            after = self.rejection_reason
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'workflowrequestmodel__rejection_reason',
                before,
                after,
            )
        if 'dead_line' in changed_fields:
            dead_line_before = changed_fields['dead_line']
            dead_line_after = self.dead_line
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'workflowrequestmodel__dead_line',
                dead_line_before,
                dead_line_after,
            )
        if 'event_date_start' in changed_fields:
            event_date_start_before = changed_fields['event_date_start']
            event_date_start_after = self.event_date_start
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'workflowrequestmodel__event_date_start',
                event_date_start_before,
                event_date_start_after,
            )
        if 'event_date_end' in changed_fields:
            event_date_end_before = changed_fields['event_date_end']
            event_date_end_after = self.event_date_end
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'workflowrequestmodel__event_date_end',
                event_date_end_before,
                event_date_end_after,
            )

        if 'amount_requested' in changed_fields:
            amount_requested_before = changed_fields['amount_requested']
            amount_requested_after = self.amount_requested
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'workflowrequestmodel__amount_requested',
                amount_requested_before,
                amount_requested_after,
            )
        if 'amount_paid' in changed_fields:
            amount_paid_before = changed_fields['amount_paid']
            amount_paid_after = self.amount_paid
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'workflowrequestmodel__amount_paid',
                amount_paid_before,
                amount_paid_after,
            )
        if 'amount_reported' in changed_fields:
            amount_reported_before = changed_fields['amount_reported']
            amount_reported_after = self.amount_reported
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'workflowrequestmodel__amount_reported',
                amount_reported_before,
                amount_reported_after,
            )
        if 'money_under_report' in changed_fields:
            money_under_report_after = self.money_under_report
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'workflowrequestmodel__money_under_report',
                money_under_report_after
            )
        if 'completed' in changed_fields:
            completed_after = self.completed
            change_history_utils.create_update_boolean(
                self.pk,
                action_date,
                'workflowrequestmodel__completed',
                completed_after
            )


class WorkflowPositionModel(BaseCatalog, BaseAbstractCatalog):
    status = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestStatusModel',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='workflow_positions',
        verbose_name=_('Статус должности')
    )

    class Meta:
        verbose_name = _('Должность')
        verbose_name_plural = _('Должности')


class WorkflowPositionUserModel(BaseAbstractModel):
    workflow_position = common_fields.CustomForeignKey(
        to='processes.WorkflowPositionModel',
        on_delete=CUSTOM_CASCADE,
        to_field='code',
        null=False,
        blank=False,
        default='director',
        related_name='workflow_position_users',
        verbose_name=_('Должность организации')
    )
    contractor_profile = common_fields.CustomForeignKey(
        to='catalogs.ContractorProfileModel',
        on_delete=CUSTOM_CASCADE,
        null=True,
        blank=False,
        related_name='workflow_position_users',
        verbose_name=_('Сотрудник организации')
    )

    class Meta:
        verbose_name = _('Должность организации')
        verbose_name_plural = _('Должности организации')


class WorkflowRequestRouteStatusModel(BaseCatalog, BaseAbstractCatalog):
    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )

    class Meta:
        verbose_name = _('Статус согласования')
        verbose_name_plural = _('Статусы согласования')


class WorkflowRequestRouteModel(BaseAbstractModel):
    workflow_request = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='request_routes',
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='children',
        verbose_name='Предыдущий этап'
    )
    workflow_position = common_fields.CustomForeignKey(
        to='processes.WorkflowPositionModel',
        on_delete=CUSTOM_CASCADE,
        to_field='code',
        null=False,
        blank=False,
        default='director',
        related_name='request_routes',
        verbose_name=_('Должность')
    )
    status = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestRouteStatusModel',
        on_delete=CUSTOM_PROTECT,
        to_field='code',
        null=False,
        blank=False,
        default='awaits',
        related_name='request_routes',
        verbose_name=_('Статус')
    )
    template = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestRouteTemplateModel',
        on_delete=CUSTOM_SET_NULL,
        null=True,
        blank=True,
        related_name='request_routes',
        verbose_name=_('Шаблон')
    )

    users = models.ManyToManyField(
        to='users.ProfileModel',
        related_name='request_routes',
        through='processes.RequestRouteUserThrough',
        through_fields=('request_route', 'user',),
    )
    not_require_approval = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Не требует согласования'
    )

    class Meta:
        verbose_name = _('Маршрут согласования')
        verbose_name_plural = _('Маршруты согласования')


class RequestRouteUserThrough(BaseAbstractModel):
    request_route = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestRouteModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='request_route_user_through',
        verbose_name=_('Маршрут'),
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='request_route_user_through',
        verbose_name=_('Пользователь'),
    )
    status = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestRouteStatusModel',
        on_delete=CUSTOM_PROTECT,
        to_field='code',
        null=False,
        blank=False,
        default='awaits',
        related_name='request_route_user_through',
        verbose_name=_('Статус')
    )

    class Meta:
        verbose_name = _('Пользователь маршрута')
        verbose_name_plural = _('Пользователи маршрута')
        unique_together = (('request_route', 'user',),)


class WorkflowRequestRouteTemplateModel(BaseCatalog, BaseAbstractCatalog):
    request_type = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestTypeModel',
        to_field='code',
        null=False,
        blank=False,
        default='finance',
        on_delete=CUSTOM_CASCADE,
        related_name='request_route_templates',
        verbose_name=_('Тип заявки')
    )

    workflow_position = common_fields.CustomForeignKey(
        to='processes.WorkflowPositionModel',
        on_delete=CUSTOM_CASCADE,
        to_field='code',
        null=False,
        blank=False,
        default='director',
        related_name='request_route_templates',
        verbose_name=_('Должность организации')
    )

    not_require_approval = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Не требует согласования'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='children',
        verbose_name='Предыдущий этап'
    )

    class Meta:
        verbose_name = _('Шаблон маршрута согласования')
        verbose_name_plural = _('Шаблоны маршрута согласования')
        unique_together = (('request_type', 'workflow_position',),)

    def __str__(self):
        return f"{self.request_type.name} {self.workflow_position.name}"


class AdvanceReportModel(BaseModel):
    owner = common_fields.CustomForeignKey(
        to='processes.WorkflowRequestModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='advance_reports',
        verbose_name=_('Заявка')
    )
    date = common_fields.CustomDateField(
        null=False,
        blank=False,
        default=timezone.localdate,
        verbose_name=_('Дата')
    )

    cost_item = common_fields.CustomForeignKey(
        to='catalogs.CostItemModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        related_name='advance_report',
        verbose_name=_('Статья затрат')
    )

    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Сумма')
    )
    description = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Комментарий')
    )

    class Meta:
        verbose_name = _('Авансовый отчет')
        verbose_name_plural = _('Авансовые отчеты')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            AdvanceReportModelCreateSerializer,
            AdvanceReportModelListSerializer,
            AdvanceReportModelUpdateSerializer
        )
        if action == 'create':
            return AdvanceReportModelCreateSerializer
        elif action in ('update', 'partial_update',):
            return AdvanceReportModelUpdateSerializer
        else:
            return AdvanceReportModelListSerializer

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            workflow_request = self.owner
            workflow_request.recalculate_amounts()

    def get_detail_permission(self, request) -> bool:
        return self.owner.get_detail_permission(request)

