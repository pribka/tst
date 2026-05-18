from django.urls import path
from . import apiviews
from rest_framework import routers

app_name = 'api_meetings'

urlpatterns = [
    # path('meeting/', apiviews.MeetingView.as_view(), name='get-meeting-url'),
    # path('connect/<int:pk>/', apiviews.ConnectMeetingView.as_view(), name='connect-to-meeting'),

    path('set_complete/', apiviews.set_meeting_complete, name='set-complete'),
    path('set_record_ready/', apiviews.set_record_ready, name='set-record-ready'),
    path('end_meeting/', apiviews.MeetingEndView.as_view(), name='meeting-end'),
    path('<uuid:pk>/connect/', apiviews.ConnectPlannedMeetingView.as_view(), name='connect-to-pm'),
    path('<uuid:pk>/restart/', apiviews.RestartPlannedMeetingView.as_view(), name='restart-pm'),
    path('<uniq>/connect_external/', apiviews.ExternalLoginPlannedMeetingView.as_view(), name='external-connect-to-pm'),
    path('<uuid:pk>/update/', apiviews.PlannedMeetingUpdate.as_view(), name='planned-meeting-update'),
    path('<uuid:pk>/members/add/', apiviews.PlannedMeetingAddMember.as_view(), name='planned-meeting-add-memeber'),
    path('<uuid:pk>/members/delete/', apiviews.PlannedMeetingDeleteMember.as_view(),
         name='planned-meeting-delete-member'),
    path('members/', apiviews.PlannedMeetingMemberListView.as_view(), name='planned-meeting-member-list'),
    path('moderator/update/', apiviews.PlannedMeetingModeratorUpdate.as_view(), name='meeting-moderator-update'),
    path('', apiviews.PlannedMeetingFilteredList.as_view(), name='planned-meeting-list'),
    path('<uuid:pk>/detail/', apiviews.MeetingDetailView.as_view(), name='meeting-detail'),
    path('<uuid:pk>/records/', apiviews.PlannedMeetingRecordings.as_view(), name='planned-meeting-records'),
    path('records/<uuid:pk>/', apiviews.MeetingRecordDetailView.as_view(), name='meeting-record-detail'),
    path('records/<uuid:pk>/transcribe/', apiviews.MeetingRecordTranscribeView.as_view(), name='meeting-record-transcribe'),
    path('create/', apiviews.PlannedMeetingCreateView.as_view(), name='planned-meeting-create'),

    path('search/', apiviews.MeetingSearchView.as_view(), name='meeting-search'),
    path('update-members/', apiviews.trigger_update_meeting_members, name='update-meeting-members'),
    path('start-related/', apiviews.StartRelatedMeetingView.as_view(), name='start-related-meeting'),
    
]

router = routers.DefaultRouter()
router.register(r"meeting", apiviews.MeetingModelViewSet, 'meeting')
router.register(r"sections", apiviews.MeetingSectionModelViewSet, "sections")
router.register(r"records", apiviews.MeetingRecordsModelViewSet, "records")
router.register(r"calls", apiviews.CallViewSet, "calls")
urlpatterns = urlpatterns + router.urls
