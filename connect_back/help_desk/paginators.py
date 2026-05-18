from collections import OrderedDict

from common.paginators import CustomPagination
from rest_framework.response import Response


class ContactPersonMessagePaginator(CustomPagination):

    def get_paginated_response(self, data):
        data.reverse()
        data_list = [
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]
        return Response(OrderedDict(data_list))
