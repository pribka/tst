from rest_framework.permissions import BasePermission
from bkz3.local_settings import IMPORT_1C_DATA_TOKEN, TOKEN_URV


class Token1CPermission(BasePermission):
    def has_permission(self, request, view):
        token_storage = None
        if request.method == 'GET':
            token_storage = request.query_params
        elif request.method == 'POST':
            token_storage = request.POST
        if token_storage and 't' in token_storage and token_storage['t'] == IMPORT_1C_DATA_TOKEN:
            return True
        return False


class URVTokenPermission(BasePermission):
    def has_permission(self, request, view):
        token_storage = None
        if request.method == 'GET':
            token_storage = request.query_params
        elif request.method == 'POST' or request.method == 'PATCH':
            token_storage = request.data
        if token_storage and 't' in token_storage and token_storage['t'] == TOKEN_URV:
            return True
        return False
