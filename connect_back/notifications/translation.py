from modeltranslation.translator import translator, TranslationOptions
from .models import EventTypeModel, EmailTemplateModel, NotificationCategoryModel


class EventTypeModelTranslationOptions(TranslationOptions):
    fields = ('template_text', 'template_html',)


class EmailTemplateModelTranslationOptions(TranslationOptions):
    fields = ()


class NotificationCategoryTranslationOptions(TranslationOptions):
    fields = ()


translator.register(EventTypeModel, EventTypeModelTranslationOptions)
translator.register(EmailTemplateModel, EmailTemplateModelTranslationOptions)
translator.register(NotificationCategoryModel, NotificationCategoryTranslationOptions)
