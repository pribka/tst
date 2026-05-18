from django.db import models
from django.utils.translation import gettext_lazy as _
from django_currentuser.middleware import get_current_authenticated_user
from django.contrib.postgres import fields as postgres_fields

from common import models as common_models
from common import fields as common_fields
from common import page_config as common_page_config
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT

class TypeOfEmployment(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    @classmethod
    def get_data_path(cls):
        return '/staff/types_of_employment/'

    @classmethod
    def is_enum(cls):
        return True

    class Meta:
        verbose_name = _('Type of employment')
        verbose_name_plural = _('Types of employment')


class Recruitment(common_models.BaseDocument):

    @classmethod
    def get_data_path(cls):
        return '/staff/recruitment/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_workers': TPRecruitmentWorkers,
            'tp_accruals': TPRecruitmentAccruals
        }

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import RecruitmentCUDSerializer, RecruitmentDetailSerializer
        #  TODO прототип для формы во вкладке табчасти
        if action in ['create', 'update', 'partial_update']:
            return RecruitmentCUDSerializer
        elif action == 'retrieve':
            return RecruitmentDetailSerializer
        else:
            return super().get_serializer_class(action)

    class Meta:
        verbose_name = _("Recruitment")
        verbose_name_plural = _("Recruitment")


class TPRecruitmentWorkers(common_models.BaseAbstractTabularPart):
    owner = models.ForeignKey(to='staff.Recruitment', on_delete=CUSTOM_CASCADE, related_name='tp_workers',
                              verbose_name=_('Document'))

    individual = common_fields.CustomForeignKey(to='common.Individual', to_field='code', null=True, blank=False,
                                                on_delete=CUSTOM_PROTECT, verbose_name=_('Individual'),
                                                )

    type_of_employment = common_fields.CustomForeignKey(to='staff.TypeOfEmployment', on_delete=CUSTOM_PROTECT,
                                                        verbose_name=_('Type of employment'), to_field='code',
                                                        null=False,
                                                        blank=True, default='main')

    @classmethod
    def get_data_path(cls):
        return '/staff/recruitment/<id>/workers/'

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data = data + ['individual', 'type_of_employment']
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPRecruitmentWorkersSerializer, TPRecruitmentWorkerCUDSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPRecruitmentWorkerCUDSerializer
        else:
            return TPRecruitmentWorkersSerializer

    class Meta:
        verbose_name = _('Worker')
        verbose_name_plural = _('Workers')


class TPRecruitmentAccruals(common_models.BaseAbstractTabularPart):
    owner = models.ForeignKey('staff.Recruitment', on_delete=CUSTOM_CASCADE, related_name='tp_accruals',
                              verbose_name=_('Document'))
    individual = common_fields.CustomForeignKey(to='common.Individual', on_delete=CUSTOM_PROTECT, to_field='code',
                                                verbose_name=_('Individual'))
    amount = common_fields.CustomDecimalField(verbose_name=_('Size'), null=False, default=0, max_digits=21,
                                              decimal_places=3)

    @classmethod
    def get_data_path(cls):
        return '/staff/recruitment/<id>/accruals/'

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data = data + ['individual', 'amount']
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPRecruitmentAccrualsSerializer, TPRecruitmentAccrualsCUDSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPRecruitmentAccrualsCUDSerializer
        return TPRecruitmentAccrualsSerializer

    class Meta:
        verbose_name = _('Accrual')
        verbose_name_plural = _('Accruals')


class Dismissal(common_models.BaseDocument):
    @classmethod
    def get_data_path(cls):
        return '/staff/dismissal/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_dismiss_staff': TPDismissalStaff
        }

    class Meta:
        verbose_name = _("Dismissal")
        verbose_name_plural = _("Dismissals")


class TPDismissalStaff(common_models.BaseAbstractTabularPart):
    owner = models.ForeignKey(to='staff.Dismissal', verbose_name=_('Document'), on_delete=CUSTOM_CASCADE,
                              related_name='tp_dismiss_staff')
    individual = common_fields.CustomForeignKey(to='common.Individual', to_field='code', on_delete=CUSTOM_PROTECT,
                                                verbose_name=_('Individual'))
    dismiss_date = models.DateField(verbose_name=_('Date of dismissal'), null=False, blank=True,
                                    default=common_models.get_default_date)

    @classmethod
    def get_data_path(cls):
        return '/staff/dismissal/<id>/staff/'

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data = data + ['individual', 'dismiss_data']
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPDismissalStaffSerializer, TPDismissalStaffCUDSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPDismissalStaffCUDSerializer
        return TPDismissalStaffSerializer

    class Meta:
        verbose_name = _('Dismissal staff')
        verbose_name_plural = _('Dismissal staff')


class Show(common_models.BaseDocument):
    amount = common_fields.CustomDecimalField(verbose_name=_('Amount'), null=False, default=0, max_digits=21,
                                              decimal_places=3)
    responsible = common_fields.CustomForeignKey(to='common.Individual', to_field='code', verbose_name=_('Responsible'),
                                                 on_delete=CUSTOM_PROTECT, null=True, blank=True)
    name = common_fields.CustomCharField(verbose_name=_('Name'), null=False, default="", blank=True, max_length=255, )
    description = common_fields.CustomCharField(verbose_name=_('Description'), null=False, default="", blank=True,
                                                max_length=1000)
    city = common_fields.CustomCharField(verbose_name=_('City'), null=False, default="NY", blank=True, max_length=255, )
    country = common_fields.CustomCharField(verbose_name=_('Country'), null=False, default="ARG", blank=True,
                                            max_length=255)
    with_gas = common_fields.CustomCharField(verbose_name=_("With gas"), default='false', null=False, blank=True,
                                             max_length=31)
    with_syrup = common_fields.CustomBooleanField(verbose_name=_("With syrup"), default=True)
    toppings = postgres_fields.ArrayField(models.CharField(max_length=31), blank=True, null=False, default=list)

    #  Пробные поля внутри вкладки с табчастью
    probaField1 = common_fields.CustomCharField(verbose_name=_('proba 1'), null=False, blank=True, default='',
                                                max_length=36)
    probaField2 = common_fields.CustomCharField(verbose_name=_('proba 2'), null=False, blank=True, default='',
                                                max_length=36)

    @classmethod
    def get_data_path(cls):
        return '/staff/show/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_tabular': TPTabular,
        }

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ShowCUDSerializer, ShowDetailSerializer
        #  TODO прототип для формы во вкладке табчасти
        if action in ['create', 'update', 'partial_update']:
            return ShowCUDSerializer
        elif action == 'retrieve':
            return ShowDetailSerializer
        else:
            return super().get_serializer_class(action)

    @classmethod
    def get_header_buttons(cls):
        buttons = common_page_config.BaseModelTableButtonSet(model=cls).set_instance(
            name="print",
            instance=common_page_config.DropdownButton(
                model=cls,
                title=_("Print"),
                action="print",
                obj_type='dashed',
                children=common_page_config.ModelSetConfig(
                    instances=('print_test_1', 'print_test_2'),
                    print_test_1=common_page_config.Button(
                        title=_("Order for an employee"),
                        action="print_test_1"
                    ),
                    print_test_2=common_page_config.Button(
                        title=_("Order for an employee (list)"),
                        action="print_test_2"
                    ),
                )
            ),
        )
        return buttons.get_dict()

    class Meta:
        verbose_name = _("Show")
        verbose_name_plural = _("Show")


class TPTabular(common_models.BaseAbstractTabularPart):
    owner = models.ForeignKey(to='staff.Show', on_delete=CUSTOM_CASCADE, related_name='tp_tabular',
                              verbose_name=_('Document'))

    individual = common_fields.CustomForeignKey(to='common.Individual', to_field='code', null=True, blank=False,
                                                on_delete=CUSTOM_PROTECT, verbose_name=_('Individual'),
                                                )

    type_of_employment = common_fields.CustomForeignKey(to='staff.TypeOfEmployment', on_delete=CUSTOM_PROTECT,
                                                        verbose_name=_('Type of employment'), to_field='code',
                                                        null=False,
                                                        blank=True, default='main')

    @classmethod
    def get_data_path(cls):
        return '/staff/show/<id>/tabular/'

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data = data + ['individual', 'type_of_employment']
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPShowTabularSerializer, TPShowTabularCUDSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPShowTabularCUDSerializer
        else:
            return TPShowTabularSerializer

    class Meta:
        verbose_name = _('Tabular')
        verbose_name_plural = _('Tabular')


class SeasonModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    @classmethod
    def get_data_path(cls):
        return '/staff/season/'

    class Meta:
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')


class WeatherModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    @classmethod
    def get_data_path(cls):
        return '/staff/weather/'

    class Meta:
        verbose_name = _('Weather')
        verbose_name_plural = _('Weathers')


class MonthModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    season = common_fields.CustomForeignKey(to='staff.SeasonModel', to_field='code', null=True, blank=True,
                                            verbose_name=_('Season'), on_delete=CUSTOM_PROTECT)

    weather = common_fields.CustomForeignKey(to='staff.WeatherModel', to_field='code', null=True, blank=True,
                                             on_delete=CUSTOM_PROTECT)

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MonthModelCUDSerializer, MonthModelListSerializer
        if action in ['create', 'update', 'partial_update']:
            return MonthModelCUDSerializer
        elif action in ['list', 'retrieve']:
            return MonthModelListSerializer
        else:
            return MonthModelListSerializer

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(3, 'season')
        data.insert(4, 'weather')
        return data

    @classmethod
    def get_data_path(cls):
        return '/staff/month/'

    class Meta:
        verbose_name = _('Month')
        verbose_name_plural = _('Month')


class CountryModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    @classmethod
    def get_data_path(cls):
        return '/staff/country/'

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')


class CityModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    country = common_fields.CustomForeignKey(to='staff.CountryModel', to_field='code',
                                             on_delete=CUSTOM_PROTECT, null=True, blank=True,
                                             verbose_name=_('Country'))

    @classmethod
    def get_data_path(cls):
        return '/staff/city/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import CityModelCUDSerializer, CityModelListSerializer
        if action in ['create', 'update', 'partial_update']:
            return CityModelCUDSerializer
        elif action in ['list', 'retrieve']:
            return CityModelListSerializer
        else:
            return CityModelListSerializer

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(4, 'country')
        return data

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')


class StreetModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    city = common_fields.CustomForeignKey(to='staff.CityModel', to_field='code',
                                          on_delete=CUSTOM_PROTECT, null=True, blank=True,
                                          verbose_name=_('City'))

    @classmethod
    def get_data_path(cls):
        return '/staff/street/'

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import StreetModelCUDSerializer, StreetModelListSerializer
        if action in ['create', 'update', 'partial_update']:
            return StreetModelCUDSerializer
        elif action in ['list', 'retrieve']:
            return StreetModelListSerializer
        else:
            return StreetModelListSerializer

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(4, 'city')
        return data

    class Meta:
        verbose_name = _('Street')
        verbose_name_plural = _('Streets')


# Создаем справочник
class MyCatalog(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    # Добавляем поле (внешний ключ)
    recruitment = common_fields.CustomForeignKey(to='staff.Recruitment', on_delete=CUSTOM_PROTECT,
                                                 verbose_name=_('Recruitment'), null=True, blank=True)
    chel = common_fields.CustomForeignKey(to='common.Individual', to_field='code', on_delete=CUSTOM_PROTECT,
                                          verbose_name=_('chel'), null=True, blank=True)
    season = common_fields.CustomForeignKey(to='staff.SeasonModel', to_field='code', null=True, blank=True,
                                            verbose_name=_('Season'), on_delete=CUSTOM_PROTECT)

    weather = common_fields.CustomForeignKey(to='staff.WeatherModel', to_field='code', null=True, blank=True,
                                             on_delete=CUSTOM_PROTECT)

    month = common_fields.CustomForeignKey(to='staff.MonthModel',
                                           to_field='code',
                                           on_delete=CUSTOM_PROTECT,
                                           verbose_name=_('month'),
                                           null=True,
                                           blank=True,
                                           field_info=common_page_config.ForeignKeyFormField(
                                               filters=[{'name': 'season',
                                                         'from_field': 'season',
                                                         'key': 'code',
                                                         'type': 'related'
                                                         },
                                                        {'name': 'weather',
                                                         'from_field': 'weather',
                                                         'key': 'code',
                                                         'type': 'related'
                                                         }
                                                        ])
                                           )

    country = common_fields.CustomForeignKey(to='staff.CountryModel', to_field='code', null=True, blank=False,
                                             on_delete=CUSTOM_PROTECT, verbose_name=_('Country'))
    city = common_fields.CustomForeignKey(to='staff.CityModel', to_field='code', null=True, blank=False,
                                          on_delete=CUSTOM_PROTECT, verbose_name=_('City'),
                                          field_info=common_page_config.ForeignKeyFormField(
                                              filters=[{"name": "country",
                                                        "from_field": "country",
                                                        "key": "code",
                                                        'type': 'related'}])
                                          )
    street = common_fields.CustomForeignKey(to='staff.StreetModel', to_field='code', null=True, blank=False,
                                            on_delete=CUSTOM_PROTECT, verbose_name=_('Street'),
                                            field_info=common_page_config.ForeignKeyFormField(
                                                filters=[{
                                                    "name": "city",
                                                    "from_field": "city",
                                                    "key": "code",
                                                    'type': 'related'}]))

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(5, 'chel')
        data.insert(6, 'season')
        data.insert(7, 'weather')
        data.insert(8, 'month')
        data.insert(9, 'country')
        data.insert(10, 'city')
        data.insert(11, 'street')
        data.insert(12, 'recruitment')
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MyCatalogCUDSerializer, MyCatalogListSerializer
        if action in ['create', 'update', 'partial_update']:
            return MyCatalogCUDSerializer
        elif action in ['list', 'retrieve']:
            return MyCatalogListSerializer
        else:
            return MyCatalogListSerializer

    @classmethod
    def get_data_path(cls):
        return '/staff/mycatalog/'

    class Meta:
        verbose_name = _('My catalog')
        verbose_name_plural = _('My catalogs')


class MyDocument(common_models.BaseDocument):
    amount = common_fields.CustomDecimalField(verbose_name=_('Amount'), null=False, default=0, max_digits=21,
                                              decimal_places=3)
    responsible = common_fields.CustomForeignKey(to='common.Individual', to_field='code', verbose_name=_('Responsible'),
                                                 on_delete=CUSTOM_PROTECT, null=True, blank=True)
    name = common_fields.CustomCharField(verbose_name=_('Name'), null=False, default="", blank=True, max_length=255, )
    description = common_fields.CustomCharField(verbose_name=_('Description'), null=False, default="", blank=True,
                                                max_length=1000)
    with_syrup = common_fields.CustomBooleanField(verbose_name=_("With syrup"), default=True)
    reason = common_fields.CustomCharField(verbose_name=_('Reason'), null=False, blank=True, default='', max_length=36,
                                           field_info=common_page_config.CharFieldFormField(css_class='inline'))
    text = common_fields.CustomCharField(verbose_name=_('Text'), null=False, blank=True, default='', max_length=36,
                                         field_info=common_page_config.CharFieldFormField(css_class='inline'))
    quantity = common_fields.CustomPositiveIntegerField(verbose_name='quantity', null=False, default=0, blank=True)
    datetime = common_fields.CustomDateTimeField(verbose_name='date time', null=False,
                                                 default=common_models.get_default_datetime, blank=True, )

    country = common_fields.CustomForeignKey(to='staff.CountryModel', to_field='code', null=True, blank=False,
                                             on_delete=CUSTOM_PROTECT, verbose_name=_('Country'))
    city = common_fields.CustomForeignKey(to='staff.CityModel', to_field='code', null=True, blank=False,
                                          on_delete=CUSTOM_PROTECT, verbose_name=_('City'),
                                          field_info=common_page_config.ForeignKeyFormField(
                                              filters=[{"name": "country",
                                                        "from_field": "country",
                                                        "key": "code",
                                                        'type': 'related'}])
                                          )
    street = common_fields.CustomForeignKey(to='staff.StreetModel', to_field='code', null=True, blank=False,
                                            on_delete=CUSTOM_PROTECT, verbose_name=_('Street'),
                                            field_info=common_page_config.ForeignKeyFormField(
                                                filters=[{"name": "city",
                                                          "from_field": "city",
                                                          "key": "code",
                                                          'type': 'related'}]))

    @classmethod
    def has_characteristics_plan(cls):
        return True

    @classmethod
    def get_data_path(cls):
        return '/staff/mydocument/'

    @classmethod
    def get_tabular_parts(cls):
        return {
            'tp_catalog': TPCatalog,
        }

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import MyDocumentCUDSerializer, MyDocumentDetailSerializer, MyDocumentListSerializer
        #  TODO прототип для формы во вкладке табчасти
        if action in ['create', 'update', 'partial_update']:
            return MyDocumentCUDSerializer
        elif action == 'retrieve':
            return MyDocumentDetailSerializer
        elif action == 'list':
            return MyDocumentListSerializer
        else:
            return super().get_serializer_class(action)

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data.insert(3, 'responsible')
        data.insert(4, 'quantity')
        data.insert(5, 'with_syrup')
        data.insert(6, 'datetime')
        data.insert(7, 'amount')
        data.insert(8, "text")
        return data

    @classmethod
    def filter_fields(cls):
        return {
            'fields': cls._meta.fields,
            'm2m_fields': cls._meta.many_to_many,
            'fields_map': cls._meta.fields_map,
        }

    class Meta:
        verbose_name = _("My Document")
        verbose_name_plural = _("My Documents")


class TPCatalog(common_models.BaseAbstractTabularPart):
    owner = models.ForeignKey(to='staff.MyDocument', on_delete=CUSTOM_CASCADE, related_name='tp_catalog',
                              verbose_name=_('Document'))

    catalog = common_fields.CustomForeignKey(to='staff.MyCatalog', to_field='code', null=True, blank=False,
                                             on_delete=CUSTOM_PROTECT, verbose_name=_('Catalog'))
    amount = common_fields.CustomDecimalField(verbose_name=_('Amount'), null=False, default=0, max_digits=21,
                                              decimal_places=3)
    is_ok = common_fields.CustomBooleanField(default=True, verbose_name=_('ok'), )
    some_string = common_fields.CustomCharField(null=False, blank=False, default='', max_length=51,
                                                verbose_name='Some string')
    some_date = common_fields.CustomDateField(null=True, blank=True, verbose_name=_('Some date'))
    some_datetime = common_fields.CustomDateTimeField(null=True,
                                                      blank=True,
                                                      tp_info=common_page_config.TPDateTimeColumn(current_date=True),
                                                      verbose_name=_('Some Datetime'))
    some_integer = common_fields.CustomPositiveIntegerField(null=False, default=0, verbose_name=_('Some Integer'),
                                                            blank=True)

    @classmethod
    def get_data_path(cls):
        return '/staff/mydocument/<id>/catalog/'

    @classmethod
    def get_table_columns(cls):
        data = super().get_table_columns()
        data = data + ['catalog', 'amount', 'is_ok', 'some_string', 'some_date', 'some_datetime', 'some_integer']
        return data

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import TPCatalogSerializer, TPCatalogCUDSerializer
        if action in ['create', 'update', 'partial_update']:
            return TPCatalogCUDSerializer
        else:
            return TPCatalogSerializer

    class Meta:
        verbose_name = _('Catalog')
        verbose_name_plural = _('Catalogs')
