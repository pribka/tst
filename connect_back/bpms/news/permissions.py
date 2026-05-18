from rest_framework.permissions import BasePermission


class UpdateNewsPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if obj.author == user or user.is_support or request.user.is_staff:
            return True
        else:
            return False


class CreateNewsPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.profile.is_support


class DetailNewsPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_detail_permission(request)
