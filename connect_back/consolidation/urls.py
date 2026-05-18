from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'consolidation'

router = DefaultRouter()

router.register('report_forms', views.ReportFormModelViewSet, basename='report-forms')
router.register('report', views.ReportModelViewSet, basename='report')
router.register('', views.ConsolidationModelViewSet, basename='consolidations')
urlpatterns = [
    path('get_org_administrators', views.GetOrgAdministratorsViewSet.as_view(), name='get-org-administrators'),
    # path('analytics', views.AnalyticsViewSet.as_view(), name='get-analytics'),
    path('analytic_reports', views.AnalyticReportModelView.as_view(), name='get-analytic-reports'),
    # path('kijlr3awx8_update_saved_reports/', views.kijlr3awx8_update_saved_reports, name='update-saved-reports'),
    path('<uuid:file_id>/get_pdf/', views.GetPDFView.as_view(), name='get-pdf')
]

urlpatterns = urlpatterns + router.urls
