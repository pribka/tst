import uuid

from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.http.response import FileResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_q.tasks import async_task, result
from rest_framework import exceptions as drf_exceptions
from rest_framework import generics
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounting_reports.models import AccountingReportTypeModel
from common.catalogs.models import ContractorModel, ContractorRelationModel
from common.models import File
from common.serializers import AppFileSerializer
from common.views import BaseCatalogViewSet
from common.utils import use_access_groups
from contractor_permissions.models import ContractorPermissionModel
from contractor_permissions.utils import check_contractor_permission, contractors_where_user_has_permission

from users.serializers import AppOrganizationSerializer

from . import (generating, models, notifications, permissions, serializers,
               utils)


class ReportFormModelViewSet(BaseCatalogViewSet):
    model = models.ReportFormModel

    def get_queryset(self):
        org_administrator = self.request.query_params.get('org_administrator', None)
        user = self.request.user.profile
        all_report_forms = self.model.objects.filter(
            is_active=True
        ).values_list('id', flat=True)
        if use_access_groups(user.pk):
            report_form_ids = all_report_forms
        else:
            report_form_ids = ContractorPermissionModel.objects.filter(
                    contractor_permission_role__contractor=org_administrator,
                    contractor_permission_role__is_active=True,
                    contractor_permission_role__contractor_profiles__user=user,
                    permission_type_id='create_consolidation',
                ).values_list('aux_conditions', flat=True)
            if None in report_form_ids:
                report_form_ids = all_report_forms
        return self.model.objects.filter(
            is_active=True,
            id__in=report_form_ids
        )


class GetOrgAdministratorsViewSet(generics.ListAPIView):
    serializer_class = AppOrganizationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user.profile
        permissioned_contractor_ids = contractors_where_user_has_permission(user.pk, 'create_consolidation', None)
        return ContractorModel.objects.filter(id__in=permissioned_contractor_ids)


class ReportModelViewSet(BaseCatalogViewSet):
    model = models.ReportModel

    @action(methods=('get',),
            detail=True,
            url_path='file_view',
            permission_classes=(
                IsAuthenticated,
                permissions.ReportFileViewPermission),)
    def file_view(self, request, *args, **kwargs):
        instance = self.get_object()
        data = serializers.ReportModelDetailSerializer(
            instance,
            context={'request': request}
        ).data
        return Response(data)

    @action(methods=('get',),
            detail=True,
            url_path='action_info',
            permission_classes=(IsAuthenticated,))
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        actions = dict()
        parent = instance.parent

        if instance.get_detail_permission(request):
            actions['open'] = {'availability': True}

        if not parent.auto_approve and parent.get_update_permission(request):
            actions['approve'] = {'availability': True}
            actions['reject'] = {'availability': True}

        return Response({'actions': actions})

    @action(methods=('post',), detail=True, url_path='generate', permission_classes=(IsAuthenticated,))
    def generate_report(self, request, *args, **kwargs):
        report = self.get_object()
        file_code = request.data.get('file_code', '')
        no_inquiries = request.data.get('no_inquiries', False)
        if not report.get_detail_permission(request):
            raise drf_exceptions.ValidationError('Вносить изменения в отчет запрещено.')
        report_file, risk_assessments_count = generating.generate_report(report, file_code, no_inquiries)
        data = AppFileSerializer(report_file).data
        data['extra_info'] = dict()
        data['extra_info']['risk_assessments_count'] = risk_assessments_count
        return Response(data)

    @action(methods=('post',),
            detail=True,
            url_path='approve',
            permission_classes=(IsAuthenticated,))
    def approve(self, request, *args, **kwargs):
        instance = self.get_object()
        consolidation = instance.parent
        report_form_instance = consolidation.get_report_form_instance()
        if not consolidation.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'У вас недостаточно прав для выполнения данного действия'
            )
        with transaction.atomic():
            report_form_instance.before_approve(instance)
            instance.status_id = 'approved'
            instance.save(update_fields=('status_id',))
            if consolidation.all_reports_is_approved():
                consolidation.status_id = 'ready_to_consolidate'
                consolidation.save(update_fields=('status_id', ))
            report_form_instance.report_approved(instance)
        report_s_data = serializers.ReportModelDetailSerializer(
            instance=instance,
            context={'request': request}
        ).data
        consolidation_s_data = serializers.ConsolidationModelDetailSerializer(
            instance=consolidation,
            context={'request': request}
        ).data
        async_task(
            notifications.notify_report_is_approved,
            str(instance.id),
            str(request.user.profile.id)
        )
        return Response({
            'report': report_s_data,
            'consolidation': consolidation_s_data,
        })

    @action(methods=('post',),
            detail=True,
            url_path='reject',
            permission_classes=(IsAuthenticated,))
    def reject(self, request, *args, **kwargs):
        instance = self.get_object()
        consolidation = instance.parent
        report_form_instance = consolidation.get_report_form_instance()
        if not consolidation.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'У вас недостаточно прав для выполнения данного действия'
            )

        with transaction.atomic():
            instance.status_id = 'rejected'
            instance.save(update_fields=('status_id',))
            consolidation.status_id = 'in_progress'
            consolidation.save(update_fields=('status_id', ))
            report_form_instance.report_rejected(instance)
            async_task(
                notifications.notify_report_is_rejected,
                str(instance.id),
                str(request.user.profile.id)
            )
        report_s_data = serializers.ReportModelDetailSerializer(
            instance=instance,
            context={'request': request}
        ).data
        consolidation_s_data = serializers.ConsolidationModelDetailSerializer(
            instance=consolidation,
            context={'request': request}
        ).data
        return Response({
            'report': report_s_data,
            'consolidation': consolidation_s_data,
        })

    @action(methods=('post',),
            detail=True,
            url_path='file_remove',
            permission_classes=(IsAuthenticated,))
    def file_remove(self, request, *args, **kwargs):
        instance = self.get_object()
        file_id = request.data.get('file', None)
        consolidation = instance.parent
        if not instance.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'Вносить изменения запрещено.'
            )
        try:
            report_file = models.ReportFileModel.objects.get(
                is_active=True,
                id=file_id
            )
        except models.ReportFileModel.DoesNotExist:
            raise drf_exceptions.ValidationError(
                'Файл отчета не найден.'
            )
        if report_file not in instance.report_files.all():
            raise drf_exceptions.ValidationError(
                'Этого файла нет в отчете.'
            )
        if report_file.original_file is None:
            raise Http404

        with transaction.atomic():
            if report_file.original_file:
                report_file.original_file.is_orphaned = True
                report_file.original_file.save(update_fields=('is_orphaned', ))
            if report_file.pdf_file:
                report_file.pdf_file.is_orphaned = True
                report_file.pdf_file.save(update_fields=('is_orphaned', ))
            report_file.is_generated = False
            report_file.original_file = None
            report_file.pdf_file = None
            report_file.upload_date = None
            report_file.uploaded_by = None
            report_file.save(update_fields=(
                'is_generated',
                'original_file',
                'pdf_file',
                'upload_date',
                'uploaded_by',
            ))

            if instance.report_files.filter(
                original_file__isnull=False
            ).exists():
                instance.status_id = 'on_review'
            else:
                instance.status_id = 'not_loaded'
            instance.save(update_fields=(
                'status_id',
            ))
            if report_file.file_type_id == 'risk_matrix':
                instance.no_inquiries = False
                instance.save(update_fields=(
                    'no_inquiries',
                ))
            consolidation.status_id = 'in_progress'
            consolidation.save(update_fields=('status_id', ))
        report_s_data = serializers.ReportModelDetailSerializer(
            instance=instance,
            context={'request': request}
        ).data
        consolidation_s_data = serializers.ConsolidationModelDetailSerializer(
            instance=consolidation,
            context={'request': request}
        ).data
        return Response({
            'report': report_s_data,
            'consolidation': consolidation_s_data,
        })


class ConsolidationModelViewSet(BaseCatalogViewSet):
    model = models.ConsolidationModel
    permission_classes = (IsAuthenticated, permissions.ConsolidationPermission)

    def list(self, request, *args, **kwargs):
        is_scheduled = request.query_params.get('is_scheduled') == 'true'
        queryset = self.model.get_queryset(request)

        qs = queryset.filter(is_scheduled=is_scheduled)
        qs = self.filter_queryset(qs)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(methods=('get',),
            detail=True,
            url_path='file_view',
            permission_classes=(
                IsAuthenticated,
                permissions.ConsolidationFileViewPermission),)
    def file_view(self, request, *args, **kwargs):
        instance = self.get_object()
        data = serializers.ConsolidationModelDetailSerializer(instance).data
        return Response(data)

    @action(methods=('post',),
            detail=True,
            url_path='send_documents',
            permission_classes=(
                IsAuthenticated,
            ))
    def send_documents(self, request, *args, **kwargs):
        recipients = request.data.get('recipients', None)
        user = request.user.profile
        if not recipients:
            raise drf_exceptions.ValidationError(
                'Список целевых консолидаций пуст.'
            )
        instance = self.get_object()
        organization_id = instance.org_administrator_id
        recipient_reports = list()
        for recipient_id in recipients:
            # Получаем отчет в целевой консолидации
            try:
                report = models.ReportModel.objects.get(
                    is_active=True,
                    parent_id=recipient_id,
                    contractor_id=organization_id
                )
            except models.ReportModel.MultipleObjectsReturned:
                raise drf_exceptions.ValidationError(
                    f'В целевой консолидации более одного отчета для организации {instance.org_administrator.name}.'
                )
            except models.ReportModel.DoesNotExist:
                raise drf_exceptions.ValidationError(
                    'Не удалось найти целевой отчет.'
                )
            # Проверяем права на изменение отчета
            report_parent = report.parent
            permissive_status_list = [
                'new',
                'on_review',
                'rejected',
                'not_loaded']
            if report_parent.auto_approve:
                permissive_status_list.append('approved')
            if report.status.code not in permissive_status_list:
                raise drf_exceptions.ValidationError(
                    'Консолидация целевого сводного отчета завершена или '
                    'находится в статусе «Подготовлена». Вносить изменения '
                    'и отправлять отчеты в текущем статусе запрещено.'
                )

            if use_access_groups(user.pk):
                try:
                    check_contractor_permission(user.pk, report.contractor_id, 'send_report', None)
                except drf_exceptions.PermissionDenied():
                    user_have_permission_to_send_document = False
                else:
                    user_have_permission_to_send_document = True
            else:
                user_have_permission_to_send_document = ContractorPermissionModel.objects.filter(
                    Q(aux_conditions=report_parent.report_form) | Q(
                        aux_conditions__isnull=True),
                    is_active=True,
                    contractor_permission_role__is_active=True,
                    permission_type_id='send_report',
                    contractor_permission_role__contractor_profiles__user=user,
                    contractor_permission_role__contractor_id=report.contractor
                ).exists()
            if not user_have_permission_to_send_document:
                raise drf_exceptions.ValidationError(
                    'Недостаточно прав для отправки итогового отчета.'
                )
            recipient_reports.append((report, report_parent.auto_approve))
        status = (http_status.HTTP_200_OK if utils.send_documents(
                    instance,
                    recipient_reports,
                    user
                ) else http_status.HTTP_400_BAD_REQUEST)

        return Response(status=status)

    @action(methods=('get',),
            detail=True,
            url_path='get_recipients',
            permission_classes=(
                IsAuthenticated,
            ))
    def get_recipients(self, request, *args, **kwargs):
        instance = self.get_object()
        start = instance.start
        end = instance.end
        report_form = instance.report_form_id
        instance_org = instance.org_administrator_id
        user = request.user.profile

        # Список id организаций в которых у текущего пользователя есть право
        # загружать отчеты по данной форме отчетности (или по всем формам)
        if use_access_groups(user.pk):
            org_ids = contractors_where_user_has_permission(
                user.pk,
                'send_report',
                None
            )
        else:
            org_ids = ContractorPermissionModel.objects.filter(
                    Q(aux_conditions=report_form) | Q(aux_conditions=None),
                    contractor_permission_role__is_active=True,
                    contractor_permission_role__contractor_profiles__user=user,
                    permission_type_id='send_report'
                ).values_list(
                    'contractor_permission_role__contractor_id',
                    flat=True
                )
        # Если список org_ids не пуст выбираем консолидации по условиям:
        # - статус 'new', 'in_progress' или 'ready_to_consolidate'
        # - организации из списка org_ids есть в списке участников
        # - в консолидации есть отчет для организации instance
        # - форма отчетности такая же как у instance
        # - start и end совпадают с периодом у instance
        # - консолидация не является периодической задачей (т.е. шаблоном)
        # Исключим из полученной выборки консолидации созданные в организации instance
        if org_ids:
            queryset = models.ConsolidationModel.objects.filter(
                is_active=True,
                status_id__in=['new', 'in_progress', 'ready_to_consolidate'],
                members__in=org_ids,
                source_reports__contractor=instance_org,
                report_form_id=report_form,
                start=start,
                end=end,
                is_scheduled=False
            ).exclude(
                org_administrator=instance_org
            ).order_by(
                '-created_at'
            ).distinct()
        else:
            queryset = models.ConsolidationModel.objects.none()

        data = serializers.ConsolidationModelRecipientListSerializer(
            queryset,
            many=True
        ).data

        return Response(data)

    @action(methods=('get',),
            detail=True,
            url_path='action_info',
            permission_classes=(IsAuthenticated,))
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        actions = dict()

        if instance.get_detail_permission(request):
            actions['open'] = {'availability': True}

        if instance.get_update_permission(request):
            if instance.status.code in ('new', 'in_progress', 'ready_to_consolidate'):
                actions['edit'] = {'availability': True}
                actions['delete'] = {'availability': True}
            if instance.is_scheduled:
                del actions['edit']
            # if instance.consolidation_file:
            #     actions['download'] = {'availability': True}

        return Response({'actions': actions})

    @action(methods=('put',),
            detail=True,
            url_path='set_template_status',
            permission_classes=(IsAuthenticated,))
    def set_template_status(self, request, *args, **kwargs):
        value = request.data.get('is_template_on', None)
        if value is None:
            raise drf_exceptions.ValidationError(
                {'message': 'Неизвестное состояние шаблона'}
            )
        if not type(value) is bool:
            raise drf_exceptions.ValidationError(
                {'message': 'Неверный тип данных'}
            )
        instance = self.get_object()
        if not instance.is_scheduled:
            raise drf_exceptions.PermissionDenied(
                {'message': 'Консолидация не является шаблоном'}
            )
        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied(
                {'message': 'У вас нет права на изменение шаблона'}
            )
        instance.is_template_on = value
        instance.save(update_fields=('is_template_on',))
        return Response({'message': 'Шаблон успешно активирован' if value else 'Шаблон деактивирован'})

    @action(methods=('post',),
            detail=True,
            url_path='delete',
            permission_classes=(IsAuthenticated,))
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.get_delete_permission(request):
            raise drf_exceptions.ValidationError(
                'Эту консолидацию удалить нельзя.'
            )

        reports = instance.source_reports.all()
        with transaction.atomic():
            instance.is_active = False
            instance.save(update_fields=('is_active',))
            if reports:
                for report in reports:
                    report.is_active = False
                    report.save(update_fields=('is_active', ))
                    report_files = report.report_files.all()
                    if report_files:
                        for file in report_files:
                            if file.original_file:
                                file.original_file.is_orphaned = True
                                file.original_file.save(update_fields=('is_orphaned',))
                            if file.pdf_file:
                                file.pdf_file.is_orphaned = True
                                file.pdf_file.save(update_fields=('is_orphaned',))

        return Response(status=http_status.HTTP_204_NO_CONTENT)

    @action(methods=('get',),
            detail=True,
            url_path='report_validation',
            permission_classes=(IsAuthenticated,))
    def report_validation(self, request, *args, **kwargs):
        consolidation = self.get_object()
        file = request.GET.get('file', None)
        code = request.GET.get('code', None)
        if not file or not consolidation:
            raise drf_exceptions.PermissionDenied(
                'Не переданы данные для проверки.'
            )

        validate = utils.report_file_validation(file, consolidation, code)
        return Response({'validate': validate})

    @action(methods=('post',),
            detail=True,
            url_path='report',
            permission_classes=(IsAuthenticated,))
    def report(self, request, *args, **kwargs):
        contractor_id = request.data.get('contractor', None)
        if contractor_id is None:
            raise drf_exceptions.ValidationError('Не указана организация.')

        try:
            contractor = ContractorModel.objects.get(
                is_active=True,
                id=contractor_id
            )
        except ContractorModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Не удалось найти организацию.')

        instance = self.get_object()

        try:
            report = models.ReportModel.objects.get(
                is_active=True,
                parent=instance,
                contractor=contractor
            )
        except models.ReportModel.DoesNotExist:
            raise drf_exceptions.ValidationError('Не удалось найти отчет.')

        if not report.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'Вносить изменения в отчет запрещено.'
            )

        is_disabled, message = report.get_update_is_disabled()
        if is_disabled:
            raise drf_exceptions.ValidationError(message)

        instance.report_form.report_form_instance().upload_report(instance, report, request)

        if instance.all_reports_is_approved():
            instance.status_id = 'ready_to_consolidate'
            instance.save(update_fields=('status_id', ))

        report_s_data = serializers.ReportModelDetailSerializer(
            instance=report,
            context={'request': request}
        ).data
        consolidation_s_data = serializers.ConsolidationModelDetailSerializer(
            instance=instance,
            context={'request': request}
        ).data
        return Response({
            'report': report_s_data,
            'consolidation': consolidation_s_data,
        }, status=http_status.HTTP_200_OK)

    @action(methods=('post',),
            detail=True,
            url_path='consolidate',
            permission_classes=(IsAuthenticated,))
    def consolidate(self, request, *args, **kwargs):
        consolidation = self.get_object()
        if not consolidation.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'У вас недостаточно прав для выполнения данного действия'
            )
        user = request.user.profile
        reports = consolidation.source_reports.filter(
            is_active=True
        )

        reports_is_valid = utils.consolidation_is_available(
            reports,
            consolidation
        )
        if len(reports) == 0 or not reports_is_valid:
            raise drf_exceptions.ValidationError(
                'Предоставлены некорректные данные'
            )

        with transaction.atomic():
            # Перекрестная проверка всех файлов в отчетах перед консолидацией
            utils.all_reports_validate(consolidation)

            # Создание файла консолидированного отчета
            files = utils.create_consolidated_reports(consolidation)

            # Проверка файла консолидированного отчета после консолидации
            if files:
                utils.consolidation_validate(consolidation)

            if consolidation.consolidation_files.exists():
                c_files = consolidation.consolidation_files.all()
                for file in c_files:
                    if file.original_file:
                        file.original_file.is_orphaned = True
                        file.original_file.save(
                            update_fields=('is_orphaned', )
                        )
                    if file.pdf_file:
                        file.pdf_file.is_orphaned = True
                        file.pdf_file.save(
                            update_fields=('is_orphaned', )
                        )

            consolidation.consolidation_files.set(files)
            consolidation.consolidated_at = timezone.now()
            consolidation.consolidator = user
            consolidation.status_id = 'completed'
            consolidation.save(
                update_fields=(
                    'consolidated_at',
                    'consolidator',
                    'status_id',
                )
            )
            for report in reports:
                report.status_id = 'consolidated'
                report.save(update_fields=('status_id', ))

            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_consolidation_is_complete,
                    str(consolidation.id),
                    str(user.id)
                )
            )

        s_data = serializers.ConsolidationModelDetailSerializer(
            instance=consolidation,
            context={'request': request}
        ).data

        return Response({
            'data': s_data,
            'status': 200
        }, status=http_status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='rollback', permission_classes=(IsAuthenticated,),)
    def rollback(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.get_update_permission(request):
            raise drf_exceptions.PermissionDenied({'message': 'У вас нет права на отзыв консолидации'})
        if not instance.status_id == 'completed':
            raise drf_exceptions.ValidationError({'message': 'Консолидация не имеет статус "Завершена"'})
        instance = utils.rollback_consolidation(instance)
        data = serializers.ConsolidationModelDetailSerializer(instance, context={'request': request}).data
        return Response(data)

    @action(methods=('get',), detail=False, url_path="(?P<pk>[^/.]+)/analytics",
            permission_classes=(IsAuthenticated,))
    def get_analytics(self, request, *args, **kwargs):
        analytic_report = request.query_params.get('analytic_report')
        if not analytic_report:
            return Response(status=http_status.HTTP_400_BAD_REQUEST)
        try:
            analytic_report = models.AnalyticReportModel.objects.get(
                is_active=True,
                id=analytic_report
            )
        except models.AnalyticReportModel.DoesNotExist:
            return Response(
                'Форма аналитического отчета не найдена',
                status=http_status.HTTP_404_NOT_FOUND
            )
        pk = self.kwargs.get('pk')
        user = self.request.user.profile
        try:
            organization = ContractorModel.objects.get(
                is_active=True,
                pk=pk,
                pk__in=user.my_organizations
            )
        except ContractorModel.DoesNotExist:
            return Response(
                'Организация не найдена',
                status=http_status.HTTP_404_NOT_FOUND
            )
        display = request.query_params.get('display', 'org_administrator_only')
        if display == 'org_administrator_only':
            organizations = [pk,]
        elif display == 'descendants':
            qs = ContractorRelationModel.objects.filter(
                is_active=True,
                contractor_parent=organization
            )
            organizations = [str(item.contractor_id) for item in qs]
        elif display == 'all':
            qs = ContractorRelationModel.objects.filter(
                is_active=True,
                contractor_parent=organization
            )
            organizations = [str(item.contractor_id) for item in qs]
            organizations.append(pk)
        else:
            try:
                org_id = uuid.UUID(display)
            except ValueError:
                organizations = []
            else:
                organizations = [str(org_id),]

        get_analytic_function, data = analytic_report.get_report_info()
        if not get_analytic_function:
            return Response(
                'Невозможно сформировать аналитический отчет',
                status=http_status.HTTP_404_NOT_FOUND)
        try:
            result = get_analytic_function(organizations, request, data)
        except Exception:
            return Response(
                'Ошибка получения аналитического отчета',
                status=http_status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                result,
                status=http_status.HTTP_200_OK
            )


# class AnalyticsViewSet(APIView):
#     permission_classes = (IsAuthenticated,)

#     def get(self, request, *args, **kwargs):
#         analytic_report = request.query_params.get('analytic_report')
#         org_administartor = request.query_params.get('org_administartor')
#         organization = request.query_params.get('organizations')
#         # display = request.query_params.get('display')
#         organizations = utils.get_organizations(org_administartor, organization)
#         if not analytic_report:
#             return Response(status=http_status.HTTP_400_BAD_REQUEST)
#         try:
#             analytic_report = models.AnalyticReportModel.objects.get(
#                 is_active=True,
#                 id=analytic_report
#             )
#         except models.AnalyticReportModel.DoesNotExist:
#             return Response(
#                 'Форма аналитического отчета не найдена',
#                 status=http_status.HTTP_404_NOT_FOUND
#             )
#         get_analytic_function, data = analytic_report.get_report_info()
#         if not get_analytic_function:
#             return Response(
#                 'Невозможно сформировать аналитический отчет',
#                 status=http_status.HTTP_404_NOT_FOUND)
#         try:
#             result = get_analytic_function(request, data)
#         except Exception:
#             return Response(
#                 'Ошибка получения аналитического отчет',
#                 status=http_status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response(
#                 result,
#                 status=http_status.HTTP_200_OK
#             )


class AnalyticReportModelView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        report_form = request.query_params.get('report_form')
        if not report_form:
            return Response(status=http_status.HTTP_400_BAD_REQUEST)
        queryset = models.AnalyticReportModel.objects.filter(
            is_active=True,
            report_form=report_form
        )
        data = serializers.AnalyticReportModelSerializer(queryset, many=True).data
        return Response(data, status=http_status.HTTP_200_OK)

    # @action(methods=('post',),
    #         detail=True,
    #         url_path='file_remove',
    #         permission_classes=(IsAuthenticated,))
    # def file_remove(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     if not instance.get_update_permission(request):
    #         raise drf_exceptions.ValidationError(
    #             'Нельзя удалить файл отчета.'
    #         )

    #     instance.consolidation_file.is_orphaned = True
    #     instance.consolidation_file.save(update_fields=('is_orphaned', ))
    #     instance.consolidation_file = None
    #     instance.pdf_consolidation_file.is_orphaned = True
    #     instance.pdf_consolidation_file.save(update_fields=('is_orphaned', ))
    #     instance.pdf_consolidation_file = None
    #     instance.consolidated_at = None
    #     instance.status_id = 'ready_to_consolidate'
    #     instance.save(
    #         update_fields=(
    #             'consolidated_at',
    #             'consolidation_file',
    #             'pdf_consolidation_file',
    #             'status_id'
    #         )
    #     )
    #     s_data = serializers.ConsolidationModelDetailSerializer(
    #         instance=instance,
    #         context={'request': request}
    #     ).data
    #     return Response(s_data)


@csrf_exempt
def kijlr3awx8_update_saved_reports(request):
    if not (request.method == 'POST' and request.POST.get('update') == 'true'):
        return HttpResponse('not_ok')
    async_task(utils.update_saved_reports)
    return HttpResponse('The task began')


class GetPDFView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        file_id = self.kwargs.get('file_id', None)
        try:
            source_file = File.objects.get(
                is_active=True,
                id=file_id
            )
        except File.DoesNotExist:
            raise Http404
        else:
            return FileResponse(
                utils.get_pdf(source_file),
                content_type='application/pdf'
            )
