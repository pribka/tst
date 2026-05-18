from django.db import models
from django.utils.translation import gettext_lazy as _
from common import models as common_models
from common import fields as common_fields
from common.page_config import TPDecimalColumn, DefaultTableColumn, ForeignKeyFormField, TPIntegerColumn
from common.page_config import ForeignKeyTableColumn, DateTableColumn, DefaultTableColumn
from django.db.models import Sum, Count, F
from common.page_config.tp_columns import TPForeignKeyColumn
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import random
import decimal
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT
"""
Модели для книжной бизнесс логики
"""


class EditionModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """
    Издание
    """

    is_periodic = common_fields.CustomBooleanField(default=False, verbose_name=_('Periodic edition'))
    isbn = common_fields.CustomCharField(max_length=255,
                                         blank=True,
                                         null=True,
                                         verbose_name=_('ISBN'))

    @classmethod
    def has_characteristics_plan(cls):
        return True

    @classmethod
    def get_table_columns(cls):
        data = []
        data.insert(1, 'name')
        data.insert(2, 'is_periodic')
        return data

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['table_columns'].append(DefaultTableColumn(
            header_name='Количество', field='unit_count', sortable=False,
            width=100).get_dict())
        data['table_columns'].append(DefaultTableColumn(
            header_name='Сумма', field='unit_amount', sortable=False,
            width=100).get_dict())
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EditionCUDSerializer, EditionListSerializer
        if action in ['create', 'update', 'partial_update']:
            return EditionCUDSerializer
        elif action in ['list', 'retrieve']:
            return EditionListSerializer
        else:
            return EditionListSerializer

    @classmethod
    def get_data_path(cls):
        return '/bpp/edition/'

    class Meta:
        verbose_name = _('Edition')
        verbose_name_plural = _('Editions')


class EditionPublisherModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """
    Издатель
    """

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EditionPublisherCUDSerializer, EditionPublisherListSerializer
        if action in ['create', 'update', 'partial_update']:
            return EditionPublisherCUDSerializer
        elif action in ['list', 'retrieve']:
            return EditionPublisherListSerializer
        else:
            return EditionPublisherListSerializer

    @classmethod
    def get_data_path(cls):
        return '/bpp/edition_publisher/'

    class Meta:
        verbose_name = _('Publisher')
        verbose_name_plural = _('Publishers')


class EditionAuthorModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """
    Автор
    """

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EditionAuthorCUDSerializer, EditionAuthorListSerializer
        if action in ['create', 'update', 'partial_update']:
            return EditionAuthorCUDSerializer
        elif action in ['list', 'retrieve']:
            return EditionAuthorListSerializer
        else:
            return EditionAuthorListSerializer

    @classmethod
    def get_data_path(cls):
        return '/bpp/edition_author/'

    class Meta:
        verbose_name = _('Author')
        verbose_name_plural = _('Authors')


class EditionPartModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """
    Часть издания
    Том/номер/выпуск
    """
    edition = common_fields.CustomForeignKey(to='bpp.EditionModel',
                                             to_field='code',
                                             null=True,
                                             blank=False,
                                             on_delete=CUSTOM_PROTECT,
                                             verbose_name=_('Edition'),
                                             related_name='edition_part',
                                             field_info=ForeignKeyFormField(filters=[{"name": "is_periodic",
                                                                                      'value': True,
                                                                                      'type': 'defined'}]))

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(3, 'edition')
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EditionPartCUDSerializer, EditionPartListSerializer
        if action in ['create', 'update', 'partial_update']:
            return EditionPartCUDSerializer
        elif action in ['list', 'retrieve']:
            return EditionPartListSerializer
        else:
            return EditionPartListSerializer

    @classmethod
    def get_data_path(cls):
        return '/bpp/edition_part/'

    class Meta:
        verbose_name = _('Volume / number / issue of the edition')
        verbose_name_plural = _('Volumes / numbers / issues of the edition')


def get_default_edition():
    instance, is_new = EditionModel.objects.get_or_create(code='no_edition', defaults={'name': 'N/A'})
    return instance.code


class EditionUnitModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """
    Экземпляр издания
    """
    invoice = common_fields.CustomForeignKey(to='bpp.TPReceiptInvoiceEditionModel', verbose_name=_('Invoice'),
                                             on_delete=CUSTOM_PROTECT, null=True, blank=False, related_name='units')
    edition_part = common_fields.CustomForeignKey(
        to='bpp.EditionPartModel', to_field='code', null=True, blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Volume / number / issue of the edition'),
        field_info=ForeignKeyFormField(filters=[{"name": "edition",
                                                 "from_field": "edition",
                                                 "key": "code",
                                                 'type': 'related'}])
    )
    price = common_fields.CustomDecimalField(decimal_places=2, null=False, default=0, max_digits=16,
                                             verbose_name=_('Price'))
    inventory_number = common_fields.CustomPositiveIntegerField(verbose_name=_('Inventory number'), null=False,
                                                                default=0,
                                                                blank=False,
                                                                table_info=DefaultTableColumn(width=160))

    def __str__(self):
        warehouse_str = ''
        warehouse = self.warehouse
        if warehouse:
            warehouse_str = warehouse.name
        return self.invoice.edition.name + ' №' + str(self.inventory_number) + ' ' + warehouse_str

    @property
    def warehouse(self):
        """
        Для админки
        """
        warehouse = self.get_actual_warehouse()
        if warehouse:
            return warehouse
        else:
            return None

    @property
    def actual_price(self):
        return self.get_actual_price()

    def get_actual_registrar_record(self):
        registrar_recs = self.registered.all()
        registrar = None
        if registrar_recs.count():
            registrar = registrar_recs.order_by('created_at').last()
        return registrar

    @property
    def income_number(self):
        return self.invoice.owner.doc_num

    @property
    def income_date(self):
        return self.invoice.owner.doc_date

    @property
    def income_source(self):
        return self.invoice.owner.source_of_receipt

    @property
    def edition_name(self):
        return self.invoice.edition.name

    @property
    def expense(self):
        registrar = self.get_actual_registrar_record()
        if registrar and registrar.type_of_accumulation == -1:
            return registrar.registrar

    def get_actual_price(self):
        price = self.price
        registrar = self.get_actual_registrar_record()
        if registrar:
            price = registrar.amount
        return price

    def get_actual_warehouse(self):
        warehouse = None
        registrar = self.get_actual_registrar_record()

        if registrar and registrar.type_of_accumulation == 1:
            warehouse = registrar.warehouse

        return warehouse

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['table_columns'].append(DefaultTableColumn(
            header_name='Сигла', field='edition_name', sortable=False, width=80).get_dict())
        data['table_columns'].append(DefaultTableColumn(
            header_name='Стоимость', field='actual_price', sortable=False, width=100).get_dict())
        data['table_columns'].append(DefaultTableColumn(
            header_name='Партия', field='income_number', sortable=False, width=65).get_dict())
        data['table_columns'].append(DateTableColumn(
            header_name='Дата партии', field='income_date', sortable=False, width=94).get_dict())
        data['table_columns'].append(ForeignKeyTableColumn(
            header_name='Источник поступления', field='income_source', sortable=False, width=160).get_dict())
        data['table_columns'].append(ForeignKeyTableColumn(
            header_name='Фонд', field='warehouse', sortable=False, width=140).get_dict())
        data['table_columns'].append(ForeignKeyTableColumn(
            header_name='Выбытие', field='expense', sortable=False, width=320).get_dict())
        return data

    @classmethod
    def get_table_columns(cls):
        data = []
        data.insert(1, 'index_row')
        data.insert(2, 'inventory_number')
        # data.insert(4, 'edition_part')
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EditionUnitCUDSerializer, EditionUnitListSerializer
        if action in ['create', 'update', 'partial_update']:
            return EditionUnitCUDSerializer
        elif action in ['list', 'retrieve']:
            return EditionUnitListSerializer
        else:
            return EditionUnitListSerializer

    @classmethod
    def get_data_path(cls):
        return '/bpp/edition_unit/?in_warehouse=true'

    class Meta:
        verbose_name = _('Instance of edition')
        verbose_name_plural = _('Instances of edition')


class ReceiptInvoiceEditionUnitModel(common_models.BaseDocument):
    """
    Приходная накаладная экземпляров изданий.
    """
    source_of_receipt = common_fields.CustomForeignKey(to='common.Organization', to_field='code',
                                                       verbose_name=_('Source of receipt'), default='current',
                                                       null=True, on_delete=CUSTOM_PROTECT,
                                                       )
    default_warehouse = common_fields.CustomForeignKey(to='catalogs.WarehouseModel', to_field='code',
                                                       verbose_name=_('Default warehouse'), default='main',
                                                       null=False, blank=False, on_delete=CUSTOM_PROTECT,
                                                       )

    @classmethod
    def get_queryset(cls, request=None):
        queryset = super().get_queryset()
        queryset = queryset.annotate(total_amount=Sum('tp_editions__amount'))
        return queryset

    @classmethod
    def get_data_path(cls):
        return '/bpp/incoming_invoice/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_editions': TPReceiptInvoiceEditionModel,
        }

    # Registrar methods
    @classmethod
    def get_type_of_accumulation(cls):
        return 1

    @classmethod
    def has_registrars(cls):
        return True

    @classmethod
    def get_registrar_tabular_parts(cls):
        return {
            'tp_editions': [common_models.AssetInWarehouse],
        }

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import IncomingInvoiceCUDSerializer, IncomingInvoiceDetailSerializer, \
            IncomingInvoiceListSerializer
        if action in ['create', 'update', 'partial_update']:
            return IncomingInvoiceCUDSerializer
        elif action == 'retrieve':
            return IncomingInvoiceDetailSerializer
        elif action == 'list':
            return IncomingInvoiceListSerializer
        else:
            return super().get_serializer_class(action)

    @classmethod
    def get_extra_table_columns(cls):
        data = super().get_extra_table_columns()
        data['total_amount'] = DefaultTableColumn(
            cell_renderer='DecimalRow', header_name=_('Amount'), field='total_amount').get_dict()
        return data

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(6, 'source_of_receipt'),
        data.insert(3, 'total_amount')
        return data

    @classmethod
    def filter_fields(cls):
        return {
            'fields': cls._meta.fields,
            'm2m_fields': cls._meta.many_to_many,
            'fields_map': cls._meta.fields_map,
        }

    class Meta:
        verbose_name = _('Income invoice')
        verbose_name_plural = _('Income invoices')


class FakeMeta:
    verbose_name = _('Экземпляр')
    verbose_name_plural = _('Экземпляры')


class FakeTabularPart:
    _meta = FakeMeta()

    @classmethod
    def get_table_structure(cls):
        model = EditionUnitModel
        table_columns = ['index_row', 'inventory_number']
        fields_dict = dict()
        data = list()
        extra_table_columns = model.get_extra_table_columns()
        for each in model._meta.fields:
            fields_dict[each.name] = each
        for field_name in table_columns:
            try:
                table_info = getattr(fields_dict.get(field_name), 'tp_info').get_dict()
            except AttributeError:
                table_info = getattr(fields_dict.get(field_name), 'tp_info', None)
            if table_info:
                data.append(table_info)
            else:
                table_info = extra_table_columns.get(field_name)
                if table_info:
                    data.append(table_info)
        result = {"table_columns": data,
                  'data_path': model.get_data_path(),
                  'key': model.get_label(),
                  'title': model._meta.verbose_name_plural,
                  'update_condition': {"is_active": True},
                  'edit_form': f'edit_{model.get_label()}',
                  'context_menu': [{
                      "action": "delete",
                      "class": "",
                      "icon": "",
                      "size": "default",
                      "title": "Удалить",
                      "type": "default",
                      "widget": "Default",
                      "disabled": False
                  }],
                  'pageConfig': {
                      "showFilter": True,
                      "headerButtons": []
                  },
                  'tableWidget': 'FlatTable',

                  }
        return result


class TPReceiptInvoiceEditionModel(common_models.BaseAbstractTabularPart):
    """
    Табличная часть приходной накладной изданий.
    """
    owner = models.ForeignKey('bpp.ReceiptInvoiceEditionUnitModel', on_delete=CUSTOM_CASCADE,
                              related_name='tp_editions',
                              verbose_name=_('Document'))
    edition = common_fields.CustomForeignKey(to='bpp.EditionModel', to_field='code', verbose_name=_('Edition'),
                                             on_delete=CUSTOM_PROTECT, null=True, blank=False, default='no_edition')
    price = common_fields.CustomDecimalField(verbose_name=_('Price'), null=False, default=0, max_digits=16,
                                             decimal_places=2, blank=True)
    amount = common_fields.CustomDecimalField(verbose_name=_('Amount'), null=False, default=0, max_digits=16,
                                              decimal_places=2, tp_info=TPDecimalColumn(f_computed=True))
    warehouse = common_fields.CustomForeignKey(to='catalogs.WarehouseModel', to_field='code', verbose_name=_('Warehouse'),
                                               null=True, blank=True, on_delete=CUSTOM_PROTECT,
                                               )

    def set_price(self):
        self.price = self.amount / self.quantity
        self.save(update_fields=('price',), force_update=True)

    # registrar methods
    def __str__(self):
        return getattr(self.edition, 'name', '') + ' ' + getattr(self.warehouse, 'name', '') + ' ' + str(self.price)

    @property
    def quantity(self):
        return self.units.all().count()

    @staticmethod
    def registrar_mapping():
        """
        Маппинг для моделей регистров, чтобы определить какое поле таб.части отностися к полю записи в регистре
        """
        return {"AssetInWarehouse": {
            "asset_owner": "edition",
            "amount": "price",
            "warehouse": "warehouse",
            "quantity": "quantity",
        }}

    def save(self, *args, **kwargs):
        # Если нет склада, записывается склад по умолчанию для документа.
        if not self.warehouse:
            self.warehouse = self.owner.default_warehouse
        super().save(*args, **kwargs)

    def create_units(self, quantity: int):
        difference = quantity - self.units.filter(is_active=True).count()
        if difference > 0:
            for each in range(0, difference):
                inventory_number = random.randrange(10 ** 6)
                EditionUnitModel.objects.create(invoice=self, inventory_number=inventory_number)
        #  TODO priority 2 просуммировать цены и подогнать под сумму amount. Последнюю цену подогнать.

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPReceiptInvoiceEditionModelCUDSerializer, TPReceiptInvoiceEditionModelListSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPReceiptInvoiceEditionModelCUDSerializer
        elif action in ['list', 'retrieve']:
            return TPReceiptInvoiceEditionModelListSerializer
        else:
            return TPReceiptInvoiceEditionModelListSerializer

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(2, 'edition')
        data.insert(3, 'quantity')
        data.insert(4, 'price')
        data.insert(5, 'amount')
        data.insert(6, 'warehouse')
        return data

    @classmethod
    def get_data_path(cls):
        return '/bpp/incoming_invoice/<id>/editions/'

    @classmethod
    def get_table_structure(cls):
        data = super().get_table_structure()
        data['size'] = {'width': 70}
        data['customActions'] = {
            "delete": {
                "path": "/bpp/edition_unit/",
                "params": {
                    "name": "invoice",
                    "key": "id"
                },
                "checkType": "array",
                "type": "CheckDependencies",
                "checkIsEmpty": True,
                "message": "Нельзя удалить: издание имеет экземпляры."
            }
        }
        data["computed"] = {
            "amount": [
                {
                    "field": "quantity",
                    "type": "recount",
                    "formula": "<quantity> * <price>"
                },
                {
                    "field": "price",
                    "type": "recount",
                    "formula": "<quantity> * <price>"
                }
            ],
            "price": [
                {
                    "field": "amount",
                    "type": "recount",
                    "formula": "<amount> / <quantity>"
                }
            ]
        }
        edition_units = FakeTabularPart.get_table_structure()
        edition_units['size'] = {'width': 30}
        edition_units['filters'] = [{"name": "invoice",
                                     "tableKey": "bpp.TPReceiptInvoiceEditionModel",
                                     "key": "id",
                                     'type': 'table'}]
        edition_units['data_path'] = '/bpp/edition_unit/?no_pagination=true'
        edition_units['customActions'] = {
            "delete": {
                "message": _("You cannot delete a copy of the publication: the document has been held."),
                "type": "CheckPost",
                "post": True
            }
        }
        return [
            {
                'name': 'tp_editions',
                'type': 'table',
                'tableInfo': data
            },
            {
                'name': 'edition_units',
                'type': 'table',
                'tableInfo': edition_units
            },
        ]

    @classmethod
    def get_extra_table_columns(cls):
        result = super().get_extra_table_columns()
        result['quantity'] = TPIntegerColumn(
            header_name=_('Quantity'), field='quantity', default_value=1, placeholder='', f_computed=True).get_dict()
        return result

    class Meta:
        verbose_name = _('Tabular part of the incoming invoice of editions')
        verbose_name_plural = _('Tabular parts of an incoming invoice of editions')


class ActWriteOffEditionUnitModel(common_models.BaseDocument):
    """
    Акт списания экземпляров изданий.
    """

    @classmethod
    def get_data_path(cls):
        return '/bpp/act_write_off/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_editions_units': TPActWriteOffEditionModel,
        }

    # Registrar methods
    @classmethod
    def get_type_of_accumulation(cls):
        return -1

    @classmethod
    def has_registrars(cls):
        return True

    @classmethod
    def get_registrar_tabular_parts(cls):
        return {
            'tp_editions_units': [common_models.AssetInWarehouse],
        }

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ActWriteOffCUDSerializer, ActWriteOffDetailSerializer, ActWriteOffListSerializer
        if action in ['create', 'update', 'partial_update']:
            return ActWriteOffCUDSerializer
        elif action == 'retrieve':
            return ActWriteOffDetailSerializer
        elif action == 'list':
            return ActWriteOffListSerializer
        else:
            return super().get_serializer_class(action)

    @classmethod
    def filter_fields(cls):
        return {
            'fields': cls._meta.fields,
            'm2m_fields': cls._meta.many_to_many,
            'fields_map': cls._meta.fields_map,
        }

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)

            # косим юниты
            # if self.is_posted:
            # units =

    class Meta:
        verbose_name = _('Act for writing off publications')
        verbose_name_plural = _('Acts for writing off publications')


class TPActWriteOffEditionModel(common_models.BaseAbstractTabularPart):
    """
    Табличная часть акта на списания изданий.
    """
    owner = models.ForeignKey('bpp.ActWriteOffEditionUnitModel', on_delete=CUSTOM_CASCADE,
                              related_name='tp_editions_units',
                              verbose_name=_('Document'))
    edition = common_fields.CustomForeignKey(to='bpp.EditionModel', to_field='code', verbose_name=_('Edition'),
                                             on_delete=CUSTOM_PROTECT, null=True, blank=False, default='no_edition')
    unit = common_fields.CustomForeignKey(to='bpp.EditionUnitModel', to_field='code',
                                          verbose_name=_('Instance of edition'),
                                          tp_info=TPForeignKeyColumn(width=360),
                                          on_delete=CUSTOM_PROTECT)

    # registrar methods
    @property
    def quantity(self):
        return 1

    @property
    def price(self):
        return self.unit.get_actual_price()

    @property
    def warehouse(self):
        return self.unit.get_actual_warehouse()

    @staticmethod
    def registrar_mapping():
        """
        Маппинг для моделей регистров, чтобы определить какое поле таб.части отностися к полю записи в регистре
        """
        return {"AssetInWarehouse": {
            "asset": "unit",
            "asset_owner": "edition",
            "amount": "price",
            "warehouse": "warehouse",
            "quantity": "quantity",
        }}

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.edition = self.unit.invoice.edition
            super().save(*args, **kwargs)

            # self.update_units()  # Выкашиваем экземпляры издания или делаем им статус списан

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPActWriteOffEditionModelCUDSerializer, TPActWriteOffEditionModelListSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPActWriteOffEditionModelCUDSerializer
        elif action in ['list', 'retrieve']:
            return TPActWriteOffEditionModelListSerializer
        else:
            return TPActWriteOffEditionModelListSerializer

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(1, 'unit')
        return data

    @classmethod
    def get_data_path(cls):
        return '/bpp/act_write_off/<id>/editions/'

    @classmethod
    def get_extra_table_columns(cls):
        result = super().get_extra_table_columns()
        result['quantity'] = TPIntegerColumn(
            header_name=_('Quantity'), field='quantity', default_value=1, placeholder='', ).get_dict()
        return result

    class Meta:
        verbose_name = _('Tabular part of the act for writing off publications')
        verbose_name_plural = _('Tabular parts of the act for writing off publications')


class EditionUnitTransferModel(common_models.BaseDocument):
    @classmethod
    def get_data_path(cls):
        return '/bpp/transfer/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_editions_units_transfer': TPEditionUnitTransferModel,
        }

    @classmethod
    def has_registrars(cls):
        return True

    @classmethod
    def is_transfer(self):
        return True

    @classmethod
    def get_registrar_tabular_parts(cls):
        return {
            'tp_editions_units_transfer': [common_models.AssetInWarehouse],
        }

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import EditionUnitTransferCUDSerializer, EditionUnitTransferDetailSerializer, \
            EditionUnitTransferListSerializer
        if action in ['create', 'update', 'partial_update']:
            return EditionUnitTransferCUDSerializer
        elif action == 'retrieve':
            return EditionUnitTransferDetailSerializer
        elif action == 'list':
            return EditionUnitTransferListSerializer
        else:
            return super().get_serializer_class(action)

    @classmethod
    def filter_fields(cls):
        return {
            'fields': cls._meta.fields,
            'm2m_fields': cls._meta.many_to_many,
            'fields_map': cls._meta.fields_map,
        }

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Moving copies of a publication')
        verbose_name_plural = _('Moving copies of the edition')


class TPEditionUnitTransferModel(common_models.BaseAbstractTabularPart):
    owner = models.ForeignKey('bpp.EditionUnitTransferModel', on_delete=CUSTOM_CASCADE,
                              related_name='tp_editions_units_transfer',
                              verbose_name=_('Document'))
    edition = common_fields.CustomForeignKey(to='bpp.EditionModel', to_field='code', verbose_name=_('Edition'),
                                             on_delete=CUSTOM_PROTECT, null=True, blank=False, default='no_edition')

    unit = common_fields.CustomForeignKey(to='bpp.EditionUnitModel', to_field='code',
                                          verbose_name=_('Instance of edition'),
                                          tp_info=TPForeignKeyColumn(width=360),
                                          on_delete=CUSTOM_PROTECT)
    recipient_warehouse = common_fields.CustomForeignKey(to='catalogs.WarehouseModel', to_field='code',
                                                         verbose_name=_('Warehouse'),
                                                         tp_info=TPForeignKeyColumn(width=240),
                                                         on_delete=CUSTOM_PROTECT)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.edition = self.unit.invoice.edition
            super().save(*args, **kwargs)

    @classmethod
    def get_data_path(cls):
        return '/bpp/transfer/<id>/editions/'

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(1, 'unit')
        data.insert(2, 'recipient_warehouse')
        return data

    # registrar methods
    @property
    def quantity(self):
        return 1

    @property
    def price(self):
        return self.unit.get_actual_price()

    @property
    def warehouse(self):
        return self.unit.get_actual_warehouse()

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPEditionUnitTransferModelCUDSerializer, TPEditionUnitTransferModelListSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPEditionUnitTransferModelCUDSerializer
        elif action in ['list', 'retrieve']:
            return TPEditionUnitTransferModelListSerializer
        else:
            return TPEditionUnitTransferModelListSerializer

    @staticmethod
    def registrar_mapping():
        """
        Маппинг для моделей регистров, чтобы определить какое поле таб.части отностися к полю записи в регистре
        """
        return {"AssetInWarehouse": {
            "asset": "unit",
            "asset_owner": "edition",
            "amount": "price",
            "warehouse": "warehouse",
            "recipient_warehouse": "recipient_warehouse",
            "quantity": "quantity",
        }}

    class Meta:
        verbose_name = _('Tabular part of movement of copies of the edition')
        verbose_name_plural = _('Tabular portions of movement of edition instances')
