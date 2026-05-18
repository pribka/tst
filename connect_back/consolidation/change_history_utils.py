from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from change_history.models import ChangeHistoryModel


def create_update_report_status(report, action_date, before_code, after_code, author):
    from .models import ReportStatusModel

    if before_code:
        try:
            before_instance = ReportStatusModel.objects.get(code=before_code)
            before = before_instance.name
        except ObjectDoesNotExist:
            before = ''
    else:
        before = ''
    if after_code:
        try:
            after_instance = ReportStatusModel.objects.get(code=after_code)
            after = after_instance.name
        except ObjectDoesNotExist:
            after = ''
    else:
        after = ''
    ChangeHistoryModel.objects.create(
        author=author,
        related_object_id=report.parent_id,
        action_id='updated',
        object_property_id='consolidation__report__status',
        before=before,
        after=after,
        before_data={"report_id": report.pk, "before_code": before_code},
        after_data={"report_id": report.pk, "after_code": after_code},
        action_date=action_date,
        description=f"{report.contractor.name}"[:1023]
    )


def create_update_report_file(report_file, action_date, before_file_id, after_file_id, author):
    from common.models import File
    if before_file_id:
        try:
            before_instance = File.objects.get(pk=before_file_id)
            before = before_instance.full_name
        except ObjectDoesNotExist:
            before = ''
    else:
        before = ''
    if after_file_id:
        try:
            after_instance = File.objects.get(pk=after_file_id)
            after = after_instance.full_name
        except ObjectDoesNotExist:
            after = ''
    else:
        after = ''
    report = report_file.report
    ChangeHistoryModel.objects.create(
        author=author,
        related_object_id=report.parent.pk,
        action_id='updated',
        object_property_id='consolidation__report__file',
        before=before,
        after=after,
        before_data={"report_id": report.pk, "report_file_id":report_file.pk, "before_file_id": before_file_id},
        after_data={"report_id": report.pk, "report_file_id":report_file.pk, "after_code": after_file_id},
        action_date=action_date,
        description=f"{report.contractor.name}, {report_file.file_type.name}"[:1023]
    )
