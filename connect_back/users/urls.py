from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'users'

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('search/', views.CustomUserAutocompleteSearchView.as_view(), name='search-user-autocomplete'),
    path('reset/password/<uuid:reset_uid>/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('get_my_default_chat/', views.GetMyDefaultChatView.as_view(), name='get_default_chat'),
    # Явно указываем методы для leave_request, чтобы можно было посылать POST-запросы от неаутентифицированных пользователей
    path('leave_request/', views.LeaveRequestViewSet.as_view({'get': 'list', 'post': 'create'}), name='leave_request'),

    # ✅ Desktop auth (sessionid + csrftoken)
    path('desktop/auth/start/', views.DesktopAuthStartView.as_view(), name='desktop_auth_start'),
    path('desktop/auth/complete/', views.DesktopAuthCompleteView.as_view(), name='desktop_auth_complete'),
    path('desktop/auth/exchange/', views.DesktopAuthExchangeView.as_view(), name='desktop_auth_exchange'),
    path("desktop/auth/webview/", views.DesktopAuthWebViewBootstrap.as_view(), name="desktop_auth_webview"),
    path('my_organizations/fire/blocking_relations/', views.FireBlockingRelationsApiView.as_view(), name='blocking-relations'),
    path('my_organizations/fire/non_blocking_relations/', views.FireNonBlockingRelationsApiView.as_view(), name='non-blocking-relations'),
    path('my_organizations/fire/', views.FireAPIView.as_view(), name='fire-user'),
]

router = DefaultRouter()
router.register(r'current_contractor', views.CurrentContractorViewSet, basename='current_contractor')
router.register(r'new_user_info', views.NewUserInfoViewSet, basename='new_user_info')
router.register(r'', views.CustomUserViewSet, basename='users')
router.register(r'google', views.GoogleOAuthViewSet, basename='google')

urlpatterns += router.urls
