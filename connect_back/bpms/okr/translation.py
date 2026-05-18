from modeltranslation.translator import translator, TranslationOptions
from . import models


class ValueEffortsModelOptions(TranslationOptions):
    fields = ()

class ObjectiveStatusModelOptions(TranslationOptions):
    fields = ()

class InitiativesRelatedObjectTypeOptions(TranslationOptions):
    fields = ()

class NotificationFrequencyModelOptions(TranslationOptions):
    fields = ('description',)

class KeyResultMetricsModelOptions(TranslationOptions):
    fields = ('description',)

translator.register(models.ValueEffortsModel, ValueEffortsModelOptions)
translator.register(models.ObjectiveStatusModel, ObjectiveStatusModelOptions)
translator.register(models.InitiativesRelatedObjectType, InitiativesRelatedObjectTypeOptions)
translator.register(models.NotificationFrequencyModel, NotificationFrequencyModelOptions)
translator.register(models.KeyResultMetricsModel, KeyResultMetricsModelOptions)

