import pyexcelerate

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import F, Sum, Q

from rest_framework import exceptions as drf_exceptions

from bpms.workgroups.models import WorkgroupModel
from bpms.tasks.models import TaskModel, TaskExecutionTimeModel

from users.models import ProfileModel

from . import models

regular_11 = pyexcelerate.Font(
    family='Arial',
    size=9,
)
bold_11 = pyexcelerate.Font(
    family='Arial',
    size=9,
    bold=True,
)
align_left = pyexcelerate.Alignment(horizontal='left', vertical='center', wrap_text=True)
align_right = pyexcelerate.Alignment(horizontal='right', vertical='center', wrap_text=True)
align_center = pyexcelerate.Alignment(horizontal='center', vertical='center', wrap_text=True)

style_header = pyexcelerate.Style(font=regular_11, alignment=align_center)
style_regular = pyexcelerate.Style(font=regular_11, alignment=align_left)
style_footer_right = pyexcelerate.Style(font=bold_11, alignment=align_right)


def get_project_work_list_wb(request):
    query_params = request.query_params
    project_id = query_params.get('project')
    if not project_id:
        return get_work_list_wb(request)
    try:
        project = WorkgroupModel.objects.get(is_active=True, pk=project_id)
    except (ValidationError, ObjectDoesNotExist,):
        raise drf_exceptions.ValidationError('Project not found')
    date_gte = query_params.get('date_gte')
    date_lte = query_params.get('date_lte')

    # if not project.get_detail_permission(request):
    #     raise drf_exceptions.PermissionDenied('project')
    group_by = query_params.get('group_by', '')

    project_tasks_qs = TaskModel.objects.filter(
        is_active=True,
        project_id=project_id
    ).values_list('pk', flat=True)
    try:
        execution_time_qs = TaskExecutionTimeModel.objects.filter(
            task__in=project_tasks_qs,
            is_active=True,
            date__gte=date_gte,
            date__lte=date_lte,
        )
    except ValidationError:
        raise drf_exceptions.ValidationError('date_gte / date_lte is not valid')


    wb = pyexcelerate.Workbook()
    ws = wb.new_sheet('Реестр выполненных работ')
    ws.set_col_style(1, pyexcelerate.Style(size=12, ))
    ws.set_col_style(2, pyexcelerate.Style(size=100, ))
    ws.set_col_style(3, pyexcelerate.Style(size=20, ))
    ws.set_col_style(4, pyexcelerate.Style(size=20, ))

    merged_cells = list()
    first_col = 1
    last_col = 4
    row = 1
    # Заголовок
    ws.set_cell_value(row, first_col, f'Реестр выполненных работ в период с {date_gte} по {date_lte}')
    ws.set_cell_style(row, first_col, style_header)
    merged_cells.append(((row, first_col), (row, last_col)))
    row += 1

    ws.set_cell_value(row, first_col, 'Проект:')
    ws.set_cell_value(row, first_col+1, project.name)
    row += 2
    data = []
    counter = 0
    ws.range((row, first_col), (row, last_col)).value = (
        ('№ п/п', 'Выполненные работы', 'Трудозатраты (план)', 'Трудозатраты (факт)',),
    )

    row += 1
    total_time_plan = 0
    total_time_fact = 0
    operator_cells = []
    total_cells = []
    if group_by == 'operator':
        operators = execution_time_qs.values('author',).distinct('author').annotate(
            id=F('author__id'),
            last_name=F('author__user__last_name'),
            first_name=F('author__user__first_name'),
        ).values('id', 'last_name', 'first_name')
        absolute_time_plan = 0
        absolute_time_fact = 0
        for operator in operators:
            ws.set_cell_value(row, 1, f"{operator['last_name']} {operator['first_name']}")
            operator_cells.append((row, 1))
            merged_cells.append(((row, first_col), (row, first_col+1)))
            row += 1
            operator_execution_times = execution_time_qs.filter(author_id=operator['id'])
            tasks = operator_execution_times.values('task').annotate(
                id=F('task__id'),
                execution_time_plan=F('task__execution_time_plan'),
            ).distinct('id')
            counter = 0
            total_time_plan = 0
            total_time_fact = 0
            data = []
            for task in tasks:
                counter += 1
                qs = operator_execution_times.filter(task_id=task['id']).distinct()
                descriptions = '. '.join(list(qs.values_list('description', flat=True)))
                execution_time_plan = task['execution_time_plan']
                total_time_plan += execution_time_plan
                execution_time_fact = qs.aggregate(hours_sum=Sum('hours'))['hours_sum']
                total_time_fact += execution_time_fact
                data.append(
                    [
                        counter,
                        descriptions,
                        execution_time_plan,
                        execution_time_fact,
                    ],
                )
            ws.range((row, first_col), (row+counter, last_col)).value = data
            row += counter
            ws.range((row, first_col), (row, last_col)).value = (
                (
                    None,
                    'Итого',
                    total_time_plan,
                    total_time_fact,
                ),
            )
            absolute_time_plan += total_time_plan
            absolute_time_fact += total_time_fact
            total_cells.append((row, first_col+1))
            row += 1

        ws.range((row, first_col), (row, last_col)).value = (
            (
                None,
                'ВСЕГО',
                absolute_time_plan,
                absolute_time_fact,
            ),
        )
        total_cells.append((row, first_col+1))

        ws.range((2, first_col), (row, last_col)).style.font = regular_11
        ws.range((2, first_col), (row, last_col)).style.alignment = align_left

        ws.range((5, first_col), (row, first_col)).style.alignment = align_center

        ws.range((5, first_col + 2), (row, first_col + 3)).style.font = bold_11
        ws.range((5, first_col + 2), (row, first_col + 3)).style.alignment = align_center
        for operator_cell in operator_cells:
            ws.set_cell_style(*operator_cell, style_regular)
        for total_cell in total_cells:
            ws.set_cell_style(*total_cell, style_footer_right)
    else:
        tasks = execution_time_qs.values('task').annotate(
            id=F('task__id'),
            execution_time_plan=F('task__execution_time_plan'),
        ).values('id', 'execution_time_plan')
        for task in tasks:
            counter += 1
            qs = execution_time_qs.filter(task_id=task['id'])
            descriptions = '. '.join(list(qs.values_list('description', flat=True)))
            execution_time_plan = task['execution_time_plan']
            total_time_plan += execution_time_plan
            execution_time_fact = qs.aggregate(hours_sum=Sum('hours'))['hours_sum']
            total_time_fact += execution_time_fact
            data.append(
                [
                    counter,
                    descriptions,
                    execution_time_plan,
                    execution_time_fact,
                ]
            )
        ws.range((row, first_col), (row + counter, last_col)).value = data
        row += counter
        ws.range((row, first_col), (row, last_col)).value = (
            (
                None,
                'ВСЕГО',
                total_time_plan,
                total_time_fact,
            ),
        )

        ws.range((2, first_col), (row, last_col)).style.font = regular_11
        ws.range((2, first_col), (row, last_col)).style.alignment = align_left

        ws.range((5, first_col), (row, first_col)).style.alignment = align_center

        ws.range((5, first_col+2), (row, first_col+3)).style.font = bold_11
        ws.range((5, first_col+2), (row, first_col+3)).style.alignment = align_center

        ws.set_cell_style(row, first_col+1, style_footer_right)

    ws.range((4, first_col), (row, last_col)).style.borders.top.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
    ws.range((4, first_col), (row, last_col)).style.borders.left.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.left.color = pyexcelerate.Color(0, 0, 0)
    ws.range((4, first_col), (row, last_col)).style.borders.bottom.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
    ws.range((4, first_col), (row, last_col)).style.borders.right.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.right.color = pyexcelerate.Color(0, 0, 0)

    for merged_cell in merged_cells:
        ws.range(*merged_cell).merge()
    return wb


def get_work_list_wb(request):
    query_params = request.query_params
    date_gte = query_params.get('date_gte')
    date_lte = query_params.get('date_lte')
    user_id = query_params.get('user')
    if not user_id:
        return get_users_work_list_wb(request)
    contractor_id = query_params.get('contractor')
    if contractor_id:
        lookup = Q(task__organization_id=contractor_id)
    else:
        lookup = Q()
    try:
        user = ProfileModel.objects.get(pk=user_id, is_active=True)
    except (ValidationError, ObjectDoesNotExist):
        raise drf_exceptions.ValidationError('user not found')
    try:
        execution_time_qs = TaskExecutionTimeModel.objects.filter(
            lookup,
            user_id=user_id,
            is_active=True,
            date__gte=date_gte,
            date__lte=date_lte,
            task__project__isnull=False,
        )
    except ValidationError:
        raise drf_exceptions.ValidationError('date_gte / date_lte is not valid')
    tasks = execution_time_qs.values('task').annotate(
        id=F('task__id'),
        execution_time_plan=F('task__execution_time_plan'),
        project_id=F('task__project_id'),
        project_name=F('task__project__name'),
    ).distinct('id')

    absolute_time_plan = 0
    absolute_time_fact = 0
    wb = pyexcelerate.Workbook()
    ws = wb.new_sheet('Реестр выполненных работ')
    ws.set_col_style(1, pyexcelerate.Style(size=12, ))
    ws.set_col_style(2, pyexcelerate.Style(size=40))
    ws.set_col_style(3, pyexcelerate.Style(size=100, ))
    ws.set_col_style(4, pyexcelerate.Style(size=20, ))
    ws.set_col_style(5, pyexcelerate.Style(size=20, ))

    row = 1

    first_col = 1
    last_col = 5

    merged_cells = list()

    # Заголовок
    ws.set_cell_value(row, first_col, f'Реестр выполненных работ в период с {date_gte} по {date_lte}')
    ws.set_cell_style(row, first_col, style_header)
    merged_cells.append(((row, first_col), (row, last_col)))
    row += 1
    ws.set_cell_value(row, 1, f'Сотрудник')
    ws.set_cell_value(row, 2, user.full_name)
    row += 2
    ws.range((row, first_col), (row, last_col)).value = (
        ('№ п/п', 'Проект', 'Выполненные работы', 'Трудозатраты (план)', 'Трудозатраты (факт)',),
    )
    row += 1
    total_time_plan = 0
    total_time_fact = 0
    counter = 0
    data = []
    for task in tasks:
        counter += 1
        project_name = task['project_name']
        qs = execution_time_qs.filter(task_id=task['id']).distinct()
        descriptions = '. '.join(list(qs.values_list('description', flat=True)))
        execution_time_plan = task['execution_time_plan']
        total_time_plan += execution_time_plan
        execution_time_fact = qs.aggregate(hours_sum=Sum('hours'))['hours_sum']
        total_time_fact += execution_time_fact

        data.append(
            [
                counter,
                project_name,
                descriptions,
                execution_time_plan,
                execution_time_fact,
            ],
        )

    ws.range((row, first_col), (row + counter, last_col)).value = data
    row += counter
    ws.range((row, first_col), (row, last_col)).value = (
        (
            None,
            None,
            'ВСЕГО',
            total_time_plan,
            total_time_fact,
        ),
    )
    absolute_time_plan += total_time_plan
    absolute_time_fact += total_time_fact

    ws.range((2, first_col), (row, last_col)).style.font = regular_11
    ws.range((2, first_col), (row, last_col)).style.alignment = align_left

    ws.range((5, first_col), (row, first_col)).style.alignment = align_center

    ws.range((5, first_col + 3), (row, first_col + 4)).style.font = bold_11
    ws.range((5, first_col + 3), (row, first_col + 4)).style.alignment = align_center
    ws.set_cell_style(row, 3, style_footer_right)

    ws.range((4, first_col), (row, last_col)).style.borders.top.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
    ws.range((4, first_col), (row, last_col)).style.borders.left.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.left.color = pyexcelerate.Color(0, 0, 0)
    ws.range((4, first_col), (row, last_col)).style.borders.bottom.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
    ws.range((4, first_col), (row, last_col)).style.borders.right.style = '_'
    ws.range((4, first_col), (row, last_col)).style.borders.right.color = pyexcelerate.Color(0, 0, 0)

    for merged_cell in merged_cells:
        ws.range(*merged_cell).merge()

    return wb


def get_users_work_list_wb(request):
    query_params = request.query_params
    date_gte = query_params.get('date_gte')
    date_lte = query_params.get('date_lte')
    users_id = query_params.get('users')

    contractor_id = query_params.get('contractor')
    if contractor_id:
        lookup = Q(task__organization_id=contractor_id)
    else:
        lookup = Q()
    try:
        users = ProfileModel.objects.filter(is_active=True, pk__in=users_id.split(','))
    except ValidationError:
        raise drf_exceptions.ValidationError('invalid users')

    absolute_time_plan = 0
    absolute_time_fact = 0
    wb = pyexcelerate.Workbook()
    ws = wb.new_sheet('Реестр выполненных работ')
    ws.set_col_style(1, pyexcelerate.Style(size=12, ))
    ws.set_col_style(2, pyexcelerate.Style(size=40))
    ws.set_col_style(3, pyexcelerate.Style(size=100, ))
    ws.set_col_style(4, pyexcelerate.Style(size=20, ))
    ws.set_col_style(5, pyexcelerate.Style(size=20, ))

    row = 1

    first_col = 1
    last_col = 5

    merged_cells = list()

    # Заголовок
    ws.set_cell_value(row, first_col, f'Реестр выполненных работ в период с {date_gte} по {date_lte}')
    ws.set_cell_style(row, first_col, style_header)
    merged_cells.append(((row, first_col), (row, last_col)))

    row += 2
    ws.range((row, first_col), (row, last_col)).value = (
        ('№ п/п', 'Проект', 'Выполненные работы', 'Трудозатраты (план)', 'Трудозатраты (факт)',),
    )
    row += 1
    user_rows = []
    total_rows = []
    for user in users:
        counter = 0
        total_time_plan = 0
        total_time_fact = 0
        user_id = user.pk
        ws.set_cell_value(row, first_col, user.full_name)
        merged_cells.append(((row, first_col), (row, first_col+2),))
        user_rows.append(row)
        row += 1
        try:
            execution_time_qs = TaskExecutionTimeModel.objects.filter(
                lookup,
                user_id=user_id,
                is_active=True,
                date__gte=date_gte,
                date__lte=date_lte,
                task__project__isnull=False,
            )
        except ValidationError:
            raise drf_exceptions.ValidationError('date_gte / date_lte is not valid')
        tasks = execution_time_qs.values('task').annotate(
            id=F('task__id'),
            execution_time_plan=F('task__execution_time_plan'),
            project_id=F('task__project_id'),
            project_name=F('task__project__name'),
        ).distinct('id')
        data = []
        for task in tasks:
            counter += 1
            project_name = task['project_name']
            qs = execution_time_qs.filter(task_id=task['id']).distinct()
            descriptions = '. '.join(list(qs.values_list('description', flat=True)))
            execution_time_plan = task['execution_time_plan']
            total_time_plan += execution_time_plan
            execution_time_fact = qs.aggregate(hours_sum=Sum('hours'))['hours_sum']
            total_time_fact += execution_time_fact

            data.append(
                [
                    counter,
                    project_name,
                    descriptions,
                    execution_time_plan,
                    execution_time_fact,
                ],
            )

        ws.range((row, first_col), (row + counter, last_col)).value = data
        row += counter
        ws.range((row, first_col), (row, last_col)).value = (
            (
                'ИТОГО',
                None,
                None,
                total_time_plan,
                total_time_fact,
            ),
        )
        total_rows.append(row)
        merged_cells.append(((row, first_col), (row, first_col+2)))
        row += 1
        absolute_time_plan += total_time_plan
        absolute_time_fact += total_time_fact

    ws.range((row, first_col), (row, last_col)).value = (
        (
            'ВСЕГО',
            None,
            None,
            absolute_time_plan,
            absolute_time_fact,
        ),
    )
    total_rows.append(row)
    merged_cells.append(((row, first_col), (row, first_col+2)))

    ws.range((2, first_col), (row, last_col)).style.font = regular_11
    ws.range((2, first_col), (row, last_col)).style.alignment = align_left

    ws.range((4, first_col), (row, first_col)).style.alignment = align_center

    ws.range((4, first_col + 3), (row, first_col + 4)).style.font = bold_11
    ws.range((4, first_col + 3), (row, first_col + 4)).style.alignment = align_center
    ws.set_cell_style(row, 3, style_footer_right)
    for user_row in user_rows:
        ws.set_cell_style(user_row, 1, style_regular)
    for total_row in total_rows:
        ws.set_cell_style(total_row, first_col, style_footer_right)

    ws.range((3, first_col), (row, last_col)).style.borders.top.style = '_'
    ws.range((3, first_col), (row, last_col)).style.borders.top.color = pyexcelerate.Color(0, 0, 0)
    ws.range((3, first_col), (row, last_col)).style.borders.left.style = '_'
    ws.range((3, first_col), (row, last_col)).style.borders.left.color = pyexcelerate.Color(0, 0, 0)
    ws.range((3, first_col), (row, last_col)).style.borders.bottom.style = '_'
    ws.range((3, first_col), (row, last_col)).style.borders.bottom.color = pyexcelerate.Color(0, 0, 0)
    ws.range((3, first_col), (row, last_col)).style.borders.right.style = '_'
    ws.range((3, first_col), (row, last_col)).style.borders.right.color = pyexcelerate.Color(0, 0, 0)

    for merged_cell in merged_cells:
        ws.range(*merged_cell).merge()

    return wb
