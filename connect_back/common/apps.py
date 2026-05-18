from django.apps import AppConfig
import os
from bkz3.settings import AVATAR_ROOT, ZIPFILES_ROOT, RECORDS_ROOT


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self):
        import common.signals
        if not os.path.exists(AVATAR_ROOT):
            os.mkdir(AVATAR_ROOT)
        if not os.path.exists(ZIPFILES_ROOT):
            os.mkdir(ZIPFILES_ROOT)
        if not os.path.exists(RECORDS_ROOT):
            os.mkdir(RECORDS_ROOT)
