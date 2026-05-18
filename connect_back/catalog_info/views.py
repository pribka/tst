from rest_framework.views import APIView
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.utils import get_available_app_section_roles_through


from . import models, serializers


class CatalogInfoListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        app_section_roles = get_available_app_section_roles_through(profile)
        qs = models.CatalogInfoModel.objects.filter(is_active=True, app_section_roles__in=app_section_roles)
        sections_id = set(qs.values_list('section', flat=True))
        sections = models.CatalogSectionModel.objects.filter(is_active=True, pk__in=sections_id).order_by(
            'sort',
            'name'
        )
        serializer = serializers.CatalogInfoSectionSerializer(
            sections,
            many=True,
            context={
                'request': request,
                'view': self,
                'catalog_qs': qs,
            }
        )
        return Response(serializer.data)
