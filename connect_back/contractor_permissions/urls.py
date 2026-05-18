from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'contractor_permissions'
router = DefaultRouter()
router.register('roles', views.ContractorPermissionRoleModelViewSet, basename='contractor-permissions')
router.register('permission_types', views.PermissionTypeModelViewSet, basename='permission-types')
router.register('access_groups', views.AccessGroupViewSet, basename='access-groups')
router.register('app_section_roles', views.AppSectionRolesViewSet, basename='app-section-roles')
router.register('app_sections', views.AppSectionsViewSet, basename='app-sections')
urlpatterns = [
    path('organizations/', views.PermissionOrganizationListView.as_view(), name='organizations')
]
urlpatterns = urlpatterns + router.urls

