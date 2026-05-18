from rest_framework.permissions import BasePermission


class WorkflowRequestPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class RequestTypePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)
