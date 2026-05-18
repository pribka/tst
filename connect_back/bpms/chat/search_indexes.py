from haystack import indexes
from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .models import ChatModel, SupportMessageTemplateModel, MessageModel


class ChatIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    chat_id = indexes.CharField(model_attr='id')
    chat_is_public = indexes.BooleanField(model_attr='is_public')
    chat_is_active = indexes.BooleanField(model_attr='is_active')
    chat_members = indexes.MultiValueField(null=True)

    def load_all_queryset(self):
        return ChatModel.objects.prefetch_related(
            'members__user',
        ).select_related(
            'author__user',
        ).all()

    def get_model(self):
        return ChatModel

    def index_queryset(self, using=None):
        qs = ChatModel.objects.filter(is_active=True)
        return qs

    def prepare_chat_members(self, obj):
        return list(obj.members.filter(is_active=True).values_list('user_id', flat=True))

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class SupportMessageTemplateIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SupportMessageTemplateModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_active=True)

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class ChatMessageIndex(DjangoQSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    chat_id = indexes.CharField(model_attr='chat_id', null=True)

    def get_model(self):
        return MessageModel

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            is_active=True, is_deleted=False, chat_id__isnull=False
        )

    def should_update(self, instance, **kwargs):
        if instance.is_active and not instance.is_deleted:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False
