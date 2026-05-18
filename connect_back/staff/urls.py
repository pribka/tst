from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'staff'

router = DefaultRouter()
router.register(r'recruitment', views.RecruitmentViewSet, basename='recruitment')
router.register(r'types_of_employment', views.TypeOfEmploymentViewSet, basename='types-of-employment')
router.register(r'dismissal', views.DismissalViewSet, basename='dismissal')
router.register(r'show', views.ShowViewSet, basename='show')
router.register(r'mycatalog', views.MyCatalogViewSet, basename='mycatalog')
router.register(r'mydocument', views.MyDocumentViewSet, basename='mydocument')
router.register(r'weather', views.WeatherModelViewSet, basename='weather')
router.register(r'season', views.SeasonModelViewSet, basename='season')
router.register(r'month', views.MonthModelViewSet, basename='month')
router.register(r'country', views.CountryModelViewSet, basename='country')
router.register(r'city', views.CityModelViewSet, basename='city')
router.register(r'street', views.StreetModelViewSet, basename='street')
urlpatterns = router.urls
