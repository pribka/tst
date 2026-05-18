from django.urls import path
from rest_framework.routers import DefaultRouter

from common.catalogs.views import ContractorListView
from users.views import UserListByTaskView, UserListView

from . import views

app_name = 'api_bpms_common'

router = DefaultRouter()
router.register('attachments', views.AttachmentViewSet)
urlpatterns = [
    # path('social_web_types/', views.SocialWebTypesListView.as_view(), name="social_web_types"),
    # path("social_links/", views.SocialURLsCreateView.as_view(), name="social_links"),
    path('user/list/', UserListView.as_view(), name='user-list'),
    path('contractor/list/', ContractorListView.as_view(), name='contractor-list'),
    path('user/list_by_task/', UserListByTaskView.as_view(), name='user-list-by-task'),
    # path('costing_object/list/', views.CostingObjectListView.as_view(), name='costing_object-list'),
    # path('program/list/', views.ProgramListView.as_view(), name='program-list'),
    # path('counterparty/list/', views.CounterpartyListView.as_view(), name='counterparty-list'),
    path('common/upload_for_editor/', views.UploadForEditorView.as_view(), name='upload-for-editor'),
    path('common/upload/', views.UploadView.as_view(), name='upload'),
    # path('attachments/<uuid:instance_id>/', views.GetAttachmentsApiView.as_view(), name='attachments'),
    # path('attachments/<uuid:instance_id>/add_files/', views.AddFileApiView.as_view(), name='attachments-add'),
    # path('attachments/<uuid:instance_id>/add_folder/', views.AddFolderApiView.as_view(), name='attachments-add-folder'),
    # path('attachments/<uuid:instance_id>/remove_files/', views.RemoveFileApiView.as_view(),
    #      name='attachments-remove-file'),
]
urlpatterns += router.urls
