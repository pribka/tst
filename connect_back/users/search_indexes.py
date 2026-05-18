from haystack import indexes
from common.djangoq_haystack.indexes import DjangoQSearchIndex
from common.current_profile.middleware import get_current_authenticated_profile
from .models import ProfileModel, NewUserInfoModel


class ProfileIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, )
    profile_id = indexes.CharField(model_attr='pk')
    full_name_auto = indexes.EdgeNgramField()
    is_active = indexes.BooleanField(model_attr='is_active')

    def load_all_queryset(self):
        from .utils import filter_users_by_organizations
        return filter_users_by_organizations(
            ProfileModel.objects.select_related('user').all(), get_current_authenticated_profile()
        )

    def prepare_full_name_auto(self, obj):
        return '' if obj.full_name is None else obj.full_name

    def get_model(self):
        return ProfileModel

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False

    def index_queryset(self, using=None):
        qs = ProfileModel.objects.filter(is_active=True)
        return qs


class NewUserInfoIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return NewUserInfoModel

    def index_queryset(self, using=None):
        qs = NewUserInfoModel.objects.filter(is_active=True).select_related('user__user')
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False
