from django.shortcuts import render
from rest_framework.decorators import action
from . import models
from common import views as common_views


class RecruitmentViewSet(common_views.BaseDocumentViewSet):
    model = models.Recruitment

    @action(methods=["get", ], detail=True, url_path='workers')
    def get_tp_workers(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)

    @action(methods=["get", ], detail=True, url_path='accruals')
    def get_tp_accruals(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class TypeOfEmploymentViewSet(common_views.BaseCatalogViewSet):
    model = models.TypeOfEmployment


class DismissalViewSet(common_views.BaseDocumentViewSet):
    model = models.Dismissal

    @action(methods=['get', ], detail=True, url_path='staff')
    def get_tp_dismiss_staff(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class ShowViewSet(common_views.BaseDocumentViewSet):
    model = models.Show

    @action(methods=["get", ], detail=True, url_path='tabular')
    def get_tp_tabular(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class MyCatalogViewSet(common_views.BaseCatalogViewSet):
    model = models.MyCatalog


class MyDocumentViewSet(common_views.BaseDocumentViewSet):
    model = models.MyDocument

    @action(methods=["get", ], detail=True, url_path='catalog')
    def get_tp_catalog(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class WeatherModelViewSet(common_views.BaseCatalogViewSet):
    model = models.WeatherModel


class SeasonModelViewSet(common_views.BaseCatalogViewSet):
    model = models.SeasonModel


class MonthModelViewSet(common_views.BaseCatalogViewSet):
    model = models.MonthModel


class CountryModelViewSet(common_views.BaseCatalogViewSet):
    model = models.CountryModel


class CityModelViewSet(common_views.BaseCatalogViewSet):
    model = models.CityModel


class StreetModelViewSet(common_views.BaseCatalogViewSet):
    model = models.StreetModel

