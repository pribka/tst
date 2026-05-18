from notifications import event_types

from users.models import ProfileModel

from . import models


def notify_about_request_update(sport_facility_id, initiator_id):
    sport_facility = models.SportFacilityInfoModel.objects.get(pk=sport_facility_id)
    initiator = ProfileModel.objects.get(pk=initiator_id)
    recipients = sport_facility.get_admins()
    if recipients:
        event_type = event_types.SportFacilityRequestUpdate()
        event_type.create_notification(recipients, initiator=initiator, subj=sport_facility)


def notify_about_change_status(sport_facility_id, status_id, initiator_id):
    subj = models.SportFacilityInfoModel.objects.get(pk=sport_facility_id)
    obj = models.SportFacilityStatusModel.objects.get(pk=status_id)
    initiator = ProfileModel.objects.get(pk=initiator_id)
    if obj.code in ('on_check', 'draft',):
        recipients = subj.get_admins()
    else:
        recipients = subj.get_creators()
    if recipients:
        event_type = event_types.SportFacilityChangeStatusGeneric()
        event_type.create_notification(recipients=recipients, subj=subj, obj=obj, initiator=initiator)
