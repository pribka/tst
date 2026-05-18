from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .import_gos24.views import TransferConnectTagImportAPIView, TransferConnectPartitionImportAPIView, \
    TransferConnectNewsImportAPIView, TransferConnectArticleImportAPIView, \
    TransferConnectOfficialClarificationOrganImportAPIView, TransferConnectOfficialClarificationImportAPIView, \
    TransferConnectQuestionImportAPIView, TransferConnectWebinarImportAPIView, TransferConnectKnowledgebaseImportAPIView
from .views import CalendarItemViewSet, CalendarFinanceItemViewSet

app_name = 'content_item_gos24'

router = DefaultRouter()
router.register('article', views.ArticleListView, basename='article')
router.register('news_publications', views.NewsPublicationsListView, basename='news_publications')
router.register('news_finance', views.NewsFinanceListView, basename='news_finance')
router.register('official', views.OfficialListView, basename='official')
router.register('webinar', views.WebinarListView, basename='webinar')
router.register('question', views.QuestionListView, basename='question')

router.register('knowledgebase', views.KnowledgebaseListView, basename='knowledgebase')
router.register('partition', views.PartitionListView, basename='partition')
router.register('organ', views.OfficialClarificationOrganListView, basename='partition')
router.register('tag', views.TagListView, basename='tag')
router.register(r'calendar-items', CalendarItemViewSet, basename='calendar-item')
router.register(r'calendar-finance-items', CalendarFinanceItemViewSet, basename='calendar-item')
urlpatterns = [
    # path('organs/', views.OfficialClarificationOrganListView.as_view(), name='official_clarification-organs-list'),
    # path('partition/', views.PartitionListView.as_view(), name='partition-list'),
    path('knowledgebase/pages/', views.KnowledgebasePages.as_view(), name='knowledgebase-pages'),
    path('upload_news_file/', views.UploadNewsFileView.as_view(), name='upload_news_file'),
    path('upload_for_editor/', views.UploadNewsForEditorView.as_view(), name='upload_for_editor'),
    # path('', views.ContentItemListView.as_view(), name='content-item-list'),
    # path('<int:pk>/', views.ContentItemRetrieveView.as_view(), name='content-item-detail'),
    # path("content-items/create/", views.ContentItemCreateView.as_view(), name="contentitem-create"),

    path('transfer-connect/tags/import/', TransferConnectTagImportAPIView.as_view(), name='transfer-connect-tag-import'),
    path('transfer-connect/partition/import/', TransferConnectPartitionImportAPIView.as_view(), name='transfer-connect-tag-import'),
    path('transfer-connect/official-organs/import/', TransferConnectOfficialClarificationOrganImportAPIView.as_view(), name='transfer-connect-official-organs-import'),

    path('transfer-connect/news/import/', TransferConnectNewsImportAPIView.as_view(), name='transfer-connect-news-import'),
    path('transfer-connect/article/import/', TransferConnectArticleImportAPIView.as_view(), name='transfer-connect-article-import'),
    path('transfer-connect/official/import/', TransferConnectOfficialClarificationImportAPIView.as_view(), name='transfer-connect-official-organs-import'),
    path('transfer-connect/question/import/', TransferConnectQuestionImportAPIView.as_view(), name='transfer-connect-question-import'),
    path('transfer-connect/webinar/import/', TransferConnectWebinarImportAPIView.as_view(), name='transfer-connect-webinar-import'),
    path('transfer-connect/knowledgebase/import/', TransferConnectKnowledgebaseImportAPIView.as_view(), name='transfer-connect-knowledgebase-import'),
]

urlpatterns = urlpatterns + router.urls
