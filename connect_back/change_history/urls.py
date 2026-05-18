from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'change_history'
router = DefaultRouter()
router.register('', views.ChangeHistoryModelViewSet, basename='change-history')

urlpatterns = []

urlpatterns = urlpatterns + router.urls
