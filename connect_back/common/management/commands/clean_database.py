import logging
from contextlib import contextmanager
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_delete, post_init
from django.db.utils import Error

from bpms.chat.models import ChatModel
from bpms.tasks.models import TaskModel
from bpms.tasks.utils import create_temp_bases
from bpms.workgroups.models import WorkgroupModel, WorkgroupMembersModel
from common.catalogs.models import (
    ContractorDepartmentModel,
    ContractorModel,
    ContractorMemberModel,
    ContractorProfileModel,
    ContractorRelationModel
)
from common.models import (
    BaseModel,
    FolderModel,
    FileBaseModel,
    File,
    CKEditorFileModel,
    FiltersStore
)
from consolidation.models import (
    ConsolidationModel,
    ConsolidationFileModel,
    ReportPersonalReceptionModel,
    ContractorBalanceModel,
    ReportModel,
    F2GOReportModel,
    ReportFileModel
)
from content_item_gos24.models import (
    ContentItem,
    OfficialClarificationOrgan,
    Partition,
    Tag
)
from contractor_permissions.models import (
    ContractorPermissionModel,
    ContractorPermissionRoleModel,
    AccessGroupMemberThroughModel
)
from bpms.event_calendar.models import (
    CalendarModel,
    CalendarCustomSetModel,
    EventCalendarAccessProfileMetadataModel,
    EventCalendarModel
)
from gallery.models import GalleryModel
from invest_projects_info.models import InvestProjectInfoModel
from bpms.meetings.models import (
    MeetingRecordsModel,
    PlannedMeetingModel,
    MeetingSectionModel,
    MeetingMemberModel
)
from notifications.models import (
    WebNotificationModel,
    EmailNotificationModel
)
from risk_assessment.models import (
    PersonalReceptionModel,
    IssueModel,
    RiskAssessmentModel
)
# from bpms.favorites.models import FavoritesModel
from sports_facilities_info.models import (
    SportFacilityRenovationInfoModel,
    SportFacilityInfoModel
)
from bpms.tasks.models import (
    TaskExecutionTimeModel,
    TaskSprintHistoryModel,
    TaskSprintModel,
    SprintExpectedResultModel
)
from users.models import CustomUser, ProfileModel
from bpms.widgets.models import (
    UserDesktopModel,
    UserWidgetOnDesktopModel
)
from bpms.workload.models import (
    WorkLoadModel,
    WorkScheduleModel
)


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.logger = None

    def _setup_logger(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'clean_database_{timestamp}.log'

        self.logger = logging.getLogger('clean_database')
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.stdout.write(self.style.NOTICE(f'Лог-файл создан: {log_filename}'))

    def _clean_users_and_profiles(self):
        """Специальная обработка для удаления пользователей и их профилей"""
        users_to_delete = CustomUser.objects.filter(
            is_superuser=False
        ).exclude(
            email__in=['akhrenennyy.nik@mail.ru', 'sevenakaoxxy@gmail.com']
        )
        total_users = users_to_delete.count()
        deleted_users = 0
        deleted_profiles = 0
        batch_size = 299

        self.stdout.write(self.style.NOTICE(
            f"Удаление пользователей и профилей. Пользователей к удалению - {total_users}."
        ))

        self.logger.info(f"Найдено {total_users} пользователей для удаления (исключая суперпользователей)")

        while users_to_delete.exists():
            batch = users_to_delete[:batch_size]
            batch_ids = list(batch.values_list('id', flat=True))

            try:
                batch_queryset = CustomUser.objects.filter(id__in=batch_ids)
                deleted_count, details = batch_queryset.delete()
                deleted_users += deleted_count
                deleted_profiles += details.get('users.ProfileModel', 0)

                self.stdout.write(f"Удалено {deleted_count} пользователей, всего: {deleted_users}/{total_users}")

            except Error as e:
                self.logger.error(f"Ошибка при удалении батча пользователей: {e}")
                break

        self.logger.info(f"Успешно удалено {deleted_users} пользователей и {deleted_profiles} профилей")

    def _clean(self, model):
        ct = ContentType.objects.get_for_model(model)
        obj_to_delete = BaseModel.objects.filter(ct=ct)

        total_count = obj_to_delete.count()
        deleted_count = 0

        self.stdout.write(self.style.NOTICE(
            f"Модель {model._meta.label}. Объектов к удалению - {total_count}."
        ))

        self.logger.info(f"Модель {model._meta.label}: найдено {total_count} объектов для удаления")

        if model == ChatModel:
            batch_size = 1
        else:
            batch_size = 299

        while obj_to_delete.exists():
            batch = obj_to_delete[:batch_size]
            batch_ids = list(batch.values_list('id', flat=True))

            try:
                batch_queryset = BaseModel.objects.filter(ct=ct, id__in=batch_ids)
                batch_deleted, _ = batch_queryset.delete()
                deleted_count += batch_deleted

                if total_count > 1000:
                    self.stdout.write(f"Удалено {batch_deleted} объектов {model._meta.label}, всего: {deleted_count}/{total_count}")

            except Error as e:
                self.logger.error(f"Ошибка при удалении батча {model._meta.label}: {e}")
                break

        self.logger.info(f"Модель {model._meta.label}: успешно удалено {deleted_count} из {total_count} объектов")

    def handle(self, *args, **options):

        MODELS_TO_DELETE = [
            WorkLoadModel,
            WorkScheduleModel,
            TaskModel,
            WorkgroupModel,
            ContractorDepartmentModel,
            ContractorModel,
            ContractorMemberModel,
            ContractorProfileModel,
            ContractorRelationModel,
            FolderModel,
            FileBaseModel,
            File,
            CKEditorFileModel,
            FiltersStore,
            ConsolidationModel,
            ConsolidationFileModel,
            ReportPersonalReceptionModel,
            ContractorBalanceModel,
            ReportModel,
            F2GOReportModel,
            ReportFileModel,
            ContentItem,
            OfficialClarificationOrgan,
            Partition,
            Tag,
            ContractorPermissionModel,
            ContractorPermissionRoleModel,
            AccessGroupMemberThroughModel,
            CalendarModel,
            CalendarCustomSetModel,
            EventCalendarAccessProfileMetadataModel,
            EventCalendarModel,
            GalleryModel,
            InvestProjectInfoModel,
            MeetingRecordsModel,
            PlannedMeetingModel,
            MeetingSectionModel,
            MeetingMemberModel,
            WebNotificationModel,
            EmailNotificationModel,
            PersonalReceptionModel,
            IssueModel,
            RiskAssessmentModel,
            # FavoritesModel,
            SportFacilityRenovationInfoModel,
            SportFacilityInfoModel,
            TaskExecutionTimeModel,
            TaskSprintHistoryModel,
            TaskSprintModel,
            SprintExpectedResultModel,
            UserDesktopModel,
            UserWidgetOnDesktopModel,
            WorkgroupMembersModel,
            ChatModel,
        ]

        @contextmanager
        def disable_signals(signal_list):
            original_receivers = {}
            for signal in signal_list:
                original_receivers[signal] = signal.receivers
                signal.receivers = []
            try:
                yield
            finally:
                for signal in signal_list:
                    signal.receivers = original_receivers[signal]

        confirmation = input(
            "Это действие необратимо.\nПеред началом создайте "
            "резервную копию БД.\nВведите 'Yes' для продолжения: "
        )
        if confirmation != 'Yes':
            self.stdout.write(self.style.NOTICE('Операция отменена'))
            return

        self._setup_logger()

        with disable_signals([post_delete, post_init]):
            create_temp_bases()

            for model in MODELS_TO_DELETE:
                self._clean(model)

            self._clean_users_and_profiles()
