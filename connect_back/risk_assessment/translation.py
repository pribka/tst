from modeltranslation.translator import TranslationOptions, translator

from .models import (AssessmentCriteriaModel, CitizensSocialStatusModel,
                     IssueCategoryModel, IssueTypeModel,
                     PersonalReceptionStatusModel, RiskAssessmentStatusModel,
                     RiskAssessmentTypeModel, PersonalReceptionModel)


class AssessmentCriteriaTranslationOptions(TranslationOptions):
    fields = ()


class RiskAssessmentTypeTranslationOptions(TranslationOptions):
    fields = ()


class RiskAssessmentStatusTranslationOptions(TranslationOptions):
    fields = ()


class IssueTypeTranslationOptions(TranslationOptions):
    fields = ()


class IssueCategoryTranslationOptions(TranslationOptions):
    fields = ()


class CitizensSocialStatusModelOptions(TranslationOptions):
    fields = ()


class PersonalReceptionStatusModelOptions(TranslationOptions):
    fields = ()


class PersonalReceptionModelOptions(TranslationOptions):
    fields = ()


translator.register(AssessmentCriteriaModel, AssessmentCriteriaTranslationOptions)
translator.register(RiskAssessmentTypeModel, RiskAssessmentTypeTranslationOptions)
translator.register(RiskAssessmentStatusModel, RiskAssessmentStatusTranslationOptions)
translator.register(IssueTypeModel, IssueTypeTranslationOptions)
translator.register(IssueCategoryModel, IssueCategoryTranslationOptions)
translator.register(CitizensSocialStatusModel, CitizensSocialStatusModelOptions)
translator.register(PersonalReceptionStatusModel, PersonalReceptionStatusModelOptions)
translator.register(PersonalReceptionModel, PersonalReceptionModelOptions)
