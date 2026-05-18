import json

from django.core.serializers.json import DjangoJSONEncoder

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL

from notifications import event_types
from common.models import BaseModel
from common.redis import socketio_redis
from users.models import ProfileModel
from .models import TagModel



RELATED_OBJECTS_MAPPING_NEW = {
    'tasks.TaskModel': event_types.TaskNewBlocker,
}

RELATED_OBJECTS_MAPPING_REMOVE = {
    'tasks.TaskModel': event_types.TaskRemoveBlocker,
}

def notify_about_new_tag(related_object_id, tag_id, initiator_id):
    related_object = BaseModel.objects.super_get(pk=related_object_id)
    tag = TagModel.objects.get(pk=tag_id)
    initiator = ProfileModel.objects.get(pk=initiator_id)

    event_type_class = RELATED_OBJECTS_MAPPING_NEW.get(related_object.get_label())
    if not event_type_class:
        return f'no event_type for related_object {related_object.get_label()}'
    event_type = event_type_class()
    event_type.create_notification(initiator=initiator, subj=related_object, obj=tag)


def notify_about_remove_tag(related_object_id, tag_id, initiator_id):
    related_object = BaseModel.objects.super_get(pk=related_object_id)
    tag = TagModel.objects.get(pk=tag_id)
    initiator = ProfileModel.objects.get(pk=initiator_id)
    
    event_type_class = RELATED_OBJECTS_MAPPING_REMOVE.get(related_object.get_label())
    if not event_type_class:
        return f'no event_type for related_object {related_object.get_label()}'
    event_type = event_type_class()
    event_type.create_notification(initiator=initiator, subj=related_object, obj=tag)