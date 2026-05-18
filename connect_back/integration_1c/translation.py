from modeltranslation.translator import translator, TranslationOptions
from .models import ModelToIntegrationModel, Profile1CDocumentsModel


class ModelToIntegrationModelTranslationOptions(TranslationOptions):
    fields = ()


class Profile1CDocumentsModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(ModelToIntegrationModel, ModelToIntegrationModelTranslationOptions)
translator.register(Profile1CDocumentsModel, Profile1CDocumentsModelTranslationOptions)



