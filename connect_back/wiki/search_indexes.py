from haystack import indexes
from django_middleware_global_request.middleware import get_request

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .models import WikiPageModel, WikiChapterModel, WikiSectionModel


class WikiSectionIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return WikiSectionModel

    def index_queryset(self, using=None):
        qs = WikiSectionModel.objects.all()
        return qs


class WikiChapterIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return WikiChapterModel

    def index_queryset(self, using=None):
        qs = WikiChapterModel.objects.all()
        return qs


class WikiPageIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)

    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return WikiPageModel

    def index_queryset(self, using=None):
        qs = WikiPageModel.objects.all()
        return qs
