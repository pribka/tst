from rest_framework import routers
from . import views as f_views
from django.urls import path, include

app_name = 'favorites'

router = routers.DefaultRouter()
router.register(r'', f_views.FavoritesViewSet, basename='favorites')

urlpatterns = [
    path('', include(router.urls)),
]
