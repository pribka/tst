from . import views
from django.urls import path

app_name = 'api_static_pages'

urlpatterns = [path('<str:code>/', views.StaticPageModelRetrieveView.as_view(), name='static_page')]
