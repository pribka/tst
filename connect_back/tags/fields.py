from django.utils.translation import gettext as _

from common import page_config, fields as common_fields


class TagsFilterField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Тэги")
    name = 'tags_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'tags.TagModel'
    model = 'tags.TagModel'
    data_path = '/app_info/select_list/?model=tags.TagModel'

    def to_filter(self, queryset, value):
        queryset = queryset.filter(object_tags__in=value.get('value'))
        return queryset

    def to_exclude(self, queryset, value):
        queryset = queryset.exclude(object_tags__in=value.get('value'))
        return queryset
