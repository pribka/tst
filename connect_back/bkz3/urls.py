"""bkz3 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from . import settings

from common import views

router = DefaultRouter()

router.register(r'api/v1/files', views.FileViewSet, basename='files')
router.register(r'api/v1/mimetypes', views.MimeTypeViewSet, basename='mimetypes')
router.register(r'api/v1/filetypes', views.FileTypeViewSet, basename='filetype')
router.register(r'api/v1/app_info', views.AppInfoViewSet, basename='app-info')
router.register(r'api/v1/organizations', views.OrganizationViewSet, basename='organizations')
router.register(r'api/v1/individuals', views.IndividualViewSet, basename='individuals')
router.register(r'api/v1/table_actions', views.BaseModelActionsViewSet, basename='table-actions')
router.register(r'api/v1/base_documents', views.BaseDocumentViewSet, basename='base-documents')
router.register(r'api/v1/plan_of_characteristic', views.PlanOfCharacteristicViewSet, basename='plan_of_characteristic')
urlpatterns = [
    path('api/v1/4e0dea26d93011eca0954216f3de51df/', admin.site.urls),
    path('get_file_path/', views.GetFilePath.as_view(), name='get-file-path'),
    path('ehub_api/', include('ehub.api_urls', namespace='ehub_api')),
    # path('api/v1/import_user_data_from_gos24/', views.import_user_data),  # закомментировано 17.04.2026
    path('api/v1/users/', include('users.urls', namespace='users')),
    path('api/v1/staff/', include('staff.urls', namespace='staff')),
    path('api/v1/bpp/', include('bpp.urls', namespace='bpp')),
    path('api/v1/flowchart/', include('flowchart.apiurls', namespace='flowchart')),
    path('api/v1/meetings/', include('bpms.meetings.apiurls', namespace='meetings')),
    path('api/v1/work_groups/', include('bpms.workgroups.urls', namespace='workgroups')),
    path('api/v1/tasks/', include('bpms.tasks.apiurls', namespace='tasks')),
    path('api/v1/news/', include('bpms.news.apiurls', namespace='news')),
    path('api/v1/processes/', include('bpms.processes.apiurls', namespace='processes')),
    path('api/v1/widgets/', include('bpms.widgets.urls', namespace='widgets')),
    path('api/v1/comments/', include('bpms.comments.urls', namespace='bpms-comments')),
    path('api/v1/chat/', include('bpms.chat.urls', namespace='bpms-chat')),
    path('api/v1/notifications/', include('notifications.urls', namespace='notifications')),
    path('api/v1/catalogs/', include('common.catalogs.urls', namespace='catalogs')),
    path('api/v1/accounting_catalogs/', include('common.accounting_catalogs.urls', namespace='accounting-catalogs')),
    path('api/v1/estimates/', include('common.estimates.urls', namespace='estimates')),
    path('api/v1/gallery/', include('gallery.urls', namespace='gallery')),
    path('api/v1/crm/', include('crm.urls', namespace='crm')),
    path('api/v1/', include('bpms.bpms_common.urls', namespace='bpms-common')),
    path('api/v1/integration_1c/', include('integration_1c.urls', namespace='intergation-1c')),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/pvh/', include('pvh.urls', namespace='pvh')),
    path('api/v1/rebuild_haystack_index/', views.RebuildHaystackIndexView.as_view(), name='rebuild-haystack-index'),
    path('api/v1/delete_filters_store/', views.DeleteFiltersStoreView.as_view(), name='delete-filters-store'),
    path('api/v1/rebuild_dsl_index/', views.RebuildDSLIndexView.as_view(), name='rebuild-dsl-index'),
    path('api/v1/update_server/', views.UpdateServerView.as_view(), name='update-server'),
    path('api/v1/clear_cache/', views.ClearCacheView.as_view(), name='clear-cache'),
    path('api/v1/clear_sessions/', views.ClearSessionsView.as_view(), name='clear-sessions'),
    path('api/v1/clear_cache_by_prefix/', views.ClearCacheByPrefixView.as_view(), name='clear-cache-by-prefix'),
    path('api/v1/task_klass_pause/', views.TaskKlassPauseView.as_view(), name='task-klass-pause'),
    path('api/v1/user_work_status/', include('user_work_status.urls', namespace='user-work-status')),
    path('api/v1/static_pages/', include('static_pages.urls', namespace='static-pages')),
    path('api/v1/vote/', include('bpms.voting.apiurls', namespace='voting')),
    path('api/v1/retrospective/', include('bpms.retrospective.urls', namespace='retrospective')),
    path('api/v1/table_info/', views.TableInfoView.as_view(), name='table-info'),
    path('api/v1/tickets/', include('tickets.apiurls', namespace='tikets')),
    path('api/v1/content_item_gos24/', include('content_item_gos24.urls', namespace='content_item_gos24')),
    path('api/v1/contractor_invites/', include('contractor_invites.urls', namespace='contractor_invites')),
    path('api/v1/contractor_docs/', include('contractor_docs.urls', namespace='contractor_docs')),
    path('api/v1/calendars/', include('bpms.event_calendar.urls', namespace='calendar')),
    path('api/v1/consolidation/', include('consolidation.urls', namespace='consolidation')),
    path('api/v1/wiki/', include('wiki.urls', namespace='wiki')),
    path('api/v1/contractor_permissions/', include('contractor_permissions.urls', namespace='contractor_permissions')),
    path('api/v1/change_history/', include('change_history.urls', namespace='change_history')),
    path('api/v1/risk_assessment/', include('risk_assessment.urls', namespace='risk_assessment')),
    path('api/v1/invest_projects_info/', include('invest_projects_info.urls', namespace='invest_projects_info')),
    path('api/v1/accounting_reports/', include('accounting_reports.urls', namespace='accounting_reports')),
    path('api/v1/set_balances', views.SetBalancesView.as_view(), name='set-balances'),
    path('api/v1/ehub/', include('ehub.urls', namespace='ehub')),
    path('api/v1/workload/', include('bpms.workload.urls', 'workload')),
    path('api/v1/favorites/', include('bpms.favorites.urls', 'favorites')),
    path('api/v1/personal_planes/', include('bpms.personal_planes.urls', namespace='personal_planes')),
    path('api/v1/contractor_reports/', include('contractor_reports.urls', namespace='contractor_reports')),
    path('api/v1/sports_facilities/', include('sports_facilities_info.urls')),
    path('api/v1/help_desk/', include('help_desk.urls')),
    path('api/v1/tags/', include('tags.urls')),
    path('api/v1/okr/', include('bpms.okr.urls', namespace='okr')),
    path('api/v1/notes/', include('notes.urls', namespace='notes')),
    path('api/v1/demo/', include('demo.urls', namespace='demo')),
    path('api/v1/billing/', include('billing.urls', namespace='billing')),
    path(r'report_builder/', include('report_builder.urls')),
    path('api/v1/reports/', include('reports.urls')),
    path('api/v1/analytics/', include('analytics.urls', namespace='analytics')),
    path('api/v1/day_summary/', include('bpms.day_summary.urls', namespace='day-summary')),
    path('api/v1/chat_ai/', include('bpms.chat_ai.urls', namespace='bpms-chat-ai')),
    path('api/v1/es_search/', include('es_search.urls', namespace='es_search')),
    path('api/v1/test_sentry/', views.TestSentryApiView.as_view(), name='test-sentry',),
    path('api/v1/sla/', include('sla.urls', namespace='sla')),
    path('api/v1/tg_mini_app/', include('tg_mini_app.urls', namespace='tg_mini_app')),
    path('api/v1/viewers/', views.ObjectViewersList.as_view(), name='viewers'),
    path('api/v1/desktop_version/', views.DesktopAppVersionView.as_view(), name='desktop_app_version'),
    path('api/v1/reactions/', include('bpms.reactions.urls', namespace='reactions',)),
    path('api/v1/catalog_info/', include('catalog_info.urls', namespace='catalog_info',)),
    path('api/v1/contractor_access_tokens/', include('contractor_access_tokens.urls', namespace='contractor_access_tokens')),
    path('api/v1/customer_contracts/', include('customer_contracts.urls', namespace='customer_contracts')),
    path('api/v1/onlyoffice/', include('bpms.onlyoffice.urls', namespace='onlyoffice')),

]
urlpatterns += router.urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

