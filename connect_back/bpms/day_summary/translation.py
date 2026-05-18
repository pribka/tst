from modeltranslation.translator import translator, TranslationOptions
from .models import DaySummaryNoteCategoryModel, DaySummaryNoteStatusModel

class ReportSettingsModelTranslationOptions(TranslationOptions):
    fields = ()

class DaySummaryNoteStatusModelTranslationOptions(TranslationOptions):
    fields = ()

translator.register(DaySummaryNoteCategoryModel, ReportSettingsModelTranslationOptions)
translator.register(DaySummaryNoteStatusModel, DaySummaryNoteStatusModelTranslationOptions)


