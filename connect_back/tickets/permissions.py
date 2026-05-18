from rest_framework import permissions

from common.current_profile.middleware import get_current_authenticated_profile


class IsAuthorOrAdministrator1C(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = get_current_authenticated_profile()
        return (
            user.check_profile_types({"administrator_1c"}) or
            obj.author == user
        )


class UpdateTicketPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.profile.check_profile_types({"administrator_1c"}):
            try:
                from bkz3.settings import ALLOW_ADMINISTRATOR_EDIT_TICKETS
                admin_permission = ALLOW_ADMINISTRATOR_EDIT_TICKETS
            except ImportError:
                admin_permission = False
        else:
            admin_permission = False

        return (obj.get_update_permission(request) or
                admin_permission)


class IsAdministrator1C(permissions.BasePermission):

    def has_permission(self, request, view):
        user = get_current_authenticated_profile()
        return user.check_profile_types({"administrator_1c"})
