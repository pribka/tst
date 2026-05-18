from modeltranslation.translator import translator, TranslationOptions
from .models import AppInfo

class AppInfoTranslationOptions(TranslationOptions):
    fields = ('_metadata',)

translator.register(AppInfo, AppInfoTranslationOptions)

