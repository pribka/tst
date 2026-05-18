from django.core.management.base import BaseCommand
from bpms.okr.models import KeyResultsModel


class Command(BaseCommand):
    help = 'Пересчитывает прогресс для всех ключевых результатов OKR на основе base, plan и fact'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key-result-id',
            type=int,
            help='ID конкретного ключевого результата для пересчета (если не указан, пересчитываются все КР)',
        )
        parser.add_argument(
            '--objective-id',
            type=int,
            help='ID цели для пересчета всех связанных ключевых результатов',
        )

    def handle(self, *args, **options):
        key_result_id = options.get('key_result_id')
        objective_id = options.get('objective_id')
        
        if key_result_id:
            try:
                key_result = KeyResultsModel.objects.get(id=key_result_id)
                self.stdout.write(f'Пересчитываем прогресс для ключевого результата ID {key_result_id}...')
                old_progress = key_result.progress
                key_result.recalculate_progress()
                key_result.save(update_fields=['progress'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Прогресс КР "{key_result.description}" обновлен: {old_progress}% -> {key_result.progress}%'
                    )
                )
            except KeyResultsModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Ключевой результат с ID {key_result_id} не найден')
                )
            return
        
        elif objective_id:
            self.stdout.write(f'Пересчитываем прогресс для всех ключевых результатов цели ID {objective_id}...')
            key_results = KeyResultsModel.objects.filter(objective_id=objective_id, is_active=True)
            count = key_results.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING(f'Ключевые результаты для цели ID {objective_id} не найдены'))
                return
            
            updated_count = 0
            for key_result in key_results:
                old_progress = key_result.progress
                key_result.recalculate_progress()
                key_result.save(update_fields=['progress'])
                if old_progress != key_result.progress:
                    updated_count += 1
                    self.stdout.write(
                        f'КР "{key_result.description}": {old_progress}% -> {key_result.progress}%'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Пересчет завершен. Обработано КР: {count}, обновлено: {updated_count}'
                )
            )
        
        else:
            self.stdout.write('Начинаем пересчет прогресса для всех ключевых результатов...')
            key_results = KeyResultsModel.objects.filter(is_active=True)
            count = key_results.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING('Активные ключевые результаты не найдены'))
                return
            
            updated_count = 0
            for key_result in key_results:
                old_progress = key_result.progress
                key_result.recalculate_progress()
                key_result.save(update_fields=['progress'])
                if old_progress != key_result.progress:
                    updated_count += 1
                    self.stdout.write(
                        f'КР "{key_result.description}" (ID: {key_result.id}): {old_progress}% -> {key_result.progress}%'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Пересчет завершен. Обработано ключевых результатов: {count}, обновлено: {updated_count}'
                )
            ) 