from decimal import Decimal
from haystack import indexes

from django_middleware_global_request.middleware import get_request

from common.djangoq_haystack.indexes import DjangoQSearchIndex
from common.utils import get_filter_queryset, order_queryset_from_get_param

from .models import (GoodsModel, GoodsCategoryModel, ContractorModel, PotentialContractorModel, ContractorMemberModel,
                     ContractorProfileRequestModel, CostItemModel)


class GoodsModelIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    popularity = indexes.FloatField(model_attr='popularity')
    price_by_catalog = indexes.IntegerField(model_attr='price_by_catalog')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def prepare_price_by_catalog(self, obj):
        return int(obj.price_by_catalog * Decimal('100'))

    def get_model(self):
        return GoodsModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_active=True)

    def load_all_queryset(self):
        request = get_request()
        model = self.get_model()
        qs = get_filter_queryset(request, model, model.get_queryset())
        category = request.GET.get('category')
        if category:
            category_obj = GoodsCategoryModel.objects.get(pk=category)
            descendants = category_obj.get_descendants(include_self=True)
            qs = qs.filter(category__in=descendants)
        qs = qs.filter(show_in_catalog=True).exclude(price_by_catalog=0)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

    def prepare(self, obj):
        prepared_data = super(GoodsModelIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data


class ContractorModelIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    text_exact = indexes.CharField(use_template=True, indexed=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return ContractorModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_active=True)

    def load_all_queryset(self):
        request = get_request()
        model = self.get_model()
        qs = get_filter_queryset(request, model, model.get_queryset())
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

    def prepare(self, obj):
        prepared_data = super(ContractorModelIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data


class ContractorMemberModelIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return ContractorMemberModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_active=True)

    def load_all_queryset(self):
        request = get_request()
        model = self.get_model()
        qs = get_filter_queryset(request, model, model.get_queryset())
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

    def prepare(self, obj):
        prepared_data = super(ContractorMemberModelIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data


class PotentialContractorModelIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return PotentialContractorModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_active=True)

    def load_all_queryset(self):
        request = get_request()
        model = self.get_model()
        qs = get_filter_queryset(request, model, model.get_queryset())
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

    def prepare(self, obj):
        prepared_data = super(PotentialContractorModelIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data


class ContractorProfileRequestModelIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at')

    def get_model(self):
        return ContractorProfileRequestModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_active=True)

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class CostItemIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return CostItemModel

    def index_queryset(self, using=None):
        qs = CostItemModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False
