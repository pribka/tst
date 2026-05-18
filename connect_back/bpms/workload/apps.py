from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkloadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bpms.workload'
    verbose_name = _('Загруженность')

    def ready(self):
        from . import signals  # noqa: F401
