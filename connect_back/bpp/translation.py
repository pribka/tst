from modeltranslation.translator import translator, TranslationOptions
from .models import EditionModel, EditionPublisherModel, EditionAuthorModel, EditionPartModel, EditionUnitModel


class EditioTranslationOptions(TranslationOptions):
    fields = ()


class EditionPublisherTranslationOptions(TranslationOptions):
    fields = ()


class EditionAuthorTranslationOptions(TranslationOptions):
    fields = ()


class  EditionPartTranslationOptions(TranslationOptions):
    fields = ()


class  EditionUnitTranslationOptions(TranslationOptions):
    fields = ()

translator.register(EditionModel, EditioTranslationOptions)
translator.register(EditionPublisherModel, EditionPublisherTranslationOptions)
translator.register(EditionAuthorModel, EditionAuthorTranslationOptions)
translator.register(EditionPartModel, EditionPartTranslationOptions)
translator.register(EditionUnitModel, EditionUnitTranslationOptions)


