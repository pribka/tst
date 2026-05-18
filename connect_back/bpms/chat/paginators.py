from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from django.core.paginator import InvalidPage, Paginator
from rest_framework.exceptions import NotFound

import json
from common.redis import socketio_redis
from . import models
from math import ceil
from django.db.models import Count
from django.db.models import Q


class ChatPagination(PageNumberPagination):
    page_size = 10000
    page_size_query_param = 'page_size'
    max_page_size = 10000
    page_query_param = 'page'


class ChatUserPagination(PageNumberPagination):
    page_size = 10000
    page_size_query_param = 'page_size'
    max_page_size = 10000
    page_query_param = 'page'


class MessagePaginator(Paginator):
    cached_data = None

    def page(self, number):
        cached_data = self.cached_data
        if not cached_data:
            return super().page(number)
        cached_data_count = cached_data.get('data_count')
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        if bottom < cached_data_count:
            bottom = 0
            top = number * self.per_page - cached_data_count
            if top < 0:
                top = 0
            cached_data_bottom = (number - 1) * self.per_page
            cached_data_top = cached_data_bottom + self.per_page
            extra_entry = cached_data.get('data')[cached_data_bottom:cached_data_top]
        else:
            bottom = bottom - cached_data_count
            top = bottom + self.per_page
            extra_entry = []
        page = self._get_page(
            self.object_list.filter(created__lt=cached_data.get('last_created'))[bottom:top], number, self
        )
        setattr(page, 'extra_entry', extra_entry)
        return page

    @cached_property
    def count(self):
        if self.cached_data:
            return super().count + self.cached_data.get('data_count', 0)
        else:
            return super().count


class MessagePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    cached_data = None

    def set_cached_data(self, request):
        data = socketio_redis.hgetall(f'messages:{request.query_params.get("chat")}')
        if not data:
            self.cached_data = None
            return
        data_list = [json.loads(value) for key, value in data.items()]

        def sort_data(val):
            return val['created']

        data_list.sort(key=sort_data, reverse=True)
        self.cached_data = {
            'data': data_list,
            'data_count': len(data_list),
            'last_created': data_list[-1].get('created')
        }

    def paginate_queryset(self, queryset, request, view=None):
        self.set_cached_data(request)
        cached_data = self.cached_data
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        paginator = MessagePaginator(queryset, page_size)
        paginator.cached_data = cached_data
        chat_id = request.query_params.get('chat')
        message_id = request.query_params.get('message')
        if message_id and chat_id and page_size:
            try:
                message = models.MessageModel.objects.get(message_uid=message_id)
            except models.MessageModel.DoesNotExist:
                message = None
            if message:
                qs = Q(created__gte=message.created)
                if cached_data:
                    qs = qs & Q(created__lt=cached_data['last_created'])
                aggr = models.MessageModel.objects.filter(
                    chat_id=chat_id,
                    is_active=True,
                ).aggregate(number=Count('pk', filter=qs))
                page_number = str(ceil(aggr['number'] / int(page_size)))
            else:
                page_number = request.query_params.get(self.page_query_param, 1)
        else:
            page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=exc
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True
        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        extra_entry = getattr(self.page, 'extra_entry', [])
        data = extra_entry + data
        data.reverse()
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class MemberPagination(PageNumberPagination):
    page_size = 10000
    page_size_query_param = 'page_size'
    max_page_size = 10000
    page_query_param = 'page'
