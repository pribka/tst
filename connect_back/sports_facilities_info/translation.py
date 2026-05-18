from modeltranslation.translator import translator, TranslationOptions
from . import models


class SportFacilityOwnershipFormOptions(TranslationOptions):
    fields = ()


class SportFacilityTypeOptions(TranslationOptions):
    fields = ('full_name',)


class SportFacilityPurposeOptions(TranslationOptions):
    fields = ('full_name',)


class SportFacilityStatusOptions(TranslationOptions):
    fields = ('btn_title',)


class SportTypeCategoryOptions(TranslationOptions):
    fields = (
        'full_name',
    )


class SportTypeOptions(TranslationOptions):
    fields = (
        'full_name',
    )


class SportFacilityRenovationWorkTypeOptions(TranslationOptions):
    fields = (
        'full_name',
    )


class SportFacilityRenovationTypeOptions(TranslationOptions):
    fields = ()


class SportBuildingPurposeModelOptions(TranslationOptions):
    fields = ()


class SportBuildingTypeModelOptions(TranslationOptions):
    fields = ()


class SportBuildingTechnicalConditionModelOptions(TranslationOptions):
    fields = ()


class SportBuildingFloorCoveringTypeModelOptions(TranslationOptions):
    fields = ()


class SportGroupTypeCatalogOptions(TranslationOptions):
    fields = ('name_plural',)


class SportCoachTypeCatalogOptions(TranslationOptions):
    fields = ('name_plural',)


class SportFacilityHeatingTypeModelOptions(TranslationOptions):
    fields = ()

translator.register(models.SportFacilityOwnershipFormModel, SportFacilityOwnershipFormOptions)

translator.register(models.SportFacilityTypeModel, SportFacilityTypeOptions)

translator.register(models.SportFacilityPurposeModel, SportFacilityPurposeOptions)

translator.register(models.SportFacilityStatusModel, SportFacilityStatusOptions)

translator.register(models.SportTypeCategoryModel, SportTypeCategoryOptions)

translator.register(models.SportTypeModel, SportTypeOptions)

translator.register(models.SportFacilityRenovationWorkTypeModel, SportFacilityRenovationWorkTypeOptions)

translator.register(models.SportFacilityRenovationTypeModel, SportFacilityRenovationTypeOptions)

translator.register(models.SportBuildingPurposeModel, SportBuildingPurposeModelOptions)

translator.register(models.SportBuildingTypeModel, SportBuildingTypeModelOptions)

translator.register(models.SportBuildingTechnicalConditionModel, SportBuildingTechnicalConditionModelOptions)

translator.register(models.SportBuildingFloorCoveringTypeModel, SportBuildingFloorCoveringTypeModelOptions)

translator.register(models.SportGroupTypeCatalog, SportGroupTypeCatalogOptions)

translator.register(models.SportCoachTypeCatalog, SportCoachTypeCatalogOptions)

translator.register(models.SportFacilityHeatingTypeModel, SportFacilityHeatingTypeModelOptions)
