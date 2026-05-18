from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination


class PagePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 2000


class StandardPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 2000