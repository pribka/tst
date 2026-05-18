from django_q.tasks import async_task

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from rest_framework import exceptions as drf_exceptions

from common.paginators import CustomPagination
from common.models import BaseModel

from bpms.reactions.models import ReactionObjectModel

from . import serializers, models, utils, permissions


class CommentCreateView(generics.CreateAPIView):
    """Создание комментария"""
    permission_classes = (
        IsAuthenticated,
    )
    serializer_class = serializers.CommentCreateSerializer
    queryset = models.CommentModel.objects.filter(is_active=True)


class CommentUpdateView(generics.UpdateAPIView):
    """Изменение комментариев"""
    permission_classes = (IsAuthenticated, permissions.CommentAuthorPermission,)
    serializer_class = serializers.CommentUpdateSerializer
    queryset = models.CommentModel.objects.filter(is_active=True)


class CommentListView(generics.ListAPIView):
    """Получение комментариев"""
    permission_classes = (
        IsAuthenticated,
    )

    serializer_class = serializers.CommentListSerializer
    pagination_class = CustomPagination
    queryset = models.CommentModel.objects.filter(is_active=True)

    def get_serializer_class(self):
        query_params = self.request.query_params
        full = query_params.get('full', None)
        if full:
            return serializers.CommentListFullSerializer

        return serializers.CommentListSerializer

    def list(self, request, *args, **kwargs):
        user = request.user.profile
        base_queryset = self.filter_queryset(utils.get_comments_queryset(request, self.queryset))
        order_by = base_queryset.query.order_by

        ids_queryset = base_queryset.values_list('pk', flat=True)
        page_ids = self.paginate_queryset(ids_queryset)
        if page_ids is None:
            return Response([])

        comment_ids = list(page_ids)
        models.CommentModel.bulk_cluts(comment_ids, user.pk)

        page_queryset = models.CommentModel.objects.filter(pk__in=comment_ids, is_active=True)
        page_queryset = utils.prepare_comments_queryset(page_queryset)
        if order_by:
            page_queryset = page_queryset.order_by(*order_by)

        user_reactions_by_object_id = {comment_id: '' for comment_id in comment_ids}
        user_reactions_by_object_id.update(
            dict(
                ReactionObjectModel.objects.filter(
                    related_object_id__in=comment_ids,
                    user=user,
                ).values_list('related_object_id', 'reaction_id')
            )
        )

        context = self.get_serializer_context()
        context['user_reactions_by_object_id'] = user_reactions_by_object_id
        serializer = self.get_serializer(page_queryset, many=True, context=context)
        return self.get_paginated_response(serializer.data)


class CommentDetailView(generics.RetrieveAPIView):
    permission_classes = (
        IsAuthenticated,
    )

    serializer_class = serializers.CommentListSerializer
    queryset = models.CommentModel.objects.filter(is_active=True)


class CommentCountView(APIView):
    permission_classes = (
        IsAuthenticated,
    )
    queryset = models.CommentModel.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        qs = utils.get_comments_queryset(request, self.queryset)
        display = request.GET.get('display', '')
        comments_count = qs.count()
        if display == 'unread':
            unread_count = qs.exclude(viewers=request.user.profile).count()
            data = {'count': comments_count, 'unread_count': unread_count}
        else:
            data = comments_count
        return Response(data, status=status.HTTP_200_OK)


class CommentDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        comment_id = request.data.get('id')
        user = request.user.profile
        try:
            instance = models.CommentModel.objects.get(is_active=True, author=user, pk=comment_id)
        except models.CommentModel.DoesNotExist:
            return Response('not_found', status=status.HTTP_400_BAD_REQUEST)
        instance.is_active = False
        instance.save(update_fields=('is_active',))
        async_task(utils.send_socketio_about_delete_comment, str(instance.pk))
        return Response('ok', status=status.HTTP_200_OK)
