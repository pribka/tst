from modeltranslation.translator import translator, TranslationOptions
from .models import (
    ReportFormModel, ConsolidationStatusModel, ReportStatusModel,
    ConsolidationFileTypeModel, ConsolidationFileModel, FileTypeModel,
    ReportTypeInfoModel, ReportFileModel, ReportModel, ConsolidationModel, AnalyticReportModel
    )


class ReportFormModelTranslationOptions(TranslationOptions):
    fields = ()


class ConsolidationStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class ReportStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class ConsolidationFileTypeModelTranslationOptions(TranslationOptions):
    fields = ('description',)


class ConsolidationFileModelTranslationOptions(TranslationOptions):
    fields = ()


class FileTypeModelTranslationOptions(TranslationOptions):
    fields = ('description',)


class ReportTypeInfoModelTranslationOptions(TranslationOptions):
    fields = ()


class ReportFileModelTranslationOptions(TranslationOptions):
    fields = ()


class ReportModelTranslationOptions(TranslationOptions):
    fields = ()


class ConsolidationModelTranslationOptions(TranslationOptions):
    fields = ()


class AnalyticReportModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(ReportFormModel, ReportFormModelTranslationOptions)
translator.register(ConsolidationStatusModel, ConsolidationStatusModelTranslationOptions)
translator.register(ReportStatusModel, ReportStatusModelTranslationOptions)
translator.register(ConsolidationFileTypeModel, ConsolidationFileTypeModelTranslationOptions)
translator.register(ConsolidationFileModel, ConsolidationFileModelTranslationOptions)
translator.register(FileTypeModel, FileTypeModelTranslationOptions)
translator.register(ReportTypeInfoModel, ReportTypeInfoModelTranslationOptions)
translator.register(ReportFileModel, ReportFileModelTranslationOptions)
translator.register(ReportModel, ReportModelTranslationOptions)
translator.register(ConsolidationModel, ConsolidationModelTranslationOptions)
translator.register(AnalyticReportModel, AnalyticReportModelTranslationOptions)


