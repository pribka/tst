from django.urls import path
from . import views
from rest_framework import routers
from django.conf.urls import include

app_name = 'api_comments'

urlpatterns = [
    path('create/', views.CommentCreateView.as_view(), name='comment-create'),
    path('<uuid:pk>/update/', views.CommentUpdateView.as_view(), name='comment-update'),
    path('', views.CommentListView.as_view(), name='comment-list'),
    path('<uuid:pk>/', views.CommentDetailView.as_view(), name='comment-list'),
    path('count/', views.CommentCountView.as_view(), name='comment-list-count'),
    path('delete/', views.CommentDeleteView.as_view(), name='comment-delete'),
]
