from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'contractor_docs'

router = DefaultRouter()

router.register('templates', views.ContractorDocTemplateModelViewSet, basename='contractor-docs-templates')
router.register('', views.ContractorDocModelViewSet, basename='contractor-docs')
urlpatterns = []

urlpatterns = urlpatterns + router.urls

