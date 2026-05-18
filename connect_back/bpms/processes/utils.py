import json
from datetime import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone, dateparse
from django.db.models import Q

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL
from bkz3.settings import TIME_ZONE

from common.utils import get_filter_queryset
from common.redis import socketio_redis

from users.utils import get_ancestor_departments_related_organizations

from . import models


def send_socketio_about_update_workflow_request(workflow_request: models.WorkflowRequestModel):
    from .serializers import WorkflowRequestDetailSerializer
    s_data = WorkflowRequestDetailSerializer(instance=workflow_request).data
    data = json.dumps(
        {
            'event': 'workflow_request_update',
            'data': s_data,
        },
        cls=DjangoJSONEncoder
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_create_workflow_request(workflow_request_id):
    """Рассылает событие о новой заявке при старте."""
    from .serializers import WorkflowRequestDetailSerializer
    workflow_request = models.WorkflowRequestModel.objects.get(pk=workflow_request_id)
    s_data = WorkflowRequestDetailSerializer(instance=workflow_request).data
    routes = workflow_request.request_routes.all().values_list('pk', flat=True)
    recipients = set(
        models.RequestRouteUserThrough.objects.filter(request_route_id__in=routes).values_list('user', flat=True)
    )
    recipients.add(workflow_request.author.pk)
    organization = workflow_request.organization
    ancestors = get_ancestor_departments_related_organizations((organization.pk,), include_self=True)
    request_type = workflow_request.request_type
    visors = set(
        models.WorkflowRequestTypeVisorModel.objects.filter(
            request_type=request_type, contractor_profile__contractor_id__in=ancestors
        ).values_list('contractor_profile__user', flat=True)
    )
    recipients = list(recipients | visors)
    data = json.dumps(
        {
            "event": "notify",
            "data": {
                "message": {
                    "event_type": "workflow_request_create",
                    "obj": s_data,
                },
                "recipients": recipients,
            }
        },
        cls=DjangoJSONEncoder
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)

