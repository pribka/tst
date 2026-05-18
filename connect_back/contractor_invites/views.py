from django_q.tasks import async_task

from django.db.models import Q

from rest_framework import generics
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from common.catalogs.models import ContractorProfileModel
from common.paginators import CustomPagination

from . import models, notifications, serializers, utils


class ContractorInviteModelCreateView(generics.CreateAPIView):
    serializer_class = serializers.ContractorInviteModelCreateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        s_data = serializers.ContractorInviteModelListSerializer(instance, context={"request": request}).data
        async_task(notifications.notify_invite_contractor, instance)
        return Response(s_data)


class ContractorInviteModelMyListView(generics.ListAPIView):
    serializer_class = serializers.ContractorInviteModelListSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user.profile
        i_am_director = ContractorProfileModel.objects.filter(
            is_active=True, director=True, user=user
        ).values_list('contractor', flat=True)
        qs = models.ContractorInviteModel.objects.select_related(
            'contractor_owner', 'contractor_parent', 'contractor', 'relation_type',
        ).filter(
            is_active=True, contractor_owner__in=i_am_director
        ).order_by('-created_at',)
        contractor_id = self.request.query_params.get('contractor_owner')
        if contractor_id:
            qs = qs.filter(contractor_owner=contractor_id)
        return qs


class ContractorInviteModelDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.ContractorInviteModelDetailSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user.profile
        i_am_director = ContractorProfileModel.objects.filter(
            is_active=True, director=True, user=user
        ).values_list('contractor', flat=True)
        queryset = models.ContractorInviteModel.objects.filter(
            Q(contractor__in=i_am_director) | Q(contractor_parent__in=i_am_director),
            is_active=True,
        )
        return queryset


class ContractorInviteModelForMeListView(generics.ListAPIView):
    serializer_class = serializers.ContractorInviteModelListSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user.profile
        i_am_director = ContractorProfileModel.objects.filter(
            is_active=True, director=True, user=user
        ).values_list('contractor', flat=True)
        qs = models.ContractorInviteModel.objects.select_related(
            'contractor_owner', 'contractor_parent', 'contractor', 'relation_type',
        ).filter(
            Q(contractor__in=i_am_director) | Q(contractor_parent__in=i_am_director), is_active=True,
        ).exclude(contractor_owner__in=i_am_director).order_by('-created_at', )
        contractor_id = self.request.query_params.get('contractor_owner')
        if contractor_id:
            qs = qs.filter(Q(contractor_id=contractor_id) | Q(contractor_parent_id=contractor_id))
        return qs


class ContractorInviteModelDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = serializers.ContractorInviteModelDeleteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data.get('id')
        if instance:
            instance.delete()
        return Response('ok')


class ContractorInviteModelAcceptView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        invite = utils.get_invite(request)
        invite = utils.accept_invite(invite)
        s_data = serializers.ContractorInviteModelListSerializer(invite, context={'request': request}).data
        return Response(s_data)


class ContractorInviteModelRejectView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        invite = utils.get_invite(request)
        invite = utils.reject_invite(invite)
        s_data = serializers.ContractorInviteModelListSerializer(invite, context={'request': request}).data
        return Response(s_data)
