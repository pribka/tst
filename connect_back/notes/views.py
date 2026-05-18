from django.shortcuts import render

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from common.views import BaseModelViewSet, BaseCatalogViewSet

from . import models, permissions


class ColorNoteModelViewSet(BaseCatalogViewSet):
    model = models.ColorNoteModel

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **wargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class NoteModelViewSet(BaseModelViewSet):
    model = models.NoteModel
    permission_classes = (IsAuthenticated, permissions.NoteModelPermission)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        related_object = instance.related_object
        if related_object:
            original_object = related_object.original_object
            try:
                result = original_object.get_note_permission(request)
            except AttributeError:
                result = original_object.get_update_permission(request)
            if result:
                actions = {
                    'create': {'availability': True},
                    'update': {'availability': True},
                    'delete': {'availability': True},
                }
        else:
            user = request.user.profile
            if instance.author == user:
                actions = {
                    'create': {'availability': True},
                    'update': {'availability': True},
                    'delete': {'availability': True},
                }
        return Response({'actions': actions})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        related_object = request.query_params.get('related_object')
        if not related_object:
            queryset = queryset.filter(related_object__isnull=True, author=request.user.profile)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
