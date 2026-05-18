from haystack import indexes
from django.utils.html import strip_tags
from django.utils.text import Truncator

from common.djangoq_haystack.indexes import DjangoQSearchIndex

from .models import CustomerCardModel, HelpDeskTicketCategoryModel, ContactPersonModel, HelpDeskTicketModel, \
    ContactPersonPostModel


class CustomerCardIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    text_exact = indexes.CharField(use_template=True, indexed=False)
    is_active = indexes.BooleanField(model_attr='is_active')
    name_auto = indexes.EdgeNgramField()

    def get_model(self):
        return CustomerCardModel

    def prepare_name_auto(self, obj):
        return '' if obj.name is None else obj.name

    def index_queryset(self, using=None):
        qs = CustomerCardModel.objects.filter(is_active=True).select_related(
            'customer'
        ).prefetch_related(
            'contact_persons',
            'contact_persons__user',
            'object_tags'
        )
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class TicketCategoryIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return HelpDeskTicketCategoryModel

    def index_queryset(self, using=None):
        qs = HelpDeskTicketCategoryModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class ContactPersonIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return ContactPersonModel

    def index_queryset(self, using=None):
        qs = ContactPersonModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class HelpDeskTicketIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    MAX_DESCRIPTION_CHARS = 1000

    def get_model(self):
        return HelpDeskTicketModel

    def index_queryset(self, using=None):
        qs = HelpDeskTicketModel.objects.filter(is_active=True)
        return qs

    def prepare_text(self, obj):
        description = obj.description or ''
        description_plain = strip_tags(description)
        description_short = Truncator(description_plain).chars(self.MAX_DESCRIPTION_CHARS, truncate='')
        parts = [
            str(obj.number) if obj.number is not None else '',
            str(obj.counter) if obj.counter is not None else '',
            obj.name or '',
            description_short,
        ]
        return ' '.join(part for part in parts if part)

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False


class ContactPersonPostIndex(DjangoQSearchIndex, indexes.Indexable):
    suggestions = indexes.FacetCharField()
    text = indexes.CharField(document=True, use_template=True)
    is_active = indexes.BooleanField(model_attr='is_active')

    def get_model(self):
        return ContactPersonPostModel

    def index_queryset(self, using=None):
        qs = ContactPersonPostModel.objects.filter(is_active=True)
        return qs

    def should_update(self, instance, **kwargs):
        if instance.is_active:
            return True
        else:
            self.remove_object(instance, **kwargs)
            return False
