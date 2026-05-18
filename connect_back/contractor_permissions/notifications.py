
from notifications import event_types

from . import models


def notify_about_add_member(profile_id, access_group_id, contractor_id):
    access_group = models.AccessGroupModel.objects.get(pk=access_group_id)
    contractor = models.ContractorModel.objects.get(pk=contractor_id)
    event_type = event_types.NewAccessGroupForMember()
    recipients = (profile_id,)
    event_type.create_notification(recipients, obj=access_group, subj=contractor)
