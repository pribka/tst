from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views


app_name = "calendar"

router = DefaultRouter()
router.register('access', views.EventCalendarAccessViewSet, basename='personal-plane-access')

router.register(r'events', views.EventCalendarModelViewSet, 'events')
router.register(r'', views.CalendarModelViewSet, 'calendar',)
router.register(r'google', views.GoogleCalendarViewSet, 'google',)
urlpatterns = [

]

urlpatterns = urlpatterns + router.urls

