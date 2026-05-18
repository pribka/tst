from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter


app_name = 'user_work_status'

urlpatterns = [

]

router = DefaultRouter()

router.register(r'', views.UserWorkStatusViewSet, basename='user-work-status')

router.register(r'reasons', views.UserWorkStatusReasonViewSet, basename='user-work-status-reason')

urlpatterns += router.urls
