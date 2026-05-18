from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "day_summary"

router = DefaultRouter()
router.register("note", views.DaySummaryNoteViewSet, basename="day-summary-note")

urlpatterns = [
    path("categories/", views.DaySummaryNoteCategoryListView.as_view(), name="note-categories"),
    path("", include(router.urls)),
]
