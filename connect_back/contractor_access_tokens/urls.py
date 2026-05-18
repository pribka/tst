from django.urls import path

from rest_framework import routers

from . import views

app_name = 'contractor_access_tokens'

router = routers.DefaultRouter()
router.register(r'', views.ContractorAccessModelViewSet, basename='contractor-access-tokens')

urlpatterns = [
    # path(r'', views..as_view(), name=''),
]

urlpatterns = urlpatterns + router.urls