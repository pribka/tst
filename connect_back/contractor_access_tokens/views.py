from django.utils import timezone
from django.http.response import Http404
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from common.paginators import CustomPagination
from common.catalogs import models as catalogs_models

from contractor_permissions.utils import check_contractor_permission

from . import serializers


class ContractorAccessModelViewSet(ModelViewSet):
    queryset = catalogs_models.Contractor1CAccessTokenModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.ContractorAccessTokenCreateSerializer
        else:
            return serializers.ContractorAccessTokenListSerializer

    def perform_update(self, serializer):
        raise drf_exceptions.MethodNotAllowed('PUT/PATCH')

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.contractor.get_update_permission(request):
            return Http404
        serializer_class = self.get_serializer_class()
        data = serializer_class(instance, context={'request': request, 'view': self}).data
        return Response(data)

    def list(self, request, *args, **kwargs):
        paginator = CustomPagination()
        qs = self.queryset
        contractor_id = request.query_params.get('contractor')
        if not contractor_id:
            qs = qs.none()
        else:
            try:
                contractor = catalogs_models.ContractorModel.objects.get(is_active=True, pk=contractor_id)
            except (ValidationError, ObjectDoesNotExist):
                qs = qs.none()
            else:
                if contractor.get_update_permission(request):
                    qs = qs.filter(contractor_id=contractor_id)
                else:
                    qs = qs.none()
        qs = qs.order_by('-created_at')
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer_class = self.get_serializer_class()
        data = serializer_class(page, many=True, context={'request': request, 'view': self}).data
        return paginator.get_paginated_response(data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.contractor.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        now = timezone.now()
        instance.deleted_at = now
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
