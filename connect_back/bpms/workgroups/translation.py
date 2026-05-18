from modeltranslation.translator import translator, TranslationOptions
from .models import WorkgroupTypes, WorkgroupStatus, WorkgroupMembershipStatus, WorkgroupMembershipRole, WorkgroupMemberOrganizationStatusModel


class WorkgroupTypesTranslationOptions(TranslationOptions):
    fields = ()


class WorkgroupStatusTranslationOptions(TranslationOptions):
    fields = ()


class WorkgroupMembershipStatusTranslationOptions(TranslationOptions):
    fields = ()


class WorkgroupMembershipRoleTranslationOptions(TranslationOptions):
    fields = ()


class WorkgroupMemberOrganizationStatusModelTranslationOptions(TranslationOptions):
    fields = ()


translator.register(WorkgroupTypes, WorkgroupTypesTranslationOptions)
translator.register(WorkgroupStatus, WorkgroupStatusTranslationOptions)
translator.register(WorkgroupMembershipStatus, WorkgroupMembershipStatusTranslationOptions)
translator.register(WorkgroupMembershipRole, WorkgroupMembershipRoleTranslationOptions)
translator.register(WorkgroupMemberOrganizationStatusModel, WorkgroupMemberOrganizationStatusModelTranslationOptions)


