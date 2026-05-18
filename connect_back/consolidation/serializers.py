from django.db import transaction
from django.db.models import Prefetch
from django_q.tasks import async_task
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers

from accounting_reports.serializers import \
    IpfProposalConsolidationExtraModelCreateSerializer
from common.catalogs.models import ContractorModel
from common.catalogs.serializers import ContractorModelByIdSerializer
from common.current_profile.middleware import get_current_authenticated_profile
from common.models import File
from common.utils import get_serialized_attachments
from users.serializers import AppUserSerializer
from contractor_permissions.utils import contractors_where_user_has_permission

from . import generating, models, notifications, utils

REPORT_TYPES = {
            'f2go': 'file_upload',
            'f2go_with_verification_act': 'file_upload',
            'ipf_proposal': 'ipf_proposal',
            'change_calculation': 'change_calculation',
            'risk_map_with_personal_reception': 'file_upload',
        }


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'next_creation_date',
            'next_dead_line',
            'next_end',
            'next_start',
            'repeat_period',
            'repeat_to',
        )


class StatusSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    color = serializers.CharField()
    created_at = serializers.DateTimeField()
    name = serializers.CharField()


class ReportFileModelSerializer(serializers.ModelSerializer):
    original_file = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()
    uploaded_by = AppUserSerializer()

    class Meta:
        model = models.ReportFileModel
        fields = (
            'id',
            'is_generated',
            'original_file',
            'pdf_file',
            'upload_date',
            'uploaded_by',
        )

    def get_original_file(self, instance):
        return utils.get_serialized_report_original_file(instance)

    def get_pdf_file(self, instance):
        return utils.get_serialized_report_pdf_file(instance)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        file_type = instance.file_type
        data['code'] = file_type.code
        data['description'] = file_type.description
        data['name'] = file_type.name
        data['widget'] = file_type.widget
        return data


class ConsolidationFileModelSerializer(serializers.ModelSerializer):
    original_file = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()
    file_type = serializers.CharField(source='file_type_id')

    class Meta:
        model = models.ConsolidationFileModel
        fields = (
            'id',
            'file_type',
            'name',
            'original_file',
            'pdf_file',
        )

    def get_original_file(self, instance):
        return utils.get_serialized_consolidation_original_file(instance)

    def get_pdf_file(self, instance):
        return utils.get_serialized_consolidation_pdf_file(instance)


class ReportFormModelSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = models.ReportFormModel
        fields = (
            'id',
            'attachments',
            'code',
            'description',
            'name',
        )

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class ConsolidationModelShortSerializer(serializers.ModelSerializer):
    report_form = ReportFormModelSerializer()
    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'auto_approve',
            'report_form'
        )


class ConsolidationModelRecipientListSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'label'
        )

    def get_label(self, instance):
        return instance.__str__()


class ReportModelDetailSerializer(serializers.ModelSerializer):
    consolidation = ConsolidationModelShortSerializer(source='parent')
    consolidator = AppUserSerializer()
    contractor = ContractorModelByIdSerializer()
    report_files = ReportFileModelSerializer(many=True)
    status = StatusSerializer()

    class Meta:
        model = models.ReportModel
        fields = (
            'id',
            'consolidation',
            'consolidator',
            'contractor',
            'no_inquiries',
            'report_files',
            'sort',
            'status',
            'without_attachments'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        permissive_status_list = self.context.get('permissive_status_list')
        create_consolidation_contractors = self.context.get('create_consolidation_contractors')
        send_report_contractors = self.context.get('send_report_contractors')
        if not permissive_status_list and not create_consolidation_contractors and not send_report_contractors:
            request = self.context.get('request')
            detail_permission = instance.get_detail_permission(request)
            update_permission = instance.get_update_permission(request)
        else:
            if not permissive_status_list or instance.status_id not in permissive_status_list:
                update_permission = False
            else:
                if instance.contractor_id in create_consolidation_contractors or instance.contractor_id in send_report_contractors:
                    update_permission = True
                else:
                    update_permission = False
            if instance.parent.org_administrator_id in create_consolidation_contractors or instance.contractor_id in send_report_contractors:
                detail_permission = True
            else:
                detail_permission = False
        data['file_viewing_is_available'] = detail_permission
        data['update_is_available'] = update_permission
        data['view_is_available'] = detail_permission

        report_type_instance = instance.parent.get_report_form_instance()
        report_type_instance.add_specific_fields_in_report(data, instance)
        is_disabled, message = instance.get_update_is_disabled()
        data['update_is_disabled'] = is_disabled
        data['update_is_disabled_message'] = message
        return data


class ReportModelNotifySerializer(serializers.ModelSerializer):
    consolidator = AppUserSerializer()
    contractor = ContractorModelByIdSerializer()
    status = StatusSerializer()
    str_view = serializers.SerializerMethodField()

    class Meta:
        model = models.ReportModel
        fields = (
            'id',
            'consolidator',
            'contractor',
            'status',
            'str_view',
        )

    def get_str_view(self, instance):
        return instance.__str__()


class ConsolidationModelListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    file_viewing_is_available = serializers.SerializerMethodField()
    org_administrator = ContractorModelByIdSerializer()
    report_form = ReportFormModelSerializer()
    status = StatusSerializer()

    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'author',
            'auto_approve',
            'created_at',
            'dead_line',
            'end',
            'file_viewing_is_available',
            'frontend_route',
            'generate_report_files',
            'is_scheduled',
            'is_template_on',
            'name',
            'next_creation_date',
            'next_dead_line',
            'next_end',
            'next_start',
            'org_administrator',
            'repeat_period',
            'repeat_to',
            'report_form',
            'start',
            'status',
        )

    def get_file_viewing_is_available(self, instance):
        request = self.context.get('request')
        return (instance.get_update_permission(request) and
                instance.consolidation_files.filter(
                is_active=True,
                original_file__isnull=False
                ).exists())


class ConsolidationModelCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    ipf_proposal_extra = IpfProposalConsolidationExtraModelCreateSerializer(
        required=False,
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ContractorModel.objects.filter(is_active=True, )
    )

    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'add_org_administrator_in_members',
            'attachments',
            'auto_approve',
            'dead_line',
            'description',
            'end',
            'generate_report_files',
            'ipf_proposal_extra',
            'is_scheduled',
            'is_template_on',
            'members',
            'name',
            'org_administrator',
            'repeat_period',
            'repeat_to',
            'report_form',
            'start'
        )

    def create(self, validated_data):
        add_org_administrator_in_members = validated_data.get('add_org_administrator_in_members', None)
        attachments = validated_data.pop('attachments', None)
        is_scheduled = validated_data.pop('is_scheduled', None)
        members = validated_data.pop('members', [])
        org_administrator = validated_data.get('org_administrator', None)
        repeat_to = validated_data.pop('repeat_to', None)
        report_form = validated_data.get('report_form', None)
        user = get_current_authenticated_profile()
        if not report_form:
            raise drf_exceptions.ValidationError('Не указана форма отчета.')
        extra_fields = validated_data.pop(f'{report_form.code}_extra', None)
        report_form_info = report_form.report_form_info.get(report_form.code, None)
        if report_form_info:
            files_info = report_form_info.get('files_info', [])
        else:
            files_info = []
        if not report_form_info:
            raise drf_exceptions.ValidationError('Ошибка получения формы отчета.')

        if add_org_administrator_in_members:
            members.append(org_administrator)
        if not members:
            raise drf_exceptions.ValidationError('Список участников пуст.')
        generate_report_files = validated_data.get('generate_report_files', False)

        with transaction.atomic():
            instance = models.ConsolidationModel.objects.create(
                **validated_data
            )
            for member in members:
                models.ConsolidationMemberModel.objects.create(
                            organization=member,
                            consolidation=instance
                        )
                sort = 100 if member == org_administrator else 500
                report = models.ReportModel.objects.create(
                        consolidator=user,
                        contractor=member,
                        parent=instance,
                        report_type_id=REPORT_TYPES[report_form.code],
                        sort=sort,
                        status_id='not_loaded'
                    )
                if files_info:
                    report_files = [
                        models.ReportFileModel.objects.create(
                            file_type_id=file_info.get('code', 'default'),
                            sort=file_info.get('sort', 500),
                        ) for file_info in files_info
                    ]
                    report.report_files.set(report_files)

            if attachments:
                instance.attachments.set(attachments)
            if is_scheduled:
                utils.create_scheduled_consolidation(instance, repeat_to, extra_fields)
            if generate_report_files and report_form.code == 'f2go':
                # generating.generate_reports(instance)
                # Убрал функционал из-за слишком большой нагрузки на сервер и сомнительный результат
                pass
            instance.get_report_form_instance().set_extra_fields(
                consolidation=instance,
                extra_fields=extra_fields
            )
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_new_consolidation_is_create,
                    str(instance.id),
                    str(user.id)
                )
            )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['attachments'] = get_serialized_attachments(instance)
        data['template'] = TemplateSerializer(instance.template).data
        return data


class ConsolidationModelDetailSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    author = AppUserSerializer()
    consolidation_files = ConsolidationFileModelSerializer(many=True)
    consolidator = AppUserSerializer()
    file_viewing_is_available = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    org_administrator = ContractorModelByIdSerializer()
    report_form = ReportFormModelSerializer()
    status = StatusSerializer()
    update_is_available = serializers.SerializerMethodField()

    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'add_org_administrator_in_members',
            'attachments',
            'author',
            'auto_approve',
            'consolidated_at',
            'consolidation_files',
            'consolidator',
            'created_at',
            'dead_line',
            'description',
            'end',
            'file_viewing_is_available',
            'generate_report_files',
            'is_scheduled',
            'is_template_on',
            'members',
            'name',
            'org_administrator',
            'repeat_period',
            'repeat_to',
            'report_form',
            'start',
            'status',
            'update_is_available',
        )

    def get_members(self, instance):
        members = instance.members.filter(
            is_active=True
        ).exclude(
            id=instance.org_administrator.id
        )
        return ContractorModelByIdSerializer(members, many=True).data

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def get_file_viewing_is_available(self, instance):
        request = self.context.get('request')
        return (instance.get_update_permission(request) and
                instance.consolidation_files.filter(
                is_active=True,
                original_file__isnull=False
                ).exists())

    def get_update_is_available(self, instance):
        request = self.context.get('request')
        return instance.get_update_permission(request)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        reports = instance.source_reports.filter(
                is_active=True
            ).select_related(
                'status',
            ).prefetch_related(
                'consolidator',
                'contractor',
                Prefetch(
                    'report_files',
                    queryset=models.ReportFileModel.objects.filter(
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
        if instance.is_scheduled:
            create_consolidation_contractors = tuple()
            send_report_contractors = tuple()
            permissive_status_list = list()
        else:
            permissive_status_list = [
                'new',
                'on_review',
                'rejected',
                'not_loaded']
            if instance.auto_approve:
                permissive_status_list.append('approved')
            user = self.context.get('request').user.profile
            create_consolidation_contractors = contractors_where_user_has_permission(
                user.pk,
                'create_consolidation',
                None
            )
            send_report_contractors = contractors_where_user_has_permission(
                user.pk,
                'send_report',
                None
            )
        data['reports'] = ReportModelDetailSerializer(
            reports,
            many=True,
            context={
                'request': request,
                'create_consolidation_contractors': create_consolidation_contractors,
                'send_report_contractors': send_report_contractors,
                'permissive_status_list': permissive_status_list,
            }
        ).data
        data['summary'] = instance.summary()
        instance.get_report_form_instance().get_extra_fields(instance, data)
        return data


class ConsolidationModelUpdateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )
    ipf_proposal_extra = IpfProposalConsolidationExtraModelCreateSerializer(
        required=False,
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ContractorModel.objects.filter(is_active=True, )
    )

    class Meta:
        model = models.ConsolidationModel
        fields = (
            'id',
            'add_org_administrator_in_members',
            'attachments',
            'auto_approve',
            'dead_line',
            'description',
            'end',
            'generate_report_files',
            'ipf_proposal_extra',
            'is_scheduled',
            'is_template_on',
            'members',
            'name',
            'org_administrator',
            'repeat_period',
            'repeat_to',
            'report_form',
            'start',
        )

    def update(self, instance, validated_data):
        if instance.is_scheduled:
            raise drf_exceptions.ValidationError(
                'Редактирование шаблона запрещено!'
            )
        request = self.context.get('request')
        is_scheduled = validated_data.pop('is_scheduled', None)
        repeat_to = validated_data.pop('repeat_to', None)
        report_form = validated_data.get('report_form', None)
        report_form_has_changed = report_form != instance.report_form
        if report_form_has_changed:
            old_report_form_instance = instance.get_report_form_instance()
        add_org_administrator_in_members = validated_data.get('add_org_administrator_in_members', None)
        attachments = validated_data.pop('attachments', None)
        org_administrator = validated_data.get('org_administrator', None)
        old_auto_approve = instance.auto_approve
        if not instance.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'Редактирование отчета запрещено!'
            )
        if not report_form:
            raise drf_exceptions.ValidationError('Не указана форма отчета.')
        extra_fields = validated_data.pop(f'{report_form.code}_extra', None)
        report_form_info = report_form.report_form_info.get(report_form.code, None)
        if report_form_info:
            files_info = report_form_info.get('files_info', [])
        else:
            files_info = []
        if not report_form_info:
            raise drf_exceptions.ValidationError('Ошибка получения формы отчета.')

        members = validated_data.pop('members', None)
        if members is not None:
            instance_members = ContractorModel.objects.filter(
                consolidations__consolidation=instance
            )

            members_to_delete_ids = [
                member.id
                for member in instance_members
                if member not in members
            ]

            if add_org_administrator_in_members and instance.org_administrator_id in members_to_delete_ids:
                members_to_delete_ids.remove(instance.org_administrator_id)

            new_members = [
                member
                for member in members
                if member not in instance_members
            ]
            if add_org_administrator_in_members and org_administrator not in instance_members:
                new_members.append(org_administrator)
        else:
            members_to_delete_ids = []
            new_members = []
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            user = get_current_authenticated_profile()

            if attachments is not None:
                instance.attachments.set(attachments)
            if is_scheduled:
                utils.create_scheduled_consolidation(instance, repeat_to, extra_fields)
            if members is not None:
                # Удаляем старые по одному объекту для добавления в историю изменений:
                members_to_delete = instance.consolidation_members.filter(
                    organization__id__in=members_to_delete_ids
                )
                for each in members_to_delete:
                    each.delete()
                reports_to_delete = models.ReportModel.objects.filter(
                    is_active=True,
                    parent=instance,
                    contractor__in=members_to_delete_ids
                )
                for report in reports_to_delete:
                    for report_file in report.report_files.all():
                        if report_file.original_file:
                            report_file.original_file.is_orphaned = True
                            report_file.original_file.save(update_fields=('is_orphaned',))
                        if report_file.pdf_file:
                            report_file.pdf_file.is_orphaned = True
                            report_file.pdf_file.save(update_fields=('is_orphaned',))
                    report.is_active = False
                    report.save(update_fields=('is_active',))
                # Добавить новые
                for member in new_members:
                    models.ConsolidationMemberModel.objects.create(
                                organization=member,
                                consolidation=instance
                            )
                    sort = 100 if member == org_administrator else 500
                    report = models.ReportModel.objects.create(
                            consolidator=user,
                            contractor=member,
                            parent=instance,
                            sort=sort,
                            status_id='not_loaded'
                        )
                    if files_info:
                        report_files = [
                            models.ReportFileModel.objects.create(
                                file_type_id=file_info.get('code', 'default'),
                                sort=file_info.get('sort', 500),
                            ) for file_info in files_info
                        ]
                        report.report_files.set(report_files)
            # Присвоим отчетам тип
            instance_reports = models.ReportModel.objects.filter(
                is_active=True,
                parent=instance
            )
            for report in instance_reports:
                report.report_type_id = REPORT_TYPES[report_form.code]
            models.ReportModel.objects.bulk_update(
                instance_reports,
                ('report_type_id',)
            )
            if not old_auto_approve and validated_data.get('auto_approve'):
                report_form_instance = instance.get_report_form_instance()
                for report in instance_reports:
                    if report.status_id != 'approved':
                        try:
                            report_form_instance.before_approve(report)
                        except drf_exceptions.ValidationError:
                            continue
                        else:
                            report.status_id = 'approved'
                            report.save(update_fields=('status_id',))

            # Присвоим консолидации новый статус
            # Если все отчёты имеют статус 'Утвержден' - 'Подготовлена'
            # иначе 'В работе'. Для новой консолидации статус не меняем.
            if instance.status_id != 'new':
                instance_status = 'ready_to_consolidate' if instance.all_reports_is_approved() else 'in_progress'
                instance.status_id = instance_status
                instance.save(update_fields=('status_id',))
            # Если форма отчетности была изменена, нужно создать новые
            # файлы отчетов, перед этим нужно присвоить признак is_orphaned
            # файлам загруженным ранее
            if report_form_has_changed:
                for report in instance_reports:
                    # Присвоим признак is_orphaned загруженным файлам
                    for report_file in report.report_files.all():
                        if report_file.original_file:
                            report_file.original_file.is_orphaned = True
                            report_file.original_file.save(update_fields=('is_orphaned',))
                        if report_file.pdf_file:
                            report_file.pdf_file.is_orphaned = True
                            report_file.pdf_file.save(update_fields=('is_orphaned',))
                    # Удалим файлы из отчёта
                    report.report_files.clear()
                    report.ipf_proposal_reports.clear()
                    # Создадим новые файлы отчёта
                    report_files = [
                        models.ReportFileModel.objects.create(
                            file_type_id=file_info.get('code', 'default'),
                            sort=file_info.get('sort', 500),
                        ) for file_info in files_info
                    ]
                    # Добавим новые файлы в отчёт
                    report.report_files.set(report_files)
                    # Присвоим отчету статус 'Не загружен'
                    report.status_id = 'not_loaded'
                models.ReportModel.objects.bulk_update(
                    instance_reports,
                    ('status_id',)
                )
                # Присвоим консолидации статус 'Новая'
                instance.status_id = 'new'
                instance.save(update_fields=('status_id',))
                # Удалим дополнительные поля предыдущей формы отчетности
                old_report_form_instance.set_extra_fields(
                    consolidation=instance,
                    clear=True
                )
            # Установим значения дополнительных полей
            instance.get_report_form_instance().set_extra_fields(
                consolidation=instance,
                extra_fields=extra_fields
            )
        return instance


class AnalyticReportModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AnalyticReportModel
        fields = (
            'id',
            'name'
        )
