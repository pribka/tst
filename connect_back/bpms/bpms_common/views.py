import os
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image

from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.core.files import File as DjangoFile
from django.db.models import Q, Count
from django.db.utils import IntegrityError


from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication

from rest_framework_simplejwt.authentication import JWTAuthentication


from django_q.tasks import async_task

try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None

from common import serializers as common_serializers
from common import paginators
from common import utils as common_utils
from common.auth_classes import CsrfExemptSessionAuthentication
from common.models import (FileBaseModel,
                           File,
                           FolderModel,
                           BaseModel,
                           FileBaseUpdateModel)
from common.serializers import BaseFolderSerializer

from . import models, serializers, permissions
from bpms.chat.models import ChatModel


CHUNK_UPLOAD_ROOT = Path(tempfile.gettempdir()) / 'bpms_chunk_uploads'
CHUNK_UPLOAD_CACHE_TIMEOUT = 60 * 60

#
# class CounterpartyListView(generics.ListAPIView):
#     queryset = models.CounterpartyModel.objects.filter(is_active=True)
#     serializer_class = serializers.CounterpartyModelBaseSerializer
#     pagination_class = paginators.CustomPagination
#
#
# class ProgramListView(generics.ListAPIView):
#     queryset = models.ProgramModel.objects.filter(is_active=True)
#     serializer_class = serializers.ProgramBaseSerializer
#     pagination_class = paginators.CustomPagination
#
#
# class CostingObjectListView(generics.ListAPIView):
#     queryset = models.CostingObjectModel.objects.filter(is_active=True)
#     serializer_class = serializers.CostingObjectBaseSerializer
#     pagination_class = paginators.CustomPagination
#
#
# class SocialWebTypesListView(generics.ListAPIView):
#     queryset = models.SocialWebType.objects.filter(is_active=True)
#     serializer_class = serializers.SocialWebTypeSerializer
#
#
# class SocialURLsCreateView(generics.CreateAPIView):
#     queryset = models.SocialWebType.objects.all()
#     serializer_class = serializers.SocialURLsSerializer
#

class AttachmentMixIn:
    def get_object(self, instance_id):
        ct = models.BaseModel.objects.get(id=instance_id).ct
        return ct.model_class().objects.get(id=instance_id)


def _chunk_upload_cache_key(upload_id):
    return f'chunk_upload_response_{upload_id}'


def _sanitize_upload_id(upload_id):
    sanitized = re.sub(r'[^A-Za-z0-9._-]', '', str(upload_id or ''))
    if not sanitized:
        raise ValidationError({'message': 'Invalid upload id.'})
    return sanitized[:128]


def _sanitize_filename(filename):
    basename = os.path.basename(str(filename or 'upload.bin')).strip()
    return basename or 'upload.bin'


def _extract_recognized_text(payload):
    if isinstance(payload, str):
        return payload.strip()

    if isinstance(payload, dict):
        for key in ('text', 'recognized_text', 'transcript', 'result', 'message'):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for key in ('data', 'response'):
            nested = payload.get(key)
            if nested is not None:
                nested_text = _extract_recognized_text(nested)
                if nested_text:
                    return nested_text

    if isinstance(payload, list):
        text = '\n'.join(filter(None, (_extract_recognized_text(item) for item in payload))).strip()
        if text:
            return text

    return ''


def _recognize_voice_input(file_obj, filename='voice-input.bin', content_type='application/octet-stream'):
    try:
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)

        recognize_response = requests.post(
            settings.VOICE_INPUT_RECOGNIZE_URL,
            files={
                'file': (
                    _sanitize_filename(filename),
                    file_obj,
                    content_type or 'application/octet-stream'
                )
            },
            timeout=(10, 180)
        )
        recognize_response.raise_for_status()
    except requests.RequestException as error:
        raise ValidationError({'message': f'Voice input recognize request failed: {error}'})

    try:
        payload = recognize_response.json()
    except ValueError:
        payload = recognize_response.text

    text = _extract_recognized_text(payload)
    if not text:
        raise ValidationError({'message': 'Recognizer returned empty text.'})

    return {'text': text}


def _parse_chunk_upload_request(request, field_name='upload'):
    upload_id = request.POST.get('upload_id')
    if not upload_id:
        return None

    chunk_file = request.FILES.get(field_name)
    if chunk_file is None:
        raise ValidationError({'message': 'Chunk file not found.'})

    try:
        chunk_index = int(request.POST.get('chunk_index'))
        total_chunks = int(request.POST.get('total_chunks'))
    except (TypeError, ValueError):
        raise ValidationError({'message': 'Invalid chunk metadata.'})

    if chunk_index < 0 or total_chunks <= 0 or chunk_index >= total_chunks:
        raise ValidationError({'message': 'Invalid chunk ordering.'})

    return {
        'upload_id': _sanitize_upload_id(upload_id),
        'chunk_index': chunk_index,
        'total_chunks': total_chunks,
        'chunk_file': chunk_file,
        'original_name': _sanitize_filename(request.POST.get('original_name') or chunk_file.name),
        'is_confined': 'is_confined' in request.POST,
        'is_voice': request.POST.get('is_voice') in ('true', '1', 'True'),
        'is_voice_input': request.POST.get('is_voice_input') in ('true', '1', 'True'),
    }


def _get_chunk_upload_dir(upload_id):
    return CHUNK_UPLOAD_ROOT / upload_id


def _get_chunk_path(upload_dir, chunk_index):
    return upload_dir / f'{chunk_index:08d}.part'


def _store_chunk_file(chunk_meta):
    upload_dir = _get_chunk_upload_dir(chunk_meta['upload_id'])
    upload_dir.mkdir(parents=True, exist_ok=True)

    chunk_path = _get_chunk_path(upload_dir, chunk_meta['chunk_index'])
    with open(chunk_path, 'wb') as destination:
        for each_chunk in chunk_meta['chunk_file'].chunks():
            destination.write(each_chunk)
    return upload_dir


def _ensure_all_chunks_present(upload_dir, total_chunks):
    missing_chunks = [
        index for index in range(total_chunks)
        if not _get_chunk_path(upload_dir, index).exists()
    ]
    if missing_chunks:
        raise ValidationError({'message': 'Upload is incomplete.'})


def _assemble_chunks(upload_dir, total_chunks, filename):
    assembled_path = upload_dir / f'assembled_{filename}'
    with open(assembled_path, 'wb') as destination:
        for chunk_index in range(total_chunks):
            chunk_path = _get_chunk_path(upload_dir, chunk_index)
            with open(chunk_path, 'rb') as source:
                shutil.copyfileobj(source, destination)
    return assembled_path


def _create_uploaded_file_instance(assembled_path, filename, is_confined=False, is_voice=False):
    with open(assembled_path, 'rb') as assembled_file:
        django_file = DjangoFile(assembled_file, name=filename)
        instance = File.objects.create(
            is_confined=is_confined,
            is_voice=is_voice,
            upload=django_file
        )
        if is_voice and (not instance.is_voice or not instance.is_audio or instance.is_video):
            instance.is_voice = True
            instance.is_audio = True
            instance.is_video = False
            instance.save(update_fields=('is_voice', 'is_audio', 'is_video'))
        return instance


def _build_editor_upload_response(instance):
    url = instance.author_url
    if DOWNLOADER_PATH is not None:
        url = url + quote('&target=ckeditor')
    return {
        'urls': {
            'default': url
        }
    }


def _build_regular_upload_response(instance):
    return common_serializers.AppFileSerializer(instance).data


def _build_regular_upload_list_response(instance):
    return [_build_regular_upload_response(instance)]


def _validate_uploaded_image(assembled_path):
    try:
        with Image.open(assembled_path):
            pass
    except OSError:
        raise ValidationError('not_image')


def _handle_chunk_upload(request, response_builder, *, field_name='upload', validator=None):
    chunk_meta = _parse_chunk_upload_request(request, field_name=field_name)
    if chunk_meta is None:
        return None

    cached_response = cache.get(_chunk_upload_cache_key(chunk_meta['upload_id']))
    if cached_response is not None:
        return JsonResponse(data=cached_response, status=status.HTTP_200_OK, safe=False)

    upload_dir = _store_chunk_file(chunk_meta)

    if chunk_meta['chunk_index'] < chunk_meta['total_chunks'] - 1:
        return JsonResponse(
            data={
                'status': 'chunk_received',
                'upload_id': chunk_meta['upload_id'],
                'chunk_index': chunk_meta['chunk_index'],
            },
            status=status.HTTP_200_OK,
            safe=False
        )

    _ensure_all_chunks_present(upload_dir, chunk_meta['total_chunks'])
    assembled_path = _assemble_chunks(
        upload_dir,
        chunk_meta['total_chunks'],
        chunk_meta['original_name']
    )

    try:
        if validator is not None:
            validator(assembled_path)

        if chunk_meta['is_voice_input']:
            with open(assembled_path, 'rb') as assembled_file:
                response_data = _recognize_voice_input(
                    assembled_file,
                    filename=chunk_meta['original_name'],
                    content_type=getattr(chunk_meta['chunk_file'], 'content_type', 'application/octet-stream')
                )
        else:
            instance = _create_uploaded_file_instance(
                assembled_path,
                chunk_meta['original_name'],
                is_confined=chunk_meta['is_confined'],
                is_voice=chunk_meta['is_voice']
            )
            response_data = response_builder(instance)

        cache.set(
            _chunk_upload_cache_key(chunk_meta['upload_id']),
            response_data,
            timeout=CHUNK_UPLOAD_CACHE_TIMEOUT
        )
        return JsonResponse(data=response_data, status=status.HTTP_200_OK, safe=False)
    finally:
        shutil.rmtree(upload_dir, ignore_errors=True)


class AttachmentViewSet(GenericViewSet):
    queryset = BaseModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated, permissions.GetAttachmentsBasePermission)
    pagination_class = paginators.BreadCramsCustomPaginator

    def get_serializer_class(self):
        if self.action == 'add_file':
            return serializers.FileAttachmentSerializer
        return serializers.FileAndFolderSerializer

    def get_object(self):
        instance_id = self.kwargs.get('pk')
        if not instance_id:
            raise NotFound()
        try:
            obj = BaseModel.objects.super_get(pk=instance_id)
        except ObjectDoesNotExist:
            raise NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        folder_id = request.GET.get('folder', None)
        search_string = request.GET.get('search', None)
        self.check_object_permissions(request, instance)

        try:
            folder = FolderModel.objects.get(id=folder_id)
        except ObjectDoesNotExist:
            folder = None
        
        if isinstance(instance, ChatModel):
            files_ids = File.objects.filter(
                is_active=True,
                related_attaches__related_object__messagemodel__chat=instance,
                related_attaches__related_object__is_active=True,
                related_attaches__related_object__messagemodel__is_deleted=False,
            ).values_list('pk', flat=True)
            # files_ids = instance.messages.filter(
            #     is_active=True,
            #     is_deleted=False,
            #     attachments__isnull=False
            # ).values(
            #     'attachments__pk',
            #     'attachments__ct'
            # ).distinct().exclude(attachments__pk__isnull=True)
            # # TODO выходим сразу на аттачи?
        else:
            files_ids = File.objects.filter(
                is_active=True,
                related_attaches__related_object=instance,
                related_attaches__folder=folder,
            ).values_list('pk', flat=True)
            #             attachments_relations = instance.files.filter(folder=folder).values_list('file', flat=True)

        if folder:
            folders_qs = folder.get_children()
        else:
            folders_qs = instance.folders.filter(parent__isnull=True)
        folders_ids = folders_qs.values_list('pk', flat=True)
        breadcrumb = []
        folder_name = None

        if folder:
            breadcrumb.append({'name': 'Все файлы', 'folder_id': None})
            folder_name = folder.name
            if folder.parent:
                ancestors = folder.get_ancestors(include_self=False).order_by('level')
                for each in ancestors:
                    breadcrumb.append({'name': each.name, 'folder_id': str(each.pk)})

        if search_string and search_string != '':
            deleted = FolderModel.objects.filter(is_active=False).get_descendants(include_self=True)
            if folder:
                folders = folder.get_descendants(include_self=True)

                folders = folders.filter(is_active=True).exclude(pk__in=deleted)
                files = File.objects.filter(
                    is_active=True,
                    related_attaches__folder__in=folders,
                    related_attaches__related_object=instance,
                )
                # files = FileBaseModel.objects.filter(folder__in=folders,
                #                                      file__is_active=True)
            else:
                folders = FolderModel.objects.filter(
                    is_active=True,
                    related_object=instance,
                ).exclude(pk__in=deleted)
                if isinstance(instance, ChatModel):
                    files = File.objects.filter(
                        is_active=True,
                        related_attaches__related_object__messagemodel__chat=instance,
                        related_attaches__related_object__is_active=True,
                        related_attaches__related_object__messagemodel__is_deleted=False,
                    ).exclude(related_attaches__folder__in=deleted)
                    # attachments_relations = instance.messages.filter(
                    #     is_active=True,
                    #     is_deleted=False,
                    #     attachments__isnull=False).distinct().exclude(attachments__pk__isnull=True)
                    # files = FileBaseModel.objects.filter(related_object__id__in=attachments_relations,
                    #                                      file__is_active=True).exclude(folder__in=deleted)
                else:
                    files = File.objects.filter(
                        is_active=True,
                        related_attaches__related_object=instance,
                    ).exclude(related_attaches__folder__in=deleted)
                    # files = FileBaseModel.objects.filter(related_object=instance,
                    #                                      file__is_active=True).exclude(folder__in=deleted)

            folders = folders.filter(Q(name__icontains=search_string) | Q(description__icontains=search_string))
            files = files.filter(Q(name__icontains=search_string) | Q(description__icontains=search_string))
            folders_ids = folders.values_list('pk', flat=True)
            files_ids = files.values_list('pk', flat=True)

            total_qs = files_ids.union(folders_ids).order_by('-ct', '-created_at')
        else:
            total_qs = files_ids.union(folders_ids).order_by('-ct', '-created_at')
            # total_qs = total_qs.filter(Q(id__in=folders_ids) | Q(id__in=attachments_relations)).order_by('-ct',
            #                                                                                              '-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(total_qs, request, self)

        context = {"related_object": instance.pk, 'request': request}
        serialized_data = serializers.CachedFileAndFolderSerializer(page, many=True, context=context).data
        paginate_response = paginator.get_paginated_response(serialized_data, breadcrumb, folder_name)

        return paginate_response
    
    def set_update_time(self, instance):
        '''
        При вызове сохраняет текущее времяв поле updated_at
        модели common.FileBaseUpdateModel если запись 
        с related_object=instance существует или создает новую
        запись в случае отсутствия
        '''
        if FileBaseUpdateModel.objects.filter(is_active=True, related_object=instance).exists():
            FileBaseUpdateModel.objects.filter(
                is_active=True,
                related_object=instance).order_by('-created_at').first().save()
        else:
            FileBaseUpdateModel.objects.create(related_object=instance)

    @action(
        methods=('post',),
        detail=True,
        url_path='add_files',
        permission_classes=(permissions.UpdateAttachmentsPermission,),
    )
    def add_file(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        files = request.data.get('files', [])
        files_already = []
        folder = request.data.get('folder', None)
        if folder:
            folder = FolderModel.objects.get(id=folder)
        for file in files:

            objs = FileBaseModel.objects.filter(folder=folder, related_object=instance, file_id=file)
            if objs.exists():
                files_already.append(file)
            else:
                FileBaseModel.objects.create(folder=folder, related_object=instance, file_id=file)

        files_data = File.objects.filter(id__in=files)
        files_data_id = list(files_data.values_list('pk', flat=True))
        for each in files_data_id:
            cache.delete(f"CachedFileAndFolderSerializer_{each}_ro_{instance.pk}")
        serialized_data = serializers.FileAttachmentSerializer(files_data, many=True).data

        for item in serialized_data:
            if item['id'] in files_already:
                item['created'] = False
            else:
                item['created'] = True

        self.set_update_time(instance)

        return Response(data=serialized_data, status=status.HTTP_200_OK)

    @action(
        methods=('get',),
        detail=True,
        url_path='folders',
        permission_classes=(IsAuthenticated, permissions.GetAttachmentsBasePermission),
    )
    def get_folders(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        folder_id = request.query_params.get('folder')
        if folder_id:
            try:
                folder = FolderModel.objects.get(pk=folder_id, is_active=True)
            except FolderModel.DoesNotExist:
                raise ValidationError('Folder not found')
        else:
            folder = None
        queryset = FolderModel.objects.filter(
            is_active=True,
            parent=folder,
            related_object=instance,
        ).order_by('name')
        paginator = paginators.CustomPagination()
        page = paginator.paginate_queryset(queryset, request, self)
        s_data = BaseFolderSerializer(page, many=True).data
        return paginator.get_paginated_response(s_data)

    @action(
        methods=('post',),
        detail=True,
        url_path='add_folder',
        permission_classes=(permissions.UpdateAttachmentsPermission,),
    )
    def add_folder(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        data = self.request.data.copy()
        data['related_object'] = kwargs.get('pk')
        folder_serializer = common_serializers.FolderCreateSerializer(data=data)
        folder_serializer.is_valid(raise_exception=True)
        folder_serializer.save()
        self.set_update_time(instance)
        return Response(data=folder_serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('put',),
        detail=True,
        url_path='update_folder',
        permission_classes=(permissions.UpdateAttachmentsPermission,),
    )
    def update_folder(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        try:
            folder = instance.folders.get(pk=data.get('id'))
        except ObjectDoesNotExist:
            raise ValidationError('Folder not found.')
        serializer = common_serializers.FolderUpdateSerializer(instance=folder, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('patch',),
        detail=True,
        url_path='update_file',
        permission_classes=(permissions.UpdateAttachmentsPermission,),
    )
    #  TODO ендпоинт не работает! Что с ним делать?
    def update_file(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        # self.check_object_permissions(request, instance)
        # try:
        #     file = instance.folders.get(pk=data.get('id'))
        # except ObjectDoesNotExist:
        #     raise ValidationError('Folder not found.')
        serializer = common_serializers.FileUpdateSerializer(instance=instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('post',),
        detail=True,
        url_path='remove_files',
        permission_classes=(permissions.UpdateAttachmentsPermission,),
    )
    def remove_file(self, request, *args, **kwargs):
        instance = self.get_object()
        files_list = request.data.get('files', [])
        folders_list = request.data.get('folders', [])
        folder_id = request.data.get('folder', None)
        if folder_id:
            try:
                folder = instance.folders.get(pk=folder_id)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found.')
        else:
            folder = None
        files_relation = FileBaseModel.objects.filter(file__in=files_list,
                                                      file__is_dynamic=False,
                                                      folder=folder,
                                                      related_object=instance)
        files_relation.delete()
        for each in files_list:
            cache.delete(f'CachedFileAndFolderSerializer_{each}_ro_{instance.pk}')
        folders = instance.folders.filter(pk__in=folders_list, parent=folder, related_object=instance)
        for each in folders:
            each.delete()
            cache.delete(f'CachedFileAndFolderSerializer_{each.pk}_ro_{instance.pk}')
        self.set_update_time(instance)

        return Response(data={'status': 'ok'}, status=status.HTTP_200_OK)

    @action(
        methods=('post',),
        detail=True,
        url_path='move_files',
        permission_classes=(permissions.UpdateAttachmentsPermission,)
    )
    def move_files(self, request, *args, **kwargs):
        instance = self.get_object()
        files_list = request.data.get('files', [])
        folders_list = request.data.get('folders', [])
        folder_id = request.data.get('folder', None)
        current_folder_id = request.data.get('current_folder', None)
        if current_folder_id:
            try:
                current_folder = instance.folders.get(pk=current_folder_id)
            except ObjectDoesNotExist:
                raise ValidationError('Current folder not found.')
        else:
            current_folder = None
        if folder_id:
            try:
                folder = instance.folders.get(pk=folder_id)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found.')
        else:
            folder = None
        files = instance.files.filter(
            file_id__in=files_list,
            file__is_dynamic=False,
            folder=current_folder,
        )
        for file in files:
            file.folder = folder
            try:
                file.save(update_fields=('folder',))
                cache.delete_pattern(f'CachedFileAndFolderSerializer_{file.file.pk}_ro_{instance.pk}')
            except IntegrityError:
                pass
        folders = instance.folders.filter(pk__in=folders_list, related_object=instance)
        for each in folders:
            each.parent = folder
            each.save()
            cache.delete_pattern(f'CachedFileAndFolderSerializer_{each.pk}_ro_{instance.pk}')

        return Response(data={'status': 'ok'}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='aggregate',)
    def get_aggregate(self, request, *args, **kwargs):
        instance = self.get_object()
        folder = request.query_params.get('folder')
        if folder:
            try:
                folder = instance.folders.get(pk=folder)
            except ObjectDoesNotExist:
                raise NotFound('Folder not found.')
            descendants = folder.get_descendants(include_self=True).filter(is_active=True)
            deleted = FolderModel.objects.filter(is_active=False).get_descendants(include_self=True).values_list('pk',
                                                                                                                 flat=True)
            descendants = descendants.exclude(pk__in=deleted)
            folders_count = descendants.count() - 1
            files_count = descendants.aggregate(files_count=Count('related_files',
                                                                  filter=Q(related_files__file__is_active=True)
                                                                         & (Q(related_files__folder__in=descendants)
                                                                            | Q(related_files__folder__isnull=True))
                                                                  ))['files_count']
        else:
            folders = instance.folders.filter(is_active=True)
            deleted = FolderModel.objects.filter(is_active=False).get_descendants(include_self=True)
            folders = folders.exclude(pk__in=deleted)
            folders_count = folders.count()
            files_count = instance.files.filter(is_active=True).exclude(folder__in=deleted).distinct('file_id').count()

        if isinstance(instance, ChatModel):
            attachments_relations = instance.messages.filter(
                is_active=True,
                is_deleted=False,
                attachments__isnull=False).prefetch_related('attachments').distinct().exclude(attachments__pk__isnull=True)
            files_count = FileBaseModel.objects.filter(related_object__id__in=attachments_relations,
                                                       file__is_active=True).count()

        return Response({'folders': folders_count, 'files': files_count})

    @action(methods=('post',), detail=True, url_path='zip')
    def create_zip(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user.profile
        folder_id = request.data.get('folder')
        if folder_id:
            try:
                folder = instance.folders.get(pk=folder_id)
            except ObjectDoesNotExist:
                raise NotFound()
        else:
            folder = None
        files_from = common_utils.FilesFrom.related_files
        already_working = cache.get(
            common_utils.get_already_working_key(
                user.pk,
                folder,
                files_from,
                instance=instance
            ),
            False
        )
        if not already_working:
            async_task(common_utils.create_zip_file, user, folder, files_from, instance, q_options={'timeout': 600})
        return Response({'already_working': already_working})


class UploadForEditorView(APIView):
    authentication_classes = (
        JWTAuthentication,
        BasicAuthentication,
        CsrfExemptSessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chunk_response = _handle_chunk_upload(
            request,
            _build_editor_upload_response,
            field_name='upload',
            validator=_validate_uploaded_image
        )
        if chunk_response is not None:
            return chunk_response
        if not request.FILES:
            raise ValidationError("Files not found.")
        file = request.FILES.getlist('upload')
        try:
            Image.open(file[0])
        except OSError:
            raise ValidationError('not_image')
        instance = File.objects.create(upload=file[0])
        return JsonResponse(data=_build_editor_upload_response(instance), status=status.HTTP_200_OK, safe=False)


class UploadView(APIView):
    authentication_classes = (
        JWTAuthentication,
        BasicAuthentication,
        CsrfExemptSessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chunk_response = _handle_chunk_upload(
            request,
            _build_regular_upload_list_response,
            field_name='upload'
        )
        if chunk_response is not None:
            return chunk_response
        if not request.FILES:
            raise ValidationError({'message': 'File not found.'})
        files = request.FILES.getlist('upload')
        is_confined = 'is_confined' in request.POST
        is_voice = request.POST.get('is_voice') in ('true', '1', 'True')
        is_voice_input = request.POST.get('is_voice_input') in ('true', '1', 'True')

        if is_voice_input:
            recognized_texts = []
            for file in files:
                recognized_payload = _recognize_voice_input(
                    file,
                    filename=getattr(file, 'name', 'voice-input.bin'),
                    content_type=getattr(file, 'content_type', 'application/octet-stream')
                )
                text = recognized_payload.get('text', '').strip()
                if text:
                    recognized_texts.append(text)

            return JsonResponse(
                data={'text': '\n'.join(recognized_texts).strip()},
                status=status.HTTP_200_OK,
                safe=False
            )

        instances = []
        for file in files:
            instance = File.objects.create(
                is_confined=is_confined,
                is_voice=is_voice,
                upload=file
            )
            if is_voice and (not instance.is_voice or not instance.is_audio or instance.is_video):
                instance.is_voice = True
                instance.is_audio = True
                instance.is_video = False
                instance.save(update_fields=('is_voice', 'is_audio', 'is_video'))
            instances.append(_build_regular_upload_response(instance))
        return JsonResponse(data=instances, status=status.HTTP_200_OK, safe=False)
