import json

from django.core.serializers.json import DjangoJSONEncoder

from common.models import BaseModel
from common.redis import socketio_redis

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL

from notifications import event_types
from . import models

RELATED_OBJECTS_MAPPING = {
    'tasks.TaskModel': (
        event_types.TaskNewComment,
        event_types.TaskNewCommentMention,
    ),
    'bpms_common.NewsModel': (event_types.NewsNewComment,),
    'crm.GoodsOrderModel': (event_types.GoodsOrderComment,),
    'event_calendar.EventCalendarModel': (event_types.EventCalendarComment,),
    'consolidation.ReportModel': (event_types.ConsolidationReportComment,),
    'consolidation.ConsolidationModel': (event_types.ConsolidationComment,),
    'help_desk.HelpDeskTicketModel': (
        event_types.HelpDeskTicketNewComment,
        event_types.HelpDeskTicketNewCommentClient,
        event_types.HelpDeskTicketNewCommentMention
    ),
    'processes.WorkflowRequestModel': (
        event_types.WorkflowRequestNewComment,
        event_types.WorkflowRequestNewCommentMention,
    )
}


def notify_about_new_comment(comment_id):
    comment = models.CommentModel.objects.get(pk=comment_id)
    related_object_id = comment.related_object_id
    if not related_object_id:
        return 'no related object.'
    related_object = BaseModel.objects.super_get(pk=related_object_id)
    event_type_classes = RELATED_OBJECTS_MAPPING.get(related_object.get_label())
    if not event_type_classes:
        return f'no event_type for related_object {related_object.get_label()}'
    for event_type_class in event_type_classes:
        event_type = event_type_class()
        event_type.create_notification(initiator=comment.author, subj=related_object, obj=comment)
    from .serializers import CommentListSerializer
    s_data = CommentListSerializer(comment).data
    data = json.dumps({
        'event': 'send_to_room',
        'event_type': 'create_comment',
        'room_name': f"detail_{related_object_id}",
        'data': s_data,
    }, cls=DjangoJSONEncoder)
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
    if not comment.is_personal:
        data = json.dumps({
            'event': 'send_to_room',
            'event_type': 'create_comment',
            'room_name': f"detail_public_{related_object_id}",
            'data': s_data,
        }, cls=DjangoJSONEncoder)
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
    new_comment_data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": {
                    "event_type": "new_comment_from_object",
                    "obj": related_object_id
                },
                "recipients": 'all',
            },
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, new_comment_data)

