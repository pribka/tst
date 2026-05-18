from rest_framework import routers
from django.urls import path
from . import views

app_name = 'integration_1c'

router = routers.DefaultRouter()

router.register('', views.WriteObjectsFrom1CViewSet, basename='write-objects',)

urlpatterns = router.urls + [
    # path('', views.WriteObjectsFrom1CViewSet.as_view(), name='write-objects'),
    path('send_data/', views.ExternalImportData.as_view(), name='send-data'),
    path('get_structure/', views.ModelStructureToImportData.as_view(), name='model-structure'),
    path('delete_objects/', views.DeleteObjects.as_view(), name='delete-objects'),
    path('send_work_type/', views.SendWorkTypeView.as_view(), name='send_work_type'),
    path('send_goods/', views.SendGoods.as_view(), name='send_goods'),
    path('send_price_type/', views.SendPriceTypes.as_view(), name='send_prices'),
    path('send_goods_prices/', views.SendGoodsPrices.as_view(), name='send_goods_prices'),
    path('send_contract/', views.SendContract.as_view(), name='send_contract'),
    path('send_type_of_payment/', views.SendTypeOfPayment.as_view(), name='send_type_of_payment'),
    path('send_goods_category/', views.SendGoodsCategory.as_view(), name='send_goods_category'),
    path('send_goods_image/', views.SendGoodImages.as_view(), name='send_goods_image'),
    path('send_contract_contractor_relation/', views.SendContractContractorRelation.as_view(),
         name='send_contract_contractor_relation'),
    path('send_order_to_1c/', views.SendOrderTo1C.as_view(), name='send_order_to_1c'),
    path('send_warehouse/', views.SendWarehouse.as_view(), name='send_warehouse'),
    path('send_goods_remnant/', views.SendGoodsRemnant.as_view(), name='send_goods_remnant'),
    path('send_contractor_addresses/', views.SendContractorAddress.as_view(), name='send_contractor_addresses'),
    path('send_task_files/', views.SendTaskFiles.as_view(), name='send_task_files'),
    path('send_order_status/', views.SendGoodsOrderExecuteStatuses.as_view(), name='send_order_status'),
    path('send_task_scenario/', views.SendTaskScenarion.as_view(), name='send_task_scenario'),
    path('test_get_remnants/', views.TestGetRemnants.as_view(), name='test_get_remnants'),
    path('send_new_order_status/', views.UpdateOrderStatus.as_view(), name='update_order_status'),
    path('send_order_payment_status/', views.SendOrderPaymentStatus.as_view(), name='send-order-payment-status'),
    path('send_cash_payment/', views.SendCashPayment.as_view(), name='send_cash_payment'),
    path('update_file/', views.CustomUpdateFile.as_view(), name='update_file'),
    path('get_loading_docs/<uuid:pk>/', views.GetLoadingDocs.as_view(), name='loading_docs_update'),
    path('get_loading_docs/', views.GetLoadingDocs.as_view(), name='loading_docs_list'),
    path('send_file_codes/', views.SendFileCodes.as_view(), name='send_file_codes'),
    path('set_is_active/', views.SetIsActive.as_view(), name='set-is-active'),
    path('get_my_docs/', views.GetMyDoc1cList.as_view(), name='my_doc_list'),
    path('get_file_from_1c/', views.GetMyFileFrom1C.as_view(), name='get_my_doc_1c'),

    path('0589710a2ef6433da0a600e3ca67fd37/', views.IsolatedGetRemnants.as_view()),  # Начальные остатки
    path('ca21fd6aff004259b93eb116b016481f/', views.IsolatedCheckOrderForm.as_view()),
    # path('test/', views.update_file_from_1c_view),
    # Проерка готовности печатной формы  заказа
    path('6c964844cca34a82bbcb23d4600a3166/', views.IsolatedCheckOrderPayFile.as_view()),
    # Проверка готовности файла на оплату заказа
    path('get_pay_file/', views.GetPayFileFrom1C.as_view(), name='get_pay_file'),
]
