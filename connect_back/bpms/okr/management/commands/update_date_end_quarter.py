from django.core.management.base import BaseCommand
from bpms.okr.models import ObjectivesModel, KeyResultsModel
from bpms.okr.utils import get_quarter


class Command(BaseCommand):
    help = 'Обновляет поле date_end_quarter для всех целей и ключевых результатов на основе date_end'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['objectives', 'key_results', 'all'],
            default='all',
            help='Модель для обновления: objectives, key_results или all (по умолчанию)',
        )
        parser.add_argument(
            '--objective-id',
            type=int,
            help='ID конкретной цели для обновления',
        )
        parser.add_argument(
            '--key-result-id',
            type=int,
            help='ID конкретного ключевого результата для обновления',
        )

    def handle(self, *args, **options):
        model_type = options.get('model')
        objective_id = options.get('objective_id')
        key_result_id = options.get('key_result_id')
        
        if objective_id:
            try:
                objective = ObjectivesModel.objects.get(id=objective_id)
                self.stdout.write(f'Обновляем квартал для цели ID {objective_id}...')
                old_quarter = objective.date_end_quarter
                # Обновляем квартал напрямую
                if objective.date_end:
                    quarter_num = get_quarter(objective.date_end)
                    objective.date_end_quarter = quarter_num
                else:
                    objective.date_end_quarter = None
                objective.save(update_fields=['date_end_quarter'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Квартал цели "{objective.objective}" обновлен: {old_quarter} -> {objective.date_end_quarter}'
                    )
                )
            except ObjectivesModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Цель с ID {objective_id} не найдена')
                )
            return
        
        if key_result_id:
            try:
                key_result = KeyResultsModel.objects.get(id=key_result_id)
                self.stdout.write(f'Обновляем квартал для ключевого результата ID {key_result_id}...')
                old_quarter = key_result.date_end_quarter
                # Обновляем квартал напрямую
                if key_result.date_end:
                    quarter_num = get_quarter(key_result.date_end)
                    key_result.date_end_quarter = quarter_num
                else:
                    key_result.date_end_quarter = None
                key_result.save(update_fields=['date_end_quarter'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Квартал КР "{key_result.description}" обновлен: {old_quarter} -> {key_result.date_end_quarter}'
                    )
                )
            except KeyResultsModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Ключевой результат с ID {key_result_id} не найден')
                )
            return
        
        if model_type in ['objectives', 'all']:
            self.stdout.write('Обновляем кварталы для всех целей...')
            objectives = ObjectivesModel.objects.all()
            count = objectives.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING('Активные цели не найдены'))
            else:
                updated_count = 0
                for objective in objectives:
                    old_quarter = objective.date_end_quarter
                    # Обновляем квартал напрямую
                    if objective.date_end:
                        quarter_num = get_quarter(objective.date_end)
                        objective.date_end_quarter = quarter_num
                    else:
                        objective.date_end_quarter = None
                    if old_quarter != objective.date_end_quarter:
                        updated_count += 1
                        self.stdout.write(
                            f'Цель "{objective.objective}" (ID: {objective.id}): {old_quarter} -> {objective.date_end_quarter}'
                        )
                    objective.save(update_fields=['date_end_quarter'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Цели: обработано {count}, обновлено {updated_count}'
                    )
                )
        
        if model_type in ['key_results', 'all']:
            self.stdout.write('Обновляем кварталы для всех ключевых результатов...')
            key_results = KeyResultsModel.objects.all()
            count = key_results.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING('Активные ключевые результаты не найдены'))
            else:
                updated_count = 0
                for key_result in key_results:
                    old_quarter = key_result.date_end_quarter
                    # Обновляем квартал напрямую
                    if key_result.date_end:
                        quarter_num = get_quarter(key_result.date_end)
                        key_result.date_end_quarter = quarter_num
                    else:
                        key_result.date_end_quarter = None
                    if old_quarter != key_result.date_end_quarter:
                        updated_count += 1
                        self.stdout.write(
                            f'КР "{key_result.description}" (ID: {key_result.id}): {old_quarter} -> {key_result.date_end_quarter}'
                        )
                    key_result.save(update_fields=['date_end_quarter'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Ключевые результаты: обработано {count}, обновлено {updated_count}'
                    )
                )
        
        if model_type == 'all':
            self.stdout.write(
                self.style.SUCCESS('Обновление кварталов завершено для всех моделей')
            ) 