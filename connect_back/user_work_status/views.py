from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from common.views import BaseCatalogViewSet

from . import models
from . import serializers


class UserWorkStatusViewSet(ViewSet):

    @action(methods=('get',), detail=False, url_path='my', permission_classes=(IsAuthenticated,))
    def get_my_work_status(self, request, *args, **kwargs):
        user = request.user.profile
        my_work_status = models.UserWorkStatusRecordingModel.objects.filter(user=user).order_by('-created_at').first()
        if not my_work_status:
            my_work_status = models.UserWorkStatusRecordingModel.objects.create(user=user, status_id='completed',)
        serialized_data = serializers.AppUserWorkStatusRecordingModelSerializer(my_work_status)
        return Response(serialized_data.data)

    @action(methods=('post',), detail=False, url_path='my/create', permission_classes=(IsAuthenticated,))
    def create_current_work_status(self, request, *args, **kwargs):
        data = request.data
        serializer = serializers.UserWorkStatusRecordingModelCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserWorkStatusReasonViewSet(BaseCatalogViewSet):
    model = models.UserWorkStatusReasonModel
