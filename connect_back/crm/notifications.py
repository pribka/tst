from notifications import event_types
from common.catalogs.models import WarehouseModel


def notify_about_update_order(initiator, subj, old_warehouse_id):
    recipients = [subj.user, subj.logistic_manager]
    task = getattr(subj.task_delivery_point, 'task', None)
    if task:
        task_operator = task.operator
        if task_operator:
            recipients.append(task_operator)
        task_owner = task.owner
        if task_owner:
            recipients.append(task_owner)
    # Уведомление кладовщика. Если склад поменялся, сообщить новому кладовщику о новом заказе.
    # Иначе сообщить об изменении заказа.
    warehouse = subj.warehouse
    if warehouse and str(warehouse.pk) == str(old_warehouse_id):
        warehouse_manager = warehouse.manager
        if warehouse_manager:
            recipients.append(warehouse_manager)
    else:
        try:
            old_warehouse = WarehouseModel.objects.get(is_active=True, pk=old_warehouse_id)
        except WarehouseModel.DoesNotExist:
            old_warehouse = None
        if old_warehouse:
            warehouse_manager = warehouse.manager
            if warehouse_manager:
                event_type = event_types.OrderCreated()
                event_type.create_notification(recipients=(warehouse_manager,), subj=subj)

    recipients = set(recipients)
    recipients.discard(None)
    recipients = tuple(recipients)
    event_type = event_types.OrderUpdate()
    event_type.create_notification(recipients=recipients, initiator=initiator, subj=subj)


def notify_about_order_delivered(initiator, subj):
    recipients = list()
    try:
        recipients.append(subj.task_delivery_point.task.owner)
    except AttributeError:
        pass
    subj_user = subj.user
    if subj_user:
        recipients.append(subj_user)
    logistic_manager = subj.logistic_manager
    if logistic_manager:
        recipients.append(logistic_manager)
    contractor = subj.contractor
    if contractor:
        director = contractor.contractor_profile.filter(user__is_active=True, director=True).first()
        if director:
            try:
                recipients.append(director.user.pk)
            except AttributeError:
                pass
    if recipients:
        recipients = set(recipients)
        recipients.discard(None)
        recipients = tuple(recipients)
        event_type = event_types.OrderDelivered()
        event_type.create_notification(recipients=recipients, initiator=initiator, subj=subj)


def notify_logistic_manager_about_new_order(initiator, subj):
    obj = subj.logistic_manager
    recipients = (obj,)
    event_type = event_types.OrderLogisticManager()
    event_type.create_notification(recipients=recipients, initiator=initiator, subj=subj)


def notify_about_new_order(subj):
    from users.models import ProfileModel
    recipients = list(ProfileModel.objects.filter(
        is_active=True,
        temporary_blocked=False,
        c1_roles__can_create_logistic_task=True
    ).values_list('pk', flat=True))
    warehouse = subj.warehouse
    if warehouse:
        warehouse_manager = warehouse.manager
        if warehouse_manager:
            recipients.append(warehouse_manager.pk)
    contractor = subj.contractor
    if contractor:
        director = contractor.contractor_profile.filter(user__is_active=True, director=True).first()
        if director:
            try:
                recipients.append(director.user.pk)
            except AttributeError:
                pass
    recipients = set(recipients)
    recipients.discard(None)
    recipients = tuple(recipients)
    if recipients:
        event_type = event_types.OrderCreated()
        event_type.create_notification(recipients=recipients, subj=subj)


def notify_pay_recipient_about_new_order(subj):
    cash_pay_recipient = subj.cash_pay_recipient
    if cash_pay_recipient:
        event_type = event_types.OrderCreatedCashPayRecipient()
        event_type.create_notification(recipients=(cash_pay_recipient,), subj=subj)
