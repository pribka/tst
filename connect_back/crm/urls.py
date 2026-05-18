from rest_framework.routers import DefaultRouter
from django.urls import include, path
from . import views

app_name = 'crm'
router = DefaultRouter()
router.register('shopping_cart', views.ShoppingCartModelViewSet, basename='shopping-cart')
router.register('return_cart', views.ReturnCartViewSet, basename='return-cart')
router.register('orders', views.GoodsOrderModelViewSet, basename='orders')
router.register('returns', views.ReturnOrderViewSet, basename='returns')
router.register('cash_pay_types', views.CashPayTypeModelViewSet, basename='cash-pay-types')
urlpatterns = [
    path('deals/', include('crm.deals_urls')),
    path('get_report/', views.GetReportAPIView.as_view(), name='get_report'),
    path('bitrix_form/', views.BitrixFormAPIView.as_view(), name='bitrix_form'),
    path('outer_hook/', views.BitrixOuterHookAPIView.as_view(), name='bitrix_outer_hook'),
    path('orders/search/', views.GoodsOrderSearchView.as_view(), name='orders-search'),
    path('contract/<uuid:contact_uid>/get_file/', views.ContractGetFileFrom1CView.as_view(), name='get_contract_file'),
    path('logistic_monitor/page_info/', views.LogisticMonitorPageInfo.as_view(), name='logistic-monitor-page-info'),
]

urlpatterns = urlpatterns + router.urls
