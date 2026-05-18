from modeltranslation.translator import translator, TranslationOptions
from .models import StaticPageModel

class StaticPageModelTranslationOptions(TranslationOptions):
    fields = ()

translator.register(StaticPageModel, StaticPageModelTranslationOptions)
