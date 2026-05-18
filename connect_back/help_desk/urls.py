from django.urls import path

from rest_framework import routers



from . import views

app_name = 'help_desk'
router = routers.DefaultRouter()
router.register(r'customer_cards', views.CustomerCardModelViewSet, basename='customer_carts')
router.register(r'config', views.HelpDeskConfigViewSet, basename='help_desk_config')
router.register(r'contact_persons/messages', views.ContactPersonMessageViewSet, basename='contact_perons_messages')
router.register(r'contact_persons', views.ContactPersonViewSet, basename='contact-perons')
router.register(r'tickets', views.HelpDeskTicketViewSet, basename='help_desk_tickets')
router.register(r'admins', views.CustomerCardAdminViewSet, basename='customer-card-admins')
router.register(r'ticket_categories', views.HelpDeskTicketCategoryViewSet, basename='ticket-categories'),
router.register(r'contact_person_post', views.ContactPersonPostViewSet, basename='contact-person-post')
router.register(r'costs', views.HelpDeskCostViewSet, basename='help-desk-costs')

urlpatterns = [
    path(r'telegram/bot/<uuid:pk>/', views.HelpdeskTelegramHandlerView.as_view(), name='telegram-handler'),
    path('tickets/statuses/', views.HelpDeskTicketStatusListView.as_view(), name='ticket-statuses'),
    path(
        'tickets/assign_analytics_key/',
        views.HelpDeskTicketViewSet.as_view({'post': 'assign_analytics_key'}),
        name='ticket-assign-analytics-key',
    ),
    path('upload_customer_cards/', views.upload_customer_cards, name='upload-customer-cards'),
    path('my_org_admins/', views.ClientOrgAdminView.as_view(), name='my-org-admins'),
    path('select_org_admin/', views.SelectedOrgAdminView.as_view(), name='select-org-admin'),
    path('org_admin/<uuid:pk>/action_info/', views.HelpDeskOrgAdminActionInfo.as_view(), name='org-admin-action-info'),
    path('default_ticket_visor/', views.DefaultTicketVisorView.as_view(), name='default-ticket-visor'),
    path('<uuid:ticket_id>/help_desk_costs/', views.hep_desk_costs, name='help-desk-costs'),
    path('set_specialists_in_all_customers/', views.SetSpecialistsInAllCustomers.as_view(), name='set-specialists-in-all-customers')
]

urlpatterns = urlpatterns + router.urls
