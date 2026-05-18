from modeltranslation.translator import translator, TranslationOptions
from . import models


class ReactionTranslation(TranslationOptions):
    fields = ()


translator.register(models.ReactionModel, ReactionTranslation)

