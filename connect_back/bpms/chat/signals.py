from django.db.models.signals import post_save
from django.dispatch import receiver

from django_q.tasks import async_task

# from users.models import ProfileModel
from .models import MemberModel


@receiver(post_save, sender=MemberModel)
def index_chat_because_member(sender, instance, created, raw, using, update_fields, **kwargs):
    from .utils import update_chat_index
    chat = getattr(instance, 'chat', None)
    if update_fields is not None and (created or 'is_active' in update_fields) and chat:
        async_task(update_chat_index, chat)

#
# @receiver(post_save, sender=ProfileModel)
# def index_chat_because_profile(sender, instance, created, raw, using, update_fields, **kwargs):
#     from .utils import update_chat_index
#     if not created:
#         members = instance.membermodel_set.all().prefetch_related('chat')
#         for member in members:
#             chat = getattr(member, 'chat', None)
#             if chat:
#                 async_task(update_chat_index, chat)
