from django.db.models import Q

from common.utils import use_access_groups

from notifications import event_types
from contractor_permissions.models import ContractorPermissionModel
from contractor_permissions.utils import users_that_have_permission_in_contractors


from users.models import ProfileModel


def notify_report_is_approved(report_id, initiator_id):
    from .models import ReportModel

    report = ReportModel.objects.filter(is_active=True, id=report_id).first()
    initiator = ProfileModel.objects.filter(is_active=True, id=initiator_id).first()
    if report and initiator:
        event_type = event_types.ReportHasApprovedEvent()
        recipients = set()
        report_files = report.report_files.all()
        for report_file in report_files:
            recipients.add(report_file.uploaded_by)
        recipients.discard(None)
        event_type.create_notification(recipients=recipients,
                                       initiator=initiator,
                                       subj=report)
    return 'done.'


def notify_report_is_rejected(report_id, initiator_id):
    from .models import ReportModel

    report = ReportModel.objects.filter(is_active=True, id=report_id).first()
    initiator = ProfileModel.objects.filter(is_active=True, id=initiator_id).first()
    if report and initiator:
        event_type = event_types.ReportHasRejectedEvent()
        recipients = set()
        report_files = report.report_files.all()
        for report_file in report_files:
            recipients.add(report_file.uploaded_by)
        recipients.discard(None)
        event_type.create_notification(recipients=recipients,
                                       initiator=initiator,
                                       subj=report)
    return 'done.'


def notify_all_reports_are_uploaded(consolidation_id, initiator_id):
    from .models import ConsolidationModel

    consolidation = ConsolidationModel.objects.filter(is_active=True, id=consolidation_id).first()
    initiator = ProfileModel.objects.filter(is_active=True, id=initiator_id).first()
    if consolidation and initiator:
        event_type = event_types.AllReportsAreUploadedEvent()
        report_form = consolidation.report_form
        if use_access_groups(initiator_id):
            recipients = set(
                users_that_have_permission_in_contractors(
                    (consolidation.org_administrator_id,),
                    'create_consolidation',
                    None,
                )
            )
        else:
            recipients = set(ContractorPermissionModel.objects.filter(
                        Q(aux_conditions=report_form) | Q(aux_conditions__isnull=True),
                        contractor_permission_role__is_active=True,
                        contractor_permission_role__contractor=consolidation.org_administrator,
                        permission_type_id__in=['create_consolidation',],
                    ).values_list(
                        'contractor_permission_role__contractor_profiles__user',
                        flat=True
                    ))
        recipients.discard(None)
        event_type.create_notification(recipients=tuple(recipients),
                                       initiator=initiator,
                                       subj=consolidation)
    return 'done.'


def notify_consolidation_is_complete(consolidation_id, initiator_id):
    from .models import ConsolidationModel

    consolidation = ConsolidationModel.objects.filter(is_active=True, id=consolidation_id).first()
    initiator = ProfileModel.objects.filter(is_active=True, id=initiator_id).first()
    if consolidation and initiator:
        event_type = event_types.ConsolidationIsCompleteEvent()
        event_type.create_notification(initiator=initiator,
                                       subj=consolidation)
    return 'done.'


def notify_new_consolidation_is_create(consolidation_id, initiator_id):
    from .models import ConsolidationModel

    consolidation = ConsolidationModel.objects.filter(is_active=True, id=consolidation_id).first()
    initiator = ProfileModel.objects.filter(is_active=True, id=initiator_id).first()
    if consolidation and initiator:
        event_type = event_types.NewConsolidationIsCreateEvent()
        members = consolidation.members.all()
        report_form = consolidation.report_form
        if use_access_groups(initiator_id):
            recipients = set(
                users_that_have_permission_in_contractors(
                    tuple(members.values_list('pk', flat=True)),
                    ('create_consolidation', 'send_report',),
                    None,
                )
            )
        else:
            recipients = set(ContractorPermissionModel.objects.filter(
                (Q(aux_conditions=report_form) | Q(aux_conditions__isnull=True)),
                contractor_permission_role__is_active=True,
                contractor_permission_role__contractor__in=members,
                permission_type_id__in=['create_consolidation', 'send_report'],
            ).values_list(
                'contractor_permission_role__contractor_profiles__user',
                flat=True
            ))
        recipients.discard(None)
        recipients.discard(initiator.id)
        event_type.create_notification(recipients=tuple(recipients),
                                       initiator=initiator,
                                       subj=consolidation)
    return 'done.'
