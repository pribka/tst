from rest_framework.permissions import BasePermission
from django.core.exceptions import ObjectDoesNotExist
from . import models
from rest_framework.exceptions import ValidationError, NotFound


class MeetingAuthorPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user.profile
        if 'pk' in view.kwargs:
            meeting_pk = view.kwargs['pk']
            try:
                meeting_obj = models.PlannedMeetingModel.objects.select_related(
                    'author',
                ).get(pk=meeting_pk)
            except ObjectDoesNotExist:
                raise NotFound('Конференция не найдена')
            if user == meeting_obj.author:
                return True
        else:
            return False


class MeetingModeratorUpdatePermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user == obj.meeting.author:
            return True
        else:
            return False


class MeetingDetailPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_detail_permission(request)

