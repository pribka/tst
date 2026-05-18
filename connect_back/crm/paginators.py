from collections import OrderedDict

from django.db.models import Sum

from rest_framework.response import Response
from rest_framework.serializers import DecimalField
from rest_framework.exceptions import NotFound

from common.paginators import CustomPagination
from common.catalogs.utils import get_user_price_type
from common.catalogs.models import ContractModel

class ShoppingCartPagination(CustomPagination):

    def paginate_queryset(self, queryset, request, view=None):
        amount = DecimalField(decimal_places=2, max_digits=15).to_representation(queryset.aggregate(Sum('amount'))['amount__sum'])
        if not amount:
            amount = "0.00"
        setattr(self, 'amount', amount)
        contract_id = request.query_params.get('contract')
        if not contract_id:
            price_type = get_user_price_type(request.user.profile)
        else:
            try:
                contract = ContractModel.objects.get(pk=contract_id)
            except ContractModel.DoesNotExist:
                raise NotFound('Contract not found.')
            price_type = contract.price_type
        currency = price_type.currency
        setattr(self, 'currency', {'name': currency.name, 'icon': currency.icon})
        return super().paginate_queryset(queryset, request, view=None)

    def get_paginated_response(self, data):
        data_list = [
            ('amount', getattr(self, 'amount', "0.00")),
            ('currency', getattr(self, 'currency', "")),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]
        return Response(OrderedDict(data_list))


class TPGoodsOrderPagination(CustomPagination):

    def paginate_queryset(self, queryset, request, view=None):
        order = view.get_object()
        amount = DecimalField(max_digits=15, decimal_places=2).to_representation(order.amount)
        setattr(self, 'amount', amount)
        price_type = order.contract.price_type
        currency = price_type.currency
        setattr(self, 'currency', {'name': currency.name, 'icon': currency.icon})
        return super().paginate_queryset(queryset, request, view=None)

    def get_paginated_response(self, data):
        for each in data:
            each['goods']['currency'] = getattr(self, 'currency', '')

        data_list = [
            ('amount', getattr(self, 'amount', "0.00")),
            ('currency', getattr(self, 'currency', "")),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]
        return Response(OrderedDict(data_list))
