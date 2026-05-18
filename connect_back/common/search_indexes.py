from haystack import indexes

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .models import File


class FileIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at', null=True)

    def get_model(self):
        return File

    def index_queryset(self, using=None):
        qs = File.objects.filter(is_deleted=False, is_confined=False)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_deleted or instance.is_confined:
            self.remove_object(instance, **kwargs)
            return False
        else:
            return True

