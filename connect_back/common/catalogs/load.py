from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import LocationAdminAreaModel, locationadminareamodel_mapping


file_path = Path(__file__).resolve().parent / "osm_regions" / "AkmolaRegion.json"


def run(verbose=True):
    lm = LayerMapping(LocationAdminAreaModel, file_path, locationadminareamodel_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
