from django.urls import path
from . import apiviews
from rest_framework.routers import DefaultRouter

app_name = 'flowchart'
router = DefaultRouter()
router.register(r"", apiviews.FlowchartApiViewSet, "flowchart")

urlpatterns = router.urls
