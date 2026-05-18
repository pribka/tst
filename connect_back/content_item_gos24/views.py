from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import requests
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response

from django.db import transaction
import uuid

from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from common.auth_classes import CsrfExemptSessionAuthentication
from common.paginators import CustomPagination
from common.views import BaseModelViewSet
from rest_framework import viewsets, status

from . import models, permissions, serializers
from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action


# class ContentItemRetrieveView(generics.RetrieveAPIView):
#     permission_classes = ()
#     queryset = models.ContentItem.objects.filter(is_active=True)
#     serializer_class = serializers.ContentItemSerializer
#
#
# class ContentItemListView(generics.ListAPIView):
#     permission_classes = (IsAuthenticated, )
#     queryset = models.ContentItem.objects.filter(is_active=True)
#     serializer_class = serializers.ContentItemSerializer
from .serializers import CalendarItemSerializer


class ArticleListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.ContentItem.objects.filter(is_active=True, kind='article')
    serializer_class = serializers.ArticleListViewSerializer
    pagination_class = CustomPagination

    # Поиск и сортировка
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description_clean', 'body_clean', 'slug']
    ordering_fields = ['publication_date', 'title', 'id']
    ordering = ['-created_at']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class NewsPublicationsListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.ContentItem.objects.filter(
        is_active=True, kind=models.ContentItem.KIND_NEWS_PUBLICATIONS_GOS24
    )
    serializer_class = serializers.NewsPublicationsListViewSerializer
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description_clean', 'body_clean', 'slug']
    ordering_fields = ['publication_date', 'title', 'id']
    ordering = ['-created_at']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class NewsFinanceListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.ContentItem.objects.filter(
        is_active=True, kind=models.ContentItem.KIND_NEWS_FINANCE
    )
    serializer_class = serializers.NewsPublicationsListViewSerializer
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description_clean', 'body_clean', 'slug']
    ordering_fields = ['publication_date', 'title', 'id']
    ordering = ['-created_at']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class OfficialListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.ContentItem.objects.filter(is_active=True, kind='official')
    serializer_class = serializers.OfficialListViewSerializer
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description_clean', 'body_clean', 'slug']
    ordering_fields = ['publication_date', 'title', 'id']
    ordering = ['-created_at']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()

class WebinarListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = models.ContentItem.objects.filter(is_active=True, kind='webinar')
    serializer_class = serializers.WebinarListViewSerializer
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'description_clean', 'slug']
    ordering_fields = ['planned_date', 'title', 'id']
    ordering = ['-created_at']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class QuestionListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = models.ContentItem.objects.filter(is_active=True, kind='qa').order_by(
        '-created_at'
    )
    serializer_class = serializers.QuestionListView
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description_clean', 'body_clean', 'slug', 'question_html', 'answer_html']

    @transaction.atomic
    def perform_update(self, serializer):
        # Сбрасываем флаг отправки в GOS24 при редактировании
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()

class KnowledgebaseListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = models.ContentItem.objects.filter(is_active=True, kind='knowledgebase').order_by(
        '-created_at'
    )
    serializer_class = serializers.KnowledgebaseViewSerializer
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'body_clean', 'slug']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()

class KnowledgebasePages(generics.ListAPIView):
    serializer_class = serializers.KnowledgebaseViewSerializer

    def get_queryset(self):
        type_page = self.request.query_params.get('type_page', None)
        tutorial_id = self.request.query_params.get('tutorial_id', None)

        if type_page == "1" and int(tutorial_id) > 0:
            queryset = models.ContentItem.objects.filter(
                is_active=True,
                content_type=type_page,
                pk=tutorial_id,
                kind='knowledgebase'
            )
        else:
            queryset = models.ContentItem.objects.filter(
                is_active=True,
                content_type=type_page,
                kind='knowledgebase'
            )
        return queryset

# class ContentItemListView(generics.ListAPIView):
#     permission_classes = ()
#     serializer_class = serializers.ContentItemSerializer
#     pagination_class = CustomPagination
#
#     def get_queryset(self):
#         kind = self.request.query_params.get('kind')
#         queryset = models.ContentItem.objects.select_related('author__profile').filter(
#             is_active=True,
#             kind=kind
#         ).order_by(
#             '-publication_date',
#             '-created',
#         )
#
#         sections = self.request.query_params.get('sections', None)
#         if sections is not None and sections != '':
#             queryset = queryset.filter(section_id__in=sections.split(','))
#
#         range_param = self.request.query_params.get('range', 'all')
#
#         if range_param and range_param != 'all':
#             now = timezone.now()
#
#             if range_param == 'week':
#                 start = now - timedelta(days=7)
#
#             elif range_param == 'month':
#                 # вариант 1 — «30 дней»
#                 start = now - timedelta(days=30)
#
#                 # вариант 2 — «календарный месяц ровно»
#                 # start = now - relativedelta(months=1)
#
#             elif range_param == 'year':
#                 # вариант 1 — «365 дней»
#                 start = now - timedelta(days=365)
#
#                 # вариант 2 — «ровно год»
#                 # start = now - relativedelta(years=1)
#
#             else:
#                 # неизвестное значение — игнорируем
#                 start = None
#
#             if start:
#                 queryset = queryset.filter(publication_date__gte=start)
#
#         tags_param = self.request.query_params.get('tags')
#         if tags_param:
#             tag_titles = [
#                 t.lstrip('#').strip()
#                 for t in tags_param.split(',')
#                 if t.strip()
#             ]
#             if tag_titles:
#                 queryset = queryset.filter(tags__title__in=tag_titles).distinct()
#
#         user = self.request.user
#         if not user.is_anonymous and user.profile.blog_admin:
#             pass
#         else:
#             queryset = queryset.filter(
#                 draft=False,
#                 publication_date__lte=timezone.now(),
#             )
#
#         return queryset
#
#     def list(self, request, *args, **kwargs):
#         data = super().list(request)
#         return Response(
#             data.data,
#             status=status.HTTP_200_OK
#         )



# class ContentItemCreateView(generics.CreateAPIView):
#     queryset = models.ContentItem.objects.all()
#     permission_classes = (IsAuthenticated, )
#     serializer_class = serializers.ContentItemCreateSerializer
#
#     def perform_create(self, serializer):
#         instance = serializer.save()  # <- ВАЖНО: получаем созданный объект
#
#         event = {
#             "event_id": str(uuid.uuid4()),
#             "event_type": "content_item.created",
#             "occurred_at": timezone.now().isoformat(),
#             "payload": {
#                 "id": instance.id,
#                 "kind": instance.kind,
#                 "title": instance.title,
#                 "slug": instance.slug,
#                 "publish": instance.publish,
#                 "draft": instance.draft,
#                 "publication_date": instance.publication_date.isoformat() if instance.publication_date else None,
#                 "only_subscribed": instance.only_subscribed,
#                 "description": instance.description,
#                 "body_html": instance.body_html,
#                 "author_id": getattr(instance, "author_id", None),
#                 "image": instance.image,
#             },
#             "idempotency_key": "content_item.created:{0}".format(instance.id),
#         }
#
#         def _send():
#             send_event(
#                 settings.KAFKA_TOPICS["content_item_created"],
#                 key=str(instance.id),  # партиционирование по id контента
#                 value=event,
#             )
#
#         # Отправляем ТОЛЬКО после успешного коммита сохранения ContentItem
#         transaction.on_commit(_send)


class OfficialClarificationOrganListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.OfficialClarificationOrganSerializer
    queryset = models.OfficialClarificationOrgan.objects.filter(is_active=True)
    pagination_class = CustomPagination

    # Поиск и сортировка
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['id', 'title']
    ordering = ['title']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class TagListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.filter(is_active=True)
    pagination_class = CustomPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['id', 'name']
    ordering = ['name']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class PartitionListView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.PartitionSerializer
    queryset = models.Partition.objects.filter(is_active=True)
    pagination_class = CustomPagination

    # Поиск и сортировка
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['id', 'name', 'code']
    ordering = ['name']

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save(sent_gos=False)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.sent_gos = False
        instance.save()


class UploadNewsFileView(APIView):
    authentication_classes = (
        JWTAuthentication,
        BasicAuthentication,
        CsrfExemptSessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        REMOTE_UPLOAD_URL = "https://gos24.kz/api/v2/common/upload/"
        if not request.FILES:
            raise ValidationError({'message': 'File not found.'})
        files = request.FILES.getlist('upload')
        instances = []
        for f in files:
            multipart = {
                'file': (f.name, f, getattr(f, 'content_type', 'application/octet-stream')),
            }

            resp = requests.post(
                REMOTE_UPLOAD_URL,
                files=multipart,
                timeout=60,
            )
            resp.raise_for_status()


            # Ожидаем, что удалённый сервер вернёт JSON с данными файла (id/url/и т.п.)
            try:
                data = resp.json()
            except ValueError:
                data = {'filename': f.name, 'detail': 'No JSON from remote'}

            instances.append(data)
        return JsonResponse(data=instances, status=status.HTTP_200_OK, safe=False)


class UploadNewsForEditorView(APIView):
    authentication_classes = (
        JWTAuthentication,
        BasicAuthentication,
        CsrfExemptSessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        REMOTE_UPLOAD_URL = "https://gos24.kz/api/v2/common/upload/"

        if not request.FILES:
            raise ValidationError({'message': 'File not found.'})
        file = request.FILES.getlist('upload')[0]

        multipart = {
            'file': (file.name, file, getattr(file, 'content_type', 'application/octet-stream')),
        }

        resp = requests.post(
            REMOTE_UPLOAD_URL,
            files=multipart,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return JsonResponse(data={"urls": data}, status=status.HTTP_200_OK, safe=False)


class CalendarItemViewSet(viewsets.ModelViewSet):
    """
    Работаем ТОЛЬКО с ContentItem(kind='calendar').
    Поддерживает:
      - GET /calendar-items/?start=YYYY-MM-DD&end=YYYY-MM-DD
      - POST /calendar-items/upsert/      body: {date:'YYYY-MM-DD', content_type:'holiday'|'workday', title?, description?}
      - DELETE /calendar-items/by_date/?date=YYYY-MM-DD
      - POST /calendar-items/bulk/        body: {items:[{date, content_type, title?, description?}, ...]}
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CalendarItemSerializer

    def get_queryset(self):
        qs = models.ContentItem.objects.filter(kind=models.ContentItem.KIND_CALENDAR, is_active=True)
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start and end:
            qs = qs.filter(common_date__range=[start, end])
        elif start:
            qs = qs.filter(common_date__gte=start)
        elif end:
            qs = qs.filter(common_date__lte=end)
        return qs.order_by('common_date')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['kind'] = models.ContentItem.KIND_CALENDAR
        return super().create(request.__class__(data=data), *args, **kwargs)

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def upsert(self, request):
        """
        Создать/обновить по дате.
        body: { "date": "2025-01-01", "content_type": "holiday"|"workday", "title": "", "description": "" }
        """
        date = (request.data or {}).get('date')
        ctype = (request.data or {}).get('content_type')
        if not date or ctype not in ('holiday', 'workday'):
            return Response({"detail": "date и content_type('holiday'|'workday') обязательны"}, status=400)

        del_cal = models.ContentItem.objects.filter(
            kind=models.ContentItem.KIND_CALENDAR,
            common_date=date,
            is_active=True,
        )
        for it in del_cal:
            it.is_active = False
            it.sent_gos = False
            it.save()

        obj = models.ContentItem.objects.create(
            kind=models.ContentItem.KIND_CALENDAR,
            common_date=date,
            is_active=True,
            content_type=ctype,
            title=request.data.get("title", "") or "",
            description=request.data.get("description", "") or "",
            publish=True,
            sent_gos=False,
        )

        return Response(CalendarItemSerializer(obj).data, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['delete'])
    def by_date(self, request):
        """
        Удалить запись по дате.
        query: ?date=YYYY-MM-DD
        """
        d = request.query_params.get('date')
        if not d:
            return Response({"detail": "date обязателен"}, status=400)
        deleted = models.ContentItem.objects.filter(kind=models.ContentItem.KIND_CALENDAR, common_date=d).first()
        deleted.is_active = False
        deleted.sent_gos = False
        deleted.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        Массовый upsert.
        body: { "items": [{ "date":"YYYY-MM-DD", "content_type":"holiday"|"workday", "title":"", "description":"" }, ...] }
        """
        items = request.data.get('items') or []
        out = []
        for it in items:
            d = it.get('date')
            ctype = it.get('content_type')
            if not d or ctype not in ('holiday', 'workday'):
                continue
            obj, created = models.ContentItem.objects.get_or_create(
                kind=models.ContentItem.KIND_CALENDAR,
                common_date=d,
                is_active=True,
                defaults={
                    "content_type": ctype,
                    "title": it.get("title", "") or "",
                    "description": it.get("description", "") or "",
                    "publish": True,
                }
            )
            if not created:
                obj.content_type = ctype
                obj.sent_gos = False
                if "title" in it:       obj.title = it.get("title") or ""
                if "description" in it: obj.description = it.get("description") or ""
                obj.full_clean()
                obj.save(update_fields=["content_type", "title", "description", "updated_at", "sent_gos"])
            out.append(obj)
        return Response(CalendarItemSerializer(out, many=True).data, status=200)


class CalendarFinanceItemViewSet(viewsets.ModelViewSet):
    """
    Работаем ТОЛЬКО с ContentItem(kind='calendar').
    Поддерживает:
      - GET /calendar-items/?start=YYYY-MM-DD&end=YYYY-MM-DD
      - POST /calendar-items/upsert/      body: {date:'YYYY-MM-DD', content_type:'holiday'|'workday', title?, description?}
      - DELETE /calendar-items/by_date/?date=YYYY-MM-DD
      - POST /calendar-items/bulk/        body: {items:[{date, content_type, title?, description?}, ...]}
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = CalendarItemSerializer

    def get_queryset(self):
        qs = models.ContentItem.objects.filter(kind=models.ContentItem.KIND_CALENDAR_FINANCE, is_active=True)
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start and end:
            qs = qs.filter(common_date__range=[start, end])
        elif start:
            qs = qs.filter(common_date__gte=start)
        elif end:
            qs = qs.filter(common_date__lte=end)
        return qs.order_by('common_date')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['kind'] = models.ContentItem.KIND_CALENDAR_FINANCE
        return super().create(request.__class__(data=data), *args, **kwargs)

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def upsert(self, request):
        """
        Создать/обновить по дате.
        body: { "date": "2025-01-01", "content_type": "holiday"|"workday", "title": "", "description": "" }
        """
        date = (request.data or {}).get('date')
        ctype = (request.data or {}).get('content_type')
        if not date or ctype not in ('holiday', 'workday'):
            return Response({"detail": "date и content_type('holiday'|'workday') обязательны"}, status=400)
        del_cal = models.ContentItem.objects.filter(
            kind=models.ContentItem.KIND_CALENDAR_FINANCE,
            common_date=date,
            is_active=True,
        )
        for it in del_cal:
            it.is_active = False
            it.sent_gos = False
            it.save()
        
        obj = models.ContentItem.objects.create(
            kind=models.ContentItem.KIND_CALENDAR_FINANCE,
            common_date=date,
            is_active=True,
            content_type=ctype,
            title=request.data.get("title", "") or "",
            description=request.data.get("description", "") or "",
            publish=True,
            sent_gos=False,
        )

        return Response(CalendarItemSerializer(obj).data, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=['delete'])
    def by_date(self, request):
        """
        Удалить запись по дате.
        query: ?date=YYYY-MM-DD
        """
        d = request.query_params.get('date')
        if not d:
            return Response({"detail": "date обязателен"}, status=400)
        deleted = models.ContentItem.objects.filter(kind=models.ContentItem.KIND_CALENDAR_FINANCE, common_date=d).first()
        deleted.is_active = False
        deleted.sent_gos = False
        deleted.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        Массовый upsert.
        body: { "items": [{ "date":"YYYY-MM-DD", "content_type":"holiday"|"workday", "title":"", "description":"" }, ...] }
        """
        items = request.data.get('items') or []
        out = []
        for it in items:
            d = it.get('date')
            ctype = it.get('content_type')
            if not d or ctype not in ('holiday', 'workday'):
                continue
            obj, created = models.ContentItem.objects.get_or_create(
                kind=models.ContentItem.KIND_CALENDAR_FINANCE,
                common_date=d,
                is_active=True,
                defaults={
                    "content_type": ctype,
                    "title": it.get("title", "") or "",
                    "description": it.get("description", "") or "",
                    "publish": True,
                }
            )
            if not created:
                obj.content_type = ctype
                obj.sent_gos = False
                if "title" in it:       obj.title = it.get("title") or ""
                if "description" in it: obj.description = it.get("description") or ""
                obj.full_clean()
                obj.save(update_fields=["content_type", "title", "description", "updated_at", "sent_gos"])
            out.append(obj)
        return Response(CalendarItemSerializer(out, many=True).data, status=200)

