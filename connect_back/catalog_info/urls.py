from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'catalog_info'
# router.register('list', views.CatalogInfoListView.as_view(), basename='catalog-info-list')

urlpatterns = [
    path('list/', views.CatalogInfoListView.as_view(), name='catalog-info-list')
]
# urlpatterns = urlpatterns + router.urls
