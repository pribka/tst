from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'wiki'
from .views import WikiSectionViewSet, WikiChapterViewSet, WikiPageViewSet

router = DefaultRouter()
router.register(r'sections', WikiSectionViewSet)
router.register(r'chapters', WikiChapterViewSet)
router.register(r'pages', WikiPageViewSet)

urlpatterns = [
    path('current_contractor/action_info/', views.CurrentOrganizationActionInfo.as_view(), name='wiki-current-org-action-info',),
    path('<uuid:pk>/access/', views.WikiAccessView.as_view(), name='wiki-access-set'),
    path('<uuid:pk>/access/add/', views.WikiAccessAddView.as_view(), name='wiki-access-add'),
    path('<uuid:pk>/access/remove/', views.WikiAccessRemoveView.as_view(), name='viki-access-remove'),
    path('', include(router.urls)),
]
