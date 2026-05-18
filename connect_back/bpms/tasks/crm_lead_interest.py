import json
import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.html import strip_tags
from django.utils import timezone

from common.catalogs.models import NomenclatureModel
from bpms.chat_ai.models import AIChatRoleModel
from bpms.chat_ai.utils.messages import invoke_role_prompt
from bpms.tasks import models as task_models


logger = logging.getLogger(__name__)


CRM_LEAD_INTEREST_ROLE = "crm_lead_interest_analyzer"
MAX_NEED_COMMENT_LENGTH = 1023
GENERIC_NEED_COMMENT_MARKERS = (
    "почему выбрано",
    "что уточнить",
    "создана из контекста лида",
    "точную товарную позицию",
    "товарную позицию нужно уточнить",
)


CRM_LEAD_INTEREST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "has_interest": {"type": "boolean"},
        "interest_name": {"type": "string"},
        "interest_description": {"type": "string"},
        "needs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "goods_id": {"type": ["string", "null"]},
                    "quantity": {"type": ["number", "string", "null"]},
                    "price": {"type": ["number", "string", "null"]},
                    "comment": {"type": ["string", "null"]},
                },
                "required": ["name", "goods_id", "quantity", "price", "comment"],
            },
        },
    },
    "required": ["has_interest", "interest_name", "interest_description", "needs"],
}


def _message_text(message):
    parts = []
    if message.email_subject:
        parts.append(f"Тема: {message.email_subject}")
    if message.text:
        parts.append(message.text)
    return "\n".join(parts).strip()


def build_lead_context(ticket):
    messages = []
    through_qs = (
        ticket.message_ticket_through
        .select_related("message")
        .filter(message__is_active=True)
        .order_by("message__message_date", "message__created_at")[:20]
    )
    for rel in through_qs:
        message = rel.message
        if not message:
            continue
        text = _message_text(message)
        if text:
            messages.append({
                "date": (message.message_date or message.created_at).isoformat() if (message.message_date or message.created_at) else "",
                "from_support": bool(message.is_help_desk),
                "text": text,
            })

    customer_card = ticket.customer_card
    contact_person = ticket.contact_person
    return {
        "id": str(ticket.pk),
        "number": ticket.number,
        "name": ticket.name,
        "description": ticket.description,
        "channel": getattr(ticket.channel, "name", "") if ticket.channel_id else "",
        "status": getattr(ticket.status, "name", "") if ticket.status_id else "",
        "created_at": ticket.created_at.isoformat() if ticket.created_at else "",
        "customer_card": {
            "id": str(customer_card.pk),
            "name": customer_card.name,
            "external_customer": str(customer_card.external_customer_id or ""),
        } if customer_card else None,
        "contact_person": {
            "id": str(contact_person.pk),
            "name": contact_person.get_display_name() if hasattr(contact_person, "get_display_name") else str(contact_person),
            "phone": getattr(contact_person, "phone", ""),
            "email": getattr(contact_person, "email", ""),
        } if contact_person else None,
        "messages": messages,
    }


def _get_user_organization(ticket, request):
    customer_card = ticket.customer_card
    if customer_card and customer_card.org_admin_id:
        return customer_card.org_admin
    profile = request.user.profile
    return profile.current_contractor


def get_nomenclature_candidates(request, organization, limit=120):
    base_qs = NomenclatureModel.get_queryset(request)
    qs = base_qs
    if organization:
        org_qs = base_qs.filter(contractor_id=organization.pk)
        if org_qs.exists():
            qs = org_qs
    qs = qs.select_related("base_measure_unit").order_by("name")[:limit]
    result = []
    for item in qs:
        result.append({
            "id": str(item.pk),
            "name": item.name,
            "name_short": item.name_short,
            "article_number": item.article_number,
            "measure_unit": getattr(item.base_measure_unit, "name_short", "") if item.base_measure_unit_id else "",
            # CRM: цену передаем в LLM-контекст, чтобы потребность сразу
            # получила расчетную стоимость из каталога товаров и услуг.
            "price": str(item.price_by_catalog or Decimal("0")),
        })
    return result


def _decimal_or_default(value, default):
    if value in (None, ""):
        return Decimal(default)
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _normalize(value):
    return (value or "").lower().replace("ё", "е")


def _compact_text(value):
    return " ".join(strip_tags(str(value or "")).split())


def _clip_comment(value):
    return _compact_text(value)[:MAX_NEED_COMMENT_LENGTH].strip()


def _is_generic_need_comment(comment):
    normalized = _normalize(comment)
    if not normalized:
        return True
    return any(marker in normalized for marker in GENERIC_NEED_COMMENT_MARKERS)


def _extract_lead_interest_text(ticket):
    parts = []
    seen = []

    def append_part(value):
        text = _compact_text(value)
        key = _normalize(text)
        if not key:
            return
        if any(key in prev or prev in key for prev in seen):
            return
        parts.append(text)
        seen.append(key)

    for value in (ticket.name, ticket.description):
        append_part(value)

    through_qs = (
        ticket.message_ticket_through
        .select_related("message")
        .filter(message__is_active=True)
        .order_by("message__message_date", "message__created_at")[:20]
    )
    client_messages = []
    fallback_messages = []
    for rel in through_qs:
        message = rel.message
        if not message:
            continue
        text = _compact_text(_message_text(message))
        key = _normalize(text)
        if not key or any(key in prev or prev in key for prev in seen):
            continue
        target = fallback_messages if message.is_help_desk else client_messages
        target.append(text)
        seen.append(key)

    parts.extend(client_messages[:3] or fallback_messages[:2])
    return _clip_comment(" ".join(parts))


def _ensure_need_comments(ticket, analysis):
    needs = analysis.get("needs") or []
    if not needs:
        return analysis

    lead_interest_text = _extract_lead_interest_text(ticket)
    result = dict(analysis)
    normalized_needs = []
    for need in needs:
        normalized_need = dict(need)
        comment = _clip_comment(normalized_need.get("comment"))
        if _is_generic_need_comment(comment):
            comment = lead_interest_text or _clip_comment(normalized_need.get("name"))
        normalized_need["comment"] = comment
        normalized_needs.append(normalized_need)
    result["needs"] = normalized_needs
    return result


def _match_goods(need, candidates):
    goods_id = need.get("goods_id")
    if goods_id and any(item["id"] == goods_id for item in candidates):
        return goods_id

    query = _normalize(" ".join([
        str(need.get("name") or ""),
        str(need.get("comment") or ""),
    ]))
    words = [word for word in query.replace("/", " ").replace("-", " ").split() if len(word) >= 4]
    best = None
    best_score = 0
    for item in candidates:
        haystack = _normalize(" ".join([
            item.get("name", ""),
            item.get("name_short", ""),
            item.get("article_number", ""),
        ]))
        score = sum(1 for word in words if word in haystack)
        if score > best_score:
            best = item
            best_score = score
    return best["id"] if best and best_score else None


def fallback_analysis(ticket):
    text = " ".join(filter(None, [ticket.name, ticket.description]))
    return {
        "has_interest": bool(text.strip()),
        "interest_name": ticket.name or f"Интерес из лида {ticket.number}",
        "interest_description": ticket.description or ticket.name or "",
        "needs": [],
        "analysis_source": "fallback",
    }


def build_interest_context(task):
    customer_card = task.customer_card
    potential_contractor = task.potential_contractor
    contractor = task.contractor
    contract = task.contract
    return {
        "id": str(task.pk),
        "counter": task.counter,
        "name": task.name,
        "description": task.description,
        "status": getattr(task.status, "name", "") if task.status_id else "",
        "created_at": task.created_at.isoformat() if task.created_at else "",
        "customer_card": {
            "id": str(customer_card.pk),
            "name": customer_card.name,
            "external_customer": str(customer_card.external_customer_id or ""),
        } if customer_card else None,
        "potential_contractor": {
            "id": str(potential_contractor.pk),
            "name": potential_contractor.name,
            "company_name": potential_contractor.company_name,
            "phone": potential_contractor.phone,
            "email": potential_contractor.email,
        } if potential_contractor else None,
        "legacy_contractor": {
            "id": str(contractor.pk),
            "name": contractor.name,
        } if contractor else None,
        "contract": {
            "id": str(contract.pk),
            "name": str(contract),
        } if contract else None,
    }


def fallback_interest_analysis(task):
    text = " ".join(filter(None, [task.name, task.description]))
    return {
        "has_interest": bool(text.strip()),
        "interest_name": task.name or f"Интерес {task.counter or task.pk}",
        "interest_description": task.description or task.name or "",
        "needs": [],
        "analysis_source": "fallback",
    }


def analyze_lead(ticket, request, candidates):
    context = {
        "lead_context_json": json.dumps(build_lead_context(ticket), ensure_ascii=False, indent=2),
        "nomenclature_json": json.dumps(candidates, ensure_ascii=False, indent=2),
        "current_date": timezone.now().date().isoformat(),
    }
    user_message = ticket.description or ticket.name

    try:
        AIChatRoleModel.objects.get(code=CRM_LEAD_INTEREST_ROLE)
        result = invoke_role_prompt(
            user_message=user_message,
            role_code=CRM_LEAD_INTEREST_ROLE,
            context=context,
            consumer=ticket,
            format_schema=CRM_LEAD_INTEREST_SCHEMA,
            url_query_param=f"crm_lead_interest&ticket={ticket.pk}",
        )
    except Exception as exc:
        logger.exception("CRM lead LLM analysis failed for ticket %s", ticket.pk)
        result = fallback_analysis(ticket)
        result["analysis_error"] = str(exc)
        return result

    if not isinstance(result, dict):
        result = fallback_analysis(ticket)
        result["analysis_error"] = "LLM returned non-object response"
        return result

    result.setdefault("needs", [])
    result.setdefault("analysis_source", "llm")
    return result


def analyze_interest(task, request, candidates):
    context = {
        "lead_context_json": json.dumps(build_interest_context(task), ensure_ascii=False, indent=2),
        "nomenclature_json": json.dumps(candidates, ensure_ascii=False, indent=2),
        "current_date": timezone.now().date().isoformat(),
    }
    user_message = task.description or task.name

    try:
        AIChatRoleModel.objects.get(code=CRM_LEAD_INTEREST_ROLE)
        result = invoke_role_prompt(
            user_message=user_message,
            role_code=CRM_LEAD_INTEREST_ROLE,
            context=context,
            consumer=task,
            format_schema=CRM_LEAD_INTEREST_SCHEMA,
            url_query_param=f"crm_interest_needs&task={task.pk}",
        )
    except Exception as exc:
        logger.exception("CRM interest LLM analysis failed for task %s", task.pk)
        result = fallback_interest_analysis(task)
        result["analysis_error"] = str(exc)
        return result

    if not isinstance(result, dict):
        result = fallback_interest_analysis(task)
        result["analysis_error"] = "LLM returned non-object response"
        return result

    result.setdefault("needs", [])
    result.setdefault("analysis_source", "llm")
    return result


def _ensure_forced_need(ticket, analysis, force_create):
    if not force_create or analysis.get("needs"):
        return analysis

    lead_text = _extract_lead_interest_text(ticket)
    if not lead_text:
        return analysis

    result = dict(analysis)
    result["has_interest"] = True
    if not result.get("interest_name"):
        result["interest_name"] = ticket.name or f"Интерес из лида {ticket.number}"
    if not result.get("interest_description"):
        result["interest_description"] = ticket.description or ticket.name or ""
    result["needs"] = [{
        "name": result["interest_name"],
        "goods_id": None,
        "quantity": 1,
        "price": None,
        "comment": lead_text,
    }]
    result["forced_need_created"] = True
    return result


def _extract_task_interest_text(task):
    parts = []
    for value in (
        task.name,
        task.description,
        getattr(task.customer_card, "name", ""),
        getattr(task.potential_contractor, "name", ""),
        getattr(task.potential_contractor, "company_name", ""),
    ):
        text = _compact_text(value)
        if text and text not in parts:
            parts.append(text)
    return _clip_comment(" ".join(parts))


def _ensure_forced_task_need(task, analysis, force_create):
    if not force_create or analysis.get("needs"):
        return analysis

    interest_text = _extract_task_interest_text(task)
    if not interest_text:
        return analysis

    result = dict(analysis)
    result["has_interest"] = True
    if not result.get("interest_name"):
        result["interest_name"] = task.name or f"Интерес {task.counter or task.pk}"
    if not result.get("interest_description"):
        result["interest_description"] = task.description or task.name or ""
    result["needs"] = [{
        "name": result["interest_name"],
        "goods_id": None,
        "quantity": 1,
        "price": None,
        "comment": interest_text,
    }]
    result["forced_need_created"] = True
    return result


def _ensure_task_need_comments(task, analysis):
    needs = analysis.get("needs") or []
    if not needs:
        return analysis

    interest_text = _extract_task_interest_text(task)
    result = dict(analysis)
    normalized_needs = []
    for need in needs:
        normalized_need = dict(need)
        comment = _clip_comment(normalized_need.get("comment"))
        if _is_generic_need_comment(comment):
            comment = interest_text or _clip_comment(normalized_need.get("name"))
        normalized_need["comment"] = comment
        normalized_needs.append(normalized_need)
    result["needs"] = normalized_needs
    return result


def create_interest_from_lead(ticket, request, *, force_create=True):
    """Создать интерес из лида и заполнить потребности по результату LLM-анализа."""
    if ticket.ticket_type_id != "lead":
        raise ValueError("Создать интерес можно только из лида.")

    existing = task_models.TaskModel.objects.filter(
        is_active=True,
        task_type_id="interest",
        reason=str(ticket.pk),
    ).order_by("-created_at").first()
    if existing:
        existing_needs = _needs_payload(existing)
        if not existing_needs:
            organization = _get_user_organization(ticket, request)
            candidates = get_nomenclature_candidates(request, organization)
            analysis = analyze_lead(ticket, request, candidates)
            analysis = _ensure_forced_need(ticket, analysis, force_create)
            analysis = _ensure_need_comments(ticket, analysis)
            needs = _create_needs(existing, analysis, candidates)
            return {
                "created": False,
                "task": _task_payload(existing),
                "analysis": analysis,
                "needs": needs,
            }
        return {
            "created": False,
            "task": _task_payload(existing),
            "analysis": None,
            "needs": existing_needs,
        }

    organization = _get_user_organization(ticket, request)
    candidates = get_nomenclature_candidates(request, organization)
    analysis = analyze_lead(ticket, request, candidates)
    analysis = _ensure_forced_need(ticket, analysis, force_create)
    analysis = _ensure_need_comments(ticket, analysis)
    if not analysis.get("has_interest") and not force_create:
        return {
            "created": False,
            "task": None,
            "analysis": analysis,
            "needs": [],
        }

    profile = request.user.profile
    name = (analysis.get("interest_name") or ticket.name or f"Интерес из лида {ticket.number}")[:255]
    description = analysis.get("interest_description") or ticket.description or ticket.name or ""
    if ticket.description and ticket.description not in description:
        description = f"{description}\n\nИсходное описание лида:\n{ticket.description}".strip()

    with transaction.atomic():
        task = task_models.TaskModel.objects.create(
            name=name,
            description=description,
            task_type_id="interest",
            reason=str(ticket.pk),
            customer_card=ticket.customer_card,
            organization=organization,
            owner=profile,
            operator=ticket.specialist or profile,
            is_indefinite=True,
            priority=2,
        )

        needs = _create_needs(task, analysis, candidates)

    return {
        "created": True,
        "task": _task_payload(task),
        "analysis": analysis,
        "needs": needs,
    }


def analyze_interest_task(task, request, *, force_create=True, refresh=False):
    """Проанализировать существующий интерес и создать/обновить его потребности."""
    if task.task_type_id != "interest":
        raise ValueError("Потребности можно выявлять только для интереса.")

    existing_needs = _needs_payload(task)
    if existing_needs and not refresh:
        return {
            "created": False,
            "task": _task_payload(task),
            "analysis": None,
            "needs": existing_needs,
        }

    if refresh and existing_needs:
        task.interest_needs.filter(is_active=True).update(is_active=False, deleted_at=timezone.now())

    organization = task.organization or getattr(request.user.profile, "current_contractor", None)
    candidates = get_nomenclature_candidates(request, organization)
    analysis = analyze_interest(task, request, candidates)
    analysis = _ensure_forced_task_need(task, analysis, force_create)
    analysis = _ensure_task_need_comments(task, analysis)
    if not analysis.get("has_interest") and not force_create:
        return {
            "created": False,
            "task": _task_payload(task),
            "analysis": analysis,
            "needs": [],
        }

    with transaction.atomic():
        needs = _create_needs(task, analysis, candidates)

    return {
        "created": bool(needs),
        "task": _task_payload(task),
        "analysis": analysis,
        "needs": needs,
    }


def _create_needs(task, analysis, candidates):
    needs = []
    candidate_map = {item["id"]: item for item in candidates}
    for need in analysis.get("needs") or []:
        need_name = (need.get("name") or "").strip()
        goods_id = _match_goods(need, candidates)
        goods = NomenclatureModel.objects.filter(pk=goods_id, is_active=True).first() if goods_id else None
        price = _decimal_or_default(need.get("price"), "0")
        if goods and price <= 0:
            # CRM: если LLM сопоставила потребность с номенклатурой, но не дала
            # цену, берем текущую каталожную цену товара/услуги.
            price = goods.price_by_catalog or Decimal("0")
        obj = task_models.TaskInterestNeedModel.objects.create(
            task=task,
            goods=goods,
            name=need_name[:255],
            quantity=_decimal_or_default(need.get("quantity"), "1"),
            price=price,
            comment=_clip_comment(need.get("comment") or need_name),
        )
        payload = _need_payload(obj)
        if goods_id:
            payload["matched_from"] = candidate_map.get(goods_id)
        needs.append(payload)
    return needs


def _task_payload(task):
    return {
        "id": str(task.pk),
        "counter": task.counter,
        "name": task.name,
        "customer_card": str(task.customer_card_id or ""),
        "status": task.status_id,
    }


def _need_payload(need):
    return {
        "id": str(need.pk),
        "goods": str(need.goods_id or ""),
        "name": need.name,
        "quantity": str(need.quantity),
        "price": str(need.price),
        "amount": str(need.amount),
        "comment": need.comment,
    }


def _needs_payload(task):
    return [_need_payload(item) for item in task.interest_needs.filter(is_active=True)]
