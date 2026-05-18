from django.apps import apps
from django.urls import include, path, re_path

from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from bkz3.settings import REPORTS_UNIVERSAL_MODELS

from . import views


router = DefaultRouter()

model_paths = REPORTS_UNIVERSAL_MODELS
for model_path in model_paths:
    model = apps.get_model(model_path)
    app_label = model._meta.app_label
    model_name = model.__name__
    basename = f'{app_label}__{model.__name__}'  # сохраняем регистр!
    router.register(model.__name__.lower(), views.UniversalModelViewSet, basename=basename)

router.register(r"report_settings", views.ReportSettingsModelViewSet, "report-settings")
router.register(r"user_report_settings", views.UserReportSettingsModelViewSet, "user-report-settings")

urlpatterns = [
    # path('<str:model>/forms/<str:form_name>/<str:action_name>/', views.form_action_view, name='form-action'),
    path('clear-meta-cache/', views.clear_meta_cache, name='clear-meta-cache'),
    path('', include(router.urls)),

]
