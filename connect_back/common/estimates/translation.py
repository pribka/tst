from modeltranslation.translator import TranslationOptions, translator

from . import models


class RegistrarDataSourceTranslationOptions(TranslationOptions):
    fields = ()


class RegistrarSectionTranslationOptions(TranslationOptions):
    fields = ()


translator.register(models.RegistrarDataSourceModel, RegistrarDataSourceTranslationOptions)
translator.register(models.RegistrarSectionModel, RegistrarSectionTranslationOptions)
