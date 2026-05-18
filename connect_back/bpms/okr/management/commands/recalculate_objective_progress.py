from django.core.management.base import BaseCommand
from bpms.okr.models import ObjectivesModel


class Command(BaseCommand):
    help = 'Пересчитывает прогресс для всех целей OKR на основе ключевых результатов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--objective-id',
            type=int,
            help='ID конкретной цели для пересчета (если не указан, пересчитываются все цели)',
        )

    def handle(self, *args, **options):
        objective_id = options.get('objective_id')
        
        if objective_id:
            try:
                objective = ObjectivesModel.objects.get(id=objective_id)
                self.stdout.write(f'Пересчитываем прогресс для цели ID {objective_id}...')
                old_progress = objective.progress
                objective.recalculate_progress()
                objective.save(update_fields=['progress'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Прогресс цели "{objective.objective}" обновлен: {old_progress}% -> {objective.progress}%'
                    )
                )
            except ObjectivesModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Цель с ID {objective_id} не найдена')
                )
        else:
            self.stdout.write('Начинаем пересчет прогресса для всех целей...')
            objectives = ObjectivesModel.objects.filter(is_active=True)
            count = objectives.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING('Активные цели не найдены'))
                return
            
            updated_count = 0
            for objective in objectives:
                old_progress = objective.progress
                objective.recalculate_progress()
                objective.save(update_fields=['progress'])
                if old_progress != objective.progress:
                    updated_count += 1
                    self.stdout.write(
                        f'Цель "{objective.objective}": {old_progress}% -> {objective.progress}%'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Пересчет завершен. Обработано целей: {count}, обновлено: {updated_count}'
                )
            ) 