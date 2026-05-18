from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'personal_planes'

router = DefaultRouter()
router.register('access', views.PersonalPlaneAccessViewSet, basename='personal-plane-access')
router.register('item', views.PersonalPlaneItemViewSet, basename='personal-plane-items')

router.register('', views.PersonalPlaneViewSet, basename='personal-planes')
urlpatterns = [

]

urlpatterns = urlpatterns + router.urls
