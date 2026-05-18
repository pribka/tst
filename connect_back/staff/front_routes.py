from django.utils.translation import gettext_lazy as _

from common import page_config, models as common_models

from . import models


class StaffCategory(page_config.Category):
    name = 'staff'
    path = 'staff'
    title = _('Staff')
    icon = 'team'
    children = page_config.SetConfig(
        type_of_employment=page_config.BaseModelPage(model=models.TypeOfEmployment),
        recruitment=page_config.BaseDocumentPage(model=models.Recruitment),
        dismissal=page_config.BaseDocumentPage(model=models.Dismissal),
        my_catalog=page_config.BaseModelPage(model=models.MyCatalog),
        my_document=page_config.BaseDocumentPage(model=models.MyDocument),
        weather=page_config.BaseModelPage(model=models.WeatherModel),
        season=page_config.BaseModelPage(model=models.SeasonModel),
        month=page_config.BaseModelPage(model=models.MonthModel),
        country=page_config.BaseModelPage(model=models.CountryModel),
        city=page_config.BaseModelPage(model=models.CityModel),
        street=page_config.BaseModelPage(model=models.StreetModel),
        instances=('type_of_employment', 'recruitment', 'dismissal', 'my_catalog', 'my_document', 'weather', 'season',
                   'month', 'country', 'city', 'street')
    )

    def get_dict(self):
        data = super().get_dict()
        # data['children'].append(show_dict)
        return data

    def prepare_my_catalog(self):
        # собираем группу полей:
        address_field_group = page_config.FormGroupFields(
            model=models.MyCatalog, title=_('Address'), collapse=False, inline=True, fields=('country', 'city', 'street'))
        self.children.my_catalog.meta.page_config.form_info.field_info.add_field(
            name='address_field_group', field=address_field_group)
        month_field_group = page_config.FormGroupFields(
            model=models.MyCatalog, title=_('Month'), inline=True, fields=('season', 'weather', 'month'), default_collapse=True)
        self.children.my_catalog.meta.page_config.form_info.field_info.add_field(
            name='month_field_group', field=month_field_group)
        self.children.my_catalog.meta.page_config.form_info.field_info.delete_fields(
            fields=('season', 'weather', 'month', 'country', 'city', 'street'))
        self.children.my_catalog.meta.page_config.form_info.field_info.name.rules_config.required.required = True

    def prepare_my_document(self):
        self.children.my_document.meta.page_config.form_info.editable_part.tp_catalog.form_info = page_config.ExtraModelFormInfo(
            name='form_in_table2', model=models.MyDocument, fields=('reason', 'text'))
        address_field_group = page_config.FormGroupFields(
            model=models.MyDocument, title=_('Address'), fields=('country', 'city', 'street'), collapse=False)
        self.children.my_document.meta.page_config.form_info.editable_part.tp_catalog.form_info.field_info.add_field(
            name='address', field=address_field_group)
        self.children.my_document.meta.page_config.form_info.editable_part.set_instance(
            name='extra_f',
            instance=page_config.ExtraModelFormInfo(
                name='extra_form1',
                title='extra form 1',
                model=models.MyDocument,
                fields=('amount', 'responsible')
            )
        )
        self.children.my_document.meta.page_config.form_info.delete_fields(
            ('reason', 'text', 'amount', 'responsible', 'country', 'city', 'street'))


show_dict = {
    'name': 'show',  # "Название страницы(Латиница)",
    'path': 'show',  # "Фронтовый путь",
    'meta': {  # Дополнительные конфиги
        'pageWidget': 'PageTable',  # "PageTable - Название виджета отрисовки самой страницы",
        'navWidget': 'NavPage',
        'itemWidget': 'ItemWidget',  # "Виджет вывода этого пункта меню, по умолчанию - ItemWidget",
        'title': _('Show'),
        'title_key': 'Show',
        'counter': '',
        'favoriteSupport': True,
        'hide': False,
        'pageConfig': {
            'tableInfo': [
                models.Show.get_table_structure()
            ],
            'filterInfo': 'app_info/filter_info/?model=staff.Show',
            'formInfo': [
                {
                    "name": f'edit_{models.Show.get_label()}',
                    "showComment": True,
                    "showAuthor": True,
                    'actions': {
                        'create': {
                            'path': models.Show.get_data_path(),
                        },
                        'update': {
                            'path': models.Show.get_data_path() + '<id>/',
                        },
                        'retrieve': {
                            'path': models.Show.get_data_path() + '<id>/',
                        }
                    },
                    "i18n": {
                        "update_title": _('Edit document'),
                        'update_title_key': 'Edit document',
                        "create_title": _("Create document"),
                        "create_title_key": "Create document"
                    },
                    'pageWidget': 'TableForm',
                    'navWidget': 'NavForm',
                    'editablePart': [
                        {
                            "name": "tp_tabular",
                            "title": _("Tabular"),
                            "title_key": "Tabular",
                            "type": "table",
                            "tableInfo": models.TPTabular.get_table_structure(),
                            "filterInfo": '',
                            # Пробная форма внутри табчасти.
                            "formInfo": {
                                "name": "form_in_table2",
                                "title": _("Form in table"),
                                "title_key": "Form in table",
                                "type": "form",
                                'pageWidget': 'Default',
                                'navWidget': 'NavForm',
                                "fields": {
                                    "create": ['probaField1', 'probaField2'],
                                    "update": ['probaField1', 'probaField2']
                                },
                                "fieldInfo": [
                                    {
                                        "name": "probaField1",
                                        "title": _('Proba 1'),
                                        'title_key': 'Proba 1',
                                        "class": "inline",
                                        "type": "string",
                                        "rulesConfig": [  # Правила валидации
                                            {
                                                "min": 0,
                                                "max": 36,
                                                "message": _('Minimum 0 characters, maximum 36 characters'),
                                                "trigger": 'change'
                                            },
                                            {
                                                "required": True,
                                                "message": _('Required to fill'),
                                            }
                                        ],
                                        "widgetConfig": {
                                            "widget": "WidgetString",
                                            "placeholder": "",
                                            "size": "default",
                                            "disabled": False
                                        }
                                    },
                                    {
                                        "name": "probaField2",
                                        "title": _('Proba 2'),
                                        'title_key': 'Proba 2',
                                        "class": "inline",
                                        "type": "string",
                                        "rulesConfig": [  # Правила валидации
                                            {
                                                "min": 0,
                                                "max": 36,
                                                "message": _('Minimum 0 characters, maximum 36 characters'),
                                                "trigger": 'change'
                                            },
                                            {
                                                "required": True,
                                                "message": _('Required to fill'),
                                            }
                                        ],
                                        "widgetConfig": {
                                            "widget": "WidgetString",
                                            "placeholder": "",
                                            "size": "default",
                                            "disabled": False
                                        }
                                    },
                                ],
                                'pageConfig': {
                                    "headerButtons": [
                                    ]
                                }
                            }

                        },
                        # Пробная форма в отдельной вкладке табчастей.
                        {
                            "name": "information",
                            "title": _("Information"),
                            "type": "form",
                            "pageWidget": "Default",
                            "navWidget": "NavForm",
                            "fields": {
                                "create": ["name", "description", "city", "country"],
                                "update": ["name", "description", "city", "country"],
                            },
                            'pageConfig': {
                                "headerButtons": [
                                ]
                            },
                            "fieldInfo": [
                                {
                                    "name": "name",
                                    "title": _('Name'),
                                    "type": "string",
                                    "rulesConfig": [  # Правила валидации
                                        {
                                            "min": 0,
                                            # Тут на своей стороне смотри сколько у стрингов максимум и минимум
                                            "max": 255,
                                            "message": _(
                                                'Minimum 0 characters, maximum 36 characters'),
                                            "trigger": 'change'
                                        },
                                        {
                                            "required": True,
                                            "message": _('Required to fill'),
                                        }
                                    ],
                                    "widgetConfig": {
                                        "widget": "WidgetString",
                                        "placeholder": "",
                                        "size": "default",
                                        "disabled": False
                                    }
                                },
                                {
                                    "name": "description",
                                    "title": _('Description'),
                                    "type": "textarea",
                                    "rulesConfig": [  # Правила валидации
                                        {
                                            "min": 0,
                                            # Тут на своей стороне смотри сколько у стрингов максимум и минимум
                                            "max": 1000,
                                            "message": _(
                                                'Minimum 0 characters, maximum 1000 characters'),
                                            "trigger": 'change'
                                        },
                                        {
                                            "required": True,
                                            "message": _('Required to fill'),
                                        }
                                    ],
                                    "autoSize": {
                                        "minRows": 5,
                                        "maxRows": 10
                                    },
                                    "widgetConfig": {
                                        "widget": "WidgetTextarea",
                                        "placeholder": "",
                                        "size": "default",
                                        "disabled": False
                                    }
                                },
                                {  # Обычная Radio кнопка
                                    "class": "",
                                    "name": "city",
                                    "rulesConfig": [
                                        {
                                            "required": True,
                                            "message": _('Required to fill'),
                                        }
                                    ],
                                    "defaultValue": "NY",
                                    # Если надо можем указать value значения по умолчанию
                                    "radioList": [
                                        {
                                            "name": _("New york"),
                                            "value": "NY",
                                            "disabled": False
                                        },
                                        {
                                            "name": _("San Francisco"),
                                            "value": "SF",
                                            "disabled": True
                                        },
                                        {
                                            "name": _("Petropavlovsk"),
                                            "value": "PTPVL",
                                            "disabled": False
                                        },
                                        {
                                            "name": _("Karaganda"),
                                            "value": "KRGD",
                                            "disabled": True
                                        }
                                    ],
                                    "radioType": "Default",  # Указывает виджет обычной кнопки
                                    "title": _("City"),
                                    "fieldName": _("City"),
                                    "type": "radio",
                                    "widgetConfig": {
                                        "disabled": False,
                                        "placeholder": "",
                                        "size": "default",
                                        "widget": "WidgetRadio"
                                    }
                                },
                                {  # Radio в виде button
                                    "class": "",
                                    "name": "country",
                                    "rulesConfig": [
                                        {
                                            "required": True,
                                            "message": _('Required to fill'),
                                        }
                                    ],
                                    "defaultValue": "ARG",
                                    # Если надо можем указать value значения по умолчанию
                                    "radioList": [
                                        {
                                            "name": _('Argentina'),
                                            "value": "ARG",
                                            "disabled": False
                                        },
                                        {
                                            "name": _("Australia"),
                                            "value": "australia",
                                            "disabled": False
                                        },
                                        {
                                            "name": _("Angola"),
                                            "value": "angola",
                                            "disabled": False
                                        },
                                        {
                                            "name": _("Algeria"),
                                            "value": "algeria",
                                            "disabled": True
                                        }
                                    ],
                                    "radioType": "Button",  # Указывает виджет обычной кнопки
                                    "title": _("Country"),
                                    "fieldName": _("Country"),
                                    "type": "radio",
                                    "widgetConfig": {
                                        "disabled": False,
                                        "placeholder": "",
                                        "size": "small",
                                        "widget": "WidgetRadio"
                                    }
                                },
                            ]
                        },
                        {
                            "name": "extra",
                            "title": _("Extra"),
                            "type": "form",
                            'pageWidget': 'Default',
                            'navWidget': 'NavForm',
                            "fields": {
                                "create": ['comment', 'amount', 'responsible', 'with_gas',
                                           'with_syrup', 'toppings'],
                                "update": ['comment', 'amount', 'responsible', 'with_gas',
                                           'with_syrup', 'toppings']
                            },
                            "fieldInfo": [
                                {
                                    "name": "comment",
                                    "title": _('Comment'),
                                    "type": "string",
                                    "class": "inline",
                                    "rulesConfig": [
                                        {
                                            "min": 0,
                                            "max": 1000,
                                            "message": _(
                                                'Minimum 0 characters, maximum 1000 characters'),
                                            "trigger": 'change'
                                        },
                                        {
                                            "required": True,
                                            "message": _('Required to fill'),
                                        }
                                    ],
                                    "widgetConfig": {
                                        "widget": "WidgetString",
                                        "placeholder": "",
                                        "size": "default",
                                        "disabled": False
                                    }
                                },
                                {
                                    "name": "responsible",
                                    "title": _("Responsible"),
                                    "divider": "Блок с ответственным",
                                    "type": "select",
                                    "toField": "code",
                                    "toName": "string_view",
                                    "key": common_models.Individual.get_label(),
                                    "dataPath": f"/app_info/select_list/?model={common_models.Individual.get_label()}",
                                    "rulesConfig": [
                                    ],
                                    "actions": {
                                        "showAll": {
                                            "tableKey": {
                                                "name": common_models.Individual.get_page_name(action='list'),
                                                "key": common_models.Individual.get_label(),
                                                "widget": "Default"},  # Имя таблицы с данными
                                            "tablePath": ''
                                        },
                                        "createOptions": {
                                            "key": f"edit_{common_models.Individual.get_label()}"
                                        }
                                    },
                                    "widgetConfig": {
                                        "widget": "WidgetSelect",
                                        "placeholder": "",
                                        "size": "default",
                                        "disabled": False
                                    }
                                },

                                {
                                    "name": "amount",
                                    "title": _("Amount"),
                                    "class": "inline",
                                    "type": "decimal",
                                    "decimalConfig": {
                                        "caretPositionOnFocus": None,
                                        "allowDecimalPadding": True,
                                        "decimalCharacter": ",",
                                        "decimalCharacterAlternative": ".",
                                        "decimalPlaces": 3,
                                        "decimalPlacesRawValue": 3,
                                        "decimalPlacesShownOnBlur": 3,
                                        "decimalPlacesShownOnFocus": 3,
                                        "digitGroupSeparator": " ",
                                        "emptyInputBehavior": "zero",
                                        "leadingZero": "keep",
                                        "isCancellable": False
                                    },
                                    "widgetConfig": {
                                        "widget": "WidgetDecimal",
                                        "size": "default",
                                        "disabled": False
                                    },
                                    "rulesConfig": [],
                                },
                                {  # Checkbox
                                    "class": "",
                                    "name": "with_gas",
                                    "rulesConfig": [],
                                    "defaultCheck": False,
                                    "title": "",
                                    "fieldName": _("With gas"),
                                    "value": "true",
                                    "type": "checkbox",
                                    "widgetConfig": {
                                        "disabled": False,
                                        "placeholder": "",
                                        "size": "default",
                                        "widget": "WidgetCheckbox"
                                    }
                                },
                                {  # Switch - возвращает true / false
                                    "class": "",
                                    "name": "with_syrup",
                                    "rulesConfig": [],
                                    "defaultCheck": False,
                                    "title": "",
                                    "fieldName": _("With syrup"),
                                    "type": "switch",
                                    "widgetConfig": {
                                        "disabled": False,
                                        "placeholder": "",
                                        "size": "default",
                                        "widget": "WidgetSwitch"
                                    }
                                },
                                {
                                    "class": "",
                                    "name": "toppings",
                                    "rulesConfig": [],
                                    "checkboxList": [
                                        {
                                            "fieldName": _("Chocolate"),
                                            "value": "chocolate",
                                            "defaultCheck": True,
                                            "disabled": False
                                        },
                                        {
                                            "fieldName": _("Nuts"),
                                            "value": "nuts",
                                            "defaultCheck": False,
                                            "disabled": False
                                        },
                                        {
                                            "fieldName": _("Coconut"),
                                            "value": "coconut",
                                            "defaultCheck": False,
                                            "disabled": False
                                        },
                                        {
                                            "fieldName": _("Jam"),
                                            "value": "jam",
                                            "defaultCheck": True,
                                            "disabled": True
                                        },
                                        {
                                            "fieldName": _("Syrup"),
                                            "value": "syrup",
                                            "defaultCheck": False,
                                            "disabled": True
                                        }
                                    ],
                                    "title": _("Toppings"),
                                    "type": "checkboxGroup",
                                    "widgetConfig": {
                                        "widget": "WidgetCheckbox"
                                    }
                                }
                            ],
                            'pageConfig': {
                                "headerButtons": [
                                ]
                            }
                        }
                    ],
                    'fields': {
                        'update': ['doc_num', 'doc_date'],
                        'create': ['doc_num', 'doc_date'],
                    },
                    'fieldInfo': [
                        {
                            "name": "doc_num",
                            "title": _('Document number'),
                            'title_key': 'Document number',
                            "type": "string",
                            "rulesConfig": [  # Правила валидации
                                {
                                    "min": 0,
                                    # Тут на своей стороне смотри сколько у стрингов максимум и минимум
                                    "max": 36,
                                    "message": _(
                                        'Minimum 0 characters, maximum 36 characters'),
                                    "trigger": 'change'
                                },
                            ],
                            "widgetConfig": {
                                "widget": "WidgetString",
                                "placeholder": "",
                                "size": "default",
                                "disabled": False
                            }
                        },
                        {
                            "name": "doc_date",
                            "title": _('Document date'),
                            "title_key": "Document date",
                            "type": "date",
                            "currentDate": True,
                            "dateFormat": "YYYY-MM-DD",
                            "maskFormat": "####-##-##",
                            "rulesConfig": [],
                            "widgetConfig": {
                                "widget": "WidgetString",
                                "size": "default",
                                "disabled": False,
                                "placeholder": "____/__/__"
                            }
                        },
                    ],
                    'pageConfig': {
                        "headerButtons": page_config.BaseDocumentButtonSet(
                            model=models.Show).set_instance(
                            name='print',
                            instance=page_config.PrintDropdownButton(
                                obj_type='dashed',
                                action='print',
                                children=page_config.ModelSetConfig(
                                    print_test_1=page_config.Button(
                                        action="print_test_1",
                                        title=_("Order for an employee")
                                    ),
                                    print_test_2=page_config.Button(
                                        action="print_test_2",
                                        title=_("Order for an employee (list)")
                                    ),
                                    instances=('print_test_1', 'print_test_2')
                                )
                            ),
                        ).get_dict()
                    }
                }
            ]
        },
        'parent': {  # Информация о родительской страницы
            'name': 'staff',  # "Название родительской страницы(Латиница)",
            'path': 'staff',  # "Путь родительской страницы",
            'icon': 'appstore',  # "Иконка родительской страницы",
            'iconSupplier': 'ant',  # "Поставщик иконок, по умолчанию вписывай - ant",
        }
    }
}
