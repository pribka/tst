from modeltranslation.translator import TranslationOptions, translator

from . import models


class CurrencyModelTranslationOptions(TranslationOptions):
    fields = ()


class PriceTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class WarehouseModelTranslationOptions(TranslationOptions):
    fields = ()


class GoodsTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class MeasureUnitModelTranslationOptions(TranslationOptions):
    fields = (
        'name_short',
        'name_plural',
    )


class GoodsModelTranslationOptions(TranslationOptions):
    fields = ()


class GoodsCategoryModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractorModelTranslationOptions(TranslationOptions):
    fields = ('full_name',)


class ContractorRelationTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class ContractorDepartmentModelTranslationOptions(TranslationOptions):
    fields = ('full_name',)


class ContractorMemberModelTranslationOptions(TranslationOptions):
    fields = ('full_name',)


class PotentialContractorModelTranslationOptions(TranslationOptions):
    fields = ()


class CashUnitModelTranslationOptions(TranslationOptions):
    fields = ()


class PaymentFormModelTranslationOptions(TranslationOptions):
    fields = ()


class PaymentOptionModelTranslationOptions(TranslationOptions):
    fields = ()


class DeliveryPointModelTranslationOptions(TranslationOptions):
    fields = ()


class OfferModelTranslationOptions(TranslationOptions):
    fields = ()


class UserURLsModelTranslationOptions(TranslationOptions):
    fields = ()


class RegisterHelpModelTranslationOptions(TranslationOptions):
    fields = ()


class DeliveryPurposeModelTranslationOptions(TranslationOptions):
    fields = ()


class BankRequisitesModelTranslationOptions(TranslationOptions):
    fields = ()


class KlassificationCategoryModelTranslationOptions(TranslationOptions):
    fields = ()


class KlassificationDimensionModelTranslationOptions(TranslationOptions):
    fields = ()


class KlassificationModelTranslationOptions(TranslationOptions):
    fields = ()


class CostItemOptions(TranslationOptions):
    fields = ()


class LegalEntityOptions(TranslationOptions):
    fields = ()


class WorkDirectionOptions(TranslationOptions):
    fields = ()


translator.register(models.CurrencyModel, CurrencyModelTranslationOptions)
translator.register(models.PriceTypeModel, PriceTypeModelTranslationOptions)
translator.register(models.WarehouseModel, WarehouseModelTranslationOptions)
translator.register(models.GoodsTypeModel, GoodsTypeModelTranslationOptions)
translator.register(models.MeasureUnitModel, MeasureUnitModelTranslationOptions)
translator.register(models.GoodsModel, GoodsModelTranslationOptions)
translator.register(models.GoodsCategoryModel, GoodsCategoryModelTranslationOptions)
translator.register(models.ContractModel, ContractModelTranslationOptions)
translator.register(models.ContractorModel, ContractorModelTranslationOptions)
translator.register(models.ContractorRelationTypeModel, ContractorRelationTypeModelTranslationOptions)
translator.register(models.ContractorDepartmentModel, ContractorDepartmentModelTranslationOptions)
translator.register(models.ContractorMemberModel, ContractorMemberModelTranslationOptions)
translator.register(models.PotentialContractorModel, PotentialContractorModelTranslationOptions)
translator.register(models.CashUnitModel, CashUnitModelTranslationOptions)
translator.register(models.PaymentFormModel, PaymentFormModelTranslationOptions)
translator.register(models.PaymentOptionModel, PaymentOptionModelTranslationOptions)
translator.register(models.DeliveryPointModel, DeliveryPointModelTranslationOptions)
translator.register(models.OfferModel, OfferModelTranslationOptions)
translator.register(models.UserURLsModel, UserURLsModelTranslationOptions)
translator.register(models.RegisterHelpModel, RegisterHelpModelTranslationOptions)
translator.register(models.DeliveryPurposeModel, DeliveryPurposeModelTranslationOptions)
translator.register(models.BankRequisitesModel, BankRequisitesModelTranslationOptions)
translator.register(models.KlassificationModel, KlassificationModelTranslationOptions)
translator.register(models.KlassificationDimensionModel, KlassificationDimensionModelTranslationOptions)
translator.register(models.KlassificationCategoryModel, KlassificationCategoryModelTranslationOptions)
translator.register(models.CostItemModel, CostItemOptions)
translator.register(models.LegalEntityModel, LegalEntityOptions)
translator.register(models.WorkDirectionModel, WorkDirectionOptions)
