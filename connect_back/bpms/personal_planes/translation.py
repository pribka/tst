from modeltranslation.translator import translator, TranslationOptions
from . import models


class PersonalPlaneStatusModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(models.PersonalPlaneStatusModel, PersonalPlaneStatusModelTranslationOptions)

