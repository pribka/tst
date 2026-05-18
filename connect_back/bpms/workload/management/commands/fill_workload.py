from django.core.management.base import BaseCommand
from progress.bar import PixelBar

from bpms.tasks import models as t_models
from bpms.workload import models as wl_models
from bpms.workload import utils
from users import models as u_models


class Command(BaseCommand):
    help = 'Загруженность по всем пользователям'

    def handle(self, *args, **kwargs):
        profiles = u_models.ProfileModel.objects.all()

        bar = PixelBar('Loading', max=profiles.count())

        for profile in profiles:
            schedule, _ = wl_models.WorkScheduleModel.objects.get_or_create(
                profile=profile
            )
            tasks = t_models.TaskModel.objects.filter(operator=profile)
            min_date = (
                tasks
                .order_by('date_start_plan__date')
                .values_list('date_start_plan__date', flat=True)
                .first()
            )
            max_date = (
                tasks
                .order_by('-dead_line__date')
                .values_list('dead_line__date', flat=True)
                .first()
            )
            dates = utils.get_dates_range(min_date, max_date)
            for date in dates:
                tasks = tasks.filter(date_start_plan__date=date)
                utils.collect_tasks(profile, date, tasks)
            bar.next()
        bar.finish()
