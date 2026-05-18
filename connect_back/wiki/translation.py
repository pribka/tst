from modeltranslation.translator import translator, TranslationOptions
from .models import WikiSectionModel, WikiChapterModel, WikiPageModel


class WikiSectionModelTranslationOptions(TranslationOptions):
    fields = ('random_html',)


class WikiChapterModelTranslationOptions(TranslationOptions):
    fields = ('random_html',)


class WikiPageModelTranslationOptions(TranslationOptions):
    fields = ('random_html',)


translator.register(WikiSectionModel, WikiSectionModelTranslationOptions)
translator.register(WikiChapterModel, WikiChapterModelTranslationOptions)
translator.register(WikiPageModel, WikiPageModelTranslationOptions)
