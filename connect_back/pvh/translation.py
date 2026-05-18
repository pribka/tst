from modeltranslation.translator import translator, TranslationOptions
from . import models


class ExtraCatalogModelOptions(TranslationOptions):
    fields = ()


translator.register(models.ExtraCatalogModel, ExtraCatalogModelOptions)
