from django.core.exceptions import BadRequest, PermissionDenied
from django.http.response import Http404
from django.utils.translation import gettext as _

from rest_framework.views import exception_handler
from rest_framework.response import Response as DRFResponse

from django.http import HttpResponse


def base_exception_handler(exc, context):
    """
    Дополнитнльная обработка исключений для возврата значения ошибок фронту (при 400)
    """
    response = HttpResponse
    if isinstance(exc, BadRequest):
        response = response(exc, status=400, )
    elif isinstance(exc, Http404):
        response = DRFResponse(data={"detail": _("Страница не найдена или удалена")}, status=404)
    else:
        response = exception_handler(exc, context)

    return response
