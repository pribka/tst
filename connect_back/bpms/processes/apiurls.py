from django.urls import path
from rest_framework import routers

from . import apiviews
app_name = 'api_processes'

router = routers.DefaultRouter()
router.register(r'workflow_requests', apiviews.WorkflowRequestViewSet, basename='workflow-requests',)
router.register(r'request_types', apiviews.RequestTypeViewSet, basename='request-types',)

# router.register(r'advance_report', apiviews.AdvanceReportViewSet, basename='advance-report',)
urlpatterns = [
    path('workflow_requests/route_template/', apiviews.RouteTemplateView.as_view(), name='route-template', )
]
urlpatterns += router.urls
