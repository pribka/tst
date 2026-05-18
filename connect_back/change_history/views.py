from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response

from common.views import BaseModelViewSet
from common.models import BaseModel

from . import models, permissions


class ChangeHistoryModelViewSet(BaseModelViewSet):
    model = models.ChangeHistoryModel
    permission_classes = (IsAuthenticated, permissions.ChangeHistoryModelDetailPermission)

    def get_queryset(self):
        request = self.request
        related_object_id = self.request.query_params.get('related_object')
        queryset = self.model.get_queryset(request)
        if self.action == 'list':
            if related_object_id:
                try:
                    related_object = BaseModel.objects.super_get(related_object_id)
                except BaseModel.DoesNotExist:
                    return queryset.none()
                if not related_object.get_detail_permission(request):
                    return queryset.none()
                queryset = queryset.filter(related_object_id=related_object_id)
            else:
                return queryset.none()
        return queryset

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
