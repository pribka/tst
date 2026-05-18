from django.urls import path
from rest_framework import routers

from . import views

app_name = 'okr'
router = routers.DefaultRouter()
router.register(r'mission', views.MissionModelViewSet, basename='mission')
router.register(r'objectives', views.ObjectivesModelViewSet, basename='objectives')
router.register(r'key_results', views.KeyResultsModelViewSet, basename='key-results')
router.register(r'initiatives', views.InitiativesModelViewSet, basename='key-initiatives')
router.register(r'metrics', views.KeyResultMetricsModelViewSet, basename='metrics')

urlpatterns = [
    path('value_efforts/', views.ValueEffortsModelView.as_view(), name='value_efforts'),
]

urlpatterns += router.urls
