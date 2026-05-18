from rest_framework.permissions import BasePermission
from common.utils import get_available_section_codes, use_access_groups


class ConsolidationPermission(BasePermission):
    def has_permission(self, request, view):
        if use_access_groups(request.user.profile.pk):
            return 'consolidation' in get_available_section_codes(request.user.profile)
        else:
            return True


class ConsolidationFileViewPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_update_permission(request)


class ReportFileViewPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_detail_permission(request)
