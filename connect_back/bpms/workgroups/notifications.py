from time import sleep
from notifications import event_types
from users.models import ProfileModel
from common.models import BaseModel

from . import models


def notify_about_new_workgroup_member(workgroup, initiator, new_member):
    if workgroup.is_project:
        event_type = event_types.NewMemberInProject()
    else:
        event_type = event_types.NewMemberInWorkGroup()
    event_type.create_notification(recipients=(workgroup.author,), initiator=initiator, subj=new_member, obj=workgroup)
    return 'done.'


def notify_about_remove_from_workgroup_member(workgroup, initiator):
    if workgroup.is_project:
        event_type = event_types.MemberRemovedFromProject()
    else:
        event_type = event_types.MemberRemovedFromWorkGroup()
    event_type.create_notification(recipients=(workgroup.author,), initiator=initiator, obj=workgroup)
    return 'done.'


def notify_about_invite_workgroup_organization_member(workgroup_id, organization_member_id, user_id):
    from users.models import ProfileModel
    from .models import WorkgroupModel, WorkgroupMemberOrganizationModel
    user = ProfileModel.objects.filter(is_active=True, pk=user_id).first()
    workgroup = WorkgroupModel.objects.filter(is_active=True, pk=workgroup_id).first()
    organization_member = WorkgroupMemberOrganizationModel.objects.filter(is_active=True, pk=organization_member_id).first()
    event_type = event_types.WorkgroupOrganizationMemberInvite()
    event_type.create_notification(recipients=(user,), obj=workgroup, subj=organization_member)
   
    return 'done.'


def notify_about_workgroup_news(news, initiator, workgroup):
    member_ids = models.WorkgroupMembersModel.objects.filter(
        is_active=True,
        work_group=workgroup,
        membership_request_status__code="APPROVED"
    ).values_list('member_id', flat=True)
    recipients = set(member_ids)
    recipients.discard(initiator.pk)
    recipients.discard(None)

    if recipients:
        if workgroup.is_project:
            event_type = event_types.NewProjectNewsCreated()
        else:
            event_type = event_types.NewWorkgroupNewsCreated()
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=news, workgroup=workgroup)
        return 'done'
    else:
        return 'no recipients. Done.'



