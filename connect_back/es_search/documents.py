from django.utils.html import strip_tags
from django.utils.text import Truncator

from django_elasticsearch_dsl import Document, fields
from users.models import ProfileModel
from bpms.workgroups.models import WorkgroupModel
from bpms.processes.models import WorkflowRequestModel
from .indexes import (
    CONNECT_INDEX_SETTINGS,
    connect,
    text_ru,
    text_fio,
    text_ru_ngram,
    number_suffix,
    number_suffix_search,
)

@connect.document
class ProfileDocument(Document):
    last_name = fields.TextField(
        analyzer=text_fio,
        fields={
            "raw": fields.KeywordField(),
            "ngram": fields.TextField(analyzer=text_ru_ngram),
        },
    )
    first_name = fields.TextField(
        analyzer=text_fio,
        fields={
            "raw": fields.KeywordField(),
            "ngram": fields.TextField(analyzer=text_ru_ngram),
        },
    )
    middle_name = fields.TextField(
        analyzer=text_fio,
        fields={
            "raw": fields.KeywordField(),
            "ngram": fields.TextField(analyzer=text_ru_ngram),
        },
    )

    class Django:
        model = ProfileModel
        fields = []

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def prepare_last_name(self, instance: ProfileModel):
        return instance.last_name or ""

    def prepare_first_name(self, instance: ProfileModel):
        return instance.first_name or ""

    def prepare_middle_name(self, instance: ProfileModel):
        return instance.middle_name or ""


@connect.document
class WorkgroupDocument(Document):
    name = fields.TextField(
        analyzer=text_ru,
        fields={
            "raw": fields.KeywordField(),
            "ngram": fields.TextField(analyzer=text_ru_ngram)
        },
    )

    class Django:
        model = WorkgroupModel
        fields = []

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def prepare_name(self, instance: WorkgroupModel):
        return instance.name or ""


@connect.document
class WorkflowRequestDocument(Document):
    number_suffix = fields.TextField(
        analyzer=number_suffix,
        search_analyzer=number_suffix_search,
    )
    description = fields.TextField(analyzer=text_ru)

    class Django:
        model = WorkflowRequestModel
        fields = []

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def prepare_number_suffix(self, instance: WorkflowRequestModel):
        return instance.number or ""

    def prepare_description(self, instance: WorkflowRequestModel):
        raw = instance.description or ""
        plain = strip_tags(raw)
        return Truncator(plain).chars(1000, truncate="")
