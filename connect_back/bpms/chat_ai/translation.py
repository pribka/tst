from modeltranslation.translator import translator, TranslationOptions
from .models import (
    AIChatRoleModel, IntentTypeModel, IntentStatusModel,
    AIProvider, AIMessageStatusModel,
    )

class AIChatRoleModelTranslationOptions(TranslationOptions):
    fields = ()


class IntentTypeModelTranslationOptions(TranslationOptions):
    fields = ('btn_title_create', 'btn_title_open', 'btn_title_delete', 'success_message',)


class IntentStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class AIProviderTranslationOptions(TranslationOptions):
    fields = ()


class AIMessageStatusModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(AIChatRoleModel, AIChatRoleModelTranslationOptions)
translator.register(IntentTypeModel, IntentTypeModelTranslationOptions)
translator.register(IntentStatusModel, IntentStatusModelTranslationOptions)
translator.register(AIProvider, AIProviderTranslationOptions)
translator.register(AIMessageStatusModel, AIMessageStatusModelTranslationOptions)
