from uuid import UUID
from datetime import timedelta
from django.db.models import Q
from django.db.models.functions import Cast
from django.db.models import TextField
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.cache import cache

from rest_framework import exceptions as drf_exceptions

from common.utils import use_access_groups, get_my_access_groups, get_tariff_section_codes, get_available_section_codes

from billing.models import ContractorTariffModel


from common.current_profile.middleware import get_current_authenticated_profile

from users.models import ProfileModel

from . import models


def check_contractor_permission(user_id, contractor_id, permission_type_code, aux_condition_id):
    """Вызывает ошибку, если пользователь (user_id) не имеет прав (permission_type_code) в организации (contractor_id)."""
    if isinstance(permission_type_code, str):
        permission_type_code = (permission_type_code,)
    if use_access_groups(user_id):
        try:
            profile = ProfileModel.objects.get(is_active=True, temporary_blocked=False, pk=user_id,)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.PermissionDenied()
        tariff_section_codes = get_tariff_section_codes(profile)
        if not models.AccessGroupModel.objects.filter(
            is_active=True,
            app_section_roles__app_section_id__in=tariff_section_codes,
            app_section_roles__permission_type_id__in=permission_type_code,
            members__contractor_id=contractor_id,
            members__user_id=profile.pk,
        ).exists():
            raise drf_exceptions.PermissionDenied()
    else:
        if not models.ContractorPermissionModel.objects.filter(
                Q(aux_conditions=aux_condition_id) | Q(aux_conditions__isnull=True),
                permission_type_id__in=permission_type_code,
                contractor_permission_role__contractor_profiles__user=user_id,
                contractor_permission_role__contractor_id=contractor_id,
                contractor_permission_role__is_active=True,
        ).exists():
            raise drf_exceptions.PermissionDenied()


def contractors_where_user_has_permission(user_id, permission_type_code, aux_condition_id):
    """Возвращает кортеж организаций, где пользователь имеет определенный вид разрешений."""
    if isinstance(permission_type_code, str):
        permission_type_code = (permission_type_code,)
    if use_access_groups(user_id):
        try:
            profile = ProfileModel.objects.get(is_active=True, temporary_blocked=False, pk=user_id,)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.PermissionDenied()
        tariff_section_codes = get_tariff_section_codes(profile)
        contractor_ids = set(models.AccessGroupModel.objects.filter(
            is_active=True,
            app_section_roles__app_section_id__in=tariff_section_codes,
            app_section_roles__permission_type_id__in=permission_type_code,
            members__user_id=user_id,
            ).values_list('members__contractor_id', flat=True).distinct())
        return tuple(contractor_ids)
    else:
        contractors = models.ContractorPermissionModel.objects.filter(
                Q(aux_conditions=aux_condition_id) | Q(aux_conditions__isnull=True),
                permission_type_id__in=permission_type_code,
                contractor_permission_role__contractor_profiles__user=user_id,
                contractor_permission_role__is_active=True,
                ).values_list('contractor_permission_role__contractor_id', flat=True)
        return tuple(contractors)


def users_that_have_permission_in_contractors(contractor_ids, permission_type_code, aux_condition_id):
    """Возвращает set пользователей, имеющих определенные права в организациях, переданных в списке"""
    if isinstance(contractor_ids, str):
        contractor_ids = (contractor_ids,)
    if use_access_groups():
        if isinstance(permission_type_code, str):
            permission_type_code = (permission_type_code,)
        contractor_tariffs = get_tariffs_id_by_contractors(contractor_ids)
        user_ids = set(models.AccessGroupModel.objects.filter(
            is_active=True,
            app_section_roles__app_section__tariffs__in=contractor_tariffs,
            app_section_roles__permission_type_id__in=permission_type_code,
            members__contractor_id__in=contractor_ids,
            ).values_list('members__user_id', flat=True).distinct())
        return user_ids
    else:
        users = models.ContractorPermissionModel.objects.filter(
                Q(aux_conditions=aux_condition_id) | Q(aux_conditions__isnull=True),
                permission_type_id=permission_type_code,
                contractor_permission_role__contractor_id__in=contractor_ids,
                contractor_permission_role__is_active=True,
        ).values_list('contractor_permission_role__contractor_profiles__user', flat=True)
        return set(users)


def users_that_have_app_section_role_in_contractors(contractor_ids, app_section_code, role=None):
    """Возвращает set пользователей, имеющих доступ к определенному разделу приложения в определенной роли.
    contractor_ids - список организаций
    app_section_code - код раздела приложения (code из таблицы AppSectionModel. Например, okr, sports-facilities и т.д.)
    role - код роли (admin, worker). Если не передан, то возвращаются все, кроме banned (Доступ запрещен).
    Аналог users_that_have_permission_in_contractors, только на вход принимает не старый permission_type_code, а новый app_section_code и role.
    """
    if isinstance(contractor_ids, str) or isinstance(contractor_ids, UUID):
        contractor_ids = (contractor_ids,)
    if role:
        lookup = Q(app_section_roles__role_id=role)
    else:
        lookup = Q(app_section_roles__role__access_level__lt=100)
    contractor_tariffs = get_tariffs_id_by_contractors(contractor_ids)
    user_ids = set(models.AccessGroupModel.objects.filter(
        lookup,
        is_active=True,
        app_section_roles__app_section__tariffs__in=contractor_tariffs,
        app_section_roles__app_section_id=app_section_code,
        members__contractor_id__in=contractor_ids,
        ).values_list('members__user_id', flat=True).distinct())
    return user_ids


def check_user_app_section_role_permission(profile_id, app_section_code, contractor_ids=None, role=None):
    """Проверяет, имеет ли пользователь доступ к разделу приложения (администратор или сотрудник)."""
    try:
        profile = ProfileModel.objects.get(is_active=True, temporary_blocked=False, pk=profile_id,)
    except (ObjectDoesNotExist, ValidationError):
        raise drf_exceptions.PermissionDenied()

    if not contractor_ids:
        contractor_ids = profile.my_organizations
    if isinstance(contractor_ids, str) or isinstance(contractor_ids, UUID):
        contractor_ids = (contractor_ids,)
    if role:
        lookup = Q(app_section_roles__role_id=role)
    else:
        lookup = Q(app_section_roles__role__access_level__lt=100)
    contractor_tariffs = get_tariffs_id_by_contractors(contractor_ids)
    return models.AccessGroupModel.objects.filter(
        lookup,
        is_active=True,
        app_section_roles__app_section__tariffs__in=contractor_tariffs,
        app_section_roles__app_section_id=app_section_code,
        members__contractor_id__in=contractor_ids,
        members__user_id=profile_id,
        ).exists()


def contractors_where_user_has_app_section_role_permission(profile_id, app_section_code, contractor_ids=None, role=None):
    """Возвращает кортеж организаций (contractor_id), где пользователь имеет доступ к разделу приложения.

    Логика аналогична `check_user_app_section_role_permission`, но вместо exists() возвращает весь список совпавших организаций.
    """
    try:
        profile = ProfileModel.objects.get(is_active=True, temporary_blocked=False, pk=profile_id,)
    except (ObjectDoesNotExist, ValidationError):
        raise drf_exceptions.PermissionDenied()

    if not contractor_ids:
        contractor_ids = profile.my_organizations
    if isinstance(contractor_ids, str) or isinstance(contractor_ids, UUID):
        contractor_ids = (contractor_ids,)

    if role:
        lookup = Q(app_section_roles__role_id=role)
    else:
        lookup = Q(app_section_roles__role__access_level__lt=100)

    contractor_tariffs = get_tariffs_id_by_contractors(contractor_ids)
    contractor_ids_qs = models.AccessGroupModel.objects.filter(
        lookup,
        is_active=True,
        app_section_roles__app_section__tariffs__in=contractor_tariffs,
        app_section_roles__app_section_id=app_section_code,
        members__contractor_id__in=contractor_ids,
        members__user_id=profile_id,
    ).values_list('members__contractor_id', flat=True).distinct()

    return tuple(contractor_ids_qs)


def contractors_where_im_director(user):
    """Возвращает кортеж организаций, где пользователь является директором."""
    contractors = user.contractor_profile.filter(director=True).values_list('contractor', flat=True)
    return tuple(contractors)


def get_tariffs_id_by_contractors(contractors):
    """Возвращает список id тарифов, которые доступны организации. С кэшированием."""
    now = timezone.now()
    from users.utils import get_ancestor_departments_related_organizations

    tariffs_set = set()
    SENTINEL = object()
    for contractor in contractors:
        cache_key = f'tariffs_id_by_contractor_{str(contractor)}'
        tariffs = cache.get(cache_key, default=SENTINEL)
        if tariffs is SENTINEL:
            # ключа в кэше нет вообще
            ancestors = get_ancestor_departments_related_organizations((contractor,), include_self=True,)
            tariffs = set(ContractorTariffModel.objects.filter(
                is_active=True,
                tariff__is_active=True,
                contractor__in=ancestors,
                date_start__lte=now,
                date_end__gte=now,
            ).values_list('tariff_id', flat=True))
            tariffs = [str(tariff_id) for tariff_id in tariffs]
            cache.set(cache_key, tariffs, timeout=timedelta(hours=1).total_seconds())
            tariffs_set.update(tariffs)
        else:
            # ключ есть, даже если tariffs == []
            tariffs_set.update(tariffs)
    return tariffs_set


def get_available_sections(contractor):
    """Возвращает queryset разделов, доступных для данной организации."""
    tariffs = get_tariffs_id_by_contractors((contractor,))
    app_sections = models.AppSectionModel.objects.filter(tariffs__in=tariffs).distinct().order_by('-is_main', 'sort', 'name',)
    return app_sections


def get_available_access_groups(contractor):
    """Возвращает queryset групп доступа, доступных для данной организации"""
    tariffs = get_tariffs_id_by_contractors((contractor,))
    access_groups = models.AccessGroupModel.objects.filter(
        Q(contractor=contractor) | Q(tariffs__in=tariffs),
        is_active=True,
    ).distinct()
    return access_groups


def validate_access_group_members(data, instance=None):
    members = data.get('members')
    if members:
        if instance:
            contractor = instance.contractor
        else:
            contractor = data.get('contractor')
        contractor_members = contractor.profiles.all().values_list('pk', flat=True)
        for each in members:
            if each.pk not in contractor_members:
                raise drf_exceptions.ValidationError(f'Member {each.full_name} not in {contractor.name}')


def get_section_codes_by_slug(slug: str) -> set:
    return set(models.AppSectionModel.objects.filter(backend_slug=slug).values_list('code', flat=True))
