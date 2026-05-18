from rest_framework.permissions import BasePermission


class PersonalPlanePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update', 'complete',):
            return obj.get_update_permission(request)
        elif view.action in ('retrieve',):
            return obj.get_detail_permission(request)


class PersonalPlaneItemPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        elif view.action in ('retrieve',):
            return obj.get_detail_permission(request)
        else:
            return False
