from modeltranslation.translator import translator, TranslationOptions
from .models import KATOCodesModel

class KATOCodesModelTranslationOptions(TranslationOptions):
    fields = ('name',)


translator.register(KATOCodesModel, KATOCodesModelTranslationOptions)