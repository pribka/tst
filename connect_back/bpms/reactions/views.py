from django.shortcuts import render
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.cache import cache
from django.db.models import Count, Exists

from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from common.views import BaseCatalogViewSet, BaseModelViewSet
from common.models import BaseModel
from common.serializers import CachedBaseCatalogSerializer
from common.paginators import CustomPagination

from bpms.chat.models import MessageModel
from bpms.comments.models import CommentModel

from users.serializers import CachedAppUserPreviewSerializer

from . import models, utils, serializers


class ReactionViewSet(BaseCatalogViewSet):
    model = models.ReactionModel

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=('post',), detail=False, url_path='related_object/(?P<pk>[^/.]+)/set')
    def set_reaction(self, request, *args, **kwargs):
        related_object = self.get_related_object(request, *args, **kwargs)
        user = request.user.profile
        object_reaction, created = models.ReactionObjectModel.objects.get_or_create(
            user=user,
            related_object=related_object,
        )
        serializer = serializers.ReactionObjectWriteSerializer(
            instance=object_reaction,
            data=request.data,
            context={'request': request, 'view': self, }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        reactions = utils.get_reactions(related_object)
        cache.set(f"object_reactions_{related_object.pk}", reactions)
        data = utils.get_reactions_data(related_object, user=user)
        if isinstance(related_object, MessageModel):
            utils.send_socketio_chat_message_reaction(related_object, user)
        elif isinstance(related_object, CommentModel):
            utils.send_socketio_about_comment_reaction(related_object, user)
        return Response(data)

    @action(methods=('get',), detail=False, url_path='related_object/(?P<pk>[^/.]+)')
    def get_reaction(self, request, *args, **kwargs):
        related_object = self.get_related_object(request, *args, **kwargs)
        user = request.user.profile
        reactions = utils.get_reactions_data(related_object, user)
        return Response(reactions)

    @action(methods=('get',), detail=False, url_path='related_object/(?P<pk>[^/.]+)/my')
    def get_my_reaction(self, request, *args, **kwargs):
        related_object = self.get_related_object(request, *args, **kwargs)
        user = request.user.profile
        try:
            reaction_id = models.ReactionObjectModel.objects.filter(
                related_object=related_object,
                user=user
            ).values_list('reaction', flat=True)[0]
        except IndexError:
            reaction_id = None
        return Response({'reaction': reaction_id})

    @action(methods=('get',), detail=False, url_path='related_object/(?P<pk>[^/.]+)/users')
    def get_users_reaction(self, request, *args, **kwargs):
        related_object = self.get_related_object(request, *args, **kwargs)
        reaction_id = request.query_params.get('reaction')
        if not reaction_id:
            reaction_users = models.ReactionObjectModel.objects.filter(
                related_object=related_object,
            ).order_by('reaction__sort', 'user__user__last_name', 'user__user__first_name')
            serializer_class = serializers.ReactionObjectListSerializer
        else:
            try:
                reaction_users = models.ReactionObjectModel.objects.filter(
                    related_object=related_object,
                    reaction_id=reaction_id,
                ).values_list('user', flat=True).order_by('user__user__last_name', 'user__user__first_name')
            except ValidationError:
                raise drf_exceptions.ValidationError('Реакция не найдена')
            serializer_class = CachedAppUserPreviewSerializer
        paginator = CustomPagination()
        page = paginator.paginate_queryset(reaction_users, request, self)
        data = serializer_class(page, many=True, context={'request': request, 'view': self}).data
        return paginator.get_paginated_response(data)

    def get_related_object(self, request, *args, **kwargs):
        related_object_id = kwargs.get('pk')
        if not related_object_id:
            raise drf_exceptions.ValidationError('related_object ID required.')
        try:
            related_object = BaseModel.objects.super_get(pk=related_object_id)
        except ValidationError:
            raise drf_exceptions.ValidationError('Invalid related_object id')
        if not related_object:
            try:
                related_object = MessageModel.objects.get(message_uid=related_object_id)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.ValidationError('related_object not found')
        if not related_object.is_active:
            raise drf_exceptions.ValidationError('related_object is deleted')
        if not related_object.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied('У Вас нет доступа к реакции этого объекта')
        return related_object
