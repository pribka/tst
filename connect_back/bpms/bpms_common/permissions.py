from rest_framework.permissions import BasePermission, SAFE_METHODS


class GetAttachmentsBasePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_detail_permission(request)


class UpdateAttachmentsPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_attach_permission(request)


class IsSuperUserOrReadOnly(BasePermission):
    """
    Пользователи с правами is_superuser могут выполнять любые действия.
    Не is_superuser могут только читать (GET).
    """

    def has_permission(self, request, view):
        # Разрешение для всех методов GET
        if request.method in SAFE_METHODS:
            return True

        # Разрешение только для is_superuser при создании или редактировании
        return request.user.is_superuser
