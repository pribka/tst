from django.urls import path
from . import views
from rest_framework import routers
from django.conf.urls import include

app_name = 'api_contractor_reports'

urlpatterns = [
    path('contractor_tasks/', views.ContractorTaskReportView.as_view(), name='contractor-task-report'),
    path('contractor_projects/', views.ContractorProjectsReportView.as_view(), name='contractor-project-report'),
    path('work_list/file/', views.WorkListFileView.as_view(), name='work-list-file'),
    ]

