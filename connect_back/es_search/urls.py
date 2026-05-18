from django.urls import path
from es_search.views import universal_search_view

app_name = 'search'

urlpatterns = [
    path("", universal_search_view, name="universal-search"),
]
