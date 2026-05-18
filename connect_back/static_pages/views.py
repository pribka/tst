from rest_framework import response
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from . import serializers
from . import models


class StaticPageModelRetrieveView(RetrieveAPIView):
    serializer_class = serializers.StaticPageModelSerializer
    queryset = models.StaticPageModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    lookup_field = 'code'
