from django.urls import path
from rest_framework.routers import DefaultRouter

from bkz3.settings import DEBUG

from . import viewsets
from . import views_generate_from_excel
# from .utils import import_from_other_system

app_name = "student_clubs"
router = DefaultRouter()
urlpatterns = [
    # path('import_from_other_system/', import_from_other_system, name="import"),  # закомментировано 17.04.2026
    path('sprints/', viewsets.WorkGroupSprintListView.as_view(), name="sprint_list"),
    path('news/<uuid:pk>/update/', viewsets.UpdateWorkGroupNewsView.as_view(), name='news-update'),
    path('<uuid:pk>/projects/', viewsets.GetProjectsView.as_view(), name='get-projects'),
    path('qaz2wsx_project_generator/', views_generate_from_excel.project_generator_view, name='project_generator_view'),
    path('qaz2wsx_invest_project_generator/', views_generate_from_excel.invest_project_generator_view, name='invest_project_generator_view'),
]
router.register(r"workgroups", viewsets.WorkGroupViewSet, "workgroups")
router.register(r"workgroups_types", viewsets.WorkGroupTypesViewSet, "workgroups_types")
router.register(r"workgroups_status", viewsets.WorkGroupStatusViewSet, "workgroups_status")
router.register(r"workgroups_membership_status", viewsets.WorkGroupMembershipStatusViewSet,
                "workgroups_membership_status")
router.register(r"workgroups_membership_role", viewsets.WorkGroupMembershipRoleViewSet,
                "workgroups_membership_role")
router.register(r"news", viewsets.WorkGroupNewsViewSet, "news")
router.register(r"events", viewsets.WorkGroupEventsViewSet, "events")
router.register(r'templates', viewsets.ProjectTemplateViewSet, 'templates')
router.register(r'task_templates', viewsets.TaskTemplateViewSet, 'task_templates')


urlpatterns = router.urls + urlpatterns
