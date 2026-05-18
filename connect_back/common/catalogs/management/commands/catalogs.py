import json

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError


from pathlib import Path
from os import listdir

from django.contrib.gis.utils import LayerMapping
from common.catalogs.models import LocationAdminAreaModel, locationadminareamodel_mapping

from common.catalogs.mapping import OSM_KATO_MAPPING

file_path = Path(__file__).resolve().parent.parent.parent / "osm_regions"


class Command(BaseCommand):
    help = "Management catalogs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--load_admin_areas',
            action='store',
            help='Load [load_admin_areas] to database.',
            required=False,
            nargs='?',
            metavar='load_admin_areas'
        )
        parser.add_argument(
            '--prepare_admin_areas',
            action='store',
            help='Prepare [file_name] for load'
        )

    def handle(self, *args, **options):
        if options['load_admin_areas']:
            with transaction.atomic():
                file_name = options['load_admin_areas']
                if file_name == 'all':
                    for each in listdir(file_path):
                        path = file_path / each
                        lm = LayerMapping(LocationAdminAreaModel, path, locationadminareamodel_mapping, transform=False)
                        lm.save(strict=True, verbose=True)
                else:
                    path = file_path / file_name
                    lm = LayerMapping(LocationAdminAreaModel, path, locationadminareamodel_mapping, transform=False)
                    lm.save(strict=True, verbose=True)
                for each in LocationAdminAreaModel.objects.all():
                    if each.parent_osm_id:
                        each.parent = LocationAdminAreaModel.objects.get(osm_id=each.parent_osm_id)
                        each.save(update_fields=('parent',))
        elif options['prepare_admin_areas']:
            file_name = options['prepare_admin_areas']
            path = file_path / file_name
            with open(path, 'rb',) as file:
                geojson = json.loads(file.read())
                features = geojson['features']
                parent_id = get_parent_id(features)
                for each in features:
                    geometry = each['geometry']
                    if not geometry['type'] == 'MultiPolygon':
                        geometry['type'] = 'MultiPolygon'
                        geometry['coordinates'] = [geometry['coordinates']]
                    properties = each['properties']
                    if properties['osm_id'] < 0:
                        properties['osm_id'] = -properties['osm_id']
                    properties['kato_code'] = OSM_KATO_MAPPING[properties['osm_id']]
                    if 'name_ru' not in properties:
                        properties['name_kk'] = properties.pop('name')
                        properties['name_ru'] = ""
                    admin_level = each['properties']['admin_level']
                    if admin_level == 6:
                        each['properties']['parent'] = parent_id
                    else:
                        each['properties']['parent'] = None
            with open(path, 'wt') as file:
                file.write(json.dumps(geojson))
            return 'ok'


def get_parent_id(features):
    parent_id = None
    for each in features:
        if each['properties']['admin_level'] == 4:
            parent_id = each['properties']['osm_id']
    return parent_id


