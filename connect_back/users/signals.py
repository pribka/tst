from django.db.models.signals import post_save
from django.dispatch import receiver

from django_q.tasks import async_task

from .models import CustomUser, ProfileModel


@receiver(post_save, sender=CustomUser)
def post_save_customuser(sender, instance, created, raw, using, update_fields, **kwargs):
    from .utils import update_profile_index, update_new_user_info_index, send_socketio_about_update_profile
    if update_fields and 'last_login' in update_fields:
        return
    profile = getattr(instance, 'profile', None)
    if profile:
        async_task(update_profile_index, profile)
        async_task(update_new_user_info_index, profile.pk)
        async_task(send_socketio_about_update_profile, profile.pk)


@receiver(post_save, sender=ProfileModel)
def post_save_profile(sender, instance, created, raw, using, update_fields, **kwargs):
    if not created:
        from .utils import send_socketio_about_update_profile
        async_task(send_socketio_about_update_profile, instance.pk)


