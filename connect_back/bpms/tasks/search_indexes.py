from haystack import indexes
from django_middleware_global_request.middleware import get_request

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .utils import get_task_queryset, get_task_sprint_queryset
from .models import TaskModel, TaskSprintModel


class TaskIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    text_exact = indexes.CharField(use_template=True, indexed=False)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return TaskModel

    def load_all_queryset(self):
        queryset = get_task_queryset(
            get_request(),
            TaskModel.objects.filter(is_active=True).select_related(
                'parent__author__user',
                'author__user',
                'owner__user',
                'operator__user',
                'workgroup',
                'project',
                'contractor',
                'potential_contractor',
                'status',
            ).prefetch_related(
                'prerequisites__author',
                'visors',
                'attachments',
                'children'
            ),
            list_type='search',
        )
        return queryset

    def index_queryset(self, using=None):
        qs = TaskModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class TaskSprintIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')
    created_at = indexes.DateTimeField(model_attr='created_at', null=True)

    def get_model(self):
        return TaskSprintModel

    def load_all_queryset(self):
        return get_task_sprint_queryset(get_request())

    def index_queryset(self, using=None):
        qs = TaskSprintModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False
