from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'estimates'

router = DefaultRouter()
router.register(r'accumulation_register', views.AccumulationRegisterViewSet, basename='accumulation-register')

urlpatterns = [
    path('', include(router.urls)),
    path('rebuild_register_periods/', views.RebuildExecutionTimeRegistersView.as_view(),
         name='rebuild-execution-time-registers'),
    path('cleanup_orphaned_helpdesk_work_log_registers/', views.CleanupOrphanedHelpDeskWorkLogRegistersView.as_view(),
         name='cleanup-orphaned-helpdesk-work-log-registers'),
]

