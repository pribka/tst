from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkgroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bpms.workgroups'
    verbose_name = _('Рабочие группы')
