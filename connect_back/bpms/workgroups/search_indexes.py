from haystack import indexes
from django_middleware_global_request.middleware import get_request

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .utils import get_workgroup_queryset
from .models import WorkgroupModel


class WorkgroupIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at', null=True)

    def get_model(self):
        return WorkgroupModel

    def load_all_queryset(self):
        queryset = get_workgroup_queryset(
            get_request(),
        )
        return queryset

    def index_queryset(self, using=None):
        qs = WorkgroupModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

