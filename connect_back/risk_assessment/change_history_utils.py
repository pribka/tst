from change_history.models import ChangeHistoryModel


def create_update_criteria_value(criteria_id, action_date, before, after, author):
    from .models import RiskAssessmentCriteriaModel

    criteria = RiskAssessmentCriteriaModel.objects.get(pk=criteria_id)
    ChangeHistoryModel.objects.create(
        related_object_id=criteria.risk_assessment_id,
        action_id='updated',
        object_property_id='risk_assessment__criteria__value',
        before=before if before is not None else '',
        after=after if after is not None else '',
        action_date=action_date,
        before_data={'criteria_id': criteria_id, 'risk_assessment_id': criteria.risk_assessment_id, 'value': before},
        after_data={'criteria_id': criteria_id, 'risk_assessment_id': criteria.risk_assessment_id, 'value': after},
        description=criteria.criteria.name,
        author=author
    )

