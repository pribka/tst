from modeltranslation.translator import translator, TranslationOptions
from . import models


class ColorNoteModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(models.ColorNoteModel, ColorNoteModelTranslationOptions)


