from modeltranslation.translator import translator, TranslationOptions
from .models import TariffModel

class TariffModelTranslationOptions(TranslationOptions):
    fields = ()

translator.register(TariffModel, TariffModelTranslationOptions)

