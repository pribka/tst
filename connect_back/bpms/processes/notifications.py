from notifications import event_types

from users.models import ProfileModel
from users.utils import get_ancestor_departments_related_organizations

from . import models

status_map = {
    ('draft', 'submitted'): event_types.WorkflowRequestForHeadOfDepartment,
    ('submitted', 'in_review_finance',): event_types.WorkflowRequestForFinanceService,
    ('in_review_finance', 'in_review_lpr'): event_types.WorkflowRequestForLPR,
    ('in_review_lpr', 'approved',): event_types.WorkflowRequestForPayMaster,
    # ('approved', 'paid'): '',
    # ('paid', 'closed',): '',
}


def notify_change_workflow_status(workflow_request_id, old_status_code, new_status_code, user_id):
    workflow_request = models.WorkflowRequestModel.objects.get(pk=workflow_request_id)
    initiator = ProfileModel.objects.get(pk=user_id)
    new_status = models.WorkflowRequestStatusModel.objects.get(code=new_status_code)
    if new_status_code == 'submitted':
        route = workflow_request.request_routes.filter(workflow_position='head_of_department').first()
        recipients = tuple(route.users.all())
        if recipients:
            event_type = event_types.WorkflowRequestForHeadOfDepartment()
            event_type.create_notification(recipients, initiator=initiator, subj=workflow_request)
    elif new_status_code == 'in_review_finance':
        route = workflow_request.request_routes.filter(workflow_position='finance_service').first()
        recipients = tuple(route.users.all())
        if recipients:
            event_type = event_types.WorkflowRequestForFinanceService()
            event_type.create_notification(recipients, subj=workflow_request, initiator=initiator)
    elif new_status_code == 'in_review_lpr':
        route = workflow_request.request_routes.filter(workflow_position='director').first()
        recipients = tuple(route.users.all())
        if recipients:
            event_type = event_types.WorkflowRequestForLPR()
            event_type.create_notification(recipients, subj=workflow_request, initiator=initiator)
    elif new_status_code == 'in_review_personnel_service':
        route = workflow_request.request_routes.filter(workflow_position='personnel_service',).first()
        recipients = tuple(route.users.all())
        if recipients:
            event_type = event_types.WorkflowRequestForPersonnelService()
            event_type.create_notification(recipients, subj=workflow_request, initiator=initiator)
    elif new_status_code == 'issuing_money':
        contractor = workflow_request.organization
        contractors = get_ancestor_departments_related_organizations(
            (contractor.pk,),
            include_self=True,
        )
        recipients = tuple(models.WorkflowPositionUserModel.objects.filter(
            contractor_profile__contractor_id__in=list(contractors),
            workflow_position_id='paymaster',
        ).values_list('contractor_profile__user', flat=True))
        event_type = event_types.WorkflowRequestForPayMaster()
        event_type.create_notification(recipients, subj=workflow_request, initiator=initiator)
    # Уведомление автора о новом статусе
    event_type = event_types.WorkflowRequestChangeStatusForAuthor()
    recipients = (workflow_request.author,)
    event_type.create_notification(recipients, subj=workflow_request, obj=new_status, initiator=initiator)
    # Уведомление автора о выданных денежных средствах
    if new_status_code == 'paid' \
            and workflow_request.money_under_report \
            and not workflow_request.advance_report_approved:

        event_type = event_types.WorkflowRequestPaidForAuthor()
        recipients = (workflow_request.author,)
        event_type.create_notification(recipients, subj=workflow_request, initiator=initiator)


def notify_about_approve_lpr(workflow_request_id):
    workflow_request = models.WorkflowRequestModel.objects.get(pk=workflow_request_id)
    event_type = event_types.WorkflowRequestLPRApprove()
    routes = workflow_request.request_routes.exclude(
        workflow_position_id__in=('director', 'paymaster',)
    ).values_list('pk', flat=True)
    recipients = set(
        models.RequestRouteUserThrough.objects.filter(
            request_route_id__in=routes,
        ).exclude(status_id__in=('approved', 'rejected')).values_list('user', flat=True)
    )
    recipients.add(workflow_request.author.pk)
    event_type.create_notification(recipients=tuple(recipients), subj=workflow_request)


def notify_about_complete(workflow_request_id):
    workflow_request = models.WorkflowRequestModel.objects.get(pk=workflow_request_id)
    event_type = event_types.WorkflowRequestComplete()
    recipients = (workflow_request.author,)
    event_type.create_notification(recipients=recipients, subj=workflow_request)


def notify_finance_service_approve_ar(workflow_request_id):
    workflow_request = models.WorkflowRequestModel.objects.get(pk=workflow_request_id)
    initiator = workflow_request.author
    event_type = event_types.WorkflowRequestFinanceServiceAdvanceReport()
    route = workflow_request.request_routes.filter(workflow_position_id='finance_service').first()
    if route:
        recipients = tuple(route.users.all())
        if recipients:
            event_type.create_notification(recipients=recipients, subj=workflow_request, initiator=initiator)
