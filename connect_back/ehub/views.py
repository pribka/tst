import requests
import json

from django.http.response import HttpResponseRedirect, HttpResponse, JsonResponse

from rest_framework import status
from rest_framework import exceptions as drf_exceptions
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import MultiPartRenderer, BrowsableAPIRenderer, JSONRenderer

from bkz3.settings import EHUB_TOKEN

from . import models, serializers


class EhubRegisterView(APIView):
    permission_classes = ()
    authentication_classes = ()
    renderer_classes = (MultiPartRenderer, JSONRenderer)

    def post(self, request, *args, **kwargs):
        serializer = serializers.EhubRegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        region = validated_data.get('region')
        avatar = validated_data.get('avatar')
        data = serializer.data
        data.pop('avatar')
        data.pop('region')
        resp = requests.post(
            url=f'{region.internal_url}/api/e-hub/register/',
            data=data,
            files={'avatar': avatar},
            cookies={'ehubtoken': EHUB_TOKEN}
        )
        if resp.status_code == 200:
            return JsonResponse(json.loads(resp.text))
        elif resp.status_code == 500:
            return JsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"message": "Ошибка сервера"})
        else:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=json.loads(resp.text))


class RedirectToServerView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        code = kwargs.get('code')
        if not code:
            raise drf_exceptions.NotFound()
        try:
            server = models.EhubServerModel.objects.get(is_active=True, code=code)
        except models.EhubServerModel.DoesNotExist:
            raise drf_exceptions.NotFound()
        email = request.user.email
        resp = requests.post(
            url=server.token_url,
            json={'username': email},
            cookies={'ehubtoken': EHUB_TOKEN}
        )
        if not resp.status_code == 200:
            raise drf_exceptions.NotFound()
        no_redirect = 'no_redirect' in request.query_params
        if no_redirect:
            return Response({'ehub_token': json.loads(resp.text)})
        return HttpResponseRedirect(redirect_to=f'{server.frontend_url}/?ehub_token={json.loads(resp.text)}')


class ServerListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.EhubServerListSerializer
    queryset = models.EhubServerModel.objects.filter(is_active=True)

    def get_queryset(self):
        queryset = self.queryset
        server_group = self.request.query_params.get('server_group')
        if server_group:
            queryset = queryset.filter(server_group_id=server_group)
        user = self.request.user.profile
        queryset = queryset.filter(users=user).distinct()
        return queryset.order_by('sort', 'name',)


class EhubRegionModelListView(ListAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializers.EhubRegionModelListSerializer
    queryset = models.EhubRegionModel.objects.filter(is_active=True).order_by('sort', 'name')


class EhubListView(APIView):
    permission_classes = ()
    authentication_classes = ()
    api_path = '/api/e-hub/insert_you_slug/'

    def get(self, request, *args, **kwargs):
        query_params = request.query_params
        region_code = query_params.get('region')
        try:
            region = models.EhubRegionModel.objects.get(code=region_code, is_active=True)
        except models.EhubRegionModel.DoesNotExist:
            raise drf_exceptions.ValidationError({'message': 'Сервер не найден'})

        resp = requests.get(
            url=f'{region.internal_url}{self.api_path}',
            params=query_params,
            cookies={'ehubtoken': EHUB_TOKEN}
        )

        if resp.status_code == 200:
            data = json.loads(resp.text)
            next_url = data.get('next')
            if next_url:
                data['next'] = True
            data.pop('previous', None)
            return Response(data)
        else:
            return Response(resp.reason, status=status.HTTP_400_BAD_REQUEST)


class AlmaMaterListView(EhubListView):
    api_path = '/api/e-hub/alma_maters/'


class PositionListView(EhubListView):
    api_path = '/api/e-hub/positions/'


class LanguageListView(EhubListView):
    api_path = '/api/e-hub/languages/'


class SexListView(EhubListView):
    api_path = '/api/e-hub/sexes/'


class GetAvatarView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request, *args, **kwargs):
        username = request.query_params.get('username')
        resp = requests.get(
            f'http://127.0.0.1:8003/api/e-hub/user/avatar/?username={username}',
            cookies={'ehubtoken': EHUB_TOKEN},
        )
        if not resp.status_code == 200:
            return Response({'status': resp.status_code})
        from common.models import File
        from django.core.files import File as DjangoFile
        from io import BytesIO
        stream = BytesIO(resp.content)
        filename = resp.headers.get('Content-Disposition').split(';')[-1].strip(' filename=').strip('"')
        django_file = DjangoFile(file=stream, name=filename)
        avatar_file = File()
        avatar_file.upload = django_file
        avatar_file.save()

        return Response({'status': resp.status_code})


class ChatInfoView(APIView):
    """
    Ендпоинт для внутреннего обмена между серверами.
    Возвращает наличие присутствия пользователей user и recipient, а также наличие чата между ними.
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        from users.models import CustomUser
        from django.core.exceptions import ValidationError
        from bpms.chat.models import ChatModel, MemberModel
        from django.db.models import Count, Q
        data = request.data
        return_data = {
            'has_user': False,
            'has_recipient': False,
            'recipient_id': None,
            'has_chat': False,
            'chat_id': None

        }
        user_email = data.get('user')
        recipient_email = data.get('recipient')
        try:
            user = CustomUser.objects.get(email=user_email)
        except (CustomUser.DoesNotExist, ValidationError):
            return Response(return_data)
        return_data['has_user'] = True
        try:
            recipient = CustomUser.objects.get(email=recipient_email)
        except (CustomUser.DoesNotExist, ValidationError):
            return Response(return_data)
        return_data['has_recipient'] = True
        return_data['recipient_id'] = str(recipient.profile.pk)
        qs = ChatModel.objects.filter(is_active=True, is_public=False).annotate(
            has_user=Count('member', filter=Q(member__user=user.profile)),
            has_recipient=Count('member', filter=Q(member__user=recipient.profile))
        ).filter(has_user__gte=1, has_recipient__gte=1)
        has_chat = qs.exists()
        if not has_chat:
            return Response(return_data)
        return_data['has_chat'] = True
        chat = qs.order_by('-created_at').first()
        return_data['chat_id'] = chat.chat_uid
        return Response(return_data)
