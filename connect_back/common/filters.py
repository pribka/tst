from django_filters import FilterSet, Filter, filters

from . import models


class IntegerListFilter(Filter):
    def filter(self, qs, value):
        if value not in (None, ''):
            integers = [int(v) for v in value.split(',')]
            return qs.filter(**{'%s__%s' % (self.field_name, self.lookup_expr): integers})
        return qs


class IntegerListExcludeFilter(Filter):
    def filter(self, qs, value):
        if value not in (None, ''):
            integers = [int(v) for v in value.split(',')]
            return qs.exclude(**{'%s__%s' % (self.field_name, self.lookup_expr): integers})
        return qs


class CharListFilter(Filter):
    def filter(self, qs, value):
        if value not in (None, ''):
            chars = value.split(',')
            return qs.filter(**{'%s__%s' % (self.field_name, self.lookup_expr): chars})
        return qs


class CharListExcludeFilter(Filter):
    def filter(self, qs, value):
        if value not in (None, ''):
            chars = value.split(',')
            return qs.exclude(**{'%s__%s' % (self.field_name, self.lookup_expr): chars})
        return qs


class BaseModelFilter(FilterSet):
    author = IntegerListFilter(field_name='author', lookup_expr='in')
    author__exclude = IntegerListExcludeFilter(field_name='author', lookup_expr='in')
    created_at = filters.IsoDateTimeFromToRangeFilter()
    updated_at = filters.IsoDateTimeFromToRangeFilter()
    deleted_at = filters.IsoDateTimeFromToRangeFilter()

    class Meta:
        model = models.BaseModel
        fields = [
            'is_active',
            'created_at',
            'updated_at',
            'deleted_at',
            'author',
            'author__exclude'
                  ]


class BaseCatalogFilter(BaseModelFilter):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta(BaseModelFilter.Meta):
        model = models.BaseCatalog
        fields = BaseModelFilter.Meta.fields + ['name', 'is_predefined']


class FileFilter(BaseCatalogFilter):
    file_type = CharListFilter(field_name='mime_type__file_type', lookup_expr='in')
    file_type__exclude = CharListExcludeFilter(field_name='mime_type__file_type', lookup_expr='in')
    size = filters.RangeFilter()

    class Meta(BaseCatalogFilter.Meta):
        fields = BaseCatalogFilter.Meta.fields + ['file_type', 'size']


class MimeTypeFilter(BaseCatalogFilter):
    file_type = CharListFilter(field_name='file_type', lookup_expr='in')
    file_type__exclude = CharListExcludeFilter(field_name='file_type', lookup_expr='in')

    class Meta(BaseCatalogFilter.Meta):
        fields = BaseCatalogFilter.Meta.fields + ['file_type', 'file_type__exclude']
