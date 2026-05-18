from datetime import datetime

from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Count, Q, Sum, When, Case, Value, BooleanField, Subquery, OuterRef
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http.response import Http404, FileResponse


from rest_framework import exceptions as drf_exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

from django_q.tasks import async_task

from common.views import BaseModelViewSet, BaseCatalogViewSet
from common.catalogs.models import LocationAdminAreaModel
from common.catalogs.serializers import LocationAdminAreaShortSerializer

from users.utils import get_ancestor_departments_related_organizations

from contractor_permissions.utils import contractors_where_user_has_permission

from . import models, serializers, utils, permissions, notifications


class SportFacilityInfoViewSet(BaseModelViewSet):
    model = models.SportFacilityInfoModel
    permission_classes = (IsAuthenticated, permissions.SportFacilityPermission)

    def get_queryset(self):
        qs = super().get_queryset()

        return qs

    @action(methods=('get',), detail=False, url_path='report')
    def get_report(self, request, *args, **kwargs):
        stream = utils.get_file_response(request)
        return FileResponse(stream, as_attachment=True, filename='otchet.xlsx')

    def filter_qs_from_param(self, queryset):
        if self.request.method == 'GET':
            query_params = self.request.query_params
        else:
            query_params = self.request.data
        region_id = query_params.get('region')
        if region_id:
            queryset = queryset.filter(location_points__admin_area__parent_id=region_id)
        district_id = query_params.get('district')
        if district_id:
            queryset = queryset.filter(location_points__admin_area_id=district_id)
        return queryset

    @action(methods=('get', 'post',), detail=False, url_path='locations/count')
    def get_locations_count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.filter_qs_from_param(queryset)
        if request.method == 'GET':
            query_params = request.query_params
        else:
            query_params = request.data
        zoom = int(query_params.get('zoom', 13))
        if 'district' in query_params:
            data = utils.get_points_data(queryset, query_params)
            return Response(data)
        if 'region' in query_params and zoom <= 9:
            data = utils.get_regions_districts_data(queryset, query_params, districts=True)
            return Response(data)
        if zoom <= 6:
            data = utils.get_regions_districts_data(queryset, query_params, districts=False)
            return Response(data)
        if 7 <= zoom <= 9:
            data = utils.get_regions_districts_data(queryset, query_params, districts=True)
            return Response(data)
        data = utils.get_points_data(queryset, query_params)
        return Response(data)

    @action(methods=('get', 'post',), detail=False, url_path='points')
    def get_points(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if request.method == 'GET':
            query_params = request.query_params
        else:
            query_params = request.data
        lat_gte = query_params.get('lat__gte', 0)
        lat_lte = query_params.get('lat__lte', 0)
        lon_gte = query_params.get('lon__gte', 0)
        lon_lte = query_params.get('lon__lte', 0)

        queryset = self.filter_qs_from_param(queryset)
        queryset = queryset.filter(
            location_points__lat__gte=lat_gte,
            location_points__lat__lte=lat_lte,
            location_points__lon__gte=lon_gte,
            location_points__lon__lte=lon_lte,
        ).distinct()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            # "summary": utils.get_summary(queryset),
            "results": serializer.data
        }
        return Response(data)

    @action(methods=('get',), detail=False, url_path='aggregate')
    def get_aggregate(self, request, *args, **kwargs):

        qs = self.filter_queryset(self.get_queryset())
        ownership_forms = qs.values('ownership_form').order_by().annotate(count=Count('pk')).values('ownership_form', 'count')
        current_year = timezone.localdate().year
        current_year_date = datetime(year=current_year, month=1, day=1)
        renovation_amount = qs.aggregate(
            amount_sum=Sum(
                'renovation_info__amount', filter=Q(renovation_info__renovation_date__gte=current_year_date)
            )
        )
        renovation_types = qs.values(
            'renovation_info__renovation_type'
        ).order_by().annotate(
            amount_sum=Sum(
                'renovation_info__amount',
                filter=Q(renovation_info__renovation_date__gte=current_year_date),
                distinct=True,
            )
        ).values('renovation_info__renovation_type', 'amount_sum',)

        facility_types = qs.values('facility_type').order_by().annotate(count=Count('pk')).values('facility_type', 'count')
        for each in ownership_forms:
            if each['ownership_form'] is None:
                each['ownership_form'] = {'name': 'Не указан', 'code': None}
            else:
                ownership_form_instance = models.SportFacilityOwnershipFormModel.objects.get(code=each['ownership_form'])
                each['ownership_form'] = serializers.OwnershipFormSerializer(ownership_form_instance).data
        for each in facility_types:
            if each['facility_type'] is None:
                each['facility_type'] = {'name': 'Не указан', 'code': None}
            else:
                facility_type_instance = models.SportFacilityTypeModel.objects.get(code=each['facility_type'])
                each['facility_type'] = serializers.SportFacilityTypeModelSerializer(facility_type_instance).data
        renovation_info_data = list()
        for each in renovation_types:
            if each['renovation_info__renovation_type'] is None:
                if each['amount_sum']:
                    renovation_info_data.append(
                        {
                            'name': 'Не указан',
                            'code': None,
                            'amount_sum': each['amount_sum']
                        }
                    )
                else:
                    continue
            else:
                renovation_info_instance = models.SportFacilityRenovationTypeModel.objects.get(
                    code=each['renovation_info__renovation_type']
                )
                renovation_info_data.append(
                    {
                        'name': renovation_info_instance.name,
                        'code': each['renovation_info__renovation_type'],
                        'amount_sum': each['amount_sum'] if each['amount_sum'] is not None else 0,
                    }
                )
        data = {
            'count': qs.count(),
            'count_facility_types': facility_types.count(),
            'renovation_info':
                {
                    'amount_sum': renovation_amount['amount_sum'] if renovation_amount['amount_sum'] is not None else 0,
                    'renovation_types': renovation_info_data,
                },
            'ownership_forms': ownership_forms,
            'facility_types': facility_types,
        }
        return Response(data)

    @action(methods=('get',), detail=False, url_path='status_statistics', )
    def get_status_statistics(self, request, *args, **kwargs):
        """Статистика по количеству спортивных объектов в каждом статусе."""
        queryset = self.filter_queryset(self.get_queryset())
        count_queryset = (
            queryset.values('status').order_by().annotate(count=Count('id')).values(
                'status',
                'count',
            )
        )
        status_queryset = models.SportFacilityStatusModel.get_select_queryset(request)
        status_codes = status_queryset.values_list('code', flat=True)
        results_dict = {'total': queryset.count()}
        results_dict.update({status: 0 for status in status_codes})

        for entry in count_queryset:
            results_dict.update({entry['status']: entry['count']})
        results = [{'status': key, 'count': value} for key, value in results_dict.items()]
        return Response(serializers.SportFacilityStatusStatisticsSerializer(results, many=True).data)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        data = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            data.update(
                {
                    'edit': {
                        'availability': True
                    },
                    'documents': {
                        'availability': True
                    },
                    'gallery': {
                        'availability': True
                    },
                    'renovation_info': {
                        'availability': True
                    },
                    'buildings_add': {
                        'availability': True
                    },
                    'buildings_edit': {
                        'availability': True
                    },
                    'buildings_delete': {
                        'availability': True
                    },
                    'sections_add': {
                        'availability': True
                    },
                    'sections_edit': {
                        'availability': True
                    },
                    'sections_delete':{
                        'availability': True
                    }
                }
            )
        if instance.get_delete_permission(request):
            data.update(
                {
                    'delete': {
                        'availability': True
                    }
                }
            )
        if instance.get_available_statuses(request):
            data.update(
                {
                    'change_status': {
                        'availability': True
                    }
                }
            )
        return Response(data)

    @action(methods=('get',), detail=True, url_path='status')
    def get_status(self, request, *args, **kwargs):
        instance = self.get_object()
        available_statuses = instance.get_available_statuses(request)
        qs = models.SportFacilityStatusModel.objects.filter(
            code__in=available_statuses,
            is_active=True,
        ).order_by('sort', 'name')
        data = serializers.SportFacilityStatusSerializer(qs, many=True).data
        return Response(data)

    @action(methods=('put',), detail=True, url_path='update_status')
    def update_status(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        serializer = serializers.SportFacilityUpdateStatusSerializer(instance=instance, data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        async_task(notifications.notify_about_change_status, str(instance.pk), str(instance.status.pk), str(request.user.profile.pk))
        return Response(serializer.data,)

    @action(methods=('post',), detail=True, url_path='request_update')
    def request_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.update_requested = True
        instance.save(update_fields=('update_requested',))
        async_task(notifications.notify_about_request_update, str(instance.pk), str(request.user.profile.pk))
        return Response()

    @action(methods=('put',), detail=False, url_path='delete')
    def delete(self, request, *args, **kwargs):
        try:
            sport_facility = models.SportFacilityInfoModel.objects.get(is_active=True, pk=self.request.data.get('id'))
        except (models.SportFacilityInfoModel.DoesNotExist, ValidationError):
            raise Http404
        if not sport_facility.get_delete_permission(request):
            raise drf_exceptions.PermissionDenied()
        sport_facility.is_active = False
        sport_facility.deleted_at = timezone.now()
        sport_facility.save(update_fields=('is_active', 'deleted_at',))
        return Response('ok')

    # Помещения/строения
    @action(methods=('get',), detail=True, url_path='building/detail')
    def get_building(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        building_id = request.query_params.get('id')
        try:
            building = instance.tp_sport_buildings.get(pk=building_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        serializer = serializers.TPSportBuildingListSerializer(building)
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='building/create')
    def create_building(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = request.data
        data['owner'] = instance.pk
        serializer = serializers.TPSportBuildingWriteSerializer(data=data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        building = serializer.save()
        return Response(serializers.TPSportBuildingListSerializer(building).data)

    @action(methods=('put',), detail=True, url_path='building/update')
    def update_building(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = request.data
        data['owner'] = instance.pk
        building_id = data.get('id')
        if not building_id:
            raise drf_exceptions.ValidationError('id is required')
        try:
            building = instance.tp_sport_buildings.get(pk=building_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        serializer = serializers.TPSportBuildingWriteSerializer(
            instance=building,
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        building = serializer.save()
        return Response(serializers.TPSportBuildingListSerializer(building).data)

    @action(methods=('post',), detail=True, url_path='building/delete')
    def delete_building(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        building_id = request.data.get('id')
        try:
            building = instance.tp_sport_buildings.get(pk=building_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        building.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('get',), detail=True, url_path='get_buildings')
    def retrieve_buildings(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.tp_sport_buildings.all().order_by('-created_at',)
        serializer = serializers.TPSportBuildingListSerializer(qs, many=True, context={'request': request, 'view': self})
        return Response(serializer.data)

    @action(methods=('put',), detail=True, url_path='update_buildings')
    def update_buildings(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.SportFacilityBuildingUpdateSerializer(
            instance=instance,
            data=request.data,
            context={"request": request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # Кружки и секции
    @action(methods=('get',), detail=True, url_path='section/detail')
    def get_section(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        section_id = request.query_params.get('id')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        serializer = serializers.TPSportSectionListSerializer(section)
        return Response(serializer.data)

    # Группы секции
    @action(methods=('get',), detail=True, url_path='section/groups')
    def get_section_groups(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        section_id = request.query_params.get('id')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        sport_group_types = models.SportGroupTypeCatalog.objects.filter(is_active=True).order_by('sort', 'name')
        for each in sport_group_types:
            models.SportSectionGroupsModel.objects.get_or_create(owner=section, sport_group_type=each)
        qs = models.SportSectionGroupsModel.objects.filter(owner=section).order_by('sport_group_type__sort',)
        serializer = serializers.SportSectionGroupsListSerializer(
            qs, many=True, context={'request': request, 'view': self}
        )
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='section/groups/update')
    def update_section_groups(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = request.data
        section_id = data.get('id')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        sport_section_groups = data.get('sport_groups')
        if isinstance(sport_section_groups, list):
            for each in sport_section_groups:
                sport_group_type_id = each.get('sport_group_type')
                if sport_group_type_id:
                    try:
                        sport_section_group, created = models.SportSectionGroupsModel.objects.get_or_create(
                            owner=section,
                            sport_group_type_id=sport_group_type_id,
                        )
                    except IntegrityError:
                        raise drf_exceptions.ValidationError('integrity')
                    serializer = serializers.SportSectionGroupsUpdateSerializer(
                        instance=sport_section_group,
                        data=each,
                        partial=True,
                        context={'request': request, 'view': self}
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                else:
                    raise drf_exceptions.ValidationError('no sport_group_type')
            aggr = models.SportSectionGroupsModel.objects.filter(is_active=True, owner=section).aggregate(
                sections_quantity=Sum('sections_quantity'),
                members_variable_quantity=Sum('members_variable_quantity'),
                members_constant_quantity=Sum('members_constant_quantity'),
            )

            section.sections_quantity = aggr['sections_quantity'] if aggr['sections_quantity'] is not None else 0
            members_variable_quantity = aggr['members_variable_quantity'] if aggr['members_variable_quantity'] is not None else 0
            members_constant_quantity = aggr['members_constant_quantity'] if aggr['members_constant_quantity'] is not None else 0
            section.members_quantity = members_variable_quantity + members_constant_quantity
            section.save(update_fields=('sections_quantity', 'members_quantity', 'coaches_quantity'))
        else:
            raise drf_exceptions.ValidationError('Некорректные данные')
        return Response('ok')

    # Тренеры/преподаватели секции
    @action(methods=('get',), detail=True, url_path='section/coaches')
    def get_section_coaches(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        section_id = request.query_params.get('id')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        sport_coach_types = models.SportCoachTypeCatalog.objects.filter(is_active=True).order_by('sort', 'name')
        for each in sport_coach_types:
            models.SportSectionCoachesModel.objects.get_or_create(owner=section, sport_coach_type=each)
        qs = models.SportSectionCoachesModel.objects.filter(owner=section).order_by('sport_coach_type__sort', )
        serializer = serializers.SportSectionCoachListSerializer(
            qs, many=True, context={'request': request, 'view': self}
        )
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='section/coaches/update')
    def update_section_coaches(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = request.data
        section_id = data.get('id')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        sport_section_coaches = data.get('sport_coaches')
        if isinstance(sport_section_coaches, list):
            for each in sport_section_coaches:
                sport_coach_type_id = each.get('sport_coach_type')
                if sport_coach_type_id:
                    try:
                        sport_section_coach, created = models.SportSectionCoachesModel.objects.get_or_create(
                            owner=section,
                            sport_coach_type_id=sport_coach_type_id,
                        )
                    except IntegrityError:
                        raise drf_exceptions.ValidationError('integrity')
                    serializer = serializers.SportSectionCoachUpdateSerializer(
                        instance=sport_section_coach,
                        data=each,
                        partial=True,
                        context={'request': request, 'view': self}
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                else:
                    raise drf_exceptions.ValidationError('sport_coach_type is required')
            aggr = models.SportSectionCoachesModel.objects.filter(is_active=True, owner=section).aggregate(
                coaches_quantity_sum=Sum('coaches_quantity')
            )

            section.coaches_quantity = aggr['coaches_quantity_sum'] if aggr['coaches_quantity_sum'] is not None else 0
            section.save(update_fields=('coaches_quantity',))
        else:
            raise drf_exceptions.ValidationError('Некорректные данные')
        return Response('ok')

    @action(methods=('post',), detail=True, url_path='section/create')
    def create_section(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = request.data
        data['owner'] = instance.pk
        serializer = serializers.TPSportSectionWriteSerializer(data=data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        building = serializer.save()
        return Response(serializers.TPSportSectionListSerializer(building).data)

    @action(methods=('put',), detail=True, url_path='section/update')
    def update_section(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = request.data
        data['owner'] = instance.pk
        section_id = data.get('id')
        if not section_id:
            raise drf_exceptions.ValidationError('id is required')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        serializer = serializers.TPSportSectionWriteSerializer(
            instance=section,
            data=data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        building = serializer.save()
        return Response(serializers.TPSportSectionListSerializer(building).data)

    @action(methods=('post',), detail=True, url_path='section/delete')
    def delete_section(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        section_id = request.data.get('id')
        try:
            section = instance.tp_sport_sections.get(pk=section_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        section.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('get',), detail=True, url_path='get_sections')
    def retrieve_sections(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.tp_sport_sections.all().order_by('-created_at',)
        serializer = serializers.TPSportSectionListSerializer(qs, many=True, context={'request': request, 'view': self})
        return Response(serializer.data)


class SportFacilityTypeModelViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.SportFacilityTypeModel.objects.filter(is_active=True).order_by('name')

    serializer_class = serializers.SportFacilityTypeModelSerializer

    def get_queryset(self):
        request = self.request
        parent = request.query_params.get('parent', 'root')
        qs = self.queryset.annotate(
            is_leaf=Case(
                When(children__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )
        if parent:
            if parent == 'root':
                qs = qs.filter(parent__isnull=True)
            else:
                try:
                    qs = qs.filter(parent_id=parent)
                except ValidationError:
                    qs = qs.none()
        else:
            qs = qs.none()
        return qs.distinct()


class SportFacilityPurposeModelViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.SportFacilityPurposeModel.objects.filter(is_active=True).order_by('sort', 'name')

    serializer_class = serializers.SportFacilityPurposeModelSerializer

    def get_queryset(self):
        request = self.request
        parent = request.query_params.get('parent', 'root')
        qs = self.queryset
        if parent:
            if parent == 'root':
                qs = qs.filter(parent__isnull=True)
            else:
                try:
                    qs = qs.filter(parent_id=parent)
                except ValidationError:
                    qs = qs.none()
        else:
            qs = qs.none()
        return qs


class SportTypeCategoryViewSet(BaseCatalogViewSet):
    permission_classes = (IsAuthenticated,)
    model = models.SportTypeCategoryModel
    pagination_class = None

    @action(methods=('get',), detail=False, url_path='rebuild_tree')
    def rebuild_tree(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        self.model.objects.rebuild()
        return Response('ok')

    def create(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('post')

    def destroy(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('delete')

    def update(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('put')


class SportTypeViewSet(BaseCatalogViewSet):
    permission_classes = (IsAuthenticated,)
    model = models.SportTypeModel


class SportFacilityRenovationInfoViewSet(BaseModelViewSet):
    permission_classes = (IsAuthenticated,)
    model = models.SportFacilityRenovationInfoModel

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.deleted_at = timezone.now()
        instance.save(update_fields=('is_active', 'deleted_at',))
        return Response(status=status.HTTP_204_NO_CONTENT)


class SportFacilityRenovationTypeViewSet(BaseCatalogViewSet):
    permission_classes = (IsAuthenticated,)
    model = models.SportFacilityRenovationTypeModel

    def create(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('post')

    def update(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('put')

    def partial_update(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('patch')


class SportFacilityRenovationWorkTypeViewSet(BaseCatalogViewSet):
    permission_classes = (IsAuthenticated,)
    model = models.SportFacilityRenovationWorkTypeModel

    def create(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('post')

    def update(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('put')

    def partial_update(self, request, *args, **kwargs):
        raise drf_exceptions.MethodNotAllowed('patch')