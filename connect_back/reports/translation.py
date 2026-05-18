from modeltranslation.translator import translator, TranslationOptions
from .models import ReportSettingsModel, UserReportSettingsModel, ReportCategoryModel

class ReportSettingsModelTranslationOptions(TranslationOptions):
    fields = ('_metadata', 'description',)

class UserReportSettingsModelTranslationOptions(TranslationOptions):
    fields = ()

class ReportCategoryModelTranslationOptions(TranslationOptions):
    fields = ()

translator.register(ReportSettingsModel, ReportSettingsModelTranslationOptions)
translator.register(UserReportSettingsModel, UserReportSettingsModelTranslationOptions)
translator.register(ReportCategoryModel, ReportCategoryModelTranslationOptions)


