from common.djangoq_haystack.indexes import DjangoQSearchIndex
from django_middleware_global_request.middleware import get_request
from haystack import indexes

from common.utils import get_filter_queryset

from .models import CustomerContractModel


class CustomerContractIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return CustomerContractModel

    def load_all_queryset(self):
        request = get_request()
        model = self.get_model()
        return get_filter_queryset(request, model, model.get_queryset(request))

    def index_queryset(self, using=None):
        return CustomerContractModel.objects.filter(is_active=True)

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        self.remove_object(instance, **kwargs)
        return False

    def prepare(self, obj):
        prepared_data = super(CustomerContractIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data
