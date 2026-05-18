from rest_framework.permissions import IsAuthenticated

from common.views import BaseModelViewSet

from . import models, serializers, utils, permissions


class RetrospectiveViewSet(BaseModelViewSet):
    model = models.RetrospectiveModel
    permission_classes = (IsAuthenticated, permissions.RetrospectivePermission)
