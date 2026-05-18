from django.core.management.base import BaseCommand, CommandError

from common.catalogs.utils import get_admin_area_for_point

from sports_facilities_info import models


class Command(BaseCommand):
    help = "Management Catalogs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild_location_points',
            action='store_true',
            help='Rebuild areas in sports facilities local points.'
        )

    def handle(self, *args, **options):
        if options['rebuild_location_points']:
            qs = models.SportFacilityInfoModel.objects.filter(is_active=True, location_points__isnull=False).distinct()
            for each in qs:
                location_points = each.location_points.all()
                for location_point in location_points:
                    point = (location_point.lon, location_point.lat)

                    admin_area = get_admin_area_for_point(point, admin_level=6)
                    location_point.admin_area = admin_area
                    location_point.save(update_fields=('admin_area',))
                    print(f'set admin area {admin_area} for {location_point.address}')
            return 'ok'
