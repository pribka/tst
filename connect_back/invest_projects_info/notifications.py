from users.models import ProfileModel
from notifications import event_types

from users.utils import get_ancestor_departments_related_organizations
from contractor_permissions.utils import users_that_have_permission_in_contractors

from . import models


INVEST_PROJECT_STATUS_NOTIFICATION_MAPPING = {
    'on_check': event_types.InvestProjectChangeStatusOnCheck,
    'on_rework': event_types.InvestProjectChangeStatusOnRework,
    'approved': event_types.InvestProjectChangeStatusApproved,
    'change_requested': event_types.InvestProjectChangeStatusChangeRequested,
}


def notify_about_new_status(invest_project, status_code, initiator):
    # оповещение пользователям с правами одобрять инвестпроекты в этой организации и В ВЫШЕСТОЯЩИХ
    if status_code in ['on_check', 'change_requested']:
        approve_permission_id = models.InvestProjectPermissionTypeModel.objects.get(code='approve')
        ancestors = get_ancestor_departments_related_organizations(
                    (invest_project.organization_id,),
                    include_self=True,
                    return_type='set',)
        recipients = users_that_have_permission_in_contractors(
            ancestors,
            'create_invest_projects_info',
            approve_permission_id)
    # оповещение пользователям с правами создавать инвестпроекты в ДАННОЙ организации
    elif status_code in ['on_rework', 'approved']:
        create_permission_id = models.InvestProjectPermissionTypeModel.objects.get(code='create')
        recipients = users_that_have_permission_in_contractors(
            (invest_project.organization_id,),
            'create_invest_projects_info',
            create_permission_id)
    else:
        return 'При данном типе статуса уведомления не рассылаются'
        
    recipients.discard(initiator)
    recipients.discard(None)
    try:
        event_type = INVEST_PROJECT_STATUS_NOTIFICATION_MAPPING.get(status_code)()
    except TypeError:
        event_type = event_types.InvestProjectChangeStatusGeneric()
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=invest_project)
    return 'done'
