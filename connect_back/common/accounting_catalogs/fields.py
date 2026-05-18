from django.db.models import Q

from common import fields as common_fields
from common import page_config
from common.accounting_catalogs.models import KATOCodesModel


class LocationFilterFakeField(common_fields.FakeField):
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = "Местоположение"
    name = 'location_filter'
    default = None
    blank = True
    to_fields = ('id',)
    remote_field = 'id'
    key = 'accounting_catalogs.KATOCodesModel'
    model = 'accounting_catalogs.KATOCodesModel'

    def to_filter(self, queryset, value):
        lookup = Q()
        locations = list()
        try:
            locations = KATOCodesModel.objects.filter(id__in=value['value'])
        except KATOCodesModel.DoesNotExist:
            pass
        for lc in locations:
            level = lc.level
            lu = Q()
            if level == 'region':
                lu = Q(
                    location__ab=lc.ab
                )
            elif level == 'district':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd
                )
            elif level == 'akimat':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd,
                    location__ef=lc.ef
                )
            elif level == 'settlement':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd,
                    location__ef=lc.ef,
                    location__hij__startswith=lc.hij[0]
                )
            elif level == 'village':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd,
                    location__ef=lc.ef,
                    location__hij=lc.hij
                )
            if lu:
                lookup |= lu
        return queryset.filter(lookup, is_active=True).distinct()

    def to_exclude(self, queryset, value):
        lookup = Q()
        locations = list()
        try:
            locations = KATOCodesModel.objects.filter(id__in=value['value'])
        except KATOCodesModel.DoesNotExist:
            pass
        for lc in locations:
            level = lc.level
            lu = Q()
            if level == 'region':
                lu = Q(
                    location__ab=lc.ab
                )
            elif level == 'district':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd
                )
            elif level == 'akimat':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd,
                    location__ef=lc.ef
                )
            elif level == 'settlement':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd,
                    location__ef=lc.ef,
                    location__hij__startswith=lc.hij[0]
                )
            elif level == 'village':
                lu = Q(
                    location__ab=lc.ab,
                    location__cd=lc.cd,
                    location__ef=lc.ef,
                    location__hij=lc.hij
                )
            if lu:
                lookup |= lu
        return queryset.exclude(lookup, is_active=True).distinct()
