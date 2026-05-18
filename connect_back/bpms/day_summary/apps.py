from django.apps import AppConfig


class DaySummaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bpms.day_summary'

    def ready(self):
        from . import signals  # noqa: F401
