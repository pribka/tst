from notifications import event_types


def notify_invite_contractor(subj):
    event_type = event_types.InviteContractor()
    initiator = subj.author
    obj = subj.contractor if subj.contractor_parent == subj.contractor_owner else subj.contractor_parent
    recipient = obj.contractor_profile.filter(is_active=True, director=True).first()
    if recipient:
        event_type.create_notification(recipients=(recipient.user,), initiator=initiator, subj=subj)


def notify_about_accept_invite(contractor_invite):
    event_type = event_types.InviteContractorAccept()
    recipients = tuple(
        contractor_invite.contractor_owner.contractor_profile.filter(
            is_active=True,
            director=True
        ).values_list('user', flat=True)
    )
    if recipients:
        event_type.create_notification(recipients=recipients, subj=contractor_invite)


def notify_about_reject_invite(contractor_invite):
    event_type = event_types.InviteContractorReject()
    recipients = tuple(
        contractor_invite.contractor_owner.contractor_profile.filter(
            is_active=True,
            director=True
        ).values_list('user', flat=True)
    )
    if recipients:
        event_type.create_notification(recipients=recipients, subj=contractor_invite)

