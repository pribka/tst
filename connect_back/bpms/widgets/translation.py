from modeltranslation.translator import translator, TranslationOptions
from .models import (
    WidgetCatalog, WidgetCategoryModel, WidgetModel, DesktopTemplateModel,
    DesktopTemplateWidgetOnDesktopModel, UserDesktopModel, UserWidgetOnDesktopModel
    )

class WidgetCatalogTranslationOptions(TranslationOptions):
    fields = ()


class WidgetCategoryTranslationOptions(TranslationOptions):
    fields = ()


class WidgetTranslationOptions(TranslationOptions):
    fields = ()


class  DesktopTemplateTranslationOptions(TranslationOptions):
    fields = ()


class DesktopTemplateWidgetOnDesktopTranslationOptions(TranslationOptions):
    fields = ()


class UserDesktopTranslationOptions(TranslationOptions):
    fields = ()


class UserWidgetOnDesktopTranslationOptions(TranslationOptions):
    fields = ()

translator.register(WidgetCatalog, WidgetCatalogTranslationOptions)
translator.register(WidgetCategoryModel, WidgetCategoryTranslationOptions)
translator.register(WidgetModel, WidgetTranslationOptions)
translator.register(DesktopTemplateModel, DesktopTemplateTranslationOptions)
translator.register(DesktopTemplateWidgetOnDesktopModel, DesktopTemplateWidgetOnDesktopTranslationOptions)
translator.register(UserDesktopModel, UserDesktopTranslationOptions)
translator.register(UserWidgetOnDesktopModel, UserWidgetOnDesktopTranslationOptions)


