from modeltranslation.translator import translator, TranslationOptions
from .models import (
    ContractorDocTypeModel, ContractorDocTemplateModel, ContractorDocDeliveryStatusModel,
    ContractorDocApprovalStatusModel, ContractorDocModel
)

class ContractorDocTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractorDocTemplateModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractorDocDeliveryStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractorDocApprovalStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractorDocModelTranslationOptions(TranslationOptions):
    fields = ()

translator.register(ContractorDocTypeModel, ContractorDocTypeModelTranslationOptions)
translator.register(ContractorDocTemplateModel, ContractorDocTemplateModelTranslationOptions)
translator.register(ContractorDocDeliveryStatusModel, ContractorDocDeliveryStatusModelTranslationOptions)
translator.register(ContractorDocApprovalStatusModel, ContractorDocApprovalStatusModelTranslationOptions)
translator.register(ContractorDocModel, ContractorDocModelTranslationOptions)


