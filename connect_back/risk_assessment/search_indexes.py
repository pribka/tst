from haystack import indexes
from common.djangoq_haystack.indexes import DjangoQSearchIndex
from common.current_profile.middleware import get_current_authenticated_profile
from .models import RiskAssessmentModel


# class RiskAssessmentIndex(DjangoQSearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=True, )
#     is_active = indexes.BooleanField(model_attr='is_active')
#
#     def load_all_queryset(self):
#         return RiskAssessmentModel.objects.all()
#
#     def prepare_full_name_auto(self, obj):
#         return '' if obj.full_name is None else obj.full_name
#
#     def get_model(self):
#         return RiskAssessmentModel
#
#     def should_update(self, instance, **kwargs):
#         if instance.is_active:
#             return True
#         else:
#             self.remove_object(instance, **kwargs)
#             return False
#
#     def index_queryset(self, using=None):
#         qs = RiskAssessmentModel.objects.filter(is_active=True)
#         return qs

