from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'invest_projects_info'

router = DefaultRouter()
router.register(r'', views.InvestProjectInfoModelViewSet, basename='invest_projects_info')

urlpatterns = [

]

urlpatterns = urlpatterns + router.urls
