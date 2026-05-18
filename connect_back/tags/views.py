from django.core.exceptions import ValidationError, ObjectDoesNotExist

from rest_framework import status, exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


from common.models import BaseModel
from common.views import BaseModelViewSet

from . import models, serializers


class TagModelViewSet(BaseModelViewSet):
    model = models.TagModel
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        qs = self.model.get_queryset(request)
        related_object_id = request.query_params.get('related_object')
        
        context = {
            'request': request,
            'view': self,
        }
        if related_object_id:
            context['related_object'] = related_object_id
            qs = qs.prefetch_related('tag_object_through')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, self)
        data = serializers.TagModelListSerializer(
            page,
            many=True,
            context=context,
        ).data
        response = paginator.get_paginated_response(data)
        return response

    @action(methods=('post',), detail=True, url_path='discard',)
    def discard(self, request, *args, **kwargs):
        tag = self.get_object()
        serializer = serializers.TagDiscardSerializer(
            instance=tag,
            data=request.data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        related_object_id = request.data.get('related_object')
        try:
            related_object = BaseModel.objects.super_get(related_object_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('related_object not found.')
        try:
            related_object_through = models.TagRelatedObjectThrough.objects.get(
                tag=instance,
                related_object=related_object,
            )
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('not found')
        serializer = serializers.TagModelUpdateSerializer(
            instance=related_object_through,
            data=request.data,
            context={
                'request': request,
                'view': self,
                'related_object': related_object_id,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        resp_data = serializers.TagModelListSerializer(
            instance=instance,
            context={
                'request': request,
                'view': self,
                'related_object': related_object_id,
            }
        ).data
        return Response(resp_data)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
