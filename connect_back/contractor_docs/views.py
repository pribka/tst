import subprocess
from urllib.parse import quote
from tempfile import NamedTemporaryFile, TemporaryDirectory
from io import BytesIO

from django.http.response import HttpResponse, FileResponse

from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app_info.models import AppInfo
from common.views import BaseCatalogViewSet

from . import models, serializers, utils


class ContractorDocTemplateModelViewSet(BaseCatalogViewSet):
    model = models.ContractorDocTemplateModel


class ContractorDocModelViewSet(BaseCatalogViewSet):
    model = models.ContractorDocModel

    @action(methods=('get',), detail=True, url_path='action_info', permission_classes=(IsAuthenticated,))
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                'edit': {'availability': True},
                'delete': {'availability': True},
                'send': {'availability': True}
            }
        elif instance.author == request.user.profile:
            actions = {
                'send': {'availability': True},
            }
        return Response({'actions': actions})

    @action(methods=('post',), detail=False, url_path='content')
    def get_content(self, request, *args, **kwargs):
        serializer = serializers.ContractorDocContentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"content": utils.render_content(serializer.validated_data)})

    @action(methods=('get',), detail=False, url_path='file_types', permission_classes=(IsAuthenticated,))
    def get_file_types(self, request, *args, **kwargs):
        try:
            file_types = AppInfo.objects.get(code='contractor_docs__file_types', is_active=True).metadata
        except AppInfo.DoesNotExist:
            file_types = [
                {
                    "name": "ODT",
                    "icon": "odt"
                },
                {
                    "name": "PDF",
                    "icon": "pdf"
                }
            ]
        return Response(file_types)

    # @action(methods=('get',), detail=True, url_path='download', permission_classes=(IsAuthenticated,))
    # def download(self, request, *args, **kwargs,):
    #     instance = self.get_object()
    #     file_type = request.query_params.get('file_type', 'pdf').lower()
    #     if not instance.get_detail_permission(request):
    #         raise drf_exceptions.PermissionDenied()
    #     stream = utils.convert_content_to_doc_file(instance, file_type)
    #     response = FileResponse(stream, filename=f'{quote(instance.name)}.{file_type}', as_attachment=True)
    #     return response

    @action(methods=('post',), detail=True, url_path='send', permission_classes=(IsAuthenticated,))
    def send(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.author == request.user.profile:
            raise drf_exceptions.PermissionDenied()

        #  TODO добавить отправку в 1С.

        instance.delivery_status_id = 'delivered'
        instance.locked = True
        instance.save(update_fields=('delivery_status_id', 'locked'))
        s_data = serializers.ContractorDocModelDetailSerializer(instance=instance, context={'request': request}).data
        return Response(s_data)
