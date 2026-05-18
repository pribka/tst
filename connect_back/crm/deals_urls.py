from rest_framework import routers

from . import deals_views

app_name = 'crm_deals'
router = routers.DefaultRouter()
router.register(r'stages', deals_views.DealStageViewSet, basename='deal-stages')
router.register(r'deals', deals_views.DealViewSet, basename='deals')

urlpatterns = router.urls
