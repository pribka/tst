from modeltranslation.translator import translator, TranslationOptions

from . import models


class ContractorPermissionTypeModelTranslationOptions(TranslationOptions):
    fields = ()


class AccessGroupModelTranslationOption(TranslationOptions):
    fields = ()


class AppSectionModelTranslationOption(TranslationOptions):
    fields = (
        '_routes',
        '_mobile_routes'
    )


class AppSectionRoleModelTranslationOption(TranslationOptions):
    fields = ()


class ContractorPermissionRoleModelTranslationOption(TranslationOptions):
    fields = ()


translator.register(models.ContractorPermissionTypeModel, ContractorPermissionTypeModelTranslationOptions)


translator.register(models.AccessGroupModel, AccessGroupModelTranslationOption)

translator.register(models.AppSectionModel, AppSectionModelTranslationOption)

translator.register(models.ContractorPermissionRoleModel, ContractorPermissionRoleModelTranslationOption)

translator.register(models.AppSectionRoleModel, AppSectionRoleModelTranslationOption)
