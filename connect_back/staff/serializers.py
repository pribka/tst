from rest_framework import serializers
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _

from . import models
from common import serializers as common_serializers


class RecruitmentCUDSerializer(common_serializers.BaseDocumentCUDSerializer):
    #  TODO прототип для формы во вкладке табчасти

    class Meta(common_serializers.BaseDocumentCUDSerializer.Meta):
        model = models.Recruitment
        fields = common_serializers.BaseDocumentCUDSerializer.Meta.fields


class RecruitmentDetailSerializer(common_serializers.BaseDocumentDetailSerializer):

    class Meta(common_serializers.BaseDocumentDetailSerializer.Meta):
        model = models.Recruitment
        fields = common_serializers.BaseDocumentDetailSerializer.Meta.fields


class TPRecruitmentWorkersSerializer(common_serializers.BaseModelSerializer):
    individual = common_serializers.BaseCatalogListSerializer(label=_('Individual'))
    type_of_employment = common_serializers.BaseCatalogListSerializer(label=_('Type of employment'))

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPRecruitmentWorkers
        fields = common_serializers.BaseModelSerializer.Meta.fields + [
            'individual',
            'type_of_employment'
        ]


class TPRecruitmentWorkerCUDSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TPRecruitmentWorkers
        fields = (
            'id',
            'owner',
            'individual',
            'type_of_employment'
        )


class TPRecruitmentAccrualsSerializer(common_serializers.BaseModelSerializer):
    individual = common_serializers.BaseCatalogListSerializer(label=_('Individual'))

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPRecruitmentAccruals
        fields = common_serializers.BaseModelSerializer.Meta.fields + [
            'individual',
            'amount'
        ]


class TPRecruitmentAccrualsCUDSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TPRecruitmentAccruals
        fields = [
            'id',
            'owner',
            'individual',
            'amount'
        ]


class TPDismissalStaffSerializer(common_serializers.BaseModelSerializer):
    individual = common_serializers.BaseCatalogListSerializer(label=_('Individual'))
    dismiss_date = serializers.DateField(required=False, allow_null=True, label=_('Date of dismissal'))

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPDismissalStaff
        fields = common_serializers.BaseModelSerializer.Meta.fields + [
            'individual',
            'dismiss_date'
        ]

    def validate_dismiss_date(self, data):
        from django.utils.timezone import localdate
        if not data:
            data = localdate()
        return data


class TPDismissalStaffCUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPDismissalStaff
        fields = [
            'id',
            'owner',
            'individual',
            'dismiss_date'
        ]


class ShowCUDSerializer(common_serializers.BaseDocumentCUDSerializer):
    #  TODO прототип для формы во вкладке табчасти

    class Meta(common_serializers.BaseDocumentCUDSerializer.Meta):
        model = models.Show
        fields = common_serializers.BaseDocumentCUDSerializer.Meta.fields + ['amount', 'responsible', 'name',
                                                                             'description', 'probaField1',
                                                                             'probaField2', 'city', 'country',
                                                                             'with_gas', 'with_syrup', 'toppings']


class ShowDetailSerializer(common_serializers.BaseDocumentDetailSerializer):
    responsible = common_serializers.IndividualSerializer()

    class Meta(common_serializers.BaseDocumentDetailSerializer.Meta):
        model = models.Show
        fields = common_serializers.BaseDocumentDetailSerializer.Meta.fields + ['amount', 'responsible', 'name',
                                                                                'description', 'probaField1',
                                                                                'probaField2', 'city', 'country',
                                                                                'with_gas', 'with_syrup', 'toppings']


class TPShowTabularSerializer(common_serializers.BaseModelSerializer):
    individual = common_serializers.BaseCatalogListSerializer(label=_('Individual'))
    type_of_employment = common_serializers.BaseCatalogListSerializer(label=_('Type of employment'))

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPTabular
        fields = common_serializers.BaseModelSerializer.Meta.fields + [
            'individual',
            'type_of_employment'
        ]


class TPShowTabularCUDSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TPTabular
        fields = (
            'id',
            'owner',
            'individual',
            'type_of_employment'
        )


class MyCatalogCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.MyCatalog
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + ['chel', 'season', 'weather', 'month',
                                                                            'country', 'city', 'street', 'recruitment']
        validators = []


class MyCatalogListSerializer(common_serializers.BaseCatalogListSerializer):
    recruitment = common_serializers.BaseCatalogListSerializer()
    chel = common_serializers.BaseCatalogListSerializer()

    season = common_serializers.BaseCatalogListSerializer()
    weather = common_serializers.BaseCatalogListSerializer()
    month = common_serializers.BaseCatalogListSerializer()

    country = common_serializers.BaseCatalogListSerializer()
    city = common_serializers.BaseCatalogListSerializer()
    street = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.MyCatalog
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + ['recruitment','chel', 'season', 'weather',
                                                                             'month', 'country', 'city', 'street']


class MyDocumentCUDSerializer(common_serializers.BaseDocumentCUDSerializer):
    class Meta(common_serializers.BaseDocumentCUDSerializer):
        model = models.MyDocument
        fields = common_serializers.BaseDocumentCUDSerializer.Meta.fields + ['amount', 'responsible', 'name',
                                                                             'description', 'with_syrup', 'reason', 'text', 'quantity',
                                                                             'datetime', 'country', 'city', 'street']
        validators = []


class MyDocumentListSerializer(common_serializers.BaseDocumentListSerializer):
    responsible = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseDocumentListSerializer.Meta):
        model = models.MyDocument
        fields = common_serializers.BaseDocumentListSerializer.Meta.fields + ['responsible', 'quantity', 'with_syrup',
                                                                              'datetime']


class MyDocumentDetailSerializer(common_serializers.BaseDocumentDetailSerializer):
    responsible = common_serializers.BaseCatalogListSerializer()

    country = common_serializers.BaseCatalogListSerializer()
    city = common_serializers.BaseCatalogListSerializer()
    street = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseDocumentDetailSerializer):
        model = models.MyDocument
        fields = common_serializers.BaseDocumentDetailSerializer.Meta.fields + [
            'amount', 'responsible', 'name', 'description', 'with_syrup', 'reason', 'text', 'quantity', 'datetime',
            'country', 'city', 'street'
        ]


class TPCatalogCUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPCatalog
        fields = ('owner', 'catalog', 'amount', 'is_ok', 'some_string', 'some_date', 'some_datetime', 'some_integer')


class TPCatalogSerializer(serializers.ModelSerializer):
    catalog = common_serializers.BaseCatalogListSerializer()

    class Meta:
        model = models.TPCatalog
        fields = ('id', 'catalog', 'amount', 'is_ok', 'some_string', 'some_date', 'some_datetime', 'some_integer')


class MonthModelCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.MonthModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + ['weather', 'season']
        validators = []


class MonthModelListSerializer(common_serializers.BaseCatalogListSerializer):
    weather = common_serializers.BaseCatalogListSerializer()
    season = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.MonthModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + ['weather', 'season']


class CityModelCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.CityModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + ['country']
        validators = []


class CityModelListSerializer(common_serializers.BaseCatalogListSerializer):
    country = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.CityModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + ['country']


class StreetModelCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.StreetModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + ['city']
        validators = []


class StreetModelListSerializer(common_serializers.BaseCatalogListSerializer):
    city = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.StreetModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + ['city']
