from modeltranslation.translator import translator, TranslationOptions
from .models import (
    WorkScheduleModel, ExceptionTypeModel, ExceptionModel, ExceptionDatesModel,
    MembersListModel, WorkLoadModel
)


class WorkScheduleModelTranslationOptions(TranslationOptions):
    fields = ()


class ExceptionTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class ExceptionModelTranslationOptions(TranslationOptions):
    fields = ()


class ExceptionDatesModelTranslationOptions(TranslationOptions):
    fields = ()


class MembersListModelTranslationOptions(TranslationOptions):
    fields = ()

class WorkLoadModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(WorkScheduleModel, WorkScheduleModelTranslationOptions)
translator.register(ExceptionTypeModel, ExceptionTypeModelTranslationOptions)
translator.register(ExceptionModel, ExceptionModelTranslationOptions)
translator.register(ExceptionDatesModel, ExceptionDatesModelTranslationOptions)
translator.register(MembersListModel, MembersListModelTranslationOptions)
translator.register(WorkLoadModel, WorkLoadModelTranslationOptions)



