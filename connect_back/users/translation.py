from modeltranslation.translator import translator, TranslationOptions
from .models import ProfileTypeModel, C1RoleModel, ProfileModel, GoogleOAuthClientIDsModel


class ProfileTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class C1RoleModelTranslationOptions(TranslationOptions):
    fields = ()


class ProfileModelTranslationOptions(TranslationOptions):
    fields = ()


class GoogleOAuthClientIDsModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(ProfileTypeModel, ProfileTypeModelTranslationOptions)
translator.register(C1RoleModel, C1RoleModelTranslationOptions)
translator.register(ProfileModel, ProfileModelTranslationOptions)
translator.register(GoogleOAuthClientIDsModel, GoogleOAuthClientIDsModelTranslationOptions)