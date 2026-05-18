import datetime

from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator

from common.catalogs import models as catalog_models

from contractor_permissions import models as contractor_permission_models

from users.utils import get_descendants_departments_related_organizations

from billing import models as billing_models


class Command(BaseCommand):
    help = "Management contractor_permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            '--init_access_groups',
            action='store_true',
            help='initialize access groups.',
        )

    def handle(self, *args, **options):
        if options['init_access_groups']:
            # Получаем корневые организации
            root_contractors_id = catalog_models.ContractorRelationModel.objects.all().values_list(
                'contractor_root',
                flat=True
            ).distinct().order_by('contractor_root',)
            # Добавляем корневым организациям тариф по умолчанию
            try:
                default_tariff = billing_models.TariffModel.objects.get(
                    code='default',
                )
            except ObjectDoesNotExist:
                return 'ERROR! Ошибка! Отсутствует тариф по умолчанию!!!'
            tariff_access_groups = default_tariff.access_groups.all()
            try:
                ag_consolidation_admin = tariff_access_groups.get(code='consolidation_admin')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Админ консолидации!!!'
            try:
                ag_consolidation_worker = tariff_access_groups.get(code='consolidation_worker')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Сотрудник консолидации!!!'
            try:
                ag_sport_facility_admin = tariff_access_groups.get(code='sport_facility_admin')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Админ спортивных объектов!!!'
            try:
                ag_sport_facility_worker = tariff_access_groups.get(code='sport_facility_worker')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Сотрудник спортивных объектов!!!'
            try:
                ag_workgroup_admin = tariff_access_groups.get(code='workgroup_admin')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Админ рабочих групп и проектов!!!'
            try:
                ag_workgroup_worker = tariff_access_groups.get(code='workgroup_worker')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Сотрудник рабочих групп и проектов!!!'
            try:
                ag_structure_admin = tariff_access_groups.get(code='admin')
            except ObjectDoesNotExist:
                return 'Отсутствует группа доступа Администратор!'
            date_start = timezone.now()
            date_end = date_start + datetime.timedelta(weeks=5000)
            for root_contractor_id in root_contractors_id:
                obj, created = billing_models.ContractorTariffModel.objects.get_or_create(
                    contractor_id=root_contractor_id,
                    tariff=default_tariff,
                    defaults={
                        'date_start': date_start,
                        'date_end': date_end
                    }
                )
                if created:
                    print(f"Default tariff for {root_contractor_id} initialized")
                else:
                    print(f"Default tariff for {root_contractor_id} has been created")

                contractors_id = get_descendants_departments_related_organizations(
                    (root_contractor_id,),
                    include_self=True
                )
                for contractor_id in contractors_id:
                    contractor_profiles = catalog_models.ContractorProfileModel.objects.filter(
                        contractor_id=contractor_id,
                    )
                    for contractor_profile in contractor_profiles:
                        permission_types = set(contractor_permission_models.ContractorPermissionModel.objects.filter(
                            contractor_permission_role__contractor_profiles=contractor_profile,
                            contractor_permission_role__contractor_id=contractor_id,
                            contractor_permission_role__is_active=True,
                            permission_type_id__in=(
                                'create_consolidation',
                                'send_report',
                                'admin_sport_facility',
                                'create_sport_facility',
                                'create_workgroup',
                                'admin',
                            )
                        ).values_list('permission_type', flat=True))
                        if permission_types:
                            if 'create_consolidation' in permission_types:
                                ag_consolidation_admin.members.add(contractor_profile)
                            if 'send_report' in permission_types and 'create_consolidation' not in permission_types:
                                ag_consolidation_worker.members.add(contractor_profile)
                            if 'admin_sport_facility' in permission_types:
                                ag_sport_facility_admin.members.add(contractor_profile)
                            if 'create_sport_facility' in permission_types and 'admin_sport_facility' not in permission_types:
                                ag_sport_facility_worker.members.add(contractor_profile)
                            if 'create_workgroup' in permission_types:
                                ag_workgroup_admin.members.add(contractor_profile)
                            if 'admin' in permission_types:
                                ag_structure_admin.members.add(contractor_profile)
                        else:
                            ag_workgroup_worker.members.add(contractor_profile)
            return 'ok'
