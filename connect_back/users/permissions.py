from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied


class LeaveRequestPermission(BasePermission):
    """Оставлять заявки могут все пользователи (в т.е. неаутентифицированные).
    Просматривать заявки может только менеджер."""
    def has_permission(self, request, view):
        if view.action in ['create',]:
            return True
        else:
            if not request.user.is_authenticated:
                return False
            return request.user.is_staff or request.user.profile.is_support
                                                                                                
    def has_object_permission(self, request, view):
            if not request.user.is_authenticated:
                return False
            return request.user.is_staff or request.user.profile.is_support
