from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'chat_ai'
router = DefaultRouter()

router.register(r'chats', views.AIChatViewSet, basename='ai-chats')
router.register(r'messages', views.AIMessageViewSet, basename='ai-messages')
router.register(r'intents', views.IntentModelViewSet, basename='ai-intents')

urlpatterns = [
    path('export_roles/', views.ExportAIChatRolesView.as_view(), name='export-roles'),
    path('import_roles/', views.ImportAIChatRolesView.as_view(), name='import-roles'),
] + router.urls