from django.contrib import admin
from common.admin import FileBaseModelInline
from crm.models import GoodsOrderModel
from . import models


class TaskVisorModelInline(admin.TabularInline):
    model = models.TaskVisor
    extra = 0
    autocomplete_fields = ('user',)


class TaskCooperatorModelInline(admin.TabularInline):
    model = models.TaskCooperator
    extra = 0
    autocomplete_fields = ('user',)
    fields = ('user', 'status',)


class TaskPrerequisiteModelInline(admin.TabularInline):
    fk_name = 'task'
    model = models.TaskPrerequisite
    extra = 0
    autocomplete_fields = ('prerequisite',)


class TaskTypeStatusModelInline(admin.TabularInline):
    model = models.TaskStatusTypeModel
    extra = 0
    fields = (
        'task_status',
        'next_status',
        'sort',
        'is_complete',
        'is_open',
    )


class TaskBudgetModelInline(admin.TabularInline):
    model = models.TaskBudgetModel
    extra = 0
    fields = (
        'cost_item',
        'quantity',
        'amount',
        'description',
    )
    fk_name = 'task'
    autocomplete_fields = ('cost_item',)


class TaskDifficultyModelInline(admin.TabularInline):
    model = models.TaskDifficulty
    extra = 0
    fields = (
        'criterion',
        'score',
    )
    fk_name = 'task'
    autocomplete_fields = ('criterion',)


class TaskStatusTypeDependsModelInline(admin.TabularInline):
    model = models.TaskStatusTypeDependsModel
    extra = 0
    fields = (
        'task_status',
    )


class TaskWorkTypeTaskTypeModelInline(admin.TabularInline):
    model = models.TaskWorkTypeTaskTypeModel
    extra = 0
    fields = (
        'work_type',
        'sort',
    )


class TaskDeliveryPointModelInline(admin.TabularInline):
    model = models.TaskDeliveryPointModel
    extra = 0
    fields = (
        'is_start',
        'delivery_point',
        'duration',
        'need_amount_pay',
        'sort',
        'delivery_date',
    )
    fk_name = 'task'
    autocomplete_fields = ('delivery_point',)


class TaskDeliveryModelInline(admin.TabularInline):
    model = models.TaskDeliveryModel
    extra = 0
    fields = (
        'good',
        'contractor',
        'amount',
        'quantity',
        'quantity_success',
        'success_date',
        'comment',
        'attachments',
    )
    autocomplete_fields = ('good', 'contractor', 'attachments')


class SprintHistoryInline(admin.TabularInline):
    model = models.TaskModel.sprint_history.through
    verbose_name = 'История спринтов'
    verbose_name_plural = 'История спринтов'
    extra = 0
    autocomplete_fields = ('tasksprintmodel',)


class GoodsOrderModelInline(admin.TabularInline):
    model = GoodsOrderModel
    extra = 0
    fk_name = 'task_delivery_point'
    autocomplete_fields = (
        'reason',
        'counter',
        'warehouse',
        'user',
        'contractor',
        'contractor_member',
        'contract',
        'delivery_company',
        'pay_file',
        'order_form',
    )


class TaskLoadedGoodsModelInline(admin.TabularInline):
    model = models.TaskLoadingGoodsModel
    extra = 0
    fk_name = 'task'
    autocomplete_fields = ('warehouse', 'goods', 'driver',)


@admin.register(models.TaskWorkTypeTaskTypeModel)
class TaskWorkTypeTaskTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'task_type',
        'work_type',
        'sort',
    )
    list_editable = ['sort']


@admin.register(models.TaskStatusWorkTypeConnectModel)
class TaskStatusWorkTypeConnectModel(admin.ModelAdmin):
    pass


@admin.register(models.TaskTypeModel)
class TaskTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'show_step',
    )
    inlines = (TaskTypeStatusModelInline, TaskWorkTypeTaskTypeModelInline)


@admin.register(models.TaskStatusTypeModel)
class TaskStatusTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'task_type',
        'task_status',
        'next_status',
        'is_complete',
        'is_open',
        'sort',
        'is_active',
    )
    list_editable = ['sort']
    inlines = (TaskStatusTypeDependsModelInline,)


@admin.register(models.TaskCounterModel)
class TaskCounterModelAdmin(admin.ModelAdmin):
    search_fields = ('pk',)

    def get_model_perms(self, request):
        return {}


@admin.register(models.TaskModel)
class TaskAdmin(admin.ModelAdmin):
    exclude = ('counter_old',)

    list_filter = (
        'task_type',
        'status',
        'is_active',
    )

    list_display = (
        'counter',
        'id',
        'owner',
        'operator',
        'name',
        'status',
        'finished_date',
        'project',
        'workgroup',
        'created_at',
        'is_active'
    )

    list_editable = [
        'project',
        'workgroup'
    ]

    search_fields = ('name', 'project__name', 'project__id', 'workgroup__name', 'workgroup__id', 'counter',)
    autocomplete_fields = (
        'sprint',
        'potential_contractor',
        'linked_chat',
        'parent',
        'owner',
        'operator',
        'workgroup',
        'project',
        'contractor',
        'sprint_history',
        'organization',
        'contract',
    )
    ordering = ('-created_at',)

    inlines = (
        FileBaseModelInline,
        TaskVisorModelInline,
        TaskCooperatorModelInline,
        TaskPrerequisiteModelInline,
        TaskBudgetModelInline,
        TaskDifficultyModelInline,
        TaskDeliveryPointModelInline,
        TaskLoadedGoodsModelInline,
        SprintHistoryInline,
    )


class TaskSprintProjectInline(admin.TabularInline):
    model = models.SprintProjectThroughModel
    fields = (
        'project',
    )
    autocomplete_fields = ('project',)
    fk_name = 'sprint'


class TasksInSprintInline(admin.TabularInline):
    model = models.TaskModel
    fields = ('id', 'name',)
    readonly_fields = ('id', 'name')
    fk_name = 'sprint'
    extra = 0


@admin.register(models.TaskSprintModel)
class TaskSprintAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'created_at',
        'updated_at',
        'deleted_at',
        'is_active',
    )
    search_fields = ('name',)
    readonly_fields = ('author', 'created_at', 'updated_at',)
    inlines = (TaskSprintProjectInline, TasksInSprintInline,)


@admin.register(models.UserTaskSort)
class UserTaskSortAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'task',
        'sort'
    )


@admin.register(models.TaskDeliveryModel)
class TaskDeliveryModelAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'contractor',
        'good',
    )
    readonly_fields = ('author',)


@admin.register(models.TaskExecutionTimeModel)
class TaskExecutionTimeModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_current',
        'author',
        'user',
        'task',
        'is_result',
        'sprint',
        'hours',
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at', 'task__name', 'author',)
    autocomplete_fields = ('task', 'author', 'user', 'sprint',)
    search_fields = ('task__name', 'task__counter', 'description',)
    readonly_fields = ('created_at', 'updated_at', 'author',)


@admin.register(models.TaskWorkTypeModel)
class TaskWorkTypeModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
    )


@admin.register(models.TaskStatusModel)
class TaskStatusModelAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'sort',
        'color',
        'btn_title',
        'progress',
    )
    readonly_fields = ('author',)
    ordering = ('sort',)
    list_editable = ['sort']


@admin.register(models.CostItemTaskModel)
class CostItemModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
    readonly_fields = ('author',)
    ordering = ('sort',)
    search_fields = ('name',)


@admin.register(models.TaskDifficultyCriterion)
class TaskDifficultyCriterionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'sort',
    )
    readonly_fields = ('author',)
    ordering = ('sort',)
    search_fields = ('name',)


@admin.register(models.TaskDeliveryPointModel)
class TaskDeliveryPointModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task',
        'delivery_point',
    )
    inlines = (
        GoodsOrderModelInline,
        TaskDeliveryModelInline,  # deprecated
    )
    search_fields = ('delivery_point__name',)
    autocomplete_fields = ('task', 'delivery_point',)


@admin.register(models.TaskLoadingGoodsModel)
class TaskLoadingGoodsModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task',
        'warehouse',
        'goods',
        'driver',
        'quantity',
    )
    autocomplete_fields = ('task', 'warehouse', 'goods', 'driver')
    readonly_fields = ('author', 'created_at', 'updated_at', 'deleted_at',)
    ordering = ('-created_at',)


@admin.register(models.TaskPointModel)
class TaskPointModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'lat',
        'lon',
        'task'
    )


@admin.register(models.LeadSourceModel)
class LeadSourceModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
    )


@admin.register(models.RejectionReasonModel)
class RejectionReasonModelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
    )


@admin.register(models.TaskSprintHistoryModel)
class TaskSprintHistoryModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sprint',
        'task',
        'moved_to',
        'moved_to_sprint',
        'created_at',
        'updated_at',
    )

    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('sprint', 'task', 'moved_to_sprint')
    search_fields = ('sprint__name', 'task__counter', 'task__name',)


@admin.register(models.SprintExpectedResultModel)
class SprintExpectedResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sprint',
        'task',
        'approved',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('author', 'created_at', 'updated_at',)
    autocomplete_fields = ('sprint', 'task',)
    search_fields = ('sprint__name', 'task__counter', 'task__name')
