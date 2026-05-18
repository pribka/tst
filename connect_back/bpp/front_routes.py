from django.utils.translation import gettext_lazy as _
from common import page_config
from . import models


class BppCategory(page_config.Category):
    name = 'bpp'
    path = 'bpp'
    title = _('Accounting of editions')
    icon = 'bar-chart'
    children = page_config.SetConfig(
        edition=page_config.BaseModelPage(model=models.EditionModel),
        edition_part=page_config.BaseModelPage(model=models.EditionPartModel),
        edition_unit=page_config.BaseModelPage(model=models.EditionUnitModel),
        edition_author=page_config.BaseModelPage(model=models.EditionAuthorModel),
        edition_publisher=page_config.BaseModelPage(model=models.EditionPublisherModel),
        incoming_invoice=page_config.BaseDocumentPage(model=models.ReceiptInvoiceEditionUnitModel),
        act_write_off=page_config.BaseDocumentPage(model=models.ActWriteOffEditionUnitModel),
        transfer=page_config.BaseDocumentPage(model=models.EditionUnitTransferModel),
        instances=('edition_publisher', 'edition_author', 'edition', 'edition_part', 'edition_unit', 'incoming_invoice',
                   'act_write_off', 'transfer')
    )

    def prepare_incoming_invoice(self):
        self.children.incoming_invoice.meta.page_config.form_info.editable_part.tp_editions.grid_type = 'inline'
        self.children.incoming_invoice.meta.page_config.form_info.editable_part.tp_editions.obj_type = 'layout'
        self.children.incoming_invoice.meta.page_config.form_info.editable_part.tp_editions.name = 'tp_edition_wrapper'
        self.children.incoming_invoice.meta.page_config.form_info.field_info.add_field(
            name='total_amount',
            position=0,
            field=page_config.DecimalFormField(
                name='total_amount',
                title=_('Сумма'),
                field_name=_('Сумма'),
                disabled=True,
                update=True,
            )
        )
        update_list = list(self.children.incoming_invoice.meta.page_config.form_info.fields.update)
        try:
            update_list.remove('total_amount')
        except ValueError:
            pass
        update_list.append('total_amount')
        self.children.incoming_invoice.meta.page_config.form_info.fields.update = tuple(update_list)
        create_list = list(self.children.incoming_invoice.meta.page_config.form_info.fields.create)
        try:
            create_list.remove('total_amount')
        except ValueError:
            pass
        create_list.append('total_amount')
        self.children.incoming_invoice.meta.page_config.form_info.fields.create = tuple(create_list)

    def get_dict(self):
        data = super().get_dict()
        return data
