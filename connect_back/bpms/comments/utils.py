import json

from django.core.serializers.json import DjangoJSONEncoder

from django.db.models import Count, OuterRef, Subquery, IntegerField, CharField
from django.db.models.functions import Coalesce, Cast

from common.redis import socketio_redis
from common.models import ObjectViewerRelationModel, BaseModel

from users.models import ProfileModel

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL

from bpms.tasks.models import TaskModel

from . import models


def prepare_comments_queryset(queryset):
    """
    Общий "тяжёлый" обвес для списка комментариев:
    - select_related/prefetch_related для сериализации
    - annotate task_count/viewer_count, чтобы не было N+1
    """
    tasks_sub = TaskModel.objects.filter(
        is_active=True,
        reason=Cast(OuterRef('pk'), CharField()),
    ).order_by().values('reason').annotate(count=Count('pk')).values('count')
    viewers_sub = ObjectViewerRelationModel.objects.filter(
        obj_id=OuterRef('pk'),
    ).order_by().values('obj_id').annotate(count=Count('pk')).values('count')

    return (
        queryset.select_related('parent')
        .prefetch_related(
            'attachments__mime_type__file_type',
            'parent__attachments__mime_type__file_type',
            'mentions',
        )
        .annotate(
            task_count=Coalesce(
                Subquery(tasks_sub, output_field=IntegerField()),
                0,
            ),
            viewer_count=Coalesce(
                Subquery(viewers_sub, output_field=IntegerField()),
                0,
            ),
        )
    )


def get_comments_queryset(request, queryset):
    """
    Аналог get_task_queryset: только фильтрации/права/сортировка.
    Никаких annotate/select_related/prefetch_related.
    """
    try:
        query_params = request.query_params
    except AttributeError:
        query_params = request.GET

    related_object_id = query_params.get('related_object', None)
    if not related_object_id:
        return queryset.none()

    related_object = BaseModel.objects.super_get(pk=related_object_id)
    if not related_object:
        return queryset.none()

    base_queryset = models.CommentModel.objects.filter(
        related_object_id=related_object,
        is_active=True,
    )

    parent = query_params.get('parent')
    if parent:
        base_queryset = base_queryset.filter(parent=parent)

    if 'reverse' in query_params:
        base_queryset = base_queryset.order_by('-created_at', 'pk')
    else:
        base_queryset = base_queryset.order_by('created_at', 'pk')

    user = request.user.profile
    try:
        base_queryset = related_object.filter_comment_qs(user, base_queryset)
    except AttributeError:
        pass

    return base_queryset


def send_socketio_about_delete_comment(comment_id):
    comment = models.CommentModel.objects.get(pk=comment_id)
    data = json.dumps({
        'event': 'send_to_room',
        'event_type': 'delete_comment',
        'room_name': f"detail_{comment.related_object.id}",
        'data': str(comment.pk),
    }, cls=DjangoJSONEncoder)
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
    if not comment.is_personal:
        data = json.dumps({
            'event': 'send_to_room',
            'event_type': 'delete_comment',
            'room_name': f"detail_public_{comment.related_object.id}",
            'data': str(comment.pk),
        }, cls=DjangoJSONEncoder)
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_update_comment(comment_id):
    from .serializers import CommentListSerializer
    comment = models.CommentModel.objects.get(pk=comment_id)
    comment_data = CommentListSerializer(comment).data
    data = json.dumps({
        'event': 'send_to_room',
        'event_type': 'update_comment',
        'room_name': f"detail_{comment.related_object.id}",
        'data': comment_data
    }, cls=DjangoJSONEncoder)
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
    if not comment.is_personal:
        data = json.dumps({
            'event': 'send_to_room',
            'event_type': 'update_comment',
            'room_name': f"detail_public_{comment.related_object.id}",
            'data': comment_data
        }, cls=DjangoJSONEncoder)
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)