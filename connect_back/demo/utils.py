from django.db.models.base import ValidationError
import pandas as pd
import os
import datetime
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from users.models import CustomUser, ProfileModel
from users import utils as user_utils
from common.catalogs.models import (
    ContractorModel, 
    ContractorMemberModel, 
    ContractorProfileModel,
    CurrencyModel,
    BankRequisitesModel
)
from contractor_permissions.models import AccessGroupMemberThroughModel, AccessGroupModel
from billing.models import ContractorTariffModel, TariffModel
from bpms.workgroups.models import (
    WorkgroupModel, 
    WorkgroupMembersModel, 
    WorkgroupMembershipRole, 
    WorkgroupMembershipStatus
)
from bpms.tasks.models import (
    TaskSprintModel, 
    SprintProjectThroughModel,
    TaskExecutionTimeModel,
    TaskModel, 
    TaskStatusModel, 
    TaskVisor, 
    TaskCooperator
)
from bpms.event_calendar.models import CalendarModel, EventCalendarModel
from bpms.event_calendar.utils import get_or_create_related_calendar
from users.utils import generate_password


def read_demo_data(model_name: str) -> pd.DataFrame:
    """
    Читает данные из указанного листа Excel файла с демо-данными.
    Автоматически заменяет NaN значения на пустые строки.
    """
    excel_path = os.path.join(settings.BASE_DIR, 'demo', 'data', 'Demo_data.xlsx')
    
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Demo data file not found: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path, sheet_name=model_name)
        
        # Заменяем NaN значения на пустые строки для всех текстовых столбцов
        df = df.fillna('')
        
        return df
    except ValueError as e:
        if "Worksheet named" in str(e):
            raise ValueError(f"Sheet '{model_name}' not found in Excel file")
        raise e


def create_demo_users(contractor):
    """
    Создает демо-пользователей на основе данных из листа 'ProfileModel' Excel файла.
    """
    
    if not contractor:
        raise ValueError("contractor cannot be empty")
    
    # Читаем данные из Excel файла
    df = read_demo_data('ProfileModel')
    created_users = {}
    
    for index, row in df.iterrows():
        slug = row['slug']
        first_name = row['first_name']
        last_name = row['last_name']
        job_title = row['job_title']
        access_group_code = row['AccessGroupModel']

        access_group = AccessGroupModel.objects.get(code=access_group_code, is_active=True)
        
        # Генерируем уникальные данные для пользователя
        username = f"demo_user_{str(uuid.uuid4())}"
        generated_sequence = user_utils.generate_user_name()
        email = f"demo_user_{generated_sequence}@example.com"
        
        with transaction.atomic():
            # Создаем пользователя
            user = CustomUser(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            rand_pass = generate_password()
            user.set_password(rand_pass)
            user.password_generated = True
            user.save(
                profile_kwargs={
                    "is_demo": True,
                    "temporary_blocked": False,
                    "job_title": job_title,
                }
            )
            
            profile = user.profile
            
            # Создаем связь пользователя с организацией
            contractor_profile = ContractorProfileModel.objects.create(
                contractor=contractor,
                user=profile
            )
            
            # Назначаем группу доступа
            access_group_member = AccessGroupMemberThroughModel.objects.create(
                member=contractor_profile,
                access_group=access_group
            )
            
            # Сохраняем созданного пользователя в словарь
            created_users[slug] = profile
    
    return created_users


def create_demo_workgroups(user, contractor, users_dict: dict):
    """
    Создает демо-проекты на основе данных из листа 'WorkgroupModel' Excel файла.
    """
    
    if not contractor:
        raise ValueError("contractor cannot be empty")
    
    if not users_dict:
        raise ValueError("users_dict cannot be empty")
    
    founder_user = user
    
    # Читаем данные проектов из Excel файла
    df_workgroups = read_demo_data('WorkgroupModel')
    created_workgroups = {}
    
    # Получаем статусы и роли
    approved_status = WorkgroupMembershipStatus.objects.get(code='APPROVED')
    founder_role = WorkgroupMembershipRole.objects.get(code='FOUNDER')
    
    for index, row in df_workgroups.iterrows():
        slug = row['slug']
        name = row['name']
        description = row.get('description', '')
        time_start = row['time_start']
        time_end = row['time_end']
        duration_days = int(row['duration'])  # продолжительность в днях
        is_project = bool(row.get('is_project', True))
        with_chat = bool(row.get('with_chat', False))
        funds = float(row.get('funds', 0))
        funds_currency_name = row.get('funds_currency', 'KZT')
        
        # Получаем валюту
        funds_currency = CurrencyModel.objects.get(name_ru=funds_currency_name, is_active=True)
        
        # Вычисляем даты начала и окончания
        current_date = timezone.now().date()
        
        # Используем объекты time напрямую (они уже приходят из Excel как datetime.time)
        date_start_plan = timezone.make_aware(
            datetime.datetime.combine(current_date, time_start)
        )
        
        # Добавляем дни к дате окончания
        end_date = current_date + datetime.timedelta(days=duration_days)
        dead_line = timezone.make_aware(
            datetime.datetime.combine(end_date, time_end)
        )
        
        with transaction.atomic():
            # Создаем проект
            workgroup = WorkgroupModel.objects.create(
                name=name,
                description=description,
                organization=contractor,
                date_start_plan=date_start_plan,
                dead_line=dead_line,
                is_project=is_project,
                with_chat=with_chat,
                funds=funds,
                funds_currency=funds_currency,
                is_demo=True,
                author=founder_user
            )
            
            # Назначаем FOUNDER
            WorkgroupMembersModel.objects.create(
                member=founder_user,
                work_group=workgroup,
                membership_role=founder_role,
                membership_request_status=approved_status,
                member_visible=True
            )
            
            # Сохраняем созданный проект в словарь
            created_workgroups[slug] = workgroup
    
    # Читаем данные участников и назначаем их в проекты
    df_members = read_demo_data('WorkgroupMembersModel')
    
    for index, row in df_members.iterrows():
        workgroup_slug = row['workgroup_slug']
        user_slug = row['user_slug'] 
        role_code = row['role_code']
        
        # Проверяем существование проекта и пользователя
        if workgroup_slug not in created_workgroups:
            print(f"Warning: workgroup_slug '{workgroup_slug}' not found for member assignment. Skipping.")
            continue
            
        if user_slug not in users_dict:
            print(f"Warning: user_slug '{user_slug}' not found for member assignment. Skipping.")
            continue
        
        try:
            role = WorkgroupMembershipRole.objects.get(code=role_code, is_active=True)
        except WorkgroupMembershipRole.DoesNotExist:
            print(f"Warning: Role with code '{role_code}' not found. Skipping.")
            continue
        
        workgroup = created_workgroups[workgroup_slug]
        user = users_dict[user_slug]
        
        # Проверяем, что пользователь еще не добавлен в проект
        if not WorkgroupMembersModel.objects.filter(
            work_group=workgroup, 
            member=user, 
            is_active=True
        ).exists():
            WorkgroupMembersModel.objects.create(
                member=user,
                work_group=workgroup,
                membership_role=role,
                membership_request_status=approved_status,
                member_visible=True,
            )
    
    return created_workgroups


def create_demo_sprints(user, workgroups_dict: dict):
    """
    Создает демо-спринты на основе данных из листа 'TaskSprintModel' Excel файла.
    """
    
    if not workgroups_dict:
        raise ValueError("workgroups_dict cannot be empty")
    
    author_user = user
    
    # Читаем данные спринтов из Excel файла
    df_sprints = read_demo_data('TaskSprintModel')
    created_sprints = {}
    
    for index, row in df_sprints.iterrows():
        slug = row['slug']
        name = row['name']
        target = row.get('target', '')
        expected_result_raw = row.get('expected_result', '')
        status = row.get('status', 'new')
        duration = int(row.get('duration', 7))
        workgroup_slugs_raw = row['workgroup_slug']
        time_start = row.get('time_start')  # время начала для in_process спринтов
        
        # Обрабатываем expected_result - разделяем по запятой и очищаем
        if expected_result_raw:
            expected_result = [item.strip() for item in str(expected_result_raw).split(',') if item.strip()]
        else:
            expected_result = []
        
        # Обрабатываем workgroup_slugs - разделяем по запятой
        workgroup_slugs = [slug.strip() for slug in str(workgroup_slugs_raw).split(',') if slug.strip()]
        
        # Проверяем, что все проекты существуют
        valid_workgroups = []
        for workgroup_slug in workgroup_slugs:
            if workgroup_slug in workgroups_dict:
                valid_workgroups.append(workgroups_dict[workgroup_slug])
            else:
                raise ValidationError(f"Warning: workgroup_slug '{workgroup_slug}' not found for sprint '{slug}'. Skipping this project.")
        
        if not valid_workgroups:
            raise ValidationError(f"Warning: No valid workgroups found for sprint '{slug}'. Skipping sprint.")
        
        # Вычисляем begin_date для спринтов в статусе 'in_process'
        begin_date = None
        if status == 'in_process':
            today = timezone.now().date()
            today_weekday = today.weekday()  # 0 = понедельник, 6 = воскресенье
            
            # Определяем понедельник для начала спринта согласно условиям:
            # Пн, Вт, Ср (0, 1, 2) - понедельник прошлой недели
            # Чт, Пт, Сб, Вс (3, 4, 5, 6) - понедельник этой недели
            if today_weekday <= 2:  # Понедельник, Вторник, Среда
                # Понедельник прошлой недели
                sprint_monday = today - datetime.timedelta(days=today_weekday + 7)
            else:  # Четверг, Пятница, Суббота, Воскресенье
                # Понедельник этой недели
                sprint_monday = today - datetime.timedelta(days=today_weekday)
            
            begin_date = timezone.make_aware(
                datetime.datetime.combine(sprint_monday, time_start)
            )
        with transaction.atomic():
            # Создаем спринт
            sprint = TaskSprintModel.objects.create(
                name=name,
                target=target,
                expected_result=expected_result,
                status=status,
                duration=duration,
                begin_date=begin_date,
                author=author_user,
                is_demo=True
            )
            
            # Создаем связи с проектами через SprintProjectThroughModel
            for workgroup in valid_workgroups:
                SprintProjectThroughModel.objects.create(
                    sprint=sprint,
                    project=workgroup
                )
            
            # Сохраняем созданный спринт в словарь
            created_sprints[slug] = sprint
    
    return created_sprints


def delete_demo_task_execution_time(contractor_id) -> int:
    """
    Удаляет демо-трудозатраты, связанные с указанной организацией.
    """
    
    if not contractor_id:
        return 0
    
    # Получаем демо-трудозатраты через задачи указанной организации
    demo_execution_times = TaskExecutionTimeModel.objects.filter(
        task__organization__pk=contractor_id,
        is_demo=True,
        is_active=True
    )
    
    count = demo_execution_times.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Мягкое удаление трудозатрат
    demo_execution_times.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def delete_demo_tasks(contractor_id) -> int:
    """
    Удаляет все задачи из демо-проектов указанной организации.
    """
    
    if not contractor_id:
        return 0
    
    # Сначала находим демо-проекты указанной организации
    demo_workgroups = WorkgroupModel.objects.filter(
        organization__pk=contractor_id,
        is_demo=True,
        is_active=True
    )
    
    if not demo_workgroups.exists():
        return 0
    
    # Получаем все задачи (включая не-демо) из найденных демо-проектов
    tasks_to_delete = TaskModel.objects.filter(
        project__in=demo_workgroups,
        is_active=True
    )
    
    count = tasks_to_delete.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Физически удаляем связанные объекты
    TaskVisor.objects.filter(task__in=tasks_to_delete).delete()
    TaskCooperator.objects.filter(task__in=tasks_to_delete).delete()
    
    # Мягкое удаление задач
    tasks_to_delete.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def delete_demo_sprints(contractor_id) -> int:
    """
    Удаляет демо-спринты, связанные с указанной организацией.
    """
    
    if not contractor_id:
        return 0
    
    # Получаем демо-спринты, связанные с проектами указанной организации
    demo_sprints_queryset = TaskSprintModel.objects.filter(
        projects__organization__pk=contractor_id,
        is_demo=True,
        is_active=True
    ).distinct()
    
    # Сохраняем список спринтов перед удалением связей
    demo_sprints_list = list(demo_sprints_queryset)
    count = len(demo_sprints_list)
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Физически удаляем связи спринтов с проектами
    SprintProjectThroughModel.objects.filter(
        sprint__in=demo_sprints_list
    ).delete()
    
    # Мягкое удаление спринтов - обновляем каждый спринт отдельно
    for sprint in demo_sprints_list:
        sprint.is_active = False
        sprint.deleted_at = current_time
        sprint.save(update_fields=['is_active', 'deleted_at'])
    
    return count


def delete_demo_workgroups(contractor_id):
    """
    Удаляет демо-проекты, принадлежащие указанной организации.
    """
    
    if not contractor_id:
        return 0
    
    # Получаем демо-проекты указанной организации
    demo_workgroups = WorkgroupModel.objects.filter(
        organization__pk=contractor_id,
        is_demo=True,
        is_active=True
    )
    
    count = demo_workgroups.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Физически удаляем участников проектов
    WorkgroupMembersModel.objects.filter(work_group__in=demo_workgroups).delete()
    
    # Мягкое удаление проектов
    demo_workgroups.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def delete_demo_users(contractor_id):
    """
    Удаляет демо-пользователей, которые являются участниками указанной организации.
    """
    contractor_instance = ContractorModel.objects.get(
        pk=contractor_id, 
        is_active=True
    )

    # Получаем демо-пользователей, которые участвуют в указанной организации
    demo_profiles = ProfileModel.objects.filter(
        is_demo=True, 
        is_active=True,
        contractor_profile__contractor=contractor_instance,
        contractor_profile__is_active=True
    ).distinct()
    
    count = demo_profiles.count()
    
    if count == 0:
        return 0
    
    demo_users = CustomUser.objects.filter(profile__in=demo_profiles, is_active=True)
    
    # Физически удаляем связанные объекты
    AccessGroupMemberThroughModel.objects.filter(
        member__user__in=demo_profiles,
        member__contractor=contractor_instance,
        is_active=True
    ).delete()
    
    ContractorProfileModel.objects.filter(
        user__in=demo_profiles,
        contractor=contractor_instance,
        is_active=True
    ).delete()
    
    # Мягкое удаление пользователей и профилей (избегаем ошибок БД)
    current_time = timezone.now()
    
    demo_profiles.update(
        is_active=False,
        deleted_at=current_time
    )
    demo_users.update(is_active=False)
    return count


def create_demo_objectives(profile_id, contractor_id, users_dict):
    """
    Создает демо-цели ОКР.
    """
    from bpms.okr.models import ObjectivesModel

    df_objectives = read_demo_data('ObjectivesModel')
    created_objectives = {}
    
    current_year = timezone.now().year
    
    for index, row in df_objectives.iterrows():
        slug = row['slug']
        operator_slug = row.get('operator')
        objective = row['objective']
        date_start_raw = row['date_start']
        date_end_raw = row['date_end']
        value_efforts_id = row.get('value_efforts')
        status_id = row.get('status', 'as_planned')
        notification_id = row.get('notification', 'quarterly')
        
        operator = users_dict[operator_slug]
        
        # Обрабатываем даты - берем день и месяц из Excel, год - текущий
        original_date_start = pd.to_datetime(date_start_raw).date()
        date_start = datetime.date(current_year, original_date_start.month, original_date_start.day)
        
        original_date_end = pd.to_datetime(date_end_raw).date()
        date_end = datetime.date(current_year, original_date_end.month, original_date_end.day)
        
        with transaction.atomic():
            objective_obj = ObjectivesModel.objects.create(
                organization_id=contractor_id,
                owner_id=profile_id,
                operator=operator,
                objective=objective,
                date_start=date_start,
                date_end=date_end,
                value_efforts_id=value_efforts_id,
                status_id=status_id,
                notification_id=notification_id,
                author_id=profile_id,
                is_demo=True
            )
            created_objectives[slug] = objective_obj
    return created_objectives


def create_demo_key_results(profile_id, contractor_id, users_dict, objectives_dict):
    """
    Создает демо-ключевые результаты ОКР.
    """
    from bpms.okr.models import KeyResultsModel, KeyResultMetricsModel
    
    df_key_results = read_demo_data('KeyResultsModel')
    created_key_results = {}
    
    current_year = timezone.now().year
    
    for index, row in df_key_results.iterrows():
        slug = row['slug']
        objective_slug = row['objective_slug']
        operator_slug = row.get('operator')
        description = row['description']
        metrics_name = row.get('metrics')
        base = float(row.get('base', 0))
        plan = float(row.get('plan', 0))
        fact = float(row.get('fact', 0))
        date_start_raw = row.get('date_start')
        date_end_raw = row.get('date_end')
        
        # Проверяем существование цели
        if objective_slug not in objectives_dict:
            raise ValidationError(f"Warning: objective_slug '{objective_slug}' not found for key result '{slug}'. Skipping.")
        
        objective = objectives_dict[objective_slug]
        operator = users_dict[operator_slug]
        
        metrics = None
        metrics, created = KeyResultMetricsModel.objects.get_or_create(
            name_ru=metrics_name,
            contractor_id=contractor_id,
            is_active=True,
            defaults={
                'author_id': profile_id,
                'is_demo': True
            }
        )
        # Обрабатываем даты - берем день и месяц из Excel, год - текущий
        original_date_start = pd.to_datetime(date_start_raw).date()
        date_start = datetime.date(current_year, original_date_start.month, original_date_start.day)
        
        original_date_end = pd.to_datetime(date_end_raw).date()
        date_end = datetime.date(current_year, original_date_end.month, original_date_end.day)
        
        with transaction.atomic():
            key_result = KeyResultsModel.objects.create(
                objective=objective,
                description=description,
                operator=operator,
                metrics=metrics,
                base=base,
                plan=plan,
                fact=fact,
                date_start=date_start,
                date_end=date_end,
                author_id=profile_id,
                is_demo=True
            )
            created_key_results[slug] = key_result
    return created_key_results


def delete_demo_key_results(contractor_id) -> int:
    """
    Удаляет ключевые результаты, связанные с демо-целями указанной организации.
    """
    from bpms.okr.models import KeyResultsModel, ObjectivesModel
    
    if not contractor_id:
        return 0
    
    # Сначала находим демо-цели указанной организации
    demo_objectives = ObjectivesModel.objects.filter(
        organization__pk=contractor_id,
        is_demo=True,
        is_active=True
    )
    
    if not demo_objectives.exists():
        return 0
    
    # Получаем все ключевые результаты (включая не-демо) из найденных демо-целей
    key_results_to_delete = KeyResultsModel.objects.filter(
        objective__in=demo_objectives,
        is_active=True
    )
    
    count = key_results_to_delete.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    key_results_to_delete.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def delete_demo_objectives(contractor_id) -> int:
    """
    Удаляет демо-цели ОКР, связанные с указанной организацией.
    """
    from bpms.okr.models import ObjectivesModel

    demo_objectives = ObjectivesModel.objects.filter(
        organization__pk=contractor_id,
        is_demo=True,
        is_active=True
    )
    
    count = demo_objectives.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Мягкое удаление целей
    demo_objectives.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def delete_demo_key_result_metrics(contractor_id) -> int:
    """
    Удаляет демо-метрики ключевых результатов, связанные с указанной организацией.
    """
    from bpms.okr.models import KeyResultsModel, KeyResultMetricsModel
   
    # Получаем демо-метрики указанной организации
    demo_metrics = KeyResultMetricsModel.objects.filter(
        contractor__pk=contractor_id,
        is_demo=True,
        is_active=True
    )
    
    count = demo_metrics.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Мягкое удаление метрик
    demo_metrics.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def create_demo_task_execution_time(sprints_dict: dict, tasks_dict: dict, users_dict: dict):
    """
    Создает демо-трудозатраты на основе данных из листа 'TaskExecutionTimeModel' Excel файла.
    """
    
    if not tasks_dict:
        raise ValueError("tasks_dict cannot be empty")
    
    if not users_dict:
        raise ValueError("users_dict cannot be empty")
    
    # Читаем данные трудозатрат из Excel файла
    df_execution_time = read_demo_data('TaskExecutionTimeModel')
    created_execution_times = {}
    
    for index, row in df_execution_time.iterrows():
        slug = row['slug']
        sprint_slug = row.get('sprint_slug')
        task_slug = row['task_slug']
        user_slug = row['user_slug']
        work_type_id = row['work_type_id']
        hours = float(row['hours'])
        description = row.get('description', '')
        days_after_task_start = int(row['days_after_task_start'])
        
        # Проверяем существование задачи
        if task_slug not in tasks_dict:
            raise ValidationError(f"Warning: task_slug '{task_slug}' not found for execution time '{slug}'. Skipping.")
        
        task = tasks_dict[task_slug]
        
        # Проверяем существование пользователя
        if user_slug not in users_dict:
            raise ValidationError(f"Warning: user_slug '{user_slug}' not found for execution time '{slug}'. Skipping.")
        
        user = users_dict[user_slug]
        
        # Проверяем существование спринта (опционально)
        sprint = None
        if sprint_slug and sprint_slug in sprints_dict:
            sprint = sprints_dict[sprint_slug]
        
        # Вычисляем дату трудозатрат на основе date_start_plan задачи
        if not task.date_start_plan:
            raise ValidationError(f"Warning: task '{task_slug}' has no date_start_plan. Cannot calculate execution time date.")
        
        # days_after_task_start: 1 = первый день задачи, 2 = второй день и т.д.
        execution_date = task.date_start_plan.date() + datetime.timedelta(days=days_after_task_start - 1)
        
        with transaction.atomic():
            # Вычисляем duration из hours (как в сериализаторе TaskExecutionTimeModelCreateSerializer)
            duration = int(Decimal(str(hours)) * 3600)
            # Создаем трудозатраты
            execution_time = TaskExecutionTimeModel.objects.create(
                task=task,
                date=execution_date,
                work_type_id=work_type_id,
                hours=hours,
                duration=duration,
                measure_unit_id='hours',
                description=description,
                author=user,
                user=user,
                is_demo=True
            )
            
            # Сохраняем созданную трудозатрату в словарь
            created_execution_times[slug] = execution_time
    
    return created_execution_times


def create_demo_tasks(user, contractor, workgroups_dict: dict, sprints_dict: dict, users_dict: dict):
    """
    Создает демо-задачи на основе данных из листа 'TaskModel' Excel файла.
    """
        
    if not contractor:
        raise ValueError("contractor cannot be empty")
    
    if not workgroups_dict:
        raise ValueError("workgroups_dict cannot be empty")
    
    author_user = user
    
    # Читаем данные задач из Excel файла
    df_tasks = read_demo_data('TaskModel')
    created_tasks = {}
    
    # Переменная для отслеживания последней даты окончания (для последовательности задач)
    last_deadline = None
    
    for index, row in df_tasks.iterrows():
        slug = row['slug']
        name = row['name']
        description = row.get('description', '')
        result = row.get('result', '')
        status = row.get('status', 'new')
        workgroup_slug = row['workgroup_slug']
        sprint_slug = row.get('sprint_slug')
        task_type = row.get('task_type', 'task')
        operator_slug = row.get('operator')
        cooperators_raw = row.get('cooperators', '')
        visors_raw = row.get('visors', '')
        time_start = row.get('time_start')
        time_end = row.get('time_end')
        duration_days = int(row.get('duration', 1))
        
        # Проверяем существование проекта
        if workgroup_slug not in workgroups_dict:
            raise ValidationError(f"Warning: workgroup_slug '{workgroup_slug}' not found for task '{slug}'. Skipping.")
        
        project = workgroups_dict[workgroup_slug]
        
        # Получаем спринт если указан
        sprint = None
        if sprint_slug and sprint_slug in sprints_dict:
            sprint = sprints_dict[sprint_slug]
        
        # Получаем оператора
        operator = None
        if operator_slug and operator_slug in users_dict:
            operator = users_dict[operator_slug]
        
        # Обрабатываем cooperators
        cooperators_list = []
        if cooperators_raw:
            cooperator_slugs = [slug.strip() for slug in str(cooperators_raw).split(',') if slug.strip()]
            for cooperator_slug in cooperator_slugs:
                if cooperator_slug in users_dict:
                    cooperators_list.append(users_dict[cooperator_slug])
                else:
                    raise ValidationError(f"Warning: cooperator_slug '{cooperator_slug}' not found for task '{slug}'. Skipping this cooperator.")
        
        # Обрабатываем visors
        visors_list = []
        if visors_raw:
            visor_slugs = [slug.strip() for slug in str(visors_raw).split(',') if slug.strip()]
            for visor_slug in visor_slugs:
                if visor_slug in users_dict:
                    visors_list.append(users_dict[visor_slug])
                else:
                    raise ValidationError(f"Warning: visor_slug '{visor_slug}' not found for task '{slug}'. Skipping this visor.")
        
        # Вычисляем даты задач
        current_date = timezone.now().date()
        
        # Для первой задачи date_start_plan = текущая дата
        if last_deadline is None:
            date_start_plan = timezone.make_aware(
                datetime.datetime.combine(current_date, time_start)
            )
        else:
            date_start_plan = timezone.make_aware(
                datetime.datetime.combine(last_deadline.date(), time_start)
            )
        
        # Вычисляем dead_line: date_start_plan + duration дней + time_end
        end_date = date_start_plan.date() + datetime.timedelta(days=duration_days)
        dead_line = timezone.make_aware(
            datetime.datetime.combine(end_date, time_end)
        )
        
        # Обновляем last_deadline для следующей задачи
        last_deadline = dead_line
        
        with transaction.atomic():
            # Создаем задачу
            task = TaskModel.objects.create(
                name=name,
                description=description,
                result=result,
                status_id=status,
                organization=contractor,
                project=project,
                sprint=sprint,
                owner=author_user,
                operator=operator,
                author=author_user,
                date_start_plan=date_start_plan,
                dead_line=dead_line,
                is_demo=True,
                task_type_id=task_type
            )
            
            # Назначаем cooperators
            for cooperator in cooperators_list:
                TaskCooperator.objects.create(
                    task=task,
                    user=cooperator,
                    status_id=status
                )
            
            # Назначаем visors
            for visor in visors_list:
                TaskVisor.objects.create(
                    task=task,
                    user=visor
                )
            
            # Сохраняем созданную задачу в словарь
            created_tasks[slug] = task
    
    return created_tasks


def create_demo_calendars(workgroups_dict: dict):
    """
    Создает демо-календари на основе данных из листа 'CalendarModel' Excel файла.
    """
    
    if not workgroups_dict:
        raise ValueError("workgroups_dict cannot be empty")
    
    created_calendars = {}
    
    # Читаем данные календари из Excel файла
    df_calendars = read_demo_data('CalendarModel')
    
    for index, row in df_calendars.iterrows():
        slug = row['slug']
        workgroup_slug = row['workgroup_slug']
        
        # Проверяем существование проекта
        if workgroup_slug not in workgroups_dict:
            raise ValidationError(f"Warning: workgroup_slug '{workgroup_slug}' not found for calendar '{slug}'. Skipping.")
        
        project = workgroups_dict[workgroup_slug]
        
        with transaction.atomic():
            # Создаем календарь через функцию get_or_create_related_calendar
            calendar = get_or_create_related_calendar('НЕ ТРЕБУЕТСЯ', project.id, False)
            calendar.is_demo = True
            calendar.save(update_fields=('is_demo',))
            
            # Сохраняем созданный календарь в словарь
            created_calendars[slug] = calendar
    
    return created_calendars


def create_demo_calendar_events(calendars_dict):
    """
    Создает демо-события на основе данных из листа 'EventCalendarModel' Excel файла.
    """
    
    if not calendars_dict:
        raise ValueError("calendars_dict cannot be empty")
    
    # Читаем данные событий из Excel файла
    df_events = read_demo_data('EventCalendarModel')
    created_events = {}
    
    for index, row in df_events.iterrows():
        slug = row['slug']
        calendar_slug = row['calendar_slug']
        event_type = row['event_type']
        name = row.get('name', '')
        description = row.get('description', '')
        days_after_project_start = int(row['days_after_project_start'])
        time_start = row['time_start']
        time_end = row['time_end']
        
        # Проверяем существование календаря
        if calendar_slug not in calendars_dict:
            raise ValidationError(f"Warning: calendar_slug '{calendar_slug}' not found for event '{slug}'. Skipping.")
        
        calendar = calendars_dict[calendar_slug]
        
        # Получаем проект, связанный с календарем
        project = calendar.related_object
        if not project:
            raise ValidationError(f"Warning: No project found for calendar '{calendar_slug}' and event '{slug}'. Skipping.")
        
        # Вычисляем start_at: дата начала проекта + количество дней + время
        project_start_date = project.date_start_plan.date()
        event_start_date = project_start_date + datetime.timedelta(days=(days_after_project_start - 1))
        start_at = timezone.make_aware(
            datetime.datetime.combine(event_start_date, time_start)
        )
        
        # Вычисляем end_at: та же дата + время окончания
        end_at = timezone.make_aware(
            datetime.datetime.combine(event_start_date, time_end)
        )
        
        with transaction.atomic():
            # Создаем событие
            event = EventCalendarModel.objects.create(
                name_ru=name,
                description=description,
                start_at=start_at,
                end_at=end_at,
                calendar=calendar,
                event_type_id=event_type,
                author=project.author,
                is_demo=True
            )
            
            # Сохраняем созданное событие в словарь
            created_events[slug] = event
    
    return created_events


def delete_demo_calendar_events(profile_id):
    """
    Удаляет все события из демо-календарей, созданных переданным пользователем.
    """
    
    # Сначала находим демо-календари, созданные пользователем
    demo_calendars = CalendarModel.objects.filter(
        author_id=profile_id,
        is_demo=True,
        is_active=True
    )
    
    if not demo_calendars.exists():
        return 0
    
    # Получаем все события (включая не-демо) из найденных демо-календарей
    events_to_delete = EventCalendarModel.objects.filter(
        calendar__in=demo_calendars,
        is_active=True
    )
    
    count = events_to_delete.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Мягкое удаление всех событий
    events_to_delete.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count


def delete_demo_calendars(profile_id):
    """
    Удаляет демо-календари, созданные пользователем.
    """
    
    # Получаем демо-календари
    demo_calendars = CalendarModel.objects.filter(
        author_id=profile_id,
        is_active=True
    )
    
    count = demo_calendars.count()
    
    if count == 0:
        return 0
    
    current_time = timezone.now()
    
    # Мягкое удаление календарей
    demo_calendars.update(
        is_active=False,
        deleted_at=current_time
    )
    
    return count




def create_demo_data(profile_id):
    """
    Создает все демо-данные для указанного пользователя.
    """
    result = {}
    
    user = ProfileModel.objects.get(pk=profile_id)
    contractor = user.current_contractor
    if not contractor:
        raise ValidationError(f"У пользователя '{profile_id}' не выбрана текущая организация.")
    
    if contractor.has_demo_data:
        raise ValidationError(f"У организации '{contractor.name}' уже установлены демо-данные.")

    # Проверяем, что пользователь является директором этой организации
    is_director = ContractorProfileModel.objects.filter(
        user=user,
        contractor=contractor,
        director=True,
        is_active=True
    ).exists()
    
    if not is_director:
        raise ValidationError(f"Пользователь '{profile_id}' не является директором организации '{contractor.name}'.")

    with transaction.atomic():
        # Создаем демо-пользователей
        users = create_demo_users(contractor)
        result['users'] = users
        
        # Создаем демо-проекты
        workgroups = create_demo_workgroups(user, contractor, users)
        result['workgroups'] = workgroups
        
        # Создаем демо-спринты
        sprints = create_demo_sprints(user, workgroups)
        result['sprints'] = sprints
        
        # Создаем демо-задачи
        tasks = create_demo_tasks(user, contractor, workgroups, sprints, users)
        result['tasks'] = tasks
        
        # Создаем демо-трудозатраты
        execution_times = create_demo_task_execution_time(sprints, tasks, users)
        result['execution_times'] = execution_times
        
        # Создаем демо-календари
        calendars = create_demo_calendars(workgroups)
        result['calendars'] = calendars
        
        # Создаем демо-события календаря
        calendar_events = create_demo_calendar_events(calendars)
        result['calendar_events'] = calendar_events

        # Создаем демо-цели ОКР
        objectives = create_demo_objectives(profile_id, contractor.id, users)
        result['objectives'] = objectives
        
        # Создаем демо-ключевые результаты ОКР
        key_results = create_demo_key_results(profile_id, contractor.id, users, objectives)
        result['key_results'] = key_results

        contractor.has_demo_data = True
        contractor.save()
    
    return result


def delete_demo_data(profile_id) -> dict:
    """
    Удаляет демо-данные для указанного пользователя.
    """
    result = {}
    
    try:
        user = ProfileModel.objects.get(pk=profile_id)
    except ProfileModel.DoesNotExist:
        raise ValueError(f"Profile with id {profile_id} does not exist")
    
    # Получаем ID первой организации, где данный пользователь является директором и установлена галочка has_demo_data
    contractor = ContractorModel.objects.filter(
        has_demo_data=True,
        is_active=True,
        contractor_profile__user=user,
        contractor_profile__director=True,
        contractor_profile__is_active=True
    ).distinct().first()
    
    if not contractor:
        return {
            'calendar_events': 0,
            'calendars': 0,
            'execution_times': 0,
            'tasks': 0,
            'sprints': 0,
            'workgroups': 0,
            'users': 0,
            'key_results': 0,
            'objectives': 0,
            'key_result_metrics': 0
        }
    
    contractor_id = contractor.id
    
    with transaction.atomic():
        # Удаляем демо-события календаря (сначала, так как они зависят от календарей)
        calendar_events_count = delete_demo_calendar_events(profile_id)
        result['calendar_events'] = calendar_events_count
        
        # Удаляем демо-календари (затем, так как они зависят от проектов)
        calendars_count = delete_demo_calendars(profile_id)
        result['calendars'] = calendars_count
        
        # Удаляем демо-трудозатраты (затем, так как они зависят от задач)
        execution_times_count = delete_demo_task_execution_time(contractor_id)
        result['execution_times'] = execution_times_count
        
        # Удаляем демо-задачи (затем, так как они зависят от спринтов и проектов)
        tasks_count = delete_demo_tasks(contractor_id)
        result['tasks'] = tasks_count
        
        # Удаляем демо-спринты (затем, так как они зависят от проектов)
        sprints_count = delete_demo_sprints(contractor_id)
        result['sprints'] = sprints_count
        
        # Удаляем демо-проекты (затем, так как они содержат пользователей)
        workgroups_count = delete_demo_workgroups(contractor_id)
        result['workgroups'] = workgroups_count
        
        # Удаляем демо-пользователей из указанной организации
        users_count = delete_demo_users(contractor_id)
        result['users'] = users_count

        # Удаляем демо-ключевые результаты ОКР (сначала, так как они зависят от целей)
        key_results_count = delete_demo_key_results(contractor_id)
        result['key_results'] = key_results_count
        
        # Удаляем демо-цели ОКР
        objectives_count = delete_demo_objectives(contractor_id)
        result['objectives'] = objectives_count
        
        # Удаляем демо-метрики ключевых результатов
        key_result_metrics_count = delete_demo_key_result_metrics(contractor_id)
        result['key_result_metrics'] = key_result_metrics_count

        contractor.has_demo_data = False
        contractor.save()   

    return result

