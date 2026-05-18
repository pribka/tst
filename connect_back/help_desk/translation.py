from modeltranslation.translator import translator, TranslationOptions
from . import models


class ContactPersonModelTranslationOptions(TranslationOptions):
    fields = ()


class HelpDeskTicketPriorityModelTranslationOptions(TranslationOptions):
    fields = ()


class HelpDeskTicketCategoryModelTranslationOptions(TranslationOptions):
    fields = ()


class ContactPersonPostModelTranslationOptions(TranslationOptions):
    fields = ()


class HelpDeskTicketStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class HelpDeskChannelModelTranslationOptions(TranslationOptions):
    fields = ()


class CustomerCardStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class CustomerCardAdminModelTranslationOptions(TranslationOptions):
    fields = ()


class HelpDeskTicketTypeModelTranslationOptions(TranslationOptions):
    fields = ()

translator.register(models.ContactPersonModel, ContactPersonModelTranslationOptions)
translator.register(models.HelpDeskTicketPriorityModel, HelpDeskTicketPriorityModelTranslationOptions)
translator.register(models.HelpDeskTicketCategoryModel, HelpDeskTicketCategoryModelTranslationOptions)
translator.register(models.ContactPersonPostModel, ContactPersonPostModelTranslationOptions)
translator.register(models.HelpDeskTicketStatusModel, HelpDeskTicketStatusModelTranslationOptions)
translator.register(models.HelpDeskChannelModel, HelpDeskChannelModelTranslationOptions)
translator.register(models.CustomerCardStatusModel, CustomerCardStatusModelTranslationOptions)
translator.register(models.CustomerCardAdminModel, CustomerCardAdminModelTranslationOptions)
translator.register(models.HelpDeskTicketTypeModel, HelpDeskTicketTypeModelTranslationOptions)
