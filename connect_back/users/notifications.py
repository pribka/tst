from bkz3.settings import COMPANY_NAME, FRONTEND_URL, SUPPORT_EMAIL
from notifications import event_types
from contractor_permissions.utils import users_that_have_app_section_role_in_contractors
from users.models import ProfileModel
from notifications.utils import send_email
from notifications.models import EmailNotificationModel, EmailNotificationRecipientModel

from . import models


def send_notify_about_new_member(contractor_profile_id):
    from common.catalogs.models import ContractorProfileModel
    contractor_profile = ContractorProfileModel.objects.get(pk=contractor_profile_id)
    event_type = event_types.OrganizationNewMember()
    contractor = contractor_profile.contractor
    admins = set(users_that_have_app_section_role_in_contractors((contractor.pk,), 'organization', 'admin'))
    director = contractor.contractor_profile.filter(is_active=True, director=True).first()
    if director:
        admins.add(director.user.pk)
    if admins:
        event_type.create_notification(tuple(admins), subj=contractor_profile)


def send_notify_about_welcome(profile_id):
    recipients = (models.ProfileModel.objects.get(pk=profile_id),)
    event_type = event_types.UserNewMemberOrganization()
    event_type.create_notification(recipients,)


def notify_about_leave_member(user, contractor):
    recipients = tuple(
        contractor.contractor_profile.filter(is_active=True, director=True).values_list('user', flat=True)
    )
    if recipients:
        event_type = event_types.OrganizationLeaveMember()
        event_type.create_notification(recipients, initiator=user, subj=contractor)


def notify_about_delete_member(recipient, contractor):
    if recipient and contractor:
        event_type = event_types.OrganizationDeleteMember()
        event_type.create_notification((recipient,), subj=contractor)


def notify_about_join_to_organization(contractor_request):
    from users.models import ProfileModel
    recipients = ProfileModel.objects.filter(
        is_active=True, temporary_blocked=False, is_support=True
    ).values_list('pk', flat=True)
    if recipients:
        event_type = event_types.RequestJoinToOrganization()
        event_type.create_notification(recipients, subj=contractor_request)


def notify_about_new_sign_request(data):

    recipients = (data['recipient'],)
    if recipients:
        event_type = event_types.DIDSignEvent()
        event_type.create_notification(recipients, subj=data)


def send_email_about_entry(profile_id):
    profile = ProfileModel.objects.get(pk=profile_id)
    email_notification = EmailNotificationModel.objects.create(
        template='register_welcome_1',
        subject=f'{COMPANY_NAME} қызметіне қош келдіңіз — жұмысты жобадан бастаңыз | Добро пожаловать в {COMPANY_NAME} — начните с проекта',
        context={
            'user_full_name': profile.full_name,
            'company_name': COMPANY_NAME,
            'url': FRONTEND_URL,
            'support_email': SUPPORT_EMAIL,
        }
    )
    EmailNotificationRecipientModel.objects.create(
        email_notification=email_notification,
        recipient=profile.user.email,
    )
    send_email(email_notification.pk)


def notify_about_new_user(new_user_info_id):
    new_user_info = models.NewUserInfoModel.objects.get(pk=new_user_info_id)
    recipients = tuple(ProfileModel.objects.filter(is_active=True, is_support=True).values_list('pk', flat=True))
    event_type = event_types.NewUserInfo()
    event_type.create_notification(recipients, subj=new_user_info)
