import json

from django_q.tasks import async_task
from contractor_permissions.utils import get_tariffs_id_by_contractors
from billing.models import ContractorTariffModel, TariffModel
from . import utils, models


def collect_emails():
    configs = models.HelpDeskConfigModel.objects.filter(is_active=True).order_by('created_at')
    for config in configs:
        imap_server = config.imap_server
        imap_port = config.imap_port
        email_username = config.email_username
        email_pass = config.email_pass
        if not imap_server or not imap_port or not email_username or not email_pass:
            continue
        contractor = config.contractor

        if not TariffModel.objects.filter(
                code='help_desk_admin',
                pk__in=get_tariffs_id_by_contractors((contractor,))
        ).exists():
            continue
        async_task(utils.get_emails, str(config.pk))
