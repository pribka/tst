from rest_framework.permissions import BasePermission

from common.catalogs.models import Contractor1CAccessTokenModel


class Contractor1CAccessTokenPermission(BasePermission):
    """
    Разрешает доступ только если запрос был успешно аутентифицирован через 1CAccessToken.
    """
    def has_permission(self, request, view):
        # Проверяем, что в request.auth лежит наш объект токена
        return isinstance(request.auth, Contractor1CAccessTokenModel)
