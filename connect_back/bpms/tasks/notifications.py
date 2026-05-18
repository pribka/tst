import uuid

from users.models import ProfileModel
from notifications import event_types

from . import models


def get_task_participants(task):
    """Получает UUID всех участников задачи."""
    recipients = set()
    recipients.add(task.author_id)
    recipients.add(task.owner_id)
    recipients.add(task.operator_id)
    recipients.update(task.visors.all().values_list('pk', flat=True))
    recipients.update(task.cooperators.all().values_list('pk', flat=True))
    return recipients


def get_workgroup_founders_and_moderators(task):
    """Получает UUID основателей и модераторов проекта и команды для задачи.
    Пока только основателей (чтобы уменьшить количество уведомлений)."""
    from bpms.workgroups.models import WorkgroupMembersModel
    
    recipients = set()
    
    # Основатели и модераторы проекта
    if task.project_id:
        project_founders_and_moderators = WorkgroupMembersModel.objects.filter(
            work_group_id=task.project_id,
            is_active=True,
            membership_request_status__code='APPROVED',
            membership_role__code__in=['FOUNDER',]
        ).values_list('member_id', flat=True)
        recipients.update(project_founders_and_moderators)
    
    # Основатели и модераторы команды
    if task.workgroup_id:
        workgroup_founders_and_moderators = WorkgroupMembersModel.objects.filter(
            work_group_id=task.workgroup_id,
            is_active=True,
            membership_request_status__code='APPROVED',
            membership_role__code__in=['FOUNDER',]
        ).values_list('member_id', flat=True)
        recipients.update(workgroup_founders_and_moderators)
    
    return recipients


def notify_about_assign_operator_task(task, initiator):
    if task.task_type_id == 'task':
        event_type = event_types.TaskAssignOperator()
        event_type.create_notification(recipients=(task.operator,), initiator=initiator, subj=task)
    if task.task_type_id == 'logistic':
        event_type = event_types.LogisticTaskAssignOperator()
        event_type.create_notification(recipients=(task.operator,), initiator=initiator, subj=task)
    return 'done.'


def notify_visors_about_assign_operator_task(task, initiator, operator, recipients: tuple = None):
    if not recipients:
        return 'no recipients'
    event_type = event_types.TaskAssignOperatorForVisors()
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task, obj=operator)
    return 'done.'


def notify_visors_about_assign_cooperator_task(task, initiator, operator, recipients: tuple = None):
    if not recipients:
        return 'no recipients'
    event_type = event_types.TaskAssignCooperatorForVisors()
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task, obj=operator)
    return 'done.'


def notify_about_assign_visor_task(task, initiator, recipients: tuple = None):
    if not recipients:
        recipients = set(task.visors.all().values_list('pk', flat=True))
    else:
        recipients = set(recipients)
    recipients.discard(initiator.pk)
    if recipients:
        event_type = event_types.TaskAssignVisor()
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task)
        return 'done.'
    else:
        return 'no visors. Done.'


def notify_about_assign_cooperator_task(task, initiator, recipients: tuple = None):
    if not recipients:
        recipients = set(task.cooperators.all().values_list('pk', flat=True))
    else:
        recipients = set(recipients)
    recipients.discard(initiator.pk)
    if recipients:
        event_type = event_types.TaskAssignCooperator()
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task)
        return 'done.'
    else:
        return 'no cooperators. Done.'


def notify_about_assign_owner_task(task, initiator):
    event_type = event_types.TaskAssignOwner()
    event_type.create_notification(recipients=(task.owner,), initiator=initiator, subj=task)
    return 'done'

def notify_about_new_workgroup_task(task, initiator):
    """Уведомление о создании новой задачи в проекте/команде. Для основателя и модераторов."""
    from bpms.workgroups.models import WorkgroupMembersModel
    
    recipients = set()
    recipients.update(get_workgroup_founders_and_moderators(task))
    task_participants = get_task_participants(task)
    recipients = recipients - task_participants
    recipients.discard(initiator.pk)
    recipients.discard(None)
    
    if recipients:
        event_type = event_types.NewWorkgroupTask()
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task)
        return 'done.'
    else:
        return 'no recipients. Done.'


TASK_STATUS_NOTIFICATION_MAPPING = {
    'in_work': event_types.TaskChangeStatusInWork,
    'on_pause': event_types.TaskChangeStatusOnPause,
    'on_rework': event_types.TaskChangeStatusOnRework,
    'on_check': event_types.TaskChangeStatusOnCheck,
    'completed': event_types.TaskChangeStatusCompleted,
}


def notify_about_new_status(task_id, status_code, initiator_id):
    task = models.TaskModel.objects.get(pk=task_id)
    initiator = ProfileModel.objects.get(pk=initiator_id)
    recipients = get_task_participants(task)
    recipients.update(get_workgroup_founders_and_moderators(task))
    recipients.discard(initiator.pk)
    recipients.discard(None)
    
    if not recipients:
        return 'no recipients'
    
    if task.task_type_id == 'task':
        try:
            event_type = TASK_STATUS_NOTIFICATION_MAPPING.get(status_code)()
        except TypeError:
            event_type = event_types.TaskChangeStatusGeneric()
    elif task.task_type_id == 'logistic':
        event_type = event_types.LogisticTaskChangeStatusGeneric()
    else:
        return 'unsupported task type'
    
    event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task)
    return 'done'


def notify_about_new_description(task, initiator):
    """Уведомление при изменении описания в задаче."""
    recipients = get_task_participants(task)
    recipients.update(get_workgroup_founders_and_moderators(task))
    recipients.discard(initiator.pk)
    recipients.discard(None)
    
    if recipients:
        event_type = event_types.TaskChangeDescription()
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task)
        return 'done'
    else:
        return 'no recipients'


def notify_about_new_cooperator_status(task_cooperator_id, status_code, initiator_id, set_task_status: bool):
    """Оповещение о смене статуса задачи соисполнителя"""
    initiator = ProfileModel.objects.get(pk=initiator_id)
    task = models.TaskCooperator.objects.get(pk=task_cooperator_id).task
    recipients = get_task_participants(task)
    recipients.update(get_workgroup_founders_and_moderators(task))
    recipients.discard(initiator.pk)
    recipients.discard(None)
    if task.task_type_id == 'task':
        event_type = event_types.TaskChangeCooperatorStatusGeneric()
        obj = models.TaskStatusModel.objects.get(code=status_code)
        event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task, obj=obj)
        if set_task_status:
            event_type = event_types.TaskCooperatorSetTaskStatus()
            event_type.create_notification(recipients=tuple(recipients), initiator=initiator, subj=task)
        return 'done'
    else:
        return


def notify_about_set_sprint(task, sprint, initiator):
    event_type = event_types.TaskSetSprint()
    event_type.create_notification(recipients=(task.operator,), initiator=initiator, obj=sprint, subj=task)
    return 'done'


def notify_about_take_auction(task, initiator):
    event_type = event_types.TaskTakeAuction()
    event_type.create_notification(recipients=(task.owner,), initiator=initiator, subj=task)
    return 'done'


def notify_driver_about_start_order(task, order, initiator):
    event_type = event_types.OrderStartForDriver()
    event_type.create_notification(recipients=(task.operator,), initiator=initiator, obj=task, subj=order)


def notify_order_user_about_start_order(task, order, initiator):
    event_type = event_types.OrderStartForOrderUser()
    event_type.create_notification(recipients=(order.user,), initiator=initiator, obj=task, subj=order)


def notify_about_order_in_transit(task, order):
    event_type = event_types.OrderDeliveryInTransit()
    recipients = [order.user_id, task.owner_id]
    contractor = order.contractor
    if contractor:
        director = contractor.contractor_profile.filter(user__is_active=True, director=True).first()
        if director:
            recipients.append(director.user.pk)
    recipients = set(recipients)
    recipients.discard(None)
    recipients = tuple(recipients)
    event_type.create_notification(recipients=recipients, initiator=task.operator, subj=order, obj=task)
    return


def notify_about_update_delivery_points(task, initiator):
    event_type = event_types.UpdateTaskDeliveryPoints()
    recipients = (task.operator,)
    event_type.create_notification(recipients=recipients, initiator=initiator, subj=task)
    return


def notify_about_task_goods_loaded(task_id, warehouse_id, driver_id):
    from common.catalogs.models import WarehouseModel
    task = models.TaskModel.objects.get(pk=task_id)
    warehouse = WarehouseModel.objects.get(pk=warehouse_id)
    driver = ProfileModel.objects.get(pk=driver_id)
    event_type = event_types.TaskGoodsLoaded()
    event_type.create_notification(recipients=(task.owner,), subj=task, obj=warehouse, initiator=driver)
    return 'complete.'
