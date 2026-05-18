from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'risk_assessment'

router = DefaultRouter()
router.register(r'issue_categories', views.IssueCategoriesViewSet, basename='issue-categories')
router.register(r'', views.RiskAssessmentViewSet, basename='risk_assessment')

urlpatterns = router.urls
