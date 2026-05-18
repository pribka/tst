from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from django.db.models.aggregates import Sum
from django.db.models import F, DecimalField, ExpressionWrapper
from math import floor


class CustomPagination(PageNumberPagination):
    page_size = 40
    page_size_query_param = 'page_size'
    max_page_size = 80
    page_query_param = 'page'

    def paginate_queryset(self, queryset, request, view=None):
        slice_count = request.query_params.get('slice_count')
        if slice_count:
            excluded = queryset[:int(slice_count)]
            queryset = queryset.exclude(pk__in=excluded)
        page_size = request.query_params.get('page_size')
        if page_size == 'all':
            request.query_params._mutable = True
            request.query_params['page_size'] = queryset.count()
            return super().paginate_queryset(queryset, request, view)

        try:
            start_row = int(request.query_params.get('start_row'))
            end_row = int(request.query_params.get('end_row')) + 1
        except TypeError:
            return super().paginate_queryset(queryset, request, view)
        if start_row is not None and end_row is not None:
            page_size = end_row - start_row
            request.query_params._mutable = True
            request.query_params['page_size'] = page_size
            request.query_params['page'] = floor(end_row / page_size)
            request.query_params._mutable = False
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):  # Кастомный респонс в пагинацию
        data_list = [
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]
        model = getattr(self.page.paginator.object_list, 'model', None)
        # словарь "calculations" для таб. частеей документов, для вычислияемых значений всей таблицы
        if hasattr(model,
                   'need_summ_pagination') and model.need_summ_pagination:  # Проверяем у модели таб. части есть ли атрибут
            calculations = {}
            objects_list = self.page.paginator.object_list.values('amount', "quantity")
            objects_list_subtotal = objects_list.annotate(subtotal=ExpressionWrapper(F('amount') * F('quantity'),
                                                                                     output_field=DecimalField()))
            calculo_total = objects_list_subtotal.aggregate(total=Sum('subtotal'))  # считаем сумму каждой записи
            try:
                calculations['total_amount'] = int(calculo_total['total'])  # считаем тотал
            except TypeError:
                calculations['total_amount'] = 0

            calculo_total_amount = objects_list_subtotal.aggregate(total_amount=Sum('amount'))
            calculo_total_quantity = objects_list_subtotal.aggregate(total_quantity=Sum('quantity'))

            try:
                calculations['amount'] = int(calculo_total_amount['total_amount'])  # сумма всех цен
            except TypeError:
                calculations['amount'] = 0
            try:
                calculations['quantity'] = int(calculo_total_quantity['total_quantity'])  # сумма количества
            except TypeError:
                calculations['quantity'] = 0
            # calculations['footer'] = True

            data_list.insert(0, ('calculations', calculations))
        return Response(OrderedDict(data_list))


class BreadCramsCustomPaginator(CustomPagination):

    def get_paginated_response(self, data, breadcrumbs=None, folder_name=None):
        data_list = [
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('breadcrumbs', breadcrumbs),
            ('name', folder_name),
            ('results', data)
        ]
        return Response(OrderedDict(data_list))


class CustomFilterPagination(CustomPagination):
    page_size = 40
    page_size_query_param = 'page_size'
    max_page_size = 80
    page_query_param = 'page'

    def get_paginated_response(self, data):  # Кастомный респонс в пагинацию
        data_list = [
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('filteredSelectList', data)
        ]
        return Response(OrderedDict(data_list))


class NoTablePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'
