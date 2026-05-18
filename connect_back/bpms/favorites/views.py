from django.core.exceptions import ValidationError, ObjectDoesNotExist

from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from common import models as common_models
from common import views as common_views

from . import models, permissions


class FavoritesViewSet(ModelViewSet):

    model = models.FavoriteModel
    pagination_class = None
    permission_classes = (IsAuthenticated, permissions.FavoritePermission)

    def get_queryset(self):
        qs = self.model.get_queryset(self.request)
        return qs

    def get_serializer_class(self):
        return self.model.get_serializer_class(action=self.action)

    def perform_update(self, serializer):
        raise drf_exceptions.MethodNotAllowed('update')

    def destroy(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('delete')

    @action(methods=('post',), detail=False, url_path='delete')
    def delete_favorite(self, request, *args, **kwargs):
        related_object_id = request.data.get('related_object')
        try:
            favorite = models.FavoriteModel.objects.get(
                related_object_id=related_object_id,
                user=request.user.profile,
            )
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Объект в избранном не найден')
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

