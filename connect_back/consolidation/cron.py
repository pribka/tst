from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django_q.tasks import async_task
from rest_framework import exceptions as drf_exceptions

from . import models, notifications


def create_consolidations():

    def is_month_end(date):
        return date.month != (date + timedelta(days=1)).month

    def get_next_creation_date(template):
        if template.repeat_period == 'WEEKLY':
            return template.next_creation_date + relativedelta(weeks=+1)
        elif template.repeat_period == 'MONTHLY':
            return template.next_creation_date + relativedelta(months=+1)
        elif template.repeat_period == 'YEARLY':
            return template.next_creation_date + relativedelta(years=+1)
        else:
            return None

    def get_next_dead_line(template, time_delta):
        if template.repeat_period == 'WEEKLY':
            next_dead_line = template.next_dead_line + time_delta
        if template.repeat_period == 'MONTHLY':
            if is_month_end(template.next_dead_line):
                next_dead_line = template.next_dead_line + relativedelta(months=+1, day=31)
            else:
                next_dead_line = template.next_dead_line + time_delta
        if template.repeat_period == 'YEARLY':
            if is_month_end(template.next_dead_line):
                next_dead_line = template.next_dead_line + relativedelta(years=+1, day=31)
            else:
                next_dead_line = template.next_dead_line + time_delta

        return next_dead_line

    def get_next_start(template, time_delta):
        return template.next_start + time_delta

    def get_next_end(template, time_delta):
        if template.repeat_period == 'WEEKLY':
            next_end = template.next_end + time_delta
        if template.repeat_period == 'MONTHLY':
            if is_month_end(template.next_end):
                next_end = template.next_end + relativedelta(months=+1, day=31)
            else:
                next_end = template.next_end + time_delta
        if template.repeat_period == 'YEARLY':
            if is_month_end(template.next_end):
                next_end = template.next_end + relativedelta(years=+1, day=31)
            else:
                next_end = template.next_end + time_delta
        return next_end

    TIMEDELTAS = {
        'WEEKLY': relativedelta(weeks=+1),
        'MONTHLY': relativedelta(months=+1),
        'YEARLY': relativedelta(years=+1),
    }

    now = timezone.now()

    consolidations_on_clone = models.ConsolidationModel.objects.filter(
        Q(repeat_to__gte=now) | Q(repeat_to__isnull=True),
        is_active=True,
        is_scheduled=True,
        is_template_on=True,
        next_creation_date__lt=now,
    )

    for each in consolidations_on_clone:
        time_delta = TIMEDELTAS.get(each.repeat_period)
        if not time_delta:
            raise drf_exceptions.ValidationError(
                'Периодичность указана некорректно'
            )
        report_form = each.report_form
        report_form_info = report_form.report_form_info.get(report_form.code, None)
        if report_form_info:
            files_info = report_form_info.get('files_info', [])
        with transaction.atomic():
            new_consolidation = models.ConsolidationModel.objects.create(
                name=f'{report_form.name} за период с {each.next_start} по {each.next_end}',
                author=each.author,
                org_administrator=each.org_administrator,
                report_form=each.report_form,
                dead_line=each.next_dead_line,
                start=each.next_start,
                end=each.next_end,
                auto_approve=each.auto_approve,
                add_org_administrator_in_members=each.add_org_administrator_in_members,
                description=each.description,
            )
            members = each.members.filter(is_active=True)
            for member in members:
                models.ConsolidationMemberModel.objects.create(
                            organization=member,
                            consolidation=new_consolidation
                        )
                report = models.ReportModel.objects.create(
                        consolidator=each.author,
                        parent=new_consolidation,
                        contractor=member,
                        status_id='not_loaded'
                    )
                if files_info:
                    report_files = [
                        models.ReportFileModel.objects.create(
                            file_type_id=file_info.get('code', 'default'),
                            sort=file_info.get('sort', 500),
                        ) for file_info in files_info
                    ]
                    report.report_files.set(report_files)
            attachments = each.attachments.filter(is_active=True)
            new_consolidation.attachments.set(attachments)
            each.next_creation_date = get_next_creation_date(each)
            each.next_dead_line = get_next_dead_line(each, time_delta)
            each.next_start = get_next_start(each, time_delta)
            each.next_end = get_next_end(each, time_delta)
            each.save(update_fields=(
                'next_creation_date',
                'next_dead_line',
                'next_start',
                'next_end'
            ))
            author_id = str(each.author.id) if each.author else None
            transaction.on_commit(
                lambda: async_task(
                    notifications.notify_new_consolidation_is_create,
                    str(new_consolidation.id),
                    author_id
                )
            )
    return
