import uuid
import json
from datetime import datetime, timedelta
from math import ceil

from drf_haystack.viewsets import HaystackViewSet
from haystack.query import SearchQuerySet

from django.utils import timezone
from django.http import Http404
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models import Q, F, Value, Count, Case, When, BooleanField, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.translation import gettext as _

from rest_framework import generics, status, exceptions as drf_exceptions, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView

from bkz3.settings import SOCKETIO_SYSTEM_CHANNEL, FRONTEND_URL, BACKEND_URL

from common.serializers import AppUserSerializer
from common.paginators import CustomPagination
from common.utils import get_filter_queryset, UUIDEncoder, filter_by_search
from common.redis import socketio_redis
from common.views import BaseModelViewSet

from contractor_permissions.utils import contractors_where_user_has_permission, get_available_section_codes

from help_desk.models import ContactPersonModel, CustomerCardModel

from users.models import ProfileModel, CustomUser as User
from users.utils import filter_users_by_organizations, get_ancestor_departments_related_organizations

from bpms.tasks.models import TaskModel
from bpms.favorites.models import FavoriteModel
from bpms.meetings.models import PlannedMeetingModel, MeetingMemberModel
from bpms.meetings.utils import get_invite_link, get_connect_meeting_url
from bpms.meetings.apiviews import MeetingConnectMixin

from app_info.models import AppInfo

from . import models
from . import serializers
from . import permissions
from . import paginators
from . import utils
from . import utils_ai
from . import notifications
from bpms.chat_ai.utils.messages import invoke_role_prompt
from django_q.tasks import async_task


def _get_message_page_size(request, default=20, max_page_size=100):
    raw_page_size = request.query_params.get('page_size', default)

    try:
        page_size = int(raw_page_size)
    except (TypeError, ValueError):
        page_size = default

    return max(1, min(page_size, max_page_size))


def _get_chat_member(request, chat_uid):
    user = request.user.profile
    return models.MemberModel.objects.select_related('chat').get(
        is_active=True,
        chat__is_active=True,
        chat_id=chat_uid,
        user=user,
    )


def _get_message_list_queryset(chat_uid, *, include_deleted=False):
    queryset = models.MessageModel.objects.prefetch_related(
        'attachments',
        'mentions',
    ).select_related(
        'message_author__user',
        'message_reply__message_author__user',
    ).filter(
        is_active=True,
        chat_id=chat_uid,
    )

    if not include_deleted:
        queryset = queryset.filter(is_deleted=False)

    return queryset


def _get_cached_message_pagination_data(chat_uid):
    cached_messages = utils.get_cached_messages_list({'chat_uid': chat_uid}) or []
    if not cached_messages:
        return None

    return {
        'data': cached_messages,
        'data_count': len(cached_messages),
        'last_created': cached_messages[-1].get('created'),
    }


def _datetime_to_redis_iso(value):
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _serialize_datetime(value):
    if value is None:
        return None
    return drf_serializers.DateTimeField().to_representation(value)


def _normalize_uuid(value):
    if value is None:
        return None
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _get_cached_messages_after(chat_uid, after_created_dt):
    after_created_str = _datetime_to_redis_iso(after_created_dt)
    cached_messages = utils.get_cached_messages_list({'chat_uid': chat_uid}) or []
    if not cached_messages:
        return []

    results = []
    for each_message in reversed(cached_messages):
        created = each_message.get('created')
        if not created:
            continue
        if created > after_created_str:
            results.append(each_message)

    return results


def _get_cached_unread_messages(chat_uid, last_message_created, page_size):
    last_message_created_str = _datetime_to_redis_iso(last_message_created) if last_message_created else None
    cached_messages = utils.get_cached_messages_list({'chat_uid': chat_uid}) or []
    if not cached_messages:
        return []

    results = []
    for each_message in reversed(cached_messages):
        created = each_message.get('created')
        if not created:
            continue
        if not last_message_created_str or created > last_message_created_str:
            results.append(each_message)
        if len(results) >= page_size:
            break

    return results


def _build_message_list_page_link(chat_uid, page_size, page_number):
    return f'/chat/message/list/?chat={chat_uid}&page_size={page_size}&page={page_number}'


def _build_unread_context_pagination_response(request, queryset, chat_uid, first_unread_message, page_size):
    pagination = paginators.MessagePagination()
    pagination.cached_data = _get_cached_message_pagination_data(chat_uid)

    paginator = paginators.MessagePaginator(queryset, page_size)
    paginator.cached_data = pagination.cached_data

    qs = Q(created__gte=first_unread_message.created)
    if pagination.cached_data:
        qs = qs & Q(created__lt=pagination.cached_data['last_created'])

    aggr = models.MessageModel.objects.filter(
        chat_id=chat_uid,
        is_active=True,
        is_deleted=False,
    ).aggregate(number=Count('pk', filter=qs))

    page_number = max(1, ceil((aggr.get('number') or 1) / int(page_size)))

    try:
        pagination.page = paginator.page(page_number)
    except Exception as exc:
        raise drf_exceptions.NotFound(str(exc))

    pagination.request = request
    pagination.display_page_controls = False

    serializer = serializers.MessageListSerializer(
        list(pagination.page),
        many=True,
        context={'request': request}
    )

    paginated_response = pagination.get_paginated_response(serializer.data)
    response_data = dict(paginated_response.data)
    current_page_number = pagination.page.number

    response_data['next'] = (
        _build_message_list_page_link(chat_uid, page_size, current_page_number + 1)
        if pagination.page.has_next() else None
    )
    response_data['previous'] = (
        _build_message_list_page_link(chat_uid, page_size, current_page_number - 1)
        if pagination.page.has_previous() else None
    )

    return response_data


def _get_first_cached_unread_message_uid(chat_uid, last_message_created):
    if not last_message_created:
        return None

    cached_messages = utils.get_cached_messages_list({'chat_uid': chat_uid}) or []
    if not cached_messages:
        return None

    last_message_created_str = last_message_created.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    for each_message in reversed(cached_messages):
        if each_message.get('created', '') > last_message_created_str:
            return each_message.get('message_uid')

    return None


def _parse_history_cursor(value, field_name):
    parsed = parse_datetime(value or '')
    if parsed is None:
        raise drf_exceptions.ValidationError({field_name: 'Invalid datetime value.'})
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed.astimezone(timezone.utc)


def _decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def _get_effective_last_read_created(user_id, chat_uid, db_value=None):
    effective_value = db_value
    cached_value = socketio_redis.hget(f"member_last_message_date_{user_id}", str(chat_uid))
    cached_value = _decode_redis_value(cached_value)
    if cached_value:
        cached_dt = _parse_history_cursor(cached_value, 'created')
        if not effective_value or cached_dt > effective_value:
            effective_value = cached_dt
    return effective_value


def _get_chat_latest_created(chat_uid):
    last_db_created = _get_message_list_queryset(chat_uid).order_by('-created').values_list('created', flat=True).first()
    cached_data = _get_cached_message_pagination_data(chat_uid)
    cached_created = None
    if cached_data and cached_data.get('last_created'):
        cached_created = _parse_history_cursor(cached_data['last_created'], 'created')

    if last_db_created and cached_created:
        return max(last_db_created, cached_created)
    return last_db_created or cached_created


class ChatCreateView(generics.CreateAPIView):
    serializer_class = serializers.ChatCreateSerializer
    permission_classes = (IsAuthenticated,)
    queryset = models.ChatModel.objects.prefetch_related(
        'members__user',
    ).filter(is_active=True)


class ChatListView(generics.ListAPIView):
    serializer_class = serializers.ChatListSerializer
    permission_classes = (IsAuthenticated,)
    queryset = models.ChatModel.objects.prefetch_related(
        'members',
    ).filter(is_active=True)
    pagination_class = paginators.ChatPagination

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user.profile
        queryset = queryset.filter(
            member__user=user,
            member__is_active=True
        ).annotate(
            new_message_count=Count(
                'messages',
                filter=Q(
                    messages__created__gt=F('member__last_message_created'),
                    messages__is_active=True,
                    messages__is_deleted=False,
                )
            ),
            new_mention_count=Count(
                'messages',
                filter=Q(
                    messages__created__gt=F('member__last_message_created'),
                    messages__is_active=True,
                    messages__is_deleted=False,
                    messages__mentions=user,
                )
            ),
            is_pinned=Case(
                When(member__user=user, member__is_pinned=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            last_message_created=F('member__last_message_created'),
            last_message_id=Subquery(
                models.MessageModel.objects.filter(
                    chat_id=OuterRef('chat_uid'),
                    is_deleted=False,
                    is_active=True,
                ).order_by('-created').values('pk')[:1]
            ),
        )
        queryset = FavoriteModel.annotate_favorites(queryset)
        # Фильтрация закрепленных чатов
        is_pinned = self.request.query_params.get('is_pinned')
        if is_pinned is not None:
            is_pinned = is_pinned.lower() == 'true'
            queryset = queryset.filter(is_pinned=is_pinned)
        # Фильтрация чатов техподдержки
        is_support = self.request.query_params.get('is_support')
        if is_support is not None:
            is_support = is_support.lower() == 'true'
            queryset = queryset.filter(is_support=is_support)
        queryset = get_filter_queryset(self.request, models.ChatModel, queryset, )
        return queryset.order_by('-is_pinned', '-last_sent')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if request.query_params.get('display', '') == 'short':
            serializer_class = serializers.ChatListShortSerializer
        else:
            serializer_class = self.serializer_class
        page = self.paginate_queryset(queryset)
        chats_for_response = page if page is not None else queryset
        last_message_ids = list({
            each_chat.last_message_id
            for each_chat in chats_for_response
            if getattr(each_chat, 'last_message_id', None)
        })
        last_messages_by_chat_uid = {}
        if last_message_ids:
            last_messages = models.MessageModel.objects.filter(pk__in=last_message_ids).select_related(
                'message_reply',
                'message_forwarded',
                'message_forwarded__chat',
                'message_forwarded__message_reply',
                'message_forwarded__message_reply__message_author',
                'message_forwarded__message_reply__message_author__user',
                'message_forwarded__message_reply__message_author__avatar',
            ).prefetch_related(
                'attachments',
                'mentions',
                'message_forwarded__attachments',
            )
            for each_message in last_messages:
                last_messages_by_chat_uid[each_message.chat_id] = each_message
        context = {
            'request': request,
            'view': self,
            'last_messages_by_chat_uid': last_messages_by_chat_uid,
        }
        if page is not None:
            serializer = serializer_class(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True, context=context)
        return Response(serializer.data)


class MessageCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user.profile
        chat_uid = request.query_params.get('chat')
        queryset = models.ChatModel.objects.prefetch_related(
            'members__user',
        ).filter(is_active=True)
        queryset = queryset.filter(
            member__user=user,
            member__is_active=True
        ).annotate(
            new_message_count=Count(
                'messages',
                filter=Q(
                    messages__created__gt=F('member__last_message_created'),
                    messages__is_active=True,
                    messages__is_deleted=False,
                )
            ),
            new_mention_count=Count(
                'messages',
                filter=Q(
                    messages__created__gt=F('member__last_message_created'),
                    messages__is_active=True,
                    messages__is_deleted=False,
                    messages__mentions=user,
                )
            ),
            last_message_created=F('member__last_message_created')
        ).values('pk', 'chat_uid', 'new_message_count', 'new_mention_count', 'last_message_created')
        if chat_uid:
            queryset = queryset.filter(chat_uid=chat_uid)

        message_count = 0
        mention_count = 0
        for chat in queryset.iterator(chunk_size=100):
            each_message_count, each_mention_count = utils.get_last_message_count(chat, user)
            message_count += each_message_count
            mention_count += each_mention_count
        return Response({'count': message_count, 'mention_count': mention_count}, status=status.HTTP_200_OK)


class LastMessageView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        chat_uid = kwargs.get('chat_uid')
        if not chat_uid:
            raise drf_exceptions.NotFound()
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid)
        except (ObjectDoesNotExist, ValidationError):
            raise drf_exceptions.NotFound()
        if not chat.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        data = utils.get_last_message_data(chat)
        if not data:
            last_message = chat.messages.filter(is_deleted=False, is_active=True).order_by('-created').first()
            data = serializers.MessageListSerializer(last_message).data
        return Response(data)


class MessageViewersListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        message_uid = kwargs.get('message_uid')
        if not message_uid:
            raise drf_exceptions.NotFound()
        qs = models.MemberModel.objects.filter(is_active=True)
        try:
            message = models.MessageModel.objects.get(message_uid=message_uid)
        except (ObjectDoesNotExist, ValidationError):
            qs = qs.none()
        else:
            if not qs.filter(chat=message.chat, user=request.user.profile).exists():
                qs = qs.none()
            else:
                message_created = message.created
                qs = qs.filter(
                    chat=message.chat,
                    last_message_created__gte=message_created,
                ).order_by(
                    'user__user__last_name',
                    'user__user__first_name',
                    'user__user__middle_name',
                ).values_list('user', flat=True)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, view=self)

        data = CachedAppUserSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class ChatQuitView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user.profile
        chat_id = request.data.get('chat')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_id, is_active=True, member__user=user)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if chat.is_public is True and chat.author_id == user.pk:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            member = chat.members.get(user=user, is_active=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        member.is_active = False
        member.save(update_fields=('is_active',))
        # # Отправка сообщения по веб-сокету:
        # user_names = list(member.chat.members.filter(
        #     is_active=True
        # ).values_list('user__username', flat=True))
        data = serializers.MemberSerializer(member).data
        # socket_data = [get_socket_data(data, member, EventType.delete)]
        # if chat.is_public is True:
        #     text = user.profile.full_name + " покинул(а) чат."
        #     message = create_system_message(chat, member, text)
        #     message_dict = serializers.MessageListSerializer(message).data
        #     socket_data.append(get_socket_data(message_dict, message, EventType.create))
        # send_socket_message(socket_data, user_names)
        # # Отправка сообщения по socketio:
        # users = list(member.chat.members.filter(is_active=True).values_list('user', flat=True))
        # tasks.send_socketio_message.delay(data, get_obj_type(member), EventType.delete.value, users)
        # if chat.is_public is True:
        #     tasks.send_socketio_message.delay(message_dict, get_obj_type(message), EventType.create.value, users)
        return Response(data, status=status.HTTP_200_OK)


class ChatDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chat_id = request.data.get('chat')
        user = request.user.profile
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_id, is_active=True, is_public=True,
                                                chat_author_id=user.pk)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        chat.is_active = False
        chat.save(update_fields=('is_active',))
        # # Отправка сообщения по веб-сокету:
        # user_names = list(chat.members.filter(
        #     is_active=True
        # ).exclude(
        #     user_id=user.pk
        # ).values_list('user__username', flat=True))
        # data = serializers.ChatListSerializer(chat, context={'request': request}).data
        # socket_data = get_socket_data(data, chat, EventType.delete)
        # send_socket_message(socket_data, user_names)
        # # Отправка сообщения по socketio:
        # users = list(chat.members.filter(is_active=True).exclude(user_id=user.pk).values_list('user', flat=True))
        # tasks.send_socketio_message.delay(data, get_obj_type(chat), EventType.delete.value, users)
        # return Response(status=status.HTTP_200_OK)


class ChatRenameView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ChatRenameSerializer
    is_sent = True

    def get_object(self):
        user = self.request.user.profile
        chat_id = self.request.data.get('chat')
        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_id, is_active=True, is_public=True, chat_autor_id=user.pk)
        except ObjectDoesNotExist:
            raise Http404
        return chat


class ChatDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, permissions.ChatDetailPermission)
    queryset = models.ChatModel.objects.prefetch_related(
        'members__user',
    ).select_related(
        'chat_author',
    ).filter(is_active=True)
    serializer_class = serializers.ChatDetailSerializer
    lookup_field = 'chat_uid'

    def get_queryset(self):
        chat_id = self.kwargs['chat_uid']
        user = self.request.user.profile
        queryset = self.queryset
        queryset = queryset.filter(
            member__user=user,
            member__is_active=True,
            chat_uid=chat_id,
        ).annotate(
            new_message_count=Count(
                'messages',
                filter=Q(
                    messages__created__gt=F('member__last_message_created'),
                    messages__is_active=True,
                    messages__is_deleted=False,
                )
            ),
            new_mention_count=Count(
                'messages',
                filter=Q(
                    messages__created__gt=F('member__last_message_created'),
                    messages__is_active=True,
                    messages__is_deleted=False,
                    messages__mentions=user,
                )
            ),
            is_pinned=Case(
                When(member__user=user, member__is_pinned=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            last_message_created=F('member__last_message_created')
        )
        return queryset


class ChatVKSView(generics.RetrieveAPIView, MeetingConnectMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ChatListSerializer
    queryset = models.ChatModel.objects.prefetch_related(
        'members__user',
    ).select_related(
        'chat_author',
    ).filter(is_active=True)
    lookup_field = 'chat_uid'

    def get_queryset(self):
        chat_id = self.kwargs['chat_uid']
        user = self.request.user.profile
        queryset = self.queryset
        queryset = queryset.filter(
            is_active=True,
            member__user=user,
            member__is_active=True,
            chat_uid=chat_id
        )

        return queryset

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        user = request.user.profile

        chat = models.ChatModel.objects.get(chat_uid=self.kwargs['chat_uid'])
        meeting = chat.meeting if (chat.meeting and chat.meeting.is_active) else None
        meeting_name = str(chat)

        if meeting is None:
            meeting = PlannedMeetingModel.objects.create(
                name=meeting_name,
                date_begin=timezone.now(),
                duration=500,
                related_object=chat
            )
            chat.meeting = meeting
            chat.save()
        else:
            if meeting.name != meeting_name:
                meeting.name = meeting_name
                meeting.save()

        chat_members = chat.members.filter(is_active=True)
        for member in chat_members:
            rec, is_new = MeetingMemberModel.objects.get_or_create(
                meeting=meeting,
                user=member.user,
                defaults={'is_moderator': True}
            )
            if not is_new and not rec.is_moderator:
                rec.is_moderator = True
                rec.save()

        if meeting.status != 'online':
            self.start_meeting(meeting, user)

        additional_data = {
            "url2": get_invite_link(meeting.invite_link),
            "url": get_connect_meeting_url(meeting.id),
            "status": "online"
        }
        response.data.update(additional_data)
        return response

from bkz3.settings import send_mikrot
class ConnectVNCView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            chat = models.ChatModel.objects.get(chat_uid=self.kwargs.get('chat_uid'))
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.NotFound('chat not found')

        if not chat.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR')
        send_mikrot(client_ip)
        return Response('ok')

    def post(self, request, *args, **kwargs):
        try:
            chat = models.ChatModel.objects.get(chat_uid=self.kwargs.get('chat_uid'))
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.NotFound('chat not found')
        if not chat.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()
        #     message = models.MessageModel()
        #     message.chat = chat
        #     message.is_system = True
        #     message.created = timezone.now()
        #     message.text = _('Начался сеанс удаленного подключения')
        #     message.save()
        #     message_data = serializers.MessageListSerializer(message).data
        #     message_data['chat_uid'] = str(message.chat.chat_uid)
        #     message_data['chat_name'] = message.chat.name
        #     message_data['is_public'] = message.chat.is_public
        #     message_data['is_new'] = True
        #     data = json.dumps(
        #         {
        #             "event": "chat_message",
        #             "data": message_data,
        #         },
        #         cls=UUIDEncoder
        #     )
        #     socketio_redis.publish(SOCKETIO_SYSTEM_CHANNEL, data)

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR')
        send_mikrot(client_ip)
        return Response('ok')


class ChatPrivateView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.user.profile.pk
        recipient_id = request.query_params.get('user')
        try:
            recipient = ProfileModel.objects.get(pk=recipient_id)
        except ProfileModel.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        chat = models.ChatModel.objects.filter(
            is_public=False,
            is_active=True,
            member__user_id=user_id,
        ).filter(member__user_id=recipient_id,).order_by('-created_at').first()
        if not chat:
            s_data = serializers.AppUserSerializer(instance=recipient, context={'request': request}).data
            s_data['type'] = recipient.get_label()
            return Response(s_data, status=status.HTTP_200_OK)
        s_data = serializers.ChatListSerializer(instance=chat, context={'request': request}).data
        s_data['type'] = chat.get_label()
        return Response(s_data, status=status.HTTP_200_OK)


class MessageCreateView(generics.CreateAPIView):
    serializer_class = serializers.MessageCreateSerializer
    permission_classes = (IsAuthenticated,)
    queryset = models.MessageModel.objects.filter(is_active=True)


class MessageDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user.profile
        message_id = request.data.get('message')
        try:
            message = models.MessageModel.objects.select_related('chat', 'message_author').get(
                is_active=True,
                message_uid=message_id,
                chat__is_active=True,
                is_system=False,
                is_deleted=False
            )
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        is_moderator = message.chat.members.filter(user_id=user.pk, is_active=True, is_moderator=True).exists()
        is_chat_author = message.chat.author_id == user.pk
        is_message_author = message.author_id == user.pk
        is_message_author_moderator = message.chat.members.filter(user_id=message.author_id, is_active=True,
                                                                  is_moderator=True)
        is_message_author_chat_author = message.chat.author_id == message.author_id
        now = timezone.now()
        if message.chat.is_public and (is_chat_author or (
                is_moderator and not (is_message_author_moderator or is_message_author_chat_author))) or (
                is_message_author and (message.created + timedelta(minutes=1)) > now):
            message.text = 'Сообщение удалено. Удалил(а): ' + user.profile.full_name
            message.is_deleted = True
            message.deleted = now
            message.message_reply = None
            message.save(update_fields=('text', 'is_deleted', 'deleted', 'message_reply'))
            serialized_data = serializers.MessageListSerializer(message, context={'request': request}).data
            serialized_data['is_new'] = False
            # # Отправка сообщения по веб-сокету:
            # user_names = list(message.chat.members.filter(
            #     is_active=True
            # ).exclude(
            #     user_id=user.pk
            # ).values_list('user__username', flat=True))
            # socket_data = get_socket_data(serialized_data, message, EventType.update)
            # send_socket_message(socket_data, user_names)
            # # Отправка сообщения по socketio:
            # users = list(message.chat.members.filter(
            #     is_active=True).exclude(user_id=user.pk).values_list('user', flat=True))
            # tasks.send_socketio_message.delay(socket_data, get_obj_type(message), EventType.update.value, users)
            return Response(serialized_data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class MessageListView(generics.ListAPIView):
    serializer_class = serializers.MessageListSerializer
    permission_classes = (IsAuthenticated,)
    queryset = models.MessageModel.objects.prefetch_related(
        'attachments',
        'mentions',
    ).select_related(
        'message_author__user',
        'message_reply__message_author__user',
    ).filter(is_active=True)
    pagination_class = paginators.MessagePagination
    old_last_message = None

    def get_queryset(self):
        queryset = self.queryset.order_by('-created')
        user = self.request.user.profile
        chat_id = self.request.query_params.get('chat')
        slice_count = self.request.query_params.get('slice_count')
        is_deleted = self.request.query_params.get('is_deleted', 'false') == 'true'
        try:
            member = models.MemberModel.objects.get(is_active=True, chat__is_active=True, chat_id=chat_id, user=user)
        except ObjectDoesNotExist:
            return queryset.none()
        queryset = queryset.filter(chat_id=chat_id)
        if is_deleted is False:
            queryset = queryset.filter(is_deleted=False)
        # Кирилл просил инструмент, чтобы срезать последние slice_count сообщений
        if slice_count:
            excluded = queryset[:int(slice_count)]
            queryset = queryset.exclude(pk__in=excluded)

        queryset = queryset.annotate(is_new=Count("id", filter=Q(created__gt=member.last_message_created)))

        return queryset


class MessageUnreadEntryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        chat_uid = kwargs.get('chat_uid')
        page_size = _get_message_page_size(request)

        try:
            member = _get_chat_member(request, chat_uid)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()

        effective_last_read_created = _get_effective_last_read_created(
            request.user.profile.pk,
            chat_uid,
            member.last_message_created,
        )

        unread_count, unread_mention_count = utils.get_last_message_count(
            {
                'chat_uid': chat_uid,
                'last_message_created': effective_last_read_created,
            },
            request.user.profile
        )

        unread_queryset = _get_message_list_queryset(chat_uid)
        if effective_last_read_created:
            unread_queryset = unread_queryset.filter(created__gt=effective_last_read_created)

        first_unread_message = unread_queryset.order_by('created').first()

        first_unread_message_uid = None
        response_data = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

        if first_unread_message:
            response_data = _build_unread_context_pagination_response(
                request,
                _get_message_list_queryset(chat_uid).order_by('-created'),
                chat_uid,
                first_unread_message,
                page_size
            )
            first_unread_message_uid = str(first_unread_message.message_uid)
        elif unread_count > 0:
            first_unread_message_uid = _get_first_cached_unread_message_uid(chat_uid, effective_last_read_created)
            cached_unread_messages = _get_cached_unread_messages(chat_uid, effective_last_read_created, page_size)
            if cached_unread_messages:
                response_data = {
                    'count': len(cached_unread_messages),
                    'next': None,
                    'previous': None,
                    'results': cached_unread_messages,
                }

        response_data.update({
            'history_mode': bool(unread_count and first_unread_message_uid),
            'unread_count': unread_count,
            'unread_mention_count': unread_mention_count,
            'first_unread_message_uid': first_unread_message_uid,
            'last_read_created': _serialize_datetime(effective_last_read_created),
        })

        return Response(response_data, status=status.HTTP_200_OK)


class MessageHistoryAfterView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        chat_uid = kwargs.get('chat_uid')
        page_size = _get_message_page_size(request)
        after_created = request.query_params.get('after_created')

        if not after_created:
            raise drf_exceptions.ValidationError({'after_created': 'This field is required.'})

        try:
            _get_chat_member(request, chat_uid)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()

        after_created_dt = _parse_history_cursor(after_created, 'after_created')

        queryset = _get_message_list_queryset(chat_uid).filter(
            created__gt=after_created_dt
        ).order_by('created')

        results = list(queryset[:page_size])
        serialized_results = serializers.MessageListSerializer(
            results,
            many=True,
            context={'request': request}
        ).data

        if results:
            last_message = results[-1]
            has_more = queryset.filter(created__gt=last_message.created).exists()
            next_after_created = last_message.created
        else:
            has_more = False
            next_after_created = after_created_dt

        if not has_more:
            cached_results = _get_cached_messages_after(chat_uid, next_after_created)
            if cached_results:
                serialized_results = list(serialized_results) + cached_results

        return Response(
            {
                'results': serialized_results,
                'has_more': has_more,
                'reached_live': not has_more,
                'next_after_created': drf_serializers.DateTimeField().to_representation(next_after_created),
            },
            status=status.HTTP_200_OK
        )


class MessageReadProgressView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chat_uid = kwargs.get('chat_uid')
        try:
            member = _get_chat_member(request, chat_uid)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()

        raw_created = request.data.get('created')
        if not raw_created:
            raise drf_exceptions.ValidationError({'created': 'This field is required.'})

        requested_created = _parse_history_cursor(str(raw_created), 'created')
        current_created = _get_effective_last_read_created(
            request.user.profile.pk,
            chat_uid,
            member.last_message_created,
        )
        latest_chat_created = _get_chat_latest_created(chat_uid)

        applied_created = requested_created
        if latest_chat_created and applied_created > latest_chat_created:
            applied_created = latest_chat_created
        if current_created and applied_created < current_created:
            applied_created = current_created

        if not member.last_message_created or applied_created > member.last_message_created:
            member.last_message_created = applied_created
            member.save(update_fields=('last_message_created',))

        socketio_redis.hset(
            f"member_last_message_date_{request.user.profile.pk}",
            str(chat_uid),
            _datetime_to_redis_iso(applied_created),
        )

        unread_count, unread_mention_count = utils.get_last_message_count(
            {
                'chat_uid': chat_uid,
                'last_message_created': applied_created,
            },
            request.user.profile
        )

        utils.publish_chat_member_read_progress(
            chat_uid=chat_uid,
            user_id=request.user.profile.pk,
            created=applied_created,
            unread_count=unread_count,
            unread_mention_count=unread_mention_count,
        )

        return Response(
            {
                'chat': str(chat_uid),
                'created': _serialize_datetime(applied_created),
                'my_readed_at': _serialize_datetime(applied_created),
                'unread_count': unread_count,
                'unread_mention_count': unread_mention_count,
            },
            status=status.HTTP_200_OK
        )


class MessageActionInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        request_user = request.user.profile
        query_params = request.query_params
        chat_uid = query_params.get('chat', '')
        if not chat_uid:
            return Response(status=status.HTTP_404_NOT_FOUND)
        message_uid = query_params.get('message', '')
        if not message_uid:
            return Response(status=status.HTTP_404_NOT_FOUND)
        message = socketio_redis.hget(f'messages:{chat_uid}', message_uid)
        create_help_desk_ticket = False
        if message:
            message_dict = json.loads(message)
            is_system = message_dict.get('is_system', True)
            if is_system:
                return Response({}, status=status.HTTP_200_OK)
            user_id = message_dict.get('message_author', dict()).get('id')
            if user_id:
                try:
                    message_author = ProfileModel.objects.get(pk=user_id)
                except ProfileModel.DoesNotExist:
                    return Response('Message author not found.', status=status.HTTP_404_NOT_FOUND)
            else:
                return Response('Message author not found', status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                message = models.MessageModel.objects.get(message_uid=message_uid, is_active=True)
            except models.MessageModel.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            is_system = message.is_system
            message_author = message.message_author
            if is_system:
                return Response({}, status=status.HTTP_200_OK)
            chat = message.chat
            if chat.is_public:
                specialist_user = request.user.profile
                client_user = message_author
                help_desk_admin_contractors = contractors_where_user_has_permission(
                    specialist_user.pk,
                    ('help_desk_admin',),
                    None
                )
                help_desk_coordinator_contractors = get_ancestor_departments_related_organizations(
                    contractors_where_user_has_permission(
                        specialist_user.pk,
                        ('help_desk_client_admin',),
                        None
                    ),
                    include_self=True
                )
                help_desk_manager_contractors = set(
                    contractors_where_user_has_permission(specialist_user.pk, ('help_desk_manager',), None))
                specialist_customer_cards = CustomerCardModel.get_qs_customer_cards_from_specialist(
                    specialist_user.pk
                ).filter(
                    org_admin_id__in=help_desk_manager_contractors
                ).values_list('pk', flat=True)
                if help_desk_manager_contractors or specialist_customer_cards or help_desk_coordinator_contractors:
                    create_help_desk_ticket = ContactPersonModel.objects.filter(
                        Q(customer_card__org_admin_id__in=help_desk_admin_contractors, ) |
                        Q(customer_card__customer_id__in=help_desk_coordinator_contractors) |
                        Q(customer_card_id__in=specialist_customer_cards),
                        is_active=True,
                        customer_card__is_active=True,
                        user=client_user,
                    ).exists()
            else:
                specialist_user = request.user.profile
                client_user = chat.members.all().exclude(user=specialist_user).order_by('-created_at').first().user
                from help_desk.utils import get_actual_specialist_from_user
                actual_specialists = get_actual_specialist_from_user(client_user, specialist_user)
                if actual_specialists.exists():
                    create_help_desk_ticket = True

        try:
            action_info = AppInfo.objects.get(is_active=True, code='chat_message_action_info').metadata
        except AppInfo.DoesNotExist:
            action_info = {
                "add_task": {
                    "availability": True
                },
                # "add_order": {
                #     "availability": True
                # },
                "pin": {
                    "availability": True
                },
                "reply": {
                    "availability": True
                }
            }
        if not message_author.contractors.filter(is_active=True).exists():
            action_info.pop('add_order', None)
        if not create_help_desk_ticket:
            action_info.pop('create_help_desk_ticket', None)
        if message_author == request_user:
            action_info['delete'] = {'availability': True}
            action_info['edit'] = {'availability': True}
        profile = request.user.profile
        if 'tasks' not in get_available_section_codes(profile):
            action_info.pop('add_task', None)
        return Response({"actions": action_info})


class MessagePinView(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.MessageModel.objects.filter(is_active=True, chat__is_active=True, is_deleted=False)

    def post(self, request, *args, **kwargs):
        message = self.get_object(request, *args, **kwargs)
        chat = message.chat
        user = request.user
        if chat.is_public is True:
            moderators = models.MemberModel.objects.filter(chat=chat, is_moderator=True).values_list('user', flat=True)
            if (user.pk in moderators or user == chat.chat_author) and message.is_pinned is False:
                message.is_pinned = True
                message.pin_author = user
                message.pin_date = timezone.now()
                message.save()
                # self.send_message(request, user, chat, message)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            if user.pk in chat.members.all().values_list('user', flat=True) and message.is_pinned is False:
                message.is_pinned = True
                message.pin_author = user
                message.pin_date = timezone.now()
                message.save()
                # self.send_message(request, user, chat, message)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response('ok', status=status.HTTP_200_OK)

    # def send_message(self, request, user, chat, message):
    #     text = user.profile.full_name + " закрепил данное сообщение."
    #     member = models.Member.objects.get(chat=chat, user=user)
    #     system_message = create_system_message(chat, member, text, reply=message)
    #     system_message_dict = serializers.MessageListSerializer(system_message).data
    #     message_dict = serializers.MessageListSerializer(message, context={"request": request}).data
    #     socket_data = [
    #         get_socket_data(system_message_dict, system_message, EventType.create),
    #         get_socket_data(message_dict, message, EventType.pin)
    #     ]
    #     user_names = list(chat.members.filter(
    #         is_active=True
    #     ).values_list('user__username', flat=True))
    #     send_socket_message(socket_data, user_names)
    #     # Отправка сообщения по socketio:
    #     users = list(chat.members.filter(is_active=True).values_list('user', flat=True))
    #     tasks.send_socketio_message.delay(message_dict, get_obj_type(message), EventType.pin.value, users)
    #     tasks.send_socketio_message.delay(system_message_dict, get_obj_type(system_message), EventType.create.value, users)

    def get_object(self, request, *args, **kwargs):
        message_id = request.data.get('message')
        try:
            message = models.MessageModel.objects.get(is_active=True, chat__is_active=True, is_deleted=False,
                                                      pk=message_id)
        except ObjectDoesNotExist:
            raise Http404
        return message


class MessageUnpinView(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.MessageModel.objects.filter(is_active=True, chat__is_active=True, is_deleted=False)

    def post(self, request, *args, **kwargs):
        message = self.get_object(request, *args, **kwargs)
        chat = message.chat
        user = request.user
        if chat.is_public is True:
            moderators = models.MemberModel.objects.filter(chat=chat, is_moderator=True).values_list('user', flat=True)
            if (user.pk in moderators or user == chat.chat_author) and message.is_pinned is True:
                message.is_pinned = False
                message.pin_author = None
                message.pin_date = None
                message.save()
                # self.send_message(request, user, chat, message)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            if user.pk in chat.members.all().values_list('user', flat=True) and message.is_pinned is True:
                message.is_pinned = False
                message.pin_author = None
                message.pin_date = None
                message.save()
                # self.send_message(request, user, chat, message)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response('ok', status=status.HTTP_200_OK)

    # def send_message(self, request, user, chat, message):
    #     text = user.profile.full_name + " открепил данное сообщение."
    #     member = models.Member.objects.get(chat=chat, user=user)
    #     system_message = create_system_message(chat, member, text, reply=message)
    #     system_message_dict = serializers.MessageListSerializer(system_message).data
    #     message_dict = serializers.MessageListSerializer(message, context={"request": request}).data
    #     socket_data = [
    #         get_socket_data(system_message_dict, system_message, EventType.create),
    #         get_socket_data(message_dict, message, EventType.unpin)
    #     ]
    #     user_names = list(chat.members.filter(
    #         is_active=True
    #     ).values_list('user__username', flat=True))
    #     send_socket_message(socket_data, user_names)
    #     # Отправка сообщения по socketio:
    #     users = list(chat.members.filter(is_active=True).values_list('user', flat=True))
    #     tasks.send_socketio_message.delay(message_dict, get_obj_type(message), EventType.unpin.value, users)
    #     tasks.send_socketio_message.delay(system_message_dict, get_obj_type(system_message), EventType.create.value, users)

    def get_object(self, request, *args, **kwargs):
        message_id = request.data.get('message')
        try:
            message = models.MessageModel.objects.get(is_active=True, chat__is_active=True, is_deleted=False,
                                                      id=message_id)
        except ObjectDoesNotExist:
            raise Http404
        return message


class AllMessageUnpinView(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.MessageModel.objects.filter(is_active=True, chat__is_active=True, is_deleted=False)

    def post(self, request, *args, **kwargs):
        chat = self.get_object(request, *args, **kwargs)
        user = request.user
        has_pinned = models.MessageModel.objects.filter(
            chat=chat, is_active=True, chat__is_active=True, is_pinned=True).exists()
        if chat.is_public is True:
            moderators = models.MemberModel.objects.filter(chat=chat, is_moderator=True).values_list('user', flat=True)
            if (user.pk in moderators or user == chat.author) and has_pinned:
                models.MessageModel.objects.filter(chat=chat, is_pinned=True).update(
                    is_pinned=False, pin_author=None, pin_date=None)
                # self.send_message(request, user, chat)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            if user.pk in chat.members.all().values_list('user', flat=True) and has_pinned:
                models.MessageModel.objects.filter(chat=chat, is_pinned=True).update(
                    is_pinned=False, pin_author=None, pin_date=None)
                self.send_message(request, user, chat)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response('ok', status=status.HTTP_200_OK)

    # def send_message(self, request, user, chat):
    #     text = user.profile.full_name + " открепил все сообщения."
    #     member = models.Member.objects.get(chat=chat, user=user)
    #     system_message = create_system_message(chat, member, text)
    #     system_message_dict = serializers.MessageListSerializer(system_message).data
    #     chat_dict = serializers.ChatListSerializer(chat, context={"request": request}).data
    #     chat_dict['is_moderator'] = member.is_moderator
    #     socket_data = [
    #         get_socket_data(system_message_dict, system_message, EventType.create),
    #         get_socket_data(chat_dict, chat, EventType.unpin)
    #     ]
    #     user_names = list(chat.members.filter(
    #         is_active=True
    #     ).values_list('user__username', flat=True))
    #     send_socket_message(socket_data, user_names)
    #     # Отправка сообщения по socketio:
    #     users = list(chat.members.filter(is_active=True).values_list('user', flat=True))
    #     tasks.send_socketio_message.delay(chat_dict, get_obj_type(chat), EventType.unpin.value, users)
    #     tasks.send_socketio_message.delay(system_message_dict, get_obj_type(system_message), EventType.create.value, users)

    def get_object(self, request, *args, **kwargs):
        chat_id = request.data.get('chat')
        try:
            chat = models.ChatModel.objects.get(is_active=True, pk=chat_id)
        except ObjectDoesNotExist:
            raise Http404
        return chat


class PinnedMessageListView(generics.ListAPIView):
    serializer_class = serializers.MessageListSerializer
    permission_classes = (IsAuthenticated,)
    queryset = models.MessageModel.objects.prefetch_related(
        'attachments'
    ).select_related(
        'message_author__user',
        'message_reply__message_author__user',
    ).filter(is_active=True, is_pinned=True)
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user.profile
        chat_id = self.request.query_params.get('chat')
        try:
            member = models.MemberModel.objects.get(is_active=True, chat__is_active=True, chat_id=chat_id, user=user)
        except ObjectDoesNotExist:
            return queryset.none()
        queryset = queryset.filter(chat_id=chat_id)
        return queryset.order_by('-pin_date')


from users.serializers import CachedAppUserSerializer


class ChatUserListView(generics.ListAPIView):
    serializer_class = CachedAppUserSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ProfileModel.objects.select_related('user').filter(is_active=True,
                                                                  temporary_blocked=False)
    pagination_class = paginators.ChatUserPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer_class = CachedAppUserSerializer
            s_data = serializer_class(page, many=True, context={'request': request, 'view': self}).data
            display = request.query_params.get('display', '')
            if display == 'help_desk':
                from help_desk.utils import get_my_actual_specialists
                user = request.user.profile
                actual_specialists = {}
                for specialist_user_id, org_admin_name, is_reserve in set(get_my_actual_specialists(user)):
                    actual_specialists[specialist_user_id] = {
                        'org_admin_name': org_admin_name,
                        'is_reserve': is_reserve,
                    }
                for each in s_data:
                    try:
                        specialist_data = actual_specialists[uuid.UUID(each['id'])]
                    except KeyError:
                        pass
                    else:
                        each['org_admin_name'] = specialist_data['org_admin_name']
                        each['is_reserve'] = specialist_data['is_reserve']

            return self.get_paginated_response(s_data)
        return Response([])

    def get_queryset(self):
        user = self.request.user.profile
        display = self.request.query_params.get('display', '')
        if display == 'help_desk':
            from help_desk.utils import get_my_actual_specialists
            actual_specialists = set(get_my_actual_specialists(user))
            actual_specialist_users = [specialist_data[0] for specialist_data in actual_specialists]
            queryset = self.queryset.filter(pk__in=actual_specialist_users).values_list('pk')
        else:
            queryset = filter_users_by_organizations(
                self.queryset,
                user,
                add_support_users=True,
            ).values_list('pk')
        is_all = self.request.query_params.get('all', 'false')
        chat_id = self.request.query_params.get('chat')
        search = self.request.query_params.get('search', None)
        text = self.request.query_params.get('text')
        if text:
            search = text
        if is_all != 'true' and not chat_id:
            chats = models.ChatModel.objects.filter(
                member__is_active=True,
                member__user=user,
                is_public=False,
                is_active=True
            ).values_list('pk', flat=True)
            queryset = queryset.exclude(chat_member__chat__in=chats)
        if chat_id:
            chat_members = models.MemberModel.objects.filter(
                chat_id=chat_id, is_active=True).values_list('user', flat=True)
            queryset = queryset.exclude(pk__in=chat_members)
        if search:
            queryset = queryset.filter(Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) |
                                       Q(user__middle_name__icontains=search))
        queryset = get_filter_queryset(self.request, ProfileModel, queryset)
        return queryset.order_by(
            '-is_support',
            'user__last_name',
            'user__first_name',
            'user__middle_name').exclude(pk=user.pk)


class ChatMemberAddView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chat_id = request.data.get('chat')
        member_is_moderator = request.data.get('is_moderator', False)
        if not isinstance(member_is_moderator, bool):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            chat = models.ChatModel.objects.select_related('chat_author').get(pk=chat_id, is_public=True,
                                                                              is_active=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = request.user.profile
        try:
            user_member = chat.members.get(user=user, is_active=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        is_moderator = user_member.is_moderator
        is_author = chat.author == user
        if not (is_moderator or is_author):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if member_is_moderator and not is_author:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        member_user_id = request.data.get('user')
        try:
            member = models.MemberModel.objects.get_or_create(chat=chat, user_id=member_user_id)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if member[0].is_active is True and member[1] is False:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if member[0].is_active is False and member[1] is False:
            member[0].is_active = True
        member[0].is_moderator = member_is_moderator
        member[0].save(update_fields=('is_moderator', 'is_active'))
        text = member[0].user.full_name + " добавлен(а) в чат. Добавил(а): " + user.full_name
        # system_message = create_system_message(chat, user_member, text)
        # member[0].last_message = system_message.pk
        member[0].save(update_fields=('last_message',))
        # system_message_dict = serializers.MessageListSerializer(system_message).data
        serialized_data = serializers.MemberSerializer(member[0], context={'request': request}).data
        # chat_dict = serializers.ChatListSerializer(chat, context={'request': request}).data
        # chat_dict["is_moderator"] = member[0].is_moderator
        # socket_data = [
        #     get_socket_data(serialized_data, member[0], EventType.create),
        #     get_socket_data(chat_dict, chat, EventType.create),
        #     get_socket_data(system_message_dict, system_message, EventType.create)
        # ]
        # user_names = list(chat.members.filter(
        #     is_active=True
        # ).values_list('user__username', flat=True))
        # send_socket_message(socket_data, user_names)
        # # Отправка сообщения по socketio:
        # users = list(chat.members.filter(is_active=True).exclude(user_id=member_user_id).values_list('user', flat=True))
        # tasks.send_socketio_message.delay(serialized_data, get_obj_type(member[0]), EventType.create.value, users)
        # tasks.send_socketio_message.delay(system_message_dict, get_obj_type(system_message), EventType.create.value, users)
        # tasks.send_socketio_message.delay(chat_dict, get_obj_type(chat), EventType.create.value, [member_user_id])
        return Response(serialized_data, status=status.HTTP_200_OK)


class ChatMemberDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        chat_id = request.data.get('chat')
        user_id = request.data.get('user')
        try:
            chat = models.ChatModel.objects.select_related('chat_author').get(pk=chat_id, is_public=True,
                                                                              is_active=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            user_member = chat.members.get(user=user, is_active=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        is_author = chat.chat_author == user
        is_moderator = user_member.is_moderator
        if not (is_author or is_moderator):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            member = chat.members.get(user_id=user_id, is_active=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if chat.author == member.user:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if member.is_moderator and not is_author:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        member.is_active = False
        member.save(update_fields=('is_active',))
        is_messages_delete = request.data.get('is_messages_delete', False)
        if is_messages_delete is True:
            models.MessageModel.objects.filter(chat=chat, author=member.user, is_active=True).update(
                text='Сообщение удалено')
        serialized_data = serializers.MemberSerializer(member, context={'request': request}).data
        # text = member.user.profile.full_name + " исключен(а) из чата. Исключил(а): " + user.profile.full_name
        # system_message = create_system_message(chat, user_member, text)
        # system_message_dict = serializers.MessageListSerializer(system_message).data
        # socket_data = [
        #     get_socket_data(serialized_data, member, EventType.delete),
        #     get_socket_data(system_message_dict, system_message, EventType.create),
        # ]
        # user_names = list(chat.members.filter(
        #     is_active=True
        # ).values_list('user__username', flat=True))
        # user_names.append(member.user.username)
        # send_socket_message(socket_data, user_names)
        # # Отправка сообщения по socketio:
        # users = list(chat.members.filter(is_active=True).exclude(user_id=user_id).values_list('user', flat=True))
        # chat_dict = serializers.ChatListSerializer(chat, context={'request': request}).data
        # tasks.send_socketio_message.delay(chat_dict, get_obj_type(chat), EventType.delete.value, [user_id])
        # tasks.send_socketio_message.delay(serialized_data, get_obj_type(member), EventType.delete.value, users)
        # tasks.send_socketio_message.delay(system_message_dict, get_obj_type(system_message), EventType.create.value, users)
        return Response(serialized_data, status=status.HTTP_200_OK)


class ChatMemberListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = models.MemberModel.objects.select_related(
        'user',
        'chat'
    ).filter(
        chat__is_active=True
    )
    serializer_class = serializers.MemberSerializer
    pagination_class = paginators.MemberPagination

    def get_queryset(self):
        user = self.request.user.profile
        chat_id = self.request.query_params.get('chat')
        queryset = self.queryset
        if not chat_id:
            return queryset.none()
        if not models.MemberModel.objects.filter(
                is_active=True,
                chat=chat_id,
                chat__is_active=True,
                user_id=user.pk,
        ).exists():
            return queryset.none()
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(user__user__last_name__icontains=search)
                | Q(user__user__first_name__icontains=search)
                | Q(user__user__middle_name__icontains=search)
            )
        if self.request.query_params.get('deleted', 'false') == 'true':
            queryset = queryset.filter(chat=chat_id)
        else:
            queryset = queryset.filter(chat=chat_id, is_active=True)
        return queryset.order_by('user__user__last_name',
                                 'user__user__first_name',
                                 'user__user__middle_name')


class ChatTaskListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MemberSerializer

    def list(self, request, *args, **kwargs):
        chat_id = self.request.query_params.get('chat')
        task_type = self.request.query_params.get('task_type')
        try:
            member = _get_chat_member(request, chat_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound()
        counts = {
            'total': TaskModel.objects.filter(message_share__chat=chat_id,
                                              task_type=task_type,
                                              is_active=True).count(),
            'in_work': TaskModel.objects.filter(message_share__chat=chat_id,
                                                status__task_status_type__is_complete=False,
                                                task_type=task_type,
                                                is_active=True).count()
        }

        return Response(counts)


class SetLastMessageView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_id = request.user.pk
        chat_id = request.query_params.get('chat')
        if chat_id:
            models.MemberModel.objects.filter(
                is_active=True,
                chat_id=chat_id,
                chat__is_active=True,
                user_id=user_id,
            ).update(
                last_message=Value(
                    getattr(models.MessageModel.objects.filter(is_active=True).only('pk').last(), 'pk', 0)
                )
            )
        return Response('ok', status=status.HTTP_204_NO_CONTENT)


class ModeratorChangeStatusMixin:
    def change_status(self, request, is_moderator):
        user = request.user
        chat_id = request.data.get('chat')
        moderator_id = request.data.get('user')
        try:
            chat = models.ChatModel.objects.get(is_active=True, pk=chat_id, is_public=True)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if chat.chat_author_id != user.pk:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            member = chat.members.get(user_id=moderator_id, is_active=True, is_moderator=not is_moderator)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        member.is_moderator = is_moderator
        member.save(update_fields=('is_moderator',))
        serialized_data = serializers.MemberSerializer(member, context={'request': request}).data
        # chat_dict = serializers.ChatListSerializer(chat, context={'request': request}).data
        # chat_dict['is_moderator'] = member.is_moderator
        # socket_data = [get_socket_data(chat_dict, chat, EventType.update)]
        # user_names = [member.user.username]
        # send_socket_message(socket_data, user_names)
        # # Отправка сообщения по socketio:
        # users = list(chat.members.filter(is_active=True).values_list('user', flat=True))
        # tasks.send_socketio_message.delay(serialized_data, get_obj_type(member), EventType.update.value, users)
        return Response(serialized_data, status=status.HTTP_200_OK)


class ModeratorAssignView(APIView, ModeratorChangeStatusMixin):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.change_status(request, True)


class ModeratorDismissView(APIView, ModeratorChangeStatusMixin):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.change_status(request, False)


class ChatSearchView(HaystackViewSet):
    index_models = (models.ChatModel, User)
    serializer_class = serializers.ChatSearchSerializer
    pagination_class = paginators.ChatPagination
    permission_classes = (
        IsAuthenticated,
    )

    def list(self, request, *args, **kwargs):
        user = request.user.profile
        text = request.query_params.get('text')
        search_queryset = utils.get_chat_search_queryset(user, text)
        guess = None
        if len(search_queryset) == 0:
            text = request.query_params.get('text')
            guess = SearchQuerySet().spelling_suggestion(text)
            if guess:
                search_queryset = utils.get_chat_search_queryset(user, guess)
        page = self.paginate_queryset(search_queryset)
        serializer = self.serializer_class(page, many=True, context={'request': request})
        s_data = serializer.data
        if guess and len(s_data) > 0:
            s_data[0]['guess'] = guess
        return self.get_paginated_response(s_data)


class MessageSearchView(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination
    serializer_class = serializers.MessageListSerializer

    def get(self, request, *args, **kwargs):
        chat_uid = request.query_params.get('chat')
        user = request.user.profile
        text = request.query_params.get('text', '')
        queryset = models.MessageModel.objects.filter(
            is_active=True,
            is_deleted=False,
            chat__member__user=user,
            chat__member__is_active=True,
        )
        if chat_uid:
            queryset = queryset.filter(chat_id=chat_uid)
        queryset = filter_by_search(text, models.MessageModel, queryset)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, self)
        serializer = serializers.MessageListSerializer(
            page,
            many=True,
            context={'request': request, 'view': self, }
        )
        return paginator.get_paginated_response(serializer.data)


class AltChatSearchView(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = paginators.ChatPagination
    serializer_class = serializers.AltChatSearchSerializer

    def get(self, request, *args, **kwargs):
        from common.models import BaseModel
        from common.utils import get_search_result
        from users.utils import filter_users_by_organizations
        user = request.user.profile
        text = request.query_params.get('text')

        search_result = get_search_result(ProfileModel, text)
        search_result_ids = [item['id'] for item in search_result]

        chats_id = []
        users_id = []

        # Публичные чаты по имени, где текущий пользователь является участником
        public_chats_by_name_ids = list(models.ChatModel.objects.filter(
            Q(name__icontains=text) &
            Q(is_public=True) &
            Q(is_active=True) &
            Q(member__user_id=user.pk, member__is_active=True)
        ).values_list('pk', flat=True))

        if search_result_ids:
            # Приватные чаты с пользователям
            members_qs = models.MemberModel.objects.filter(
                Q(user_id__in=search_result_ids) &
                Q(chat__member__user_id=user.pk, chat__member__is_active=True) &
                Q(chat__is_public=False) &
                Q(chat__is_active=True)
            ).exclude(
                user_id=user.pk
            )
            chats_id.extend(members_qs.values_list('chat__pk', flat=True))

            # Просто пользователи, с которыми еще нет приватных чатов
            found_member_user_ids = members_qs.values_list('user', flat=True)
            users_id = filter_users_by_organizations(
                ProfileModel.objects.filter(
                    pk__in=search_result_ids,
                    is_active=True,
                ),
                user,
                add_support_users=True,
                add_org_support_users=True,
            ).exclude(pk__in=found_member_user_ids).values_list('pk', flat=True)

        chats_id.extend(public_chats_by_name_ids)

        qs = BaseModel.objects.filter(Q(pk__in=chats_id) | Q(pk__in=users_id), is_active=True)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = self.serializer_class(page, many=True, context={'request': request})
        s_data = serializer.data
        response = paginator.get_paginated_response(s_data)
        return response


class RecoverChatRooms(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        utils.recover_chat_rooms()
        return Response('ok')


class SupportMessageTemplateViewSet(BaseModelViewSet):
    model = models.SupportMessageTemplateModel
    permission_classes = (permissions.OnlySupportPermission, IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=('is_active',))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClearMessageKeysView(APIView):

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        map_keys = socketio_redis.keys('messages*')
        for each in map_keys:
            socketio_redis.delete(each)
        return Response({"deleted": map_keys})


class ChatSummaryView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        chat_uid = kwargs.get('chat_uid')
        if not chat_uid:
            raise drf_exceptions.NotFound('Chat not found')

        try:
            chat = models.ChatModel.objects.get(chat_uid=chat_uid, is_active=True)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound('Chat not found')

        # Check permissions
        if not chat.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()

        # Get date parameters from request body
        start_date_str = request.data.get('start')
        end_date_str = request.data.get('end')

        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'Both start and end date parameters are required (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse and validate dates
        try:
            date_from = timezone.make_aware(datetime.fromisoformat(start_date_str))
            # For end date, include the entire day (extend to end of day)
            date_to = timezone.make_aware(datetime.fromisoformat(end_date_str)) + timedelta(days=1) - timedelta(
                microseconds=1)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate date range
        if date_from > date_to:
            return Response(
                {'error': 'Start date must be before or equal to end date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if there's already a pending summary for this user and chat
        user = request.user.profile
        start_date_obj = date_from.date()
        end_date_obj = datetime.fromisoformat(end_date_str).date()

        existing_pending = models.ChatSummaryModel.objects.filter(
            chat=chat,
            user=user,
            status='pending',
            is_active=True
        ).first()

        if existing_pending:
            # Return existing pending record
            serializer = serializers.ChatSummarySerializer(existing_pending)
            return Response(serializer.data)

        # Create ChatSummaryModel record with pending status
        chat_summary = models.ChatSummaryModel.objects.create(
            chat=chat,
            user=user,
            start_date=start_date_obj,
            end_date=end_date_obj,
            status='pending',
            started_at=timezone.now(),
        )

        # Delete all other ChatSummaryModel records for this chat and user with status != 'pending'
        models.ChatSummaryModel.objects.filter(
            chat=chat,
            user=user,
            status__in=['completed', 'failed'],
            is_active=True
        ).delete()

        # Start async task for summary generation
        async_task(utils.generate_chat_summary, str(chat_summary.pk))

        # Return pending summary immediately
        serializer = serializers.ChatSummarySerializer(chat_summary)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        chat_uid = kwargs.get('chat_uid')
        chat = models.ChatModel.objects.get(chat_uid=chat_uid, is_active=True)
        if not chat.get_detail_permission(request):
            raise drf_exceptions.PermissionDenied()

        user_id = request.user.profile.pk
        chat_summary = models.ChatSummaryModel.objects.filter(
            chat=chat,
            user_id=user_id,
            is_active=True
        ).order_by('-created_at').first()

        if not chat_summary:
            raise drf_exceptions.NotFound('Chat summary not found')

        serializer = serializers.ChatSummarySerializer(chat_summary)
        return Response(serializer.data)
