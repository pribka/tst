from collections import OrderedDict

from rest_framework.response import Response

from common.paginators import CustomPagination


class AdvanceReportPagination(CustomPagination):
    def get_paginated_response(self, data):
        amount_sum = data.get('amount_sum')
        if not amount_sum:
            amount_sum = 0
        results = data.get('results')
        data_list = [
            ('amount_sum', amount_sum),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', results)
        ]
        return Response(OrderedDict(data_list))
