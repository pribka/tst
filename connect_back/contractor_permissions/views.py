import uuid

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Value, Case, When, Value, IntegerField

from django_q.tasks import async_task

from rest_framework import status
from rest_framework.response import Response
from rest_framework import exceptions as drf_exceptions
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.views import BaseCatalogViewSet
from common.paginators import CustomPagination

from common.catalogs.models import ContractorModel, ContractorProfileModel
from common.catalogs.serializers import ContractorModelShortSerializer
from common.utils import use_access_groups, filter_by_search


from users.models import ProfileModel
from users.utils import get_descendants_departments_related_organizations
from users.serializers import CachedAppUserSerializer

from . import models, serializers, permissions, utils, notifications


class ContractorPermissionRoleModelViewSet(BaseCatalogViewSet):
    model = models.ContractorPermissionRoleModel


class PermissionTypeModelViewSet(BaseCatalogViewSet):
    model = models.ContractorPermissionTypeModel

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class PermissionOrganizationListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ContractorModelShortSerializer
    queryset = ContractorModel.objects.filter(is_active=True)

    def get_queryset(self):
        request = self.request
        permission_type_id = request.query_params.get('permission_type')
        if not permission_type_id:
            return self.queryset.none()
        else:
            permission_type_id_list = permission_type_id.split(',')
        user = request.user.profile
        display = request.query_params.get('display')
        if use_access_groups(user.pk):
            from common.utils import get_my_access_groups
            my_access_groups_id = get_my_access_groups(user)
            permission_access_groups_id = models.AccessGroupAppSectionRoleThrough.objects.filter(
                access_group__in=my_access_groups_id,
                app_section_role__permission_type_id__in=permission_type_id_list,
            ).values_list('access_group', flat=True)
            permission_contractor_ids = models.AccessGroupMemberThroughModel.objects.filter(
                access_group__in=permission_access_groups_id,
                member__user=user,
            ).values_list('member__contractor', flat=True)
        else:
            permission_contractor_ids = models.ContractorPermissionModel.objects.filter(
                contractor_permission_role__contractor__in=user.my_organizations,
                contractor_permission_role__is_active=True,
                contractor_permission_role__contractor_profiles__user=user,
                permission_type_id__in=permission_type_id_list,
            ).values_list('contractor_permission_role__contractor', flat=True)

        if display == 'descendants':
            permission_contractor_ids = get_descendants_departments_related_organizations(
                permission_contractor_ids,
                include_self=True
            )
        qs = self.queryset.filter(pk__in=permission_contractor_ids)
        search = request.query_params.get('search')
        if search and len(search) >= 2:
            qs = filter_by_search(search, ContractorModel, qs)
        return qs


class AccessGroupViewSet(BaseCatalogViewSet):
    model = models.AccessGroupModel
    permission_classes = (IsAuthenticated,)

    @action(methods=('get',), detail=True, url_path='members')
    def get_members(self, request, *args, **kwargs):
        instance = self.get_object()
        contractor_id = request.query_params.get('contractor')
        if not contractor_id:
            raise drf_exceptions.ValidationError('param contractor required')
        members = instance.members.filter(contractor_id=contractor_id).values_list('user', flat=True)
        users = ProfileModel.objects.filter(is_active=True, pk__in=members)
        text = request.query_params.get('text')
        if text and len(text) > 2:
            users = users.filter(
                Q(user__first_name__icontains=text)
                | Q(user__last_name__icontains=text)
                | Q(user__middle_name__icontains=text)
            ).distinct()
        paginator = CustomPagination()
        page = paginator.paginate_queryset(users, request, self)
        s_data = CachedAppUserSerializer(page, many=True).data
        response = paginator.get_paginated_response(s_data)
        return response

    @action(methods=('post',), detail=False, url_path='set_user')
    def set_user(self, request, *args, **kwargs):
        from common.catalogs.models import ContractorProfileModel
        data = request.data
        user_id = data.get('user')
        contractor_id = data.get('contractor')
        try:
            contractor_profile = ContractorProfileModel.objects.get(user_id=user_id, contractor_id=contractor_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('ContractorProfile does not exist')
        access_groups_id = data.get('access_groups')
        if access_groups_id:
            try:
                available_access_groups_id = list(utils.get_available_access_groups(
                    contractor_profile.contractor).filter(pk__in=access_groups_id).values_list('pk', flat=True))
            except ValidationError:
                raise drf_exceptions.ValidationError('Invalid access groups')
            contractor_profile.access_groups.set(available_access_groups_id)
        else:
            contractor_profile.access_groups.clear()
        return Response()

    @action(methods=('post',), detail=True, url_path='members/add')
    def add_members(self, request, *args, **kwargs):
        data = request.data
        access_group = self.get_object()
        contractor_id = data.get('contractor')
        if not contractor_id:
            raise drf_exceptions.ValidationError('contractor required')
        try:
            contractor = models.ContractorModel.objects.get(is_active=True, pk=contractor_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('contractor does not exist')
        if not utils.get_available_access_groups(contractor).filter(pk=access_group.pk).exists():
            raise drf_exceptions.ValidationError('Access group is not available')
        members_id = request.data.get('members')
        if not members_id:
            return Response()
        if not isinstance(members_id, list):
            raise drf_exceptions.ValidationError('Invalid members')
        with transaction.atomic():
            for user_id in members_id:
                try:
                    contractor_profile = contractor.contractor_profile.get(user=user_id)
                except (ObjectDoesNotExist, ValidationError):
                    raise drf_exceptions.ValidationError(f'Invalid member {user_id}')
                access_group.members.add(contractor_profile)
        for user_id in members_id:
            cache.delete(f'tariff_section_codes_{user_id}')
            async_task(notifications.notify_about_add_member, str(user_id), str(access_group.pk), str(contractor_id))
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='members/remove')
    def remove_members(self, request, *args, **kwargs):
        data = request.data
        access_group = self.get_object()
        contractor_id = data.get('contractor')
        if not contractor_id:
            raise drf_exceptions.ValidationError('contractor required')
        try:
            contractor = models.ContractorModel.objects.get(is_active=True, pk=contractor_id)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError('contractor does not exist')
        if not utils.get_available_access_groups(contractor).filter(pk=access_group.pk).exists():
            raise drf_exceptions.ValidationError('Access group is not available')
        members_id = request.data.get('members')
        if not members_id:
            return Response()
        if not isinstance(members_id, list):
            raise drf_exceptions.ValidationError('Invalid members')
        with transaction.atomic():
            for user_id in members_id:
                try:
                    contractor_profile = contractor.contractor_profile.get(user=user_id)
                except (ObjectDoesNotExist, ValidationError):
                    raise drf_exceptions.ValidationError(f'Invalid member {user_id}')
                access_group.members.remove(contractor_profile)
        for user_id in members_id:
            cache.delete(f'tariff_section_codes_{user_id}')
        return Response('ok')

    @action(methods=('get',), detail=False, url_path='available_sections')
    def get_available_sections(self, request, *args, **kwargs):
        contractor_id = request.query_params.get('contractor')
        if not contractor_id:
            return Response([])
        try:
            contractor = ContractorModel.objects.get(is_active=True, pk=contractor_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response([])
        available_sections = utils.get_available_sections(contractor).prefetch_related(
            'roles'
        ).order_by('-is_main', 'sort', 'name')
        serializer = serializers.AppSectionListSerializer(
            available_sections,
            many=True,
            context={'request': request, 'view': self}
        )
        data = serializer.data
        return Response(data)


class AppSectionRolesViewSet(BaseCatalogViewSet):
    model = models.AppSectionRoleModel


class AppSectionsViewSet(BaseCatalogViewSet):
    model = models.AppSectionModel
    permission_classes = (IsAuthenticated,)

    @action(methods=('get',), detail=False, url_path='(?P<code>[a-zA-Z_]+)/members')
    def get_members(self, request, *args, **kwargs):
        """Возвращает список пользователей, которые имеют доступ к разделу (администраторы или сотрудники)."""
        from contractor_permissions.utils import users_that_have_app_section_role_in_contractors
        contractor_id = request.query_params.get('contractor')
        first = request.query_params.get('first')
        app_section_code = kwargs['code']
        if not contractor_id:
            raise drf_exceptions.ValidationError('param contractor required')
        users_id = users_that_have_app_section_role_in_contractors(contractor_id, app_section_code, None)
        if users_id:
            users = ProfileModel.objects.filter(is_active=True, pk__in=users_id)
            text = request.query_params.get('text')
            if text and len(text) > 2:
                users = users.filter(
                    Q(user__first_name__icontains=text)
                    | Q(user__last_name__icontains=text)
                    | Q(user__middle_name__icontains=text)
                ).distinct()
            if first:
                first_uuid = uuid.UUID(first)
                users = users.annotate(
                    custom_order=Case(
                        When(id=first_uuid, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                ).order_by('custom_order')
        else:
            users = ProfileModel.objects.none()
        paginator = CustomPagination()
        page = paginator.paginate_queryset(users, request, self)
        s_data = CachedAppUserSerializer(page, many=True).data
        response = paginator.get_paginated_response(s_data)
        return response