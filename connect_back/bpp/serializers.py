from django.db.models import Sum
from rest_framework import serializers
from rest_framework.validators import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from common import serializers as common_serializers
from common import models as common_models
from . import models


# Edition
class EditionCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.EditionModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + ['is_periodic']
        validators = []


class EditionListSerializer(common_serializers.BaseCatalogListSerializer):
    unit_count = serializers.SerializerMethodField()
    unit_amount = serializers.SerializerMethodField()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.EditionModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + ['is_periodic',
                                                                             'unit_count',
                                                                             'unit_amount']

    @staticmethod
    def get_unit_count(instance):
        count = common_models.AssetInWarehouse.get_count(asset_owner=instance)
        if count:
            count = int(count)
        else:
            count = 0
        return count

    @staticmethod
    def get_unit_amount(instance):
        amount = common_models.AssetInWarehouse.get_amount(asset_owner=instance)
        if not amount:
            amount = 0
        return amount


# EditionPart
class EditionPartCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    def validate_edition(self, data):
        if data and data.is_periodic is False:
            raise ValidationError('Edition is not periodic')
        return data

    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.EditionPartModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + ['edition']
        validators = []


class EditionPartListSerializer(common_serializers.BaseCatalogListSerializer):
    edition = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.EditionPartModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + ['edition']


# EditionAuthor
class EditionAuthorCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.EditionAuthorModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields
        validators = []


class EditionAuthorListSerializer(common_serializers.BaseCatalogListSerializer):
    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.EditionAuthorModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields


# EditionPublisher
class EditionPublisherCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.EditionPublisherModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields
        validators = []


class EditionPublisherListSerializer(common_serializers.BaseCatalogListSerializer):
    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.EditionPublisherModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields


# EditionUnit
class EditionUnitCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    # def validate_edition_part(self, data):
    #     if data:
    #         edition_code = self.initial_data.get('edition')
    #         if not data.edition.code == edition_code:
    #             raise ValidationError(_('Invalid Edition part'))
    #     return data
    #
    # def validate_edition(self, data):
    #     if data:
    #         edition_part = self.initial_data.get('edition_part')
    #         if edition_part and data.is_periodic is False:
    #             raise ValidationError(_('Edition is not periodic'))
    #     return data

    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.EditionUnitModel
        fields = common_serializers.BaseCatalogCUDSerializer.Meta.fields + [
            # 'edition',
            'edition_part',
            'inventory_number'
        ]
        validators = []


class EditionUnitListSerializer(common_serializers.BaseCatalogListSerializer):
    # edition = common_serializers.BaseCatalogListSerializer()
    edition_part = common_serializers.BaseCatalogListSerializer()
    invoice = common_serializers.BaseCatalogListSerializer()
    warehouse = common_serializers.BaseCatalogListSerializer()
    income_source = common_serializers.BaseCatalogListSerializer()
    expense = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseCatalogListSerializer.Meta):
        model = models.EditionUnitModel
        fields = common_serializers.BaseCatalogListSerializer.Meta.fields + [
            # 'edition',
            'edition_part',
            'invoice',
            'inventory_number',
            'warehouse',
            'actual_price',
            'income_source',
            'income_date',
            'income_number',
            'expense',
            'edition_name',
        ]


# IncomingInvoice
class IncomingInvoiceCUDSerializer(common_serializers.BaseDocumentCUDSerializer):
    class Meta(common_serializers.BaseDocumentCUDSerializer):
        model = models.ReceiptInvoiceEditionUnitModel
        fields = common_serializers.BaseDocumentCUDSerializer.Meta.fields + [
            'source_of_receipt',
            'default_warehouse',
        ]
        validators = []

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            edition_units_list = self.initial_data.get('edition_units', dict()).get('edit')
            if isinstance(edition_units_list, list):
                for each in edition_units_list:
                    if not instance.tp_editions.filter(units=each.get('id')).exists():
                        continue
                    try:
                        obj = models.EditionUnitModel.objects.get(pk=each.get('id'))
                    except models.EditionUnitModel.DoesNotExist:
                        continue
                    edition_unit_serializer = EditionUnitCUDSerializer(instance=obj, data=each, partial=True)
                    edition_unit_serializer.is_valid(raise_exception=True)
                    edition_unit_serializer.save()
            edition_units_delete = self.initial_data.get('edition_units', dict()).get('delete')
            if isinstance(edition_units_delete, list):
                models.EditionUnitModel.objects.filter(pk__in=edition_units_delete, invoice__owner=instance).delete()
            return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        total_amount = instance.tp_editions.aggregate(value=Sum('amount'))
        data['total_amount'] = total_amount['value']
        return data


class IncomingInvoiceListSerializer(common_serializers.BaseDocumentListSerializer):
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, instance):
        return getattr(instance, 'total_amount', None)

    class Meta(common_serializers.BaseDocumentListSerializer.Meta):
        model = models.ReceiptInvoiceEditionUnitModel
        fields = common_serializers.BaseDocumentListSerializer.Meta.fields + [
            'source_of_receipt',
            'total_amount'
        ]


class IncomingInvoiceDetailSerializer(common_serializers.BaseDocumentDetailSerializer):
    source_of_receipt = common_serializers.BaseCatalogListSerializer()
    default_warehouse = common_serializers.BaseCatalogListSerializer()
    total_amount = serializers.SerializerMethodField()

    def get_total_amount(self, instance):
        return instance.total_amount

    class Meta(common_serializers.BaseDocumentDetailSerializer):
        model = models.ReceiptInvoiceEditionUnitModel
        fields = common_serializers.BaseDocumentDetailSerializer.Meta.fields + [
            # 'edition_units_amount',
            'source_of_receipt',
            'default_warehouse',
            'total_amount'
        ]


# TP IncomingInvoice

class TPReceiptInvoiceEditionModelCUDSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(allow_null=False, default=0)
    price = serializers.DecimalField(allow_null=True, max_digits=16, decimal_places=2, default=0)

    # edition = serializers.PrimaryKeyRelatedField(allow_null=False, required=True, queryset=models.EditionModel.objects.filter(is_active=True))

    class Meta:
        model = models.TPReceiptInvoiceEditionModel
        fields = ('id', 'owner', 'edition', 'price', 'quantity', 'amount', 'warehouse')

    def create(self, validated_data):
        quantity = validated_data.pop('quantity', 1)
        if quantity == 0:
            quantity = 1
        if not validated_data.get('price'):
            validated_data['price'] = 0
        instance = super().create(validated_data)
        instance.create_units(quantity)
        instance.set_price()
        return instance

    def update(self, instance, validated_data):
        quantity = validated_data.pop('quantity', 0)
        if not validated_data.get('price'):
            validated_data['price'] = 0
        instance = super().update(instance, validated_data)
        instance.create_units(quantity)
        instance.set_price()
        return instance


class TPReceiptInvoiceEditionModelListSerializer(common_serializers.BaseModelSerializer):
    edition = common_serializers.BaseCatalogListSerializer()
    quantity = serializers.SerializerMethodField()
    warehouse = common_serializers.BaseCatalogListSerializer()

    def get_quantity(self, instance):
        return instance.units.filter(is_active=True).count()

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPReceiptInvoiceEditionModel
        fields = common_serializers.BaseModelSerializer.Meta.fields + ['edition', 'price', 'quantity', 'amount',
                                                                       'warehouse']


# class TPReceiptInvoiceEditionUnitModelCUDSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.TPReceiptInvoiceEditionUnitModel
#         fields = ('id', 'owner', 'unit')
#
#
# class TPReceiptInvoiceEditionUnitModelListSerializer(common_serializers.BaseModelSerializer):
#     unit = common_serializers.BaseCatalogListSerializer()
#     price = serializers.SerializerMethodField()
#
#     def get_price(self, instance):
#         return getattr(instance.invoice_edition, 'price', None)
#
#     class Meta(common_serializers.BaseModelSerializer):
#         model = models.TPReceiptInvoiceEditionUnitModel
#         fields = common_serializers.BaseModelSerializer.Meta.fields + ['unit', 'price']


# ActWriteOff
class ActWriteOffCUDSerializer(common_serializers.BaseDocumentCUDSerializer):
    class Meta(common_serializers.BaseDocumentCUDSerializer):
        model = models.ActWriteOffEditionUnitModel
        fields = common_serializers.BaseDocumentCUDSerializer.Meta.fields
        validators = []


class ActWriteOffListSerializer(common_serializers.BaseDocumentListSerializer):
    # source_of_receipt = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseDocumentListSerializer.Meta):
        model = models.ActWriteOffEditionUnitModel
        fields = common_serializers.BaseDocumentListSerializer.Meta.fields


class ActWriteOffDetailSerializer(common_serializers.BaseDocumentDetailSerializer):
    class Meta(common_serializers.BaseDocumentDetailSerializer):
        model = models.ActWriteOffEditionUnitModel
        fields = common_serializers.BaseDocumentDetailSerializer.Meta.fields

    # TP IncomingInvoice


class TPActWriteOffEditionModelCUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPActWriteOffEditionModel
        fields = ('id', 'owner', 'unit')

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        return instance


class TPActWriteOffEditionModelListSerializer(common_serializers.BaseModelSerializer):
    # quantity = serializers.SerializerMethodField()
    unit = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPActWriteOffEditionModel
        fields = common_serializers.BaseModelSerializer.Meta.fields + ['unit']


# EditionUnitTransfer
class EditionUnitTransferCUDSerializer(common_serializers.BaseDocumentCUDSerializer):
    class Meta(common_serializers.BaseDocumentCUDSerializer):
        model = models.EditionUnitTransferModel
        fields = common_serializers.BaseDocumentCUDSerializer.Meta.fields
        validators = []


class EditionUnitTransferListSerializer(common_serializers.BaseDocumentListSerializer):
    class Meta(common_serializers.BaseDocumentListSerializer.Meta):
        model = models.EditionUnitTransferModel
        fields = common_serializers.BaseDocumentListSerializer.Meta.fields


class EditionUnitTransferDetailSerializer(common_serializers.BaseDocumentDetailSerializer):
    class Meta(common_serializers.BaseDocumentDetailSerializer):
        model = models.EditionUnitTransferModel
        fields = common_serializers.BaseDocumentDetailSerializer.Meta.fields


class TPEditionUnitTransferModelCUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TPEditionUnitTransferModel
        fields = ('id', 'owner', 'unit', 'recipient_warehouse')

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        return instance


class TPEditionUnitTransferModelListSerializer(common_serializers.BaseModelSerializer):
    unit = common_serializers.BaseCatalogListSerializer()
    recipient_warehouse = common_serializers.BaseCatalogListSerializer()

    class Meta(common_serializers.BaseModelSerializer):
        model = models.TPEditionUnitTransferModel
        fields = common_serializers.BaseModelSerializer.Meta.fields + ['unit', 'recipient_warehouse']
