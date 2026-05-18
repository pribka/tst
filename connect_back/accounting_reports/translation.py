from modeltranslation.translator import translator, TranslationOptions
from .models import AccountingReportStatusModel, AccountingReportTypeModel, AccountingReportSubtypeModel

class AccountingReportStatusTranslationOptions(TranslationOptions):
    fields = ()


class AccountingReportTranslationOptions(TranslationOptions):
    fields = ()


class AccountingReportSubtypeTranslationOptions(TranslationOptions):
    fields = ()


translator.register(AccountingReportStatusModel, AccountingReportStatusTranslationOptions)
translator.register(AccountingReportTypeModel, AccountingReportTranslationOptions)
translator.register(AccountingReportSubtypeModel, AccountingReportSubtypeTranslationOptions)
