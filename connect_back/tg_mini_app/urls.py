from django.urls import path

from . import views
app_name = 'tg_mini_app'

urlpatterns = [
    path(r'main', views.main, name='tg-mini-app-main'),
]

