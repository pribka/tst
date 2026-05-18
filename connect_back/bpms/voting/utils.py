from django.core.cache import cache
from django.db.models import Count

from . import models


def get_cache_key_name(instance) -> str:
    return f'{instance._meta.app_label}_{instance.id}'


def get_vote_info(instance):
    votes = cache.get(get_cache_key_name(instance))
    result = update_vote_cache_for_instance(instance) if votes is None else votes
    return result


def update_vote_cache_for_instance(instance):
    votes_count = (models.UserVotesModel.objects
                   .filter(is_active=True, related_object=instance)
                   .values('vote')
                   .annotate(count=Count('vote')))
    result = dict({'likes_count': 0, 'dislikes_count': 0})
    for count in votes_count:
        if count['vote']:
            result['likes_count'] = count['count']
        else:
            result['dislikes_count'] = count['count']

    cache.set(get_cache_key_name(instance), result)
    return result
