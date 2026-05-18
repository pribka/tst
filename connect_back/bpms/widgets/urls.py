from rest_framework.routers import DefaultRouter
from . import views
from .apps import WidgetsConfig
from .views import WidgetCategoryViewSet, WidgetViewSet, DesktopTemplateViewSet, UserDesktopViewSet, \
    UserWidgetOnDesktopViewSet

app_name = WidgetsConfig.name
router = DefaultRouter()


# router.register(
#     r"user_widgets", views.UserWidgetView, "user_widgets"
# )
router.register(r'widget_categories', WidgetCategoryViewSet)
router.register(r'widgets', WidgetViewSet)
router.register(r'desktop_templates', DesktopTemplateViewSet)
router.register(r'user_desktops', UserDesktopViewSet)
router.register(r'user_widgets_on_desktop', UserWidgetOnDesktopViewSet)

urlpatterns = router.urls
