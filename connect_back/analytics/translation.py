from modeltranslation.translator import translator, TranslationOptions
from . import models


class DashboardSectionModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(models.DashboardSectionModel, DashboardSectionModelTranslationOptions)
