import json
import string
import secrets
import uuid
import random
import datetime

from django_q.tasks import async_task

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Prefetch, Case, When, Value, BooleanField, Count
from django.utils import timezone
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import exceptions

from common.redis import socketio_redis
from common.models import File
from common.utils import use_access_groups

from common.catalogs.models import ContractorRelationModel, ContractorModel, ContractorProfileModel, ContractorMemberModel
from bpms.workgroups.models import WorkgroupMembersModel, WorkgroupMembershipStatus
from bpms.chat.models import ChatModel, MemberModel

from contractor_permissions.utils import users_that_have_permission_in_contractors

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL, COMPANY_NAME, FRONTEND_URL, FILTER_BY_ORGANIZATIONS
from django.db import IntegrityError
from notifications.models import EmailNotificationModel, EmailNotificationRecipientModel
from notifications.utils import send_email
from notifications.utils import send_sms_message
from app_info.models import AppInfo

from . import search_indexes, serializers, notifications
from .models import (
    CustomUser, InviteModel, EmailInviteModel, LeaveRequestModel, MobileTokenModel, EntryInfoModel, NewUserInfoModel,
    ProfileModel,
)


def build_captcha_debug_data(request, validation_error):
    captcha_debug = {
        "details": validation_error.get_full_details(),
        "recaptcha_testing": getattr(settings, "DRF_RECAPTCHA_TESTING", False),
        "has_captcha_token": bool(request.data.get("captcha")),
        "captcha_token_length": len(str(request.data.get("captcha", ""))),
        "client_ip": request.META.get("REMOTE_ADDR"),
        "x_forwarded_for": request.META.get("HTTP_X_FORWARDED_FOR"),
    }
    recaptcha_secret_key = getattr(settings, "DRF_RECAPTCHA_SECRET_KEY", "")
    if recaptcha_secret_key and request.data.get("captcha"):
        recaptcha_domain = getattr(settings, "DRF_RECAPTCHA_DOMAIN", "www.google.com")
        verify_url = f"https://{recaptcha_domain}/recaptcha/api/siteverify"
        verify_timeout = getattr(settings, "DRF_RECAPTCHA_VERIFY_REQUEST_TIMEOUT", 10)
        verify_payload = {
            "secret": recaptcha_secret_key,
            "response": request.data.get("captcha"),
            "remoteip": request.META.get("REMOTE_ADDR"),
        }
        try:
            verify_response = requests.post(
                url=verify_url,
                data=verify_payload,
                timeout=verify_timeout,
            )
            captcha_debug["google_verify_status_code"] = verify_response.status_code
            try:
                captcha_debug["google_verify_response"] = verify_response.json()
            except ValueError:
                captcha_debug["google_verify_response"] = {
                    "raw_body": verify_response.text
                }
        except requests.RequestException as verify_error:
            captcha_debug["google_verify_request_error"] = str(verify_error)
    else:
        captcha_debug["google_verify_skipped"] = (
            "missing DRF_RECAPTCHA_SECRET_KEY or captcha token"
        )
    return captcha_debug


def update_profile_index(profile):
    search_indexes.ProfileIndex().update_object(profile)
    return 'done.'


def update_new_user_info_index(profile_id):
    """
    Переиндексируем NewUserInfoModel при изменении профиля пользователя.
    В индексе используются user.full_name и user.user.email.
    """
    try:
        profile = ProfileModel.objects.get(pk=profile_id)
        new_user_info = NewUserInfoModel.objects.get(user=profile)
        search_indexes.NewUserInfoIndex().update_object(new_user_info)
        return 'done.'
    except (ProfileModel.DoesNotExist, NewUserInfoModel.DoesNotExist):
        pass


def send_socketio_about_update_profile(profile_id):
    data = json.dumps({
        'event': 'update_user',
        'data': f"{profile_id}",
    }, cls=DjangoJSONEncoder)
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def check_login_exist(login_name):
    return CustomUser.objects.filter(
        Q(username=login_name)
        | Q(email=login_name)
        | Q(profile__phone=login_name)
    ).exists()


def generate_confirm_code() -> str:
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for each in range(6))


def generate_user_name() -> str:
    alphabet = string.digits + string.ascii_lowercase
    return ''.join(secrets.choice(alphabet) for each in range(6))


def get_confirm_code_key(login: str, target: str) -> str:
    return f'confirm_code__{target}__{login}'


def get_confirm_token_key(login: str, target: str) -> str:
    return f'confirm_token__{target}__{login}'


def set_confirm_code(login: str, target: str) -> str:
    confirm_code = generate_confirm_code()
    cache.set(get_confirm_code_key(login, target), confirm_code, timeout=1200)
    return confirm_code


def get_confirm_code(login: str, target: str) -> str:
    return cache.get(get_confirm_code_key(login, target), '')


def check_confirm_code(login: str, target: str, confirm_code: str) -> bool:
    cached_confirm_code = get_confirm_code(login, target)
    return cached_confirm_code == confirm_code


def set_confirm_token(login: str, target: str) -> str:
    confirm_token = str(uuid.uuid4())
    cache.set(get_confirm_token_key(login, target), confirm_token, timeout=1800)
    cache.delete(get_confirm_code_key(login, target))
    return confirm_token


def get_confirm_token(login: str, target: str) -> str:
    return cache.get(get_confirm_token_key(login, target), '')


def check_confirm_token(login: str, target: str, confirm_token: str) -> bool:
    cached_confirm_token = get_confirm_token(login, target)
    return cached_confirm_token == confirm_token


def delete_confirm_token(login: str, target: str) -> None:
    cache.delete(get_confirm_token_key(login, target))


def send_email_confirm_code(email: str, confirm_code: str) -> None:
    with transaction.atomic():
        notification = EmailNotificationModel.objects.create(template='confirm_code',
                                                             subject='Подтверждение электронной почты',
                                                             context={"confirm_code": confirm_code})
        EmailNotificationRecipientModel.objects.create(recipient=email, email_notification=notification)

    send_email(notification.pk)


def send_sms_confirm_code(phone: str, confirm_code: str) -> None:
    message_text = f"Код активации на портале {COMPANY_NAME}: {confirm_code}"
    send_sms_message(message_text, phone)


def send_email_forgot_password(forgot_password, user):
    context = {'url': f'{FRONTEND_URL}/user/reset-password/{forgot_password.uuid}/', 'user_full_name': user.full_name}
    notification = EmailNotificationModel.objects.create(template='forgot_password',
                                                         subject='Сброс пароля',
                                                         context=context)
    recipient = EmailNotificationRecipientModel.objects.create(email_notification=notification,
                                                               recipient=user.email)
    async_task(send_email, notification.id)


def get_forgot_password_key(phone):
    return f"forgot_password__{phone}"


def get_forgot_password_code(phone):
    return cache.get(get_forgot_password_key(phone), '')


def send_sms_forgot_password(phone: str) -> None:
    confirm_code = generate_confirm_code()
    cache.set(get_forgot_password_key(phone), confirm_code, timeout=1200)
    message_text = f"Код подтверждения на портале {COMPANY_NAME}: {confirm_code}"
    send_sms_message(message_text, phone)


def check_sms_forgot_password(phone: str, confirm_code: str) -> bool:
    if not phone or not confirm_code:
        return False
    cached_confirm_code = cache.get(get_forgot_password_key(phone), '')
    if not cached_confirm_code:
        return False
    if cached_confirm_code == confirm_code:
        return True
    return False


def get_target_name(target: str) -> str:
    if target == 'phone':
        target_name = 'номер телефона'
    else:
        target_name = 'адрес электронной почты'
    return target_name


def validate_logo(serializer, data):
    try:
        user = serializer.context.get('request').user.profile
    except AttributeError:
        raise exceptions.ValidationError('Serializer has no request!')
    if data:
        if not data.author == user:
            raise exceptions.ValidationError('Incorrect logo file')
        if not data.is_image:
            raise exceptions.ValidationError('Incorrect logo file')
    return data


def get_logo_path(logo_instance: File) -> str:
    if logo_instance:
        return f"{logo_instance.pk}.{logo_instance.extension}" if logo_instance.extension else f"{logo_instance.pk}"
    else:
        return ''


def check_invite_token(token: str):
    if not token:
        raise exceptions.ValidationError({"message": "Приглашение аннулировано."})
    now = timezone.now()
    from help_desk.models import ContactPersonModel
    if not InviteModel.objects.filter(
            Q(deactivate_at__isnull=True) | Q(deactivate_at__gte=now),
            is_active=True,
            token=token
    ).exists() and not EmailInviteModel.objects.filter(
        Q(deactivate_at__isnull=True) | Q(deactivate_at__gte=now),
        is_active=True,
        is_sent=True,
        is_accepted=False,
        token=token
    ).exists() and not ContactPersonModel.objects.filter(
        user__isnull=True,
        invite_token=token,
        is_active=True,
    ):
        raise exceptions.ValidationError({"message": "Приглашение аннулировано."})


def get_invite_instance_from_token(token: str):
    """Возвращает экземпляр приглашения (InviteModel или EmailInviteModel) по токену"""
    try:
        instance = InviteModel.objects.get(is_active=True, token=token)
    except InviteModel.DoesNotExist:
        try:
            instance = EmailInviteModel.objects.get(is_active=True, is_sent=True, is_accepted=False, token=token)
        except EmailInviteModel.DoesNotExist:
            return None
    return instance


def get_organization_from_invite_token(token: str):
    instance = get_invite_instance_from_token(token)
    return instance.contractor if instance else None


def get_is_create_new_contractor_from_token(token: str):
    """Возвращает значение is_create_new_contractor для инвайта"""
    instance = get_invite_instance_from_token(token)
    if not instance:
        return False
    return instance.is_create_new_contractor


def create_entry_info_for_user(profile):
    """Создает запись EntryInfoModel для пользователя"""
    entry = EntryInfoModel()
    entry.user = profile
    entry.save()
    return entry


def get_contact_person_from_invite_token(token: str):
    from help_desk.models import ContactPersonModel
    try:
        instance = ContactPersonModel.objects.filter(
            user__isnull=True,
            invite_token=token,
            is_active=True,
        ).order_by('-created_at').first()
    except (ContactPersonModel.DoesNotExist, ValidationError):
        instance = None
    return instance


def get_invite_url(token):
    return f"{FRONTEND_URL}/user/join-user?token={token}"


def send_email_invite(email_invite):
    with transaction.atomic():
        notification = EmailNotificationModel.objects.create(
            template='email_invite',
            subject='Приглашение',
            context={
                "author_name": email_invite.author.full_name,
                "contractor_name": email_invite.contractor.name,
                "company_name": COMPANY_NAME,
                "url": get_invite_url(email_invite.token),
            }
        )
        EmailNotificationRecipientModel.objects.create(recipient=email_invite.email, email_notification=notification)
    email_invite.is_sent = True
    email_invite.save(update_fields=("is_sent",),)
    send_email(notification.pk)


def accept_invite(invite_token, profile):
    """Добавляет пользователя в проект/команду. Меняет булеан приглашения на ПОДТВЕРЖДЁН у Email-инвайта."""
    if not invite_token:
        return
    invite = None
    email_invite = None
    # Находим инвайт (обычный или email-инвайт)
    try:
        email_invite = EmailInviteModel.objects.get(token=invite_token)
        workgroup = getattr(email_invite, "workgroup", None)
    except EmailInviteModel.DoesNotExist:
        try:
            invite = InviteModel.objects.get(token=invite_token)
            workgroup = getattr(invite, "workgroup", None)
        except InviteModel.DoesNotExist:
            return

    # Добавляем пользователя в команду, если она задана
    if workgroup:
        from bpms.workgroups.models import (
            WorkgroupMembersModel, WorkgroupMembershipRole, WorkgroupMembershipStatus
        )
        from bpms.workgroups.utils import create_workgroup_chat_members
        from bpms.workgroups.notifications import  notify_about_new_workgroup_member

        with transaction.atomic():
            default_status = WorkgroupMembershipStatus.objects.get(code="APPROVED")
            default_role = WorkgroupMembershipRole.objects.get(code="MEMBER")

            member, created = WorkgroupMembersModel.objects.get_or_create(
                member=profile,
                work_group=workgroup,
                defaults={
                    "membership_request_status": default_status,
                    "membership_role": default_role,
                    "is_active": True,
                },
            )
            transaction.on_commit(
                lambda: async_task(notify_about_new_workgroup_member, workgroup, profile, profile)
                )
            transaction.on_commit(
                lambda: async_task(create_workgroup_chat_members, str(workgroup.pk), (str(profile.pk),))
                )


    # Для email-инвайта отмечаем принятие
    if email_invite:
        email_invite.is_accepted = True
        email_invite.accepted_user = profile
        email_invite.save(update_fields=("is_accepted", "accepted_user"))


def join_by_invite(invite_token, profile):
    """Принятие инвайта в организацию и проект/команду.
    Соединение карточки клиента с профилем (для хэлпдеска)."""
    check_invite_token(invite_token)
    contractor = get_organization_from_invite_token(invite_token)
    if not contractor:
        contact_person = get_contact_person_from_invite_token(invite_token)
        if not contact_person:
            raise ValidationError({"message": "Приглашение недействительно."})
        contact_person.user = profile
        contact_person.unknown = False
        contact_person.save(update_fields=('user', 'unknown'))
        return True

    with transaction.atomic():
        is_create_new_contractor = get_is_create_new_contractor_from_token(invite_token)
        if not is_create_new_contractor:
            contractor_profile = create_contractor_profile(contractor, profile, 'contractor_guest')
            transaction.on_commit(lambda: async_task(notifications.send_notify_about_new_member, str(contractor_profile.pk)))
        accept_invite(invite_token, profile)
    return True


def get_ancestor_related_organizations(contractor_id, include_self=False):
    contractors = (contractor_id,)
    if include_self:
        result = [contractor_id]
    else:
        result = []
    while True:
        contractor_parents = set(ContractorRelationModel.objects.filter(
            contractor_id__in=contractors,
            is_active=True
        ).values_list('contractor_parent', flat=True))
        result = result + list(contractor_parents)
        if len(contractor_parents) == 0:
            result = set(result)
            return result
        contractors = contractor_parents


def get_ancestor_departments_related_organizations(contractors, include_self=False, return_type='set'):
    """Возвращает все структурные подразделения, являщиеся родительскими по отношению к переданным."""
    if include_self:
        result = list(contractors)
    else:
        result = []
    while True:
        contractor_parents = set(ContractorRelationModel.objects.filter(
            contractor_id__in=contractors,
            relation_type_id='structural_division',
            is_active=True,
        ).values_list('contractor_parent', flat=True))
        result.extend(contractor_parents)
        if len(contractor_parents) == 0:
            if return_type == 'set':
                result = set(result)
            return result
        contractors = contractor_parents


def get_descendants_departments_related_organizations(contractors_seed, include_self=True) -> set:
    """Возвращает все структурные подразделения, являщиеся дочерними по отношению к переданным."""
    if include_self:
        result = list(contractors_seed)
    else:
        result = []
    while True:
        contractors = set(ContractorRelationModel.objects.filter(
            contractor_parent_id__in=contractors_seed,
            relation_type_id='structural_division',
            is_active=True,
        ).values_list('contractor', flat=True))
        result = result + list(contractors)
        if len(contractors) == 0:
            result = set(result)
            return result
        contractors_seed = contractors


def get_tree_departments_related_organizations(organizations):
    """Возвращает полное дерево организаций (структурных подразделений) (вышестоящие и нижестоящие по отношению к переданным)"""
    roots = get_roots_departments_related_organizations(organizations)
    tree = get_descendants_departments_related_organizations(roots)
    return tree


def get_roots_departments_related_organizations(organizations):
    """Возвращает корневые организации и организации без структурных отношений."""
    roots = set(ContractorRelationModel.objects.filter(
        Q(contractor_id__in=organizations) |
        Q(contractor_parent_id__in=organizations),
        relation_type_id='structural_division',
    ).values_list('contractor_root', flat=True).distinct())

    structural_relations_qs = ContractorRelationModel.objects.filter(
        Q(contractor_id__in=organizations) | Q(contractor_parent_id__in=organizations),
        relation_type_id='structural_division')
    organizations_without_relations = set(ContractorModel.objects
                                       .filter(~Q(pk__in=structural_relations_qs.values_list('contractor')),
                                               ~Q(pk__in=structural_relations_qs.values_list('contractor_parent')),
                                               pk__in=organizations)
                                        .values_list('pk', flat=True))
    roots.update(set(organizations_without_relations))

    return roots


def check_update_organization_permission(organization_id, user):
    ancestors = get_ancestor_departments_related_organizations((organization_id,), include_self=True)
    is_director = user.contractor_profile.filter(
        is_active=True,
        director=True,
        contractor_id__in=ancestors
    ).exists()
    if is_director:
        return
    if use_access_groups(user.pk):
        if user.pk not in users_that_have_permission_in_contractors(ancestors, 'admin', None):
            raise exceptions.PermissionDenied()
    else:
        from contractor_permissions.models import ContractorPermissionRoleModel
        if not ContractorPermissionRoleModel.objects.filter(
                    is_active=True,
                    contractor_profiles__user=user,
                    contractor_permissions__permission_type_id='admin',
                    contractor_id__in=ancestors,
                ).exists():
            raise exceptions.PermissionDenied()


def check_detail_organization_permission(organization_id, user):
    if get_tree_departments_related_organizations((organization_id,)).isdisjoint(set(user.my_organizations)):
        raise exceptions.PermissionDenied()


def filter_users_by_organizations(queryset, user, add_support_users=False, add_org_support_users=False, only_my=None):
    if FILTER_BY_ORGANIZATIONS:
        user_organizations = user.my_organizations
        organizations = get_tree_departments_related_organizations(user_organizations)
        
        # Получаем команды и проекты, где пользователь является участником с одобренным статусом
        approved_status = WorkgroupMembershipStatus.objects.get(code="APPROVED")
        user_workgroups = WorkgroupMembersModel.objects.filter(
            member=user,
            is_active=True,
            membership_request_status=approved_status
        ).values_list('work_group_id', flat=True)
        
        # Получаем пользователей, которые являются участниками этих команд и проектов
        workgroup_members = WorkgroupMembersModel.objects.filter(
            work_group_id__in=user_workgroups,
            is_active=True,
            membership_request_status=approved_status
        ).values_list('member_id', flat=True)
        
        # Получаем пользователей из доступных контактных лиц в разделе техподдержки
        from help_desk.utils import get_contact_persons_queryset
        available_contact_persons = get_contact_persons_queryset(user.pk)
        contact_person_user_ids = available_contact_persons.filter(
            user__isnull=False
        ).values_list('user_id', flat=True).distinct()
        
        if only_my is True:
            lookup = Q(contractors__in=organizations)
        elif only_my is False:
            lookup = (Q(id__in=workgroup_members) | Q(id__in=contact_person_user_ids)) & ~Q(contractors__in=organizations)
        else:
            lookup = Q(contractors__in=organizations) | Q(id__in=workgroup_members) | Q(id__in=contact_person_user_ids)
        
        if add_support_users:
            lookup |= Q(is_support=True)
        if add_org_support_users:
            from help_desk.utils import get_my_actual_specialists
            actual_specialist_users = [specialist_data[0] for specialist_data in set(get_my_actual_specialists(user))]
            lookup |= Q(pk__in=actual_specialist_users)
            queryset = queryset.annotate(
                is_org_support=Case(
                    When(pk__in=actual_specialist_users, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
        queryset = queryset.filter(lookup).distinct()
    return queryset


def index_contractor_profile_requests(profile_id):
    from common.catalogs.models import ContractorProfileRequestModel
    from common.catalogs.search_indexes import ContractorProfileRequestModelIndex
    contractor_profile_requests = ContractorProfileRequestModel.objects.filter(
        is_active=True,
        user_id=profile_id
    ).order_by('created_at')
    for each in contractor_profile_requests:
        ContractorProfileRequestModelIndex().update_object(each)


def initial_contractor_request(contractor_request_id):
    from common.catalogs.models import ContractorProfileRequestModel
    from .notifications import notify_about_join_to_organization
    contractor_request = ContractorProfileRequestModel.objects.get(pk=contractor_request_id)
    notify_about_join_to_organization(contractor_request)


def login_user(request, user_previous_login, user):
    serialized_data = serializers.CustomUserDetailSerializer(user.profile).data
    backend = getattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
    login(request, user, backend=backend)
    refresh = RefreshToken.for_user(user)

    invite_token = request.data.get('invite_token')
    if invite_token:
        join_by_invite(invite_token, user.profile)

    if request.data.get('mobile', None):
        tokenobject = MobileTokenModel.objects.create(user=user)
        serialized_data['token'] = tokenobject.token
    serialized_data['jwt_access'] = str(refresh.access_token)
    serialized_data['jwt_refresh'] = str(refresh)
    serialized_data['user_previous_login'] = user_previous_login
    serialized_data['entry_complete'] = get_entry_complete(user.profile)
    return serialized_data


def get_entry_complete(profile):
    try:
        entry = profile.entry_info
    except ObjectDoesNotExist:
        entry = None
    if entry and not entry.complete:
        entry_complete = False
    else:
        entry_complete = True
    return entry_complete


def send_leave_request_email(leave_request_id: str):
    """Оповещение о новой заявке (кнопка 'Запросить демонстрацию').
    На вход принимает экземпляр LeaveRequestModel"""
    instance = LeaveRequestModel.objects.get(pk=leave_request_id)
    # Общий контекст для всех заявок
    context = dict()
    context['name'] = instance.name
    context['phone'] = instance.phone
    context['email'] = instance.email
    request_type_id = instance.request_type.code
    if request_type_id == 'request_demonstration':
        subject = f"Новый запрос на демонстрацию - {context['name']}"
    elif request_type_id == 'request_tariff':
        # Добавляем контекст, специфичный для заявки на подключение тарифа
        context['organization'] = instance.data.get('organization', '')
        context['tariff'] = instance.data.get('tariff', '')
        subject = f"Новая заявка на подключение тарифа - {context['organization']}"
    else:
        return
    notification = EmailNotificationModel.objects.create(
        template=request_type_id,
        subject=subject,
        context=context
    )
    EmailNotificationRecipientModel.objects.create(
        email_notification=notification,
        recipient=instance.request_type.email
    )
    send_email(notification.id)


def generate_password(length: int = 12) -> str:
    if length < 4:
        raise ValueError("Пароль должен быть длиной минимум 4 символа")

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+[]{};:,.<>?/"

    all_chars = lowercase + uppercase + digits + symbols

    # Обеспечиваем хотя бы по одному символу из каждой категории
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(symbols),
    ]

    # Остальные символы — любые
    password += random.choices(all_chars, k=length - 4)

    # Перемешиваем список, чтобы не шло в предсказуемом порядке
    random.shuffle(password)

    return "".join(password)


def create_new_user_info(profile_id, contractor_id):
    new_user_info = NewUserInfoModel.objects.create(user_id=profile_id, contractor_id=contractor_id)
    notifications.notify_about_new_user(str(new_user_info.pk))


def create_new_contractor(profile, contractor_name, contractor_bin, tariff_code):
    """Создает новую организацию с именем contractor_name и БИН contractor_bin.
    Назначает тариф с кодом tariff_code.
    Назначает пользователя profile ее директором, добавляет его в группу админов."""
    from billing.models import ContractorTariffModel, TariffModel
    from contractor_permissions.models import AccessGroupMemberThroughModel, AccessGroupModel

    contractor = ContractorModel()
    contractor.name = contractor_name
    contractor.full_name = contractor_name
    contractor.save()

    contractor_member = ContractorMemberModel()
    contractor_member.contractor = contractor
    contractor_member.name = contractor.name
    contractor_member.inn = contractor_bin
    contractor_member.save()

    contractor_profile = ContractorProfileModel()
    contractor_profile.contractor = contractor
    contractor_profile.user = profile
    contractor_profile.director = True
    contractor_profile.save()

    profile.current_contractor = contractor
    profile.save()

    default_tariff = TariffModel.objects.get(code=tariff_code)
    contractor_tariff = ContractorTariffModel()
    contractor_tariff.contractor = contractor
    contractor_tariff.tariff = default_tariff
    contractor_tariff.date_start = timezone.now()
    contractor_tariff.date_end = contractor_tariff.date_start + datetime.timedelta(days=default_tariff.duration)
    contractor_tariff.save()

    access_group_member = AccessGroupMemberThroughModel()
    access_group_member.member = contractor_profile
    admin_access_group = AccessGroupModel.objects.get(code='admin')
    access_group_member.access_group = admin_access_group
    access_group_member.save()

    return contractor


def create_demo_contractor(profile, contractor_name=None):
    """Создает пользователю новую организацию 'Моя организация' с демо-тарифом."""
    with transaction.atomic():
        contractor = create_new_contractor(profile, contractor_name or 'Моя организация', '', 'demo')
        transaction.on_commit(lambda: async_task(notifications.send_email_about_entry, str(profile.pk)))
        transaction.on_commit(lambda: async_task(create_new_user_info, str(profile.pk), str(contractor.pk)))
    return contractor


def create_customer_card_contractor(customer_card, profile):
    """Создает пользователю новую организацию в соответствии карточкой клиента.
    С тарифом help_desk_client."""
    with transaction.atomic():
        contractor = create_new_contractor(profile, customer_card.name, customer_card.inn, 'help_desk_client')
        customer_card.customer = contractor
        customer_card.save()
        # TODO Здесь не надо никаких уведомлений??? Как create_demo_contractor
    return contractor


def create_contractor_profile(contractor, profile, access_group_code):
    """Добавляем пользователя profile в организацию contractor.
    Назначает ему группу доступа с кодом access_group_code"""
    from contractor_permissions.models import AccessGroupMemberThroughModel, AccessGroupModel

    contractor_profile, created = ContractorProfileModel.objects.get_or_create(
        contractor=contractor,
        user=profile,
    )

    access_group_member = AccessGroupMemberThroughModel()
    access_group_member.member = contractor_profile
    access_group = AccessGroupModel.objects.get(code=access_group_code)
    access_group_member.access_group = access_group
    access_group_member.save()

    cache_key = f'tariff_section_codes_{str(profile.pk)}'
    cache.delete(cache_key)

    return contractor_profile


def handle_is_support_change(profile_id, old_value, new_value):
    """
    Обработчик изменения поля is_support у профиля пользователя.
    """
    profile = ProfileModel.objects.get(pk=profile_id)
    
    if new_value:  # Пользователь стал сотрудником техподдержки
        # Добавляем его во все активные чаты техподдержки как модератора
        support_chats = ChatModel.objects.filter(
            is_active=True,
            is_support=True
        ).exclude(
            chat_author=profile,
            member__user=profile,
            member__is_active=True
        )
        
        for chat in support_chats:
            # Создаем нового участника-модератора
            try:
                member = MemberModel.objects.create(
                    chat=chat,
                    user=profile,
                    is_moderator=True,
                    is_active=True
                )
                chat_members = [member]
            except IntegrityError:
                # Участник уже существует, активируем его
                member = chat.members.filter(user=profile).first()
                if member:
                    member.is_active = True
                    member.is_moderator = True
                    member.save(update_fields=('is_active', 'is_moderator'))
                    chat_members = [member]
                else:
                    continue
            
    else:  # Пользователь перестал быть сотрудником техподдержки
        # Исключаем его из всех чатов техподдержки
        support_chats = ChatModel.objects.filter(
            is_active=True,
            is_support=True,
            member__user=profile,
            member__is_active=True,
        ).exclude(chat_author=profile)
        
        for chat in support_chats:
            member = chat.members.filter(
                user=profile,
                is_active=True,
            ).first()
            
            if member:
                member.is_active = False
                member.save(update_fields=('is_active',))
               

def get_blocking_relations(contractor_profile):
    """
    Возвращает словарь с блокирующими отношениями сотрудника. Ключи словаря:
    director - true/false: является ли сотрудник руководителем организации.
    admin - true/false: является ли сотрудник единственным админом организации.
    projects_founder - list: список проектов, где сотрудник основатель.
    workgroups_founder - list: список команд, где сотрудник основатель.
    tasks - list: задачи, где сотрудник постановщик или ответственный.
    tickets - list: обращения, где сотрудник ответственный.
    """
    blocking_relations = dict()

    # Проверяем на руководителя:
    blocking_relations['director'] = contractor_profile.director
    organization = contractor_profile.contractor
    profile = contractor_profile.user
    # Проверяем является ли единственным администратором:
    from contractor_permissions.models import AccessGroupModel, AccessGroupMemberThroughModel
    admin_access_group_members = AccessGroupMemberThroughModel.objects.filter(
        access_group__code='admin',
        member__contractor=organization,
    ).values_list('member__user', flat=True)
    if admin_access_group_members.count() == 1 and admin_access_group_members[0] == profile.pk:
        blocking_relations['admin'] = True
    else:
        blocking_relations['admin'] = False

    # Руководитель (основатель) проекта:
    from bpms.workgroups.models import WorkgroupModel, WorkgroupMembersModel
    projects_founder_id = WorkgroupMembersModel.objects.filter(
        is_active=True,
        work_group__is_project=True,
        work_group__organization=organization,
        member=profile,
        membership_role__code='FOUNDER',
    ).values_list('work_group', flat=True)
    projects = list(
        WorkgroupModel.objects.filter(
            pk__in=projects_founder_id,
            is_active=True
        ).order_by('name')
    )
    blocking_relations['projects'] = projects

    # Руководитель (основатель) команды:
    workgroup_founder_id = WorkgroupMembersModel.objects.filter(
        is_active=True,
        work_group__is_project=False,
        work_group__organization=organization,
        member=profile,
        membership_role__code='FOUNDER',
    ).values_list('work_group', flat=True)
    workgroups = list(
        WorkgroupModel.objects.filter(
            pk__in=workgroup_founder_id,
            is_active=True
        ).order_by('name', )
    )
    blocking_relations['workgroups'] = workgroups

    # Чаты проектов:
    from bpms.chat.models import ChatModel, MemberModel
    chat_uid_list = WorkgroupModel.objects.filter(
        is_active=True,
        workgroupmembersmodel__is_active=True,
        workgroupmembersmodel__member=profile,
        workgroupmembersmodel__membership_request_status__code='APPROVED',
        with_chat=True,
        linked_chat__isnull=False,
    ).distinct().values_list('linked_chat', flat=True)
    chats = list(
        ChatModel.objects.filter(
            is_active=True,
            chat_uid__in=chat_uid_list,
            member__user=profile,
            member__is_active=True,
            member__is_moderator=True
        ).annotate(
            moderator_count=Count('member', filter=Q(member__is_moderator=True))
        ).filter(moderator_count=1).order_by('name')
    )
    blocking_relations['chats'] = chats

    # Постановщик/ответственный задачи:
    from bpms.tasks.models import TaskModel, TaskStatusTypeModel
    not_complete_statuses = TaskStatusTypeModel.objects.filter(
        is_active=True,
        task_type='task',
        is_complete=False
    ).values_list('task_status', flat=True)
    tasks = list(
        TaskModel.objects.filter(
            Q(owner=profile) | Q(operator=profile),
            is_active=True,
            task_type='task',
            organization=organization,
            status_id__in=not_complete_statuses,
        ).distinct().order_by('counter', 'name', ).distinct()
    )
    blocking_relations['tasks'] = tasks

    # Ответственный в обращениях:
    from help_desk.models import HelpDeskTicketModel
    from help_desk.utils import get_completed_statuses_id
    tickets = list(
        HelpDeskTicketModel.objects.filter(
            customer_card__org_admin=organization,
            specialist=profile,
            is_active=True,
        ).exclude(status_id__in=get_completed_statuses_id()).order_by('number', 'name')
    )
    blocking_relations['tickets'] = tickets

    return blocking_relations


def get_non_blocking_relations(contractor_profile):
    organization = contractor_profile.contractor
    profile = contractor_profile.user
    non_blocking_relations = dict()

    # Участник проекта:
    from bpms.workgroups.models import WorkgroupModel, WorkgroupMembersModel
    projects_member_id = WorkgroupMembersModel.objects.filter(
        is_active=True,
        work_group__is_project=True,
        work_group__organization=organization,
        member=profile,
    ).exclude(
        membership_role__code='MODERATOR',
    ).values_list('work_group', flat=True)
    projects = list(
        WorkgroupModel.objects.filter(
            pk__in=projects_member_id,
            is_active=True
        ).order_by('name',)
    )
    non_blocking_relations['projects'] = projects

    # Участник команды
    projects_member_id = WorkgroupMembersModel.objects.filter(
        is_active=True,
        work_group__is_project=False,
        work_group__organization=organization,
        member=profile,
    ).exclude(
        membership_role__code='MODERATOR',
    ).values_list('work_group', flat=True)
    projects = list(
        WorkgroupModel.objects.filter(
            pk__in=projects_member_id,
            is_active=True
        ).order_by('name',)
    )
    non_blocking_relations['workgroups'] = projects

    # Наблюдатель/соисполнитель задач:
    from bpms.tasks.models import TaskModel, TaskStatusTypeModel
    not_complete_statuses = TaskStatusTypeModel.objects.filter(
        is_active=True,
        task_type='task',
        is_complete=False
    ).values_list('task_status', flat=True)
    tasks = list(
        TaskModel.objects.filter(
            Q(visors=profile) | Q(cooperators=profile),
            is_active=True,
            task_type='task',
            organization=organization,
            status_id__in=not_complete_statuses,
        ).distinct().order_by('counter', 'name', ).distinct()
    )
    non_blocking_relations['tasks'] = tasks

    # Наблюдатель в обращениях:
    from help_desk.models import HelpDeskTicketModel
    from help_desk.utils import get_completed_statuses_id
    tickets = list(
        HelpDeskTicketModel.objects.filter(
            customer_card__org_admin=organization,
            visors=profile,
            is_active=True,
        ).exclude(status_id__in=get_completed_statuses_id()).order_by('number', 'name')
    )
    non_blocking_relations['tickets'] = tickets
    return non_blocking_relations

