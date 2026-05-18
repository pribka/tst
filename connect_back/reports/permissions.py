from rest_framework.permissions import BasePermission


class ReportSettingsModelPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ('create', 'update', 'partial_update', 'destroy'):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.get_detail_permission(request)


class UserReportSettingsModelPermission(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update', 'destroy'):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)
