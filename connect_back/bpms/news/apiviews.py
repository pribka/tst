import json

from django.db.models import Q, Count, F, Exists, Case, Value, IntegerField, When
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.dateparse import parse_date

from rest_framework import status, generics, exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.decorators import action

from common import utils as common_utils
from common.paginators import CustomPagination
from common.views import BaseModelViewSet
from bpms.workgroups.models import WorkgroupModel

from . import permissions
from . import serializers
from . import models
from . import utils

from bpms.bpms_common import models as common_models
from common.utils import order_queryset_from_get_param
from common.models import BaseModel


class UnreadCountView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.NewsListSerializer
    queryset = common_models.NewsModel.objects.filter(is_active=True)
    pagination_class = CustomPagination
    model = common_models.BaseModel

    def list(self, request, *args, **kwargs):
        qs1 = common_models.NewsModel.objects.filter(is_active=True, is_independent=True).count()

        qs2 = common_models.NewsModel.objects.filter(is_active=True, is_independent=True,
                                                     viewers__user=request.user).count()

        return Response({"unread_count": qs1 - qs2})



class ListNewsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.NewsListSerializer
    queryset = common_models.NewsModel.objects.filter(is_active=True)
    pagination_class = CustomPagination
    model = common_models.BaseModel

    def get_queryset(self):
        base_qs = super().get_queryset()

        related_object_id = self.request.query_params.get('related_object')
        request = self.request
        is_banner_param = self.request.query_params.get('is_banner', '')
        if is_banner_param == 'true':
            base_qs = base_qs.filter(is_banner=True)
        if related_object_id:
            try:
                related_object = BaseModel.objects.super_get(related_object_id)
            except BaseModel.DoesNotExist:
                return base_qs.none()
            if related_object.get_detail_permission(request):
                base_qs = base_qs.filter(related_object=related_object_id)
            else:
                return base_qs.none()
        else:
            user = request.user.profile
            my_workgroups = utils.get_my_workgroups(request)
            try:
                checked_category = models.CheckedNewsCategoryModel.objects.get(user=user)
            except models.CheckedNewsCategoryModel.DoesNotExist:
                base_qs = base_qs.filter(
                    Q(is_independent=True) | Q(work_groups__in=my_workgroups.values_list('pk', flat=True))
                ).distinct()
            else:
                checked_category_data = checked_category.data
                category_id_list = checked_category_data.get('categories')
                lookup = Q()
                if category_id_list:
                    lookup = lookup | Q(category_id__in=category_id_list, is_independent=True)
                workgroup_id_list = checked_category_data.get('workgroups')
                if workgroup_id_list:
                    my_workgroups = my_workgroups.filter(pk__in=workgroup_id_list)
                    lookup = lookup | Q(
                        work_groups__in=my_workgroups.values_list('pk', flat=True), is_independent=False
                    )
                if lookup:
                    base_qs = base_qs.filter(lookup).distinct()
                else:
                    base_qs = base_qs.filter(
                        Q(is_independent=True) | Q(work_groups__in=my_workgroups.values_list('pk', flat=True))
                    ).distinct()

        qs = order_queryset_from_get_param(request, self.model, base_qs)
        if not qs.ordered:
            qs = qs.order_by('-created_at')
        return qs


class DetailNewsView(generics.RetrieveAPIView):
    permission_classes = (permissions.DetailNewsPermission,)
    serializer_class = serializers.NewsDetailSerializer
    queryset = common_models.NewsModel.objects.filter(is_active=True, )


class CreateNewsView(generics.CreateAPIView):
    permission_classes = (permissions.CreateNewsPermission,)
    serializer_class = serializers.NewsCreateSerializer
    queryset = common_models.NewsModel.objects.filter(is_active=True, is_independent=True)


class UpdateNewsView(generics.UpdateAPIView):
    permission_classes = (IsAdminUser, permissions.UpdateNewsPermission)
    serializer_class = serializers.NewsUpdateSerializer
    queryset = common_models.NewsModel.objects.filter(is_active=True, is_independent=True)


class NewsActionInfoView(APIView):

    def get(self, request, *args, **kwargs):
        actions = dict()
        try:
            obj = common_models.NewsModel.objects.get(is_active=True, pk=kwargs.get('pk'))
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('news not found')
        user = request.user.profile
        if obj.author == user or user.is_support or request.user.is_staff:
            actions = {
                'edit': {'availability': True},
                'delete': {'availability': True}
            }
        return Response({'actions': actions})


class NewsFiltersView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response(utils.get_news_filters(request))


class CheckCategoryNewsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user.profile
        checked_categories, created = models.CheckedNewsCategoryModel.objects.get_or_create(user=user)
        category_type = request.data.get('type')
        category_id = request.data.get('id')
        data = checked_categories.data
        data_list = data.get(category_type, 'none')
        if data_list == 'none':
            return Response(utils.get_news_filters(request))
        data_list = set(data_list)
        data_list.add(category_id)
        data[category_type] = list(data_list)
        checked_categories.data = json.dumps(data)
        checked_categories.save()
        return Response(utils.get_news_filters(request))


class UncheckCategoryNewsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user.profile
        checked_categories, created = models.CheckedNewsCategoryModel.objects.get_or_create(user=user)
        category_type = request.data.get('type')
        category_id = request.data.get('id')
        data = checked_categories.data
        data_list = data.get(category_type, 'none')
        if data_list == 'none':
            return Response(utils.get_news_filters(request))
        data_list = set(data_list)
        data_list.discard(category_id)
        data[category_type] = list(data_list)
        checked_categories.data = json.dumps(data)
        checked_categories.save()
        return Response(utils.get_news_filters(request))
