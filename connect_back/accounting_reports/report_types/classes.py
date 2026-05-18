from abc import ABC

from django.apps import apps


class ReportTypeBaseClass(ABC):
    '''
    Базовый класс форм бухгалтерской отчетности.
    '''

    def __init__(self) -> None:
        self._code = ''
        self._name = ''
        self._widget = ''
        self._model_label = ''
        self._model = None
        self._info = dict()

    def get_code(self):
        return self._code

    def get_name(self):
        return self._name

    def get_widget(self):
        return self._widget

    def get_model_label(self):
        return self._model_label

    def get_info(self):
        return self._info

    def __str__(self) -> str:
        return f'Форма отчетности - {self.name}'

    def get_reports_for_consolidation(self, request, *args, **kwargs): ...


class FinancePlanChangeReportType(ReportTypeBaseClass):
    '''
    Форма отчетности 'Заявка на изменение плана финансирования
    по платежам администратора бюджетных программ'
    '''

    def __init__(self) -> None:
        super().__init__()
        self._code = 'finance_plan_change'
        self._name = ('Заявка на изменение плана финансирования по платежам '
                      'администратора бюджетных программ')
        self._widget = 'FinancePlanChange'
        self._model_label = 'FPCReportModel'
        self._model = apps.get_model(
            'accounting_reports',
            'FPCReportModel'
        )
        self._info = {
            'rules': {
                'date': [{'required': True, 'message': 'Обязательно для заполнения', 'trigger': 'focus'}, ],
                'number': [{'required': True, 'message': 'Обязательно для заполнения', 'trigger': 'blur'}, ]
            },
            'form': {
                'responsible_position': None,
                'responsible_name': None,
                'proposals': list(),
                'subtype': None
            }
        }

    def get_reports_for_consolidation(self, request, *args, **kwargs):
        from accounting_reports.serializers import \
            FPCReportModelWidgetSerializer

        start = request.query_params.get('start')
        end = request.query_params.get('end')
        organization = request.query_params.get('organization')
        subtype = request.query_params.get('subtype')

        if start and end and organization and subtype:

            queryset = self._model.objects.filter(
                is_active=True,
                subtype_id=subtype,
                organization_id=organization,
                status_id__in=['new', 'processed', 'rejected'],
                date__gte=start,
                date__lte=end
            )
        else:
            queryset = self._model.objects.none()

        return FPCReportModelWidgetSerializer(
            queryset,
            many=True
        ).data


class ChangeCalculationReportType(ReportTypeBaseClass):
    '''
    Форма отчетности 'Расчет на внесение изменений в
    индивидуальный план финансирования по платежам'
    '''

    def __init__(self) -> None:
        super().__init__()
        self._code = 'change_calculation'
        self._name = ('Расчет на внесение изменений в индивидуальный '
                      'план финансирования по платежам')
        self._widget = 'ChangeCalculation'
        self._model_label = 'ChangeCalculationReportModel'
        self._model = apps.get_model(
            'accounting_reports',
            'ChangeCalculationReportModel'
        )
        self._info = {
            'rules': {
                'range': [{'required': True, 'message': 'Обязательно для заполнения', 'trigger': 'focus'}, ],
                'responsible_position': [{'required':  True, 'message': 'Обязательно для заполнения', 'trigger': 'focus'}, ],
                'responsible_name': [{'required': True, 'message': 'Обязательно для заполнения', 'trigger': 'focus'}, ],
                'pdf_file': [{'required': True, 'message': 'Обязательно для заполнения', 'trigger': 'blur'}, ]
            },
            'form': {
                'responsible_position': None,
                'responsible_name': None,
                'calculations': list(),
                'pdf_file': None,
                'start': None,
                'end': None,
                'is_accumulated': False
            }
        }

    def get_reports_for_consolidation(self, request, *args, **kwargs):
        from accounting_reports.serializers import \
            ChangeCalculationReportModelWidgetSerializer

        start = request.query_params.get('start')
        end = request.query_params.get('end')
        organization = request.query_params.get('organization')

        if start and end and organization:

            queryset = self._model.objects.filter(
                is_active=True,
                organization_id=organization,
                status_id__in=['new', 'processed', 'rejected'],
                start=start,
                end=end
            )
        else:
            queryset = self._model.objects.none()

        return ChangeCalculationReportModelWidgetSerializer(
            queryset,
            many=True
        ).data


def get_report_type_instance(code):
    REPORT_TYPE_CLASSES = {
        'finance_plan_change': FinancePlanChangeReportType,
        'change_calculation': ChangeCalculationReportType
    }
    report_type_instance = REPORT_TYPE_CLASSES.get(code)
    return report_type_instance() if report_type_instance else None
