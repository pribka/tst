from modeltranslation.translator import translator, TranslationOptions
from .models import (
    Partition, Tag, ContentItem, OfficialClarificationOrgan
)
from modeltranslation.translator import register, TranslationOptions

class PartitionTranslationOptions(TranslationOptions):
    fields = ()


translator.register(Partition, PartitionTranslationOptions)

class TagTranslationOptions(TranslationOptions):
    fields = ()


translator.register(Tag, TagTranslationOptions)

@register(ContentItem)
class ContentItemTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'body',
        'body_clean',
        'description',
        'description_clean',
        'question',
        'question_html',
        'answer',
        'answer_html',
    )

@register(OfficialClarificationOrgan)
class OfficialClarificationOrganOptions(TranslationOptions):
    fields = (
        'title',
    )

