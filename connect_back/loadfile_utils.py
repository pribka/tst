import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()

import glob
from common.models import File, FileBaseModel, FolderModel
from bpms.workgroups.models import BaseModel
from bkz3.settings import MEDIA_ROOT

short_path = f'{MEDIA_ROOT}/prst_files'
related_obj = None
if len(sys.argv) > 1:
    related_obj = BaseModel.objects.get(id=sys.argv[1])
    print(related_obj)
    # parse_files(sys.argv[0])


def parse_files(file_path=short_path, parent=None):
    in_current_dirct = glob.glob(file_path + '//*')

    if not in_current_dirct:
        parent = None
    for path in in_current_dirct:
        path_name = path.split('/')[-1]
        if os.path.isfile(path):
            try:
                file = File.objects.create(upload=path.replace(MEDIA_ROOT + '/', ''),
                                           name=path_name)
            except Exception as e:
                print(path)
                print(e)
                continue
            if parent:
                FileBaseModel.objects.create(folder=parent,
                                             file=file,
                                             related_object=related_obj,
                                             )
            else:
                FileBaseModel.objects.create(related_object=related_obj,
                                             file=file)
        else:
            folder = FolderModel.objects.create(parent=parent,
                                                related_object=related_obj,
                                                name=path_name,
                                                )
            parse_files(path, parent=folder)


if related_obj:
    parse_files()
