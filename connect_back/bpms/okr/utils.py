import re
from datetime import date, datetime, time, timedelta

import pyexcelerate
from croniter import croniter
from dateutil.relativedelta import relativedelta
from django.db.models import Case, CharField, Count, F, Q, Value, When
from django.utils import timezone
from django.utils.timezone import get_default_timezone, make_aware
from django.utils.translation import get_language

from common.catalogs.models import ContractorDepartmentModel

from . import models


def is_last_friday_of_month(dt: datetime) -> bool:
    """Проверяет, является ли дата последней пятницей месяца."""
    # Проверяем, находится ли следующая пятница в том же месяце
    next_friday = dt + timedelta(days=7)
    return next_friday.month != dt.month


def calculate_next_notification_run(code:str, cron_expr:str, start_date: date, end_date: date):
    """Возвращает следующую дату оповещения или None.
    code - код частоты напоминания. Варианты: never, weekly, fortnightly, monthly, quarterly.
    cron_expr - cron-выражение (например, 0 10 * * 5)
    start_date - дата начала рассылки уведомлений, DateField.
    end_date - дата конца рассылки уведомлений, DateField.
    """
    if code == 'never':
        return None

    now = timezone.now()
    # Если start_date (дата начала цели) еще не наступила, то используем ее как начало отсчета для уведомлений
    if now.date() < start_date:
        # Преобразуем DateField в TZ aware datetime, который нужен для croniter
        start_date = make_aware(datetime.combine(start_date, time.min), timezone=get_default_timezone())
    else:
        start_date = now # В противном случае считаем от текущего момента.

    cron = croniter(cron_expr, start_date)

    if code == 'weekly':
        next_date = cron.get_next(datetime)

    if code == 'fortnightly':
        next_date = cron.get_next(datetime)
        next_date = cron.get_next(datetime)

    if code == 'monthly':
        while True:
            next_date = cron.get_next(datetime)
            if is_last_friday_of_month(next_date):
                break

    if code == 'quarterly':
        while True:
            next_date = cron.get_next(datetime)
            if is_last_friday_of_month(next_date):
                if next_date.month in {3, 6, 9, 12}:
                    break

    if next_date.date() > end_date:
        return None
    else:
        return next_date


def calculate_key_result_progress(base, plan, fact):
    """Вычисляет процент выполнения ключевого результата.
    Возвращает значение от 0 до 1."""
    planned_delta = plan - base
    current_delta = fact - base
    try:
        progress = round(current_delta / planned_delta, 2)
        return max(0, min(1, progress)) * 100
    except:
        return 0
    

def get_quarter(date):
    """Вычисляет квартал из даты."""
    return (date.month-1)//3 + 1


def get_objectives_status_count(queryset):
    """Принимает queryset объектов ObjectivesModel. Считает количество целей в каждом статусе."""
    statuses = models.ObjectiveStatusModel.objects.filter(is_active=True).order_by('sort').values_list('code', flat=True)
    aggregate_lookup = {
        status_code: Count('status', filter=Q(status=status_code)) for status_code in statuses
    }
    data = queryset.aggregate(
        **aggregate_lookup,
        # closed=Count(
        #     'pk',
        #     filter=Q(status__is_closed=True)
        # ),
        # overdue=Count(
        #     'pk',
        #     filter=Q(date_end__lt=timezone.now(), status__is_closed=False)
        # )
    )
    return data


# Стили для Excel-файла
align_center = pyexcelerate.Alignment(horizontal='center', vertical='center', wrap_text=True)
align_left = pyexcelerate.Alignment(horizontal='left', vertical='center', wrap_text=True)

normal_11 = pyexcelerate.Font(family='Arial', size=11,)
bold_11 = pyexcelerate.Font(bold=True, family='Arial', size=11,)

yellow_fill=pyexcelerate.Fill(background=pyexcelerate.Color(255, 255, 166))
dark_grey_fill=pyexcelerate.Fill(background=pyexcelerate.Color(204, 204, 204))

bold_11_center_style = pyexcelerate.Style(font=bold_11, alignment=align_center)
bold_11_center_style_yellow = pyexcelerate.Style(font=bold_11, alignment=align_center, fill=yellow_fill)
bold_11_left_style_grey = pyexcelerate.Style(font=bold_11, alignment=align_left, fill=dark_grey_fill)
normal_11_left_style = pyexcelerate.Style(font=normal_11, alignment=align_left, )
normal_11_center_style = pyexcelerate.Style(font=normal_11, alignment=align_center,)

def apply_row_style(ws, first_row, first_col, last_row, last_col, style):
    """Применяет стиль к диапазону ячеек листа"""
    width = last_col - first_col + 1
    height = last_row - first_row + 1
    style_matrix = [[style] * width for _ in range(height)]
    ws.range((first_row, first_col), (last_row, last_col)).style = style_matrix

def calculate_row_height(text: str, max_chars_per_line: int = 50, base_height: int = 15) -> int:
    """
    Возвращает высоту строки в Excel в зависимости от длины текста и ширины ячейки.
    
    :param text: Текст, который будет записан в ячейку
    :param max_chars_per_line: Максимальное число символов в строке без переноса (имитация ширины столбца)
    :param base_height: Базовая высота строки в пикселях (для одной строки текста)
    """
    import math
    lines = math.ceil(len(text) / max_chars_per_line)
    return base_height * lines


def set_row_heights(ws, start_row, heights):
    """
    Устанавливает высоты строк по списку, начиная с указанной строки (Excel-style, 1-based).
    :param ws: Worksheet объект из pyexlerate
    :param start_row: Номер первой строки, с которой начинается установка (1-based, как в Excel)
    :param heights: Список высот строк (в пикселях), соответствующий строкам [start_row, start_row + len(heights) - 1]
    """
    for i, height in enumerate(heights):
        ws.set_row_style(start_row + i, pyexcelerate.Style(size=height))


def get_okr_report_file(request, queryset):
    """Формирует Excel-файл отчета по ОКР."""
    # Подготовка исходных данных
    all_objectives_progress_dict = dict()
    for objective in queryset:
        all_objectives_progress_dict[objective.id] = objective.progress

    objective_ids = queryset.values_list('id', flat=True)
    all_key_results = models.KeyResultsModel.objects.filter(objective_id__in=objective_ids).order_by('date_start', 'date_end', '-created_at')
    all_key_results_progress_dict = dict()
    for key_result in all_key_results:
        all_key_results_progress_dict[key_result.id] = key_result.progress
    current_language = get_language()
    
   
    # Базовые аннотации
    all_key_results = all_key_results.annotate(
        operator_first_name=F('operator__user__first_name'),
        operator_last_name=F('operator__user__last_name'),
        operator_middle_name=F('operator__user__middle_name'),
    )
    
    # Добавляем metrics_name в зависимости от языка
    if current_language == 'kk':
        all_key_results = all_key_results.annotate(
            metrics_name=Case(
                When(metrics__name_kk__isnull=False, metrics__name_kk__gt='', then=F('metrics__name_kk')),
                default=F('metrics__name_ru'),
                output_field=CharField(),
            )
        )
    else:
        all_key_results = all_key_results.annotate(metrics_name=F('metrics__name_ru'))
    
    all_key_results = all_key_results.values(
        'id', 'objective_id', 'date_start', 'date_end', 'description',
        'operator_first_name', 'operator_last_name', 'operator_middle_name',
        'metrics_name', 'base', 'plan', 'fact',
    )

     
    all_key_results = list(all_key_results)

    wb = pyexcelerate.Workbook()
    # Сначала добавляем цели всей организации (department=None), затем цели отделов.
    department_ids = queryset.values_list('department_id', flat=True)
    department_ids = list(set(department_ids))
    department_ids = sorted(department_ids, key=lambda x: (x is not None, x))
    for department_id in department_ids:
        if department_id:
            name = ContractorDepartmentModel.objects.get(pk=department_id).name
        else:
            user = request.user.profile
            name = user.current_contractor.name
        name = re.sub(r"[:\\/*?\[\]'&]", '_', name)
        name = name.strip()
        short_name = name[:27] + "..." if len(name) > 30 else name
        department_objectives_qs = queryset.filter(department_id=department_id)
        wb = add_data_to_sheet(wb,
                            short_name,
                            department_objectives_qs,
                            all_key_results,
                            all_objectives_progress_dict,
                            all_key_results_progress_dict)
    return wb


def add_data_to_sheet(wb, sheet_name, queryset, all_key_results, all_objectives_progress_dict, all_key_results_progress_dict):
    """Формирует лист Excel-файла отчета по ОКР."""
    ws = wb.new_sheet(sheet_name)

    ws.set_col_style(1, pyexcelerate.Style(size=10,))
    ws.set_col_style(2, pyexcelerate.Style(size=10,))
    ws.set_col_style(3, pyexcelerate.Style(size=10,))
    ws.set_col_style(4, pyexcelerate.Style(size=50,))
    ws.set_col_style(5, pyexcelerate.Style(size=30,))
    ws.set_col_style(6, pyexcelerate.Style(size=20,))
    ws.set_col_style(7, pyexcelerate.Style(size=15,))
    ws.set_col_style(8, pyexcelerate.Style(size=15,))
    ws.set_col_style(9, pyexcelerate.Style(size=15,))

    row = 1
    first_col = 1
    last_col = 9

    table_header_data = (
        (
            'Прогресс',
            'Квартал',
            '№',
            'Описание',
            'Ответственный',
            'Метрика',
            'Баз.знач.',
            'План',
            'Факт',
        ),
    )
    ws.range((row, first_col), (row, last_col)).value = table_header_data
    apply_row_style(ws, row, first_col, row, last_col, bold_11_center_style_yellow)

    objectives_counter = 1
    for objective in queryset:
        row += 1
        objective_data = (
            (
                f"{all_objectives_progress_dict[objective.id]*100:0.0f}%",
                f"Q{get_quarter(objective.date_end)}_{objective.date_end.year}",
                f"Цель {objectives_counter}",
                objective.objective,
                '', '', '', '', '',
            ),
        )
        ws.range((row, first_col), (row, last_col)).value = objective_data
        apply_row_style(ws, row, first_col, row, last_col, bold_11_left_style_grey)
        set_row_heights(ws, row, [calculate_row_height(objective.objective),])

        key_results = [kr for kr in all_key_results if kr['objective_id'] == objective.id]
        if key_results:
            row += 1
            key_results_counter = 1
            key_results_data = list()
            row_heights = []
            for key_result in key_results:
                operator_full_name = f"{key_result['operator_last_name']} {key_result['operator_first_name']} {key_result['operator_middle_name']}"
                key_results_data.append(
                    (
                        f"{all_key_results_progress_dict[key_result.get('id')]*100:0.0f}%",
                        f"Q{get_quarter(key_result.get('date_end'))}_{key_result.get('date_end').year}",
                        f"КР {key_results_counter}",
                        key_result.get('description'),
                        operator_full_name,
                        key_result.get('metrics_name'),
                        key_result.get('base'),
                        key_result.get('plan'),
                        key_result.get('fact'),
                    )
                )
                key_results_counter += 1
                row_height = max(calculate_row_height(key_result.get('description') or ''),
                                  calculate_row_height(key_result.get('metrics_name') or '',
                                  20))
                row_heights.append(row_height)
            ws.range((row, first_col), (row + key_results_counter - 1, last_col)).value = key_results_data
            apply_row_style(ws, row, first_col, row + key_results_counter - 1, last_col, normal_11_left_style)
            set_row_heights(ws, row, row_heights)
            row = row + key_results_counter - 2
        objectives_counter += 1

    # Границы ячеек:
    ws.range((1, first_col), (row, last_col)).style.borders.top.style = '_'
    ws.range((1, first_col), (row, last_col)).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
    ws.range((1, first_col), (row, last_col)).style.borders.left.style = '_'
    ws.range((1, first_col), (row, last_col)).style.borders.left.color = pyexcelerate.Color(0, 0, 0)
    ws.range((1, first_col), (row, last_col)).style.borders.bottom.style = '_'
    ws.range((1, first_col), (row, last_col)).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
    ws.range((1, first_col), (row, last_col)).style.borders.right.style = '_'
    ws.range((1, first_col), (row, last_col)).style.borders.right.color = pyexcelerate.Color(0, 0, 0)

    return wb


def get_quarter_dates(quarter: int):
    "Возвращает даты первого и последнего дня квартала"

    current_year = date.today().year
    first_month_of_quarter = (quarter - 1) * 3 + 1
    date_start = date(current_year, first_month_of_quarter, 1)
    date_end = date_start + relativedelta(months=3, days=-1)

    return date_start, date_end
