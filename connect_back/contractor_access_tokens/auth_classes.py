from django.core.exceptions import ValidationError, ObjectDoesNotExist

from rest_framework import exceptions as drf_exceptions

from rest_framework.authentication import BaseAuthentication
from common.catalogs.models import Contractor1CAccessTokenModel


class Contractor1CAccessTokenAuthentication(BaseAuthentication):
    """
    Класс аутентификации для обмена с 1С
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        error_msg = 'Invalid or missing authentication credentials.'

        if not auth_header or not auth_header.startswith('Bearer '):
            raise drf_exceptions.AuthenticationFailed(error_msg)
        token = auth_header.split(' ')[1]
        token_hash = Contractor1CAccessTokenModel.hash_token(token)

        try:
            token_obj = Contractor1CAccessTokenModel.objects.get(token_hash=token_hash, is_active=True)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.AuthenticationFailed(error_msg)

        if token_obj.is_expired:
            raise drf_exceptions.AuthenticationFailed(error_msg)

        # Возвращаем (None, объект_токена)
        return (None, token_obj,)

