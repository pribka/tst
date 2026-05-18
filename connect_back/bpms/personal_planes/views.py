import uuid
import datetime
from tempfile import NamedTemporaryFile, TemporaryDirectory

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http.response import FileResponse

from rest_framework import status, viewsets, exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from bkz3.settings import BASE_DIR

from common.views import BaseModelViewSet, BaseCatalogViewSet
from common.catalogs.serializers import ContractorModelShortSerializer
from common.catalogs.models import ContractorModel
from bpms.tasks.models import TaskExecutionTimeModel
from bpms.tasks.serializers import TaskExecutionTimeModelCreateSerializer
from users.models import ProfileModel
from users.serializers import AppUserSerializer

from . import models, serializers, permissions, utils


class PersonalPlaneViewSet(BaseModelViewSet):
    model = models.PersonalPlaneModel
    permission_classes = (IsAuthenticated, permissions.PersonalPlanePermission,)

    @action(methods=('get',), detail=False, url_path='report/file')
    def get_report_file(self, request, *args, **kwargs):
        file_type = request.query_params.get('file_type', 'xlsx')
        if file_type == 'xlsx':
            wb = utils.get_personal_planes_report(request)
            with NamedTemporaryFile() as tmp_file:
                wb.save(tmp_file.name)
                return FileResponse(
                    open(tmp_file.name, 'rb', ),
                    filename=f'report.xlsx',
                    as_attachment=True,
                )
        else:
            wb = utils.get_personal_planes_report(request)
            with NamedTemporaryFile() as tmp_file:
                wb.save(tmp_file.name)
                with TemporaryDirectory() as tmp_dir:
                    file_name = utils.convert_report_to_pdf(tmp_file, tmp_dir)
                    return FileResponse(
                        open(file_name, 'rb', ),
                        filename=f'report.pdf',
                    )

    @action(methods=('get',), detail=False, url_path='work_plan_show', permission_classes=(IsAuthenticated,))
    def get_work_plan_show(self, request, *args, **kwargs):
        return Response({
            'WorkPlanShow': utils.has_work_plan_access(request),
            'WorkPlanShowV2': utils.has_work_plan_access_v2(request)
        })

    @action(methods=('get',), detail=False, url_path='days', permission_classes=(IsAuthenticated,))
    def get_work_plan_days(self, request, *args, **kwargs):
        from django.db.models import Sum

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({})

        planes = models.PersonalPlaneModel.objects.filter(
            is_active=True,
            author=request.user.profile,
            plane_date__gte=start_date,
            plane_date__lte=end_date
        ).prefetch_related('plane_items')

        result = {}
        for plane in planes:
            total_duration = plane.plane_items.aggregate(
                total=Sum('duration_fact')
            )['total'] or 0

            result[plane.plane_date.strftime('%Y-%m-%d')] = {
                'status': plane.status_id,
                'description': str(total_duration)
            }

        return Response(result)

    @action(methods=('post',), detail=True, url_path='complete')
    def complete(self, request, *args, **kwargs):
        instance = self.get_object()
        plane_date = instance.plane_date
        user = request.user.profile
        if not instance.status_id == 'completed':
            with transaction.atomic():
                complete_status = models.PersonalPlaneStatusModel.objects.get(code='completed')
                instance.status = complete_status
                instance.save(update_fields=('status',))
                items = instance.plane_items.all()
                for item in items:
                    task = item.task
                    if task:
                        utils.validate_task(task, request)
                        serializer = TaskExecutionTimeModelCreateSerializer(
                            data={
                                'task': task.pk,
                                'user': user.pk,
                                'work_type': item.work_type.code if item.work_type else None,
                                'hours': item.duration_fact,
                                'date': plane_date,
                                'description': item.description,
                                'is_result': item.is_result,
                            },
                            context={'request': request}
                        )
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
        else:
            raise drf_exceptions.ValidationError('Рабочий день уже завершен')
        serializer = serializers.MyPersonalPlaneModelSerializer(instance, context={'request': request, 'view': self})
        data = serializer.data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='my/current')
    def get_my_current_plane(self, request, *args, **kwargs):
        user = request.user.profile
        instance = self.model.objects.filter(
            is_active=True,
            author=user,
            status_id='in_work'
        ).order_by('-plane_date').first()
        if not instance:
            plane_date = request.query_params.get('plane_date')
            if plane_date:
                try:
                    instance = self.model.objects.filter(
                        is_active=True,
                        author=user,
                        plane_date=plane_date
                    ).order_by('-plane_date').first()
                except ValidationError:
                    raise drf_exceptions.ValidationError('plane_date')
            else:
                instance = self.model.objects.filter(
                    is_active=True,
                    author=user,
                ).order_by('-plane_date').first()
        if not instance:
            return Response()
        data = serializers.MyPersonalPlaneModelSerializer(instance=instance).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='plan_by_user',)
    def get_plan_by_user(self, request, *args, **kwargs):
        plane_date = request.query_params.get('plane_date')
        user_id = request.query_params.get('user')
        if not (plane_date and user_id):
            return Response()
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            raise drf_exceptions.ValidationError('invalid user id')
        if user_id not in utils.get_access_users(request):
            raise drf_exceptions.PermissionDenied('У вас нет доступа к дейликам этого пользователя')
        try:
            instance = models.PersonalPlaneModel.objects.get(is_active=True, author_id=user_id, plane_date=plane_date)
        except models.PersonalPlaneModel.DoesNotExist:
            raise drf_exceptions.NotFound('Дейлик не найден')
        except ValidationError:
            raise drf_exceptions.ValidationError('Invalid parameters')
        serializer = serializers.MyPersonalPlaneModelSerializer(instance)
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='my/calendar')
    def get_my_calendar(self, request, *args, **kwargs):
        """Дейлик для календаря по дате"""
        plane_date = request.query_params.get('plane_date')
        if not plane_date:
            return Response()
        try:
            instance = models.PersonalPlaneModel.objects.select_related('status',).filter(
                is_active=True,
                author=request.user.profile,
                plane_date=plane_date,
            ).order_by('plane_date',).first()
        except ValidationError:
            raise drf_exceptions.ValidationError('Invalid plane_date')
        if not instance:
            return Response()
        serializer = serializers.MyPersonalPlaneModelSerializer(
            instance,
            context={'request': request, 'view': self}
        )
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='user_plans')
    def get_user_plans(self, request, *args, **kwargs,):
        """Планы в разрезе пользователей."""
        qs = ProfileModel.objects.filter(is_active=True)
        plane_date_gte = request.query_params.get('plane_date_gte')
        plane_date_lte = request.query_params.get('plane_date_lte')
        try:
            plane_date_gte_date = datetime.datetime.strptime(plane_date_gte, "%Y-%m-%d")
            plane_date_lte_date = datetime.datetime.strptime(plane_date_lte, "%Y-%m-%d")
        except ValueError:
            qs = qs.none()
        else:
            delta = plane_date_lte_date - plane_date_gte_date
            if abs(delta.days) > 32:
                qs = qs.none()
            else:
                org_id = request.query_params.get('organization')
                if org_id:
                    try:
                        qs = qs.filter(contractors=org_id)
                    except ValidationError:
                        raise drf_exceptions.ValidationError('Invalid organization id')
                access_users_id = utils.get_access_users(request)
                qs = qs.filter(pk__in=access_users_id).distinct()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.UserPlanListSerializer(page, many=True, context={'request': request, 'view': self})
        data = serializer.data
        return paginator.get_paginated_response(data)


class PersonalPlaneItemViewSet(BaseModelViewSet):
    model = models.PersonalPlaneItemModel
    permissions = (IsAuthenticated, permissions.PersonalPlaneItemPermission,)

    def list(self, request, *args, **kwargs):
        return Response()

    def create(self, request, *args, **kwargs):
        plane_id = request.data.get('plane')
        if not plane_id:
            raise drf_exceptions.ValidationError('plane is required.')
        try:
            plane = models.PersonalPlaneModel.objects.get(is_active=True, pk=plane_id)
        except (ValidationError, models.PersonalPlaneModel.DoesNotExist):
            raise drf_exceptions.ValidationError(f'plane {plane_id} not found')
        if not plane.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PersonalPlaneAccessViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        owner = request.user.profile
        request_data = request.data
        users_id = request_data.get('users')
        orgs_id = request_data.get('organizations')

        with transaction.atomic():
            owner.personal_plane_access_profiles.all().delete()
            user_access_list = []
            for each in users_id:
                user_access = models.PersonalPlaneAccessProfileModel()
                user_access.owner = owner
                user_access.user_id = each
                user_access_list.append(user_access)
            try:
                models.PersonalPlaneAccessProfileModel.objects.bulk_create(user_access_list)
            except ValidationError:
                raise drf_exceptions.ValidationError('Invalid users')
            org_access_list = []
            owner.personal_plane_access_org.all().delete()
            for each in orgs_id:
                org_access = models.PersonalPlaneAccessOrganizationModel()
                org_access.owner = owner
                org_access.organization_id = each
                org_access_list.append(org_access)
            try:
                models.PersonalPlaneAccessOrganizationModel.objects.bulk_create(org_access_list)
            except ValidationError:
                raise drf_exceptions.ValidationError('Invalid organizations')
            metadata_obj, created = models.PersonalPlanAccessProfileMetadataModel.objects.get_or_create(
                user=request.user.profile,
            )
            serializer = serializers.PersonalPlanAccessProfileMetadataModelSerializer(
                metadata_obj, data=request_data, context={'request': request, 'view': self}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        data = {
            'users': [],
            'organizations': [],
        }
        user = request.user.profile
        users_id = user.personal_plane_access_profiles.all().values_list('user', flat=True)
        users = ProfileModel.objects.filter(pk__in=users_id)
        context = {'request': request, 'view': self}
        if users:
            serializer = AppUserSerializer(users, many=True, context=context)
            data['users'] = serializer.data
        orgs_id = user.personal_plane_access_org.all().values_list('organization', flat=True)
        orgs = ContractorModel.objects.filter(pk__in=orgs_id)
        if orgs:
            serializer = ContractorModelShortSerializer(orgs, many=True, context=context)
            data['organizations'] = serializer.data

        metadata_obj, created = models.PersonalPlanAccessProfileMetadataModel.objects.get_or_create(
            user=user,
        )
        metadata = serializers.PersonalPlanAccessProfileMetadataModelSerializer(
            metadata_obj, context={'request': request, 'view': self}
        ).data
        data['metadata'] = metadata['metadata']
        return Response(data)
