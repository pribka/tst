from django.shortcuts import render
from rest_framework.decorators import action
from . import models
from common import views as common_views
from django.db.models import Max, F


class EditionViewSet(common_views.BaseCatalogViewSet):
    model = models.EditionModel


class EditionUnitViewSet(common_views.BaseCatalogViewSet):
    model = models.EditionUnitModel

    def filter_queryset(self, queryset):
        """
        Осставляем только экземпляры которые имеют запись в регистре
        """
        in_warehouse = self.request.query_params.get('in_warehouse')
        if in_warehouse == 'true':
            queryset = queryset.prefetch_related('registered').annotate(
                latest_record=Max('registered__created_at')).filter(
                registered__created_at=F('latest_record')).distinct()
        filtered_qs = super().filter_queryset(queryset)
        return filtered_qs


class EditionPartViewSet(common_views.BaseCatalogViewSet):
    model = models.EditionPartModel


class IncomingInvoiceViewSet(common_views.BaseDocumentViewSet):
    model = models.ReceiptInvoiceEditionUnitModel

    @action(methods=["get", ], detail=True, url_path='units')
    def get_tp_edition_units(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)

    @action(methods=["get", ], detail=True, url_path='editions')
    def get_tp_editions(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class ActWriteOffViewSet(common_views.BaseDocumentViewSet):
    model = models.ActWriteOffEditionUnitModel

    @action(methods=["get", ], detail=True, url_path='editions')
    def get_tp_editions_units(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class EditionUnitTransferViewSet(common_views.BaseDocumentViewSet):
    model = models.EditionUnitTransferModel

    @action(methods=["get", ], detail=True, url_path='editions')
    def get_tp_editions_units_transfer(self, request, *args, **kwargs):
        return self.get_tabular_parts(request, pk=None)


class EditionAuthorViewSet(common_views.BaseCatalogViewSet):
    model = models.EditionAuthorModel


class EditionPublisherViewSet(common_views.BaseCatalogViewSet):
    model = models.EditionPublisherModel
# Create your views here.
