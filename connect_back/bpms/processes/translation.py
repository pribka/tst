from modeltranslation.translator import translator, TranslationOptions
from . import models


class WorkflowRequestTypeOptions(TranslationOptions):
    fields = (
        '_metadata',
    )


class WorkflowRequestStatusOptions(TranslationOptions):
    fields = ()


class WorkflowPositionOptions(TranslationOptions):
    fields = ()


class WorkflowRequestRouteStatusOptions(TranslationOptions):
    fields = ()


class WorkflowRequestRouteTemplateOptions(TranslationOptions):
    fields = ()


translator.register(models.WorkflowRequestTypeModel, WorkflowRequestTypeOptions)

translator.register(models.WorkflowRequestStatusModel, WorkflowRequestStatusOptions)

translator.register(models.WorkflowPositionModel, WorkflowPositionOptions)

translator.register(models.WorkflowRequestRouteStatusModel, WorkflowRequestRouteStatusOptions)

translator.register(models.WorkflowRequestRouteTemplateModel, WorkflowRequestRouteTemplateOptions)