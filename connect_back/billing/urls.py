from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('send-tariff-ending-notifications/', views.send_tariff_ending_notifications_view, name='send_tariff_ending_notifications'),
    path('send-tariff-started-notifications/', views.send_tariff_started_notifications_view, name='send_tariff_started_notifications'),
] 