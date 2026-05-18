from modeltranslation.translator import translator, TranslationOptions
from .models import MeetingServerModel, PlannedMeetingModel, MeetingRecordsModel, CallStatusModel


class MeetingServerTranslationOptions(TranslationOptions):
    fields = ()


class PlannedMeetingTranslationOptions(TranslationOptions):
    fields = ()


class MeetingRecordsTranslationOptions(TranslationOptions):
    fields = ()


class CallStatusTranslationOptions(TranslationOptions):
    fields = ()


translator.register(MeetingServerModel, MeetingServerTranslationOptions)
translator.register(PlannedMeetingModel, PlannedMeetingTranslationOptions)
translator.register(MeetingRecordsModel, MeetingRecordsTranslationOptions)
translator.register(CallStatusModel, CallStatusTranslationOptions)


