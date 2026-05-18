from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404

from common.accounting_catalogs.models import KATOCodesModel
from common.accounting_catalogs.serializers import CachedKATOCodesModelSerializer


def get_locations_queryset(parent_id: str):
    if parent_id == 'root':
        return KATOCodesModel.objects.filter(
            is_active=True,
            code__endswith='0000000'
        ).order_by(
            'code'
        )

    try:
        parent = KATOCodesModel.objects.get(
            is_active=True,
            id=parent_id
        )
    except (KATOCodesModel.DoesNotExist, ValidationError):
        raise Http404

    parent_level = parent.level

    if parent_level == 'region':
        return KATOCodesModel.objects.filter(
            ~Q(cd='00'),
            is_active=True,
            ab=parent.ab,
            code__endswith='00000'
        ).order_by(
            'code'
        )
    elif parent_level == 'district':
        return KATOCodesModel.objects.filter(
            ~Q(ef='00'),
            is_active=True,
            ab=parent.ab,
            cd=parent.cd,
            code__endswith='000'
        ).order_by(
            'code'
        )
    elif parent_level == 'akimat':
        return KATOCodesModel.objects.filter(
            ~Q(hij='000'),
            is_active=True,
            ab=parent.ab,
            cd=parent.cd,
            ef=parent.ef,
            hij__endswith='00'
        ).order_by(
            'code'
        )
    elif parent_level == 'settlement':
        return KATOCodesModel.objects.filter(
            ~Q(hij__endswith='00'),
            is_active=True,
            ab=parent.ab,
            cd=parent.cd,
            ef=parent.ef,
            hij__startswith=parent.hij[0]
        ).order_by(
            'code'
        )


def get_location_structure(location_id):
    location_structure = dict()
    try:
        location = KATOCodesModel.objects.get(
            is_active=True,
            id=location_id
        )
    except (KATOCodesModel.DoesNotExist, ValidationError):
        raise Http404
    else:
        level = location.level
        if level == 'region':
            location_structure = {
                level: CachedKATOCodesModelSerializer(location.pk).data
            }
        elif level == 'district':
            region = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    code__endswith='0000000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            if region:
                location_structure = {
                    'region': CachedKATOCodesModelSerializer(region.pk).data,
                    level: CachedKATOCodesModelSerializer(location.pk).data
                }
            else:
                raise Http404
        elif level == 'akimat':
            region = None
            district = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    code__endswith='0000000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            try:
                district = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    cd=location.cd,
                    code__endswith='00000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            if region and district:
                location_structure = {
                    'region': CachedKATOCodesModelSerializer(region.pk).data,
                    'district': CachedKATOCodesModelSerializer(district.pk).data,
                    level: CachedKATOCodesModelSerializer(location.pk).data
                }
            else:
                raise Http404
        elif level == 'settlement':
            region = None
            district = None
            akimat = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    code__endswith='0000000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            try:
                district = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    cd=location.cd,
                    code__endswith='00000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            try:
                akimat = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    cd=location.cd,
                    ef=location.ef,
                    code__endswith='000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            if region and district and akimat:
                location_structure = {
                    'region': CachedKATOCodesModelSerializer(region.pk).data,
                    'district': CachedKATOCodesModelSerializer(district.pk).data,
                    'akimat': CachedKATOCodesModelSerializer(akimat.pk).data,
                    level: CachedKATOCodesModelSerializer(location.pk).data
                }
            else:
                raise Http404
        elif level == 'village':
            region = None
            district = None
            akimat = None
            settlement = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    code__endswith='0000000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            try:
                district = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    cd=location.cd,
                    code__endswith='00000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            try:
                akimat = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    cd=location.cd,
                    ef=location.ef,
                    code__endswith='000'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            try:
                settlement = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=location.ab,
                    cd=location.cd,
                    ef=location.ef,
                    hij__startswith=location.hij[0],
                    code__endswith='00'
                )
            except (KATOCodesModel.DoesNotExist, ValidationError):
                pass
            if region and district and akimat and settlement:
                location_structure = {
                    'region': CachedKATOCodesModelSerializer(region.pk).data,
                    'district': CachedKATOCodesModelSerializer(district.pk).data,
                    'akimat': CachedKATOCodesModelSerializer(akimat.pk).data,
                    'settlement': CachedKATOCodesModelSerializer(settlement.pk).data,
                    level: CachedKATOCodesModelSerializer(location.pk).data
                }
        return location_structure
