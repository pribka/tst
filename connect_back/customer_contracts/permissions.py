from rest_framework.permissions import BasePermission


class CustomerContractPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        if obj.get_detail_permission(request):
            return True
        else:
            return False
