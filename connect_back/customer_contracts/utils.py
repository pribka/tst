from crm import deals_models as crm_models
from help_desk.models import CustomerCardModel

from . import models


CONTRACT_STATUS_TO_DEAL_STAGE = {
    'lead': 'lead',
    'active': 'production',
    'on_pause': 'production',
    'completed': 'won',
}


def get_deal_stage_for_customer_contract(contract):
    stage_code = CONTRACT_STATUS_TO_DEAL_STAGE.get(getattr(contract.status, 'code', None))
    if not stage_code:
        if contract.is_signed or contract.is_exists:
            stage_code = 'production'
        else:
            stage_code = 'lead'
    return crm_models.DealStageModel.objects.filter(is_active=True, code=stage_code).first()


def get_probability_for_customer_contract(contract):
    if getattr(contract.status, 'code', None) == 'lead':
        return 30
    if contract.is_signed or contract.is_exists or getattr(contract.status, 'code', None) in ('active', 'on_pause', 'completed'):
        return 100
    return 50


def get_deal_name_for_customer_contract(contract):
    customer_name = ''
    if contract.customer_card_id:
        customer_name = getattr(contract.customer_card, 'full_name', None) or getattr(contract.customer_card, 'name', None) or ''
    number = (contract.number or '').strip()
    if number and customer_name:
        return f'{number} - {customer_name}'
    if number:
        return f'Контракт {number}'
    if customer_name:
        return f'Сделка: {customer_name}'
    return f'Контракт {contract.pk}'


def ensure_deal_for_customer_contract(contract):
    if contract.deal_id:
        return contract.deal

    stage = get_deal_stage_for_customer_contract(contract)
    deal = crm_models.DealModel.objects.create(
        author_id=contract.author_id,
        name=get_deal_name_for_customer_contract(contract),
        description='Сделка создана автоматически на основе контракта.',
        stage=stage,
        responsible_id=contract.author_id,
        customer_card_id=contract.customer_card_id,
        expected_amount=contract.amount or 0,
        probability=get_probability_for_customer_contract(contract),
        planned_close_date=contract.date_end or contract.contract_date,
    )
    models.CustomerContractModel.objects.filter(pk=contract.pk).update(deal=deal)
    contract.deal = deal
    return deal


def ensure_serviced_cards_for_customer_contract(contract):
    if not contract or not contract.pk:
        return {'created': 0, 'reactivated': 0}

    organization_id = getattr(contract, 'organization_id', None)
    external_customer_id = getattr(contract, 'external_customer_id', None)
    if not organization_id or not external_customer_id:
        return {'created': 0, 'reactivated': 0}

    external_customer = getattr(contract, 'external_customer', None)
    external_inn = (getattr(external_customer, 'inn', '') or '').strip()
    if not external_inn:
        return {'created': 0, 'reactivated': 0}

    cards_qs = CustomerCardModel.objects.filter(
        is_active=True,
        org_admin_id=organization_id,
        inn=external_inn,
    )

    created_count = 0
    reactivated_count = 0
    for card in cards_qs:
        relation = models.CustomerContractServicedCardModel.objects.filter(
            customer_contract_id=contract.pk,
            customer_card_id=card.pk,
        ).first()
        if relation is None:
            models.CustomerContractServicedCardModel.objects.create(
                customer_contract_id=contract.pk,
                customer_card_id=card.pk,
            )
            created_count += 1
            continue

        if not relation.is_active:
            relation.is_active = True
            relation.deleted_at = None
            relation.save(update_fields=('is_active', 'deleted_at', 'updated_at'))
            reactivated_count += 1

    return {'created': created_count, 'reactivated': reactivated_count}
