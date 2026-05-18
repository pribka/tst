from modeltranslation.translator import translator, TranslationOptions
from .models import UserWorkStatusModel, UserWorkStatusReasonModel


class UserWorkStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class UserWorkStatusReasonModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(UserWorkStatusModel, UserWorkStatusModelTranslationOptions)
translator.register(UserWorkStatusReasonModel, UserWorkStatusReasonModelTranslationOptions)
