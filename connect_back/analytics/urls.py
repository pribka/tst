from rest_framework.routers import DefaultRouter

from . import views

app_name = 'analytics'

router = DefaultRouter()
# Конкретные префиксы регистрируем первыми, иначе "summaries/" матчится как pk корневого вьюсета (POST даёт 405)
router.register(r'dashboard', views.DashboardConfigViewSet, basename='dashboard-config')
router.register(r'summaries', views.ActivitySummaryViewSet, basename='activity-summary')
router.register(r'digests', views.ActivityDigestViewSet, basename='activity-digest')
router.register(r'', views.ActivityViewSet, basename='activity')

urlpatterns = router.urls
