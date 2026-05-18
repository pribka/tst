from haystack import indexes
from . import models, utils
from common.djangoq_haystack.indexes import DjangoQSearchIndex
from django_middleware_global_request.middleware import get_request


class MeetingIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def load_all_queryset(self):
        request = get_request()
        return utils.get_meeting_queryset(request)

    def get_model(self):
        return models.PlannedMeetingModel

    def index_queryset(self, using=None):
        qs = models.PlannedMeetingModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

