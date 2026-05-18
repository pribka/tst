from rest_framework.permissions import BasePermission


class ChangeHistoryModelDetailPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.get_detail_permission(request):
            return True
        else:
            return False
