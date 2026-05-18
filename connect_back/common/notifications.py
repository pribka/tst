from datetime import timedelta

from django.utils import timezone

import humanize

from bkz3.settings import ZIPFILES_EXPIRE

from common.humanize import get_humanized_timezone
from common.utils import convert_to_local_timezone

from notifications import event_types


def notify_about_zipfile_created(recipients, url, folder_name, file_size):
    expire_date = convert_to_local_timezone(timezone.now() + timedelta(seconds=ZIPFILES_EXPIRE))
    event_types.ZipFileCreated().create_notification(
        recipients=recipients,
        url=url,
        folder_name=folder_name,
        expire=f"{expire_date.strftime('%d.%m.%Y %H:%M')} {get_humanized_timezone()}",
        file_size=humanize.filesize.naturalsize(file_size)
        )
