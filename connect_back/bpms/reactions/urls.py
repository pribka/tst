from rest_framework import routers

from . import views


app_name = 'api_reactions'

router = routers.DefaultRouter()

router.register('', views.ReactionViewSet, basename='reactions',)

urlpatterns = []

urlpatterns = urlpatterns + router.urls

