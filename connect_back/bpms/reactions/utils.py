import json

from django.db.models import Count
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL
from common.redis import socketio_redis

from . import models
from . import serializers


def get_reactions_data(related_object, user=None, prefetched_user_reaction_id=None):
    """
    prefetched_user_reaction_id:
    - None: не передано, получить реакцию пользователя запросом
    - '' (пустая строка): реакции у пользователя нет (запрос не нужен)
    - UUID: id реакции пользователя (запрос не нужен)
    """
    reactions = cache.get(f"object_reactions_{related_object.pk}")
    if not reactions:
        reactions = get_reactions(related_object)
        cache.set(f"object_reactions_{related_object.pk}", reactions)
    if user:
        if prefetched_user_reaction_id is not None:
            user_reaction_id = prefetched_user_reaction_id or ''
        else:
            try:
                user_reaction_id = models.ReactionObjectModel.objects.filter(
                    related_object=related_object,
                    user=user,
                ).values_list('reaction', flat=True)[0]
            except IndexError:
                user_reaction_id = ''
        for each in reactions:
            each['reaction'] = serializers.CachedReactionSerializer(each['pk']).data
            if each['pk'] == user_reaction_id:
                each['my_reaction'] = True
            else:
                each['my_reaction'] = False
    else:
        for each in reactions:
            each['reaction'] = serializers.CachedReactionSerializer(each['pk']).data
    return reactions


def get_reactions(related_object):
    reactions = list(models.ReactionModel.objects.filter(
        object_reactions__related_object=related_object,
    ).annotate(
        users_count=Count('object_reactions'),
    ).values('pk', 'users_count').order_by('sort'))
    return reactions


def send_socketio_chat_message_reaction(related_object, user):
    reactions = get_reactions_data(related_object)
    data = {
        'chat_uid': related_object.chat.chat_uid,
        'message_uid': related_object.message_uid,
        'author': user.pk,
        'reactions': reactions,
    }
    return_data = json.dumps(
        {
            "event": "chat_message_reaction",
            "data": data,
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, return_data)


def send_socketio_about_comment_reaction(comment, user):
    reactions = get_reactions_data(comment)
    reactions_data = {
        'comment': comment.pk,
        'author': user.pk,
        'reactions': reactions,
    }

    data = json.dumps({
        'event': 'send_to_room',
        'event_type': 'comment_reaction',
        'room_name': f"detail_{comment.related_object.id}",
        'data': reactions_data
    }, cls=DjangoJSONEncoder)
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
