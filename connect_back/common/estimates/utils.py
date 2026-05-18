from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Exists, OuterRef

from bpms.tasks.models import TaskExecutionTimeModel, TaskModel
from help_desk.models import HelpDeskTicketModel, HelpDeskWorkLogModel

from .models import AccumulationRegister


def rebuild_execution_time_registers():
    """
    Пересоздает записи AccumulationRegister для трудозатрат, чтобы period писался в UTC-полночь.
    """
    results = {
        "tasks": {"processed": 0, "missing": 0},
    }

    mapping = (
        ("tasks", ContentType.objects.get_for_model(TaskModel), TaskExecutionTimeModel),
    )

    for key, registrar_ct, exec_model in mapping:
        regs = AccumulationRegister.objects.filter(registrar__ct=registrar_ct).iterator()
        for reg in regs:
            try:
                exec_obj = exec_model.objects.get(pk=reg.registrar_row_uuid)
            except exec_model.DoesNotExist:
                results[key]["missing"] += 1
                continue

            # save() пересоздаст запись AccumulationRegister с корректным period
            with transaction.atomic():
                exec_obj.save()
                results[key]["processed"] += 1

    return results


def cleanup_orphaned_helpdesk_work_log_registers():
    """
    Удаляет из AccumulationRegister осиротевшие записи по трудозатратам тикетов
    (registrar_row_uuid указывает на несуществующий HelpDeskWorkLogModel)
    и пересчитывает duration у затронутых тикетов.
    Отбор осиротевших выполняется в БД через NOT EXISTS, без передачи больших списков UUID.
    """
    helpdesk_ticket_ct = ContentType.objects.get_for_model(HelpDeskTicketModel)
    work_log_exists = HelpDeskWorkLogModel.objects.filter(
        pk=OuterRef('registrar_row_uuid')
    )
    orphaned_qs = AccumulationRegister.objects.filter(
        section_id='work_costs',
        doc_fact__ct_id=helpdesk_ticket_ct.id,
        registrar_row_uuid__isnull=False,
    ).exclude(Exists(work_log_exists))

    ticket_ids_recalculated = list(
        orphaned_qs.values_list('doc_fact_id', flat=True).distinct()
    )
    if not ticket_ids_recalculated:
        return {"deleted_count": 0, "ticket_ids_recalculated": []}

    with transaction.atomic():
        deleted_count, _ = orphaned_qs.delete()
        for ticket_id in ticket_ids_recalculated:
            HelpDeskWorkLogModel._recalculate_ticket_duration(ticket_id)

    return {
        "deleted_count": deleted_count,
        "ticket_ids_recalculated": [str(tid) for tid in ticket_ids_recalculated],
    }

