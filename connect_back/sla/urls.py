from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'sla'

router = DefaultRouter()
router.register(r'', views.SLAViewSet, basename='sla')

urlpatterns = router.urls
