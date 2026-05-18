from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse
from django.core import exceptions as django_exceptions
from django.contrib.auth import login

from rest_framework import status

from bkz3.settings import FRONTEND_URL, BACKEND_URL

from users.models import CustomUser

from . import utils


@csrf_exempt
def main(request):
    if request.method == 'GET':
        return render(request, 'mini_app.html',)
    elif request.method == 'POST':
        data = request.POST
        init_data = data.get('init_data')
        if not init_data:
            raise django_exceptions.ValidationError('')
        telegram_id = utils.get_telegram_id(init_data)
        if request.user.is_anonymous or not request.user.profile.telegram_id == telegram_id:
            user = CustomUser.objects.filter(profile__telegram_id=telegram_id).order_by('-date_joined').first()
            if not user:
                return redirect(FRONTEND_URL)
            login(request, user, backend='axes.backends.AxesBackend')
        redirect_to = data.get('redirect_to')
        if not redirect_to:
            return redirect(FRONTEND_URL)
        return redirect(f"{BACKEND_URL}{redirect_to}")
    else:
        return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)
