from django.urls import path

from rest_framework import routers

from . import views

app_name = 'catalogs'
router = routers.DefaultRouter()
router.register(r'price_types', views.PriceTypeModelViewSet, basename='price-types')
router.register(r'warehouses', views.WarehouseModelViewSet, basename='warehouses')
router.register(r'goods', views.GoodsModelViewSet, basename='goods')
router.register(r'goods_category', views.GoodsCategoryModelViewSet, basename='goods-category')
router.register(r'delivery_addresses', views.DeliveryAddressesViewSet, basename='delivery-addresses')
router.register(r'contracts', views.ContractModelViewSet, basename='contracts')
router.register(r'contractors', views.ContractorModelViewSet, basename='contractors')
router.register(r'leads', views.PotentialContractorModelViewSet, basename='leads')
router.register(r'goods_remnants', views.GoodsRemnantModelViewSet, basename='goods-remnants')
router.register(r'goods_prices', views.GoodsPriceModelViewSet, basename='goods-prices')
router.register(r'payment_form', views.PaymentFormModelViewSet, basename='payment-form')
router.register(r'my_delivery_points', views.MyDeliveryPointsViewSet, basename='my_delivery_points')
router.register(r'delivery_purpose', views.DeliveryPurposeViewSet, basename='delivery-purpose')
router.register(r'contractor_relation_types', views.ContractorRelationTypesModelViewSet, basename='contractor-relation-types')
router.register(r'contractor_members', views.ContractorMemberModelViewSet, basename='contractor_members')
router.register(r'profile_requests', views.ContractorProfileRequestModel, basename='profile_requests')
router.register(r'location_admin_area', views.LocationAdminAreaViewSet, basename='location_admin_area')
router.register(r'nomenclature', views.NomenclatureViewSet, basename='nomenclature')
router.register(r'cost_items', views.CostItemViewSet, basename='cost-items')
router.register(r'work_directions', views.WorkDirectionViewSet, basename='work-directions')

urlpatterns = [
    path('user_offer/', views.OfferViewSet.as_view(), name='user_offer'),
    path('register_help/', views.RegisterHelpViewSet.as_view(), name='register_help'),
    path('urls_widget/', views.URLsWidgetViewSet.as_view(), name='urls_widget'),
    path('goods/search/', views.GoodsModelSearchView.as_view(), name='goods-search'),
    path('goods_category_structure/<uuid:pk>/', views.GoodCategoryTreeParentStructure.as_view(),
         name='goods-category-tree'),
    path('upload_contractors/', views.upload_contractors, name='upload-contractors'),
    path('create_contractors_from_dict/', views.CreateContractorsFromDict.as_view(), name='create-contractors-from-dict'),
    path('contractors_by_inn/', views.ContractorListByIIN.as_view(), name='contractors-by-inn'),
    path('contractor_from_egov/', views.GetContractorFromStatGovView.as_view(), name='contractor-from-egov'),
    path('contractors_report_file/', views.ContractorsReportFileView.as_view(), name='contractors-report-file'),
    path('kijlr3awx8_set_balances/', views.kijlr3awx8_set_balances, name='set-balances'),
    # path('location_admin_area/list/', views.LocationAdminAreaListView.as_view(), name='location-admin-area-list')
    path('block_contractor_users/', views.BlockContractorUsersView.as_view(), name='block-contractor_users'),
    path('unblock_contractor_users/', views.UnblockContractorUsersView.as_view(), name='unblock-contractor_users'),
    path('nomenclatures/autocomplete/', views.NomenclatureAutocomplete.as_view(), name='nomenclatures-autocomplete')

]
urlpatterns = urlpatterns + router.urls
