import json
import random
from decimal import Decimal
from datetime import datetime

from django.apps import apps
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.urls import reverse
from django_q.tasks import async_task
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework import exceptions as drf_exceptions
from rest_framework.exceptions import PermissionDenied

from common.views import BaseModelViewSet
from common.current_profile.middleware import get_current_authenticated_profile
from . import models
from .utils.intents import build_resolved_data
from .utils.messages import process_message
from .utils.workflow_requests import is_workflow_request_intent, materialize_workflow_request_intent
from .paginators import AIMessagePagination


# permissions.py
from rest_framework import permissions

class AIBotEnabled(permissions.BasePermission):
    message = "Доступ к AI-боту отключён для вашего профиля. Обратитесь к администратору."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        # Профиль может отсутствовать — на всякий случай обрабатываем
        profile = getattr(user, "profile", None)
        return bool(getattr(profile, "use_ai_bot", False))



class AIChatViewSet(BaseModelViewSet):
    model = models.AIChatModel
    permission_classes = (IsAuthenticated, AIBotEnabled)

    def list(self, request, *args, **kwargs):
        """
        Получить список чатов пользователя.
        Если у пользователя нет активных чатов, создает новый и возвращает его.
        """
        profile = request.user.profile

        # Получаем активные чаты пользователя
        active_chats = self.get_queryset().filter(
            chat_author=profile,
            is_active=True
        )

        # Если нет активных чатов, создаем новый
        if not active_chats.exists():
            models.AIChatModel.objects.create(
                chat_author=profile,
                name=f"Чат {profile.full_name}",
                is_active=True
            )

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True, context={
            'request': request
            })
        return self.get_paginated_response(serializer.data)

    @action(methods=['post'], detail=True, url_path='clear-messages')
    def clear_messages(self, request, pk=None):
        """Очистить все сообщения чата."""
        chat = self.get_object()
        if chat.chat_author != request.user.profile:
            return Response(
                {'error': 'У вас нет прав для очистки этого чата'},
                status=status.HTTP_403_FORBIDDEN
            )
        with transaction.atomic():
            messages = models.AIMessageModel.objects.filter(is_active=True, chat=chat)
            intents = models.IntentModel.objects.filter(is_active=True, source_object__in=messages)
            current_time = datetime.now()
            intents.update(is_active=False, deleted_at=current_time)
            messages.update(is_active=False, deleted_at=current_time)
            chat.last_sent = current_time
            chat.save()

        return Response(status=status.HTTP_200_OK)


class AIMessageViewSet(BaseModelViewSet):
    model = models.AIMessageModel
    permission_classes = (IsAuthenticated,)
    pagination_class = AIMessagePagination

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            chat__chat_author=self.request.user.profile,
            chat__is_active=True,
        )
        chat_id = self.request.query_params.get('chat')
        since = self.request.query_params.get('since')
        slice_count = self.request.query_params.get('slice_count')
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        if since:
            queryset = queryset.filter(created_at__gt=since)
        queryset = queryset.order_by('-created_at')
        if slice_count:
            excluded = queryset[:int(slice_count)]
            queryset = queryset.exclude(pk__in=excluded)
        return queryset

    def get_owned_chat(self, request, chat_id):
        try:
            return models.AIChatModel.objects.get(
                pk=chat_id,
                chat_author=request.user.profile,
                is_active=True,
            )
        except models.AIChatModel.DoesNotExist:
            raise PermissionDenied('У вас нет доступа к этому чату')

    # def create(self, request, *args, **kwargs):
    #     """Заглушка для создания сообщения пользователя."""
    #     # Возвращаем фиксированный JSON ответ
    #     response_data = {
    #         "id": "8224ef7b-9788-11f0-81dd-f98f0fe182e9",
    #         "created_at": "2025-09-22T10:48:20.336804+03:00",
    #         "message_author": None,
    #         "chat": "d3556fce-8fda-11f0-90b7-8d510b2412da",
    #         "reply_to": "76a480c0-9788-11f0-81dd-f98f0fe182e9",
    #         "text": "Я выявил 3 намерени(я/й). Проверьте и уточните данные при необходимости.",
    #         "status": "done",
    #         "is_bot": True,
    #         "is_intent": False,
    #         "intents": STUB_INTENTS_DATA
    #     }

    #     return Response(response_data, status=status.HTTP_201_CREATED)

    def create_sync_legacy(self, request, *args, **kwargs):
        """Создает сообщение пользователя и возвращает ответ бота."""
        chat_id = request.data.get('chat')
        chat = self.get_owned_chat(request, chat_id)

        with transaction.atomic():
            # Создаем сообщение пользователя
            user_message_data = {
                'chat': chat_id,
                'text': request.data.get('text', ''),
                'message_author': request.user.profile,
                'status': 'queued',
            }
            user_serializer = self.get_serializer(data=user_message_data)
            user_serializer.is_valid(raise_exception=True)
            user_message = user_serializer.save()

            # Обновляем last_sent у чата
            chat.last_sent = timezone.now()
            chat.save(update_fields=['last_sent'])

            # async_task(process_message, user_message.id) # пока решили сделать синхронно
            bot_msg = process_message(user_message.id, request)

            serializer_class = bot_msg.get_serializer_class(action='detail')
            serializer = serializer_class(bot_msg)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    def create(self, request, *args, **kwargs):
        """Accept user message, create assistant placeholder, and process asynchronously."""
        chat_id = request.data.get('chat')
        chat = self.get_owned_chat(request, chat_id)

        with transaction.atomic():
            user_message_data = {
                'chat': chat_id,
                'text': request.data.get('text', ''),
                'message_author': request.user.profile,
                'status': 'queued',
            }
            user_serializer = self.get_serializer(data=user_message_data)
            user_serializer.is_valid(raise_exception=True)
            user_message = user_serializer.save()

            chat.last_sent = timezone.now()
            chat.save(update_fields=['last_sent'])

            bot_msg = models.AIMessageModel.objects.create(
                chat=chat,
                message_author=None,
                text='',
                is_bot=True,
                reply_to=user_message,
                status_id='queued',
            )

            response_payload = {
                'status': 'accepted',
                'chat_id': str(chat.pk),
                'job_id': str(user_message.pk),
                'user_message': user_message.get_serializer_class(action='detail')(user_message).data,
                'assistant_message': bot_msg.get_serializer_class(action='detail')(bot_msg).data,
            }

            transaction.on_commit(
                lambda: async_task(
                    process_message,
                    str(user_message.pk),
                    str(bot_msg.pk),
                    str(request.user.profile.pk),
                )
            )

            return Response(response_payload, status=status.HTTP_202_ACCEPTED)

    @action(methods=['get'], detail=True, url_path='status')
    def status(self, request, pk=None):
        """Возвращает только статус сообщения."""
        from .serializers import MessageStatusSerializer
        message = self.get_object()
        serializer = MessageStatusSerializer(message)
        return Response(serializer.data)


class IntentModelViewSet(BaseModelViewSet):
    model = models.IntentModel
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.set_is_active(False, request)
        instance.save(update_fields=('is_active', 'deleted_at',))
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(methods=['put', 'patch'], detail=True, url_path='update-value')
    def update_value(self, request, pk=None):
        intent = self.get_object()
        
        if not intent.get_update_permission(request):
            raise PermissionDenied('У вас нет прав на редактирование этого намерения')
        
        field_name = request.data.get('field_name')
        raw_value = request.data.get('value')
        field_metadata = request.data.get('metadata')

        # Получаем метаданные поля
        metadata = getattr(intent.intent_type, 'metadata', {})
        schema = metadata.get('fields', {})
        field_def = schema.get(field_name)

        if not field_def:
            return Response({'error': 'Field not found'}, status=400)

        # Обрабатываем null значение
        if raw_value is None:
            # Получаем default значение из метаданных поля
            default_value = field_def.get('default')
            processed_value = default_value if default_value is not None else None
        else:
            # Определяем тип поля
            field_type = field_def.get("type", "")
            model_path = field_def.get("model", "")

            # Обрабатываем value в зависимости от типа
            if model_path:
                # Ссылочное поле
                from django.apps import apps
                app_label, model_name = model_path.split('.', 1)
                model_class = apps.get_model(app_label, model_name)

                if field_type in ["ForeignKey", "OneToOneField"]:
                    processed_value = model_class.get_snapshot(raw_value)
                elif field_type == "ManyToManyField":
                    processed_value = [model_class.get_snapshot(id) for id in raw_value]
            else:
                # Простое поле
                processed_value = str(raw_value)

        # Обновляем value в resolutions
        if field_name in intent.resolutions:
            intent.resolutions[field_name]["value"] = processed_value

            # Если передали metadata, сохраняем его
            if field_metadata is not None:
                intent.resolutions[field_name]["metadata"] = field_metadata

            # Запускаем повторную обработку
            build_resolved_data(intent)
            intent.save()

        return Response({'status': 'updated'})

    @action(methods=['post'], detail=True, url_path='materialize')
    def materialize(self, request, pk=None):
        """Создать объект из намерения."""
        intent = self.get_object()
        
        if not intent.get_update_permission(request):
            raise PermissionDenied('У вас нет прав на создание объекта из этого намерения')

        # Проверяем статус намерения
        if intent.status_id != 'ready':
            return Response({
                'error': f'Intent status must be "ready", current status: {intent.status_id}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем метаданные
        metadata = getattr(intent.intent_type, 'metadata', {})
        target_info = metadata.get('target', {})
        model_path = target_info.get('model')
        action = target_info.get('action', 'create')

        try:
            if is_workflow_request_intent(intent):
                created_object = materialize_workflow_request_intent(intent, request)
                return Response({
                    'status': 'success',
                    'object_id': str(created_object.pk),
                    'object_type': created_object.__class__.__name__
                }, status=status.HTTP_201_CREATED)

            with transaction.atomic():
                # Получаем модель и сериализатор через get_serializer_class
                app_label, model_name = model_path.split('.', 1)
                model_class = apps.get_model(app_label, model_name)
                serializer_class = model_class.get_serializer_class(action=action)

                # Создаем объект через сериализатор
                serializer = serializer_class(
                    data=intent.resolved_data,
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                created_object = serializer.save()

                # Обновляем intent внутри транзакции при успехе
                intent.related_object = created_object
                intent.status_id = 'done'
                intent.errors = []
                intent.save(update_fields=['related_object', 'status', 'errors'])

            return Response({
                'status': 'success',
                'object_id': str(created_object.pk),
                'object_type': created_object.__class__.__name__
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            error_message = f'Failed to materialize intent: {str(e)}'
            # Обновляем статус intent на failed вне транзакции
            intent.status_id = 'failed'
            intent.errors = error_message
            intent.save(update_fields=['status', 'errors'])
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)


# --- Export/Import AI Chat Roles (admin) ---

EXPORT_FIELDS = (
    'code', 'name', 'sort', 'is_active', 'is_predefined',
    'user_message', 'system_message', 'description',
    'model_name', 'temperature', 'max_output_tokens', 'top_p', 'num_ctx',
)


def _role_to_export_dict(role):
    """Serialize one AIChatRoleModel to export dict (no id, provider as code)."""
    data = {}
    for field_name in EXPORT_FIELDS:
        value = getattr(role, field_name)
        if field_name in ('temperature', 'top_p') and value is not None:
            value = str(value)
        data[field_name] = value
    data['provider'] = role.provider_id if role.provider_id else None
    return data


@method_decorator(staff_member_required, name='dispatch')
class ExportAIChatRolesView(View):
    """Страница выбора ролей и скачивание JSON-файла."""

    def get_roles_queryset(self):
        return models.AIChatRoleModel.objects.select_related('provider').defer(
            'provider__api_key'
        ).order_by('-sort')

    def get(self, request):
        roles = self.get_roles_queryset()
        return render(request, 'chat_ai/export_roles.html', {'roles': roles})

    def post(self, request):
        selected_ids = request.POST.getlist('role_ids')
        if not selected_ids:
            roles = self.get_roles_queryset()
            messages.error(request, 'Выберите хотя бы одну роль для выгрузки.')
            return render(request, 'chat_ai/export_roles.html', {'roles': roles})
        roles = self.get_roles_queryset().filter(pk__in=selected_ids)
        payload = {
            'version': 1,
            'exported_at': timezone.now().isoformat(),
            'roles': [_role_to_export_dict(role) for role in roles],
        }
        json_str = json.dumps(payload, ensure_ascii=False, indent=2)
        filename = f"ai_chat_roles_{timezone.now().strftime('%Y%m%d_%H%M')}.json"
        response = HttpResponse(json_str, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


@method_decorator(staff_member_required, name='dispatch')
class ImportAIChatRolesView(View):
    """Страница загрузки JSON-файла и импорт ролей (по code: update or create)."""

    def get(self, request):
        return render(request, 'chat_ai/import_roles.html')

    def post(self, request):
        upload = request.FILES.get('file')
        if not upload:
            messages.error(request, 'Выберите файл для загрузки.')
            return render(request, 'chat_ai/import_roles.html')
        try:
            raw = upload.read().decode('utf-8')
            data = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            messages.error(request, f'Ошибка чтения JSON: {exc}')
            return render(request, 'chat_ai/import_roles.html')
        roles_data = data.get('roles') if isinstance(data, dict) else data
        if not isinstance(roles_data, list):
            messages.error(request, 'В файле должен быть список ролей (ключ "roles" или корневой массив).')
            return render(request, 'chat_ai/import_roles.html')
        created = 0
        updated = 0
        errors = []
        profile = get_current_authenticated_profile()
        if not profile:
            profile = getattr(request.user, 'profile', None)
        for item in roles_data:
            if not isinstance(item, dict):
                errors.append('Запись не является объектом — пропущена.')
                continue
            code = item.get('code')
            if not code:
                errors.append('Запись без code — пропущена.')
                continue
            provider_code = item.get('provider')
            provider = None
            if provider_code:
                try:
                    provider = models.AIProvider.objects.defer('api_key').get(code=provider_code)
                except models.AIProvider.DoesNotExist:
                    errors.append(f'Роль {code}: провайдер с code="{provider_code}" не найден.')
                    continue
            try:
                role = models.AIChatRoleModel.objects.filter(code=code).first()
                if role:
                    for field_name in EXPORT_FIELDS:
                        if field_name in item:
                            value = item[field_name]
                            if field_name in ('temperature', 'top_p') and value is not None:
                                value = Decimal(str(value))
                            setattr(role, field_name, value)
                    if provider is not None:
                        role.provider_id = provider.code
                    role.save()
                    updated += 1
                else:
                    kwargs = {'code': code, 'author': profile}
                    for field_name in EXPORT_FIELDS:
                        if field_name in item:
                            value = item[field_name]
                            if field_name in ('temperature', 'top_p') and value is not None:
                                value = Decimal(str(value))
                            kwargs[field_name] = value
                    if provider is not None:
                        kwargs['provider_id'] = provider.code
                    models.AIChatRoleModel.objects.create(**kwargs)
                    created += 1
            except Exception as exc:
                errors.append(f'Роль {code}: {exc}')
        changelist_url = reverse('admin:chat_ai_aichatrolemodel_changelist')
        if created or updated:
            messages.success(
                request,
                f'Импорт завершён: создано {created}, обновлено {updated}.'
            )
        for err in errors:
            messages.error(request, err)
        if not (created or updated) and not errors:
            messages.warning(request, 'Нет записей для импорта.')
        return redirect(changelist_url)
