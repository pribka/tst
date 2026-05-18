import json
import hashlib
import logging

from django.db import transaction
from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import get_template
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import generics
from common.views import BaseModelViewSet
from telebot.apihelper import ApiTelegramException

from common.utils import get_filter_queryset, get_tariff_section_codes, order_queryset_from_get_param
from telegram_bot.base import base_bot
from users.models import ProfileModel
from users.notifications import notify_about_new_sign_request
from . import models, paginators, serializers, utils
from bkz3.settings import DID_SALT

logger = logging.getLogger(__name__)


class WebNotificationViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.WebNotificationSerializer
    queryset = models.WebNotificationModel.objects.filter(is_active=True).select_related('event_type__category')
    permission_classes = (IsAuthenticated,)
    pagination_class = paginators.WebNotificationPagination
    model = models.WebNotificationModel

    def get_queryset(self):
        """Базовый per-user queryset со всеми фильтрами (без ordering).
        Переиспользуется в list / grouped / retrieve / mark-as-read."""
        request = self.request
        profile = request.user.profile
        queryset = get_filter_queryset(
            request,
            models.WebNotificationModel,
            self.queryset.filter(webnotificationrecipientmodel__recipient=profile).annotate(
                read_at=F('webnotificationrecipientmodel__read_at'),
                is_read=F('webnotificationrecipientmodel__is_read'),
            ),
        )
        if profile.hide_read_notifications:
            queryset = queryset.filter(is_read=False)
        exclude_category_raw = request.query_params.get('exclude_category', '')
        exclude_category_codes = [
            category_code.strip() for category_code in exclude_category_raw.split(',') if category_code.strip()
        ]
        if exclude_category_codes:
            queryset = queryset.exclude(event_type__category__in=exclude_category_codes)
        object_id = request.query_params.get('object_id')
        if object_id:
            queryset = queryset.filter(object_id=object_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = order_queryset_from_get_param(request, models.WebNotificationModel, queryset)
        if not queryset.ordered:
            queryset = queryset.order_by('-created_at')
        page = self.paginate_queryset(queryset)
        items = page if page is not None else list(queryset)
        data = self.get_serializer(items, many=True).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    @staticmethod
    def _apply_group_stats(base_qs, items):
        """Проставляет на инстансы transient-атрибуты group_total/group_unread."""
        object_ids = [item.object_id for item in items if item.object_id]
        stats_map = {}
        if object_ids:
            rows = (
                base_qs.filter(object_id__in=object_ids)
                .values('object_id')
                .annotate(
                    total=Count('pk'),
                    unread=Count('pk', filter=Q(is_read=False)),
                )
            )
            stats_map = {row['object_id']: row for row in rows}

        for obj in items:
            oid = getattr(obj, 'object_id', None)
            stats = stats_map.get(oid) if oid else None
            if stats:
                obj.group_total = stats['total']
                obj.group_unread = stats['unread']
            else:
                obj.group_total = 1
                obj.group_unread = 0 if getattr(obj, 'is_read', False) else 1

    @action(methods=['get'], detail=False, url_path='grouped', url_name='grouped')
    def grouped_list(self, request, *args, **kwargs):
        """Сгруппированный список: по одной «голове» на object_id (самое свежее уведомление).
        Уведомления без object_id — каждое своей одиночной группой.

        Чтобы не гонять тяжёлый per-user queryset в паджинаторе (JOIN recipient + сортировка),
        материализуем head-список (pk, created_at), сортируем/пагинируем в Python,
        а полную выборку со всеми аннотациями делаем только для PK-ов страницы.
        """
        base = self.get_queryset()

        # DISTINCT ON (object_id) на PG-стороне — только для grouped (object_id IS NOT NULL).
        # Ungrouped (object_id IS NULL) являются сами себе «головой».
        grouped_head_rows = list(
            base.filter(object_id__isnull=False)
            .order_by('object_id', '-created_at')
            .distinct('object_id')
            .values_list('pk', 'created_at')
        )
        ungrouped_rows = list(
            base.filter(object_id__isnull=True).values_list('pk', 'created_at')
        )
        head_rows = grouped_head_rows + ungrouped_rows
        head_rows.sort(key=lambda row: row[1], reverse=True)

        page_rows = self.paginate_queryset(head_rows)
        if page_rows is None:
            page_rows = head_rows
        page_pks = [pk for pk, _ in page_rows]

        # Полная выборка (аннотации is_read/read_at, select_related event_type__category/content_type)
        # — только для страницы.
        by_pk = {
            item.pk: item
            for item in base.filter(pk__in=page_pks).select_related('content_type')
        }
        items = [by_pk[pk] for pk in page_pks if pk in by_pk]

        self._apply_group_stats(base, items)
        serializer_context = self.get_serializer_context()
        serializer_context['grouped_mode'] = True
        data = self.get_serializer(items, many=True, context=serializer_context).data

        if self.paginator is not None and hasattr(self.paginator, 'get_paginated_response'):
            return self.get_paginated_response(data)
        return Response(data)

    @action(methods=['get', ], detail=False, url_path='unread_count', url_name='unread_count')
    def get_unread_count(self, request, *args, **kwargs):
        base_qs = models.WebNotificationModel.objects.filter(
            recipients=request.user.profile,
            is_active=True,
            webnotificationrecipientmodel__is_read=False
        )
        non_mention_qs = base_qs.filter(event_type__is_mention=False)
        unread_count = non_mention_qs.count()
        unread_by_category = dict(
            non_mention_qs.values('event_type__category__code')
            .annotate(count=Count('id'))
            .values_list('event_type__category__code', 'count')
        )
        unread_mentions_count = base_qs.filter(event_type__is_mention=True).count()
        return Response({
            'unread_count': unread_count,
            'unread_by_category': unread_by_category,
            'unread_mentions_count': unread_mentions_count,
        })

    @action(methods=['post', ],
            detail=False,
            url_path='tg_unsubscribe',
            url_name='tg_unsubscribe')
    def tg_unsubscribe(self, request, *args, **kwargs):
        user = request.user.profile
        if user.telegram_id is not None:
            tg_id = user.telegram_id
            try:
                base_bot.send_message(
                    text='Вы отписались от уведомлений',
                    chat_id=tg_id
                )
            except ApiTelegramException as e:
                if e.error_code == 403:
                    tg_recipients = ProfileModel.objects.filter(
                        telegram_id=tg_id
                    )
                    tg_recipients.update(telegram_id=None)
            user.telegram_id = None
            user.save(update_fields=('telegram_id',))
            data = 'Вы отписались от уведомлений'
        else:
            data = 'Аккаунт не привязан'

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, url_path='is_read', url_name='is_read')
    def post_is_read(self, request, *args, **kwargs):
        notifications_id = request.data.get('notifications', None)
        categories = request.data.get('category', None)
        is_mention = request.data.get('is_mention', None)
        object_id = request.data.get('object_id', None)

        base_qs = models.WebNotificationRecipientModel.objects.filter(
            recipient=request.user.profile,
        )

        if object_id is not None:
            base_qs = base_qs.filter(notification__object_id=object_id)

        recipients = None
        if isinstance(notifications_id, list):
            recipients = base_qs.filter(notification__id__in=notifications_id)
        elif notifications_id == 'all':
            recipients = base_qs.filter(is_read=False)
        elif object_id is not None:
            recipients = base_qs.filter(is_read=False)

        if categories:
            recipients = recipients.filter(
                notification__event_type__category__in=categories,
            )

        if is_mention is not None:
            recipients = recipients.filter(
                notification__event_type__is_mention=is_mention,
            )

        now = timezone.now()
        updated_count = recipients.update(read_at=now, is_read=True)

        return Response(
            {
                'read_at': serializers.serializers.DateTimeField().to_representation(now),
                'updated': updated_count,
                'category': categories or [],
                'is_mention': is_mention,
                'object_id': object_id,
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=['get', ], detail=False, url_path='test_notify', url_name='test_notify')
    def test_web_notify(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('forbidden')
        user_id = request.GET['id']
        try:
            user = ProfileModel.objects.get(id=user_id)
        except ProfileModel.DoesNotExist:
            return HttpResponse('user not found.', status=status.HTTP_400_BAD_REQUEST)
        async_task(utils.send_test_message, user.pk, request.user.profile)
        return HttpResponse('ok')

    @action(methods=['post'], detail=False, url_path='devices/register', url_name='devices-register')
    def register_mobile_push_device(self, request, *args, **kwargs):
        token = str(request.data.get('token', '') or '').strip()
        platform = str(request.data.get('platform', '') or '').strip().lower()
        push_provider = str(
            request.data.get('push_provider', models.MobilePushDeviceModel.PROVIDER_FCM) or ''
        ).strip().lower()
        device_id = str(request.data.get('device_id', '') or '').strip()
        app_version = str(request.data.get('app_version', '') or '').strip()
        locale = str(request.data.get('locale', '') or '').strip()
        metadata = request.data.get('metadata') if isinstance(request.data.get('metadata'), dict) else {}

        logger.info(
            'Mobile push register requested user_id=%s profile_id=%s platform=%s provider=%s device_id=%s token_prefix=%s',
            getattr(request.user, 'id', None),
            getattr(getattr(request.user, 'profile', None), 'id', None),
            platform,
            push_provider,
            device_id,
            token[:12],
        )

        if not token:
            raise ValidationError({'token': 'This field is required.'})
        if platform not in dict(models.MobilePushDeviceModel.PLATFORM_CHOICES):
            raise ValidationError({'platform': 'Unsupported platform.'})
        if push_provider not in dict(models.MobilePushDeviceModel.PROVIDER_CHOICES):
            raise ValidationError({'push_provider': 'Unsupported push provider.'})

        now = timezone.now()
        device, created = models.MobilePushDeviceModel.objects.update_or_create(
            token=token,
            defaults={
                'profile': request.user.profile,
                'platform': platform,
                'push_provider': push_provider,
                'device_id': device_id,
                'app_version': app_version,
                'locale': locale,
                'is_active': True,
                'last_seen_at': now,
                'last_error': '',
                'metadata': metadata,
            },
        )

        deactivated = 0
        if device_id:
            deactivated = models.MobilePushDeviceModel.objects.filter(
                profile=request.user.profile,
                platform=platform,
                push_provider=push_provider,
                device_id=device_id,
                is_active=True,
            ).exclude(pk=device.pk).update(
                is_active=False,
                last_seen_at=now,
            )

        return Response(
            {
                'id': device.id,
                'created': created,
                'deactivated': deactivated,
                'is_active': device.is_active,
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=['post'], detail=False, url_path='devices/unregister', url_name='devices-unregister')
    def unregister_mobile_push_device(self, request, *args, **kwargs):
        token = str(request.data.get('token', '') or '').strip()
        device_id = str(request.data.get('device_id', '') or '').strip()

        logger.info(
            'Mobile push unregister requested user_id=%s profile_id=%s device_id=%s token_prefix=%s',
            getattr(request.user, 'id', None),
            getattr(getattr(request.user, 'profile', None), 'id', None),
            device_id,
            token[:12],
        )

        if not token and not device_id:
            raise ValidationError({'detail': 'token or device_id is required.'})

        queryset = models.MobilePushDeviceModel.objects.filter(
            profile=request.user.profile,
            is_active=True,
        )
        if token:
            queryset = queryset.filter(token=token)
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        updated = queryset.update(
            is_active=False,
            last_seen_at=timezone.now(),
        )
        return Response({'updated': updated}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='webpush/register', url_name='webpush-register')
    def register_web_push_subscription(self, request, *args, **kwargs):
        serializer = serializers.WebPushRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = serializer.validated_data['subscription']
        now = timezone.now()
        defaults = {
            'profile': request.user.profile,
            'endpoint': subscription['endpoint'],
            'p256dh': subscription['p256dh'],
            'platform': subscription.get('platform', '').strip(),
            'browser': subscription.get('browser', '').strip(),
            'metadata': subscription.get('metadata', {}),
            'last_error': '',
            'last_seen_at': now,
            'is_active': True,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:2000],
        }
        models.WebPushSubscriptionModel.objects.update_or_create(
            auth=subscription['auth'],
            defaults=defaults,
        )
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='webpush/update', url_name='webpush-update')
    def update_web_push_subscription(self, request, *args, **kwargs):
        serializer = serializers.WebPushUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth = serializer.validated_data['auth']
        subscription = serializer.validated_data['subscription']
        now = timezone.now()
        models.WebPushSubscriptionModel.objects.filter(
            auth=auth,
            profile=request.user.profile,
        ).update(
            endpoint=subscription['endpoint'],
            auth=subscription['auth'],
            p256dh=subscription['p256dh'],
            platform=subscription.get('platform', '').strip(),
            browser=subscription.get('browser', '').strip(),
            metadata=subscription.get('metadata', {}),
            last_seen_at=now,
            last_error='',
            is_active=True,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:2000],
        )
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='webpush/unregister', url_name='webpush-unregister')
    def unregister_web_push_subscription(self, request, *args, **kwargs):
        serializer = serializers.WebPushUnregisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth = serializer.validated_data['auth']
        models.WebPushSubscriptionModel.objects.filter(
            auth=auth,
            profile=request.user.profile,
            is_active=True,
        ).update(
            is_active=False,
            last_seen_at=timezone.now(),
        )
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='webpush/status', url_name='webpush-status')
    def web_push_subscription_status(self, request, *args, **kwargs):
        serializer = serializers.WebPushStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.validated_data['subscription']
        profile = request.user.profile
        is_subscribed = models.WebPushSubscriptionModel.objects.filter(
            profile=profile,
            endpoint=subscription['endpoint'],
            auth=subscription['auth'],
            is_active=True,
        ).exists()
        return Response({'is_subscribed': is_subscribed}, status=status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, url_path='reset_event_types', url_name='reset_event_types',
            permission_classes=(IsAdminUser,))
    def reset_event_types(self, request, *args, **kwargs):
        from . import event_types
        created_count = 0
        updated_count = 0
        for each in event_types.BaseEventType.__subclasses__():
            is_mention = getattr(each, 'is_mention', False)
            obj, created = models.EventTypeModel.objects.update_or_create(
                code=each.code,
                defaults={
                    'color': each.color,
                    'icon': each.icon,
                    'template_html': each.template_html,
                    'template_text': each.template_text,
                    'template_html_ru': each.template_html,
                    'template_text_ru': each.template_text,
                    'template_html_kk': each.template_html_kk,
                    'template_text_kk': each.template_text_kk,
                    'name_ru': each.verbose_name,
                    'name_kk': each.verbose_name_kk,
                    'url': each.url,
                    'is_mention': is_mention
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        return Response(data={"created": created_count, "updated": updated_count}, status=status.HTTP_200_OK)

    @action(methods=['post', ],
            detail=False,
            permission_classes=[],
            url_path='bkz_sign_request',
            url_name='bkz_sign_request')
    def bkz_sign_request(self, request, *args, **kwargs):

        data = request.data
        secret = data.pop('secret', '')

        if hashlib.md5((json.dumps(data) + DID_SALT).encode('utf-8')).hexdigest() == secret:

            notify_about_new_sign_request(data)
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'failed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=('post',), detail=False, url_path='socketio')
    def send_socketio(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        from common.redis import socketio_redis
        from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL

        data = json.dumps(request.data, cls=DjangoJSONEncoder)
        socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)
        return Response('ok')


def get_test_ws_view(request):
    template = get_template('test_ws.html')
    from . import event_types
    return HttpResponse(template.render(context={}))


class NotificationSettingsViewSet(BaseModelViewSet):
    """
    ViewSet для управления настройками уведомлений пользователя.
    """
    permission_classes = (IsAuthenticated,)
    queryset = models.NotificationCategoryModel.objects.none()  # Пустой queryset для роутера

    def get_queryset(self):
        """Переопределяем, чтобы не требовалась модель"""
        return models.NotificationCategoryModel.objects.none()

    def filter_queryset(self, queryset):
        """Переопределяем, чтобы не требовалась модель"""
        return queryset

    def get_serializer_class(self, *args, **kwargs):
        """Переопределяем, чтобы не требовалась модель"""
        # Возвращаем базовый сериализатор для браузерного API
        return drf_serializers.Serializer

    def list(self, request, *args, **kwargs):
        """
        Возвращает дерево настроек: категории и события с их статусами.
        """
        from .serializers import (
            NotificationSettingsCategorySerializer,
        )

        profile = request.user.profile

        # Получаем список доступных секций для пользователя
        from common.utils import get_tariff_section_codes
        available_section_codes = set(get_tariff_section_codes(profile))
        # Категория 'system' доступна всем
        available_section_codes.add('system')

        # Получаем только доступные категории, отсортированные по sort
        categories = models.NotificationCategoryModel.objects.filter(
            is_active=True,
            code__in=available_section_codes
        ).order_by('sort', 'name').only('code', 'name')

        # Получаем все event types с категориями, видимые в настройках и доступные пользователю
        event_types = models.EventTypeModel.objects.filter(
            is_active=True,
            show_in_settings=True,
            category__isnull=False,
            category_id__in=available_section_codes
        ).exclude(code='test_signal').order_by('category__sort', 'name').values(
            'code', 'name', 'default_enabled', 'category_id'
        )
        user_category_preferences = dict(
            models.NotificationCategoryPreferenceModel.objects.filter(
                user=profile
            ).values_list('category_id', 'is_enabled')
        )

        # Получаем пользовательские настройки одним запросом
        user_preferences = dict(
            models.NotificationEventTypePreferenceModel.objects.filter(
                user=profile
            ).values_list('event_type_id', 'is_enabled')
        )

        # Группируем события по категориям через словарь
        events_by_category = {}
        for event_type in event_types:
            category_code = event_type['category_id']
            if category_code not in events_by_category:
                events_by_category[category_code] = []

            # Определяем enabled
            if event_type['code'] in user_preferences:
                enabled = user_preferences[event_type['code']]
            else:
                enabled = event_type['default_enabled']

            events_by_category[category_code].append({
                'code': event_type['code'],
                'name': event_type['name'],
                'enabled': enabled,
            })

        # Формируем финальный список категорий
        categories_data = []
        for category in categories:
            category_code = category.code
            categories_data.append({
                'code': category_code,
                'name': category.name,
                'enabled': user_category_preferences.get(category_code, True),
                'events': events_by_category.get(category_code, []),
            })

        serializer = NotificationSettingsCategorySerializer(categories_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=False, url_path='update_event', url_name='update_event')
    def update_event_preference(self, request):
        """
        Обновляет настройку для конкретного типа события.
        Body: {"event_type_code": "task_assign_operator_notify", "is_enabled": true}
        """
        from .serializers import EventTypePreferenceUpdateSerializer

        serializer = EventTypePreferenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_type_code = serializer.validated_data['event_type_code']
        is_enabled = serializer.validated_data['is_enabled']
        profile = request.user.profile

        # Проверяем, что event_type существует и видим в настройках
        try:
            event_type = models.EventTypeModel.objects.get(
                code=event_type_code,
                is_active=True,
                show_in_settings=True
            )
        except models.EventTypeModel.DoesNotExist:
            raise ValidationError({'event_type_code': 'Тип события не найден или недоступен для настройки'})

        # Создаём или обновляем настройку
        preference, created = models.NotificationEventTypePreferenceModel.objects.update_or_create(
            user=profile,
            event_type=event_type,
            defaults={'is_enabled': is_enabled}
        )

        return Response({
            'event_type_code': event_type_code,
            'is_enabled': preference.is_enabled,
            'created': created
        }, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=False, url_path='update_category', url_name='update_category')
    def update_category_preference(self, request):
        from .serializers import CategoryPreferenceUpdateSerializer

        serializer = CategoryPreferenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = serializer.validated_data['category']
        is_enabled = serializer.validated_data['is_enabled']
        profile = request.user.profile

        try:
            category_obj = models.NotificationCategoryModel.objects.get(
                code=category,
                is_active=True,
            )
        except models.NotificationCategoryModel.DoesNotExist:
            raise ValidationError({'category': 'Категория не найдена или неактивна'})

        preference, created = models.NotificationCategoryPreferenceModel.objects.update_or_create(
            user=profile,
            category=category_obj,
            defaults={'is_enabled': is_enabled},
        )

        return Response({
            'category': category,
            'is_enabled': preference.is_enabled,
            'created': created,
        }, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=False, url_path='update_category_order', url_name='update_category_order')
    def update_category_order(self, request):
        from .serializers import CategoryOrderUpdateSerializer

        serializer = CategoryOrderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category_codes = serializer.validated_data['categories']
        profile = request.user.profile

        existing_categories = models.NotificationCategoryModel.objects.filter(
            is_active=True,
            code__in=category_codes,
        ).values_list('code', flat=True)
        existing_category_codes = set(existing_categories)
        missing_category_codes = [
            category_code for category_code in category_codes
            if category_code not in existing_category_codes
        ]
        if missing_category_codes:
            raise ValidationError({
                'categories': (
                    'Не найдены или неактивны категории: '
                    + ', '.join(sorted(missing_category_codes))
                )
            })

        with transaction.atomic():
            models.NotificationCategoryPreferenceModel.objects.filter(
                user=profile,
            ).exclude(
                category_id__in=category_codes
            ).update(
                sort_order=None,
            )

            for sort_index, category_code in enumerate(category_codes, start=1):
                models.NotificationCategoryPreferenceModel.objects.update_or_create(
                    user=profile,
                    category_id=category_code,
                    defaults={'sort_order': sort_index},
                )

        return Response(status=status.HTTP_200_OK)


class NotificationCategoryListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.NotificationCategorySerializer
    queryset = models.NotificationCategoryModel.objects.filter(is_active=True)

    def get_queryset(self):
        profile = self.request.user.profile

        category_codes = models.WebNotificationRecipientModel.objects.filter(
            recipient=profile,
            notification__is_active=True,
            notification__event_type__category__isnull=False,
        ).values_list(
            'notification__event_type__category',
            flat=True
        ).distinct()
        disabled_category_codes = models.NotificationCategoryPreferenceModel.objects.filter(
            user=profile,
            is_enabled=False,
        ).values_list('category_id', flat=True)

        user_sort_subquery = models.NotificationCategoryPreferenceModel.objects.filter(
            user=profile,
            category_id=OuterRef('code'),
        ).values('sort_order')[:1]

        return self.queryset.filter(
            code__in=category_codes
        ).exclude(
            code__in=disabled_category_codes
        ).annotate(
            user_sort_order=Subquery(user_sort_subquery),
            effective_sort_order=Coalesce(
                'user_sort_order',
                Value(2147483647),
                output_field=IntegerField(),
            ),
        ).order_by('effective_sort_order', 'sort', 'name')
