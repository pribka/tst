from rest_framework.permissions import BasePermission


class FavoritePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.profile == obj.user:
            return True
        return False

