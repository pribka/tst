import datetime
import os
import subprocess

import openpyxl
import pyexcelerate
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from openpyxl.worksheet.page import PageMargins
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers

from app_info.models import AppInfo

from common.utils import get_filter_queryset

from users.models import ProfileModel

from . import models


def get_access_users(request):
    if not request:
        return set()
    user = request.user.profile
    my_organizations = user.my_organizations
    from_organizations = set(models.PersonalPlaneAccessOrganizationModel.objects.filter(
        organization_id__in=my_organizations
    ).values_list('owner', flat=True))
    from_profiles = set(models.PersonalPlaneAccessProfileModel.objects.filter(
        user=user,
    ).values_list('owner', flat=True))
    from_access = from_organizations | from_profiles
    from_access.add(user.pk)
    return from_access


align_center = pyexcelerate.Alignment(horizontal='center', vertical='center', wrap_text=True)
align_left = pyexcelerate.Alignment(horizontal='left', vertical='center', wrap_text=True)
align_right = pyexcelerate.Alignment(horizontal='right', vertical='center', wrap_text=True)

normal_9 = pyexcelerate.Font(family='Times new roman', size=9,)
bold_9 = pyexcelerate.Font(bold=True, family='Times new roman', size=9,)

bold_9_center_style = pyexcelerate.Style(font=bold_9, alignment=align_center,)
bold_9_right_style = pyexcelerate.Style(font=bold_9, alignment=align_right,)
normal_9_left_style = pyexcelerate.Style(font=normal_9, alignment=align_left)
normal_9_center_style = pyexcelerate.Style(font=normal_9, alignment=align_center)


def get_personal_planes_report(request):
    from bpms.event_calendar.utils import get_access_users as event_get_access_users
    from bpms.event_calendar.models import EventCalendarModel
    qs = models.PersonalPlaneModel.objects.filter(is_active=True)
    access_users_id = get_access_users(request)
    filtered_access_users_id = get_filter_queryset(
        request,
        ProfileModel,
        ProfileModel.objects.filter(pk__in=access_users_id)
    ).values_list('pk', flat=True)
    event_access_users_id = event_get_access_users(request)
    filtered_event_access_users_id = get_filter_queryset(
        request,
        ProfileModel,
        ProfileModel.objects.filter(pk__in=event_access_users_id)
    )
    qs = qs.filter(author_id__in=filtered_access_users_id)
    query_params = request.query_params
    plane_datetime_gte = query_params.get('start')
    plane_datetime_lte = query_params.get('end')
    try:
        plane_date_gte = plane_datetime_gte[:10]
        plane_date_lte = plane_datetime_lte[:10]
    except TypeError:
        raise drf_exceptions.ValidationError('start, end is required.')
    try:
        plane_date_gte_date = datetime.datetime.strptime(plane_date_gte, "%Y-%m-%d")
        plane_date_lte_date = datetime.datetime.strptime(plane_date_lte, "%Y-%m-%d")
    except ValueError:
        raise drf_exceptions.ValidationError('invalid start, end.')
    else:
        delta = plane_date_lte_date - plane_date_gte_date
        if delta.days > 32 or delta.days < 0:
            raise drf_exceptions.ValidationError('Max. delta is month')
        else:
            org_id = request.query_params.get('organization')
            if org_id:
                try:
                    qs = qs.filter(author__contractors=org_id)
                except ValidationError:
                    raise drf_exceptions.ValidationError('Invalid organization id')
            else:
                raise drf_exceptions.ValidationError('Organization is required')
    plane_datetime_gte = serializers.DateTimeField().to_internal_value(plane_datetime_gte)
    plane_datetime_lte = serializers.DateTimeField().to_internal_value(plane_datetime_lte)
    gte = plane_datetime_gte
    plane_date_date_gte = serializers.DateField().to_internal_value(plane_date_gte)
    date_list = []
    for each in range(0, (plane_datetime_lte - plane_datetime_gte).days + 1):
        lt = gte + datetime.timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
        date_list.append({'start': gte, 'end': lt, 'date': plane_date_date_gte})
        gte += datetime.timedelta(days=1)
        plane_date_date_gte += datetime.timedelta(days=1)

    if delta.days == 0:
        ws_name = f'Отчет за {plane_date_gte_date.strftime("%d.%m")}'
    else:
        ws_name = f'Отчет за {plane_date_gte_date.strftime("%d.%m")}-{plane_date_lte_date.strftime("%d.%m")}'
    wb = pyexcelerate.Workbook()
    ws = wb.new_sheet(ws_name)
    ws.set_col_style(1, pyexcelerate.Style(size=30, ))
    ws.set_col_style(2, pyexcelerate.Style(size=30, ))
    ws.set_col_style(3, pyexcelerate.Style(size=10, ))
    ws.set_col_style(4, pyexcelerate.Style(size=50, ))
    ws.set_col_style(5, pyexcelerate.Style(size=20, ))
    ws.set_col_style(6, pyexcelerate.Style(size=50, ))
    ws.set_col_style(7, pyexcelerate.Style(size=15, ))
    ws.set_col_style(8, pyexcelerate.Style(size=15, ))
    merged_cells = list()
    border_cells = list()
    row = 1
    users = qs.values('author').annotate(
        last_name=F('author__user__last_name'),
        first_name=F('author__user__first_name'),
        middle_name=F('author__user__middle_name'),
    ).distinct().order_by(
        'last_name',
        'first_name',
        'middle_name',
    ).values(
        'author',
        'last_name',
        'first_name',
        'middle_name',
    )
    table_header = (
        (
            'ФИО',
            'Проект',
            'Тип',
            'Название',
            'Вид работы/события',
            'Описание',
            'Трудозатраты (план)',
            'Трудозатраты (факт)',
        ),
    )

    for date_day in date_list:
        ws.set_cell_value(row, 1, f"План работ на {date_day['date'].strftime('%d.%m')}")
        ws.set_cell_style(row, 1, bold_9_center_style)
        merged_cells.append(((row, 1), (row, 8),))
        row += 1
        ws.range((row, 1), (row, 8)).value = table_header
        ws.range((row, 1), (row, 8)).style.font = normal_9
        ws.range((row, 1), (row, 8)).style.alignment = align_center
        border_start = row
        row += 1
        day_qs = qs.filter(plane_date=date_day['date'])
        daily_duration_plan = 0
        daily_duration_fact = 0
        for user in users:
            user_plan = day_qs.filter(author_id=user['author']).first()
            if user_plan:
                user_plan_items = user_plan.plane_items.all().values_list(
                    'task__project__name',
                    'task__name',
                    'work_type__name',
                    'description',
                    'duration_plane',
                    'duration_fact',
                )
                if user_plan_items:
                    user_plan_data = []
                    correction = 0
                    for user_plan_item in user_plan_items:
                        user_plan_data.append(
                            (
                                f"{user['last_name']} {user['first_name']} {user['middle_name']}",
                                user_plan_item[0],
                                'задача',
                                user_plan_item[1],
                                user_plan_item[2],
                                user_plan_item[3],
                                user_plan_item[4],
                                user_plan_item[5],
                            )
                        )
                        daily_duration_plan += user_plan_item[4]
                        daily_duration_fact += user_plan_item[5]
                        correction += 1
                    ws.range((row, 1), (row + correction - 1, 8)).value = user_plan_data
                    ws.range((row, 1), (row + correction - 1, 8)).style.font = normal_9
                    ws.range((row, 1), (row + correction - 1, 6)).style.alignment = align_left
                    ws.range((row, 7), (row + correction - 1, 8)).style.alignment = align_center
                    row += correction
            if user['author'] in filtered_event_access_users_id:
                event_data = []
                correction = 0
                event_calendar_qs = EventCalendarModel.objects.filter(
                    Q(start_at__gte=date_day['start']) | Q(end_at__gte=date_day['start']),
                    Q(start_at__lte=date_day['end']) | Q(end_at__lte=date_day['end']),
                    is_active=True,
                    calendar__is_active=True,
                    members=user['author'],
                    ).order_by('start_at',).values_list(
                    'name', 'event_type__name', 'description',
                )
                for event in event_calendar_qs:
                    event_data.append(
                        (
                            f"{user['last_name']} {user['first_name']} {user['middle_name']}",
                            None,
                            'событие',
                            event[0],
                            event[1],
                            BeautifulSoup(event[2], 'lxml').get_text(separator=" ").strip(),
                            None,
                            None,
                        )
                    )
                    correction += 1
                ws.range((row, 1), (row + correction - 1, 8)).value = event_data
                ws.range((row, 1), (row + correction - 1, 8)).style.font = normal_9
                ws.range((row, 1), (row + correction - 1, 6)).style.alignment = align_left
                ws.range((row, 7), (row + correction - 1, 8)).style.alignment = align_center
                row += correction
        ws.set_cell_value(row, 6, 'Итого')
        ws.set_cell_style(row, 6, bold_9_right_style)
        ws.set_cell_value(row, 7, daily_duration_plan)
        ws.set_cell_value(row, 8, daily_duration_fact)
        ws.range((row, 6), (row, 8)).style.font = bold_9
        ws.range((row, 7), (row, 8)).style.alignment = align_center
        row += 1
        border_cells.append(((border_start, 1), (row - 1, 8)))
        row += 1
    for merged_cell in merged_cells:
        ws.range(*merged_cell).merge()
    for border_cell in border_cells:
        ws.range(*border_cell).style.borders.top.style = '_'
        ws.range(*border_cell).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
        ws.range(*border_cell).style.borders.left.style = '_'
        ws.range(*border_cell).style.borders.left.color = pyexcelerate.Color(0, 0, 0)
        ws.range(*border_cell).style.borders.bottom.style = '_'
        ws.range(*border_cell).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
        ws.range(*border_cell).style.borders.right.style = '_'
        ws.range(*border_cell).style.borders.right.color = pyexcelerate.Color(0, 0, 0)
    return wb


def convert_report_to_pdf(source_file, out_dir):
    wb = openpyxl.load_workbook(source_file)
    ws = wb.active
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToHeight = False
    ws.page_margins = PageMargins(left=0.75, right=0.25, top=0.25, bottom=0.25)
    wb.save(source_file.name)
    wb.close()
    try:
        result = subprocess.check_output(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', out_dir, source_file.name],
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        raise drf_exceptions.ValidationError('CalledProcessError')
    except OSError:
        raise drf_exceptions.ValidationError('OSError')
    if result.startswith(b'Error'):
        raise drf_exceptions.ValidationError('Error')
    out_file_name = os.path.join(out_dir, f"{os.path.split(source_file.name)[-1]}.pdf")
    return out_file_name


def has_work_plan_access(request) -> bool:
    """
    Проверяет, имеет ли пользователь доступ к функционалу рабочего плана.
    """
    work_plan_access = False

    try:
        app_info = AppInfo.objects.get(code='work_plan_show', is_active=True)
    except AppInfo.DoesNotExist:
        pass
    else:
        metadata = app_info.metadata
        if isinstance(metadata, list):
            metadata = set(metadata)
            user = request.user.profile
            orgs = set([str(each) for each in user.my_organizations])
            if not orgs.isdisjoint(metadata):
                work_plan_access = True

    return work_plan_access


def has_work_plan_access_v2(request) -> bool:
    """
    Проверяет, имеет ли пользователь доступ к функционалу рабочего плана v2.
    Проверка осуществляется по pk профиля пользователя.
    """
    work_plan_access = False

    try:
        app_info = AppInfo.objects.get(code='work_plan_show_v2', is_active=True)
    except AppInfo.DoesNotExist:
        pass
    else:
        metadata = app_info.metadata
        if isinstance(metadata, list):
            metadata = set([str(each) for each in metadata])
            user = request.user.profile
            user_pk = str(user.pk)
            if user_pk in metadata:
                work_plan_access = True

    return work_plan_access


def validate_task(task, request):
    if task:
        profile = request.user.profile
        roles = set(task.get_task_roles(profile.pk))
        if roles.isdisjoint({'owner', 'operator', 'cooperator', 'visor'}):
            raise drf_exceptions.ValidationError('Вы не являетесь участником этой задачи')
    return task
