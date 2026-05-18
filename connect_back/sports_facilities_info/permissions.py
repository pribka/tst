from rest_framework.permissions import BasePermission


class SportFacilityPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        action = view.action
        if action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        elif action in ('update_status',):
            return obj.get_update_status_permission(request)
        elif action in ('request_update',):
            return obj.get_request_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class SportFacilityRenovationInfoPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        action = view.action
        if action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        elif action == 'destroy':
            return obj.get_delete_permission(request)
        else:
            return obj.get_detail_permission(request)
