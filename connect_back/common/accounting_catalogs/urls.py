from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

app_name = 'accounting_catalogs'

router = DefaultRouter()
router.register(r'', views.ClassificationOfBudgetExpensesViewSet, basename='budget_expenses')
router.register(r'locations', views.LocationViewSet, basename='locations')

urlpatterns = [
    path('set_budget_administrators/', views.SetBudgetAdministrators.as_view(), name='set-budget-administrators'),
    path('set_kato_codes/', views.SetKATOCodes.as_view(), name='set-kato-codes'),
]

urlpatterns = urlpatterns + router.urls
