from modeltranslation.translator import translator, TranslationOptions
from .models import SocialWebType, Unit, NewsCategoryModel, ProgramModel, CostingObjectModel, CounterpartyModel

class SocialWebTypeTranslationOptions(TranslationOptions):
    fields = ()


class UnitTranslationOptions(TranslationOptions):
    fields = ()


class NewsCategoryTranslationOptions(TranslationOptions):
    fields = ()


class ProgramTranslationOptions(TranslationOptions):
    fields = ()


class CostingObjectTranslationOptions(TranslationOptions):
    fields = ()


class CounterpartyTranslationOptions(TranslationOptions):
    fields = ()


translator.register(SocialWebType, SocialWebTypeTranslationOptions)
translator.register(Unit, UnitTranslationOptions)
translator.register(NewsCategoryModel, NewsCategoryTranslationOptions)
translator.register(ProgramModel, ProgramTranslationOptions)
translator.register(CostingObjectModel, CostingObjectTranslationOptions)
translator.register(CounterpartyModel, CounterpartyTranslationOptions)


