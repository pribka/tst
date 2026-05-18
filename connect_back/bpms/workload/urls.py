from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'workload'

router = DefaultRouter()
router.register(r'schedules', views.WorkScheduleModelViewSet, 'schedules')
router.register(r'exception_dates', views.ExceptionModelViewSet, 'exceptions')
router.register(r'', views.WorkLoadViewSet, 'workload')

urlpatterns = [
    path('', include(router.urls))
]
