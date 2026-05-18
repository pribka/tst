from rest_framework.permissions import BasePermission


class SectionPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('create', 'update', 'partial_update', 'destroy',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


