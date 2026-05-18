import json
from io import BytesIO

from django.db import transaction
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers

from common.catalogs.serializers import ContractorModelShortSerializer
from common.models import File
from common.utils import get_serialized_attachments
from consolidation.models import ConsolidationModel
from users.serializers import AppUserSerializer
from common.accounting_catalogs.serializers import BudgetFunctionalGroupModelSerializer, BudgetFunctionalSubgroupModelSerializer, BudgetProgramAdministratorModelSerializer

from . import models, utils


class RationaleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RationaleModel
        fields = (
            'id',
            'rationale',
        )


class AccountingReportStatusModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountingReportStatusModel
        fields = (
            'id',
            'code',
            'name',
            'color',
        )


class AccountingReportTypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountingReportTypeModel
        fields = (
            'id',
            'code',
            'name',
            'widget',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.info:
            info = json.loads(instance.info)
            data['rules'] = info.get('rules', dict())
            data['form'] = info.get('form', dict())
        return data


class AccountingReportSubtypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccountingReportSubtypeModel
        fields = (
            'id',
            'code',
            'name',
        )


class SpecificityStructureModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SpecificityStructureModel
        fields = [
            'id',
            'code',
            'name',
        ]


class ProposalItemModelCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ProposalItemModel
        fields = [
            'id',
            'functional_group',
            'functional_subgroup',
            'budget_program_administrator',
            'program',
            'subprogram',
            'specificity',
            'january',
            'february',
            'march',
            'april',
            'may',
            'june',
            'july',
            'august',
            'september',
            'october',
            'november',
            'december',
            'attachments',
            'rationale',
        ]


class ProposalItemModelDetailSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    budget_program_administrator = BudgetProgramAdministratorModelSerializer()
    functional_group = BudgetFunctionalGroupModelSerializer()
    functional_subgroup = BudgetFunctionalSubgroupModelSerializer()
    specificity = SpecificityStructureModelSerializer()

    class Meta:
        model = models.ProposalItemModel
        fields = [
            'id',
            'functional_group',
            'functional_subgroup',
            'budget_program_administrator',
            'program',
            'subprogram',
            'specificity',
            'january',
            'february',
            'march',
            'april',
            'may',
            'june',
            'july',
            'august',
            'september',
            'october',
            'november',
            'december',
            'attachments',
            'rationale',
        ]

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class ChangeCalculationItemModelDetailSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    budget_program_administrator = BudgetProgramAdministratorModelSerializer()
    functional_group = BudgetFunctionalGroupModelSerializer()
    functional_subgroup = BudgetFunctionalSubgroupModelSerializer()
    specificity = SpecificityStructureModelSerializer()

    class Meta:
        model = models.ChangeCalculationItemModel
        fields = [
            'id',
            'actual_amount',
            'actual_quantity',
            'attachments',
            'budget_program_administrator',
            'functional_group',
            'functional_subgroup',
            'plan_amount',
            'plan_quantity',
            'program',
            'rationale',
            'specificity',
            'subprogram',
        ]

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class AccountingReportBaseModelListSerializer(serializers.ModelSerializer):
    author = AppUserSerializer()
    organization = ContractorModelShortSerializer()
    status = AccountingReportStatusModelSerializer()
    type = AccountingReportTypeModelSerializer()

    class Meta:
        model = models.AccountingReportBaseModel
        fields = [
            'id',
            'author',
            'created_at',
            'organization',
            'status',
            'type',
        ]


class FPCReportModelDetailSerializer(serializers.ModelSerializer):
    organization = ContractorModelShortSerializer()
    proposals = ProposalItemModelDetailSerializer(
        source='proposal_items',
        many=True
    )
    status = AccountingReportStatusModelSerializer()
    subtype = AccountingReportSubtypeModelSerializer()
    type = AccountingReportTypeModelSerializer()

    class Meta:
        model = models.FPCReportModel
        fields = [
            'id',
            'date',
            'number',
            'organization',
            'proposals',
            'responsible_name',
            'responsible_position',
            'status',
            'subtype',
            'type',
        ]


class ChangeCalculationModelDetailSerializer(serializers.ModelSerializer):
    calculations = ChangeCalculationItemModelDetailSerializer(
        source='change_calculation_items',
        many=True
    )
    file_data = serializers.SerializerMethodField()
    organization = ContractorModelShortSerializer()
    pdf_file = serializers.SerializerMethodField()
    status = AccountingReportStatusModelSerializer()
    type = AccountingReportTypeModelSerializer()

    class Meta:
        model = models.ChangeCalculationReportModel
        fields = [
            'id',
            'calculations',
            'end',
            'file_data',
            'is_accumulated',
            'organization',
            'pdf_file',
            'responsible_name',
            'responsible_position',
            'start',
            'status',
            'type'
        ]

    def get_file_data(self, instance):
        file_obj = instance.attachments.filter(
            is_active=True
        ).first()
        with open(file_obj.upload.path, 'rb') as file:
            file_data = BytesIO(file.read())
        budget_program_admin = instance.organization.budget_program_administrator
        return utils.parse_expense_report_from_pdf(file_data, budget_program_admin)

    def get_pdf_file(self, instance):
        attachments = get_serialized_attachments(instance)
        return attachments[0] if attachments else None


class FPCReportModelCreateSerializer(serializers.ModelSerializer):
    proposals = ProposalItemModelCreateSerializer(required=False, many=True)

    class Meta:
        model = models.FPCReportModel
        fields = [
            'id',
            'date',
            'number',
            'organization',
            'proposals',
            'responsible_name',
            'responsible_position',
            'subtype',
            'type',
        ]

    def validate(self, validated_data):
        number = validated_data.get('number')
        organization = validated_data.get('organization')
        report_type = validated_data.get('type')

        number_is_exist = self.Meta.model.objects.filter(
            is_active=True,
            organization=organization,
            type=report_type,
            number=number
        ).exists()
        if number_is_exist:
            error_message = (
                f'Отчёт "{report_type}" с номером "{number}" уже '
                f'зарегистрирован для организации "{organization}"'
            )
            raise drf_exceptions.ValidationError({'error': error_message})
        return validated_data

    def create(self, validated_data):
        proposals = validated_data.pop('proposals')
        if not proposals:
            raise drf_exceptions.ValidationError(
                'В отчёте нет заявок.'
            )

        with transaction.atomic():
            instance = models.FPCReportModel.objects.create(
                **validated_data
            )
            for proposal in proposals:
                attachments = proposal.pop('attachments')
                proposal_obj = models.ProposalItemModel.objects.create(
                    report=instance,
                    **proposal
                )
                if attachments:
                    proposal_obj.attachments.set(attachments)
        return instance


class FPCReportModelUpdateSerializer(serializers.ModelSerializer):
    proposals = ProposalItemModelCreateSerializer(required=False, many=True)

    class Meta:
        model = models.FPCReportModel
        fields = [
            'id',
            'date',
            'number',
            'organization',
            'proposals',
            'responsible_name',
            'responsible_position',
            'subtype',
            'type',
        ]

    def validate(self, validated_data):
        number = validated_data.get('number')
        organization = validated_data.get('organization')
        report_type = validated_data.get('type')

        number_is_exist = self.Meta.model.objects.filter(
            is_active=True,
            organization=organization,
            type=report_type,
            number=number
        ).exclude(pk=self.instance.id).exists()
        if number_is_exist:
            error_message = (
                f'Отчёт "{report_type}" с номером "{number}" уже '
                f'зарегистрирован для организации "{organization}"'
            )
            raise drf_exceptions.ValidationError({'error': error_message})
        if self.instance.organization != organization:
            raise drf_exceptions.ValidationError(
                {
                    'error': 'Изменять организацию отчёта запрещено'
                }
            )
        if self.instance.type != report_type:
            raise drf_exceptions.ValidationError(
                {
                    'error': 'Изменять форму отчёта запрещено'
                }
            )
        return validated_data

    def update(self, instance, validated_data):
        proposals = validated_data.pop('proposals')
        if not proposals:
            raise drf_exceptions.ValidationError(
                'В отчёте нет заявок.'
            )
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            # 1. Удаляем имеющиеся заявки из отчета
            instance.proposal_items.all().delete()

            # 2. Создаем новые заявки
            for proposal in proposals:
                attachments = proposal.pop('attachments')
                proposal_obj = models.ProposalItemModel.objects.create(
                    report=instance,
                    **proposal
                )
                if attachments:
                    proposal_obj.attachments.set(attachments)

        return instance


class FPCReportModelListSerializer(serializers.ModelSerializer):
    organization = ContractorModelShortSerializer()
    status = AccountingReportStatusModelSerializer()
    subtype = AccountingReportSubtypeModelSerializer()
    type = AccountingReportTypeModelSerializer()

    class Meta:
        model = models.FPCReportModel
        fields = [
            'id',
            'date',
            'number',
            'organization',
            'status',
            'subtype',
            'type',
        ]


class ChangeCalculationModelListSerializer(serializers.ModelSerializer):
    organization = ContractorModelShortSerializer()
    status = AccountingReportStatusModelSerializer()
    type = AccountingReportTypeModelSerializer()

    class Meta:
        model = models.ChangeCalculationReportModel
        fields = [
            'id',
            'end',
            'is_accumulated',
            'organization',
            'start',
            'status',
            'type',
        ]


class FPCReportModelWidgetSerializer(serializers.ModelSerializer):
    subtype = AccountingReportSubtypeModelSerializer()

    class Meta:
        model = models.FPCReportModel
        fields = [
            'id',
            'date',
            'number',
            'subtype',
        ]


class ChangeCalculationReportModelWidgetSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ChangeCalculationReportModel
        fields = [
            'id',
            'start',
            'end',
            'is_accumulated',
            'created_at'
        ]


class IpfProposalConsolidationExtraModelDetailSerializer(serializers.ModelSerializer):
    subtype = AccountingReportSubtypeModelSerializer()

    class Meta:
        model = models.IpfProposalConsolidationExtraModel
        fields = [
            'id',
            'date',
            'number',
            'subtype',
        ]


class IpfProposalConsolidationExtraModelCreateSerializer(serializers.ModelSerializer):
    consolidation = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=ConsolidationModel.objects.filter(is_active=True)
    )
    subtype = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.AccountingReportSubtypeModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.IpfProposalConsolidationExtraModel
        fields = [
            'consolidation',
            'date',
            'number',
            'subtype',
        ]


class ChangeCalculationItemModelCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ChangeCalculationItemModel
        fields = [
            'id',
            'functional_group',
            'functional_subgroup',
            'budget_program_administrator',
            'program',
            'subprogram',
            'specificity',
            'rationale',
            'plan_quantity',
            'plan_amount',
            'actual_quantity',
            'actual_amount',
            'attachments',
        ]


class ChangeCalculationModelCreateSerializer(serializers.ModelSerializer):
    calculations = ChangeCalculationItemModelCreateSerializer(required=False, many=True)
    pdf_file = serializers.PrimaryKeyRelatedField(
        many=False,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ChangeCalculationReportModel
        fields = [
            'calculations',
            'end',
            'is_accumulated',
            'organization',
            'pdf_file',
            'responsible_name',
            'responsible_position',
            'start',
            'type',
        ]

    def create(self, validated_data):
        calculations = validated_data.pop('calculations')
        pdf_file = validated_data.pop('pdf_file')
        if not calculations:
            raise drf_exceptions.ValidationError(
                'В отчёте нет расчётов.'
            )

        with transaction.atomic():
            instance = models.ChangeCalculationReportModel.objects.create(
                **validated_data
            )
            for calculation in calculations:
                attachments = calculation.pop('attachments')
                calculation_obj = models.ChangeCalculationItemModel.objects.create(
                    report=instance,
                    **calculation
                )
                if attachments:
                    calculation_obj.attachments.set(attachments)
            if pdf_file:
                instance.attachments.set((pdf_file, ))
        return instance


class ChangeCalculationModelUpdateSerializer(serializers.ModelSerializer):
    calculations = ChangeCalculationItemModelCreateSerializer(required=False, many=True)
    pdf_file = serializers.PrimaryKeyRelatedField(
        many=False,
        required=False,
        queryset=File.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ChangeCalculationReportModel
        fields = [
            'calculations',
            'end',
            'is_accumulated',
            'organization',
            'pdf_file',
            'responsible_name',
            'responsible_position',
            'start',
            'type',
        ]

    def update(self, instance, validated_data):
        calculations = validated_data.pop('calculations')
        pdf_file = validated_data.pop('pdf_file')
        if not calculations:
            raise drf_exceptions.ValidationError(
                'В отчёте нет расчётов.'
            )
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            # 1. Удаляем имеющиеся расчеты из отчета
            instance.change_calculation_items.all().delete()
            # 2. Создаем новые расчеты
            for calculation in calculations:
                attachments = calculation.pop('attachments')
                calculation_obj = models.ChangeCalculationItemModel.objects.create(
                    report=instance,
                    **calculation
                )
                if attachments:
                    calculation_obj.attachments.set(attachments)
            if pdf_file:
                instance.attachments.set((pdf_file, ))
        return instance
