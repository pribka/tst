from rest_framework.permissions import BasePermission


class HasFullAccessToOrderEditing(BasePermission):
    def has_permission(self, request, view):
        user = request.user.profile
        return user.has_full_access_to_order_editing


class ContractorProfileRequestPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.is_support

    def has_object_permission(self, request, view, obj):
        return request.user.profile.is_support
