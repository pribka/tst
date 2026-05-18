from common.djangoq_haystack.indexes import DjangoQSearchIndex
from haystack import indexes
from django_middleware_global_request.middleware import get_request

from common.utils import get_filter_queryset

from .models import DealModel, GoodsOrderModel


class GoodsOrderModelIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def load_all_queryset(self):
        return get_filter_queryset(get_request(), self.get_model(), self.get_model().get_queryset())

    def get_model(self):
        return GoodsOrderModel

    def index_queryset(self, using=None):
        qs = GoodsOrderModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class DealModelIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return DealModel

    def load_all_queryset(self):
        request = get_request()
        model = self.get_model()
        qs = get_filter_queryset(request, model, model.get_queryset(request))
        return qs

    def index_queryset(self, using=None):
        return DealModel.objects.filter(is_active=True)

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

    def prepare(self, obj):
        prepared_data = super(DealModelIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data


