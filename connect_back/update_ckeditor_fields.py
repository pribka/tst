import os
import re
from math import ceil
from bs4 import BeautifulSoup
import django
from django.db import IntegrityError
from django.apps import apps
from django.db.models import TextField
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bkz3.settings')
django.setup()
from bkz3.settings import BACKEND_URL, DOWNLOADER_PATH
from common.models import File, CKEditorFileModel


def main():
    ckeditor_models = (
        ('bpms_common', 'NewsModel'),
        ('comments', 'CommentModel'),
        ('common', 'Events'),
        ('tasks', 'TaskModel'),
        ('meetings', 'PlannedMeetingModel'),
        ('workgroups', 'WorkgroupModel'),
    )
    if DOWNLOADER_PATH is None:
        print("DOWNLOADER_PATH is None. Please, set DOWNLOADER_PATH.")
        return
    for app_label, model_name in ckeditor_models:
        model = apps.get_model(app_label, model_name)
        print(f"\nUpdating for {model._meta.label}...")
        qs = model.objects.all()
        count = ceil(qs.count() / 100)
        for each in range(count):
            instances = qs[each * 100:each * 100 + 100]
            for instance in instances:
                fields = instance._meta.local_fields
                new_values = dict()
                for field in fields:
                    if isinstance(field, TextField):
                        value = getattr(instance, field.name, '')
                        if value is None or not value.strip():
                            continue
                        soup = BeautifulSoup(value, 'lxml')
                        img_urls = set(img_tag.get('src', '') for img_tag in soup.find_all('img'))
                        changed = False
                        for each in img_urls:
                            match = re.match(
                                re.escape(BACKEND_URL) +
                                r'/media/user_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/(.*)',
                                each
                            )
                            try:
                                user_id = match.group(1)
                            except AttributeError:
                                continue
                            try:
                                file_name = match.group(2)
                            except AttributeError:
                                continue
                            try:
                                file = File.objects.get(
                                    author_id=user_id,
                                    upload=f"user_{user_id}/{file_name}",
                                )
                            except File.DoesNotExist:
                                continue
                            try:
                                CKEditorFileModel.objects.create(
                                    file=file,
                                    related_object=instance,
                                    field_name=field.name
                                )
                            except IntegrityError:
                                continue
                            value = value.replace(
                                each,
                                f"{DOWNLOADER_PATH}/?path=%3Fid%3D{file.pk}%26obj%3D{instance.pk}%26target%3Dckeditor"
                            )
                            changed = True
                        if changed:
                            new_values[field.name] = value
                    else:
                        continue
                if new_values:
                    instance._meta.model.objects.filter(pk=instance.pk).update(**new_values)
                    print(f"Updated urls for {instance.pk}")
                else:
                    print(f"Has no urls for {instance.pk}")
    print('Done.')


if __name__ == '__main__':
    main()
