import re
from uuid import UUID
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rest_framework import exceptions as drf_exceptions

from common.current_profile.middleware import user_context
from common.utils import filter_by_search
from common.catalogs.models import ContractorModel
from users.utils import get_ancestor_departments_related_organizations

from bpms.processes import models as process_models


WORKFLOW_REQUEST_INTENT_TYPE = "create_workflow_request"
WORKFLOW_REQUEST_TARGET_MODEL = "processes.WorkflowRequestModel"
REQUEST_APPROVAL_PERMISSION_TYPES = ("request_approvals_manager", "request_approvals_admin")


def is_workflow_request_intent(intent_obj) -> bool:
    intent_type_id = getattr(intent_obj, "intent_type_id", "") or ""
    if intent_type_id == WORKFLOW_REQUEST_INTENT_TYPE:
        return True

    metadata = getattr(getattr(intent_obj, "intent_type", None), "metadata", {}) or {}
    target_info = metadata.get("target", {}) if isinstance(metadata, dict) else {}
    return target_info.get("model") == WORKFLOW_REQUEST_TARGET_MODEL


def _profile_from_request(request):
    profile = getattr(request, "profile", None)
    if profile is not None:
        return profile

    user = getattr(request, "user", None)
    profile = getattr(user, "profile", None)
    if profile is None:
        raise drf_exceptions.ValidationError("Не удалось определить профиль пользователя.")
    return profile


def _is_empty(value) -> bool:
    if value in (None, "", [], {}):
        return True
    if isinstance(value, str) and value.strip().lower() in {"null", "none", "не указано"}:
        return True
    return False


def _scalar(value):
    if isinstance(value, dict):
        for key in ("id", "code", "name", "repr", "title"):
            if not _is_empty(value.get(key)):
                return value.get(key)
        return None
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _intent_value(intent_obj, field_name, *, prefer_resolved=False):
    raw_data = intent_obj.raw_data if isinstance(intent_obj.raw_data, dict) else {}
    resolved_data = intent_obj.resolved_data if isinstance(intent_obj.resolved_data, dict) else {}

    resolved_value = resolved_data.get(field_name)
    if prefer_resolved and not _is_empty(resolved_value):
        return resolved_value

    raw_value = raw_data.get(field_name)
    if not _is_empty(raw_value):
        return raw_value
    return resolved_value


def _normalize_text(value) -> str:
    value = _scalar(value)
    return str(value or "").strip()


def resolve_workflow_request_type(raw_value):
    text = _normalize_text(raw_value).lower()
    request_type_model = process_models.WorkflowRequestTypeModel

    def _by_code(code):
        exact = request_type_model.objects.filter(is_active=True, code=code).first()
        if exact:
            return exact
        if code == "finance":
            prefixed = request_type_model.objects.filter(is_active=True, code__startswith="finance").order_by("sort", "code").first()
            if prefixed:
                return prefixed
        return None

    aliases = (
        ("finance", ("finance", "финанс", "деньг", "оплат", "аванс", "счет", "счёт", "под отчет", "под отчёт")),
        ("trip", ("trip", "командиров", "поездк")),
        ("vacation", ("vacation", "отпуск", "отгул")),
        ("other", ("other", "проч", "друг")),
    )
    for code, markers in aliases:
        if any(marker in text for marker in markers):
            request_type = _by_code(code)
            if request_type:
                return request_type

    if text:
        exact = request_type_model.objects.filter(is_active=True).filter(
            Q(code__iexact=text) | Q(name__iexact=text)
        ).first()
        if exact:
            return exact

        contains = request_type_model.objects.filter(is_active=True, name__icontains=text).first()
        if contains:
            return contains

    raise drf_exceptions.ValidationError("Укажите тип заявки: финансы, командировка, отпуск или другое.")


def _request_approval_organization_queryset(profile):
    return ContractorModel.get_request_approval_select_queryset(profile)


def resolve_workflow_request_organization(raw_value, profile):
    qs = _request_approval_organization_queryset(profile)
    text = _normalize_text(raw_value)

    if text:
        try:
            UUID(text)
        except (TypeError, ValueError):
            exact = None
        else:
            exact = qs.filter(pk=text).first()
            if exact:
                return exact

        name_match = qs.filter(Q(name__iexact=text) | Q(full_name__iexact=text))
        count = name_match.count()
        if count == 1:
            return name_match.first()
        if count > 1:
            names = ", ".join(name_match.values_list("name", flat=True)[:5])
            raise drf_exceptions.ValidationError(
                f"Найдено несколько организаций для заявки: {names}. Уточните организацию."
            )

        name_match = qs.filter(Q(name__icontains=text) | Q(full_name__icontains=text))
        count = name_match.count()
        if count == 1:
            return name_match.first()
        if count > 1:
            names = ", ".join(name_match.values_list("name", flat=True)[:5])
            raise drf_exceptions.ValidationError(
                f"Найдено несколько организаций для заявки: {names}. Уточните организацию."
            )

        if len(text) >= 3:
            filtered = filter_by_search(text, ContractorModel, qs)
            count = filtered.count()
            if count == 1:
                return filtered.first()
            if count > 1:
                names = ", ".join(filtered.values_list("name", flat=True)[:5])
                raise drf_exceptions.ValidationError(
                    f"Найдено несколько организаций для заявки: {names}. Уточните организацию."
                )

        raise drf_exceptions.ValidationError(f"Организация для заявки не найдена: {text}.")

    count = qs.count()
    if count == 1:
        return qs.first()
    if count > 1:
        names = ", ".join(qs.values_list("name", flat=True)[:5])
        raise drf_exceptions.ValidationError(
            f"Укажите организацию для заявки. Доступные варианты: {names}."
        )
    raise drf_exceptions.PermissionDenied("Нет организаций с правом создания заявок на согласование.")


def _normalize_datetime(value, *, default_time="18:00:00"):
    value = _normalize_text(value)
    if not value:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value}T{default_time}"

    parsed = parse_datetime(value)
    if parsed:
        return parsed.isoformat()

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
        return f"{value}:00"

    return value


def _normalize_decimal(value):
    value = _normalize_text(value)
    if not value:
        return None

    value = value.replace("\u00a0", " ").replace(",", ".")
    match = re.search(r"-?\d+(?:\s\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?", value)
    if not match:
        return None

    number = match.group(0).replace(" ", "")
    try:
        return str(Decimal(number))
    except (InvalidOperation, ValueError):
        return None


def _normalize_bool(value):
    if isinstance(value, bool):
        return value
    text = _normalize_text(value).lower()
    if not text:
        return False
    return any(marker in text for marker in ("true", "1", "да", "yes", "под отчет", "под отчёт"))


def build_workflow_request_route_payload(request_type_code, organization_id):
    contractors = get_ancestor_departments_related_organizations((organization_id,), include_self=True)
    templates = list(
        process_models.WorkflowRequestRouteTemplateModel.objects.filter(
            is_active=True,
            request_type_id=request_type_code,
        ).order_by("sort")
    )

    route = []
    ambiguous_positions = []
    empty_required_positions = []

    for template in templates:
        raw_user_ids = list(
            process_models.WorkflowPositionUserModel.objects.filter(
                workflow_position_id=template.workflow_position_id,
                contractor_profile__contractor_id__in=contractors,
            )
            .order_by(
                "contractor_profile__user__user__last_name",
                "contractor_profile__user__user__first_name",
            )
            .values_list("contractor_profile__user", flat=True)
        )
        user_ids = []
        seen_user_ids = set()
        for user_id in raw_user_ids:
            if user_id in seen_user_ids:
                continue
            seen_user_ids.add(user_id)
            user_ids.append(user_id)

        if len(user_ids) > 1:
            ambiguous_positions.append(template.workflow_position.name)
        elif not user_ids and not template.not_require_approval:
            empty_required_positions.append(template.workflow_position.name)

        route.append({
            "position": template.workflow_position_id,
            "users": user_ids if len(user_ids) == 1 else [],
        })

    if ambiguous_positions:
        raise drf_exceptions.ValidationError(
            "В маршруте согласования несколько кандидатов на позиции: "
            + ", ".join(ambiguous_positions)
            + ". Уточните согласующих вручную в заявке."
        )

    if empty_required_positions:
        raise drf_exceptions.ValidationError(
            "В маршруте согласования нет пользователей на позициях: "
            + ", ".join(empty_required_positions)
            + ". Настройте маршрут согласования."
        )

    return route


def build_workflow_request_payload(intent_obj, request):
    profile = _profile_from_request(request)
    request_type = resolve_workflow_request_type(_intent_value(intent_obj, "request_type"))
    organization = resolve_workflow_request_organization(
        _intent_value(intent_obj, "organization", prefer_resolved=True),
        profile,
    )

    payload = {
        "request_type": request_type.code,
        "organization": organization.pk,
        "description": _normalize_text(_intent_value(intent_obj, "description")),
        "dead_line": _normalize_datetime(_intent_value(intent_obj, "dead_line")),
        "money_under_report": _normalize_bool(_intent_value(intent_obj, "money_under_report")),
    }

    project_id = _scalar(_intent_value(intent_obj, "project", prefer_resolved=True))
    if not _is_empty(project_id):
        payload["project"] = project_id

    amount_requested = _normalize_decimal(_intent_value(intent_obj, "amount_requested"))
    if request_type.code == "finance" and amount_requested is None:
        raise drf_exceptions.ValidationError("Укажите сумму финансовой заявки.")
    if amount_requested is not None:
        payload["amount_requested"] = amount_requested

    event_date_start = _normalize_datetime(_intent_value(intent_obj, "event_date_start"), default_time="09:00:00")
    if event_date_start:
        payload["event_date_start"] = event_date_start

    event_date_end = _normalize_datetime(_intent_value(intent_obj, "event_date_end"), default_time="18:00:00")
    if event_date_end:
        payload["event_date_end"] = event_date_end

    payload["route"] = build_workflow_request_route_payload(
        request_type_code=request_type.code,
        organization_id=organization.pk,
    )
    return payload


def materialize_workflow_request_intent(intent_obj, request):
    payload = build_workflow_request_payload(intent_obj, request)
    serializer_class = process_models.WorkflowRequestModel.get_serializer_class(action="create")

    with transaction.atomic():
        serializer = serializer_class(data=payload, context={"request": request})
        actor_user = getattr(request, "user", None)
        context_guard = user_context(actor_user) if actor_user else transaction.atomic()
        with context_guard:
            serializer.is_valid(raise_exception=True)
            created_object = serializer.save()

        intent_obj.related_object = created_object
        intent_obj.status_id = "done"
        intent_obj.errors = []
        intent_obj.save(update_fields=["related_object", "status", "errors"])

    return created_object
