from modeltranslation.translator import translator, TranslationOptions
from . import models


class RetrospectiveTypeOptions(TranslationOptions):
    fields = ()


translator.register(models.RetrospectiveTypeModel, RetrospectiveTypeOptions)

