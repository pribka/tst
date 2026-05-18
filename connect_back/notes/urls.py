from . import views
from django.urls import path, include
from rest_framework import routers

app_name = 'api_notes'

router = routers.DefaultRouter()

router.register("colors", views.ColorNoteModelViewSet, basename='note_colors')

router.register("", views.NoteModelViewSet, basename='notes')

urlpatterns = router.urls
