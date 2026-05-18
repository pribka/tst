import pyexcelerate
from io import BytesIO

from django.db.models import Count, Sum, Q
from django.utils import timezone

from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import Polygon, LinearRing

from common import utils as common_utils
from common.accounting_catalogs.models import KATOCodesModel
from common.catalogs.models import LocationAdminAreaModel

from . import models


font_bold_14 = pyexcelerate.Font(bold=True, family='Times new roman', size=14,)
font_bold_11 = pyexcelerate.Font(bold=True, family='Times new roman', size=11,)
font_11 = pyexcelerate.Font(family='Times new roman', size=11,)
font_bold_9 = pyexcelerate.Font(bold=True, family='Times new roman', size=9,)
center_alignment = pyexcelerate.Alignment(horizontal='center', vertical='center', wrap_text=True, )
left_alignment = pyexcelerate.Alignment(horizontal='left', vertical='center', wrap_text=True, )

style_bold_14_center = pyexcelerate.Style(font=font_bold_14, alignment=center_alignment)
style_bold_11_center = pyexcelerate.Style(font=font_bold_11, alignment=center_alignment)
style_11_center = pyexcelerate.Style(font=font_11, alignment=center_alignment)
style_bold_11_left = pyexcelerate.Style(font=font_bold_11, alignment=center_alignment)
style_bold_9_center = pyexcelerate.Style(font=font_bold_9, alignment=center_alignment)


def get_file_response(request):
    locations = KATOCodesModel.objects.filter(
            is_active=True,
            code__endswith='0000000'
        ).order_by(
            'code',
        ).values_list('ab', 'name',)
    qs = models.SportFacilityInfoModel.objects.filter(is_active=True, status_id='approved').order_by('created_at',)

    wb = pyexcelerate.Workbook()
    current_year = timezone.localdate().year
    ws = wb.new_sheet(f'{current_year} -1ФК')

    ws.set_col_style(2, pyexcelerate.Style(size=30))
    ws.set_col_style(3, pyexcelerate.Style(size=20))
    ws.set_col_style(4, pyexcelerate.Style(size=20))
    ws.set_col_style(5, pyexcelerate.Style(size=20))
    ws.set_col_style(6, pyexcelerate.Style(size=20))
    ws.set_col_style(7, pyexcelerate.Style(size=20))
    ws.set_col_style(8, pyexcelerate.Style(size=20))
    ws.set_col_style(9, pyexcelerate.Style(size=20))
    ws.set_col_style(10, pyexcelerate.Style(size=20))
    ws.set_col_style(11, pyexcelerate.Style(size=20))
    ws.set_col_style(12, pyexcelerate.Style(size=20))
    ws.set_col_style(13, pyexcelerate.Style(size=20))

    merge_set = set()

    # Общая таблица
    row = 2
    ws.set_cell_value(row, 2, 1)
    ws.set_cell_style(row, 2, style_bold_14_center)
    row += 1
    row = set_table_header(row, ws, merge_set)
    start_row = row
    for ab, name in locations:
        common_aggregates = aggregate_qs(qs.filter(location__ab=ab))
        set_table_row(row, ws, common_aggregates, name)
        row += 1
    common_aggregates = aggregate_qs(qs)

    set_table_row(row, ws, common_aggregates, 'Итого')

    ws.range((start_row, 2), (row, 3)).style.font = font_bold_11
    ws.range((start_row, 4), (row, 8)).style.font = font_11
    ws.range((start_row, 9), (row, 9)).style.font = font_bold_11
    ws.range((start_row, 2), (row, 2)).style.alignment = left_alignment
    ws.range((start_row, 3), (row, 9)).style.alignment = center_alignment
    ws.range((start_row-4, 2), (row, 9)).style.borders.top.style = '_'
    ws.range((start_row-4, 2), (row, 9)).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
    ws.range((start_row-4, 2), (row, 9)).style.borders.right.style = '_'
    ws.range((start_row-4, 2), (row, 9)).style.borders.right.color = pyexcelerate.Color(0, 0, 0)
    ws.range((start_row-4, 2), (row, 9)).style.borders.bottom.style = '_'
    ws.range((start_row-4, 2), (row, 9)).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
    ws.range((start_row-4, 2), (row, 9)).style.borders.left.style = '_'
    ws.range((start_row-4, 2), (row, 9)).style.borders.left.color = pyexcelerate.Color(0, 0, 0)
    row += 2

    # Таблицы в разрезе типов спортивных объектов
    facility_types = models.SportFacilityTypeModel.objects.filter(is_active=True, parent__isnull=True).order_by('sort',)
    table_number = 1
    for facility_type in facility_types:
        ws.set_cell_value(row, 2, f"1.{table_number}")
        ws.set_cell_style(row, 2, style_bold_14_center)
        row += 1
        facility_type_children = facility_type.children.filter(is_active=True).order_by('sort',).values_list('code', 'name',)
        row = set_table_header(row, ws, merge_set, facility_type, facility_type_children)
        start_row = row
        if facility_type_children:
            lookup = Q(facility_type_id__in=[_[0] for _ in facility_type_children])
        else:
            lookup = Q(facility_type=facility_type)
        for ab, name in locations:
            aggregates = aggregate_qs(qs.filter(lookup, location__ab=ab, ))
            set_table_row(row, ws, aggregates, name, facility_type_children)
            if facility_type_children:
                aggr_children = aggregate_children(qs.filter(lookup, location__ab=ab,), facility_type_children)
                set_children_row(row, ws, aggr_children, facility_type_children)
            row += 1
        # Итого
        aggregates = aggregate_qs(qs.filter(lookup))
        set_table_row(row, ws, aggregates, 'Итого', facility_type_children)
        if facility_type_children:
            aggr_children = aggregate_children(qs.filter(lookup), facility_type_children)
            set_children_row(row, ws, aggr_children, facility_type_children)
        table_number += 1
        children_count = len(facility_type_children)
        ws.range((start_row, 2), (row, 3)).style.font = font_bold_11
        ws.range((start_row, 4), (row, 8+children_count)).style.font = font_11
        ws.range((start_row, 9), (row, 9+children_count)).style.font = font_bold_11
        ws.range((start_row, 2), (row, 2)).style.alignment = left_alignment
        ws.range((start_row, 3), (row, 9+children_count)).style.alignment = center_alignment
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.top.style = '_'
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.right.style = '_'
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.right.color = pyexcelerate.Color(0, 0, 0)
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.bottom.style = '_'
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.left.style = '_'
        ws.range((start_row-4, 2), (row, 9+children_count)).style.borders.left.color = pyexcelerate.Color(0, 0, 0)

        row += 2
    for each in merge_set:
        ws.range(each[0], each[1]).merge()
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def set_table_header(row, ws, merge_set, facility_type=None, children=None):
    filler_count = 0
    if not facility_type:
        name = "Спортивные сооружения"
        diff = 4
    else:
        name = facility_type.name
        diff = 4
    if not children:
        data = (
            ("Области", name, None, None, None, None, None, "Пропускная способность, чел."),
            (None, "Всего", "в том числе", None, None, "из них", None, None),
            (None, None, "объекты физкультурно-спортивного назначения (ФСН)",
             "объекты учреждений образования (включая спортивные школы) (ОУО)", None, "на селе", "частные", None,),
            (None, None, None, "учреждения образования (УО)", "спортивные школы (СШ)", None, None, None,),
        )
    else:
        filler_count = len(children)
        filler = tuple(None for each in range(0, filler_count))
        data = (
            ("Области", name, None, None, None, None, None, *filler, "Пропускная способность, чел."),
            (None, "Всего", "в том числе", None, None, "из них", None, 'в том числе', None, None),
            (None, None, "объекты физкультурно-спортивного назначения (ФСН)",
             "объекты учреждений образования (включая спортивные школы) (ОУО)", None, "на селе",  "частные", *[_[1] for _ in children], None,),
            (None, None, None, "учреждения образования (УО)", "спортивные школы (СШ)", None, None, *filler, None,),
        )
        if filler_count > 1:
            merge_set.add(((row + 1, 9), (row + 1, 8 + filler_count)))
        for each in range(1, filler_count + 1):
            merge_set.add(((row + 2, 8 + each), (row + 3, 8 + each)))
    ws.range((row, 2), (row+3, 9+filler_count)).value = data
    # стилизация
    ws.range((row, 2), (row+3, 9+filler_count)).style.font = font_bold_9
    ws.range((row, 2), (row + 3, 9 + filler_count)).style.alignment = center_alignment
    ws.set_cell_style(row, 3, style_bold_11_center)
    merge_set.add(((row, 2), (row + 3, 2)))
    merge_set.add(((row, 3), (row, 8 + filler_count)))
    merge_set.add(((row + 1, 3), (row + 3, 3)))
    merge_set.add(((row + 1, 4), (row + 1, 6)))
    merge_set.add(((row + 1, 7), (row + 1, 8)))
    merge_set.add(((row + 2, 5), (row + 2, 6)))
    merge_set.add(((row + 2, 4), (row + 3, 4)))
    # merge_set.add(((row + 2, 6), (row + 3, 6)))
    merge_set.add(((row + 2, 7), (row + 3, 7)))
    merge_set.add(((row + 2, 8), (row + 3, 8)))
    merge_set.add(((row, 9 + filler_count), (row + 3, 9 + filler_count)))
    row += diff
    return row


def aggregate_qs(qs):
    return qs.aggregate(
        total=Count('pk'),
        physical_edu_sport=Count('pk', filter=Q(purpose_id='physical_edu_sport')),
        edu_inst=Count('pk', filter=Q(purpose_id='edu_inst')),
        sport_school=Count('pk',
                           filter=Q(purpose_id__in=('high_sport_school', 'sport_intern', 'children_sport_school',))),
        countryside=Count('pk', filter=Q(is_countryside=True)),
        ownership_private=Count('pk', filter=Q(ownership_form_id='private')),
        bandwidth_total=Sum('bandwidth'),
    )


def set_table_row(row, ws, aggr_data, name, children=None):
    filler_count = 0
    if children:
        filler_count = len(children)
        filler = tuple(None for each in range(0, filler_count))
        data = (
            (
                name,
                aggr_data['total'],
                aggr_data['physical_edu_sport'],
                aggr_data['edu_inst'],
                aggr_data['sport_school'],
                aggr_data['countryside'],
                aggr_data['ownership_private'],
                *filler,
                aggr_data['bandwidth_total'] if aggr_data['bandwidth_total'] else 0,
            ),
        )
    else:
        data = (
            (
                name,
                aggr_data['total'],
                aggr_data['physical_edu_sport'],
                aggr_data['edu_inst'],
                aggr_data['sport_school'],
                aggr_data['countryside'],
                aggr_data['ownership_private'],
                aggr_data['bandwidth_total'] if aggr_data['bandwidth_total'] else 0,
            ),
        )
    ws.range((row, 2), (row, 9 + filler_count)).value = data


def aggregate_children(qs, children):
    lookup = dict()
    for each in children:
        lookup[f'count_{each[0]}'] = Count('pk', filter=Q(facility_type_id=each[0]))
    qs = qs.aggregate(**lookup)
    return qs


def set_children_row(row, ws, aggr_data, children):
    data = (
        tuple(aggr_data[f'count_{_[0]}'] for _ in children),
    )
    ws.range((row, 9), (row, 9+len(children))).value = data


def get_regions_districts_data(qs, qp, districts=True):
    if districts is True:
        admin_level = 6
        lookup_key = 'location_points__admin_area'
    else:
        admin_level = 4
        lookup_key = 'location_points__admin_area__parent'
    areas_data = []
    total_count = 0
    lat_gte = float(qp.get('lat__gte', 0))
    lat_lte = float(qp.get('lat__lte', 0))
    lon_gte = float(qp.get('lon__gte', 0))
    lon_lte = float(qp.get('lon__lte', 0))
    rectangle = Polygon(LinearRing(
        ((lon_gte, lat_gte), (lon_gte, lat_lte), (lon_lte, lat_lte), (lon_lte, lat_gte), (lon_gte, lat_gte))))
    regions = LocationAdminAreaModel.objects.filter(admin_level=admin_level, is_active=True).annotate(
        centroid=Centroid('geom')
    ).filter(centroid__intersects=rectangle).order_by('name_ru')
    for each in regions:
        count = qs.filter(**{lookup_key: each}).distinct().count()
        if count == 0:
            continue
        total_count += count
        area_data = {
            'count': count,
            'centroid': [each.centroid.y, each.centroid.x]
        }
        areas_data.append(area_data)
    data = {
        'count': total_count,
        'centroids': areas_data
    }
    return data

def get_points_data(qs, qp,):
    from .serializers import SportFacilityInfoForPointsSerializer
    lat_gte = float(qp.get('lat__gte', 0))
    lat_lte = float(qp.get('lat__lte', 0))
    lon_gte = float(qp.get('lon__gte', 0))
    lon_lte = float(qp.get('lon__lte', 0))
    qs = qs.filter(
        location_points__lat__gte=lat_gte,
        location_points__lat__lte=lat_lte,
        location_points__lon__gte=lon_gte,
        location_points__lon__lte=lon_lte,
    ).distinct()
    serializer = SportFacilityInfoForPointsSerializer(qs, many=True)
    data = {
        "count": qs.count(),
        "points": serializer.data
    }
    return data
