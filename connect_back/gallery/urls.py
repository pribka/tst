from rest_framework import routers
from . import views
app_name = 'gallery'
router = routers.DefaultRouter()
router.register(r'', views.GalleryModelViewSet, basename='gallery')
urlpatterns = router.urls
