from modeltranslation.translator import translator, TranslationOptions
from .models import ChangeHistoryActionModel, ChangeHistoryObjectPropertyModel

class ChangeHistoryActionTranslationOptions(TranslationOptions):
    fields = ()


class ChangeHistoryObjectPropertyTranslationOptions(TranslationOptions):
    fields = ()


translator.register(ChangeHistoryActionModel, ChangeHistoryActionTranslationOptions)
translator.register(ChangeHistoryObjectPropertyModel, ChangeHistoryObjectPropertyTranslationOptions)


