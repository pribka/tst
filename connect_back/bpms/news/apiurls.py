from django.urls import path
from . import apiviews
from rest_framework import routers
from django.conf.urls import include

app_name = 'news_api'
urlpatterns = [
    path('news/create/', apiviews.CreateNewsView.as_view(), name='news-create'),
    path('news/<uuid:pk>/update/', apiviews.UpdateNewsView.as_view(), name='news-update'),
    path('news/<uuid:pk>/action_info/', apiviews.NewsActionInfoView.as_view(), name='news-action-info'),
    path('news/<uuid:pk>/', apiviews.DetailNewsView.as_view(), name='news-detail'),
    path('news/list/', apiviews.ListNewsView.as_view(), name='news-list'),
    path('news/unread_count/', apiviews.UnreadCountView.as_view(), name='unread-count'),
    path('news/filters/', apiviews.NewsFiltersView.as_view(), name='news-filters'),
    path('news/filters/check/', apiviews.CheckCategoryNewsView.as_view(), name='news-filters-check'),
    path('news/filters/uncheck/', apiviews.UncheckCategoryNewsView.as_view(), name='news-filters-uncheck'),
]
