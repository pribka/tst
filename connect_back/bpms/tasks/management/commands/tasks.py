import json
import datetime
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from bpms.tasks import models, utils


class Command(BaseCommand):
    help = "Management tasks."

    def add_arguments(self, parser):
        parser.add_argument(
            '--set_sprint_for_time_tracking',
            action='store_true',
            help='Set sprint in TaskExecutionTimeModel.',
        )

    def handle(self, *args, **options):
        if options['set_sprint_for_time_tracking']:
            sprints = models.TaskSprintModel.objects.filter(
                is_active=True,
                created_at__gte="2025-03-1T00:00:00.0Z"
            )
            for sprint in sprints:
                date_begin = sprint.begin_date
                date_end = sprint.dead_line
                if date_begin and date_end:
                    sprint_tasks_id = utils.get_all_sprint_tasks(sprint)
                    sprint_tasks_time_executed = models.TaskExecutionTimeModel.objects.filter(
                        is_active=True,
                        task_id__in=sprint_tasks_id,
                        sprint__isnull=True,
                        date__gte=date_begin,
                        date__lte=date_end,
                    )
                    sprint_tasks_time_executed.update(sprint=sprint)
                    print(f"set sprint {sprint.pk} for time_tracking")
            return 'ok'


def get_parent_id(features):
    parent_id = None
    for each in features:
        if each['properties']['admin_level'] == 4:
            parent_id = each['properties']['osm_id']
    return parent_id


