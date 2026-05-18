from django.urls import path

from . import views

app_name = "onlyoffice"

urlpatterns = [
    path("config/", views.OnlyofficeConfigView.as_view(), name="config"),
    path("report-session/", views.OnlyofficeReportSessionView.as_view(), name="report-session"),
    path("report-session/refresh/", views.OnlyofficeReportSessionRefreshView.as_view(), name="report-session-refresh"),
    path("download/", views.OnlyofficeDownloadView.as_view(), name="download"),
    path("callback/", views.OnlyofficeCallbackView.as_view(), name="callback"),
]
