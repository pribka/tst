from django.utils.translation import gettext_lazy as _
from common.fields import FakeField
from common import page_config
from common.current_profile.middleware import get_current_authenticated_profile


class InFavoritesFilterField(FakeField):
    table_info = page_config.BooleanTableColumn()
    field_info = page_config.BooleanFormField()
    filter_info = page_config.BooleanFilterField()
    tp_info = page_config.TPSwitchColumn()
    filter_lookup = {"value": ""}
    internal_type = 'BooleanField'
    name = 'in_favorites_filter'
    verbose_name = _('В избранном')
    default = None
    blank = True

    def to_filter(self, queryset, value):
        if value.get('value') is True:
            return queryset.filter(in_favorites=True)
        else:
            return queryset.filter(in_favorites=False)

    def to_exclude(self, queryset, value):
        if value.get('value') is True:
            return queryset.exclude(in_favorites=True)
        else:
            return queryset.filter(in_favorites=False)
