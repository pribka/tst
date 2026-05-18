from modeltranslation.translator import translator, TranslationOptions
from .models import (
    CalendarGroupModel, ExternalCalendarModel, CalendarModel,
    EventCalendarTypeModel, EventCalendarPrivacyModel, EventCalendarModel
    )

class CalendarGroupTranslationOptions(TranslationOptions):
    fields = ()


class ExternalCalendarTranslationOptions(TranslationOptions):
    fields = ()


class CalendarTranslationOptions(TranslationOptions):
    fields = ()


class  EventCalendarTypeTranslationOptions(TranslationOptions):
    fields = ()


class EventCalendarPrivacyTranslationOptions(TranslationOptions):
    fields = ()


class EventCalendarTranslationOptions(TranslationOptions):
    fields = ()


translator.register(CalendarGroupModel, CalendarGroupTranslationOptions)
translator.register(ExternalCalendarModel, ExternalCalendarTranslationOptions)
translator.register(CalendarModel, CalendarTranslationOptions)
translator.register(EventCalendarTypeModel, EventCalendarTypeTranslationOptions)
translator.register(EventCalendarPrivacyModel, EventCalendarPrivacyTranslationOptions)
translator.register(EventCalendarModel, EventCalendarTranslationOptions)


