from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.views import BaseCatalogViewSet, BaseModelViewSet

from . import deals_models as models


class DealStageViewSet(BaseCatalogViewSet):
    model = models.DealStageModel
    permission_classes = (IsAuthenticated,)

    def _check_manage_permission(self, request):
        user = request.user.profile
        if not getattr(user, 'check_profile_types', None) or not user.check_profile_types({'superuser', 'admin'}):
            raise PermissionDenied('Недостаточно прав для изменения стадий сделок.')

    def create(self, request, *args, **kwargs):
        self._check_manage_permission(request)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._check_manage_permission(request)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._check_manage_permission(request)
        return super().partial_update(request, *args, **kwargs)


class DealViewSet(BaseModelViewSet):
    model = models.DealModel
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super().get_queryset()
        stage_id = self.request.query_params.get('stage')
        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)
        return queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise PermissionDenied('Недостаточно прав для изменения сделки.')
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise PermissionDenied('Недостаточно прав для изменения сделки.')
        return super().partial_update(request, *args, **kwargs)
