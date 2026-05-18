import os
from io import BytesIO
import subprocess
from tempfile import TemporaryDirectory, NamedTemporaryFile
from urllib.parse import quote

from django.core.files import File as DjangoFile
from django.template import Template, Context

from rest_framework import exceptions as drf_exceptions

from common.models import File

from bkz3.settings import DOWNLOADER_PATH, BACKEND_URL

from . import models

def get_serialized_doc_file(instance):
    from common.serializers import AppFileSerializer
    doc_file = instance.doc_file
    if not doc_file:
        return None
    s_data = AppFileSerializer(doc_file).data
    if DOWNLOADER_PATH is not None:
        parent_path = quote(f"?obj={instance.pk}&id={s_data.get('id')}&target=doc_file")
        s_data['path'] = f'{BACKEND_URL}{DOWNLOADER_PATH}/?path={parent_path}'
    return s_data


def validate_doc_file(doc_file, request):
    if doc_file:
        user = request.user.profile
        if not doc_file.author == user:
            raise drf_exceptions.ValidationError({"message": "Файл не найден"})
    return doc_file


def convert_content_to_doc_file(instance, file_type='odt'):
    content = instance.content
    with TemporaryDirectory() as tmpdir:
        with NamedTemporaryFile(mode='w+', dir=tmpdir) as tmp_source:
            tmp_source.write(content)
            tmp_source.seek(0)

            try:
                result = subprocess.check_output(
                    ['soffice', '--headless', '--convert-to', file_type, '--outdir', tmpdir, tmp_source.name],
                    stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError:
                raise drf_exceptions.ValidationError()
            except OSError:
                raise drf_exceptions.ValidationError()
            if result.startswith(b'Error'):
                raise drf_exceptions.ValidationError()
        with open(f"{tmp_source.name}.{file_type}", 'rb') as target_file:
            stream = BytesIO(target_file.read())
    return stream


def create_doc_file(instance):
    stream = convert_content_to_doc_file(instance)
    django_file = DjangoFile(file=stream, name=f"{instance.name}.odt")
    file = File()
    file.upload = django_file
    file.save()
    return file


def update_doc_file(instance):
    stream = convert_content_to_doc_file(instance)
    django_file = DjangoFile(file=stream, name=f"{instance.name}.odt")
    doc_file = instance.doc_file
    if doc_file:
        doc_file.upload = django_file
        doc_file.save()
    else:
        file = File()
        file.upload = django_file
        file.save()
        instance.doc_file = file
        instance.save()


def render_content(validated_data):
    template = validated_data.get('template')
    html_template = Template(template.content)
    context = Context(validated_data)
    return html_template.render(context)
