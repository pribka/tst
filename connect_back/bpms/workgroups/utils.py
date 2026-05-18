import json
from urllib.parse import quote

from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.db.models import Count, Q, Exists, OuterRef
from django.utils import timezone
from django.db import transaction

from django_q.tasks import async_task

from bkz3.settings import (
    DOWNLOADER_PATH,
    FILTER_BY_ORGANIZATIONS,
    SOCKETIO_SYSTEM_CHANNEL,
)
from common.redis import socketio_redis
from common.serializers import AppFileSerializer
from common.utils import get_filter_queryset, order_queryset_from_get_param

from contractor_permissions.utils import contractors_where_user_has_permission

from users.models import ProfileModel

from bpms.chat.models import MessageModel
from bpms.chat.serializers import MessageListSerializer

from bpms.favorites.models import FavoriteModel

from . import models


def get_workgroup_queryset(request):
    queryset = models.WorkgroupModel.objects.filter(is_active=True)
    query_params = getattr(request, 'query_params', None)
    if query_params is None or not query_params:
        query_params = request.GET
    workgroups_name = query_params.get("workgroups_name", None)
    workgroups_type = query_params.get("workgroups_type", None)
    is_project = query_params.get("is_project", None)
    my = query_params.get("my", None)
    # TODO Если функционал публичных проектов и команд уже не нужен, то функцию можно сильно сократить.
    user = request.user.profile
    if my == "1":
        moderator = query_params.get('moderator')
        if moderator == "1":
            workgroup_member = models.WorkgroupMembersModel.objects.filter(
                member=user,
                is_active=True,
                membership_request_status__code="APPROVED",
                membership_role__code__in=('FOUNDER', 'MODERATOR'),
            ).values_list("work_group", flat=True).distinct("work_group")
        else:
            workgroup_member = models.WorkgroupMembersModel.objects.filter(
                member=user,
                is_active=True,
                membership_request_status__code="APPROVED"
            ).values_list("work_group", flat=True).distinct("work_group")
        queryset = queryset.filter(pk__in=workgroup_member, is_active=True).order_by('is_finished', '-created_at')
    else:
        workgroup_member = models.WorkgroupMembersModel.objects.filter(
            member=user,  # Добавила 1.09.2025, чтобы в любом случае видеть только те, где я участник.
            is_active=True,
            membership_request_status__code="APPROVED"
        ).values_list("work_group", flat=True).distinct("work_group")
        permission_lookup = Q(pk__in=workgroup_member)
        visor_orgs = contractors_where_user_has_permission(user.pk, 'workgroups_supervisor', None)
        if visor_orgs:
            permission_lookup = permission_lookup | Q(organization_id__in=visor_orgs)
        queryset = queryset.filter(permission_lookup, is_active=True,).annotate(
            is_user=Count('workgroupmembersmodel__member',
                          filter=Q(workgroupmembersmodel__member=user,
                                   workgroupmembersmodel__is_active=True))).order_by(
            'is_finished', '-is_user', '-created_at'
        )
    lookup = Q()
    if workgroups_name:
        lookup &= Q(name__icontains=workgroups_name)
    if workgroups_type:
        lookup &= Q(workgroups_type=workgroups_type)
    if is_project == "1":
        lookup &= Q(is_project=True)
    if is_project == "0":
        lookup &= Q(is_project=False)

    workgroup_members = models.WorkgroupMembersModel.objects.filter(member=user, work_group=OuterRef('pk'), is_active=True,)
    queryset = queryset.filter(lookup, is_active=True).annotate(
        is_user=Exists(workgroup_members),
    )
    queryset = FavoriteModel.annotate_favorites(queryset)
    queryset = order_queryset_from_get_param(
        request,
        models.WorkgroupModel,
        get_filter_queryset(request, models.WorkgroupModel, queryset)
    )
    if not queryset.ordered:
        queryset = queryset.order_by('is_finished', '-is_user', '-created_at')

    # TODO НИД ХЕЛП МОГ ОШИБИТЬСЯ
    if user.is_support:
        return queryset
    else:
        if FILTER_BY_ORGANIZATIONS:
            # queryset = queryset.filter(Q(is_user__gt=0) | Q(public_or_private=False))
            # queryset = queryset.filter(Q(is_user__gt=0) | (Q(is_project=False) & Q(public_or_private=False)))
            pass
        else:
            queryset = queryset.filter(Q(is_user=True) | (Q(is_project=False) & Q(public_or_private=False)))
        return queryset


def create_workgroup_chat_members(workgroup_id, users_id: tuple):
    workgroup = models.WorkgroupModel.objects.get(pk=workgroup_id)
    linked_chat = workgroup.linked_chat
    if not workgroup.with_chat or not linked_chat:
        return
    chat_members = []
    users = ProfileModel.objects.filter(pk__in=users_id)
    for user in users:
        try:
            member, created = linked_chat.members.filter(is_active=False).get_or_create(
                user=user, chat=linked_chat,
            )
        except IntegrityError:
            continue
        if not created:
            member.last_message_created = timezone.now()
            member.is_active = True
            member.save(update_fields=('is_active', 'last_message_created'))
        chat_members.append(member)
    data = json.dumps(
        {
            'event': 'chat_add_user',
            'data': {
                "chat_uid": str(linked_chat.chat_uid),
                "members": [{"user": str(each.user_id), "is_moderator": str(each.is_moderator)} for each in chat_members],
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_new_chat_author(chat):
    data = json.dumps(
        {
            'event': 'assign_chat_author',
            'data': {
                'chat_uid': chat.chat_uid,
                'chat_author': chat.chat_author.pk
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def send_socketio_about_update_chat_member(chat, members):
    data = json.dumps(
        {
            'event': 'chat_update_members',
            'data': {
                'chat_uid': chat.chat_uid,
                'members': [{'user': str(each[0]), 'is_moderator': str(each[1])} for each in members]
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def delete_workgroup_chat_members(workgroup: models.WorkgroupModel, users_id: tuple):
    linked_chat = workgroup.linked_chat
    if not workgroup.with_chat or not linked_chat:
        return
    chat_members = linked_chat.members.filter(is_active=True, user__in=users_id)
    for member in chat_members:
        member.is_active = False
        member.save(update_fields=('is_active',))
    data = json.dumps(
        {
            'event': 'chat_delete_user',
            'data': {
                "chat_uid": str(linked_chat.chat_uid),
                "members": [{"user": str(member.user_id)} for member in chat_members]
            }
        },
        cls=DjangoJSONEncoder,
    )
    socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)


def get_serialized_workgroup_logo(instance: models.WorkgroupModel):
    if instance is None or not instance.workgroup_logo_id or not instance.workgroup_logo.is_active:
        return ""
    workgroup_logo = AppFileSerializer(instance=instance.workgroup_logo).data
    if workgroup_logo and DOWNLOADER_PATH is not None:
        workgroup_logo['path'] = workgroup_logo['path'] + quote(f"&target=workgroup_logo&obj={instance.pk}")
    return workgroup_logo


from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from bkz3.settings import TOKEN_FOR_IMPORT_PROJECTS


@csrf_exempt
def import_from_other_system(request):
    data = json.loads(request.body)
    owner = data.pop('owner')
    pk = data.pop('id')
    token = data.pop('token')

    if token != TOKEN_FOR_IMPORT_PROJECTS:
        return HttpResponse('error')

    proj, is_new = models.WorkgroupModel.objects.get_or_create(id=pk, defaults=data)
    if is_new:
        mem = models.ProfileModel.objects.get(pk=owner)
        members_create = models.WorkgroupMembersModel.objects.create(
            member=mem,
            work_group=proj,
            membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER"),
            membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        )
        members_create.save()

    return HttpResponse('ok')


def create_subtasks_from_template(parent_template_task, parent):
    from bpms.tasks.serializers import CreateTaskSerializer

    if parent_template_task.is_leaf_node():
        return parent.date_start_plan + parent_template_task.duration
    
    template = parent_template_task.template
    next_level = parent_template_task.level + 1
    template_tasks = template.tasks.filter(level=next_level, parent=parent_template_task).order_by('order')
    date_start_plan = parent.date_start_plan

    for template_task in template_tasks:
        task_data = {}
        task_data['name'] = template_task.name
        task_data['result'] = template_task.result
        task_data['description'] = template_task.description
        task_data['task_type'] = template_task.task_type
        task_data['parent'] = parent
        task_data['project'] = parent.project
        task_data['organization'] = parent.project.organization
        task_data['date_start_plan'] = date_start_plan

        serializer = CreateTaskSerializer(data=task_data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        # Продолжительность задачи считается либо как сумма продолжительности подзадач,
        # либо как указанная продолжительность текущей задачи. Берется бОльшее значение.
        dead_line_from_subtasks = create_subtasks_from_template(template_task, task)
        dead_line_from_self_duration = date_start_plan + template_task.duration
        if dead_line_from_subtasks > dead_line_from_self_duration:
            dead_line = dead_line_from_subtasks
        else:
            dead_line = dead_line_from_self_duration

        task.dead_line = dead_line
        task.save(update_fields=('dead_line',))
        date_start_plan = dead_line

    return date_start_plan


def create_project_from_template(project, template):
    from bpms.tasks.serializers import CreateTaskSerializer

    # задачи верхнего уровня
    template_tasks = template.tasks.filter(level=0).order_by('order')
    # инициализируем дату начала первой задачи
    date_start_plan = project.date_start_plan
    for template_task in template_tasks:
        task_data = {}
        task_data['name'] = template_task.name
        task_data['result'] = template_task.result
        task_data['description'] = template_task.description
        task_data['task_type'] = template_task.task_type
        task_data['project'] = project
        task_data['organization'] = project.organization
        task_data['date_start_plan'] = date_start_plan
        serializer = CreateTaskSerializer(data=task_data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()

        dead_line = create_subtasks_from_template(template_task, task)
        task.dead_line = dead_line
        task.save(update_fields=('dead_line',))

        date_start_plan = dead_line
    # крайний срок проекта - это крайний срок последней задачи проекта.
    project.dead_line = date_start_plan
    project.save(update_fields=('dead_line',))
     

def swap_task_order(first_task, second_task):
    """Меняет местами свойство order у задач шаблона проекта."""
    first_order = first_task.order
    second_order = second_task.order
    with transaction.atomic():
        first_task.order = second_order
        first_task.save(update_fields=('order',))
        second_task.order = first_order
        second_task.save(update_fields=('order',))


def set_workgroup_members(workgroup, profiles: set):
    """
    Устанавливает участников проекта/рабочей группы.
    workgroup - рабочая группа/проект (объект).
    profiles - список id профилей пользователей
    """
    default_status = models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
    members_in_group = workgroup.workgroupmembersmodel_set.filter(
        is_active=True,
        membership_request_status=default_status,
    ).values_list(
        'member_id',
        flat=True
    )

    users_id = [
        str(_) for _ in ProfileModel.objects.filter(id__in=profiles).exclude(id__in=members_in_group).values_list(
            'pk', flat=True
        )
    ]
    default_role = models.WorkgroupMembershipRole.objects.get(code="MEMBER")
    default_data = {
        'membership_request_status': default_status,
        'membership_role': default_role,
        'is_active': True,
    }
    members = []
    for user_id in users_id:
        member, created = models.WorkgroupMembersModel.objects.update_or_create(
            member_id=user_id,
            work_group=workgroup,
            defaults=default_data,
        )
        members.append(member)
    if workgroup.with_chat and workgroup.linked_chat:
        transaction.on_commit(lambda: create_workgroup_chat_members(str(workgroup.pk), tuple(users_id)))
    return members


def compute_workgroup_progress(workgroup):
    """
    Возвращает прогресс выполнения задач для рабочей группы или проекта.
    Теперь возвращает int от 0 до 100 (проценты). Если задач нет — 0.
    """
    if workgroup.is_project:
        subtasks = workgroup.project_tasks.filter(is_active=True, task_type='task')
    else:
        subtasks = workgroup.workgroup_tasks.filter(is_active=True, task_type='task')
    if subtasks.exists():
        from bpms.tasks.utils import get_tasks_status_count
        tasks_status = get_tasks_status_count(subtasks)
        percent = int(tasks_status.get('completed', 0) / subtasks.count() * 100)
        return percent
    return 0


def send_message_chat_project(project_id, text: str):
    """Отправляет в связанный чат проекта системное сообщение о завершении проекта"""
    project = models.WorkgroupModel.objects.get(pk=project_id)
    if not project.with_chat:
        return
    chat = project.linked_chat
    if chat:
        message = MessageModel()
        message.chat = chat
        message.is_system = True
        message.created = timezone.now()
        message.text = text
        message.save()
        message_data = MessageListSerializer(message).data
        message_data['chat_uid'] = str(chat.chat_uid)
        message_data['chat_name'] = chat.name
        message_data['is_public'] = chat.is_public
        message_data['is_new'] = True
        data = json.dumps(
            {
                "event": "chat_message",
                "data": message_data,
            },
            cls=DjangoJSONEncoder
        )
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
