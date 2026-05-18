from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'contractor_invites'

urlpatterns = [
    path(
        'create/',
        views.ContractorInviteModelCreateView.as_view(),
        name='contractor-invites-create'
    ),
    path(
        'my/',
        views.ContractorInviteModelMyListView.as_view(),
        name='contractor-invites-my'
    ),
    path(
        'for_me/',
        views.ContractorInviteModelForMeListView.as_view(),
        name='contractor-invites-for-me'
    ),
    path(
        'delete/',
        views.ContractorInviteModelDeleteView.as_view(),
        name='contractor-invites-delete',
    ),
    path(
        'accept/',
        views.ContractorInviteModelAcceptView.as_view(),
        name='contractor-invites-accept',
    ),
    path(
        'reject/',
        views.ContractorInviteModelRejectView.as_view(),
        name='contractor-invites-reject',
    ),
    path(
        '<uuid:pk>/',
        views.ContractorInviteModelDetailView.as_view(),
        name='contractor-invites-detail',
    )
]
