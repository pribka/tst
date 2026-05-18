from django.urls import path
from . import views
from rest_framework import routers
from django.conf.urls import include

app_name = 'api_chat'

router = routers.DefaultRouter()
# router.register("search", views.ChatSearchView, basename="chat-search")
router.register('message_templates', views.SupportMessageTemplateViewSet, basename='message-templates')
urlpatterns = [
    path('', include(router.urls)),
    path('list/', views.ChatListView.as_view(), name='chat-list'),
    path('<uuid:chat_uid>/detail/', views.ChatDetailView.as_view(), name='chat-detail'),
    path('<uuid:chat_uid>/summary/', views.ChatSummaryView.as_view(), name='chat-summary'),
    path('<uuid:chat_uid>/vks/', views.ChatVKSView.as_view(), name='chat-detail'),
    path('<uuid:chat_uid>/connect_vnc/', views.ConnectVNCView.as_view(), name='connect-vnc'),
    path('<uuid:chat_uid>/last_message/', views.LastMessageView.as_view(), name='last-message'),
    path('<uuid:chat_uid>/message/unread_entry/', views.MessageUnreadEntryView.as_view(), name='message-unread-entry'),
    path('<uuid:chat_uid>/message/history_after/', views.MessageHistoryAfterView.as_view(), name='message-history-after'),
    path('<uuid:chat_uid>/message/read_progress/', views.MessageReadProgressView.as_view(), name='message-read-progress'),
    path('message/<uuid:message_uid>/viewers/', views.MessageViewersListView.as_view(), name='message-viewers'),
    path('private/', views.ChatPrivateView.as_view(), name='private-chate'),
    path('message/list/', views.MessageListView.as_view(), name='message-list'),
    path('message/action_info/', views.MessageActionInfoView.as_view(), name='message-action-info'),
    path('message/count/', views.MessageCountView.as_view(), name='message-count'),
    path('message/search/', views.MessageSearchView.as_view(), name='message-search'),
    path('pinned_message/list/', views.PinnedMessageListView.as_view(), name='pinned-message-list'),
    path('member/list/', views.ChatMemberListView.as_view(), name='chat-member-list'),
    path('task/list/', views.ChatTaskListView.as_view(), name='chat-task-list'),
    path('member/set_last_message/', views.SetLastMessageView.as_view(), name='set-last-message'),
    path('users/', views.ChatUserListView.as_view(), name='chat-user-list'),
    path('recover_chat_rooms/', views.RecoverChatRooms.as_view(), name='recover_chat_rooms'),
    path('search/', views.AltChatSearchView.as_view(), name='alt-chat-search',),
    path('clear_message_cache/', views.ClearMessageKeysView.as_view(), name='clear-message-cache'),

    # path('create/', views.ChatCreateView.as_view(), name='chat-create'),
    # path('quit/', views.ChatQuitView.as_view(), name='chat-quit'),
    # path('delete/', views.ChatDeleteView.as_view(), name='chat-delete'),
    # path('rename/', views.ChatRenameView.as_view(), name='chat-rename'),
    # path('message/create/', views.MessageCreateView.as_view(), name='message-create'),
    # path('message/delete/', views.MessageDeleteView.as_view(), name='message-delete'),
    # path('message/pin/', views.MessagePinView.as_view(), name='message-pin'),
    # path('message/unpin/', views.MessageUnpinView.as_view(), name='message-unpin'),
    # path('message/unpin/all/', views.AllMessageUnpinView.as_view(), name='all-message-unpin'),
    # path('member/add/', views.ChatMemberAddView.as_view(), name='chat-member-add'),
    # path('member/delete/', views.ChatMemberDeleteView.as_view(), name='chat-member-delete'),
    # path('moderator/assign/', views.ModeratorAssignView.as_view(), name='moderator-assign'),
    # path('moderator/dismiss/', views.ModeratorDismissView.as_view(), name='moderator-dismiss'),
    # path('download_file/', views.download_file, name='download-file'),
]
