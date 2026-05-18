from modeltranslation.translator import translator, TranslationOptions
from . import models


class CatalogSectionOptions(TranslationOptions):
    fields = ()


class CatalogInfoOptions(TranslationOptions):
    fields = (
        '_form_info',
    )


translator.register(models.CatalogSectionModel, CatalogSectionOptions)
translator.register(models.CatalogInfoModel, CatalogInfoOptions)
