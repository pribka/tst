from django.db import models
from django.db.models import Q, Exists, OuterRef, Subquery
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from common import models as common_models
from common import fields as common_fields
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT, CUSTOM_SET_NULL, URLS


class AccumulationRegister(common_models.BaseAbstractModel):
    meta_exclude_fields = ['author', 'created_at', 'mentions', 'ct',
    'data_source', 'section', 'stuff', 'name_short', 'name', 'article_number', 
    'base_measure_unit', 'measure_unit',
    'registrar', 'registrar_row_uuid', 'work_type', 'work_type_str',
    'meeting_section', 'comment', 'amount_fact',
    ]
    """Регистр накопления"""
    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='accum_registers',
        verbose_name=_('Организация'),
    )
    calc_object = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='accum_registers_calc_obj',
        verbose_name=_('Объект калькуляции')
    )

    doc_fact = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='accum_registers_rel_obj',
        verbose_name=_('Документ факта')
    )
    registrar = common_fields.CustomForeignKey(
        to='common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='accum_registers_registrar',
        verbose_name=_('Регистратор')
    )

    # Вспомогательные поля
    data_source = common_fields.CustomForeignKey(
        to='RegistrarDataSourceModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=True,
        default='web',
        related_name='accum_registers_data_source',
        verbose_name=_('Источник данных')
    )

    section = common_fields.CustomForeignKey(
        to='RegistrarSectionModel',
        to_field='code',
        on_delete=CUSTOM_PROTECT,
        null=False,
        blank=True,
        default='stuff',
        related_name='accum_registers_section',
        verbose_name=_('Раздел')
    )

    stuff = common_fields.CustomForeignKey(
        to='catalogs.GoodsModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='accum_registers_stuff',
        verbose_name=_('Материал')
    )
    # Поля материала
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
        related_name='accum_registers_base_measure_unit',
    )
    work_type = common_fields.CustomForeignKey(
        to='common.BaseCatalog',
        null=True,
        blank=True,
        verbose_name=_('Вид работ'),
        on_delete=CUSTOM_SET_NULL,
        related_name='accum_registers_work_type',
    )
    work_type_str = common_fields.CustomCharField(
        max_length=255,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Вид работ')
    )

    quantity_fact = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_('Количество факт'),
    )
    amount_fact = common_fields.CustomDecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Сумма факт')
    )

    measure_unit = common_fields.CustomForeignKey(
        to='catalogs.MeasureUnitModel',
        null=True,
        blank=True,
        verbose_name=_("Единица измерения"),
        on_delete=CUSTOM_PROTECT,
        related_name='accum_registers_measure_unit',
    )

    comment = common_fields.CustomCharField(
        max_length=1023,
        null=False,
        default='',
        blank=True,
        verbose_name=_('Комментарий')
    )
    description = common_fields.CustomCharField(
        max_length=4096,
        null=False,
        blank=True,
        default='',
        verbose_name=_('Описание'),
    )

    period = common_fields.CustomDateTimeField(
        null=False,
        default=timezone.now,
        verbose_name=_('Период')
    )

    registrar_row_uuid = models.UUIDField(
        verbose_name=_('Строковый идентификатор строки регистратора'),
        null=True,
        blank=True,
        db_index=True,
    )

    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        related_name='accum_registers',
        verbose_name=_('Пользователь'),
        help_text=_('Сотрудник, выполнивший работы и понёсший трудозатраты'),
    )

    @classmethod
    def get_report_annotations(cls, request, requested_computed):
        """Возвращает SQL-аннотации для отчётов."""
        from django.db.models import Case, When, Value, CharField, F, IntegerField, Func
        from django.db.models.functions import Cast, Concat, Coalesce, TruncDate
        from django.contrib.contenttypes.models import ContentType
        from django.apps import apps

        annotations = {}
        names = set(requested_computed or [])

        if 'report_day' in names:
            annotations['report_day'] = TruncDate('period')

        if 'quantity_fact_duration' in names:
            # quantity_fact хранится в часах, для DurationField ожидаем секунды (IntegerField)
            annotations['quantity_fact_duration'] = Cast(
                F('quantity_fact') * Value(3600),
                IntegerField(),
            )

        if 'root_organization' in names:
            from common.catalogs.models import ContractorRelationModel

            organization_pk_field = cls._meta.get_field('organization').target_field
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

        if {'doc_fact_type', 'doc_fact_link'} & names:
            # Получаем ContentType ID и модели для Task и HelpDeskTicket
            task_model = apps.get_model('tasks', 'TaskModel')
            ticket_model = apps.get_model('help_desk', 'HelpDeskTicketModel')

            task_ct = ContentType.objects.get_for_model(task_model)
            ticket_ct = ContentType.objects.get_for_model(ticket_model)

        if 'doc_fact_type' in names:
            annotations['doc_fact_type'] = Case(
                When(doc_fact__ct_id=task_ct.id, then=Value(str(task_model._meta.verbose_name_plural))),
                When(doc_fact__ct_id=ticket_ct.id, then=Value(str(ticket_model._meta.verbose_name_plural))),
                default=Value('Неизвестно'),
                output_field=CharField()
            )

        if 'doc_fact_link' in names:
            # Ссылка на документ факта (TaskModel или HelpDeskTicketModel)
            task_base_url = URLS['tasks']
            task_url_expr = Concat(
                Value(task_base_url),
                Value('?task='),
                Cast(F('doc_fact_id'), models.CharField()),
            )

            ticket_base_url = URLS['helpdesk_tickets']
            ticket_url_expr = Concat(
                Value(ticket_base_url),
                Value('?ticketView='),
                Cast(F('doc_fact_id'), CharField()),
            )

            # repr для задачи — номер + название (TaskModel.counter + TaskModel.name)
            task_counter_subquery = task_model.objects.filter(
                pk=OuterRef('doc_fact_id')
            ).values('counter')[:1]
            task_name_subquery = task_model.objects.filter(
                pk=OuterRef('doc_fact_id')
            ).values('name')[:1]
            task_repr_expr = Concat(
                Coalesce(Subquery(task_counter_subquery, output_field=CharField()), Value('')),
                Value(' '),
                Coalesce(Subquery(task_name_subquery, output_field=CharField()), Value('')),
                output_field=CharField(),
            )

            # repr для тикета — номер + название (HelpDeskTicketModel.number + HelpDeskTicketModel.name)
            from help_desk.models import HelpDeskTicketModel

            ticket_number_subquery = HelpDeskTicketModel.objects.filter(
                pk=OuterRef('doc_fact_id')
            ).values('number')[:1]
            ticket_name_subquery = HelpDeskTicketModel.objects.filter(
                pk=OuterRef('doc_fact_id')
            ).values('name')[:1]
            ticket_repr_expr = Concat(
                Coalesce(Subquery(ticket_number_subquery, output_field=CharField()), Value('')),
                Value(' '),
                Coalesce(Subquery(ticket_name_subquery, output_field=CharField()), Value('')),
                output_field=CharField(),
            )

            annotations['doc_fact_link'] = Case(
                When(
                    doc_fact__ct_id=task_ct.id,
                    then=Func(
                        Value('repr'),
                        task_repr_expr,
                        Value('url'),
                        task_url_expr,
                        function='jsonb_build_object',
                        output_field=models.JSONField(),
                    ),
                ),
                When(
                    doc_fact__ct_id=ticket_ct.id,
                    then=Func(
                        Value('repr'),
                        ticket_repr_expr,
                        Value('url'),
                        ticket_url_expr,
                        function='jsonb_build_object',
                        output_field=models.JSONField(),
                    ),
                ),
                default=Value(None, output_field=models.JSONField()),
                output_field=models.JSONField(),
            )

        if 'calc_object_link' in names:
            workgroup_model = apps.get_model('workgroups', 'WorkgroupModel')
            customer_card_model = apps.get_model('help_desk', 'CustomerCardModel')

            workgroup_ct = ContentType.objects.get_for_model(workgroup_model)
            customer_card_ct = ContentType.objects.get_for_model(customer_card_model)

            project_base_url = URLS['projects']
            project_url_expr = Concat(
                Value(project_base_url),
                Value('?viewProject='),
                Cast(F('calc_object_id'), CharField()),
            )

            customer_cards_base_url = URLS['helpdesk_clients']
            customer_card_url_expr = Concat(
                Value(customer_cards_base_url),
                Value('?client='),
                Cast(F('calc_object_id'), CharField()),
            )

            workgroup_name_subquery = workgroup_model.objects.filter(
                pk=OuterRef('calc_object_id')
            ).values('name')[:1]
            customer_card_name_subquery = customer_card_model.objects.filter(
                pk=OuterRef('calc_object_id')
            ).values('name')[:1]

            annotations['calc_object_link'] = Case(
                When(
                    calc_object__ct_id=workgroup_ct.id,
                    then=Func(
                        Value('repr'),
                        Coalesce(Subquery(workgroup_name_subquery, output_field=CharField()), Value('')),
                        Value('url'),
                        project_url_expr,
                        function='jsonb_build_object',
                        output_field=models.JSONField(),
                    ),
                ),
                When(
                    calc_object__ct_id=customer_card_ct.id,
                    then=Func(
                        Value('repr'),
                        Coalesce(Subquery(customer_card_name_subquery, output_field=CharField()), Value('')),
                        Value('url'),
                        customer_card_url_expr,
                        function='jsonb_build_object',
                        output_field=models.JSONField(),
                    ),
                ),
                default=Value(None, output_field=models.JSONField()),
                output_field=models.JSONField(),
            )

        return annotations

    @classmethod
    def get_report_computed_fields_meta(cls):
        """Возвращает метаданные вычисляемых полей для отчётов."""
        from django.apps import apps
        
        # Получаем verbose_name_plural для моделей
        task_model = apps.get_model('tasks', 'TaskModel')
        ticket_model = apps.get_model('help_desk', 'HelpDeskTicketModel')
        
        return [
            {
                "name": "report_day",
                "type": "DateField",
                "verbose_name": _("Дата отчета"),
                "date_axis": True,
                "axis_granularity": "day",
                "axis_freq": "D",
                "period_filter": {
                    "start_field": "period",
                    "end_field": "period",
                },
            },
            {
                "name": "quantity_fact_duration",
                "type": "DurationField",
                "verbose_name": _("Количество факт, чч:мм:сс"),
            },
            {
                "name": "doc_fact_type",
                "type": "CharField",
                "verbose_name": _("Тип документа факта"),
                "choices": [
                    [str(task_model._meta.verbose_name_plural), str(task_model._meta.verbose_name_plural)],
                    [str(ticket_model._meta.verbose_name_plural), str(ticket_model._meta.verbose_name_plural)],
                ],
            },
            {
                "name": "doc_fact_link",
                "type": "JSONField",
                "verbose_name": _("Ссылка на документ факта"),
            },
            {
                "name": "calc_object_link",
                "type": "JSONField",
                "verbose_name": _("Ссылка на объект калькуляции"),
            },
            {
                "name": "root_organization",
                "type": "ForeignKey",
                "related_model": "catalogs.ContractorModel",
                "verbose_name": _("Головная организация"),
            },
        ]

    @classmethod
    def filter_by_permissions(cls, qs, request):
        """Фильтрует queryset AccumulationRegister по правам доступа к doc_fact."""
       
        task_model = apps.get_model('tasks', 'TaskModel')
        ticket_model = apps.get_model('help_desk', 'HelpDeskTicketModel')
        
        task_ct = ContentType.objects.get_for_model(task_model)
        ticket_ct = ContentType.objects.get_for_model(ticket_model)
        
        ticket_queryset_params = {'view_type': 'contractor'}
        allowed_tickets_qs = ticket_model.get_queryset(request, ticket_queryset_params)
        ticket_permission_subquery = allowed_tickets_qs.filter(
            pk=OuterRef('doc_fact_id')
        )
        
        # Для задач получаем ID через отдельный запрос
        # Это необходимо, так как filter_by_permissions для TaskModel использует extra()
        # и временные таблицы, которые не работают в подзапросах
        allowed_task_ids = list(task_model.get_queryset(request).values_list('pk', flat=True))
        
        task_qs = qs.filter(doc_fact__ct_id=task_ct.id)
        ticket_qs = qs.filter(doc_fact__ct_id=ticket_ct.id)
        
        if allowed_task_ids:
            task_qs = task_qs.filter(doc_fact_id__in=allowed_task_ids)
        else:
            task_qs = task_qs.none()
        
        ticket_qs = ticket_qs.annotate(
            has_ticket_permission=Exists(ticket_permission_subquery)
        ).filter(has_ticket_permission=True)

        # task_qs и ticket_qs взаимоисключающие по doc_fact__ct_id, DISTINCT лишний.
        return task_qs | ticket_qs

    @classmethod
    def get_queryset(cls, request=None, queryset_params=None):
        """Возвращает queryset с фильтрацией по правам доступа для трудозатрат."""
        qs = cls.objects.filter(is_active=True)
        
        if not request or not queryset_params:
            return qs
        
        view_type = queryset_params.get('view_type')
        if view_type == 'work_costs':
            qs = qs.filter(section_id='work_costs')
            qs = cls.filter_by_permissions(qs, request)

        return qs

    class Meta:
        verbose_name = _('Регистр накопления')
        verbose_name_plural = _('Регистры накопления')


class RegistrarDataSourceModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """Источники данных регистра накопления"""
    class Meta:
        verbose_name = _('Источник данных')
        verbose_name_plural = _('Источники данных')


class RegistrarSectionModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """Разделы регистра накопления"""
    class Meta:
        verbose_name = _('Раздел')
        verbose_name_plural = _('Разделы')

