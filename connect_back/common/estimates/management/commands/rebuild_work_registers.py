from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef

from bpms.tasks.models import TaskExecutionTimeModel
from help_desk.models import HelpDeskWorkLogModel
from common.estimates.models import AccumulationRegister


class Command(BaseCommand):
    help = (
        "Создает недостающие записи регистра накопления для "
        "TaskExecutionTimeModel и HelpDeskWorkLogModel."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            choices=['task_execution_time', 'help_desk_work_log', 'all'],
            default='all',
            help='Какие модели обрабатывать: task_execution_time, help_desk_work_log, all',
        )

    def handle(self, *args, **options):
        model_name = options['model']
        batch_size = 500

        if model_name in ['task_execution_time', 'all']:
            task_queryset = TaskExecutionTimeModel.objects.filter(
                is_active=True,
                task__isnull=False,
                task__project__isnull=False,
            )
            self._process_queryset(
                queryset=task_queryset,
                select_related=['task', 'task__project', 'measure_unit', 'work_type', 'user'],
                label='TaskExecutionTimeModel',
                batch_size=batch_size,
            )

        if model_name in ['help_desk_work_log', 'all']:
            worklog_queryset = HelpDeskWorkLogModel.objects.filter(
                is_active=True,
                ticket__isnull=False,
                ticket__customer_card__isnull=False,
            )
            self._process_queryset(
                queryset=worklog_queryset,
                select_related=['ticket', 'ticket__customer_card', 'user'],
                label='HelpDeskWorkLogModel',
                batch_size=batch_size,
            )

    def _missing_register_queryset(self, queryset):
        return queryset.annotate(
            has_register=Exists(
                AccumulationRegister.objects.filter(
                    registrar_row_uuid=OuterRef('pk')
                )
            )
        ).filter(has_register=False)

    def _yield_batches(self, iterator, batch_size):
        batch = []
        for item_id in iterator:
            batch.append(item_id)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _process_queryset(self, queryset, select_related, label, batch_size):
        missing_queryset = self._missing_register_queryset(queryset).order_by('pk')

        total_count = missing_queryset.count()
        if total_count == 0:
            self.stdout.write(self.style.NOTICE(f'{label}: нет записей без регистра'))
            return

        self.stdout.write(self.style.NOTICE(
            f'{label}: найдено {total_count} записей без регистра'
        ))

        processed_count = 0
        id_iterator = missing_queryset.values_list('pk', flat=True).iterator(chunk_size=batch_size)
        for batch_ids in self._yield_batches(id_iterator, batch_size):
            batch_queryset = queryset.filter(pk__in=batch_ids).select_related(
                *select_related
            ).order_by('pk')

            with transaction.atomic():
                for record in batch_queryset:
                    record.build_register_entry(created=True)
                    processed_count += 1

            self.stdout.write(f'{label}: {processed_count}/{total_count}')
