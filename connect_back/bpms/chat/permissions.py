from rest_framework.permissions import BasePermission


class ChatDetailPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_id = request.user.profile.pk
        return obj.members.filter(is_active=True, user=user_id).exists()


class OnlySupportPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.profile.is_support

    def has_object_permission(self, request, view, obj):
        return obj.get_update_permission(request)
