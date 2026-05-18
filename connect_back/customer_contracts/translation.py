from modeltranslation.translator import translator, TranslationOptions
from . import models


class CustomerContractStatusOption(TranslationOptions):
    fields = ()


translator.register(models.CustomerContractStatusModel, CustomerContractStatusOption)
