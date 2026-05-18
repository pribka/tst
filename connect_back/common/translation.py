from modeltranslation.translator import translator, TranslationOptions
from .models import (
    BaseCatalog, FolderModel, File, FileType, MimeType, Organization,
    Individual, NotificationTypes,RepetitionTypes, Events,PlanOfCharacteristicBlock,
    PlanOfCharacteristicLookup, CustomThemeModel, CustomJSModel
    )


class BaseCatalogTranslationOptions(TranslationOptions):
    fields = ('name',)


class FolderModelTranslationOptions(TranslationOptions):
    fields = ()


class FileTranslationOptions(TranslationOptions):
    fields = ()


class FileTypeTranslationOptions(TranslationOptions):
    fields = ()


class MimeTypeTranslationOptions(TranslationOptions):
    fields = ()


class OrganizationTranslationOptions(TranslationOptions):
    fields = ()


class IndividualTranslationOptions(TranslationOptions):
    fields = ()


class NotificationTypesTranslationOptions(TranslationOptions):
    fields = ()


class RepetitionTypesTranslationOptions(TranslationOptions):
    fields = ()


class EventsTranslationOptions(TranslationOptions):
    fields = ()


class PlanOfCharacteristicBlockTranslationOptions(TranslationOptions):
    fields = ()


class PlanOfCharacteristicLookupTranslationOptions(TranslationOptions):
    fields = ()


class CustomThemeModelTranslationOptions(TranslationOptions):
    fields = ()


class CustomJSModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(BaseCatalog, BaseCatalogTranslationOptions)
translator.register(FolderModel, FolderModelTranslationOptions)
translator.register(File, FileTranslationOptions)
translator.register(FileType, FileTypeTranslationOptions)
translator.register(MimeType, MimeTypeTranslationOptions)
translator.register(Organization, OrganizationTranslationOptions)
translator.register(Individual, IndividualTranslationOptions)
translator.register(NotificationTypes, NotificationTypesTranslationOptions)
translator.register(RepetitionTypes, RepetitionTypesTranslationOptions)
translator.register(Events, EventsTranslationOptions)
translator.register(PlanOfCharacteristicBlock, PlanOfCharacteristicBlockTranslationOptions)
translator.register(PlanOfCharacteristicLookup, PlanOfCharacteristicLookupTranslationOptions)
translator.register(CustomThemeModel, CustomThemeModelTranslationOptions)
translator.register(CustomJSModel, CustomJSModelTranslationOptions)