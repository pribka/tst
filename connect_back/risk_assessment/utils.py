from django.db.models import Case, Count, IntegerField, Sum, When
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import Polygon, LinearRing


from common.catalogs.models import LocationAdminAreaModel

from . import search_indexes


# def index_risk_assessment_model(issue):
#     risk_assessments = issue.risk_assessments.filter(is_active=True)
#     for each in risk_assessments:
#         search_indexes.RiskAssessmentIndex().update_object(each)


def get_summary(queryset):
    return queryset.aggregate(
        white=Sum(
            Case(
                When(total_value__exact=0, then=1),
                output_field=IntegerField(),
                default=0
            )
        ),
        yellow=Sum(
            Case(
                When(total_value__range=(1, 2), then=1),
                output_field=IntegerField(),
                default=0
            )
        ),
        orange=Sum(
            Case(
                When(total_value__range=(3, 5), then=1),
                output_field=IntegerField(),
                default=0
            )
        ),
        red=Sum(
            Case(
                When(total_value__range=(6, 10), then=1),
                output_field=IntegerField(),
                default=0
            )
        ),
        total=Count('id')
    )


def get_regions_districts_data(queryset, query_params, districts=True):
    if districts is True:
        admin_level = 6
        lookup_key = 'location_points__admin_area'
    else:
        admin_level = 4
        lookup_key = 'location_points__admin_area__parent'
    areas_data = []
    total_summary = {
        "white": 0,
        "yellow": 0,
        "orange": 0,
        "red": 0,
        "total": 0,
    }
    lat_gte = float(query_params.get('lat__gte', 0))
    lon_gte = float(query_params.get('lon__gte', 0))
    lat_lte = float(query_params.get('lat__lte', 0))
    lon_lte = float(query_params.get('lon__lte', 0))
    rectangle = Polygon(LinearRing(
        ((lon_gte, lat_gte), (lon_gte, lat_lte), (lon_lte, lat_lte), (lon_lte, lat_gte), (lon_gte, lat_gte))))
    districts = LocationAdminAreaModel.objects.filter(admin_level=admin_level, is_active=True).annotate(
        centroid=Centroid('geom')
    ).filter(centroid__intersects=rectangle).order_by('name_ru')
    for each in districts:
        qs = queryset.filter(**{lookup_key: each}).distinct()
        if qs.count() == 0:
            continue
        summary = get_summary(qs)
        for key, value in summary.items():
            total_summary[key] += value
        area_data = {
            'summary': get_summary(qs),
            'centroid': [each.centroid.y, each.centroid.x]
        }
        areas_data.append(area_data)
    data = {
        'summary': total_summary,
        'centroids': areas_data,
    }
    return data


def get_points_data(queryset, query_params):
    from .serializers import RiskAssessmentModelMapSerializer
    lat_gte = query_params.get('lat__gte', 0)
    lat_lte = query_params.get('lat__lte', 0)
    lon_gte = query_params.get('lon__gte', 0)
    lon_lte = query_params.get('lon__lte', 0)

    queryset = queryset.filter(
        location_points__lat__gte=lat_gte,
        location_points__lat__lte=lat_lte,
        location_points__lon__gte=lon_gte,
        location_points__lon__lte=lon_lte,
    ).distinct()
    serializer = RiskAssessmentModelMapSerializer(queryset, many=True)
    data = {
        "summary": get_summary(queryset),
        "points": serializer.data
    }
    return data
