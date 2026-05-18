from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Prefetch

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions as drf_exceptions

from gallery.models import GalleryModel

from . import models
from . import serializers
from . import permissions


class GalleryModelViewSet(viewsets.ModelViewSet):
    queryset = models.GalleryModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated, permissions.GalleryModelUpdatePermission)
    model = models.GalleryModel

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.GalleryModelListSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.GalleryModelUpdateSerializer
        elif self.action == 'create':
            return serializers.GalleryModelCreateSerializer

    def get_queryset(self):
        queryset = self.queryset
        related_object_id = self.request.query_params.get('related_object')
        if not related_object_id or not isinstance(related_object_id, str):
            return queryset.none()
        try:
            related_object = models.BaseModel.objects.super_get(related_object_id)
        except ObjectDoesNotExist:
            return queryset.none()
        if not related_object.get_detail_permission(self.request):
            return queryset.none()
        return queryset.filter(
            related_object=related_object,
            file__is_active=True,
        ).order_by('-is_main', 'sort', 'created_at')