from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'accounting_reports'

router = DefaultRouter()
router.register(r'', views.AccountingReportsViewSet, basename='accounting_reports')
urlpatterns = [
    path('get_organizations', views.GetOrganizationsViewSet.as_view(), name='get-organizations'),
    path('expense_report/', views.UploadExpenseReportView.as_view(), name='expense-report'),
]

urlpatterns = urlpatterns + router.urls
