from django.utils import timezone

from common.models import BaseModel
from change_history import utils as change_history_utils


def create_tag_history(related_object_id, tag, action):
    """Создает запись в истории изменений объекта, к которому был добавлен тег."""

    original_object = BaseModel.objects.super_get(related_object_id)
    if original_object.get_label() == 'tasks.TaskModel':
        task = original_object
        action_date = timezone.now()
        object_property_id = 'task__blockers'
        
        if action == 'added':
            change_history_utils.create_add_m2m(
                task.pk,
                action_date,
                object_property_id,
                tag.name,
                [tag.pk]
            )
        elif action == 'removed':
            change_history_utils.create_remove_m2m(
                task.pk,
                action_date,
                object_property_id,
                tag.name,
                [tag.pk]
            )
