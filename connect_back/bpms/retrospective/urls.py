from rest_framework import routers

from . import views

app_name = 'api_retrospective'

router = routers.DefaultRouter()

router.register('', views.RetrospectiveViewSet, 'retrospective')

urlpatterns = router.urls
