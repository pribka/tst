import json
import re
import uuid
import datetime
from decimal import Decimal, ROUND_UP

from django_q.tasks import async_task

from django.contrib.postgres.aggregates import StringAgg
from django.db import models, transaction
from django.db.models import Q, Sum, Exists, OuterRef, Case, When, IntegerField, Value, CharField, F, Subquery, Func
from django.db.models.functions import Coalesce, Concat, Trim
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils import dateparse
from django.core.serializers.json import DjangoJSONEncoder

from haystack.query import SearchQuerySet

from model_utils import FieldTracker

from bs4 import BeautifulSoup

from rest_framework import exceptions as drf_exceptions

from common import models as common_models
from common import fields as common_fields
from common.redis import socketio_redis
from common.validators import iin_validator, normalize_kz_bin, kz_bin_validator
from common.utils import get_search_result
from common.page_config import filter_fields
from common.catalogs.models import NomenclatureModel, MeasureUnitModel
from common.estimates.models import AccumulationRegister
from common.current_profile.middleware import get_current_authenticated_profile

from bpms.tasks.models import TaskWorkTypeModel

from contractor_permissions.utils import (
    check_contractor_permission,
    contractors_where_user_has_permission, contractors_where_im_director,
    users_that_have_app_section_role_in_contractors
)

from change_history import utils as change_history_utils

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE, CUSTOM_SET_NULL, SOCKETIO_SYSTEM_CHANNEL, URLS

from users.models import ProfileModel

from tags.fields import TagsFilterField

from . import fields


class CustomerCardModel(common_models.BaseModel):
    meta_exclude_fields = ['author', 'external_id', 'external_customer', 'unknown', 
                           'description', 'created_at', 'status', 'mentions', 'ct', 'client_guest', 
                           'external_id', 'bin_validated',]

    # Поля контрагента:
    name = common_fields.CustomCharField(
        verbose_name=_('Наименование'),
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    full_name = common_fields.CustomCharField(
        max_length=511,  # TODO увеличить размер?
        null=False,
        blank=True,
        default='',
        verbose_name=_('Полное наименование')
    )
    inn = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('БИН'),
    )

    bin_validated = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('БИН провалидирован'),
    )

    legal_address = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Юридический адрес'),
    )
    # /Поля контрагента

    external_id = common_fields.CustomCharField(
        max_length=36,
        null=False,
        default='',
        blank=True,
        verbose_name=_('id из 1C'),
    )
    external_customer = common_fields.CustomForeignKey(
        to='catalogs.ExternalCustomerModel',
        null=True,
        blank=True,
        related_name='customer_cards',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Клиент от внешнего сервиса')
    )
    status = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='new',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус'),
        related_name='customers_help_desk',
    )
    org_admin = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация техподдержки'),
        related_name='admins_help_desk'
    )
    main_contact_person = common_fields.CustomForeignKey(
        to='help_desk.ContactPersonModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Основной контакт'),
        related_name='customer_card_main',
    )

    admins = models.ManyToManyField(
        to='help_desk.CustomerCardAdminModel',
        through='help_desk.CustomerCardAdminThroughModel',
        through_fields=('customer_card', 'admin'),
        verbose_name=_('Организация-администратор')
    )

    customer = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Контрагент'),
        related_name='customers_help_desk'
    )
    description = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )
    unknown = common_fields.CustomBooleanField(
        default=False,
    )
    client_guest = common_fields.CustomBooleanField(default=False)

    tags_filter = TagsFilterField()
    org_admin_filter = fields.OrgAdminFilterField()
    specialist_filter = fields.SpecialistFilterField()
    main_specialist_filter = fields.MainSpecialistFilterField()
    reserve_specialist_filter = fields.ReserveSpecialistFilterField()
    admins_filter = fields.CustomerCardAdminsFilterField()
    main_contact_exist_filter = fields.MainContactExistField()
    main_contact_post_filter = fields.MainContactPersonPostField()

    class Meta:
        verbose_name = _('Карточка клиента')
        verbose_name_plural = _('Карточки клиентов')
        unique_together = (('org_admin', 'customer',),)

    def __str__(self):
        return self.name

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        data = super().get_filter_fields(exclude, request)
        for each in data:
            if each['name'] in ('name', 'name__exclude',):
                each['verbose_name'] = _('Наименование организации')
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.CustomerCardModelCreateSerializer
        elif action == 'retrieve':
            return serializers.CustomerCardModelDetailSerializer
        elif action in ('update', 'partial_update',):
            return serializers.CustomerCardModelUpdateSerializer
        elif action == 'update_specialist':
            return serializers.CustomerSpecialistListSerializer
        elif action == 'update_contact_person':
            return serializers.ContactPersonModelListSerializer
        else:
            return serializers.CustomerCardModelListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        user = request.user.profile
        user_id = user.pk
        help_desk_admin_contractors = set(
            contractors_where_user_has_permission(
                user_id, ('admin', 'create_workgroup', 'help_desk_admin', 'help_desk_supervisor'), None)
        )
        help_desk_manager_contractors = set(
            contractors_where_user_has_permission(user_id, ('help_desk_manager',), None))
        specialist_customer_cards = cls.get_qs_customer_cards_from_specialist(
            user_id
        ).filter(
            org_admin_id__in=help_desk_manager_contractors
        ).values_list('pk', flat=True)
        qs = qs.filter(Q(org_admin_id__in=help_desk_admin_contractors) | Q(pk__in=specialist_customer_cards))
        contractor_id = request.query_params.get('contractor')
        if contractor_id:
            try:
                qs = qs.filter(org_admin=contractor_id)
            except ValidationError:
                pass
        exclude_id = request.query_params.get('exclude')
        if exclude_id:
            try:
                qs = qs.exclude(pk=exclude_id)
            except ValidationError:
                pass
        return qs.order_by('-created_at', )

    @classmethod
    def get_select_queryset(cls, request=None):
        qs = cls.get_queryset(request)
        qs = qs.exclude(unknown=True)
        return qs.order_by('name', 'created_at', )

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        qs = cls.get_select_queryset(request)
        search_result = list(
            SearchQuerySet().autocomplete(name_auto=text).models(cls).values_list('pk', flat=True)[:300]
        )
        preserved = models.Case(*[models.When(pk=pk, then=pos) for pos, pk in enumerate(search_result)])
        qs = qs.filter(pk__in=search_result).order_by(preserved)
        return qs

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_table_columns(cls):
        return ['name', 'org_admin_filter', 'tags_filter', 'status',
                'specialist_filter', 'main_specialist_filter', 'reserve_specialist_filter', 'admins_filter',
                'main_contact_exist_filter', 'main_contact_post_filter',
                ]

    @classmethod
    def get_order_param(cls):
        return ['name', 'created_at', ]

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        """Вычисляемые поля для отчётов: work_duration, contact_persons, tags.
        В отчёте по связанной модели (например по специалистам) передаётся outer_ref_column —
        тогда подзапрос привязывается к FK строки (customer_card_id), а не к pk карточки."""
        from django.db.models import CharField, Subquery
        from django.db.models import UUIDField
        from django.db.models.functions import Coalesce
        from django.contrib.postgres.aggregates import StringAgg, ArrayAgg
        from django.contrib.postgres.fields import ArrayField

        ref = kwargs.get('outer_ref_column') or 'pk'
        annotations = {}
        names = set(requested_computed or [])
        if 'work_duration' in names:
            subq = HelpDeskTicketModel.objects.filter(
                customer_card_id=OuterRef(ref),
                status_id='completed',
            ).values('customer_card_id').annotate(s=Sum('duration')).values('s')[:1]
            annotations['work_duration'] = Coalesce(
                Subquery(subq, output_field=IntegerField()),
                Value(0),
                output_field=IntegerField(),
            )
        if 'contact_persons' in names:
            contact_persons_subq = ContactPersonModel.objects.filter(
                customer_card_id=OuterRef(ref),
            ).order_by('name').values('customer_card_id').annotate(
                names=StringAgg('name', ', ', ordering='name'),
            ).values('names')[:1]
            annotations['contact_persons'] = Coalesce(
                Subquery(contact_persons_subq, output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )
        if 'tags' in names:
            from tags.models import TagRelatedObjectThrough
            tags_subq = TagRelatedObjectThrough.objects.filter(
                related_object_id=OuterRef(ref),
                tag_id__isnull=False,
            ).values('related_object_id').annotate(
                # Важно: не делать order_by до aggregation, чтобы Django не
                # разворачивал GROUP BY и не резал агрегат до одного элемента.
                # Важно для Postgres: DISTINCT + ORDER BY (не в аргументах) ломается.
                # У нас tag/related_object уникальны, поэтому DISTINCT не нужен.
                tag_ids=ArrayAgg('tag_id', ordering='tag__name'),
            ).values('tag_ids')[:1]
            annotations['tags'] = Coalesce(
                Subquery(
                    tags_subq,
                    output_field=ArrayField(UUIDField()),
                ),
                Value([], output_field=ArrayField(UUIDField())),
                output_field=ArrayField(UUIDField()),
            )
        if 'root_org_admin' in names:
            from common.catalogs.models import ContractorRelationModel

            organization_pk_field = cls._meta.get_field('org_admin').target_field
            if kwargs.get('outer_ref_column'):
                root_org_admin_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('org_admin_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                customer_card_root_subquery = cls.objects.filter(
                    pk=OuterRef(kwargs.get('outer_ref_column')),
                ).annotate(
                    resolved_root_org_admin=Coalesce(
                        Subquery(root_org_admin_subquery),
                        F('org_admin_id'),
                        output_field=organization_pk_field,
                    )
                ).values('resolved_root_org_admin')[:1]
                annotations['root_org_admin'] = Subquery(
                    customer_card_root_subquery,
                    output_field=organization_pk_field,
                )
            else:
                root_org_admin_subquery = ContractorRelationModel.objects.filter(
                    contractor_id=OuterRef('org_admin_id'),
                    relation_type_id='structural_division',
                    is_active=True,
                ).values('contractor_root_id')[:1]
                annotations['root_org_admin'] = Coalesce(
                    Subquery(root_org_admin_subquery),
                    F('org_admin_id'),
                    output_field=organization_pk_field,
                )
        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                "name": "work_duration",
                "type": "DurationField",
                "verbose_name": _("Трудозатраты"),
            },
            {
                "name": "contact_persons",
                "type": "CharField",
                "verbose_name": _("Контактные лица"),
            },
            {
                "name": "tags",
                "type": "ForeignKey",
                "related_model": "tags.TagModel",
                "verbose_name": _("Теги"),
            },
            {
                "name": "root_org_admin",
                "type": "ForeignKey",
                "related_model": "catalogs.ContractorModel",
                "verbose_name": _("Головная организация техподдержки"),
            },
        ]

    @classmethod
    def build_report_field_q(cls, field, comparison, value):
        """
        Спец-логика для вычисляемого поля `tags`:
        фронт начнет слать id тэгов (как для ForeignKey), а не строку имён.
        """
        if field == "tags" and comparison in ("=", "in", "!=", "not in"):
            from tags.models import TagRelatedObjectThrough
            from common.utils import is_uuid as common_is_uuid

            is_negative = comparison in ("!=", "not in")
            if value in (None, ""):
                return Q() if is_negative else Q(pk__in=[])

            if comparison in ("in", "not in") and isinstance(value, str):
                # Поддержка формата "id1,id2" вместо массива
                values = [item.strip() for item in value.split(",") if item.strip()]
            elif not isinstance(value, (list, tuple, set)):
                values = [value]
            else:
                values = list(value)

            normalized_values = []
            for item in values:
                if isinstance(item, dict):
                    if "id" in item:
                        normalized_values.append(item.get("id"))
                    elif "value" in item:
                        normalized_values.append(item.get("value"))
                    elif "pk" in item:
                        normalized_values.append(item.get("pk"))
                    else:
                        normalized_values.append(None)
                else:
                    normalized_values.append(item)

            tag_ids = [
                item for item in normalized_values
                if item not in (None, "") and common_is_uuid(item)
            ]
            if not tag_ids:
                return Q() if is_negative else Q(pk__in=[])

            tagged_object_ids = TagRelatedObjectThrough.objects.filter(
                tag_id__in=tag_ids,
            ).values_list("related_object_id", flat=True).distinct()

            if is_negative:
                return ~Q(pk__in=tagged_object_ids)
            return Q(pk__in=tagged_object_ids)

        return None

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        user_id = user.pk
        contractor_id = self.org_admin.pk

        try:
            check_contractor_permission(user_id, contractor_id, 'help_desk_admin', None)
        except drf_exceptions.PermissionDenied:
            pass
        else:
            return True

        try:
            check_contractor_permission(user_id, contractor_id, 'help_desk_manager', None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return self.actual_specialists.filter(user=user).exists()

    def get_create_ticket_permission(self, request):
        user_id = request.user.profile.pk
        contractor_id = self.org_admin.pk
        try:
            check_contractor_permission(
                user_id,
                contractor_id,
                ('help_desk_admin',),
                None
            )
        except drf_exceptions.PermissionDenied:
            try:
                check_contractor_permission(
                    user_id,
                    contractor_id,
                    ('help_desk_manager',),
                    None
                )
            except drf_exceptions.PermissionDenied:
                return False
            else:
                if self.actual_specialists.filter(user_id=user_id).exists():
                    return True
                else:
                    return False
        else:
            return True

    def get_specialist_update_permission(self, request):
        user_id = request.user.profile.pk
        contractor_id = self.org_admin.pk
        try:
            check_contractor_permission(user_id, contractor_id, 'help_desk_admin', None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def get_note_permission(self, request) -> bool:
        user_id = request.user.profile.pk
        contractor_id = self.org_admin.pk
        try:
            check_contractor_permission(user_id, contractor_id, ('help_desk_admin', 'help_desk_manager',), None)
        except drf_exceptions.PermissionDenied:
            return False
        return True

    def get_detail_permission(self, request) -> bool:
        user_id = request.user.profile.pk
        contractor_id = self.org_admin.pk
        try:
            check_contractor_permission(
                user_id,
                contractor_id,
                ('help_desk_admin', 'help_desk_supervisor',),
                None
            )
        except drf_exceptions.PermissionDenied:
            try:
                check_contractor_permission(
                    user_id,
                    contractor_id,
                    ('help_desk_manager',),
                    None
                )
            except drf_exceptions.PermissionDenied:
                return False
            else:
                if self.actual_specialists.filter(user_id=user_id).exists():
                    return True
                else:
                    return False
        else:
            return True

    def get_delete_permission(self, request):
        user = request.user.profile
        contractor = self.org_admin
        try:
            check_contractor_permission(user.pk, contractor.pk, 'help_desk_admin', None)
        except drf_exceptions.PermissionDenied:
            return False
        return True

    def save(self, *args, **kwargs):
        self.inn = normalize_kz_bin(self.inn)

        if self.inn:
            kz_bin_validator(self.inn)
            self.bin_validated = True
        else:
            self.bin_validated = False

        super().save(*args, **kwargs)

    def set_is_active(self, value: bool, request):
        if not self.get_delete_permission(request):
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

    @property
    def actual_specialists(self):
        """Возвращает queryset с актуальными специалистами тех. поддержки карточки клиента"""
        local_date = timezone.localdate()
        return self.customer_support_specialists.filter(  # noqa
            (
                Q(start_date__lte=local_date) | Q(start_date__isnull=True)
            ) & (
                Q(end_date__gte=local_date) | Q(end_date__isnull=True)
            )
        ).exclude(
            vacation_dates__start_date__lte=local_date,
            vacation_dates__end_date__gte=local_date,
        ).order_by(
            'is_reserve',
            'user__user__last_name',
            'user__user__first_name',
            'user__user__middle_name',
        )

    @staticmethod
    def get_qs_customer_cards_from_specialist(profile_id):
        """
        Возвращает qs карточек клиента, где profile_id является актуальным специалистом
        """
        local_date = timezone.localdate()
        date_condition = (
                (Q(customer_support_specialists__start_date__lte=local_date) |
                 Q(customer_support_specialists__start_date__isnull=True)) &
                (Q(customer_support_specialists__end_date__gte=local_date) |
                 Q(customer_support_specialists__end_date__isnull=True))
        )
        vacation_condition = ~Q(
            customer_support_specialists__vacation_dates__start_date__lte=local_date,
            customer_support_specialists__vacation_dates__end_date__gte=local_date
        )
        qs = CustomerCardModel.objects.filter(
            Q(customer_support_specialists__user_id=profile_id),
            date_condition,
            vacation_condition,
            is_active=True,
        ).distinct()
        return qs


class CustomerCardAdminModel(common_models.BaseCatalog, ):
    org_admin = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация техподдержки'),
        related_name='customer_card_admins'
    )

    bin = common_fields.CustomCharField(
        max_length=12,
        null=False,
        default='',
        blank=False,
        verbose_name=_('БИН'),
        validators=(iin_validator,)
    )

    class Meta:
        verbose_name = _('Администратор')
        verbose_name_plural = _('Администраторы')
        unique_together = (('org_admin', 'bin',),)
        ordering = ('name',)

    @classmethod
    def get_select_queryset(cls, request=None):
        qs = cls.objects.all()
        if not request:
            return qs.none()
        else:
            user = request.user.profile
            from contractor_permissions.utils import contractors_where_user_has_permission
            org_admins = contractors_where_user_has_permission(
                user.pk,
                ('help_desk_admin', 'help_desk_manager', 'help_desk_supervisor',),
                None
            )
            qs = qs.filter(org_admin_id__in=org_admins)
            org_admin = request.query_params.get('org_admin')
            if org_admin:
                qs = qs.filter(org_admin_id=org_admin)
            return qs.order_by('name')

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_select_queryset(request).filter(Q(name__icontains=text) | Q(bin__icontains=text))

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.CustomerCardAdminCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.CustomerCardAdminUpdateSerializer
        return serializers.CustomerCardAdminListSerializer

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        org_admin = self.org_admin
        try:
            check_contractor_permission(user.pk, org_admin.pk, ('help_desk_admin', 'help_desk_manager'), None)
        except drf_exceptions.PermissionDenied():
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        org_admin = self.org_admin
        if org_admin.pk in user.my_organizations:
            return True
        else:
            return False


class CustomerCardAdminThroughModel(common_models.BaseAbstractModel):
    customer_card = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='customer_card_admin_through',
    )
    admin = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardAdminModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='customer_card_admin_through',
    )

    class Meta:
        verbose_name = _('Администратор карточки клиента')
        verbose_name_plural = _('Администраторы карточки клиента')
        unique_together = (('customer_card', 'admin'),)


class CustomerCardStatusModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'color', 'created_at', 'mentions', 'ct', ]

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='blue',
        blank=False,
        verbose_name=_('Цвет')
    )

    class Meta:
        verbose_name = _('Статус клиента')
        verbose_name_plural = _('Статусы клиента')


class CustomerSupportSpecialistModel(common_models.BaseAbstractModel):
    meta_exclude_fields = ['author', 'created_at', 'comment', 'accepts_calls', 'call_priority',]

    customer_card = common_fields.CustomForeignKey(
        to='CustomerCardModel',
        on_delete=CUSTOM_CASCADE,
        related_name='customer_support_specialists',
        null=True,
        blank=False,
        verbose_name=_('Карточка клиента'),
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_CASCADE,
        related_name='customer_support_specialists',
        null=True,
        blank=False,
        verbose_name=_('Специалист')
    )

    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )
    start_date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала'),
    )
    end_date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    duration_plan = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('План часов')
    )
    is_reserve = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Замена')
    )
    accepts_calls = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Принимает звонки')
    )
    call_priority = common_fields.CustomPositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Приоритет при распределении звонков')
    )

    @classmethod
    def rebuild_call_priorities_for_customer_card(cls, customer_card_id, moved_specialist_id=None):
        """
        Пересчитывает call_priority для специалистов одного customer_card так, чтобы:
        - основные (is_reserve=False) шли первыми
        - заменяющие (is_reserve=True) сразу после основных
        - внутри каждой группы порядок сохранялся по текущему call_priority
        - moved_specialist_id (если передан) вставляется в конец своей текущей группы
        """
        if not customer_card_id:
            return

        locked_qs = cls.objects.select_for_update().filter(
            customer_card_id=customer_card_id,
            is_active=True,
        )

        moved_instance = None
        if moved_specialist_id:
            moved_instance = locked_qs.only('id', 'is_reserve', 'call_priority').filter(pk=moved_specialist_id).first()

        base_qs = locked_qs
        if moved_specialist_id:
            base_qs = base_qs.exclude(pk=moved_specialist_id)

        main_specialists = list(
            base_qs.filter(is_reserve=False).only('id', 'call_priority').order_by('call_priority')
        )
        reserve_specialists = list(
            base_qs.filter(is_reserve=True).only('id', 'call_priority').order_by('call_priority')
        )

        if moved_instance:
            if moved_instance.is_reserve:
                reserve_specialists.append(moved_instance)
            else:
                main_specialists.append(moved_instance)

        updates = []
        next_priority = 1
        for specialist in main_specialists:
            if specialist.call_priority != next_priority:
                specialist.call_priority = next_priority
                updates.append(specialist)
            next_priority += 1

        for specialist in reserve_specialists:
            if specialist.call_priority != next_priority:
                specialist.call_priority = next_priority
                updates.append(specialist)
            next_priority += 1

        if updates:
            cls.objects.bulk_update(updates, ['call_priority'], batch_size=1000)

    def save(self, *args, **kwargs):
        is_created = self._state.adding
        old_is_reserve = None
        if not is_created:
            old_is_reserve = CustomerSupportSpecialistModel.objects.filter(pk=self.pk).values_list('is_reserve', flat=True).first()

        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_created or (old_is_reserve is not None and old_is_reserve != self.is_reserve):
                self.rebuild_call_priorities_for_customer_card(
                    customer_card_id=self.customer_card_id,
                    moved_specialist_id=self.pk,
                )

    def delete(self, *args, **kwargs):
        customer_card_id = self.customer_card_id
        with transaction.atomic():
            super().delete(*args, **kwargs)
            self.rebuild_call_priorities_for_customer_card(customer_card_id=customer_card_id)

    @property
    def instance_duration_fact(self):
        duration_sum = HelpDeskWorkLogModel.objects.filter(
            user=self.user,
            ticket__customer_card=self.customer_card,
            is_active=True,
        ).aggregate(duration_sum=Sum('duration'))['duration_sum']
        if duration_sum is None:
            duration_sum = 0
        return duration_sum

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        return serializers.CustomerSpecialistListSerializer

    def get_update_permission(self, request) -> bool:
        return self.customer_card.get_update_permission(request)

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        annotations = {}
        names = set(requested_computed or [])
        customer_card_ref = kwargs.get('outer_ref_column') or 'customer_card_id'

        if 'main_specialist' in names:
            main_specialist_qs = cls.objects.filter(
                customer_card_id=OuterRef(customer_card_ref),
                is_reserve=False,
                user__isnull=False,
            ).annotate(
                full_name=Trim(
                    Concat(
                        Coalesce(F('user__user__last_name'), Value('')),
                        Value(' '),
                        Coalesce(F('user__user__first_name'), Value('')),
                        Value(' '),
                        Coalesce(F('user__user__middle_name'), Value('')),
                        output_field=CharField(),
                    )
                ),
            ).order_by(
                'full_name',
            )

            annotations['main_specialist_sort'] = Subquery(
                main_specialist_qs.values_list('full_name', flat=True)[:1],
                output_field=CharField(),
            )
            annotations['main_specialist'] = Subquery(
                main_specialist_qs.values_list('user_id', flat=True)[:1],
                output_field=models.UUIDField(),
            )

        if 'customer_card_main_specialists_list' in names:
            specialists_subq = cls.objects.filter(
                customer_card_id=OuterRef(customer_card_ref),
                is_reserve=False,
                user__isnull=False,
            ).annotate(
                full_name=Trim(
                    Concat(
                    Coalesce(F('user__user__last_name'), Value('')),
                    Value(' '),
                    Coalesce(F('user__user__first_name'), Value('')),
                    Value(' '),
                    Coalesce(F('user__user__middle_name'), Value('')),
                    output_field=CharField(),
                    )
                ),
            ).values(
                'customer_card_id'
            ).annotate(
                names=StringAgg('full_name', ', ', ordering='full_name'),
            ).values('names')[:1]

            annotations['customer_card_main_specialists_list'] = Coalesce(
                Subquery(specialists_subq, output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )

        if 'reserve_period' in names:
            start_fmt = Coalesce(
                Func(F('start_date'), Value('DD.MM.YYYY'), function='to_char', output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )
            end_fmt = Coalesce(
                Func(F('end_date'), Value('DD.MM.YYYY'), function='to_char', output_field=CharField()),
                Value(''),
                output_field=CharField(),
            )
            annotations['reserve_period'] = Concat(
                start_fmt,
                Value(' - '),
                end_fmt,
                output_field=CharField(),
            )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                "name": "customer_card_main_specialists_list",
                "type": "CharField",
                "verbose_name": _("Основные специалисты контрагента"),
            },
            {
                "name": "reserve_period",
                "type": "DateField",
                "verbose_name": _("Период замещения"),
                "period_filter": {
                    "start_field": "start_date",
                    "end_field": "end_date",
                },
            },
            {
                "name": "main_specialist",
                "type": "ForeignKey",
                "related_model": "users.ProfileModel",
                "verbose_name": _("Основной специалист"),
                "order_by_field": "main_specialist_sort",
            },
        ]

    @classmethod
    def build_report_field_q(cls, field, comparison, value):
        if field == "main_specialist" and comparison in ("=", "in") and value not in (None, ""):
            if not isinstance(value, (list, tuple, set)):
                values = [value]
            else:
                values = list(value)
            values = [item for item in values if item not in (None, "")]
            if not values:
                return Q(pk__in=[])
            customer_card_ids = cls.objects.filter(
                is_reserve=False,
                user_id__in=values,
                is_active=True,
            ).values_list("customer_card_id", flat=True)
            return Q(customer_card_id__in=customer_card_ids)
        return None

    class Meta:
        verbose_name = _('Специалист поддержки')
        verbose_name_plural = _('Специалисты поддержки')
        unique_together = (('customer_card', 'user',),)


class VacationDateModel(common_models.BaseAbstractModel):
    specialist = common_fields.CustomForeignKey(
        to='help_desk.CustomerSupportSpecialistModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='vacation_dates',
        verbose_name=_('Специалист карточки клиента')
    )
    start_date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала'),
    )
    end_date = common_fields.CustomDateField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )

    class Meta:
        verbose_name = _('Дата отпуска')
        verbose_name_plural = _('Даты отпуска')
        ordering = ('start_date',)


class ContactPersonPostModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'contractor', 'created_at', 'mentions', 'ct', ]

    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='contact_person_posts',
        verbose_name=_('Организация')
    )

    class Meta:
        verbose_name = _('Должность контактного лица')
        verbose_name_plural = _('Должности контактного лица')

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.ContactPersonPostCreateSerializer
        elif action in ('update', 'partial_update'):
            return serializers.ContactPersonPostUpdateSerializer
        elif action == 'retrieve':
            return serializers.ContactPersonPostDetailSerializer
        else:
            return serializers.ContactPersonPostSerializer

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import get_help_desk_admin_manager_contractors
        from users.utils import get_tree_departments_related_organizations
        lookup = Q(contractor__isnull=True)
        qs = cls.objects.filter(is_active=True)
        if request:
            page_name = request.query_params.get('page_name')
            if page_name:
                prefix = "helpdesk_contact_person_by_"
                if page_name.startswith(prefix):
                    uid = page_name[len(prefix):]
                    if uid:
                        try:
                            customer_card = common_models.BaseModel.objects.super_get(pk=uid)
                        except (ObjectDoesNotExist, ValidationError):
                            pass
                        else:
                            contractor = customer_card.org_admin
                            contractors_id = get_tree_departments_related_organizations((contractor.pk,))
                            qs = qs.filter(contractor__in=contractors_id)
            contractors_id = get_help_desk_admin_manager_contractors(request.user.profile)
            if contractors_id:
                contractors_id = get_tree_departments_related_organizations(contractors_id)
                if contractors_id:
                    lookup |= Q(contractor__in=contractors_id)
        return qs.filter(lookup).order_by('sort', 'name')

    def get_update_permission(self, request) -> bool:
        contractor = self.contractor
        if not contractor:
            return False
        from users.utils import get_ancestor_departments_related_organizations
        contractors_id = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        permission_contractors_id = set(
            contractors_where_user_has_permission(request.user.profile.pk, 'help_desk_admin', None)
        )
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        contractor = self.contractor
        if not contractor:
            return True
        from users.utils import get_tree_departments_related_organizations
        from .utils import get_help_desk_admin_manager_contractors
        contractors_id = get_tree_departments_related_organizations((contractor.pk,))
        permission_contractors_id = set(get_help_desk_admin_manager_contractors(user))
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

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


class ContactPersonModel(common_models.BaseCatalog):
    meta_exclude_fields = ['author', 'created_at', 'customer_card',
                           'phone', 'telegram', 'telegram_id', 'email',
                           'invite_token', 'letter_sent', 'letter_sent_date', 'unknown', 'spam', 'comment', 'mentions',
                           'ct']
    field_verbose_names = {
        'name': _('Имя'),
    }

    customer_card = common_fields.CustomForeignKey(
        to='CustomerCardModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Карточка клиента'),
        related_name='contact_persons',
    )

    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        on_delete=CUSTOM_SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Пользователь'),
        related_name='contact_persons',
    )
    # post = common_fields.CustomCharField(
    #     max_length=1023,
    #     null=False,
    #     default='',
    #     blank=True,
    #     verbose_name=_('Должность')
    # )
    post_inst = common_fields.CustomForeignKey(
        to='help_desk.ContactPersonPostModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Должность'),
        related_name='contact_persons'
    )

    phone = common_fields.CustomCharField(
        max_length=20,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Телефон'),
    )
    telegram = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Телеграм'),
    )
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('telegram id'),
    )
    email = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('email'),
    )
    invite_token = models.CharField(
        null=False,
        default=uuid.uuid4,
        max_length=36,
        blank=True,
    )

    letter_sent = models.BooleanField(
        default=False,
    )
    letter_sent_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    unknown = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Неизвестный контакт')
    )
    spam = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Спам'),
    )
    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )

    has_profile_filter = fields.HasProfileFilterField()
    sla_filter = fields.SlaFilterField()

    class Meta:
        verbose_name = _('Контактное лицо')
        verbose_name_plural = _('Контактные лица')

    @classmethod
    def get_table_columns(cls):
        return ['post_inst', 'has_profile_filter', 'sla_filter']

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'retrieve':
            return serializers.ContactPersonModelListSerializer
        return serializers.ContactPersonModelListSerializer

    def get_detail_permission(self, request) -> bool:
        return self.customer_card.get_detail_permission(request)

    def get_update_permission(self, request) -> bool:
        return self.customer_card.get_update_permission(request)

    @classmethod
    def get_queryset(cls, request=None):
        from help_desk.utils import get_contact_persons_queryset
        user = request.user.profile
        user_id = user.pk
        return get_contact_persons_queryset(user_id)

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_protected_fields(cls):
        """Возвращает список полей, по которым нельзя фильтровать для защиты персональных данных."""
        return ['phone', 'telegram', 'email']


class HelpDeskChannelModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'icon', 'created_at', 'mentions', 'ct']
    icon = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Путь до иконки')
    )

    class Meta:
        verbose_name = _('Канал связи')
        verbose_name_plural = _('Каналы связи')


class ContactPersonMessageModel(common_models.BaseModel):
    contact_person = common_fields.CustomForeignKey(
        to='ContactPersonModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='contact_person_messages',
        verbose_name=_('Контактное лицо'),
    )
    reply = common_fields.CustomForeignKey(
        to='self',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='contact_person_replies',
        verbose_name=_('Ответ на сообщение')
    )
    channel = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskChannelModel',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='contact_person_messages',
        verbose_name=_('Канал связи'),
    )
    text = models.TextField(
        null=False,
        default='',
        blank=False,
        verbose_name=_('Текст сообщения')
    )
    source_message = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Исходник')
    )
    files_message = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Файлы')
    )

    message_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата сообщения')
    )
    message_id = common_fields.CustomCharField(
        max_length=255,
        null=False,
        blank=True,
        default='',
        verbose_name=_('id сообщения')
    )
    is_help_desk = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Специалист тех. поддержки')
    )
    email_subject = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name=_('Тема письма')
    )

    @property
    def short_text(self):
        """Возвращает чистый текст из HTML, обрезанный до 100 символов"""
        if not self.text:
            return ''
        soup = BeautifulSoup(self.text, 'lxml')
        for tag in soup.find_all(['img', 'video', 'figure', 'iframe']):
            tag.decompose()
        clean_text = soup.get_text(separator=" ", strip=True)

        if len(clean_text) < 100:
            return clean_text
        else:
            return clean_text[:97] + '...'

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")

    def save(self, *args, ticket=None, **kwargs):
        is_created = True if self.pk is None else False
        super().save(*args, **kwargs)
        if is_created:
            contact_person = self.contact_person
            if contact_person:

                if ticket:
                    MessageTicketThroughModel.objects.create(
                        ticket=ticket,
                        message=self,
                    )
                else:
                    from .utils import get_completed_statuses_id
                    completed_statuses = get_completed_statuses_id()
                    tickets = HelpDeskTicketModel.objects.filter(
                        is_active=True,
                        contact_person=contact_person,
                        channel=self.channel
                    ).exclude(status_id__in=completed_statuses, ).order_by('-created_at')
                    if tickets.exists():
                        for ticket in tickets:
                            MessageTicketThroughModel.objects.create(
                                ticket=ticket,
                                message=self,
                            )
                        ticket = tickets.first()

                    else:
                        if not self.is_help_desk:
                            customer_card = self.contact_person.customer_card
                            unknown = customer_card.unknown
                            specialist = None
                            if unknown:
                                new_ticket_name = 'Лид'
                                ticket_type_id = 'lead'
                            else:
                                ticket_type_id = 'issue'
                                if self.channel_id == 'email' and self.email_subject:
                                    new_ticket_name = self.email_subject
                                else:
                                    new_ticket_name = BeautifulSoup(self.text, 'lxml').get_text(
                                        separator=" ", strip=True
                                    )
                                if len(new_ticket_name) >= 100:
                                    new_ticket_name = new_ticket_name[:97] + '...'
                                actual_specialists = customer_card.actual_specialists
                                if actual_specialists.count() == 1:
                                    specialist = actual_specialists.first().user
                            new_ticket = HelpDeskTicketModel.objects.create(
                                name=new_ticket_name,
                                description=self.text,
                                channel=self.channel,
                                contact_person=self.contact_person,
                                customer_card=customer_card,
                                created_from_messages=True,
                                ticket_type_id=ticket_type_id,
                                specialist=specialist
                            )
                            transaction.on_commit(lambda: new_ticket.set_attachments_from_message(self))
                            MessageTicketThroughModel.objects.create(
                                ticket=new_ticket,
                                message=self,
                            )
                            from .notifications import notify_about_new_ticket
                            transaction.on_commit(lambda: async_task(notify_about_new_ticket, str(new_ticket.pk)))
            if not self.is_help_desk:
                from .notifications import notify_about_new_ticket_client_message
                transaction.on_commit(
                    lambda: async_task(notify_about_new_ticket_client_message, str(ticket.pk), str(self.pk))
                )
            transaction.on_commit(lambda: self.send_socketio_about_new_message())

    def send_socketio_about_new_message(self):
        from .serializers import ContactPersonMessageListSerializer, ContactPersonMessageClientListSerializer
        s_data = ContactPersonMessageListSerializer(instance=self).data
        recipients = set(self.contact_person.customer_card.actual_specialists.values_list('user', flat=True))
        try:
            org_admin_id = self.contact_person.customer_card.org_admin.pk
        except AttributeError:
            members = set()
        else:
            members = users_that_have_app_section_role_in_contractors(
                (org_admin_id,),
                'help_desk',
            )
        recipients = recipients | members
        data = json.dumps(
            {
                "event": "notify",
                "data": {
                    "message": {
                        "event_type": "help_desk_message_create",
                        "obj": s_data,
                        "tickets": list(self.tickets.all().values_list('pk', flat=True))
                    },
                    "recipients": list(recipients),
                }
            },
            cls=DjangoJSONEncoder
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
        contact_person = self.contact_person
        if contact_person:
            contact_person_user = contact_person.user
            if contact_person_user:
                client_s_data = ContactPersonMessageClientListSerializer(instance=self).data
                client_data = json.dumps(
                    {
                        "event": "notify",
                        "data": {
                            "message": {
                                "event_type": "help_desk_client_message_create",
                                "obj": client_s_data,
                                "tickets": list(self.tickets.all().values_list('pk', flat=True))
                            },
                            "recipients": [contact_person_user.pk],
                        }
                    },
                    cls=DjangoJSONEncoder
                )
                socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, client_data)

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        user = request.user.profile
        director_contractors = set(contractors_where_im_director(user))
        permission_contractors = set(
            contractors_where_user_has_permission(
                user.pk,
                (
                    'admin',
                    'help_desk_admin',
                    'help_desk_manager',
                    'help_desk_supervisor',
                ),
                None,
            )
        )
        permission_contractors.update(director_contractors)
        qs = qs.filter(
            contact_person__customer_card__org_admin__in=permission_contractors,
            contact_person__is_active=True,
            contact_person__customer_card__is_active=True,
            contact_person__customer_card__org_admin__is_active=True,
        )
        return qs

    def get_update_permission(self, request) -> bool:
        return self.contact_person.customer_card.get_update_permission(request)

    def get_detail_permission(self, request) -> bool:
        return self.contact_person.customer_card.get_detail_permission(request)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContactPersonMessageListSerializer, ContactPersonMessageNotifySerializer
        if action == 'notify':
            return ContactPersonMessageNotifySerializer
        else:
            return ContactPersonMessageListSerializer


class HelpDeskConfigModel(common_models.BaseAbstractModel):
    contractor = models.OneToOneField(
        'catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Организация'),
        related_name='help_desk_config',
    )
    ticket_prefix = models.CharField(
        max_length=10,
        null=False,
        default='',
        blank=True,
        verbose_name=_('префикс тикетов')
    )
    telegram_token = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Токен telegram')
    )
    telegram_webhook_token = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Токен вебхука телеграм')
    )
    telegram_user = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Имя пользователя telegram')
    )
    email_pass = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Пароль email')
    )
    imap_server = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('IMAP-сервер')
    )
    imap_port = common_fields.CustomPositiveIntegerField(
        null=False,
        default=993,
        blank=True,
    )

    smtp_server = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    smtp_port = common_fields.CustomPositiveIntegerField(
        null=False,
        default=465,
        blank=True,
    )
    email_username = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Имя пользователя эл. почты')
    )
    email_last_uid = common_fields.CustomCharField(
        max_length=127,
        null=False,
        default='',
        blank=True,
        verbose_name=_('UID последнего email-сообщения')
    )
    email_signature = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name=_('Подпись email сообщения')
    )

    class Meta:
        verbose_name = _('Конфигурация техподдержки')
        verbose_name_plural = _('Конфигурации техподдержки')


class HelpDeskTicketTypeModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'created_at', 'mentions', 'ct', ]

    class Meta:
        verbose_name = _('Тип тикета')
        verbose_name_plural = _('Типы тикета')
        ordering = ('sort', 'name',)


class HelpDeskTicketModel(common_models.BaseModel, common_models.MetadataAbstractModel):
    meta_exclude_fields = ['visors', 'messages', 'created_at', 'completed_by_reserve', 'mentions', 'ct',]
    field_verbose_names = {'author': _('Создатель обращения'), }

    COMPLETED_BY_SPECIALIST_TYPE_CHOICES = (
        ('primary', _('Основной')),
        ('reserve', _('Заменяющий')),
    )

    tracker = FieldTracker(
        fields=(
            'status_id',
            'category_id',
            'priority_id',
            'specialist_id',
            'contact_person_id',
            'name',
            'description',
            'execution_result',
            'dead_line',
            'start_date',
            'end_date',
            'receipt_date',
            'analytics_key_id',
        )
    )

    ticket_type = common_fields.CustomForeignKey(
        to='HelpDeskTicketTypeModel',
        to_field='code',
        null=False,
        default='issue',
        on_delete=CUSTOM_PROTECT,
        related_name='help_desk_tickets',
        verbose_name=_('Тип')
    )
    number = common_fields.CustomCharField(
        max_length=31,
        null=False,
        default='',
        blank=False,
        verbose_name=_('Номер')
    )
    counter = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Номер (число)')
    )
    channel = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskChannelModel',
        to_field='code',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='help_desk_tickets',
        verbose_name=_('Канал связи'),
    )
    category = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketCategoryModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Категория'),
        related_name='help_desk_tickets'
    )
    priority = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketPriorityModel',
        to_field='code',
        null=False,
        blank=True,
        default='2',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Приоритет'),
        related_name='help_desk_tickets',
    )
    status = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketStatusModel',
        to_field='code',
        null=False,
        blank=True,
        default='new',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Статус'),
        related_name='help_desk_tickets',
    )

    status_from_client = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Статус от клиента')
    )

    customer_card = common_fields.CustomForeignKey(
        to='help_desk.CustomerCardModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Клиент'),
        related_name='help_desk_tickets',
    )
    specialist = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Ответственный'),
        related_name='help_desk_tickets',
        filter_info=filter_fields.ProfileFilterField()
    )
    contact_person = common_fields.CustomForeignKey(
        to='help_desk.ContactPersonModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Контактное лицо'),
        related_name='help_desk_tickets',
    )
    analytics_key = common_fields.CustomForeignKey(
        to='customer_contracts.CustomerContractProjectModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name=_('Ключ аналитики'),
        related_name='help_desk_tickets',
    )

    visors = models.ManyToManyField(
        to='users.ProfileModel',
        through='help_desk.HelpDeskTicketVisorsModel',
        through_fields=('ticket', 'user'),
        related_name='ticket_visors',
        verbose_name=_('Наблюдатели'),
    )
    members = models.ManyToManyField(
        to='users.ProfileModel',
        through='help_desk.HelpDeskTicketMembersModel',
        through_fields=('ticket', 'user'),
        related_name='ticket_members',
        verbose_name=_('Участники'),
    )
    created_from_messages = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Создано из сообщений')
    )
    messages = models.ManyToManyField(
        to='help_desk.ContactPersonMessageModel',
        through='help_desk.MessageTicketThroughModel',
        through_fields=('ticket', 'message',),
        related_name='tickets',
        verbose_name=_('Сообщения')
    )
    name = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Название'),
    )
    description = models.TextField(
        null=False,
        default='',
        blank=True,
        verbose_name=_('Описание')
    )
    execution_result = common_fields.CustomCharField(
        max_length=1000,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Результат выполнения')
    )
    dead_line = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Крайний срок')
    )
    start_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата начала работы')
    )
    end_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата завершения')
    )
    receipt_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата поступления'),
        help_text='Дата создания, которую можно переопределять'
    )
    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Продолжительность, сек'),
        help_text='в секундах'
    )

    completed_by_reserve = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Завершено не основным специалистом')
    )

    completed_by_specialist_type = common_fields.CustomCharField(
        max_length=50,
        null=False,
        blank=True,
        default='',
        choices=COMPLETED_BY_SPECIALIST_TYPE_CHOICES,
        verbose_name=_('Какой специалист завершил (основной/заменяющий)'),
        filter_info=filter_fields.ChoiceFilterField(),
        filter_lookup={'value': '__in'},
    )

    is_overdue_filter = fields.TicketIsOverdueFilterField()
    visors_filter = fields.VisorFilterField()
    members_filter = fields.MemberFilterField()
    help_desk_ticket_org_admin_filter = fields.HelpDeskTicketOrgAdminFilterField()
    rating_filter = fields.RatingFilterField()

    class Meta:
        verbose_name = _('Обращение')
        verbose_name_plural = _('Обращения')
        ordering = ('-created_at',)

    @property
    def get_member_ids(self):
        """Возвращает список ID ProfileModel участников обращения.
        Участниками считаются: ответственный (specialist), контактное лицо (contact_person.user при наличии), наблюдатели."""
        member_ids = set()
        if self.specialist_id:
            member_ids.add(self.specialist_id)
        if self.contact_person_id:
            contact_person = self.contact_person
            if contact_person.user_id:
                member_ids.add(contact_person.user_id)
        member_ids.update(self.visors.filter(is_active=True).values_list('pk', flat=True))
        member_ids.update(self.members.filter(is_active=True).values_list('pk', flat=True))
        return list(member_ids)

    @property
    def reserve_specialists(self):
        """
        Строка ФИО запасных специалистов (is_reserve=True) по всем карточкам с тем же основным специалистом
        и org_admin, что и у карточки тикета. Для плейсхолдера {{ reserve_specialists }} в шаблоне отчёта.
        """
        if not self.customer_card_id:
            return ''
        main_specialist = CustomerSupportSpecialistModel.objects.filter(
            customer_card_id=self.customer_card_id,
            is_reserve=False,
        ).values_list('user_id', flat=True).first()
        if not main_specialist:
            return ''
        org_admin = self.customer_card.org_admin
        if not org_admin:
            return ''
        customer_card_ids = CustomerSupportSpecialistModel.objects.filter(
            user_id=main_specialist,
            is_reserve=False,
            customer_card__org_admin=org_admin,
        ).values_list('customer_card_id', flat=True)
        if not customer_card_ids:
            return ''
        reserve_qs = CustomerSupportSpecialistModel.objects.filter(
            customer_card_id__in=customer_card_ids,
            is_reserve=True,
        ).order_by('user_id').distinct('user_id').select_related('user__user')
        specialists = list(reserve_qs)
        specialists.sort(key=lambda spec: spec.user.user.get_full_name())
        return ', '.join(spec.user.user.get_full_name() for spec in specialists)

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def _extract_report_bounds(cls, request, field_names):
        """Возвращает границы периода (date_from, date_to) из списка фильтров поля."""
        if not field_names:
            return None, None

        cache_attr = "_helpdesk_ticket_report_bounds_cache"
        cache_value = getattr(request, cache_attr, None)
        if not isinstance(cache_value, dict):
            cache_value = {}
            setattr(request, cache_attr, cache_value)
        cache_key = tuple(sorted(field_names))
        if cache_key in cache_value:
            return cache_value[cache_key]

        filters_raw = None
        query_params = getattr(request, "query_params", None)
        if query_params is not None:
            filters_raw = query_params.get("filters")
        if filters_raw in (None, "") and hasattr(request, "data"):
            request_data = request.data
            if isinstance(request_data, dict):
                filters_raw = request_data.get("filters")

        if not filters_raw:
            cache_value[cache_key] = (None, None)
            return None, None

        parsed_filters = filters_raw
        if isinstance(filters_raw, str):
            try:
                parsed_filters = json.loads(filters_raw)
            except (TypeError, json.JSONDecodeError):
                cache_value[cache_key] = (None, None)
                return None, None

        if isinstance(parsed_filters, list):
            parsed_filters = {
                "logic": "and",
                "filters": parsed_filters,
            }

        if not isinstance(parsed_filters, dict):
            cache_value[cache_key] = (None, None)
            return None, None

        def to_date(raw_value):
            if raw_value is None:
                return None
            if isinstance(raw_value, datetime.datetime):
                return raw_value.date()
            if isinstance(raw_value, datetime.date):
                return raw_value
            if isinstance(raw_value, str):
                parsed_datetime = dateparse.parse_datetime(raw_value)
                if parsed_datetime is not None:
                    return parsed_datetime.date()
                parsed_date = dateparse.parse_date(raw_value)
                if parsed_date is not None:
                    return parsed_date
            return None

        def iter_leaf_filters(group):
            for filter_item in group.get("filters", []):
                if "filters" in filter_item and isinstance(filter_item, dict):
                    yield from iter_leaf_filters(filter_item)
                elif isinstance(filter_item, dict):
                    yield filter_item

        period_from = None
        period_to = None
        field_names_set = set(field_names)
        for filter_item in iter_leaf_filters(parsed_filters):
            if filter_item.get("field") not in field_names_set:
                continue
            comparison_type = filter_item.get("comparison_type")
            raw_value = filter_item.get("value")
            normalized_date = to_date(raw_value)
            if normalized_date is None:
                continue

            if comparison_type in (">=", ">"):
                if period_from is None or normalized_date > period_from:
                    period_from = normalized_date
            elif comparison_type in ("<=", "<"):
                if period_to is None or normalized_date < period_to:
                    period_to = normalized_date

        cache_value[cache_key] = (period_from, period_to)
        return period_from, period_to

    @classmethod
    def get_report_annotations(cls, request, requested_computed, **kwargs):
        """Возвращает SQL-аннотации для отчётов.

        Поддерживаемое вычисляемое поле:
        - time_to_close: разница end_date - receipt_date (IntegerField, секунды)
        - time_to_first_response: разница start_date - receipt_date (IntegerField, секунды)
        - work_duration: duration (секунды) как IntegerField для форматирования
        - hours: duration переведённый в часы (DecimalField, 2 знака)
        - main_specialist: основной специалист карточки (is_reserve=False) как FK на ProfileModel (UUID).
        При запросе main_specialist добавляется и main_specialist_sort (ФИО) для сортировки.
        """
        from django.db.models import Case, CharField, F, Func, IntegerField, OuterRef, Subquery, Value, When
        from django.db.models.functions import Cast, Concat, Coalesce, Extract, TruncDate
        from django.db.models.expressions import ExpressionWrapper

        annotations = {}
        names = set(requested_computed or [])
        period_from, period_to = cls._extract_report_bounds(
            request,
            ["report_day", "report_period", "receipt_date", "end_date"],
        )

        if 'report_day' in names:
            annotations['report_day'] = TruncDate('receipt_date')

        completed_statuses = []
        if names.intersection({'closed_in_period', 'currently_completed', 'currently_overdue'}):
            from .utils import get_completed_statuses_id
            completed_statuses = get_completed_statuses_id()

        if 'currently_completed' in names:
            annotations['currently_completed'] = models.Case(
                models.When(models.Q(status_id__in=completed_statuses), then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            )

        if 'currently_overdue' in names:
            annotations['currently_overdue'] = models.Case(
                models.When(
                    models.Q(
                        dead_line__isnull=False,
                        dead_line__lt=timezone.now(),
                    ) & ~models.Q(status_id__in=completed_statuses),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=models.BooleanField(),
            )

        created_period_filter = models.Q(receipt_date__isnull=False)
        created_period_is_set = False
        if period_from is not None:
            created_period_filter &= models.Q(receipt_date__date__gte=period_from)
            created_period_is_set = True
        if period_to is not None:
            created_period_filter &= models.Q(receipt_date__date__lte=period_to)
            created_period_is_set = True

        if 'created_in_period' in names:
            if created_period_is_set:
                annotations['created_in_period'] = models.Case(
                    models.When(created_period_filter, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            else:
                annotations['created_in_period'] = Value(False, output_field=models.BooleanField())

        closed_period_filter = models.Q(
            status_id__in=completed_statuses,
            end_date__isnull=False,
        )
        closed_period_is_set = False
        if period_from is not None:
            closed_period_filter &= models.Q(end_date__date__gte=period_from)
            closed_period_is_set = True
        if period_to is not None:
            closed_period_filter &= models.Q(end_date__date__lte=period_to)
            closed_period_is_set = True

        if 'closed_in_period' in names:
            if closed_period_is_set:
                annotations['closed_in_period'] = models.Case(
                    models.When(closed_period_filter, then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            else:
                annotations['closed_in_period'] = Value(False, output_field=models.BooleanField())

        if 'link' in names:
            base_url = URLS['helpdesk_tickets']
            url_expr = Concat(
                Value(base_url),
                Value('?ticketView='),
                Cast(F('pk'), CharField()),
            )
            annotations['link'] = Func(
                Value('repr'),
                F('number'),
                Value('url'),
                url_expr,
                function='jsonb_build_object',
                output_field=models.JSONField(),
            )
        if 'main_specialist' in names:
            main_specialist_sort_qs = CustomerSupportSpecialistModel.objects.filter(
                customer_card_id=OuterRef('customer_card_id'),
                is_reserve=False,
            ).annotate(
                full_name=Concat(
                    Coalesce(F('user__user__last_name'), Value('')),
                    Value(' '),
                    Coalesce(F('user__user__first_name'), Value('')),
                    Value(' '),
                    Coalesce(F('user__user__middle_name'), Value('')),
                    output_field=CharField(),
                ),
            ).values_list('full_name', flat=True)[:1]
            annotations['main_specialist_sort'] = Subquery(
                main_specialist_sort_qs, output_field=CharField()
            )
            main_specialist_qs = CustomerSupportSpecialistModel.objects.filter(
                customer_card_id=OuterRef('customer_card_id'),
                is_reserve=False,
            ).values_list('user_id', flat=True)[:1]
            annotations['main_specialist'] = Subquery(
                main_specialist_qs,
                output_field=models.UUIDField(),
            )
        if 'time_to_close' in names:
            annotations['time_to_close'] = Extract(
                F('end_date') - F('receipt_date'),
                'epoch',
                output_field=IntegerField()
            )
        if 'time_to_first_response' in names:
            annotations['time_to_first_response'] = Extract(
                F('start_date') - F('receipt_date'),
                'epoch',
                output_field=IntegerField()
            )
        if 'work_duration' in names:
            annotations['work_duration'] = ExpressionWrapper(
                F('duration'),
                output_field=IntegerField()
            )
        if 'hours' in names:
            annotations['hours'] = Func(
                Cast(F('duration'), models.DecimalField(max_digits=10, decimal_places=2)) / Value(3600),
                Value(2),
                function='ROUND',
                output_field=models.DecimalField(max_digits=10, decimal_places=2),
            )
        if 'related_tasks' in names:
            from django.db.models.expressions import RawSQL
            from bpms.tasks.models import TaskModel
            ticket_table = cls._meta.db_table
            task_table = TaskModel._meta.db_table
            ticket_pk_column = cls._meta.pk.column
            task_pk_column = TaskModel._meta.pk.column
            base_url = URLS['tasks']
            sql = (
                f"(SELECT COALESCE(jsonb_agg(j), '[]'::jsonb) FROM ("
                f"SELECT jsonb_build_object('repr', {task_table}.counter, 'url', %s || '?task=' || {task_table}.{task_pk_column}::text) AS j "
                f"FROM {task_table} "
                f"WHERE {task_table}.reason = {ticket_table}.{ticket_pk_column}::text AND {task_table}.is_active_custom = true"
                f") sub)"
            )
            annotations['related_tasks'] = RawSQL(
                sql, [base_url], output_field=models.JSONField()
            )
        if 'related_chat' in names:
            from bpms.chat.models import ChatModel, MessageModel

            uuid_regex = (
                r'^[0-9a-fA-F]{8}-'
                r'[0-9a-fA-F]{4}-'
                r'[0-9a-fA-F]{4}-'
                r'[0-9a-fA-F]{4}-'
                r'[0-9a-fA-F]{12}$'
            )
            # Берём строго первое сообщение тикета по created_at.
            # Если оно не связано с chat.MessageModel, related_chat остаётся пустым.
            through_with_chat_qs = MessageTicketThroughModel.objects.filter(
                ticket_id=OuterRef('pk'),
            ).annotate(
                message_uid_cast=Case(
                    When(
                        message__message_id__regex=uuid_regex,
                        then=Cast(F('message__message_id'), models.UUIDField()),
                    ),
                    default=Value(None),
                    output_field=models.UUIDField(),
                ),
                chat_uid=Subquery(
                    MessageModel.objects.filter(
                        message_uid=OuterRef('message_uid_cast'),
                    ).values_list('chat_id', flat=True)[:1]
                ),
                chat_pk=Subquery(
                    ChatModel.objects.filter(
                        chat_uid=OuterRef('chat_uid'),
                    ).values_list('pk', flat=True)[:1]
                ),
                chat_name=Subquery(
                    ChatModel.objects.filter(
                        chat_uid=OuterRef('chat_uid'),
                    ).values_list('name', flat=True)[:1]
                ),
            ).order_by(
                'created_at',
            )
            annotations['related_chat_sort'] = Subquery(
                through_with_chat_qs.values_list('chat_name', flat=True)[:1],
                output_field=CharField(),
            )
            annotations['related_chat'] = Subquery(
                through_with_chat_qs.values_list('chat_pk', flat=True)[:1],
                output_field=models.UUIDField(),
            )
        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                "name": "report_day",
                "type": "DateField",
                "verbose_name": _("Дата отчета"),
                "date_axis": True,
                "axis_granularity": "day",
                "axis_freq": "D",
                "apply_to_queryset": False,
                "period_filter": {
                    "start_field": "receipt_date",
                    "end_field": "receipt_date",
                },
            },
            {
                "name": "created_in_period",
                "type": "BooleanField",
                "verbose_name": _("Создано за период"),
            },
            {
                "name": "closed_in_period",
                "type": "BooleanField",
                "verbose_name": _("Закрыто за период"),
            },
            {
                "name": "currently_completed",
                "type": "BooleanField",
                "verbose_name": _("Завершено"),
            },
            {
                "name": "currently_overdue",
                "type": "BooleanField",
                "verbose_name": _("Просрочено"),
            },
            {
                "name": "link",
                "type": "CharField",
                "verbose_name": _("Ссылка"),
                "order_by_field": "counter",
            },
            {
                "name": "time_to_close",
                "type": "DurationField",
                "verbose_name": _("Время от создания до закрытия"),
            },
            {
                "name": "time_to_first_response",
                "type": "DurationField",
                "verbose_name": _("Время до взятия в работу"),
            },
            {
                "name": "work_duration",
                "type": "DurationField",
                "verbose_name": _("Трудозатраты"),
            },
            {
                "name": "hours",
                "type": "DecimalField",
                "verbose_name": _("Затраченные часы"),
            },
            {
                "name": "main_specialist",
                "type": "ForeignKey",
                "related_model": "users.ProfileModel",
                "verbose_name": _("Основной специалист"),
                "order_by_field": "main_specialist_sort",
            },
            {
                "name": "related_chat",
                "type": "ForeignKey",
                "related_model": "chat.ChatModel",
                "verbose_name": _("Чат (источник обращения)"),
                "order_by_field": "related_chat_sort",
            },
            {
                "name": "related_tasks",
                "type": "LinkListField",
                "verbose_name": _("Задачи"),
            },
        ]

    @classmethod
    def build_report_field_q(cls, field, comparison, value):
        """
        Хук для отчётной фильтрации вычисляемого `customer_card__tags`.

        На уровне БД `customer_card__tags` является ArrayField(UUID), поэтому стандартный
        lookup `__in` может пытаться распарсить RHS как массив UUID и падать.
        Мы конвертим filter по tag_id в список customer_card_id через TagRelatedObjectThrough.
        """
        if not field or comparison not in ("=", "in", "!=", "not in"):
            return None
        if not field.endswith("__tags"):
            return None

        is_negative = comparison in ("!=", "not in")
        if value in (None, ""):
            return Q() if is_negative else Q(pk__in=[])

        from tags.models import TagRelatedObjectThrough
        from common.utils import is_uuid as common_is_uuid

        relation_path = field.rsplit("__", 1)[0]  # например: "customer_card"

        # Нормализуем RHS в список tag_id
        if comparison in ("in", "not in") and isinstance(value, str):
            raw_values = [item.strip() for item in value.split(",") if item.strip()]
        elif not isinstance(value, (list, tuple, set)):
            raw_values = [value]
        else:
            raw_values = list(value)

        normalized_tag_ids = []
        for item in raw_values:
            if isinstance(item, dict):
                tag_id = item.get("id") or item.get("pk") or item.get("value")
            else:
                tag_id = item
            if tag_id in (None, ""):
                continue
            if common_is_uuid(tag_id):
                normalized_tag_ids.append(tag_id)

        if not normalized_tag_ids:
            return Q() if is_negative else Q(pk__in=[])

        tagged_object_ids = TagRelatedObjectThrough.objects.filter(
            tag_id__in=normalized_tag_ids,
            tag_id__isnull=False,
        ).values_list("related_object_id", flat=True).distinct()

        # customer_card_id / specialist_id / etc.
        try:
            fk_field = cls._meta.get_field(relation_path)
            attname = getattr(fk_field, "attname", f"{relation_path}_id")
        except Exception:
            attname = f"{relation_path}_id"

        base_q = Q(**{f"{attname}__in": tagged_object_ids})
        if is_negative:
            return ~base_q
        return base_q

    @classmethod
    def get_table_columns(cls):
        return ['category', 'channel', 'customer_card', 'specialist', 'author',
                'help_desk_ticket_org_admin_filter', 'contact_person', 'status', 'created_at', 'visors_filter',
                'members_filter', 'is_overdue_filter', 'rating_filter', ]

    @classmethod
    def get_filter_fields(cls, exclude: bool = False, request=None):
        """Исключаем лишние поля из фильтра страницы 'Неподтвержденные обращения'"""
        page_name = request.query_params.get('page_name', '')
        data = super().get_filter_fields(exclude, request)
        if page_name == 'help_desk.UnconfirmedAppealsPage':
            data = list(filter(
                lambda x: x.get('name', '') not in (
                    'customer_card',
                    'customer_card__exclude',
                    'specialist',
                    'specialist__exclude',
                    'author',
                    'author__exclude',
                    'contact_person',
                    'contact_person__exclude',
                    'visors_filter',
                    'visors_filter__exclude',
                    'members_filter',
                    'members_filter__exclude',
                    'is_overdue_filter',
                    'is_overdue_filter__exclude',
                ),
                data
            ))
        if 'helpdeskforclient' in page_name.lower():
            data = list(filter(
                lambda x: x.get('name', '') not in (
                    'customer_card',
                    'customer_card__exclude',
                    'contact_person',
                    'contact_person__exclude',
                    'visors_filter',
                    'visors_filter__exclude',
                    'members_filter',
                    'members_filter__exclude',
                    'is_overdue_filter',
                    'is_overdue_filter__exclude',
                    'help_desk_ticket_org_admin_filter',
                    'help_desk_ticket_org_admin_filter__exclude',
                ),
                data
            ))
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.HelpDeskTicketCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.HelpDeskTicketUpdateSerializer
        elif action == 'retrieve':
            return serializers.HelpDeskTicketDetailSerializer
        elif action == 'notify':
            return serializers.HelpDeskTicketNotifySerializer
        elif action == 'chat_share':
            return serializers.HelpDeskTicketChatShareSerializer
        elif action == 'short_list':
            return serializers.HelpDeskTicketShortSerializer
        else:
            return serializers.HelpDeskTicketListSerializer

    @classmethod
    def get_queryset(cls, request=None, queryset_params=None):
        """queryset_params - передаются из отчетов. Чтобы указать в качестве кого мы получаем тикеты:
        в качестве клиента (view_type='client') или в качестве поставщика услуг (view_type='contractor')."""
        qs = cls.objects.filter(is_active=True)

        # Если это не для отчета (не переданы queryset_params), то оставляем как было
        if not request or not queryset_params:
            return qs
        view_type = queryset_params.get('view_type')
        qs = cls.filter_by_permissions(qs, request, view_type)
        return qs

    @classmethod
    def filter_by_permissions(cls, qs, request, view_type='contractor'):
        user = request.user.profile
        from contractor_permissions.utils import (
            contractors_where_user_has_permission,
            contractors_where_im_director
        )
        from users.utils import get_ancestor_departments_related_organizations
        if view_type == 'contractor':
            # Базовый queryset (без M2M-join по visors) — на нём строим окончательный список тикетов
            base_qs = qs.filter(contact_person__spam=False, customer_card__is_active=True)

            help_desk_admin_contractors = set(
                contractors_where_user_has_permission(
                    user.pk,
                    ('help_desk_admin', 'help_desk_supervisor'),
                    None,
                )
            )
            help_desk_manager_contractors = set(
                contractors_where_user_has_permission(
                    user.pk,
                    ('help_desk_manager',),
                    None,
                )
            )

            # Карточки клиентов, по которым пользователь является специалистом
            specialist_customer_cards = CustomerCardModel.get_qs_customer_cards_from_specialist(
                user.pk
            ).filter(
                org_admin_id__in=help_desk_manager_contractors
            ).values_list('pk', flat=True)

            # Пермишены считаем через подзапрос с EXISTS,
            # чтобы не тянуть M2M-join по visors в основной queryset.
            perm_subquery = cls.objects.filter(
                pk=OuterRef('pk')
            ).filter(
                Q(customer_card__org_admin_id__in=help_desk_admin_contractors) |
                Q(customer_card_id__in=specialist_customer_cards) |
                Q(visors=user) |
                Q(members=user)
            )

            qs = base_qs.filter(Exists(perm_subquery))
        elif view_type == 'client':
            contact_persons = ContactPersonModel.objects.filter(
                is_active=True,
                user=user,
            ).values_list('pk', flat=True)
            director_contractors = get_ancestor_departments_related_organizations(
                contractors_where_im_director(user),
                include_self=True
            )
            client_contractors = get_ancestor_departments_related_organizations(
                contractors_where_user_has_permission(
                    user.pk,
                    ('help_desk_client_supervisor', 'help_desk_client_admin',),
                    None
                ),
                include_self=True,
            )

            permission_contractors = director_contractors | client_contractors
            qs = qs.filter(
                Q(customer_card__customer_id__in=permission_contractors) |
                Q(contact_person__in=contact_persons)
            ).exclude(ticket_type_id='lead').distinct()
        else:
            qs = qs.none()
        return qs

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.objects.none()

    @staticmethod
    def get_sla(data: dict):
        """
        Получаем данные по объекту, возвращаем данные по sla объекта
        """
        from sla.models import SLAModel, SLARelatedObjectModel
        from sla.serializers import SLAListSerializer, SLARelatedObjectSerializer
        customer_card_id = data.get('customer_card')
        # return_data = {'first_reaction_time': None, 'solve_time': None}
        return_data = dict()
        if customer_card_id:
            try:
                customer_card = CustomerCardModel.objects.get(pk=customer_card_id)
            except (ValidationError, ObjectDoesNotExist,):
                return None
            else:
                org_admin = customer_card.org_admin
            post_inst = None
            category = None
            if org_admin:
                contact_person_id = data.get('contact_person')
                contact_person = None
                if contact_person_id:
                    try:
                        contact_person = ContactPersonModel.objects.get(pk=contact_person_id)
                    except (ValidationError, ObjectDoesNotExist,):
                        pass
                    else:
                        post_inst = contact_person.post_inst
                category_id = data.get('category')
                if category_id:
                    try:
                        category = HelpDeskTicketCategoryModel.objects.get(pk=category_id)
                    except (ValidationError, ObjectDoesNotExist,):
                        pass
                sla_list = []
                if contact_person:
                    contact_person_sla = SLARelatedObjectModel.objects.filter(
                        related_object=contact_person,
                        sla__contractor=org_admin,
                    ).order_by('created_at').first()
                    if contact_person_sla:
                        sla_list.append(('contact_person', contact_person_sla))
                    else:
                        if post_inst:
                            post_inst_sla = SLARelatedObjectModel.objects.filter(
                                related_object=post_inst,
                                sla__contractor=org_admin
                            ).order_by('created_at').first()
                            if post_inst_sla:
                                sla_list.append(('post', post_inst_sla))
                if category:
                    category_sla = SLARelatedObjectModel.objects.filter(
                        related_object=category,
                        sla__contractor=org_admin
                    ).order_by('created_at').first()
                    if category_sla:
                        sla_list.append(('category', category_sla))
                if sla_list:
                    sorted_sla_list = sorted(sla_list, key=lambda x: x[1].sla.level)
                    sla = sorted_sla_list[0]
                    return_data = {
                        'sla': SLAListSerializer(sla[1].sla).data
                    }
                    source_list = []
                    for each in sorted_sla_list:
                        source_dict = SLARelatedObjectSerializer(each[1]).data
                        if each[0] == 'post':
                            source_dict['description'] = 'Должность контактного лица'
                        elif each[0] == 'category':
                            source_dict['description'] = 'Категория обращения'
                        elif each[0] == 'contact_person':
                            source_dict['description'] = 'Контактное лицо'
                        source_list.append(source_dict)
                    return_data['sources'] = source_list
                else:
                    default_sla = SLAModel.objects.filter(
                        contractor=org_admin,
                        is_default=True
                    ).order_by('created_at').first()
                    if default_sla:
                        default_sla_data = SLAListSerializer(default_sla).data
                        return_data = {
                            'sla': default_sla_data,
                            'sources': [
                                {
                                    'sla': default_sla_data,
                                    'related_object': None,
                                    'description': 'По умолчанию'
                                }
                            ]
                        }
        return return_data

    def filter_comment_qs(self, user, queryset):
        """Фильтруем queryset комментариев, связанных с обращением"""
        org_admin = self.customer_card.org_admin
        try:
            check_contractor_permission(
                user.pk,
                org_admin.pk,
                ('help_desk_admin', 'help_desk_manager', 'help_desk_supervisor'),
                None
            )
        except drf_exceptions.PermissionDenied:
            if not self.visors.filter(pk=user.pk).exists() and not self.members.filter(pk=user.pk).exists():
                queryset = queryset.filter(is_personal=False)
        return queryset

    def set_attachments_from_message(self, message):
        self.attachments.set(list(message.attachments.all()))

    def set_sla_value(self):
        from sla.models import SLAValueModel
        category = self.category
        if category:
            category_id = category.pk
        else:
            category_id = None
        sla_dict = {
            'customer_card': self.customer_card_id,
            'contact_person': self.contact_person_id,
        }
        if category_id:
            sla_dict['category'] = self.category_id
        sla_data = self.get_sla(
            sla_dict,
        )
        if sla_data:
            with transaction.atomic():
                sla_value, created = SLAValueModel.objects.update_or_create(
                    related_object=self,
                    defaults={
                        'first_reaction_time': sla_data['sla'].get('first_reaction_time'),
                        'solve_time': sla_data['sla'].get('solve_time'),
                        'sla_id': sla_data['sla'].get('id')
                    }
                )
                sla_sources = sla_data.get('sources')
                sla_value.value_sources.clear()
                if sla_sources:
                    for each in sla_sources:
                        related_object = each.get('related_object')
                        if related_object:
                            related_object_id = related_object.get('id')
                        else:
                            related_object_id = None
                        sla_value.value_sources.create(
                            owner=sla_value,
                            related_object_id=related_object_id,
                            description=each.get('description', ''),
                            first_reaction_time=each['sla'].get('first_reaction_time'),
                            solve_time=each['sla'].get('solve_time'),
                            sla_id=each['sla'].get('id')
                        )
        else:
            SLAValueModel.objects.filter(
                related_object=self,
            ).delete()

    def track_m2m_fields(self, sender, model, pk_set, action, action_date):
        try:
            sender_label = sender.get_label()
        except AttributeError:
            return
        if sender_label == 'common.FileBaseModel':
            object_property_id = 'help_desk_ticket__attachments'
            str_view = ','.join([each.full_name for each in list(model.objects.filter(pk__in=pk_set))])
        elif sender_label == 'help_desk.HelpDeskTicketVisorsModel':
            object_property_id = 'help_desk_ticket__visors'
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
        if 'contact_person_id' in changed_fields:
            contact_person_id_before = changed_fields['contact_person_id']
            contact_person_id_after = self.contact_person.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'help_desk_ticket__contact_person',
                contact_person_id_before,
                contact_person_id_after,
            )
        if 'status_id' in changed_fields:
            status_code_before = changed_fields['status_id']
            if status_code_before:
                status_id_before = HelpDeskTicketStatusModel.objects.get(code=status_code_before).pk
            else:
                status_id_before = None
            status_id_after = self.status.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'help_desk_ticket__status',
                status_id_before,
                status_id_after,
            )
        if 'category_id' in changed_fields:
            category_id_before = changed_fields['category_id']
            category_id_after = self.category.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'help_desk_ticket__category',
                category_id_before,
                category_id_after,
            )
        if 'priority_id' in changed_fields:
            priority_code_before = changed_fields['priority_id']
            if priority_code_before:
                priority_id_before = HelpDeskTicketPriorityModel.objects.get(code=priority_code_before).pk
            else:
                priority_id_before = None
            priority_id_after = self.priority.pk
            change_history_utils.create_update_catalog_fk(
                self.pk,
                action_date,
                'help_desk_ticket__priority',
                priority_id_before,
                priority_id_after,
            )
        if 'specialist_id' in changed_fields:
            specialist_id_before = changed_fields['specialist_id']
            specialist_after = self.specialist
            if specialist_after:
                specialist_id_after = self.specialist.pk
            else:
                specialist_id_after = None
            change_history_utils.create_update_profile_fk(
                self.pk,
                action_date,
                'help_desk_ticket__specialist',
                specialist_id_before,
                specialist_id_after,
            )
        if 'name' in changed_fields:
            before = changed_fields['name'],
            after = self.name,
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'help_desk_ticket__name',
                before,
                after,
            )
        if 'description' in changed_fields:
            before = changed_fields['description']
            after = self.description
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'help_desk_ticket__description',
                before,
                after,
            )
        if 'execution_result' in changed_fields:
            before = changed_fields['execution_result']
            after = self.execution_result
            change_history_utils.create_update_str(
                self.pk,
                action_date,
                'help_desk_ticket__execution_result',
                before,
                after,
            )
        if 'dead_line' in changed_fields:
            dead_line_before = changed_fields['dead_line']
            dead_line_after = self.dead_line
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'help_desk_ticket__dead_line',
                dead_line_before,
                dead_line_after,
            )
        if 'start_date' in changed_fields:
            start_date_before = changed_fields['start_date']
            start_date_after = self.start_date
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'help_desk_ticket__start_date',
                start_date_before,
                start_date_after,
            )
        if 'end_date' in changed_fields:
            end_date_before = changed_fields['end_date']
            end_date_after = self.end_date
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'help_desk_ticket__end_date',
                end_date_before,
                end_date_after,
            )
        if 'receipt_date' in changed_fields:
            receipt_date_before = changed_fields['receipt_date']
            receipt_date_after = self.receipt_date
            change_history_utils.create_update_datetime(
                self.pk,
                action_date,
                'help_desk_ticket__receipt_date',
                receipt_date_before,
                receipt_date_after,
            )

    def save(self, *args, **kwargs):
        is_created = True if self.pk is None else False
        stop_work_logs = False
        old_status_code = self.tracker.changed().get('status_id', '')
        old_analytics_key_id = self.tracker.changed().get('analytics_key_id', '')
        new_analytics_key = self.analytics_key
        if is_created:
            if not self.receipt_date:
                self.receipt_date = timezone.now()
            counter = self.get_counter_instance()
            self.number = counter.number_formatted
            self.counter = counter.number
        else:
            changed_fields = self.tracker.changed()
            if 'status_id' in changed_fields:
                profile = get_current_authenticated_profile()
                if profile \
                        and not self.specialist == profile \
                        and self.status_id in ('rejected', 'on_pause', 'completed', 'clarification_required'):
                    stop_work_logs = True
                specialist = self.specialist
                if specialist:
                    customer_card = self.customer_card
                    if not customer_card.actual_specialists.filter(is_reserve=False, user=specialist).exists():
                        self.completed_by_reserve = True
                        self.completed_by_specialist_type = 'reserve'
                    else:
                        self.completed_by_reserve = False
                        self.completed_by_specialist_type = 'primary'
        super().save(*args, **kwargs)
        if old_analytics_key_id:
            from customer_contracts.models import CustomerContractProjectModel
            old_analytics_key = CustomerContractProjectModel.objects.filter(pk=old_analytics_key_id).first()
            if old_analytics_key and old_analytics_key.customer_contract:
                old_analytics_key.customer_contract.recalculate_hours_fact()
        if new_analytics_key and new_analytics_key.customer_contract:
            new_analytics_key.customer_contract.recalculate_hours_fact()
        if stop_work_logs:
            from .utils import stop_work_log_timer
            incomplete_logs = HelpDeskWorkLogModel.objects.filter(
                ticket=self,
                is_current=True
            ).order_by('created_at')
            for each in incomplete_logs:
                with transaction.atomic():
                    user = each.user
                    stop_work_log_timer(user, self)
        if is_created:
            transaction.on_commit(lambda: self.send_socketio_about_new_ticket())
        if not is_created and self.is_active:
            from .utils import send_socketio_about_update_ticket
            transaction.on_commit(lambda: send_socketio_about_update_ticket(self))
        if not self.is_active and self.analytics_key and self.analytics_key.customer_contract:
            self.analytics_key.customer_contract.recalculate_hours_fact()
        from .utils import get_completed_statuses_id
        completed_statuses_id = get_completed_statuses_id()
        if old_status_code not in completed_statuses_id and self.status_id in completed_statuses_id:
            profiles_id = list(ProfileModel.objects.filter(current_work_id=self.pk).values_list('pk', flat=True))
            ProfileModel.objects.filter(pk__in=profiles_id).update(current_work=None)
            from common.utils import send_socketio_about_update_current_work
            transaction.on_commit(
                lambda: async_task(send_socketio_about_update_current_work, [str(_) for _ in profiles_id],)
            )


    def send_socketio_about_new_ticket(self):
        from .serializers import HelpDeskTicketNotifySerializer
        s_data = HelpDeskTicketNotifySerializer(instance=self).data
        recipients = list(self.customer_card.actual_specialists.values_list('user', flat=True))
        data = json.dumps(
            {
                "event": "notify",
                "data": {
                    "message": {
                        "event_type": "help_desk_new_ticket",
                        "obj": s_data,
                    },
                    "recipients": recipients,
                }
            },
            cls=DjangoJSONEncoder
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)

    def get_counter_instance(self):
        counter = HelpDeskTicketCounterModel.objects.create(org_admin=self.customer_card.org_admin)
        return counter

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if user == self.specialist and not self.status_id == 'completed':
            return True
        org_admin = self.customer_card.org_admin
        try:
            check_contractor_permission(user.pk, org_admin.pk, ('help_desk_admin',), None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def get_available_statuses(self, user):
        from users.utils import get_ancestor_departments_related_organizations
        current_status_code = self.status.code
        current_is_completed = False
        from .utils import get_completed_statuses_id
        completed_statuses = get_completed_statuses_id()
        if current_status_code in completed_statuses:
            current_is_completed = True
        available_statuses = []
        is_client = False
        contact_person = self.contact_person
        if contact_person:
            contact_person_user = contact_person.user
            if contact_person_user and contact_person_user == user:
                is_client = True
        is_specialist = self.specialist == user
        org_admin = self.customer_card.org_admin
        try:
            check_contractor_permission(user.pk, org_admin.pk, ('help_desk_admin',), None)
        except drf_exceptions.PermissionDenied:
            is_admin = False
        else:
            is_admin = True
        customer_id = self.customer_card.customer_id
        help_desk_client_admin_contractors = get_ancestor_departments_related_organizations(
            contractors_where_user_has_permission(
                user.pk,
                'help_desk_client_admin',
                None
            ),
            include_self=True,
        )
        is_help_desk_client_admin = customer_id in help_desk_client_admin_contractors

        if is_help_desk_client_admin and not current_is_completed:
            available_statuses = available_statuses + ['rejected', ]
        if is_help_desk_client_admin and current_is_completed:
            available_statuses = available_statuses + ['on_rework', ]
        if is_client and current_is_completed:
            available_statuses = available_statuses + ['on_rework', ]
        if is_client and not current_is_completed:
            available_statuses = available_statuses + ['rejected', 'completed']
        if is_admin and current_is_completed:
            available_statuses = available_statuses + ['on_rework', ]
        if is_admin and not current_is_completed:
            available_statuses = available_statuses + ['rejected', 'clarification_required']
        if is_specialist and not current_is_completed:
            available_statuses = available_statuses + ['in_work', 'on_pause', 'completed', 'clarification_required']
        available_statuses = set(available_statuses)
        available_statuses.discard(current_status_code)
        return list(available_statuses)

    def update_rating_permission(self, request) -> bool:
        user = request.user.profile
        contact_person = self.contact_person
        if contact_person:
            contact_person_user = contact_person.user
            if contact_person_user == user:
                return True
            else:
                return False
        else:
            return False

    def create_work_log_permission(self, request) -> bool:
        profile = request.user.profile
        if profile == self.specialist or self.members.filter(pk=profile.pk).exists():
            return True
        return self.edit_work_log_user_permission(request)

    def edit_work_log_user_permission(self, request):
        org_admin = self.customer_card.org_admin
        profile = request.user.profile
        try:
            check_contractor_permission(profile.pk, org_admin.pk, 'help_desk_admin', None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def update_execution_result_permission(self, request) -> bool:
        if not self.status_id == 'completed':
            return False
        org_admin = self.customer_card.org_admin
        profile = request.user.profile
        try:
            check_contractor_permission(profile.pk, org_admin.pk, 'help_desk_admin', None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def get_take_permission(self, request) -> bool:
        """
        Разрешение на взятие пользователем тикета: стать ответственным за тикет
        """
        if self.specialist:
            return False
        customer_card = self.customer_card
        org_admin = customer_card.org_admin
        user = request.user.profile
        try:
            check_contractor_permission(user.pk, org_admin.pk, 'help_desk_manager', None)
        except drf_exceptions.PermissionDenied:
            return False
        if customer_card.actual_specialists.filter(user=user).exists():
            return True
        return False

    def get_detail_permission(self, request) -> bool:
        from users.utils import get_ancestor_departments_related_organizations
        customer_card = self.customer_card
        org_admin = customer_card.org_admin
        user = request.user.profile
        contact_person = self.contact_person
        customer = customer_card.customer
        if customer:
            customer_director_list = get_ancestor_departments_related_organizations(
                contractors_where_im_director(user),
                include_self=True
            )
            customer_supervisor_list = get_ancestor_departments_related_organizations(
                contractors_where_user_has_permission(
                    user.pk,
                    ('help_desk_client_supervisor', 'help_desk_client_admin',),
                    None
                ),
                include_self=True,
            )

            customer_permission_list = customer_director_list | customer_supervisor_list

            if customer.pk in customer_permission_list:
                return True
        if self.visors.filter(pk=user.pk).exists() or self.members.filter(pk=user.pk).exists():
            return True
        if contact_person:
            contact_person_user = contact_person.user
            if contact_person_user == user:
                return True
        try:
            check_contractor_permission(
                user.pk,
                org_admin.pk,
                ('help_desk_admin', 'help_desk_supervisor'),
                None
            )
        except drf_exceptions.PermissionDenied:
            try:
                check_contractor_permission(
                    user.pk,
                    org_admin.pk,
                    ('help_desk_manager',),
                    None
                )
            except drf_exceptions.PermissionDenied:
                return False
            else:
                if customer_card.actual_specialists.filter(user=user).exists():
                    return True
                else:
                    return False
        else:
            return True

    def get_create_message_permission(self, request):
        from .utils import get_completed_statuses_id, get_ticket_first_chat_message
        completed_statuses = get_completed_statuses_id()
        if self.status_id in completed_statuses:
            return False
        org_admin_id = self.customer_card.org_admin.pk
        user = request.user.profile
        try:
            check_contractor_permission(user.pk, org_admin_id, ('help_desk_manager', 'help_desk_admin',), None)
        except drf_exceptions.PermissionDenied:
            return False
        if not user == self.specialist:
            return False
        if self.channel_id == 'internal_chat':
            chat_message = get_ticket_first_chat_message(self)
            if not chat_message:
                return False
            chat = chat_message.chat
            if chat.is_public:
                return False
        return True

    def get_delete_permission(self, request):
        if not self.channel_id == 'internal':
            return False
        user = request.user.profile
        org_admin = self.customer_card.org_admin
        try:
            check_contractor_permission(user.pk, org_admin.pk, ('help_desk_admin',), None)
        except drf_exceptions.PermissionDenied:
            return False
        else:
            return True

    def set_is_active(self, value: bool, request):
        if not self.get_delete_permission(request):
            raise drf_exceptions.PermissionDenied('Вы не можете удалить этот тикет')
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

    def __str__(self):
        return f"{self.number} {self.name}"


class HelpDeskTicketCounterModel(models.Model):
    org_admin = models.ForeignKey('catalogs.ContractorModel',
                                  null=True,
                                  blank=False,
                                  verbose_name=_('Организация для нумерации'),
                                  on_delete=CUSTOM_CASCADE)
    number = models.IntegerField(default=0,
                                 verbose_name=_('Числовой инкрементальный номер'))
    number_formatted = models.CharField(default='',
                                        verbose_name=_('Строковый номер с префиксом'),
                                        max_length=31,
                                        db_index=True)

    def __str__(self):
        return self.number_formatted

    def save(self, *args, **kwargs):

        with transaction.atomic():
            for_lock = self.__class__.objects.filter(org_admin=self.org_admin).select_for_update(nowait=False)
            max_number = for_lock.aggregate(number=models.Max('number'))
            numb = max_number['number']
            if not numb:
                numb = 0
            self.number = numb + 1

            prefix = ''
            try:
                config = self.org_admin.help_desk_config
            except ObjectDoesNotExist:
                pass
            else:
                if config.ticket_prefix.strip() != '':
                    prefix = config.ticket_prefix + '-'

            self.number_formatted = prefix + "{:05d}".format(self.number)

            super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Номер тикета')
        verbose_name_plural = _('Номеры тикета')


class HelpDeskTicketCategoryModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'contractor', 'created_at', 'mentions', 'ct', ]

    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='ticket_categories',
        verbose_name=_('Организация')
    )

    class Meta:
        verbose_name = _('Категория тикета')
        verbose_name_plural = _('Категории тикета')

    @classmethod
    def search_input(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.TicketCategoryCreateSerializer
        elif action in ('update', 'partial_update'):
            return serializers.TicketCategoryUpdateSerializer
        elif action == 'retrieve':
            return serializers.TicketCategoryDetailSerializer
        else:
            return serializers.HelpDeskTicketCategorySerializer

    @classmethod
    def is_enum(cls):
        return False

    @classmethod
    def get_queryset(cls, request=None):
        from .utils import get_help_desk_admin_manager_contractors
        from users.utils import get_tree_departments_related_organizations
        qs = cls.objects.filter(is_active=True)
        if request:
            permission_contractors_id = get_help_desk_admin_manager_contractors(request.user.profile)
            if permission_contractors_id:
                tree_permission_contractors_id = get_tree_departments_related_organizations(permission_contractors_id)
                contractor_id = request.query_params.get('contractor')
                if contractor_id:
                    if uuid.UUID(contractor_id) in tree_permission_contractors_id:
                        contractors_id = get_tree_departments_related_organizations((contractor_id,))
                        qs = qs.filter(
                            Q(contractor__isnull=True) | Q(contractor_id__in=contractors_id)).annotate(
                            contractor_order=Case(
                                When(contractor_id=contractor_id, then=Value(0)),
                                default=Value(1),
                                output_field=IntegerField(),
                            )
                        ).order_by('contractor_order', 'sort', 'name')
                    else:
                        return qs.none()
                else:
                    qs = qs.filter(
                        Q(contractor__isnull=True) | Q(contractor_id__in=tree_permission_contractors_id)
                    ).order_by('sort', 'name')
            else:
                return qs.none()
        return qs

    def get_update_permission(self, request) -> bool:
        contractor = self.contractor
        if not contractor:
            return False
        from users.utils import get_ancestor_departments_related_organizations
        contractors_id = get_ancestor_departments_related_organizations((contractor.pk,), include_self=True)
        permission_contractors_id = set(
            contractors_where_user_has_permission(request.user.profile.pk, 'help_desk_admin', None)
        )
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

    def get_detail_permission(self, request) -> bool:
        user = request.user.profile
        contractor = self.contractor
        if not contractor:
            return True
        from users.utils import get_tree_departments_related_organizations
        from .utils import get_help_desk_admin_manager_contractors
        contractors_id = get_tree_departments_related_organizations((contractor.pk,))
        permission_contractors_id = set(get_help_desk_admin_manager_contractors(user))
        if contractors_id.isdisjoint(permission_contractors_id):
            return False
        else:
            return True

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


class HelpDeskTicketStatusModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'color', 'created_at', 'mentions', 'ct', ]

    color = common_fields.CustomCharField(
        null=False,
        default='default',
        blank=True,
        max_length=20,
        verbose_name=_('Цвет'),
    )

    class Meta:
        verbose_name = _('Статус тикета')
        verbose_name_plural = _('Статусы тикета')

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import HelpDeskTicketStatusSerializer
        return HelpDeskTicketStatusSerializer


class HelpDeskTicketPriorityModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    meta_exclude_fields = ['author', 'name', 'code', 'created_at', 'mentions', 'ct', ]

    class Meta:
        verbose_name = _('Приоритет тикета')
        verbose_name_plural = _('Приоритеты тикета')


class HelpDeskTicketVisorsModel(common_models.BaseAbstractModel):
    ticket = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='visors_through',
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='visors_through',
    )

    class Meta:
        verbose_name = _('Наблюдатель тикета')
        verbose_name_plural = _('Наблюдатели тикета')
        unique_together = (('ticket', 'user'),)


class HelpDeskTicketMembersModel(common_models.BaseAbstractModel):
    ticket = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='ticket_members_through',
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='ticket_members_through',
    )

    class Meta:
        verbose_name = _('Участник обращения')
        verbose_name_plural = _('Участники обращения')
        unique_together = (('ticket', 'user'),)


class MessageTicketThroughModel(common_models.BaseAbstractModel):
    ticket = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('Тикет'),
        related_name='message_ticket_through',
    )
    message = common_fields.CustomForeignKey(
        to='help_desk.ContactPersonMessageModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name=_('сообщение'),
        related_name='message_ticket_through',
    )

    class Meta:
        verbose_name = _('Сообщение тикета')
        verbose_name_plural = _('Сообщения тикета')
        unique_together = (('ticket', 'message',),)


class HelpDeskWorkLogModel(common_models.BaseModel):
    meta_exclude_fields = ['author', 'created_at', 'edited', 'is_current', 'duration', 'mentions', 'ct']
    field_verbose_names = {
        'ticket': _('Обращение'),
    }

    tracker = FieldTracker(
        fields=(
            'user',
            'description',
            'date',
            'duration',
        )
    )

    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        related_name='work_logs',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Пользователь')
    )
    ticket = common_fields.CustomForeignKey(
        to='help_desk.HelpDeskTicketModel',
        null=True,
        blank=False,
        related_name='work_logs',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Тикет')
    )
    meeting_section = common_fields.CustomForeignKey(
        to='meetings.MeetingSectionModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='help_desk_work_logs',
        verbose_name=_('Сессия собрания'),
    )
    description = common_fields.CustomCharField(
        max_length=1024,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание работы'),
    )
    finished_date = common_fields.CustomDateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    date = common_fields.CustomDateField(
        null=False,
        blank=True,
        default=timezone.localdate,
        verbose_name=_('Дата'),
    )
    duration = common_fields.CustomPositiveIntegerField(
        null=False,
        default=0,
        blank=True,
        verbose_name=_('Продолжительность, сек'),
        help_text='в секундах'
    )
    hours = common_fields.CustomDecimalField(
        default=0,
        max_digits=4,
        decimal_places=2,
        verbose_name=_('Затраченные часы'),
        validators=(MinValueValidator(0, message=_('The value can only be positive or 0')),)
    )
    is_current = common_fields.CustomBooleanField(
        default=True,
    )
    is_result = common_fields.CustomBooleanField(
        null=False,
        default=False,
        verbose_name=_('Не брать в зачёт')
    )
    edited = common_fields.CustomBooleanField(
        default=False,
        verbose_name=_('Отредактировано')
    )

    class Meta:
        verbose_name = _('Трудозатраты')
        verbose_name_plural = _('Трудозатраты')

    def build_register_entry(self, created: bool) -> None:
        if not created:
            AccumulationRegister.objects.filter(registrar_row_uuid=self.pk).delete()
        if self.is_active:
            hours_measure_unit = MeasureUnitModel.objects.get(code='hours')
            maintenance_work_type = TaskWorkTypeModel.objects.get(code='maintenance')
            AccumulationRegister.objects.create(
                calc_object=self.ticket.customer_card,
                organization=self.ticket.customer_card.org_admin,
                doc_fact=self.ticket,
                registrar=self.ticket,
                section_id='work_costs',
                base_measure_unit=hours_measure_unit,
                measure_unit=hours_measure_unit,
                work_type=maintenance_work_type,
                quantity_fact=self.hours,
                amount_fact=self.hours * 10000,  # TODO потом изменить логику расчета amount
                period=timezone.make_aware(
                    datetime.datetime.combine(self.date, datetime.time.min),
                    timezone.utc
                ),
                registrar_row_uuid=self.pk,
                user=self.user,
                description=self.description,
            )
        if self.ticket.analytics_key and self.ticket.analytics_key.customer_contract:
            transaction.on_commit(lambda: self.ticket.analytics_key.customer_contract.recalculate_hours_fact())

    def save(self, *args, **kwargs):
        created = self.pk is None
        duration_value = self.duration if self.duration is not None else 0
        hours_value = (Decimal(duration_value) / Decimal('3600')).quantize(Decimal('0.01'), rounding=ROUND_UP)
        self.hours = hours_value
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            update_fields_set = set(update_fields)
            update_fields_set.add('hours')
            kwargs['update_fields'] = tuple(sorted(update_fields_set))

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.build_register_entry(created=created)

        if self.ticket_id:
            transaction.on_commit(
                lambda: self._recalculate_ticket_duration(self.ticket_id)
            )

    @property
    def ticket_customer_card(self):
        ticket = self.ticket
        if ticket:
            return ticket.customer_card
        else:
            return None

    @classmethod
    def get_report_annotations(cls, request, requested_computed):
        """Возвращает SQL-аннотации для отчётов.

        Поддерживаемое вычисляемое поле:
        - work_duration: duration (секунды) как IntegerField для форматирования
        """
        from django.db.models import F, IntegerField, ExpressionWrapper

        annotations = {}
        names = set(requested_computed or [])
        if 'work_duration' in names:
            # Используем duration напрямую (уже в секундах)
            annotations['work_duration'] = ExpressionWrapper(
                F('duration'),
                output_field=IntegerField()
            )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        return [
            {
                "name": "work_duration",
                "type": "DurationField",
                "verbose_name": _("Трудозатраты"),
            }
        ]

    @staticmethod
    def humanize_duration(duration: int):
        duration_min = duration // 60
        duration_str = f"{duration_min} мин"
        duration_remainder = duration % 60
        if duration_remainder:
            duration_str = duration_str + f" {duration_remainder} сек"
        return duration_str

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        if self.is_current:
            return
        related_object_id = self.ticket.pk
        object_property_id = 'help_desk_ticket__work_log'
        obj_user = self.user
        if obj_user:
            user_full_name = obj_user.full_name
        else:
            user_full_name = ''
        after = f'<li>Описание: {self.description} </li>' \
                f'<li>Пользователь: {user_full_name} \n</li>' \
                f'<li>Продолжительность: {self.humanize_duration(self.duration)} \n</li>' \
                f'<li>Дата: {self.date.strftime("%d.%m.%Y")}</li>'
        if created:
            change_history_utils.create_add_m2m(
                related_object_id, action_date, object_property_id, after, [self.pk, ]
            )
        elif deleted:
            change_history_utils.create_delete_m2m(
                related_object_id, action_date, object_property_id, after, [self.pk, ]
            )
        else:
            before_description = changed_fields.get('description')
            if not before_description:
                before_description = self.description
            before_duration = changed_fields.get('duration')
            if not before_duration:
                before_duration = self.duration
            before_date = changed_fields.get('date')
            if not before_date:
                before_date = self.date
            before_user_id = changed_fields.get('user_id')
            if before_user_id:
                before_user = ProfileModel.objects.get(pk=before_user_id)
            else:
                before_user = self.user
            before = f"<li>Описание: {before_description} \n</li>" \
                     f"<li>Пользователь: {before_user.full_name} \n</li>" \
                     f"<li>Продолжительность: {self.humanize_duration(before_duration)} \n</li>" \
                     f"<li>Дата: {before_date.strftime('%d.%m.%Y')}</li>"
            change_history_utils.create_update_m2m(
                related_object_id, action_date, object_property_id, before, after, [self.pk, ]
            )

    def delete(self, *args, **kwargs):
        AccumulationRegister.objects.filter(registrar_row_uuid=self.pk).delete()
        ticket = self.ticket
        super().delete(*args, **kwargs)

        if ticket:
            transaction.on_commit(
                lambda: self._recalculate_ticket_duration(ticket.pk)
            )
            if ticket.analytics_key and ticket.analytics_key.customer_contract:
                transaction.on_commit(
                    lambda: ticket.analytics_key.customer_contract.recalculate_hours_fact()
                )

    @staticmethod
    def _recalculate_ticket_duration(ticket_id):
        """Пересчитывает duration тикета как сумму всех завершенных work_logs (is_current=False)"""
        total_duration = HelpDeskWorkLogModel.objects.filter(
            ticket_id=ticket_id,
            is_active=True,
            is_current=False
        ).aggregate(
            total=Sum('duration')
        )['total'] or 0

        HelpDeskTicketModel.objects.filter(pk=ticket_id).update(duration=total_duration)

    def get_update_permission(self, request) -> bool:
        user = request.user.profile
        if self.is_current:
            return False
        if self.user == user:
            return True
        return self.ticket.edit_work_log_user_permission(request)


class HelpDeskCostModel(common_models.BaseModel):
    """Материальные траты"""

    tracker = FieldTracker(
        fields=(
            'goods_id',
            'quantity',
            'amount',
            'comment',
            'period',
        )
    )

    owner = common_fields.CustomForeignKey(
        to='HelpDeskTicketModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='help_desk_costs',
        verbose_name=_('Обращение'),
    )

    goods = common_fields.CustomForeignKey(
        to='catalogs.NomenclatureModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='help_desk_costs',
        verbose_name=_('Товар')
    )

    name = common_fields.CustomCharField(
        verbose_name=_('Название'),
        max_length=255,
        null=False,
        default='',
        blank=True,
    )
    name_short = common_fields.CustomCharField(
        max_length=127,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Краткое наименование'),
    )
    article_number = common_fields.CustomCharField(
        max_length=255,
        null=True,
        blank=True,
        default='',
        verbose_name=_('Артикул')
    )
    base_measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_("Базовая ед. изм."),
        on_delete=CUSTOM_PROTECT,
        related_name='help_desk_costs_base_measure_unit',
    )

    quantity = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=False,
        blank=False,
        default=0,
        verbose_name=_('Количество'),
    )
    amount = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=False,
        default=0,
        verbose_name=_('Сумма')
    )

    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_("Единица измерения"),
        on_delete=CUSTOM_PROTECT,
        related_name='help_desk_costs_measure_unit',
    )

    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )

    period = common_fields.CustomDateField(
        null=False,
        default=timezone.localdate,
        verbose_name=_('Период')
    )

    class Meta:
        verbose_name = _('Материальные затраты')
        verbose_name_plural = _('Материальные затраты')
        ordering = ('created_at',)

    def track_fields(self, changed_fields: dict, action_date: datetime.datetime, created: bool = False,
                     deleted: bool = False):
        related_object_id = self.owner.pk
        object_property_id = 'help_desk_ticket__costs'
        try:
            after_period = self.period.strftime("%d.%m.%Y")
        except AttributeError:
            after_period = ''
        after = f'<li>Номенклатура: {self.goods} </li>' \
                f'<li>Количество: {self.quantity} \n</li>' \
                f'<li>Период: {after_period}</li>' \
                f'<li>Комментарий: {self.comment}</li>'
        if created:
            change_history_utils.create_add_m2m(
                related_object_id, action_date, object_property_id, after, [self.pk, ]
            )
            return
        if deleted:
            change_history_utils.create_delete_m2m(
                related_object_id, action_date, object_property_id, after, [self.pk, ]
            )
            return
        if 'before_comment' in changed_fields:
            before_comment = changed_fields.get('comment')
        else:
            before_comment = self.comment
        if 'period' in changed_fields:
            try:
                before_period = changed_fields.get('period').strftime("%d.%m.%Y")
            except AttributeError:
                before_period = ''
        else:
            before_period = after_period
        if 'goods_id' in changed_fields:
            before_goods_id = changed_fields.get('goods_id')
            if before_goods_id:
                try:
                    before_goods = NomenclatureModel.objects.get(pk=before_goods_id)
                except (ObjectDoesNotExist, ValidationError):
                    before_goods = None
            else:
                before_goods = None
        else:
            before_goods = self.goods
        if 'quantity' in changed_fields:
            before_quantity = changed_fields.get('quantity')
        else:
            before_quantity = self.quantity

        before = f'<li>Номенклатура: {before_goods} </li>' \
                 f'<li>Количество: {before_quantity} \n</li>' \
                 f'<li>Период: {before_period}</li>' \
                 f'<li>Комментарий: {before_comment}</li>'
        change_history_utils.create_update_m2m(
            related_object_id, action_date, object_property_id, before, after, [self.pk, ]
        )

    def save(self, *args, **kwargs):
        created = self.pk is None
        with transaction.atomic():
            goods = self.goods
            self.name = goods.name
            self.name_short = goods.name_short
            self.article_number = goods.article_number
            self.base_measure_unit = goods.base_measure_unit
            self.measure_unit = goods.base_measure_unit
            super().save(*args, **kwargs)
            if not created:
                AccumulationRegister.objects.filter(registrar=self).update(is_active=False)
                if not self.is_active:
                    return
            AccumulationRegister.objects.create(
                calc_object=self.owner.customer_card,
                organization=self.owner.customer_card.org_admin,
                doc_fact=self.owner,
                registrar=self,
                stuff=self.goods,
                name=self.name,
                name_short=self.name_short,
                article_number=self.article_number,
                base_measure_unit=self.base_measure_unit,
                quantity_fact=self.quantity,
                amount_fact=self.amount,
                measure_unit=self.measure_unit,
                period=self.period,
            )

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.HelpDeskCostCreateSerializer
        elif action in ('update', 'partial_update',):
            return serializers.HelpDeskCostUpdateSerializer
        elif action == 'retrieve':
            return serializers.HelpDeskCostDetailSerializer
        else:
            return serializers.HelpDeskCostListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(is_active=True)
        user = request.user.profile
        help_desk_admins = contractors_where_user_has_permission(user.pk, 'help_desk_admin', None)
        help_desk_managers = contractors_where_user_has_permission(user.pk, 'help_desk_manager', None)
        qs = qs.filter(
            Q(owner__customer_card__org_admin__in=help_desk_admins) |
            Q(owner__customer_card__org_admin__in=help_desk_managers, owner__specialist=user)
        )
        owner_id = request.query_params.get('owner')
        if owner_id:
            qs = qs.filter(owner_id=owner_id)
        return qs

    def get_update_permission(self, request) -> bool:
        return self.owner.get_update_permission(request)

    def get_detail_permission(self, request) -> bool:
        return self.owner.get_detail_permission(request)

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


class AsteriskCallRecord(models.Model):
    call_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="ID звонка",
    )
    call_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Дата звонка",
    )

    manager_ext = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Внутренний номер менеджера",
    )
    client_number = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Номер клиента",
    )
    duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Длительность, сек",
    )

    src = models.CharField(max_length=64, null=True, blank=True)
    dst = models.CharField(max_length=64, null=True, blank=True)
    cnum = models.CharField(max_length=64, null=True, blank=True)
    dstchannel = models.CharField(max_length=255, null=True, blank=True)
    lastapp = models.CharField(max_length=128, null=True, blank=True)
    lastdata = models.TextField(null=True, blank=True)
    dcontext = models.CharField(max_length=128, null=True, blank=True)
    recordingfile = models.CharField(max_length=512, null=True, blank=True)

    raw_payload = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Сырой payload из RabbitMQ",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Запись звонка из RabbitMQ"
        verbose_name_plural = "Записи звонков из RabbitMQ"
        ordering = ("-call_date", "-id")

    def __str__(self):
        return f"{self.call_id} | {self.client_number or '-'} -> {self.manager_ext or '-'}"


