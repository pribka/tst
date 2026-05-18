from rest_framework.permissions import BasePermission


class CalendarModelPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        return obj.get_detail_permission(request)


class EventCalendarPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        return obj.get_detail_permission(request)

