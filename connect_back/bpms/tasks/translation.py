from modeltranslation.translator import translator, TranslationOptions
from .models import (
    TaskScenarioModel, TaskTypeModel, TaskStatusModel,
    TaskWorkTypeModel, TaskDifficultyCriterion, CostItemTaskModel
    )

class TaskScenarioTranslationOptions(TranslationOptions):
    fields = ()


class TaskTypeTranslationOptions(TranslationOptions):
    fields = ()


class TaskStatusTranslationOptions(TranslationOptions):
    fields = ('btn_title',)


class  TaskWorkTypeTranslationOptions(TranslationOptions):
    fields = ()


class TaskDifficultyCriterionTranslationOptions(TranslationOptions):
    fields = ()


class CostItemTaskTranslationOptions(TranslationOptions):
    fields = ()


translator.register(TaskScenarioModel, TaskScenarioTranslationOptions)
translator.register(TaskTypeModel, TaskTypeTranslationOptions)
translator.register(TaskStatusModel, TaskStatusTranslationOptions)
translator.register(TaskWorkTypeModel, TaskWorkTypeTranslationOptions)
translator.register(TaskDifficultyCriterion, TaskDifficultyCriterionTranslationOptions)
translator.register(CostItemTaskModel, CostItemTaskTranslationOptions)


