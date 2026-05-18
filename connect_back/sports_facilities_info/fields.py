from common import fields as common_fields, page_config


class RepubCompFilterField(common_fields.FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'repub_comp_filter'
    verbose_name = 'Соответствует республиканским соревнованиям'
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(repub_comp=True)
        else:
            return queryset.filter(repub_comp=False)

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(repub_comp=False)
        else:
            return queryset.exclude(repub_comp=True)
