from common.current_profile.middleware import get_current_authenticated_profile
from . import models


def get_in_favorites(instance):
    try:
        in_favorites = instance.in_favorites
    except AttributeError:
        in_favorites = instance.profile_favorites.filter(user=get_current_authenticated_profile()).exists()
    return in_favorites
