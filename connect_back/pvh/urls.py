from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api_plan_of_characteristic'

router = DefaultRouter()
router.register("", views.PlanOfCharacteristicViewSet, basename='pvh')

urlpatterns = [
    path('attr_names/', views.AttrNamesView.as_view(), name='attr_names'),
    path('properties/', views.PropertyListViewSet.as_view(), name='pvh_properties')
]
urlpatterns = urlpatterns + router.urls


