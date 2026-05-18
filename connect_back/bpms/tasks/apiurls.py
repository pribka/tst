from django.urls import path
from . import apiviews
from rest_framework import routers
from django.conf.urls import include

app_name = 'api_tasks'

urlpatterns = [
    path('task/bulk_create/', apiviews.BulkCreateTaskView.as_view(), name='task-bulk-create'),
    path('task/bulk_delete/', apiviews.BulkDeleteTaskView.as_view(), name='task-bulk-create'),
    path('task/create/', apiviews.CreateTaskView.as_view(), name='task-create'),
    path(
        'task/assign_contract/',
        apiviews.TaskModelViewSet.as_view({'post': 'assign_contract'}),
        name='task-assign-contract'
    ),
    path('task/create_from_order/', apiviews.CreateTaskFromOrderView.as_view(), name='task-create-from-order'),
    path('task/delete/', apiviews.DeleteTaskView.as_view(), name='task-delete'),
    path('task/<uuid:pk>/update/', apiviews.UpdateTaskView.as_view(), name='task-update'),
    # path('task/<uuid:pk>/', apiviews.DetailTaskView.as_view(), name='task-detail'), # Перенесено в TaskModelViewSet 23.09.2025
    path('task/<uuid:pk>/by_secret_status/', apiviews.UpdateBySecretStatusTaskView.as_view(), name='update-status-by-secret'),
    path('task/<uuid:pk>/status/', apiviews.UpdateStatusTaskView.as_view(), name='update-status'),
    path('task/<uuid:pk>/pin/', apiviews.TaskPinView.as_view(), name='task-pin'),
    path('task/<uuid:pk>/cooperator_status/', apiviews.UpdateCooperatorStatusTaskView.as_view(), name='update-cooperator-status'),
    path('task/<uuid:pk>/set_rejection_reason/', apiviews.UpdateRejectionReasonTaskView.as_view(), name='update-rejection-reason'),
    path('task/<uuid:pk>/take/', apiviews.TakeAuctionTaskView.as_view(), name='take-task-status'),
    path('task/<uuid:pk>/update_operator/', apiviews.UpdateOperatorTaskView.as_view(), name='task-update-operator'),
    path('task/<uuid:pk>/update_deadline/', apiviews.UpdateDeadlineTaskView.as_view(), name='task-update-deadline'),
    path('task/<uuid:pk>/update_owner/', apiviews.UpdateOwnerTaskView.as_view(), name='task-update-owner'),
    path('task/<uuid:pk>/update_reason/', apiviews.UpdateReasonTaskView.as_view(), name='task-update-reason'),
    path('task/<uuid:pk>/set_sprint/', apiviews.SetSprintTaskView.as_view(), name='task=set-sprint'),
    path('task/bulk_set_sprint/', apiviews.BulkSetSprintTaskView.as_view(), name='bulk-set-sprint'),
    path('week_stats_operator/', apiviews.WeekOperatorStatsView.as_view(), name='task=set-sprint'),
    path('task/list/', apiviews.ListTaskView.as_view(), name='task-list'),
    path('list_from_reason/', apiviews.TaskListFromReason.as_view(), name='task-from-reason'),
    path('task_members/', apiviews.TaskMembersListView.as_view(), name='task-members-list'),
    path('task/list/points/', apiviews.ListTaskPointsView.as_view(), name='task-points-list'),
    path('task/my_tasks_count/', apiviews.MyTasksCountView.as_view(), name='my-tasks-count'),
    path('task/calendar/', apiviews.ListCalendarTaskView.as_view(), name='task-calendar'),
    path('task_kanban/<uuid:pk>/status/', apiviews.UpdateKanbanStatusTaskView.as_view(), name='update-kanban-status'),
    path('task_kanban/list/', apiviews.ListKanbanTaskView.as_view(), name='task-kanban-list'),
    path('task_kanban/status_count/', apiviews.CountKanbanStatusView.as_view(), name='task-kanban-status-count'),
    path('tasks_chart_gantt/list/', apiviews.ListChartGanttTaskView.as_view(), name='task-gantt-list'),
    path('tasks_chart_gantt_v2/list/', apiviews.ListChartGanttTaskView_v2.as_view(), name='task-gantt-list_v2'),
    path('sprint/create/', apiviews.CreateSprintView.as_view(), name='sprint-create'),
    path('sprint/<uuid:pk>/update/', apiviews.UpdateSprintView.as_view(), name='sprint-update'),
    path('sprint/<uuid:pk>/update_status/', apiviews.UpdateTaskSprintStatusView.as_view(), name='sprint-status-update'),
    path('sprint/<uuid:pk>/tasks_list/', apiviews.ListTasksBySprintListView.as_view(), name='tasks-by-sprint-list'),
    path('sprint/<uuid:pk>/tasks_count/', apiviews.TaskCountSprintView.as_view(), name='tasks-count-sprint'),
    path('sprint/<uuid:pk>/', apiviews.DetailSprintView.as_view(), name='sprint-detail'),
    path('sprint/<uuid:pk>/expected_results/', apiviews.SprintExpectedResultView.as_view(), name='sprint-expected-result'),
    path('sprint/<uuid:pk>/members/', apiviews.SprintMemberListView.as_view(), name='sprint-members'),
    path('sprint/<uuid:pk>/analytics/', apiviews.SprintAnalyticView.as_view(), name='sprint-analytics'),
    path('sprint/expected_results/<uuid:pk>/update/', apiviews.SprintExpectedResultUpdateView.as_view(), name='sprint-expected-result-update'),
    path('sprint/list/', apiviews.ListSprintView.as_view(), name='sprint-list'),
    path('sprint/task/list/', apiviews.ListSprintTaskView.as_view(), name='tasks-sprint-list'),
    # path('sprint/<uuid:pk>/report/', apiviews.ReportSprintView.as_view(), name='sprint-report'),
    path('sprint/<uuid:pk>/report/time_tracking/', apiviews.ReportTimeSprintView.as_view(), name='sprint-time-report'),
    path('sprint/<uuid:pk>/report/file/', apiviews.ReportFileSprintView.as_view(), name='sprint-report-file'),
    path('sprint/<uuid:pk>/report/tasks/', apiviews.ReportTasksSprintView.as_view(), name='sprint-tasks-report'),
    path('sprint/<uuid:pk>/action_info/', apiviews.SprintActionInfoView.as_view(), name='sprint-action-info'),
    path('sprint/select_list/', apiviews.SelectListSprintView.as_view(), name='sprint-select-list'),
    path('import_task_from_urv/', apiviews.ImportTaskFromUrv.as_view(), name='task-from-urv'),
    path('get_lead_task/', apiviews.GetLeadTask.as_view(), name='get-lead-tasks'),
    path('task/search/', apiviews.TaskSearchView.as_view(), name='task-search'),
    path('task_status/', apiviews.TaskStatusListView.as_view(), name='task-status'),
    path('analytics/', apiviews.TaskAnalyticsView.as_view(), name='task-analytics'),
    path('analytics/file/', apiviews.TaskAnalyticsFileView.as_view(), name='task-analytics-file'),
    path('task_list/file/', apiviews.TaskListFileView.as_view(), name='task-list-file'),
    path('interest_list/file/', apiviews.InterestListFileView.as_view(), name='interest-list-file'),
    path('table_info/', apiviews.TableInfoView.as_view(), name='table-info'),
    path('<uuid:pk>/action_info/', apiviews.ActionsInfoView.as_view(), name='action-info'),
    path('delivery/<uuid:pk>/', apiviews.UpdateDeliveryView.as_view(), name='update-delivery'),
    path('<uuid:pk>/goods/', apiviews.TaskGoodsView.as_view(), name='task-goods'),
    path('<uuid:pk>/goods_by_warehouses/', apiviews.GoodsByWarehousesView.as_view(), name='goods-by-warehouses'),
    path('load_goods/', apiviews.TaskLoadingCreateView.as_view(), name='load-goods'),
    path('<uuid:pk>/payment_to_warehouses/', apiviews.TaskPaymentToWarehousesView.as_view(), name='amount-paid'),
    path('<uuid:pk>/delivery_points/create/', apiviews.TaskDeliveryPointCreateView.as_view(), name='create-delivery-points'),
    path('<uuid:pk>/delivery_points/delete/', apiviews.TaskDeliveryPointDeleteView.as_view(), name='delivery-point-delete'),
    path('<uuid:pk>/delivery_points/orders/delete/', apiviews.TaskDeliveryPointDeleteOrdersView.as_view(), name='delivery-point-delete-order'),
    path('<uuid:pk>/delivery_points/', apiviews.TaskDeliveryPointListView.as_view(), name='task-delivery-points'),
    path('<uuid:pk>/delivery_points/update/', apiviews.TaskDeliveryPointUpdateView.as_view(), name='task-delivery-points-update'),
    path('delivery_points/<uuid:pk>/need_amount_pay/', apiviews.TaskDeliveryPointSetNeedPayAmount.as_view(), name='set-need-pay-amount'),
    path('plus_one_day_logistic/', apiviews.LogisticTaskPlusOneDay.as_view(), name='logistic-plus-data'),
    path('task/<uuid:pk>/sort_delivery_points/', apiviews.TaskDeliveryPointSortView.as_view(),
         name='sort-delivery-points'),
    path('form_info/', apiviews.TaskFormInfoView.as_view(), name='task-form-info'),
    path('form_info/points/', apiviews.TaskPointsInfoView.as_view(), name='task-points-info'),
    path('form_info/lead_sources/', apiviews.LeadSourcesView.as_view(), name='lead-sources'),
    path('form_info/rejection_reason/', apiviews.RejectionReasonsView.as_view(), name='rejection-reasons'),
    path('drivers/', apiviews.DriverListView.as_view(), name='driver-list'),
    path('delete_void_logistic_tasks/', apiviews.DeleteVoidLogisticTasks.as_view(), name='del-void-log-tasks'),
    path('efficiency/<uuid:pk>/', apiviews.EfficiencyView.as_view(), name='efficiency'),
    path('<uuid:pk>/time_tracking/start/', apiviews.TaskExecutionTimeStartView.as_view(), name='time-tracking-start'),
    path('<uuid:pk>/time_tracking/stop/', apiviews.TaskExecutionTimeStopView.as_view(), name='time-tracking-stop'),
    path('<uuid:pk>/time_tracking/duration/', apiviews.TaskExecutionTimeDurationView.as_view(), name='time-tracking-duration'),

]
router = routers.DefaultRouter()
router.register(r"time_tracking", apiviews.TaskExecutionTimeModelViewSet, "time-tracking")
router.register(r"budget", apiviews.TaskBudgetModelViewSet, 'task-budget', )
router.register(r"interest_needs", apiviews.TaskInterestNeedViewSet, 'task-interest-needs')
router.register(r"difficulty", apiviews.TaskDifficultyModelViewSet, 'task-difficulty')
router.register(r"onboarding", apiviews.OnboardingTasksViewSet, 'onboarding-tasks')
router.register(r"task", apiviews.TaskModelViewSet, 'task')
urlpatterns = urlpatterns + router.urls
