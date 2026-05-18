from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('create/', views.create_demo_data_view, name='create_demo_data'),
    path('delete/', views.delete_demo_data_view, name='delete_demo_data'),
] 