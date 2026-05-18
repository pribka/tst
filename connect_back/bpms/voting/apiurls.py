from django.urls import path

from . import apiviews

app_name = 'api_voting'

urlpatterns = [
    path('<uuid:pk>/', apiviews.VoteView.as_view(), name='vote'),
    path('rating/', apiviews.UserRatingView.as_view(), name='rating')
]
