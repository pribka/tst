from modeltranslation.translator import translator, TranslationOptions
from .models import (
    InvestProjectStageModel, InvestProjectCategoryModel, InvestProjectSubcategoryModel,
    InvestProjectFundingSourceModel, InvestProjectMeasureUnitModel,
    InvestProjectPermissionTypeModel, InvestProjectStatusModel
    )

class InvestProjectStageModelTranslationOptions(TranslationOptions):
    fields = ()


class InvestProjectCategoryModelTranslationOptions(TranslationOptions):
    fields = ()


class InvestProjectSubcategoryModelTranslationOptions(TranslationOptions):
    fields = ()


class InvestProjectFundingSourceModelTranslationOptions(TranslationOptions):
    fields = ('short_name',)


class InvestProjectMeasureUnitModelTranslationOptions(TranslationOptions):
    fields = ()


class InvestProjectPermissionTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class InvestProjectStatusModelTranslationOptions(TranslationOptions):
    fields = ('btn_title',)


translator.register(InvestProjectStageModel, InvestProjectStageModelTranslationOptions)
translator.register(InvestProjectCategoryModel, InvestProjectCategoryModelTranslationOptions)
translator.register(InvestProjectSubcategoryModel, InvestProjectSubcategoryModelTranslationOptions)
translator.register(InvestProjectFundingSourceModel, InvestProjectFundingSourceModelTranslationOptions)
translator.register(InvestProjectMeasureUnitModel, InvestProjectMeasureUnitModelTranslationOptions)
translator.register(InvestProjectPermissionTypeModel, InvestProjectPermissionTypeModelTranslationOptions)
translator.register(InvestProjectStatusModel, InvestProjectStatusModelTranslationOptions)