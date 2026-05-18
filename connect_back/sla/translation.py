from modeltranslation.translator import TranslationOptions, translator

from . import models


class SLATranslationOptions(TranslationOptions):
    fields = ()


translator.register(models.SLAModel, SLATranslationOptions)
