from django.urls import path
from . import apiviews

app_name = 'api_tickets'

urlpatterns = [
    path('ticket/<uuid:pk>/', apiviews.TicketDetailView.as_view(), name='ticket-detail'),
    path('ticket/<uuid:pk>/update/', apiviews.UpdateTicketView.as_view(), name='ticket-update'),
    path('form_info/', apiviews.TicketFormInfoView.as_view(), name='tickets-form-info'),
    path('new_ticket/', apiviews.CreateTicketView.as_view(), name='new-tickets-create'),
    path('ticket_type_options/', apiviews.TicketTypeOptionsView.as_view(), name='ticket-type-options'),
    path('configs_1c/', apiviews.Config1CListView.as_view(), name='config-1c-list'),
    path('tariffs_1c/', apiviews.Tariff1CListView.as_view(), name='tariffs-list'),
    path('list/', apiviews.TicketListView.as_view(), name='ticket-list'),
    path('ticket/<uuid:pk>/set_status/', apiviews.SetTicketStatusView.as_view(), name='set-ticket-status'),
    path('ticket/<uuid:pk>/action_info/', apiviews.ActionsInfoView.as_view(), name='action-info'),
]
