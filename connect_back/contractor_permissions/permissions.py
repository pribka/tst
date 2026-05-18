from rest_framework.permissions import BasePermission


class AccessGroupPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':  # TODO определить потом кто может создавать
            return True
        return True

    def has_object_permission(self, request, view, obj):
        action = view.action
        if action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)
