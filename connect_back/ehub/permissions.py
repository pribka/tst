from rest_framework.permissions import BasePermission
from bkz3.settings import EHUB_TOKEN


class EhubPermission(BasePermission):
    class EhubPermission(BasePermission):
        def has_permission(self, request, view):
            token = request.COOKIES.get('ehubtoken')
            if token and token == EHUB_TOKEN:
                return True
            return False
