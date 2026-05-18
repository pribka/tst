from . import views
from django.urls import path, include
from rest_framework import routers

app_name = 'api_notifications'

router = routers.DefaultRouter()
router.register("settings", views.NotificationSettingsViewSet, basename='notification-settings')
router.register("", views.WebNotificationViewSet)

urlpatterns = [
    path('test_ws/', views.get_test_ws_view, name='test-ws'),
    path('categories/', views.NotificationCategoryListView.as_view(), name='categories'),
]
urlpatterns = urlpatterns + router.urls
