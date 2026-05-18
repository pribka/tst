from django.urls import path

from rest_framework import routers

from . import views

app_name = 'customer_contracts'
router = routers.DefaultRouter()
router.register(r'', views.CustomerContractViewSet, basename='customer-contracts')

urlpatterns = [
    path('analytics_keys/', views.CustomerContractAnalyticsKeysAPIView.as_view(), name='customer-contracts-analytics-keys'),
    path('analytics_keys/by_project/', views.CustomerContractByProjectAPIView.as_view(), name='customer-contracts-by-project'),
]

urlpatterns = urlpatterns + router.urls
