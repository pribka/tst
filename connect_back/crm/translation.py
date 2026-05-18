from modeltranslation.translator import translator, TranslationOptions
from .models import (
    CartTypeModel, GoodsOrderExecuteStatusModel, OrderOperationTypeModel,
    PayTypeModel, CashPayTypeModel, DeliveryStatusModel, PaymentStatusModel,
    DealStageModel,
    )


class CartTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class GoodsOrderExecuteStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class OrderOperationTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class PayTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class CashPayTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class DeliveryStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class PaymentStatusModelTranslationOptions(TranslationOptions):
    fields = ()


class DealStageModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(CartTypeModel, CartTypeModelTranslationOptions)
translator.register(GoodsOrderExecuteStatusModel, GoodsOrderExecuteStatusModelTranslationOptions)
translator.register(OrderOperationTypeModel, OrderOperationTypeModelTranslationOptions)
translator.register(PayTypeModel, PayTypeModelTranslationOptions)
translator.register(CashPayTypeModel, CashPayTypeModelTranslationOptions)
translator.register(DeliveryStatusModel, DeliveryStatusModelTranslationOptions)
translator.register(PaymentStatusModel, PaymentStatusModelTranslationOptions)
translator.register(DealStageModel, DealStageModelTranslationOptions)
