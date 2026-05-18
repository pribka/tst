from modeltranslation.translator import translator, TranslationOptions
from .models import (
    Configuration1cModel, Tariff1CModel, TicketTypeModel, TicketTypeOptionModel,
    TicketModel
)

class Configuration1cModelTranslationOptions(TranslationOptions):
    fields = ()


class Tariff1CModelTranslationOptions(TranslationOptions):
    fields = ()


class TicketTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class TicketTypeOptionModelTranslationOptions(TranslationOptions):
    fields = ()


class TicketModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(Configuration1cModel, Configuration1cModelTranslationOptions)
translator.register(Tariff1CModel, Tariff1CModelTranslationOptions)
translator.register(TicketTypeModel, TicketTypeModelTranslationOptions)
translator.register(TicketTypeOptionModel, TicketTypeOptionModelTranslationOptions)
translator.register(TicketModel, TicketModelTranslationOptions)
