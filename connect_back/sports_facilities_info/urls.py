from rest_framework.routers import DefaultRouter
from . import views

app_name = 'sports_facilities'

router = DefaultRouter()
router.register(r'purposes', views.SportFacilityPurposeModelViewSet, basename='sports_facilities_purposes')
router.register(r'types', views.SportFacilityTypeModelViewSet, basename='sports_facilities_types')
router.register(r'sport_categories', views.SportTypeCategoryViewSet, basename='sport_type_categories')
router.register('sport_types', views.SportTypeViewSet, basename='sport_types')
router.register('renovation/types', views.SportFacilityRenovationTypeViewSet, basename='renovation_types')
router.register('renovation/work_types', views.SportFacilityRenovationWorkTypeViewSet, basename='renovation_work_types')

router.register('renovation', views.SportFacilityRenovationInfoViewSet, basename='renovation_info')
router.register(r'', views.SportFacilityInfoViewSet, basename='sports_facilities')


urlpatterns = router.urls
