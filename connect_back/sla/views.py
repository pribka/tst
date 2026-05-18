from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction, IntegrityError

from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from common.models import BaseModel
from common.views import BaseModelViewSet

from common.catalogs.models import ContractorModel

from . import serializers, models


class SLAViewSet(BaseModelViewSet):
    model = models.SLAModel

    @action(methods=('post',), detail=False, url_path='set_objects')
    def set_sla(self, request, *args, **kwargs):
        data = request.data
        sla_id = data.get('sla')
        try:
            sla = models.SLAModel.objects.get(pk=sla_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('SLA не найден')
        related_objects_id = data.get('related_objects')
        if not isinstance(related_objects_id, list):
            raise drf_exceptions.ValidationError('Связанные объекты должны быть в списке')
        with transaction.atomic():
            for each in related_objects_id:
                try:
                    related_object = BaseModel.objects.super_get(pk=each)
                except (ValidationError, ObjectDoesNotExist):
                    raise drf_exceptions.ValidationError(f'объект {each} не найден')
                instance, created = models.SLARelatedObjectModel.objects.get_or_create(
                    sla=sla,
                    related_object=related_object,
                )
        return Response('ok')


    # @action(methods=('get', 'post'), detail=False, url_path='from_object/(?P<pk>[^/.]+)', url_name='from_object')
    # def from_object(self, request, *args, **kwargs):
    #     """
    #     get: Возвращает sla объекта по его id и id организации (гет-параметр organizaion)
    #     post: Создает или изменяет sla объекта по его id и id организации (ключ organization в data)
    #     """
    #     if request.method == 'GET':
    #         data = request.query_params
    #     else:
    #         data = request.data
    #
    #     # Получаем организацию
    #     org_id = data.get('organization')
    #     if not org_id:
    #         raise drf_exceptions.ValidationError('Organization required')
    #     try:
    #         org = ContractorModel.objects.get(pk=org_id)
    #     except (ValidationError, ObjectDoesNotExist):
    #         raise drf_exceptions.NotFound('Organization not found')
    #     user = request.user.profile
    #     user_organizations = user.my_organizations
    #     if org.pk not in user_organizations:
    #         raise drf_exceptions.PermissionDenied()
    #     # Получаем объект:
    #     obj_id = kwargs.get('pk')
    #     if not obj_id:
    #         raise drf_exceptions.ValidationError('Object id required')
    #     try:
    #         obj = BaseModel.objects.super_get(pk=obj_id)
    #     except (ValidationError, ObjectDoesNotExist):
    #         raise drf_exceptions.NotFound('Object not found')
    #     if request.method == 'GET':
    #         # Получаем sla:
    #         try:
    #             sla = models.SLAModel.objects.get(related_object=obj, organization=org)
    #         except ObjectDoesNotExist:
    #             return Response(dict())
    #         serializer = serializers.SLADetailSerializer(sla, context={'request': request, 'view': self})
    #         return Response(serializer.data)
    #     else:
    #         try:
    #             sla = models.SLAModel.objects.get(related_object=obj, organization=org)
    #         except ObjectDoesNotExist:
    #             data['related_object'] = obj_id
    #             serializer = serializers.SLACreateSerializer(data=data, context={'request': request, 'view': self})
    #         else:
    #             serializer = serializers.SLAUpdateSerializer(sla, data=data, context={'request': request, 'view': self})
    #         serializer.is_valid(raise_exception=True)
    #         instance = serializer.save()
    #         return Response(serializers.SLADetailSerializer(instance, context={'request': request, 'view': self}).data)

    @action(methods=('get',), url_path='(?P<pk>[^/.]+)/value', detail=False,)
    def get_sla_value(self, request, *args, **kwargs):
        related_object_id = kwargs.get('pk')
        try:
            related_object = BaseModel.objects.super_get(pk=related_object_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.NotFound('Запись не найдена')
        try:
            sla_value = related_object.sla_value
        except ObjectDoesNotExist:
            return Response(dict())
        serializer = serializers.SLAValueSerializer(sla_value, context={'request': request, 'view': self})
        return Response(serializer.data)

    # @action(methods=('get', 'post',), url_path='default/(?P<pk>[^/.]+)', detail=False, url_name='default')
    # def default(self, request, *args, **kwargs):
    #
    #     if request.method == 'GET':
    #         data = request.query_params
    #     else:
    #         data = request.data
    #     org_id = kwargs.get('pk')
    #     if not org_id:
    #         raise drf_exceptions.ValidationError('organization id required')
    #     try:
    #         org = ContractorModel.objects.get(pk=org_id)
    #     except (ValidationError, ObjectDoesNotExist,):
    #         raise drf_exceptions.ValidationError('Organization not found')
    #     user = request.user.profile
    #     user_organizations = user.my_organizations
    #     if org.pk not in user_organizations:
    #         raise drf_exceptions.PermissionDenied()
    #     # TODO добавить разрешение на изменение значения по умолчанию
    #     if request.method == 'GET':
    #         try:
    #             sla = models.SLAModel.objects.get(related_object__isnull=True, organization=org)
    #         except ObjectDoesNotExist:
    #             return Response(dict())
    #         serializer = serializers.SLADetailSerializer(sla, context={'request': request, 'view': self})
    #         return Response(serializer.data)
    #     try:
    #         sla = models.SLAModel.objects.get(related_object__isnull=True, organization=org)
    #     except ObjectDoesNotExist:
    #         data['related_object'] = None
    #         data['organization'] = org_id
    #         serializer = serializers.SLACreateSerializer(data=data, context={'request': request, 'view': self})
    #     else:
    #         data['organization'] = org_id
    #         serializer = serializers.SLAUpdateSerializer(sla, data=data, context={'request': request, 'view': self})
    #     serializer.is_valid(raise_exception=True)
    #     instance = serializer.save()
    #     return Response(serializers.SLADetailSerializer(instance, context={'request': request, 'view': self}).data)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
