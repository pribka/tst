from modeltranslation.translator import translator, TranslationOptions
from .models import (
    TypeOfEmployment, SeasonModel, WeatherModel, MonthModel,
    CountryModel, CityModel, StreetModel, MyCatalog
)

class TypeOfEmploymentTranslationOptions(TranslationOptions):
    fields = ()


class SeasonModelTranslationOptions(TranslationOptions):
    fields = ()


class WeatherModelTranslationOptions(TranslationOptions):
    fields = ()


class MonthModelTranslationOptions(TranslationOptions):
    fields = ()


class CountryModelTranslationOptions(TranslationOptions):
    fields = ()


class CityModelTranslationOptions(TranslationOptions):
    fields = ()


class StreetModelTranslationOptions(TranslationOptions):
    fields = ()


class MyCatalogTranslationOptions(TranslationOptions):
    fields = ()


translator.register(TypeOfEmployment, TypeOfEmploymentTranslationOptions)
translator.register(SeasonModel, SeasonModelTranslationOptions)
translator.register(WeatherModel, WeatherModelTranslationOptions)
translator.register(MonthModel, MonthModelTranslationOptions)
translator.register(CountryModel, CountryModelTranslationOptions)
translator.register(CityModel, CityModelTranslationOptions)
translator.register(StreetModel, StreetModelTranslationOptions)
translator.register(MyCatalog, MyCatalogTranslationOptions)