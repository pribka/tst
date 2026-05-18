from haystack import indexes
from django.utils.html import strip_tags
from django.utils.text import Truncator

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .models import DaySummaryNoteModel


class DaySummaryNoteIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=False)
    is_active = indexes.BooleanField(model_attr='is_active')

    MAX_CONTENT_CHARS = 1000

    def get_model(self):
        return DaySummaryNoteModel

    def index_queryset(self, using=None):
        return DaySummaryNoteModel.objects.filter(is_active=True)

    def prepare_text(self, obj):
        content = obj.content or ''
        content_plain = strip_tags(content)
        content_short = Truncator(content_plain).chars(
            self.MAX_CONTENT_CHARS, truncate=''
        )
        return content_short

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        self.remove_object(instance, **kwargs)
        return False
