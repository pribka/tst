from haystack import indexes
from django_middleware_global_request.middleware import get_request

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .models import SportFacilityInfoModel


class SportFacilityIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return SportFacilityInfoModel

    def index_queryset(self, using=None):
        qs = SportFacilityInfoModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False
