import json
import requests
import secrets
import string
import datetime
import uuid
from functools import partial

from django.conf import settings
from django.http import HttpResponseRedirect
from django.middleware import csrf
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.views import redirect_to_login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import DesktopAuthCode, DesktopWebViewSecret
from bpms.voting.apiviews import VoteView
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Value, Q, Case, When, Count, Prefetch, BooleanField, PositiveIntegerField, \
    CharField, OuterRef, Func, F, Subquery, Exists
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import status, generics, viewsets, exceptions as drf_exceptions

from common import views as common_views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.throttling import AnonRateThrottle

from axes.decorators import axes_dispatch
from drf_haystack.generics import GenericAPIView as HaystackGenericApiView
from haystack.query import SearchQuerySet
from haystack.query import RelatedSearchQuerySet
from django_q.tasks import async_task

from bkz3.settings import TOKEN_URV
from bkz3.settings import TG_BOT_NAME, FRONTEND_URL

from common import paginators
from common import utils as common_utils
from common.models import FiltersStore
from common.serializers import CachedBaseModelSerializer
from common.current_profile.middleware import get_current_authenticated_profile
from common.paginators import CustomPagination
from common.catalogs.models import ContractorModel, ContractorProfileModel
from common.catalogs.models import ContractorMemberModel, ContractorRelationModel, ContractorDepartmentModel
from common.utils import get_search_bool, get_filter_queryset, filter_queryset_from_get_param, use_access_groups, \
    get_search_result
from common.catalogs.serializers import (ContractorRelationModelListSerializer, ContractorDepartmentListSerializer,
                                         ContractorDepartmentCreateSerializer, ContractorDepartmentUpdateSerializer,
                                         ContractorDepartmentDetailSerializer,
                                         ContractorDepartmentShortListSerializer, MyContractorsListSerializer,
                                         ContractorModelDetailSerializer,
                                         ContractorModelShortSerializer)

from ehub.models import EhubServerModel

from contractor_permissions.models import ContractorPermissionRoleModel, ContractorPermissionRoleProfileModel
from contractor_permissions.utils import (
    check_contractor_permission,
    contractors_where_user_has_permission,
    users_that_have_permission_in_contractors,
)

from notifications.event_types import SetNewPassword

from integration_1c import utils as integration_1c_utils

from app_info.models import AppInfo

from bpms.tasks.models import TaskModel
from bpms.tasks.utils import get_tasks_status_count

from bpms.workgroups.models import WorkgroupModel
from bpms.chat.serializers import ChatListSerializer

from . import models, notifications, utils, serializers, permissions
from .models import ProfileModel, GoogleTokenModel, GoogleOAuthClientIDsModel
from .serializers import AppUserSerializer, AppObjectViewerSerializer

from users.models import C1RoleModel


class CheckEmailThrottle(AnonRateThrottle):
    rate = '5/min'


from axes.decorators import axes_dispatch


class CustomUserViewSet(viewsets.ViewSet):

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'login':
            return serializers.LoginCustomUserSerializer
        elif self.action == 'get_info':
            return serializers.CustomUserDetailSerializer
        elif self.action == 'register':
            return serializers.RegisterUserSerializer

    @action(methods=('get',), detail=False, url_path='tab_info', permission_classes=(IsAuthenticated,))
    def get_tab_info(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(is_active=True, code='users_tab_info').metadata
        except AppInfo.DoesNotExist:
            data = [
                {
                    'code': 'users',
                    'name': 'Список пользователей',
                    'widget': 'userList'
                }
            ]
        return Response(data)

    @action(
        methods=('post',),
        detail=False,
        url_path='send_confirm_code',
        permission_classes=(),
        authentication_classes=(),
    )
    def send_confirm_code(self, request, *args, **kwargs):
        data = request.data
        serializer = serializers.SendConfirmCodeSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        login_name = serializer.validated_data.get('login')
        target = serializer.validated_data.get('target')
        confirm_code = utils.set_confirm_code(login_name, target)
        print(f'\n\nconfirm_code  {confirm_code}\n\n')
        if target == 'email':
            async_task(utils.send_email_confirm_code, login_name, confirm_code)
        elif target == 'phone':
            async_task(utils.send_sms_confirm_code, login_name, confirm_code)
        return Response('ok')

    @action(
        methods=('post',),
        detail=False,
        url_path='check_email',
        permission_classes=(),
        authentication_classes=(),
        throttle_classes=(CheckEmailThrottle,)
    )
    def check_email(self, request, *args, **kwargs):
        serializer = serializers.CheckEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'is_user_exists': serializer.validated_data.get('is_user_exists')
        })

    @action(
        methods=("post",),
        detail=False,
        url_path="confirm",
        permission_classes=(),
        authentication_classes=(),
    )
    def confirm(self, request, *args, **kwargs):
        confirm_code = request.data.get('confirm_code', '')
        if not isinstance(confirm_code, str) or not confirm_code:
            raise drf_exceptions.ValidationError("Неверный код подтверждения.")
        invite_token = request.data.get('invite_token')
        if invite_token:
            utils.check_invite_token(invite_token)
        login_name = request.data.get('login', '').strip().lower()
        target = request.data.get('target', 'email')
        target_name = utils.get_target_name(target)
        if not isinstance(login_name, str) or not login_name:
            raise drf_exceptions.ValidationError(f"Некорректный {target_name}.")
        if utils.check_login_exist(login_name):
            raise drf_exceptions.ValidationError({"message": f"Такой {target_name} уже существует."})
        if not utils.check_confirm_code(login_name, target, confirm_code):
            raise drf_exceptions.ValidationError({"message": "Неверный код подтверждения."})
        confirm_token = utils.set_confirm_token(login_name, target)
        return Response({"confirm_token": confirm_token})

    @action(
        methods=("post",),
        detail=False,
        url_path="validate_password",
        permission_classes=(),
        authentication_classes=(),
    )
    def validate_password(self, request, *args, **kwargs):
        serializer = serializers.ValidatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response()

    @action(
        methods=("post",),
        detail=False,
        url_path='register',
        url_name='register',
        permission_classes=(),
        authentication_classes=(),
    )
    def register(self, request, *args, **kwargs):
        data = request.data
        serializer = serializers.RegisterUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend='axes.backends.AxesBackend')
        refresh = RefreshToken.for_user(user)
        serialized_data = serializers.CustomUserDetailSerializer(instance=user.profile).data
        serialized_data['jwt_access'] = str(refresh.access_token)
        serialized_data['jwt_refresh'] = str(refresh)
        serialized_data['user_previous_login'] = None
        return Response(data=serialized_data, status=status.HTTP_200_OK)

    @action(
        methods=("post",),
        detail=False,
        url_path='b2g/register',
        permission_classes=(),
        authentication_classes=(),
    )
    def register_b2g(self, request, *args, **kwargs):
        data = request.data
        serializer = serializers.RegisterUserB2GSerializer(data=data, context={'request': request, 'view': self})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend='axes.backends.AxesBackend')
        refresh = RefreshToken.for_user(user)
        serialized_data = serializers.CustomUserDetailSerializer(
            instance=user.profile,
            context={'request': request, 'view': self}
        ).data
        serialized_data['jwt_access'] = str(refresh.access_token)
        serialized_data['user_previous_login'] = None
        serialized_data['entry_complete'] = utils.get_entry_complete(user.profile)
        return Response(data=serialized_data, status=status.HTTP_200_OK)

    @action(
        methods=("put", "get",),
        detail=False,
        url_path='b2g/entry',
        permission_classes=(IsAuthenticated,)
    )
    def entry_b2g(self, request, *args, **kwargs):
        user = request.user.profile
        try:
            instance = user.entry_info
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError({"message": "Вы уже прошли первичную настройку"})
        else:
            if not instance.complete:
                if request.method == 'PUT':
                    serializer = serializers.EntryInfoModelUpdateSerializer(
                        instance=instance,
                        data=request.data,
                        context={'request': request, 'view': self},
                    )
                    serializer.is_valid(raise_exception=True)
                    instance = serializer.save()
                else:
                    pass
                serializer_data = serializers.EntryInfoModelDetailSerializer(instance).data
                return Response(serializer_data)

            else:
                raise drf_exceptions.ValidationError({"message": "Вы уже прошли первичную настройку"})

    @action(methods=('get',), detail=False, url_path='entry/invite_url')
    def get_entry_invite_url(self, request, *args, **kwargs):
        user = request.user.profile
        if utils.get_entry_complete(user):
            raise drf_exceptions.ValidationError({"message": "Вы уже прошли первичную настройку"})
        invite = models.InviteModel.objects.filter(
            is_active=True,
            contractor=None,
            author=user
        ).order_by('-created_at').first()
        if not invite:
            invite = models.InviteModel.objects.create(is_active=True, contractor=None)
        return Response(
            {
                "invite": utils.get_invite_url(invite.token),
                "deactivate_at": invite.deactivate_at,
                "token": invite.token,
            }
        )

    @action(
        methods=("post",),
        detail=False,
        url_path="intro",
        permission_classes=(IsAuthenticated,),
    )
    def intro(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        serializer = serializers.UserIntroSerializer(data=data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        s_data = serializers.CustomUserDetailSerializer(instance=user.profile).data
        return Response(s_data)

    @action(methods=["post", ], detail=False, url_path="login", url_name="login", permission_classes=(),
            authentication_classes=())
    @method_decorator(axes_dispatch, name='dispatch')
    def login(self, request, *args, **kwargs):
        """Логин пользователя в приложение"""
        input_serializer = serializers.LoginCustomUserSerializer(data=request.data, context={"request": request})
        try:
            input_serializer.is_valid(raise_exception=True)
        except drf_exceptions.ValidationError as exc:
            errors = exc.detail
            if not (isinstance(errors, dict) and 'captcha' in errors):
                raise
            response_data = {
                "status": "Ошибка reCAPTCHA",
            }
            if settings.DEBUG:
                response_data["captcha_debug"] = utils.build_captcha_debug_data(request, exc)
            return Response(data=response_data, status=status.HTTP_400_BAD_REQUEST)
        input_val_data = input_serializer.validated_data
        email = input_val_data.get('email', '').lower()
        password = input_val_data.get('password')
        if email:
            try:
                user = models.CustomUser.objects.get(email=email)
            except models.CustomUser.DoesNotExist:
                data = dict()
                correct_password = False
                login_data = dict()
                for ehub_server in list(EhubServerModel.objects.filter(is_active=True).order_by('created_at', )):
                    resp = requests.post(
                        url=ehub_server.user_url,
                        json={'username': email, 'password': password},
                    )
                    if not resp.status_code == 200:
                        continue
                    ehub_data = json.loads(resp.text)
                    if ehub_data.get('correct_password'):
                        correct_password = True
                        login_data = ehub_data
                    data[ehub_server.code] = ehub_data
                if not data:
                    # Вызываем authenticate для несуществующего пользователя,
                    # чтобы axes зафиксировал неудачную попытку входа
                    authenticate(request, username=email, password=password)
                    return Response(data={"status": "Логин или пароль не верны"},
                                    status=status.HTTP_403_FORBIDDEN)
                if not login_data:
                    login_data = list(data.values())[0]
                with transaction.atomic():
                    # Создаем пользователя
                    user = models.CustomUser(username=email, email=email)
                    if not correct_password:
                        alphabet = string.ascii_letters + string.digits
                        password = ''.join(secrets.choice(alphabet) for i in range(8))
                    user.set_password(password)
                    user.first_name = login_data.get('first_name', '')
                    user.last_name = login_data.get('last_name', '')
                    user.middle_name = login_data.get('middle_name', '')
                    user.save()

                    # Создаем организацию и ее родителей, если их нет

                    contractors = list()
                    for key, value in data.items():
                        # Добавляем профилю сервера:
                        user.profile.ehub_user_servers.create(server_id=key)
                        contractors += value.get('contractors')
                    for each in contractors:
                        contractor, created = ContractorModel.objects.get_or_create(
                            code=each.get('code'), defaults={'name': each.get('name', '')}
                        )
                        if created:
                            ContractorMemberModel.objects.create(
                                contractor=contractor, inn=each.get('bin', ''), name=each.get('name')
                            )
                            parent_dict = each.get('parent')
                            contractor_buffer = contractor
                            while parent_dict is not None:
                                parent, parent_created = ContractorModel.objects.get_or_create(
                                    code=parent_dict.get('code'), defaults={'name': parent_dict.get('name', '')}
                                )
                                ContractorRelationModel.objects.create(
                                    contractor=contractor_buffer,
                                    contractor_parent=parent,
                                    relation_type_id='structural_division'
                                )
                                if parent_created:
                                    ContractorMemberModel.objects.create(
                                        contractor=parent, name=parent_dict.get('name', ''),
                                        inn=parent_dict.get('bin', '')
                                    )
                                    contractor_buffer = parent
                                    parent_dict = parent_dict.get('parent')
                                else:
                                    break
                        # Добавляем пользователя в организацию
                        ContractorProfileModel.objects.get_or_create(contractor=contractor, user=user.profile,
                                                                     defaults={'director': False})
                    # Добавляем аватар:
                    ehub_servers = user.profile.ehub_user_servers.all()
                    profile = user.profile
                    from common.models import File
                    from django.core.files import File as DjangoFile
                    from io import BytesIO
                    for each in ehub_servers:
                        server = each.server
                        resp = requests.get(f'{server.internal_url}/e-hub/user/avatar/?username={user.username}')
                        if not resp.status_code == 200:
                            continue
                        stream = BytesIO(resp.content)
                        filename = resp.headers.get('Content-Disposition').split(';')[-1].strip(' filename=').strip('"')
                        django_file = DjangoFile(file=stream, name=filename)
                        avatar_file = File()
                        avatar_file.upload = django_file
                        avatar_file.author = profile
                        avatar_file.save()
                        profile.avatar = avatar_file
                        profile.save(update_fields=('avatar',))
                        break

        else:
            phone = input_val_data.get('phone', '')
            try:
                user = models.CustomUser.objects.get(profile__phone=phone, is_active=True)
            except models.CustomUser.DoesNotExist:
                # Вызываем authenticate для несуществующего пользователя,
                # чтобы axes зафиксировал неудачную попытку входа
                # Используем phone как username для отслеживания
                authenticate(request, username=phone, password=input_val_data.get('password'))
                return Response(data={"status": "Логин или пароль не верны"},
                                status=status.HTTP_403_FORBIDDEN)
        user_previous_login = user.last_login
        auth_user = authenticate(request, username=user.username,
                                 password=input_val_data.get('password'))
        if auth_user and auth_user.profile.temporary_blocked:
            return Response(data={"status": "Пользователь заблокирован"},
                            status=status.HTTP_403_FORBIDDEN)  # TODO вывести данные об ошибке для фронтенда
        if auth_user:
            serialized_data = utils.login_user(request, user_previous_login, auth_user)
            return Response(data=serialized_data, status=status.HTTP_200_OK)
        else:
            if not user.last_login:
                ehub_servers = user.profile.ehub_servers.filter(is_active=True)
                for each in ehub_servers:
                    resp = requests.post(
                        url=each.check_password_url,
                        json={
                            "username": user.email,
                            "password": input_val_data.get('password')
                        }
                    )
                    if resp.status_code == 200:
                        user.set_password(input_val_data.get('password'))
                        user.save()
                        serialized_data = utils.login_user(request, user_previous_login, user)
                        return Response(data=serialized_data, status=status.HTTP_200_OK)
            return Response(data={"status": "Логин или пароль не верны"},
                            status=status.HTTP_403_FORBIDDEN)  # TODO вывести данные об ошибке для фронтенда

    @action(methods=["post", ], detail=False, url_path="login2", url_name="login2", permission_classes=(),
            authentication_classes=())
    @method_decorator(axes_dispatch, name='dispatch')
    def login2(self, request, *args, **kwargs):
        """Логин пользователя в приложение (без reCAPTCHA)."""
        input_serializer = serializers.LoginCustomUserSerializerNoCaptcha(
            data=request.data, context={"request": request}
        )
        input_serializer.is_valid(raise_exception=True)
        input_val_data = input_serializer.validated_data
        email = input_val_data.get('email', '').lower()
        password = input_val_data.get('password')
        if email:
            try:
                user = models.CustomUser.objects.get(email=email)
            except models.CustomUser.DoesNotExist:
                data = dict()
                correct_password = False
                login_data = dict()
                for ehub_server in list(EhubServerModel.objects.filter(is_active=True).order_by('created_at', )):
                    resp = requests.post(
                        url=ehub_server.user_url,
                        json={'username': email, 'password': password},
                    )
                    if not resp.status_code == 200:
                        continue
                    ehub_data = json.loads(resp.text)
                    if ehub_data.get('correct_password'):
                        correct_password = True
                        login_data = ehub_data
                    data[ehub_server.code] = ehub_data
                if not data:
                    authenticate(request, username=email, password=password)
                    return Response(data={"status": "Логин или пароль не верны"},
                                    status=status.HTTP_403_FORBIDDEN)
                if not login_data:
                    login_data = list(data.values())[0]
                with transaction.atomic():
                    user = models.CustomUser(username=email, email=email)
                    if not correct_password:
                        alphabet = string.ascii_letters + string.digits
                        password = ''.join(secrets.choice(alphabet) for i in range(8))
                    user.set_password(password)
                    user.first_name = login_data.get('first_name', '')
                    user.last_name = login_data.get('last_name', '')
                    user.middle_name = login_data.get('middle_name', '')
                    user.save()

                    contractors = list()
                    for key, value in data.items():
                        user.profile.ehub_user_servers.create(server_id=key)
                        contractors += value.get('contractors')
                    for each in contractors:
                        contractor, created = ContractorModel.objects.get_or_create(
                            code=each.get('code'), defaults={'name': each.get('name', '')}
                        )
                        if created:
                            ContractorMemberModel.objects.create(
                                contractor=contractor, inn=each.get('bin', ''), name=each.get('name')
                            )
                            parent_dict = each.get('parent')
                            contractor_buffer = contractor
                            while parent_dict is not None:
                                parent, parent_created = ContractorModel.objects.get_or_create(
                                    code=parent_dict.get('code'), defaults={'name': parent_dict.get('name', '')}
                                )
                                ContractorRelationModel.objects.create(
                                    contractor=contractor_buffer,
                                    contractor_parent=parent,
                                    relation_type_id='structural_division'
                                )
                                if parent_created:
                                    ContractorMemberModel.objects.create(
                                        contractor=parent, name=parent_dict.get('name', ''),
                                        inn=parent_dict.get('bin', '')
                                    )
                                    contractor_buffer = parent
                                    parent_dict = parent_dict.get('parent')
                                else:
                                    break
                        ContractorProfileModel.objects.get_or_create(contractor=contractor, user=user.profile,
                                                                     defaults={'director': False})
                    ehub_servers = user.profile.ehub_user_servers.all()
                    profile = user.profile
                    from common.models import File
                    from django.core.files import File as DjangoFile
                    from io import BytesIO
                    for each in ehub_servers:
                        server = each.server
                        resp = requests.get(f'{server.internal_url}/e-hub/user/avatar/?username={user.username}')
                        if not resp.status_code == 200:
                            continue
                        stream = BytesIO(resp.content)
                        filename = resp.headers.get('Content-Disposition').split(';')[-1].strip(' filename=').strip('"')
                        django_file = DjangoFile(file=stream, name=filename)
                        avatar_file = File()
                        avatar_file.upload = django_file
                        avatar_file.author = profile
                        avatar_file.save()
                        profile.avatar = avatar_file
                        profile.save(update_fields=('avatar',))
                        break

        else:
            phone = input_val_data.get('phone', '')
            try:
                user = models.CustomUser.objects.get(profile__phone=phone, is_active=True)
            except models.CustomUser.DoesNotExist:
                authenticate(request, username=phone, password=input_val_data.get('password'))
                return Response(data={"status": "Логин или пароль не верны"},
                                status=status.HTTP_403_FORBIDDEN)
        user_previous_login = user.last_login
        auth_user = authenticate(request, username=user.username,
                                 password=input_val_data.get('password'))
        if auth_user and auth_user.profile.temporary_blocked:
            return Response(data={"status": "Пользователь заблокирован"},
                            status=status.HTTP_403_FORBIDDEN)
        if auth_user:
            serialized_data = utils.login_user(request, user_previous_login, auth_user)
            return Response(data=serialized_data, status=status.HTTP_200_OK)
        else:
            if not user.last_login:
                ehub_servers = user.profile.ehub_servers.filter(is_active=True)
                for each in ehub_servers:
                    resp = requests.post(
                        url=each.check_password_url,
                        json={
                            "username": user.email,
                            "password": input_val_data.get('password')
                        }
                    )
                    if resp.status_code == 200:
                        user.set_password(input_val_data.get('password'))
                        user.save()
                        serialized_data = utils.login_user(request, user_previous_login, user)
                        return Response(data=serialized_data, status=status.HTTP_200_OK)
            return Response(data={"status": "Логин или пароль не верны"},
                            status=status.HTTP_403_FORBIDDEN)

    @action(methods=['get', ], detail=False, url_path='jwt-token', url_name='jwt-token', permission_classes=())
    def get_jwt_token(self, request, *args, **kwargs):
        """Получить информацию о текущем пользователе"""
        user = request.user
        if user.is_authenticated:
            refresh = RefreshToken.for_user(user)
            data = dict()
            data['jwt_access'] = str(refresh.access_token)
            data['jwt_refresh'] = str(refresh)
            return Response(data)
        else:
            return Response({"status": 401})

    def retrieve(self, request, *args, **kwargs):
        profile_id = kwargs.get('pk')
        qs = utils.filter_users_by_organizations(
            ProfileModel.objects.all(),
            request.user.profile
        )
        try:
            user = qs.get(pk=profile_id)
        except ProfileModel.DoesNotExist:
            raise drf_exceptions.NotFound()
        data = serializers.AppUserDetailSerializer(user).data
        return Response(data)

    @action(methods=['get', ], detail=False, url_path='info', url_name='info', permission_classes=())
    def get_info(self, request, *args, **kwargs):
        """Получить информацию о текущем пользователе"""
        user = request.user
        try:
            profile = user.profile
        except AttributeError:
            return Response(None)

        if user.is_authenticated:
            cache.set('CachedAppUserSerializer_' + str(profile.pk), None)
            cache.set('CachedAppUserPreviewSerializer_' + str(profile.pk), None)
            cache.delete(f'tariff_section_codes_{profile.pk}')
            data = {'user': self.get_serializer_class()(profile).data,
                    'status': 200}
            # data['user']['me_logistic_manager_only'] = True
            data['user']['phone'] = profile.phone  # чтоб сериализатор не ломать
            data['user']['is_staff'] = user.is_staff
            data['user']['entry_complete'] = utils.get_entry_complete(profile)
            if user.profile.temporary_blocked:
                logout(request)
                return Response(data={"status": "Пользователь заблокирован"},
                                status=status.HTTP_403_FORBIDDEN)
            permission_type_ids = ('help_desk_admin', 'help_desk_manager')
            helpdesk_contractor_ids = contractors_where_user_has_permission(profile.pk, permission_type_ids, None)
            data['user']['is_helpdesk_support'] = bool(helpdesk_contractor_ids)

            withsecret = (request.query_params.get("withsecret", "") or "").lower() == "true"
            if withsecret:
                # генерим одноразовый секрет (короткоживущий)
                secret_val = secrets.token_urlsafe(32)

                DesktopWebViewSecret.objects.create(
                    user=user,
                    secret=secret_val,
                )
                data["secret"] = secret_val

            response = Response(data)
            if withsecret:
                response.delete_cookie("sessionid", )
                response.delete_cookie("csrftoken", )
            return response
        else:
            return Response({"status": 401})

    @action(methods=['get', ], detail=False, url_path='logout', permission_classes=(),
            authentication_classes=())
    def logout(self, request, *args, **kwargs):
        """Выход из приложения"""
        logout(request)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, url_path='change_password', permission_classes=(IsAuthenticated,))
    def change_password(self, request, *args, **kwargs):
        """Смена пароля"""
        serializer = serializers.ChangePasswordSerializer(data=request.data,
                                                          context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
            models.MobileTokenModel.objects.filter(user=request.user).delete()
            return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='set_new_password', permission_classes=(IsAuthenticated,))
    def set_new_password(self, request, *args, **kwargs):
        """Смена пароля для пользовталей с автоматически сгенрированным паролем"""

        serializer = serializers.SetNewPasswordSerializer(data=request.data,
                                                          context={"request": request})
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                serializer.save()
                event = SetNewPassword()
                event.create_notification(recipients=(request.user.profile,))
            login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
            models.MobileTokenModel.objects.filter(user=request.user).delete()
            return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='skip_set_new_password', permission_classes=(IsAuthenticated,))
    def skip_set_new_password(self, request, *args, **kwargs):
        """Пропуск процедуры смены автоматической смеын пароля"""
        user = request.user
        user.password_generated = False
        user.save()

        return Response(status=status.HTTP_200_OK)

    @action(methods=('put', 'patch'), detail=False, url_path='update_profile', permission_classes=(IsAuthenticated,), )
    def update_profile(self, request, *args, **kwargs):
        instance = request.user
        serializer = serializers.CustomUserUpdateSerializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        profile = instance.profile
        ehub_data = {
            'username': instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'middle_name': instance.middle_name,
            'job_title': profile.job_title,
            'phone': profile.contact_phone,
            'birthday': profile.birthday.isoformat() if profile.birthday else None,
        }
        for each in profile.ehub_user_servers.all():
            r = requests.post(f"{each.server.user_url}update/", json=ehub_data)
        s_data = serializers.CustomUserDetailSerializer(instance=instance.profile).data
        return Response(s_data)

    @action(methods=('patch',), detail=False, url_path='chat_ai_tooltip', permission_classes=(IsAuthenticated,))
    def update_chat_ai_tooltip(self, request, *args, **kwargs):
        profile = request.user.profile
        serializer = serializers.ChatAiTooltipUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        current_chat_ai_tooltip = profile.chat_ai_tooltip if isinstance(profile.chat_ai_tooltip, dict) else {}
        for key, value in serializer.validated_data.items():
            current_chat_ai_tooltip[key] = value

        profile.chat_ai_tooltip = current_chat_ai_tooltip
        profile.save(update_fields=('chat_ai_tooltip',))

        return Response(serializers.CustomUserDetailSerializer(profile).data, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, url_path='change_avatar', permission_classes=(IsAuthenticated,))
    def set_avatar(self, request, *args, **kwargs):
        """Смена автарки"""
        serializer = serializers.SetAvatarSerializer(data=request.data, instance=request.user.profile)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        for each in profile.ehub_user_servers.all():
            resp = requests.post(
                url=f"{each.server.user_url}set_avatar/",
                data={
                    "username": profile.user.username,
                    "filename": profile.avatar.full_name,
                },
                files={'avatar': profile.avatar.upload},
            )
        return Response(status=status.HTTP_200_OK)

    @action(methods=('post',), detail=False, url_path='set_header_image', permission_classes=(IsAuthenticated,))
    def set_header_image(self, request, *args, **kwargs):
        """Смена картинки в шапке профиля"""
        serializer = serializers.SetHeaderImageSerializer(data=request.data, instance=request.user.profile)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, url_path='connect_telegram_url', permission_classes=(IsAuthenticated,))
    def get_connect_telegram_url(self, request, *args, **kwargs):
        """Получить ссылку для подключения к телеграму"""
        user = request.user
        profile = user.profile
        url = F'https://www.telegram.me/{TG_BOT_NAME}?start={profile.telegram_connect_token}'
        return Response(data={"url": url}, status=status.HTTP_200_OK)

    @action(methods=['post', ''], detail=False, url_path='forgot_password', permission_classes=())
    def forgot_password(self, request, *args, **kwargs):
        serializer = serializers.ForgetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'message': 'ok'
            },
            status=status.HTTP_200_OK
        )

    @action(methods=("post",), detail=False, url_path='reset/confirm', permission_classes=(), authentication_classes=())
    def confirm_reset_password(self, request, *args, **kwargs):
        data = request.data
        phone = data.get('phone', '')
        confirm_code = data.get('confirm_code', '')
        validation_error = drf_exceptions.ValidationError({"message": "Код активации недействителен."})
        if not utils.check_sms_forgot_password(phone, confirm_code):
            raise validation_error
        try:
            user = models.CustomUser.objects.get(
                profile__phone=phone,
                is_active=True,
                profile__is_active=True,
                profile__temporary_blocked=False
            )
        except models.CustomUser.DoesNotExist:
            raise validation_error
        reset_password = models.ResetPasswordModel.objects.filter(
            is_active=True,
            user=user,
            changed=False
        ).order_by('-created_at').first()
        if not reset_password:
            raise validation_error
        token = reset_password.uuid
        data = {"uuid": token}
        return Response(data)

    @action(methods=["post", ], detail=False, url_path="create_from_1c", url_name="create_from_1c",
            permission_classes=(),
            authentication_classes=())
    def create_from_1c(self, request, *args, **kwargs):
        """Создать дилера и связку с пользователями"""
        raise drf_exceptions.NotFound() #  # 17.04.2025

        data = request.data
        print(data)
        if data['t'] != TOKEN_URV:
            return Response(data={'status': 'no'}, status=status.HTTP_418_IM_A_TEAPOT)

        docs = data['data']

        for doc in docs:

            dealer, is_new = ContractorModel.objects.get_or_create(id=doc['dealer_id'])
            dealer.id = doc['dealer_id']
            dealer.name = doc['dealer_name']
            dealer.is_carrier = doc.get('dealer_carrier', False)
            dealer.phone = doc.get('dealer_phone', '')
            dealer.save()

            dealer_member_list = doc.get('dealer_member_list', [])
            for dealer_member_dict in dealer_member_list:
                dealer_member, new_dm = ContractorMemberModel.objects.get_or_create(id=dealer_member_dict['id'],
                                                                                    defaults={"contractor": dealer,
                                                                                              "name":
                                                                                                  dealer_member_dict[
                                                                                                      'name']})
                dealer_member.name = dealer_member_dict.get('name', '')
                dealer_member.contractor = dealer
                dealer_member.save()

            for user in doc['users']:
                is_new_profile = not ProfileModel.objects.filter(id=user['user_id']).exists()
                director = user.get('director', False)
                is_auctioneer = user.get('is_auctioneer', False)
                if is_new_profile:
                    us = models.CustomUser()
                    us.username = user['email'].lower()
                    us.email = user['email'].lower()
                    us.first_name = user['i']
                    us.last_name = user['f']
                    us.is_loading = True
                    try:
                        us.save()
                    except IntegrityError:
                        us = models.CustomUser.objects.get(username=user['email'])
                        if us.profile:
                            raise drf_exceptions.ValidationError(
                                f"Пользователь {user['email']} уже существует и имеет профиль."
                            )
                    profile, created = ProfileModel.objects.get_or_create(id=user['user_id'], defaults={"user": us})
                    profile.name = user['username']
                    profile.phone = user['telephone']
                    profile.company = user['user_org']  # Компания
                    profile.job_title = user['user_position']  # Должность
                    profile.is_auctioneer = is_auctioneer
                    # profile.default_chat = dealer_chat
                    profile.save()
                    roles = user.get('role', [])
                    profile.c1_roles.clear()
                    for item in roles:
                        role, is_new = C1RoleModel.objects.get_or_create(id=item['id'], defaults={'name': item['name']})
                        profile.c1_roles.add(role)
                    # integration_1c_utils.set_random_password_and_send_email(us)
                    async_task(integration_1c_utils.set_random_password_and_send_email, us)

                else:
                    profile = ProfileModel.objects.get(id=user['user_id'])
                    profile.user.email = user['email']
                    profile.phone = user['telephone']
                    profile.user.first_name = user['i']
                    # profile.default_chat = dealer_chat
                    profile.user.last_name = user['f']
                    profile.name = user['username']
                    profile.company = user['user_org']  # Компания
                    profile.job_title = user['user_position']  # Должность
                    profile.is_auctioneer = is_auctioneer
                    profile.user.save()
                    profile.save()
                    roles = user.get('role', [])
                    profile.c1_roles.clear()
                    for item in roles:
                        role, is_new = C1RoleModel.objects.get_or_create(id=item['id'], defaults={'name': item['name']})
                        profile.c1_roles.add(role)

                dealer_profile, created = dealer.profiles.through.objects.get_or_create(user=profile, contractor=dealer,
                                                                                        defaults={"director": director})
                # member, member_created = MemberModel.objects.get_or_create(chat=dealer_chat, user_id=profile.id)
                if not created:
                    m2m_model_obj = dealer.profiles.through.objects.get(contractor=dealer, user=profile)
                    m2m_model_obj.director = director
                    m2m_model_obj.save()

        return Response(data={'status': 'ok'}, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=False, url_path="check", url_name="check",
            permission_classes=())
    def get_check(self, request, *args, **kwargs):
        return Response(request.user.is_authenticated)

    @action(methods=["get", ], detail=False, url_path="viewers/(?P<pk>[^/.]+)", url_name="viewers",
            permission_classes=())
    def object_viewers(self, request, pk=None, *args, **kwargs):

        related_object = VoteView.get_rated_object(self, request)
        relations = related_object.object_viewer_relations.all().order_by('created_at')
        data = AppObjectViewerSerializer(relations, many=True).data

        return Response(data)

    # Организации
    def get_my_organization(self):
        try:
            instance = ContractorModel.objects.get(pk=self.kwargs.get('pk'))
        except ContractorModel.DoesNotExist:
            raise drf_exceptions.NotFound()
        return instance

    @action(methods=("get",), detail=False, url_path="my_organizations", permission_classes=(IsAuthenticated,))
    def get_my_organizations(self, request, *args, **kwargs):
        user = request.user.profile
        organizations = set()
        my_organizations = user.my_organizations
        parent_id = request.query_params.get('parent')
        if parent_id:
            children_id_list = ContractorRelationModel.objects.filter(
                contractor_parent_id=parent_id,
                relation_type_id='structural_division',
            ).values_list('contractor', flat=True)
            qs = ContractorModel.objects.filter(is_active=True, pk__in=children_id_list).order_by('name', 'created_at')
        else:
            # Если в фильтрах есть поиск, то выбираем все организации:
            search_param = request.query_params.get('search', )
            has_search = common_utils.has_active_search_query(request, ContractorModel)
            if has_search:
                organizations = utils.get_tree_departments_related_organizations(my_organizations)
            # Иначе смотрим на гет-параметр display:
            if not organizations:
                display = request.query_params.get('display', 'my_organizations_only')
                if display == 'descendants':
                    organizations = utils.get_descendants_departments_related_organizations(my_organizations)
                elif display == 'descendants_director':
                    organizations = utils.get_descendants_departments_related_organizations(
                        set(user.contractor_profile.filter(is_active=True, director=True).values_list('contractor',
                                                                                                      flat=True)))
                elif display == 'tree':
                    organizations = utils.get_tree_departments_related_organizations(my_organizations)
                elif display == 'root':
                    organizations = utils.get_roots_departments_related_organizations(my_organizations)
                else:
                    organizations = my_organizations
            # task_qs = TaskModel.objects.filter(
            #     organization_id=OuterRef('pk'),
            #     is_active=True,
            #     task_type_id='task',
            #     status__task_status_type__is_complete=False).annotate(
            #     count=Func(F('pk'), function='Count', )
            # ).values('count')
            qs = ContractorModel.objects.filter(is_active=True, pk__in=organizations).annotate(
                # annotate_task_count=Subquery(task_qs),
                annotate_members_count=Count(
                    'profiles',
                    filter=Q(profiles__is_active=True, profiles__temporary_blocked=False),
                    distinct=True
                ),
                annotate_structural_division_count=Count(
                    'contractor_relations_parent',
                    filter=Q(contractor_relations_parent__relation_type_id='structural_division'),
                    distinct=True
                ),
                annotate_department_count=Count(
                    'departments',
                    filter=Q(departments__is_active=True),
                    distinct=True
                ),
                # annotate_project_count=Count(
                #     'workgroups',
                #     filter=Q(
                #         workgroups__is_project=True,
                #         workgroups__is_active=True,
                #         workgroups__is_finished=False,
                #     ),
                #     distinct=True
                # ),
                is_my=Case(
                    When(
                        pk__in=my_organizations,
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            ).prefetch_related(
                Prefetch(
                    'contractor_profile',
                    queryset=ContractorProfileModel.objects.filter(director=True).select_related(
                        'user__user',
                        'user__avatar'
                    ),
                    to_attr='contractor_director'
                ),
                'contractor_members',
            ).order_by('name', 'created_at')
            exclude_root = request.query_params.get('exclude_root')
            if exclude_root:
                try:
                    exclude_tree = utils.get_descendants_departments_related_organizations((exclude_root,))
                except ValidationError:
                    pass
                else:
                    qs = qs.exclude(pk__in=exclude_tree)
            qs = get_filter_queryset(request, ContractorModel, qs)
            if search_param and len(search_param) >= 3:
                search_result = get_search_result(ContractorModel, search_param)
                if len(search_result) > 0:
                    search_result_ids = [item['id'] for item in search_result]
                    qs = qs.filter(pk__in=list(search_result_ids))
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        data = serializers.AppOrganizationSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

    @action(methods=("get",), detail=False, url_path="my_organizations_short", permission_classes=(IsAuthenticated,))
    def get_my_organizations_short(self, request, *args, **kwargs):
        """Короткая версия эндпойнта my_organizations. Использует короткий кэширующий сериализатор.
        Для списка организаций в драйвере выбора пользователя."""
        user = request.user.profile
        organizations = set()
        my_organizations = user.my_organizations

        display = request.query_params.get('display', 'my_organizations_only')
        if display == 'descendants':
            organizations = utils.get_descendants_departments_related_organizations(my_organizations)
        elif display == 'descendants_director':
            organizations = utils.get_descendants_departments_related_organizations(
                set(user.contractor_profile.filter(is_active=True, director=True).values_list('contractor', flat=True)))
        elif display == 'tree':
            organizations = utils.get_tree_departments_related_organizations(my_organizations)
        elif display == 'root':
            organizations = utils.get_roots_departments_related_organizations(my_organizations)
        else:
            organizations = my_organizations

        qs = ContractorModel.objects.filter(
            is_active=True,
            pk__in=organizations
        ).annotate(
            annotate_structural_division_count=Count(
                'contractor_relations_parent',
                filter=Q(contractor_relations_parent__relation_type_id='structural_division'),
                distinct=True
            )
        ).order_by('name', 'created_at')
        qs = get_filter_queryset(request, ContractorModel, qs)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        page_ids = [obj.pk for obj in page]
        data = CachedBaseModelSerializer(page_ids, many=True, serializer_class=ContractorModelShortSerializer).data
        counts_map = {str(obj.id): obj.annotate_structural_division_count for obj in page}
        return_data = [{**d, 'structural_division_count': counts_map.get(d['id'])} for d in data]
        return paginator.get_paginated_response(return_data)

    @action(methods=('get',), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/detail",
            permission_classes=(IsAuthenticated,))
    def get_my_organizations_detail(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_detail_organization_permission(instance.pk, user)
        s_data = serializers.MyOrganizationDetailSerializer(instance).data
        return Response(s_data)

    @action(methods=('get',), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/relations",
            permission_classes=(IsAuthenticated,))
    def get_related_organizations(self, request, *args, **kwargs):
        user = request.user.profile
        instance = self.get_my_organization()
        utils.check_detail_organization_permission(instance.pk, user)
        qs = ContractorRelationModel.objects.filter(
            is_active=True,
            contractor_parent=instance
        ).order_by('contractor__name')
        query_params = request.query_params
        if 'filters' in list(query_params.keys()):
            try:
                filters_dict = json.loads(query_params.get('filters'))
            except json.JSONDecodeError:
                pass
            else:
                qs = filter_queryset_from_get_param(filters_dict, qs)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        data = ContractorRelationModelListSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

    @action(methods=('GET',), detail=False, url_path='my_organizations/(?P<pk>[^/.]+)/contractors',
            permission_classes=(IsAuthenticated,), )
    def get_contractors(self, request, *args, **kwargs):
        """Возвращает список связанных организаций. Типы связи - все кроме structural_division."""
        user = request.user.profile
        instance = self.get_my_organization()
        utils.check_detail_organization_permission(instance.pk, user)
        qs = ContractorRelationModel.objects.filter(
            Q(contractor_parent=instance) | Q(contractor=instance),
            contractor__is_active=True,
            contractor_parent__is_active=True,
            is_active=True,
        ).exclude(
            relation_type_id='structural_division'
        ).annotate(
            annotate_name=Case(
                When(
                    contractor_id=instance.pk,
                    then=F('contractor_parent__name')
                ),
                default=F('contractor__name'),
                output_field=CharField(),
            )
        ).order_by('annotate_name')
        query_params = request.query_params
        if 'filters' in list(query_params.keys()):
            try:
                filters_dict = json.loads(query_params.get('filters'))
            except json.JSONDecodeError:
                pass
            else:
                qs = filter_queryset_from_get_param(filters_dict, qs)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        data = MyContractorsListSerializer(page, many=True,
                                           context={"request": request, "instance_id": instance.pk}).data
        return paginator.get_paginated_response(data)

    @action(methods=("PUT",), detail=False, url_path="my_organizations/relations/(?P<rel_id>[^/.]+)/update",
            permission_classes=(IsAuthenticated,))
    def update_relation(self, request, *args, **kwargs):
        try:
            instance = ContractorRelationModel.objects.get(pk=kwargs.get('rel_id'))
        except ContractorRelationModel.DoesNotExist:
            raise drf_exceptions.NotFound()
        user = request.user.profile
        contractor = instance.contractor
        utils.check_update_organization_permission(contractor.pk, user)
        serializer = serializers.ContractorRelationUpdateSerializer(
            data=request.data, context={"request": request, "contractor": contractor}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        contractor_parent = validated_data.get('contractor_parent')
        if not contractor_parent:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            utils.check_update_organization_permission(contractor_parent.pk, user)
        serializer.save()
        data = ContractorRelationModelListSerializer(instance=instance).data
        return Response(data)

    @action(methods=("post",), detail=False, url_path="my_organizations/create", permission_classes=(IsAuthenticated,))
    def create_my_organizations(self, request, *args, **kwargs):
        serializer = serializers.MyOrganizationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        contractor_parent = serializer.validated_data.get('contractor_parent')
        if contractor_parent:
            user = request.user.profile
            utils.check_update_organization_permission(contractor_parent.pk, user)
        instance = serializer.save()
        get_relation = bool(request.data.get('get_relation', False))
        if get_relation:
            s_data = ContractorRelationModelListSerializer(serializer.context.get('relation', None)).data
        else:
            s_data = serializers.MyOrganizationDetailSerializer(instance).data
        return Response(s_data)

    @action(methods=("post",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/delete",
            permission_classes=(IsAuthenticated,))
    def delete_my_organizations(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        utils.check_update_organization_permission(instance.pk, request.user.profile)
        instance.is_active = False
        with transaction.atomic():
            instance.save(update_fields=('is_active',))
            contractor_relations = ContractorRelationModel.objects.filter(
                Q(contractor=instance) | Q(contractor_parent=instance)
            )
            for each in contractor_relations:
                each.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=("put", "patch",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/update",
            permission_classes=(IsAuthenticated,))
    def update_my_organizations(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        utils.check_update_organization_permission(instance.pk, request.user.profile)
        serializer = serializers.MyOrganizationUpdateSerializer(
            instance=instance,
            data=request.data,
            context={"request": request},
            partial=request.method == 'PATCH',
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        s_data = serializers.AppOrganizationSerializer(instance).data
        return Response(s_data)

    @action(methods=("post",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/logo",
            permission_classes=(IsAuthenticated,))
    def update_organization_logo(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_update_organization_permission(instance.pk, user)
        serializer = serializers.MyOrganizationUpdateLogoSerializer(
            instance=instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        s_data = serializers.AppOrganizationSerializer(instance).data
        return Response(s_data)

    @action(methods=("get",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/action_info",
            permission_classes=(IsAuthenticated,))
    def get_my_organizations_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_my_organization()
        user = request.user.profile
        try:
            utils.check_update_organization_permission(instance.pk, user)
        except drf_exceptions.PermissionDenied:
            return Response({"actions": actions})
        else:
            actions['edit'] = {"availability": True}
            actions['invite'] = {"availability": True}
            actions['manage'] = {"availability": True}
        try:
            check_contractor_permission(user.pk, instance.pk, 'create_workgroup', None)
        except drf_exceptions.PermissionDenied:
            pass
        else:
            actions['create_project'] = {"availability": True}
        try:
            check_contractor_permission(user.pk, instance.pk, ('help_desk_admin', 'help_desk_manager',), None)
        except drf_exceptions.PermissionDenied:
            pass
        else:
            actions['set_default_ticket_visor'] = {'availability': True}
        return Response({"actions": actions})

    def get_task_qs(self, instance: ContractorModel):
        from bpms.tasks.models import TaskModel
        display = self.request.query_params.get('display', 'node')
        if display == 'children':
            organizations = set(ContractorRelationModel.objects.filter(
                contractor_parent=instance,
                relation_type_id='structural_division',
            ).values_list('contractor', flat=True))
        elif display == 'node_children':
            organizations = set(ContractorRelationModel.objects.filter(
                contractor_parent=instance,
                relation_type_id='structural_division',
            ).values_list('contractor', flat=True))
            organizations.add(instance.pk)
        else:
            organizations = {instance.pk, }
        qs = TaskModel.objects.filter(is_active=True, organization_id__in=organizations)
        return qs

    @action(methods=("get",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/task_count",
            permission_classes=(IsAuthenticated,))
    def get_my_organizations_task_count(self, request, *args, **kwargs):
        from bpms.tasks.models import TaskStatusTypeModel
        instance = self.get_my_organization()
        qs = self.get_task_qs(instance)
        qs = get_tasks_status_count(qs)
        return Response(qs)

    @action(methods=("get",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/tasks",
            permission_classes=(IsAuthenticated,))
    def get_my_organizations_tasks(self, request, *args, **kwargs):
        from django.db.models import IntegerField, Min
        from bpms.tasks.utils import get_task_queryset, order_tasks_queryset_from_get_param
        from bpms.tasks.serializers import ListTaskSerializer
        from bpms.tasks.models import TaskModel
        instance = self.get_my_organization()
        qs = order_tasks_queryset_from_get_param(
            self.request, get_task_queryset(self.request, self.get_task_qs(instance)),
        )
        qs = qs.annotate(
            completed_children_count=Count(
                'children',
                filter=Q(
                    children__is_active=True,
                    children__status__code__in=(
                        'completed',
                        'successfully'
                    )
                ),
                distinct=True
            ),
            comments_count=Count(
                'comments',
                filter=Q(
                    comments__is_active=True
                ),
                distinct=True
            ),
            attachments_count=Count(
                'files',
                filter=Q(
                    files__is_active=True
                ),
                distinct=True
            ),
            has_description=Case(
                When(
                    description__gt='',
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        )
        qs_pk = qs.values_list('id', flat=True)
        paginator = CustomPagination()
        qs_pk = paginator.paginate_queryset(qs_pk, request)
        qs = TaskModel.objects.all().filter(pk__in=qs_pk)
        qs = qs.select_related(
            #   'counter',
            'parent',
            'workgroup',
            'workgroup__workgroup_logo',
            'workgroup__workgroup_logo__mime_type',
            'workgroup__workgroup_logo__mime_type__file_type',
            'project',
            'project__workgroup_logo',
            'project__workgroup_logo__mime_type',
            'project__workgroup_logo__mime_type__file_type',
            'contractor',
            'contractor__contact_person',
            'potential_contractor',
            'status',
            'rejection_reason',
            'lead_source',
        ).prefetch_related(
            'prerequisites',
            'attachments',
            'children',
            'task_delivery_points',
            'event_calendars',
            'event_calendars__events',
        )
        qs = qs.annotate(
            completed_children_count=Count(
                'children',
                filter=Q(
                    children__is_active=True,
                    children__status__code__in=(
                        'completed',
                        'successfully'
                    )
                ),
                distinct=True
            ),
            comments_count=Count(
                'comments',
                filter=Q(
                    comments__is_active=True
                ),
                distinct=True
            ),
            attachments_count=Count(
                'files',
                filter=Q(
                    files__is_active=True
                ),
                distinct=True
            ),
            has_description=Case(
                When(
                    description__gt='',
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        )
        qs = qs.annotate(annotate_is_finished=Case(
            When(status_id='completed',
                 then=Value(1)),
            default=Value(0),
            output_field=IntegerField()),

            annotate_order_exists=Case(
                When(
                    task_delivery_points=None,
                    then=Value(0)
                ),
                default=Value(1),
                output_field=IntegerField()
            ),
            annotate_order_date_start_plan=Min("task_delivery_points__start_goods_orders__delivery_date_plan_gte"),
        )
        qs = qs.order_by(*(qs.query.order_by))
        serializer = ListTaskSerializer(qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=("post",), detail=False, url_path="my_organizations/action_info")
    def get_my_organizations_bulk_action_info(self, request, *args, **kwargs):
        organizations_id = request.data
        if not isinstance(organizations_id, list):
            raise drf_exceptions.ValidationError()
        result = dict()
        user = request.user.profile
        create_workgroup_orgs = [
            str(_) for _ in contractors_where_user_has_permission(user.pk, 'create_workgroup', None)
        ]
        set_default_ticket_visors = [
            str(_) for _ in contractors_where_user_has_permission(
                user.pk, ('help_desk_admin', 'help_desk_manager',), None
            )
        ]
        for each in organizations_id:
            try:
                utils.check_update_organization_permission(each, user)
            except drf_exceptions.PermissionDenied:
                actions = dict()
            else:
                actions = {
                    "edit": {"availability": True},
                    "invite": {"availability": True},
                    "manage": {"availability": True}
                }
            if each in create_workgroup_orgs:
                actions['create_project'] = {"availability": True}
            if each in set_default_ticket_visors:
                actions['set_default_ticket_visor'] = {'availability': True}
            result[each] = actions
        return Response(result)

    @action(methods=("get", "post"), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/invite",
            permission_classes=(IsAuthenticated,))
    def get_post_invite_link(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_update_organization_permission(instance.pk, user)
        if request.method == 'POST':
            serializer = serializers.InviteModelCreateSerializer(
                data=request.data, context={"request": request, "contractor": instance}
            )
            serializer.is_valid(raise_exception=True)
            invite = serializer.save()
        else:
            invite, created = models.InviteModel.objects.get_or_create(
                is_active=True,
                contractor=instance,
                workgroup__isnull=True,
                is_create_new_contractor=False,
            )
        return Response(
            {
                "invite": utils.get_invite_url(invite.token),
                "deactivate_at": invite.deactivate_at,
            }
        )

    @action(methods=("get", "post",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/email_invite",
            permission_classes=(IsAuthenticated,))
    def send_invite_to_email(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_update_organization_permission(instance.pk, user)
        if request.method == 'POST':
            data = request.data
            if not isinstance(data, list):
                raise drf_exceptions.ValidationError()
            for each in data:
                with transaction.atomic():
                    if 'group' in each:
                        each['workgroup'] = each['group']
                    serializer = serializers.EmailInviteModelCreateSerializer(
                        data=each,
                        context={"request": request, "contractor": instance},
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
            return Response("ok")
        else:
            qs = models.EmailInviteModel.objects.filter(contractor=instance, is_active=True).order_by('-created_at')
            paginator = CustomPagination()
            page = paginator.paginate_queryset(qs, request, self)
            data = serializers.EmailInviteListSerializer(page, many=True, context={"request": request}).data
            return paginator.get_paginated_response(data)

    @action(methods=("get",), detail=False, url_path="my_organizations/invite/check")
    def check_invite(self, request, *args, **kwargs):
        token = request.query_params.get('token')
        try:
            utils.check_invite_token(token)
        except drf_exceptions.ValidationError:
            return Response(False)
        return Response(True)

    @action(methods=("get",), detail=False, url_path="my_organizations/invite/info",
            permission_classes=())
    def get_invite_info(self, request, *args, **kwargs):
        token = request.query_params.get('token')
        skip_membership_check = request.query_params.get('skip_membership_check', 'false').lower() == 'true'
        utils.check_invite_token(token)

        # Приглашения хэлпдеска
        contractor = utils.get_organization_from_invite_token(token)
        if not contractor:
            contact_person = utils.get_contact_person_from_invite_token(token)
            if not contact_person:
                raise drf_exceptions.ValidationError("Приглашение недействительно.")
            customer_card = contact_person.customer_card
            contractor = customer_card.org_admin
            invite = models.InviteModel()
            invite.token = token
            invite.contractor = contractor
            invite.id = ''
            invite.created_at = None
            invite.author = None
            return_data = serializers.InviteInfoSerializer(invite).data
            customer = customer_card.customer
            if customer:
                customer_name = customer.name
            else:
                customer_name = customer_card.name
            return_data['customer_name'] = customer_name
            return Response(return_data)

        # для неавторизованных или если передан skip_membership_check=true сразу отдаем информацию о приглашении
        invite = utils.get_invite_instance_from_token(token)
        user = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
        if not user or skip_membership_check:
            return Response(serializers.InviteInfoSerializer(invite).data)

        # Проверяем, что пользователь еще не является участником организации/рабочей группы
        if invite.is_create_new_contractor:
            if invite.workgroup:
                from bpms.workgroups.models import WorkgroupMembersModel, WorkgroupMembershipStatus
                from bpms.workgroups.models import WorkgroupMembershipStatus
                if WorkgroupMembersModel.objects.filter(
                        member=user,
                        work_group=invite.workgroup,
                        is_active=True,
                        membership_request_status=WorkgroupMembershipStatus.objects.get(code="APPROVED")
                ).exists():
                    if invite.workgroup.is_project:
                        error_message = _("Вы уже являетесь участником этого проекта")
                    else:
                        error_message = _("Вы уже являетесь участником этой команды")
                    raise drf_exceptions.ValidationError(error_message)
            else:
                # таких инвайтов быть не должно
                raise drf_exceptions.ValidationError(
                    "Ссылка не предполагает вступление в организацию или рабочую группу")

        else:
            contractor_profile = contractor.contractor_profile.filter(is_active=True, user=user).exists()
            if invite.workgroup:
                from bpms.workgroups.models import WorkgroupMembersModel, WorkgroupMembershipStatus
                from bpms.workgroups.models import WorkgroupMembershipStatus
                workgroup_member = WorkgroupMembersModel.objects.filter(
                    member=user,
                    work_group=invite.workgroup,
                    is_active=True,
                    membership_request_status=WorkgroupMembershipStatus.objects.get(code="APPROVED")
                ).exists()
                if contractor_profile and workgroup_member:
                    # Определяем тип сообщения в зависимости от is_project
                    if invite.workgroup.is_project:
                        error_message = _("Вы уже являетесь участником этой организации и проекта")
                    else:
                        error_message = _("Вы уже являетесь участником этой организации и команды")
                    raise drf_exceptions.ValidationError(error_message)
            else:
                if contractor_profile:
                    raise drf_exceptions.ValidationError({"message": "Вы уже являетесь участником этой организации"})
        data = serializers.InviteInfoSerializer(invite).data
        return Response(data)

    @action(methods=("post",), detail=False, url_path="my_organizations/join_by_invite",
            permission_classes=(IsAuthenticated,))
    def join_by_invite(self, request, *args, **kwargs):
        token = request.data.get('token')
        user = request.user.profile
        utils.join_by_invite(token, user)
        return Response('ok')

    @action(methods=("post",), detail=False, url_path="my_organizations/get_contractor_by_invite_token",
            permission_classes=())
    def get_contractor_by_invite_token(self, request, *args, **kwargs):
        token = request.data.get('token')
        utils.check_invite_token(token)
        contractor = utils.get_organization_from_invite_token(token)
        if contractor:
            is_create_new_contractor = utils.get_is_create_new_contractor_from_token(token)
            serialized_data = serializers.TokenContractorSerializer(contractor).data
            serialized_data['is_create_new_contractor'] = is_create_new_contractor
        else:
            contact_person = utils.get_contact_person_from_invite_token(token)
            if not contact_person:
                raise drf_exceptions.ValidationError({"message": "Токен недействителен."})
            customer_card = contact_person.customer_card
            serialized_data = {
                "id": "",
                "name": customer_card.name,
                "full_name": customer_card.full_name
            }
        return Response(serialized_data)

    @action(methods=("get",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/users",
            permission_classes=(IsAuthenticated,))
    def get_my_organizations_users(self, request, *args, **kwargs):
        user = request.user.profile
        instance = self.get_my_organization()
        utils.check_detail_organization_permission(instance.pk, user)
        qs = instance.contractor_profile.filter(
            user__is_active=True, user__temporary_blocked=False
        )
        app_section_code = request.query_params.get('app_section')
        if app_section_code:
            from contractor_permissions.utils import users_that_have_app_section_role_in_contractors
            app_section_users = users_that_have_app_section_role_in_contractors((instance.pk,), app_section_code, )
            qs = qs.filter(user_id__in=app_section_users)
        # Исключаем сотрудников отдела. Нужно для выбора новых сотрудников для отдела.
        exclude_department_id = request.query_params.get('exclude_department')
        if exclude_department_id:
            try:
                exclude_department = ContractorDepartmentModel.objects.get(
                    is_active=True,
                    contractor=instance,
                    pk=exclude_department_id
                )
            except ContractorDepartmentModel.DoesNotExist:
                pass
            else:
                exclude_department_users = exclude_department.contractor_profiles.filter(
                    is_active=True,
                ).values_list('user', flat=True)
                qs = qs.exclude(user__in=exclude_department_users)

        text = request.query_params.get('text')
        search = request.query_params.get('search')
        if search:
            text = search
        if text:
            search_queryset = RelatedSearchQuerySet().filter(
                content=text,
                profile_id__in=qs.values_list('user_id', flat=True),
            ).models(ProfileModel).load_all()
            qs = qs.filter(user_id__in=search_queryset.values_list('profile_id', flat=True))
        if 'exclude_director' in request.query_params:
            qs = qs.exclude(user_id=instance.director.pk)
        qs = qs.order_by("user__user__last_name", "user__user__first_name", "user__user__middle_name")
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        admins = users_that_have_permission_in_contractors((instance.pk,), 'admin', None)
        data = serializers.MyOrganizationUserSerializer(
            page, many=True, context={"request": request, 'admins': admins, 'contractor': instance}).data
        return paginator.get_paginated_response(data)

    @action(methods=("get",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/users_short",
            permission_classes=(IsAuthenticated,))
    def get_my_organizations_users_short(self, request, *args, **kwargs):
        """Список сотрудников организации. Вывод с помощью общего сериализатора AppUserSerializer."""
        user = request.user.profile
        instance = self.get_my_organization()
        utils.check_detail_organization_permission(instance.pk, user)

        query_params = request.query_params
        display = query_params.get('display', 'my_organizations_only')

        if display == 'descendants':
            organizations = utils.get_descendants_departments_related_organizations({instance.pk})
            qs = ProfileModel.objects.filter(
                contractors__in=organizations,
                is_active=True,
                temporary_blocked=False
            ).distinct()
        elif display == 'tree':
            organizations = utils.get_tree_departments_related_organizations((instance.pk,))
            qs = ProfileModel.objects.filter(
                contractors__in=organizations,
                is_active=True,
                temporary_blocked=False
            )
        else:
            qs = instance.profiles.filter(
                is_active=True, temporary_blocked=False
            )

        if 'filters' in list(query_params.keys()):
            try:
                filters_dict = json.loads(query_params.get('filters'))
            except json.JSONDecodeError:
                pass
            else:
                qs = filter_queryset_from_get_param(filters_dict, qs)
        search = query_params.get('search')
        if search and len(search) >= 2:
            search_queryset = RelatedSearchQuerySet().filter(
                content=search,
            ).models(ProfileModel)
            qs = qs.filter(pk__in=search_queryset.values_list('profile_id', flat=True))
        qs = qs.order_by("user__last_name", "user__first_name", "user__middle_name").values_list('pk', flat=True)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        page_ids = list(page)
        data = serializers.CachedAppUserPreviewSerializer(page_ids, many=True).data
        return paginator.get_paginated_response(data)

    @action(methods=("post",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/users/create",
            permission_classes=(IsAuthenticated,))
    def create_my_organization_user(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_update_organization_permission(instance.pk, user)
        create_user_id = request.data.get('user')
        if not create_user_id:
            raise drf_exceptions.ValidationError()
        try:
            create_user = ProfileModel.objects.get(pk=create_user_id, is_active=True, temporary_blocked=False)
        except ProfileModel.DoesNotExist:
            raise drf_exceptions.ValidationError({"message": "Пользователь не найден"})
        created_user, created = ContractorProfileModel.objects.get_or_create(user=create_user, contractor=instance)
        s_data = AppUserSerializer(instance=create_user).data
        s_data['created'] = created
        cache_key = f'tariff_section_codes_{str(create_user_id)}'
        cache.delete(cache_key)
        return Response(s_data)

    @action(methods=("post",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/users/delete",
            permission_classes=(IsAuthenticated,))
    def delete_my_organization_user(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_update_organization_permission(instance.pk, user)
        delete_user_id = request.data.get('id')
        if delete_user_id == user.pk:
            raise drf_exceptions.ValidationError({"message": "Вы не можете покинуть организацию."})
        try:
            contractor_profile = instance.contractor_profile.get(user_id=delete_user_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError({"message": "Пользователь не состоит в организации."})
        contractor_profile.delete()
        async_task(notifications.notify_about_delete_member, delete_user_id, instance)
        cache_key = f'tariff_section_codes_{str(delete_user_id)}'
        cache.delete(cache_key)
        return Response()

    @action(methods=("post",), detail=False, url_path="my_organizations/(?P<pk>[^/.]+)/leave")
    def leave_my_organization(self, request, *args, **kwargs):
        user = request.user.profile
        instance = self.get_my_organization()
        try:
            contractor_profile = ContractorProfileModel.objects.get(is_active=True, user=user, contractor=instance)
        except ContractorProfileModel.DoesNotExist:
            raise drf_exceptions.ValidationError({"message": "Вы не состоите в организации."})
        if contractor_profile.director:
            raise drf_exceptions.ValidationError({"message": "Вы не можете покинуть организацию."})
        contractor_profile.delete()
        async_task(notifications.notify_about_leave_member, user, instance)
        cache_key = f'tariff_section_codes_{str(user.pk)}'
        cache.delete(cache_key)
        return Response("ok")

    # Отделы
    def get_department(self):
        try:
            department = ContractorDepartmentModel.objects.get(is_active=True, pk=self.kwargs.get('pk'))
        except ContractorDepartmentModel.DoesNotExist:
            raise drf_exceptions.NotFound()
        return department

    @action(methods=('get',), detail=False, url_path='my_organizations/(?P<pk>[^/.]+)/departments',
            permission_classes=(IsAuthenticated,))
    def get_departments(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_detail_organization_permission(instance.pk, user)
        qs = instance.departments.filter(is_active=True).annotate(
            annotate_members_count=Count('contractor_profiles', distinct=True)
        ).order_by('name')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = ContractorDepartmentListSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(s_data)

    @action(methods=('get',), detail=False, url_path='my_organizations/(?P<pk>[^/.]+)/departments_select_list',
            permission_classes=(IsAuthenticated,))
    def get_departments_select_list(self, request, *args, **kwargs):
        """Список отделов с коротким сериализатором. Для выпадающих списков выбора отдела."""
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_detail_organization_permission(instance.pk, user)
        qs = instance.departments.filter(is_active=True).order_by('name')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        s_data = ContractorDepartmentShortListSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(s_data)

    @action(methods=('get',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/detail',
            permission_classes=(IsAuthenticated,))
    def get_departments_detail(self, request, *args, **kwargs):
        department = self.get_department()
        contractor = department.contractor
        user = request.user.profile
        utils.check_detail_organization_permission(contractor.pk, user)
        return Response(ContractorDepartmentDetailSerializer(instance=department).data)

    @action(methods=('post',), detail=False, url_path='my_organizations/(?P<pk>[^/.]+)/departments/create')
    def create_department(self, request, *args, **kwargs):
        instance = self.get_my_organization()
        user = request.user.profile
        utils.check_update_organization_permission(instance.pk, user)
        serializer = ContractorDepartmentCreateSerializer(
            data=request.data, context={"request": request, "contractor": instance}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=('post',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/delete')
    def delete_department(self, request, *args, **kwargs):
        department = self.get_department()
        contractor = department.contractor
        user = request.user.profile
        utils.check_update_organization_permission(contractor.pk, user)
        department.is_active = False
        department.save(update_fields=('is_active',))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('put', 'patch',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/update')
    def update_department(self, request, *args, **kwargs):
        department = self.get_department()
        user = request.user.profile
        organization = department.contractor
        if not organization:
            raise drf_exceptions.NotFound()
        utils.check_update_organization_permission(organization.pk, user)
        serializer = ContractorDepartmentUpdateSerializer(
            instance=department,
            data=request.data,
            context={'request': request},
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        contractor = serializer.validated_data.get('contractor')
        if contractor:
            utils.check_update_organization_permission(contractor.pk, user)
        serializer.save()
        return Response(serializer.data)

    @action(methods=('get',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/users')
    def get_department_users(self, request, *args, **kwargs):
        department = self.get_department()
        contractor = department.contractor
        user = request.user.profile
        utils.check_detail_organization_permission(contractor.pk, user)
        department_profiles = department.contractor_profiles.filter(
            is_active=True,
        ).values_list('user', flat=True)
        qs = ProfileModel.objects.filter(
            pk__in=department_profiles,
            is_active=True,
            temporary_blocked=False,
        )
        text = request.query_params.get('text', '')
        if text:
            search_queryset = RelatedSearchQuerySet().filter(
                content=text,
                profile_id__in=qs.values_list('id', flat=True),
            ).models(ProfileModel).load_all()
            qs = qs.filter(pk__in=search_queryset.values_list('profile_id', flat=True))
        qs = qs.order_by("user__last_name", "user__first_name", "user__middle_name")
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        data = serializers.AppUserSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)

    @action(methods=('post',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/users/create',
            permission_classes=(IsAuthenticated,))
    def create_department_user(self, request, *args, **kwargs):
        department = self.get_department()
        contractor = department.contractor
        user = request.user.profile
        utils.check_update_organization_permission(contractor.pk, user)
        create_user_id = request.data.get('id')
        with transaction.atomic():
            contractor_profile, contractor_created = contractor.contractor_profile.get_or_create(user_id=create_user_id)
            department_profile, department_created = department.department_profiles.get_or_create(
                contractor_profile=contractor_profile
            )
        created_department_user = contractor_profile.user
        s_data = AppUserSerializer(created_department_user).data
        s_data['created'] = department_created
        return Response(s_data)

    @action(methods=('post',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/users/delete',
            permission_classes=(IsAuthenticated,))
    def delete_department_user(self, request, *args, **kwargs):
        department = self.get_department()
        contractor = department.contractor
        user = request.user.profile
        utils.check_update_organization_permission(contractor.pk, user)
        delete_user_id = request.data.get('id')
        try:
            contractor_profile = contractor.contractor_profile.get(user_id=delete_user_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError({'message': 'Пользователь не найден'})
        try:
            department_profile = department.department_profiles.get(contractor_profile=contractor_profile)
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError({'message': 'Пользователь не найден'})
        department_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('post',), detail=False, url_path='my_organizations/departments/(?P<pk>[^/.]+)/users/leave',
            permission_classes=(IsAuthenticated,))
    def leave_department_user(self, request, *args, **kwargs):
        user = request.user.profile
        department = self.get_department()
        try:
            department_profile = department.department_profiles.get(contractor_profile__user_id=user.pk)
        except ObjectDoesNotExist:
            raise drf_exceptions.NotFound({'message': 'Пользователь не найден.'})
        department_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('get',), detail=False, url_path='get_support_chat')
    def get_support_chat(self, request, *args, **kwargs):
        """Получить UID чата техподдержки для указанного пользователя"""
        profile_id = request.query_params.get('profile')
        if not profile_id:
            raise drf_exceptions.ValidationError({"message": "Не указан ID профиля пользователя"})

        try:
            profile = ProfileModel.objects.get(pk=profile_id, is_active=True)
        except ProfileModel.DoesNotExist:
            raise drf_exceptions.NotFound({"message": "Пользователь не найден"})

        support_chat_id = profile.support_chat
        return Response({"support_chat": support_chat_id})

    @action(methods=('get',), detail=False, url_path='activities')
    def get_activities(self, request, *args, **kwargs):
        from bpms.personal_planes import utils as planes_utils
        from bpms.event_calendar import utils as calendar_utils
        qs = ProfileModel.objects.filter(is_active=True)
        qs = common_utils.get_filter_queryset(request, ProfileModel, qs)
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        planes_access_users_id = set()
        calendar_access_users_id = set()
        # try:
        start_date = datetime.datetime.strptime(start[:10], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end[:10], "%Y-%m-%d")
        # except (ValueError, TypeError):
        #     qs = qs.none()
        # else:
        delta = end_date - start_date
        if delta.days > 6 or delta.days < 0:
            qs = qs.none()
        else:
            org_id = request.query_params.get('organization')
            if org_id:
                try:
                    qs = qs.filter(contractors=org_id)
                except ValidationError:
                    raise drf_exceptions.ValidationError('Invalid organization id')
            planes_access_users_id = planes_utils.get_access_users(request)
            calendar_access_users_id = calendar_utils.get_access_users(request)
            access_users_id = planes_access_users_id | calendar_access_users_id
            qs = qs.filter(pk__in=access_users_id)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        serializer = serializers.UserActivitiesSerializer(
            page,
            many=True,
            context={
                'request': request,
                'view': self,
                'plans_users': planes_access_users_id,
                'events_users': calendar_access_users_id
            }
        )
        data = serializer.data
        return paginator.get_paginated_response(data)


class CurrentContractorViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(methods=('get',), detail=False, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        user = request.user.profile
        instance = user.get_or_set_current_contractor()
        if not instance:
            return Response(dict())
        try:
            utils.check_update_organization_permission(instance.pk, user)
        except drf_exceptions.PermissionDenied:
            return Response({"actions": actions})
        actions['edit'] = {"availability": True}
        actions['invite'] = {"availability": True}
        actions['manage'] = {"availability": True}
        return Response({"actions": actions})

    @action(methods=('get',), detail=False, url_path=r'detail', )
    def get_detail(self, request, *args, **kwargs):
        user = request.user.profile
        current_contractor = user.get_or_set_current_contractor()
        if current_contractor:
            s_data = serializers.MyOrganizationDetailSerializer(current_contractor).data
        else:
            s_data = dict()
        return Response(s_data)

    @action(methods=('post',), detail=False, url_path=r'change')
    def change(self, request, *args, **kwargs):
        user = request.user.profile
        current_contractor_id = request.data.get('id')
        try:
            current_contractor = ContractorModel.objects.filter(
                pk__in=user.my_organizations, is_active=True
            ).get(pk=current_contractor_id)
        except (ContractorModel.DoesNotExist, ValidationError):
            raise drf_exceptions.ValidationError({"message": "Организация не найдена."})
        user.current_contractor = current_contractor
        user.save(update_fields=('current_contractor',))
        return Response()

    @action(methods=('get',), detail=False, url_path='list', )
    def get_list(self, request, *args, **kwargs):
        user = request.user.profile
        current_contractor = user.get_or_set_current_contractor()
        if current_contractor:
            qs = ContractorModel.objects.filter(is_active=True, pk__in=user.my_organizations).annotate(
                my_contractor_order=Case(
                    When(
                        pk=current_contractor.pk,
                        then=Value(0)
                    ),
                    default=Value(1),
                    output_field=PositiveIntegerField()
                )
            ).order_by('my_contractor_order', 'name', 'created_at', )
        else:
            qs = ContractorModel.objects.filter(is_active=True, pk__in=user.my_organizations).order_by(
                'name', 'created_at',
            )
        from common.catalogs.serializers import ContractorModelByIdSerializer
        s_data = ContractorModelByIdSerializer(qs, many=True).data
        for each in s_data:
            if ContractorProfileModel.objects.filter(user=user, contractor_id=each.get('id'), director=True).exists():
                each['is_director'] = True
            else:
                each['is_director'] = False
        return Response(s_data)

    @action(methods=('get',), detail=False, url_path='tree', )
    def get_tree(self, request, *args, **kwargs):
        user = request.user.profile
        current_contractor = user.get_or_set_current_contractor()
        empty_data = {'root': None, 'parents': []}
        if current_contractor:
            ancestors = utils.get_ancestor_departments_related_organizations(
                (current_contractor.pk,),
                include_self=True,
                return_type='list',
            )
            ancestors.reverse()
            root_id = ancestors[0]
            try:
                root = ContractorModel.objects.get(pk=root_id, is_active=True)
            except ContractorModel.DoesNotExist:
                return Response(empty_data)
            root_data = serializers.AppOrganizationSerializer(root, context={'request': request}).data
            data = {'root': root_data, 'parents': ancestors}
        else:
            data = empty_data
        return Response(data)

    @action(methods=('get',), detail=False, url_path='contractors', )
    def get_contractors(self, request, *args, **kwargs):
        user = request.user.profile
        instance = user.get_or_set_current_contractor()
        if not instance:
            return Response([])
        qs = ContractorRelationModel.objects.filter(
            Q(contractor_parent=instance) | Q(contractor=instance),
            contractor__is_active=True,
            contractor_parent__is_active=True,
            is_active=True,
        ).exclude(
            relation_type_id='structural_division'
        ).annotate(
            annotate_name=Case(
                When(
                    contractor_id=instance.pk,
                    then=F('contractor_parent__name')
                ),
                default=F('contractor__name'),
                output_field=CharField(),
            )
        ).order_by('annotate_name')
        query_params = request.query_params
        if 'filters' in list(query_params.keys()):
            try:
                filters_dict = json.loads(query_params.get('filters'))
            except json.JSONDecodeError:
                pass
            else:
                qs = filter_queryset_from_get_param(filters_dict, qs)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        data = MyContractorsListSerializer(page, many=True,
                                           context={"request": request, "instance_id": instance.pk}).data
        return paginator.get_paginated_response(data)

    @action(methods=('get',), detail=False, url_path='users', )
    def get_users(self, request, *args, **kwargs):
        user = request.user.profile
        current_contractor = user.get_or_set_current_contractor()
        paginator = CustomPagination()
        if current_contractor:
            qs = current_contractor.profiles.filter(
                is_active=True, temporary_blocked=False
            )
            if 'exclude_director' in request.query_params:
                qs = qs.exclude(pk=current_contractor.director.pk)
            qs = qs.order_by("user__last_name", "user__first_name", "user__middle_name")
            page = paginator.paginate_queryset(qs, request, self)
            admins = users_that_have_permission_in_contractors((current_contractor.pk,), 'admin', None)
            data = serializers.MyOrganizationUserSerializer(
                page, many=True, context={"request": request, 'admins': admins, 'contractor': current_contractor}).data
        else:
            data = []
        return paginator.get_paginated_response(data)

    @action(methods=('post',), detail=False, url_path='users/delete')
    def delete_user(self, request, *args, **kwargs):
        user = request.user.profile
        instance = user.get_or_set_current_contractor()
        if not instance:
            raise drf_exceptions.NotFound()
        utils.check_update_organization_permission(instance.pk, user)
        delete_user_id = request.data.get('id')
        if delete_user_id == user.pk:
            raise drf_exceptions.ValidationError({"message": "Вы не можете покинуть организацию."})
        try:
            contractor_profile = instance.contractor_profile.get(user_id=delete_user_id)
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError({"message": "Пользователь не состоит в организации."})
        contractor_profile.delete()
        async_task(notifications.notify_about_delete_member, delete_user_id, instance)
        return Response()


class ResetPasswordView(generics.RetrieveUpdateAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializers.ResetPasswordSerializer
    queryset = models.ResetPasswordModel.objects.filter(changed=False,
                                                        is_active=True)

    def get_object(self):
        reset = self.queryset.filter(uuid=self.kwargs.get('reset_uid')).order_by('created_at')
        if reset.exists():
            return reset.last()
        return reset.none()


class CustomUserAutocompleteSearchView(HaystackGenericApiView):
    index_models = (models.ProfileModel,)
    # serializer_class = serializers.CustomUserSearchSerializer
    serializer_class = serializers.AppUserSerializer
    pagination_class = CustomPagination
    pagination_class.max_page_size = 10000
    queryset = models.ProfileModel.objects.filter(is_active=True, temporary_blocked=False)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        full_name = request.query_params.get('fullname')
        exclude_workgroup = request.query_params.get('exclude_workgroup')
        exclude_users = request.query_params.get('exclude_users')
        search_bool = get_search_bool()
        if not full_name:
            search_queryset = SearchQuerySet().none()
        else:
            search_queryset = SearchQuerySet().autocomplete(
                full_name_auto=full_name
            ).models(models.ProfileModel, ).filter(is_active=search_bool)
        results = [r.pk for r in search_queryset]
        queryset = models.ProfileModel.get_queryset(request)
        queryset = queryset.select_related('avatar', ).filter(id__in=results)
        if exclude_workgroup:
            workgroup = WorkgroupModel.objects.get(id=exclude_workgroup)
            exclude_workgroup_member_list = workgroup.workgroupmembersmodel_set.filter(is_active=True).values_list(
                'member', flat=True)
            queryset = queryset.exclude(id__in=exclude_workgroup_member_list)
        if exclude_users:
            exclude_users_list = exclude_users.split(',')
            if exclude_users_list:
                queryset = queryset.exclude(pk__in=exclude_users_list)
        page = self.paginate_queryset(queryset)
        s_data = self.serializer_class(page, many=True, context={'request': request}).data
        return self.get_paginated_response(s_data)


class UserListView(generics.ListAPIView):
    serializer_class = AppUserSerializer
    pagination_class = paginators.CustomPagination
    queryset = ProfileModel.objects.filter(is_active=True, temporary_blocked=False)
    permission_classes = (IsAuthenticated,)

    def get_union_queryset(self):
        """ Порежем выборку
        0. сначала выбранные в селекте
        1. потом не выбранные в селекте
        Иначе - стандартная схема
        """
        selected_string = self.request.query_params.get('selected')
        only_my_param = self.request.query_params.get('only_my')
        only_my = None
        if only_my_param is not None:
            only_my = only_my_param.lower() == 'true'

        queryset = ProfileModel.objects.filter(is_active=True, temporary_blocked=False,
                                               user__isnull=False)
        if selected_string == '':
            selected_string = None
        user = self.request.user.profile
        if selected_string:
            selected_array = selected_string.split(',')
            qs1 = ProfileModel.objects.filter(is_active=True, temporary_blocked=False,
                                              user__isnull=False,
                                              pk__in=selected_array).annotate(priority=Value(0)).select_related('user')
            qs2 = ProfileModel.objects.filter(is_active=True,
                                              user__isnull=False).exclude(pk__in=qs1).annotate(
                priority=Value(1)).select_related('user')
            qs2 = utils.filter_users_by_organizations(qs2, user, only_my=only_my)
            qs2 = common_utils.get_filter_queryset(self.request, ProfileModel, qs2)
            queryset = qs1.union(qs2)
            queryset = queryset.order_by('priority', 'user__last_name', 'user__first_name', 'user__middle_name')
        else:
            queryset = get_filter_queryset(
                self.request,
                ProfileModel,
                utils.filter_users_by_organizations(queryset, user, only_my=only_my)
            )
            if len(queryset.query.order_by) == 0 and not common_utils.has_active_search_query(self.request,
                                                                                              ProfileModel):
                queryset = queryset.order_by('user__last_name', 'user__first_name', 'user__middle_name')
        return queryset

    def get_queryset(self):
        search = self.request.query_params.get('search')
        if isinstance(search, str):
            queryset = ProfileModel.get_filtered_select_queryset(search)
        else:
            queryset = self.get_union_queryset()
        return queryset


class UserListByTaskView(generics.ListAPIView):
    serializer_class = AppUserSerializer
    pagination_class = paginators.CustomPagination
    queryset = ProfileModel.objects.filter(
        is_active=True,
        temporary_blocked=False
    )
    permission_classes = (IsAuthenticated,)
    tasks_in_work = True

    def get_queryset(self):
        from bpms.tasks.models import TaskModel
        queryset = self.queryset
        user = self.request.user.profile
        queryset = utils.filter_users_by_organizations(queryset, user)
        queryset = get_filter_queryset(self.request, models.ProfileModel, queryset)

        task_id = self.request.query_params.get('task', None)
        if task_id:
            task = TaskModel.objects.get(id=task_id)
            if not task.owner == user and task.contractor:
                contractor_profiles_list = list(task.contractor.profiles.all().values_list('id', flat=True))
                contractor_profiles_list.append(task.owner.pk)
                queryset = queryset.filter(id__in=contractor_profiles_list)

        search = self.request.query_params.get('search')

        if isinstance(search, str):
            return models.ProfileModel.get_filtered_select_queryset(search)

        if len(queryset.query.order_by) == 0:
            queryset = queryset.order_by('user__last_name', 'user__first_name', 'user__middle_name')
        return queryset


class GetMyDefaultChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        profile = get_current_authenticated_profile()
        return Response(ChatListSerializer(profile.default_chat, context={"request": request}).data,
                        status=status.HTTP_200_OK)


def lockout(request, credentials, *args, **kwargs):
    response = Response(data={"status": "Слишком много попыток входа, попробуйте через 15 минут"}, status=403)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    response.render()
    return response


class GoogleOAuthViewSet(ViewSet):

    @action(detail=False, methods=['post'], permission_classes=(IsAuthenticated,))
    def authorization(self, request, pk=None):
        if not request.data:
            return Response(data={'error': 'cancelled_by_user'}, status=status.HTTP_200_OK)
        auth_code = request.data.get('code')
        google_oauth_client = GoogleOAuthClientIDsModel.objects.filter(
            name=GoogleOAuthClientIDsModel.WEB_CLIENT).first()
        if not google_oauth_client:
            return Response(data={'error': 'no_oauth_client_in_database'}, status=status.HTTP_200_OK)
        client_info = json.loads(google_oauth_client.client_info)
        client_id = client_info["web"]["client_id"]
        client_secret = client_info["web"]["client_secret"]
        request_data = {'code': auth_code,
                        'client_id': client_id,
                        'client_secret': client_secret,
                        # Для локальной разработки в redirect_uri нужно указать localhost, например:
                        # 'redirect_uri': 'http://localhost:8085'
                        'redirect_uri': FRONTEND_URL,
                        'grant_type': 'authorization_code'}
        r = requests.post('https://oauth2.googleapis.com/token', data=request_data)
        token_data = json.loads(r.text)
        g_token = GoogleTokenModel.objects.filter(profile=request.user.profile,
                                                  oauth_client=google_oauth_client).first()
        data = GoogleTokenModel.prepare_token_data_for_saving(token_data)
        if g_token:
            g_token.update_token_data(data)
        else:
            GoogleTokenModel.objects.create(profile=request.user.profile,
                                            oauth_client=google_oauth_client,
                                            **data
                                            )
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,))
    def client_info(self, request, pk=None):
        google_oauth_client = GoogleOAuthClientIDsModel.objects.filter(
            name=GoogleOAuthClientIDsModel.WEB_CLIENT).first()
        if google_oauth_client:
            client_info = json.loads(google_oauth_client.client_info)
            return Response(data=client_info, status=status.HTTP_200_OK)
        else:
            return Response(data={}, status=status.HTTP_200_OK)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """Оставить заявку"""
    throttle_classes = [AnonRateThrottle, ]
    permission_classes = (permissions.LeaveRequestPermission,)
    queryset = models.LeaveRequestModel.objects.all().order_by('-created_at')
    serializer_class = serializers.LeaveRequestSerializer
    pagination_class = CustomPagination
    http_method_names = ['get', 'post']  # Разрешаем только GET и POST

    def get_authenticators(self):
        """Разрешаем как анонимный, так и аутентифицированный доступ"""
        # Всегда возвращаем стандартные аутентификаторы
        return super().get_authenticators()


class NewUserInfoViewSet(common_views.BaseModelViewSet):
    model = models.NewUserInfoModel

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return serializers.NewUserInfoUpdateSerializer
        return serializers.NewUserInfoListSerializer

    def list(self, request, *args, **kwargs):
        if not request.user.profile.is_support:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.profile.is_support:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not request.user.profile.is_support:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# =========================
# Helpers
# =========================

def _connect_base_url():
    # положи в settings.py:
    # CONNECT_WEB_URL = "https://connect.gos24.kz"
    return getattr(settings, "BACKEND_URL", "https://connect.gos24.kz")


def _desktop_scheme():
    # положи в settings.py:
    # GOS24CONNECT_URI_SCHEME = "gos24connect"
    return getattr(settings, "GOS24CONNECT_URI_SCHEME", "gos24connect")


def _auth_backend_path():
    backends = getattr(settings, "AUTHENTICATION_BACKENDS", None)
    # if backends and len(backends) > 0:
    #     return backends[1]
    return "django.contrib.auth.backends.ModelBackend"


# =========================
# Views
# =========================

class DesktopAuthStartView(APIView):
    """
    Desktop app -> открывает дефолтный браузер:
    GET /api/v1/users/desktop/auth/start/?state=<uuid>

    Мы редиректим на страницу фронта (connect), где будет кнопка/скрипт,
    который вызовет /complete.
    """
    permission_classes = [AllowAny]

    def get(self, request):

        state_raw = request.query_params.get("state")

        if not state_raw:
            return Response({"detail": "state is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_authenticated:
            return HttpResponseRedirect(
                f"https://auth.connect.gos24.kz/sign-in?redirect_url={FRONTEND_URL}/api/v1/users/desktop/auth/start/?state={state_raw}")
        try:
            state = uuid.UUID(str(state_raw))
        except Exception:
            return Response({"detail": "invalid state"}, status=status.HTTP_400_BAD_REQUEST)

        # Страница фронта, например:
        # https://connect.gos24.kz/desktop-auth?state=...
        url = "{0}/api/v1/users/desktop/auth/complete/?state={1}".format(_connect_base_url(), state)
        return HttpResponseRedirect(url)


import json
from django.http import HttpResponse


class DesktopAuthCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        state_raw = request.query_params.get("state")
        if not state_raw:
            return Response({"detail": "state is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            state = uuid.UUID(str(state_raw))
        except Exception:
            return Response({"detail": "invalid state"}, status=status.HTTP_400_BAD_REQUEST)

        obj = DesktopAuthCode.create_for_user(request.user, state, ttl_minutes=2)

        redirect_url = "{0}://callback?state={1}&code={2}".format(
            _desktop_scheme(), obj.state, obj.code
        )

        html = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Connect Gos24</title>

  <!-- meta-refresh оставим, но НЕ 0, чтобы не триггерить блокировки "мгновенного автоперехода" -->
  <meta http-equiv="refresh" content="2;url={url}">

  <style>
    :root {{
      --bg1:#f0f2f5;
      --card:#ffffff;
      --text:#141414;
      --muted:#8c8c8c;
      --border:#f0f0f0;
      --shadow:0 6px 20px rgba(0,0,0,.08);
      --radius:12px;
      --primary:#1677ff;
    }}

    html, body {{
      height: 100%;
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Arial, sans-serif;
      background:
        radial-gradient(1200px 600px at 20% 10%, rgba(22,119,255,.15), transparent 60%),
        radial-gradient(900px 500px at 90% 30%, rgba(82,196,26,.12), transparent 55%),
        var(--bg1);
      color: var(--text);
    }}

    .wrap {{
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}

    .card {{
      width: min(520px, 92vw);
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
      cursor: pointer; /* клик по карточке = user gesture */
    }}

    .top {{
      padding: 22px 22px 10px;
      text-align: center;
    }}

    .logo {{
      width: 220px;
      max-width: 70%;
      height: auto;
      display: inline-block;
      opacity: .95;
      pointer-events: none;
    }}

    .content {{
      padding: 8px 22px 22px;
      text-align: center;
      cursor: default;
    }}

    .title {{
      margin: 10px 0 6px;
      font-size: 18px;
      font-weight: 600;
      letter-spacing: .2px;
    }}

    .desc {{
      margin: 0 auto 16px;
      max-width: 420px;
      color: var(--muted);
      line-height: 1.45;
      font-size: 14px;
    }}

    .status {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #fafafa;
      user-select: none;
    }}

    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--primary);
      box-shadow: 0 0 0 6px rgba(22,119,255,.12);
      animation: pulse 1.2s infinite ease-in-out;
    }}

    @keyframes pulse {{
      0%   {{ transform: scale(1);   opacity: 1; }}
      50%  {{ transform: scale(1.15);opacity: .75; }}
      100% {{ transform: scale(1);   opacity: 1; }}
    }}

    .counter {{
      font-size: 14px;
      color: var(--text);
      font-weight: 500;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-top: 14px;
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px solid rgba(22,119,255,.25);
      background: rgba(22,119,255,.08);
      color: var(--primary);
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      user-select: none;
    }}
    .btn:hover {{
      background: rgba(22,119,255,.12);
    }}

    .hint {{
      margin-top: 12px;
      font-size: 12px;
      color: var(--muted);
    }}

    .footer {{
      border-top: 1px solid var(--border);
      padding: 12px 16px;
      text-align: center;
      color: var(--muted);
      font-size: 12px;
      background: #fcfcfc;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card" id="card" role="dialog" aria-label="Connect Gos24">
      <div class="top">
        <img class="logo" alt="Connect Gos24" src="https://connect.gos24.kz/img/default.64bb231f.svg">
      </div>

      <div class="content" onclick="event.stopPropagation()">
        <div class="title">Открываю приложение…</div>
        <p class="desc">
          Если приложение установлено, оно откроется автоматически.
          Если нет — нажмите кнопку ниже (Opera часто требует клик).
        </p>

        <div class="status" aria-live="polite">
          <span class="dot" aria-hidden="true"></span>
          <span class="counter">Окно закроется через <span id="sec">7</span> сек.</span>
        </div>

        <!-- ВАЖНО: ссылка не показывается как "страшная", но она есть (user gesture) -->
        <div>
          <a class="btn" id="openBtn" href="{url}">Открыть Connect Gos24</a>
        </div>

        <div class="hint">
          Можно просто закрыть вкладку, если она не закрылась автоматически.
        </div>
      </div>

      <div class="footer">Connect Gos24</div>
    </div>
  </div>

  <script>
    const deepLink = {url_js};

    function openApp() {{
      // несколько способов - иногда один из них "заводится" лучше
      try {{ window.location.href = deepLink; }} catch (e) {{}}
      try {{ window.location.assign(deepLink); }} catch (e) {{}}
    }}

    // Автопопытка (может быть заблокирована в Opera — тогда спасает кнопка/клик)
    setTimeout(openApp, 150);

    // Кнопка = user gesture
    document.getElementById('openBtn').addEventListener('click', function(e) {{
      e.preventDefault();
      openApp();
    }});

    // Клик по карточке тоже = user gesture
    document.getElementById('card').addEventListener('click', function() {{
      openApp();
    }}, {{ once: true }});

    // Счётчик и "мягкое" закрытие
    (function() {{
      var s = 7;
      var el = document.getElementById('sec');
      function tick() {{
        s -= 1;
        if (el) el.textContent = String(Math.max(0, s));
        if (s <= 0) {{
          try {{ window.close(); }} catch (e) {{}}
        }} else {{
          setTimeout(tick, 1000);
        }}
      }}
      setTimeout(tick, 1000);
    }})();
  </script>
</body>
</html>
""".format(url=redirect_url, url_js=json.dumps(redirect_url))

        return HttpResponse(html, content_type="text/html; charset=utf-8")


def _auth_backend_path():
    backends = getattr(settings, "AUTHENTICATION_BACKENDS", None)
    if backends and len(backends) > 0:
        return backends[0]
    return "django.contrib.auth.backends.ModelBackend"


class DesktopAuthExchangeView(APIView):
    """
    POST /api/v1/users/desktop/auth/exchange/
    body: {"code": "<uuid>"}

    Делает обычный login(request, user), чтобы Django сам создал sessionid cookie.
    Возвращаем куки и в JSON тоже (на всякий случай).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        code_raw = request.data.get("code")
        if not code_raw:
            return Response({"detail": "code is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            code_uuid = uuid.UUID(str(code_raw))
        except Exception:
            return Response({"detail": "invalid code"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = DesktopAuthCode.objects.select_related("user").get(code=code_uuid)
        except DesktopAuthCode.DoesNotExist:
            return Response({"detail": "code not found"}, status=status.HTTP_400_BAD_REQUEST)

        if not obj.is_valid():
            return Response({"detail": "code expired/used"}, status=status.HTTP_400_BAD_REQUEST)

        user = obj.user

        # ✅ Обычный login (важно указать backend, иначе иногда падает)
        login(request, user, backend=_auth_backend_path())

        # ✅ Обновим csrf после логина
        csrftoken_val = csrf.get_token(request)

        # ✅ помечаем code использованным
        obj.used_at = timezone.now()
        obj.save(update_fields=["used_at"])

        # sessionid уже лежит в request.session.session_key
        sessionid = getattr(getattr(request, "session", None), "session_key", None)

        resp = Response(
            {
                "ok": True,
                "sessionid": sessionid,
                "csrftoken": csrftoken_val,
                "user_id": user.pk,
            },
            status=200,
        )

        resp.set_cookie("sessionid", sessionid, httponly=True, secure=True, samesite="Lax")
        resp.set_cookie("csrftoken", csrftoken_val, httponly=False, secure=True, samesite="Lax")
        return resp


from django.contrib.sessions.models import Session

CONNECT_HOME = "https://connect.gos24.kz/"


class DesktopAuthWebViewBootstrap(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        secret = (request.query_params.get("secret") or "").strip()
        if not secret:
            return Response({"detail": "secret is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = DesktopWebViewSecret.objects.select_related("user").get(secret=secret)
        except DesktopWebViewSecret.DoesNotExist:
            return Response({"detail": "invalid secret"}, status=status.HTTP_400_BAD_REQUEST)

        if not obj.is_valid(ttl_seconds=10):

            # на всякий случай пометим использованным/просроченным
            if obj.used_at is None:
                obj.used_at = timezone.now()
                obj.save(update_fields=["used_at"])

            return Response({"detail": "secret expired/used"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ инвалидируем сразу
        obj.used_at = timezone.now()
        obj.save(update_fields=["used_at"])
        login(request, obj.user, backend=_auth_backend_path())
        target = CONNECT_HOME
        open_url = (request.query_params.get("open_url") or "").strip()
        if open_url:
            target = open_url
        resp = HttpResponseRedirect(target)
        return resp


class FireBlockingRelationsApiView(APIView):
    """
    Блокирующие отношения при увольнении сотрудника.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        blocking_relations_data = dict()
        query_params = request.query_params
        organization_id = query_params.get('organization')
        try:
            organization = ContractorModel.objects.get(pk=organization_id, is_active=True)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Организация не найдена')
        if not organization.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        profile_id = query_params.get('user')
        user = request.user.profile
        try:
            profile = models.ProfileModel.objects.get(is_active=True, pk=profile_id)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Пользователь не найден')
        try:
            contractor_profile = ContractorProfileModel.objects.get(user=profile, contractor=organization)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Пользователь не является сотрудником организации')

        blocking_relations = utils.get_blocking_relations(contractor_profile)
        # Проверяем на руководителя:
        blocking_relations_data['director'] = blocking_relations['director']

        # Проверяем является ли единственным администратором:
        blocking_relations_data['admin'] = blocking_relations['admin']

        # Руководитель (основатель) проекта:
        from bpms.workgroups.serializers import WorkgroupNameLogoSerializer
        projects_founder_data = WorkgroupNameLogoSerializer(blocking_relations['projects'], many=True).data
        blocking_relations_data['projects'] = projects_founder_data

        # Руководитель (основатель) команды:
        workgroups_founder_data = WorkgroupNameLogoSerializer(blocking_relations['workgroups'], many=True).data
        blocking_relations_data['workgroups'] = workgroups_founder_data

        # Модератор чата проекта:
        from bpms.chat.serializers import ChatListShortSerializer
        chats = blocking_relations['chats']
        blocking_relations_data['chats'] = ChatListShortSerializer(
            chats,
            many=True,
            context={'request': request, 'view': self},
        ).data

        # Постановщик/ответственный задачи:
        from bpms.tasks.serializers import ShortFireTaskSerializer
        tasks = blocking_relations['tasks']
        blocking_relations_data['tasks'] = ShortFireTaskSerializer(tasks, many=True,).data

        # Ответственный в обращениях:
        from help_desk.serializers import HelpDeskTicketFireSerializer
        tickets = blocking_relations['tickets']
        blocking_relations_data['tickets'] = HelpDeskTicketFireSerializer(tickets, many=True).data
        data = {'blocking_relations': blocking_relations_data}
        return Response(data)


class FireNonBlockingRelationsApiView(APIView):
    """
    Неблокирующие отношения при увольнении сотрудника.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        non_blocking_relations_data = dict()
        query_params = request.query_params
        organization_id = query_params.get('organization')
        try:
            organization = ContractorModel.objects.get(pk=organization_id, is_active=True)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Организация не найдена')
        if not organization.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        profile_id = query_params.get('user')
        user = request.user.profile
        try:
            profile = models.ProfileModel.objects.get(is_active=True, pk=profile_id)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Пользователь не найден')
        try:
            contractor_profile = ContractorProfileModel.objects.get(user=profile, contractor=organization)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Пользователь не является сотрудником организации')

        non_blocking_relations = utils.get_non_blocking_relations(contractor_profile)
        # Участник проектов:
        from bpms.workgroups.serializers import WorkgroupNameLogoSerializer
        projects_member_data = WorkgroupNameLogoSerializer(non_blocking_relations['projects'], many=True).data
        non_blocking_relations_data['projects'] = projects_member_data

        # Участник команды:
        workgroups_member_data = WorkgroupNameLogoSerializer(non_blocking_relations['workgroups'], many=True).data
        non_blocking_relations_data['workgroups'] = workgroups_member_data

        # Наблюдатель/соисполнитель задачи:
        from bpms.tasks.serializers import ShortFireTaskSerializer
        tasks = non_blocking_relations['tasks']
        non_blocking_relations_data['tasks'] = ShortFireTaskSerializer(tasks, many=True, ).data

        # Наблюдатель в обращениях:
        from help_desk.serializers import HelpDeskTicketFireSerializer
        tickets = non_blocking_relations['tickets']
        non_blocking_relations_data['tickets'] = HelpDeskTicketFireSerializer(tickets, many=True).data
        data = {'non_blocking_relations': non_blocking_relations_data}
        return Response(data)


class FireAPIView(APIView):
    """
    Увольнение сотрудника.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user.profile
        data = request.data
        organization_id = data.get('organization')
        try:
            organization = ContractorModel.objects.get(pk=organization_id, is_active=True)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Организация не найдена')
        profile_id = data.get('user')
        if not organization.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        from common.catalogs.models import ContractorProfileModel
        try:
            profile = models.ProfileModel.objects.get(is_active=True, pk=profile_id)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Пользователь не найден')
        try:
            contractor_profile = ContractorProfileModel.objects.get(user=profile, contractor=organization)
        except (ValidationError, ObjectDoesNotExist,):
            raise drf_exceptions.ValidationError('Пользователь не является сотрудником организации')

        # Смена блокирующих связей:
        #
        blocking_relations = utils.get_blocking_relations(contractor_profile)
        from bpms.workgroups.models import WorkgroupMembersModel, WorkgroupMembershipRole, WorkgroupMembershipStatus
        from bpms.workgroups.utils import delete_workgroup_chat_members, create_workgroup_chat_members
        from bpms.tasks.models import TaskVisor, TaskCooperator
        from help_desk.models import HelpDeskTicketVisorsModel
        from bpms.chat.utils import delete_chat_members, add_chat_members

        with transaction.atomic():
            # Смена руководителя
            if blocking_relations['director']:
                director_profile_id = data.get('director')
                if not director_profile_id:
                    raise drf_exceptions.ValidationError('Не назначен новый руководитель организации')
                try:
                    director_contractor_profile = ContractorProfileModel.objects.get(
                        contractor=organization,
                        user_id=director_profile_id,
                    )
                except (ValidationError, ObjectDoesNotExist,):
                    raise drf_exceptions.ValidationError('Новый руководитель не является участником организации')
                contractor_profile.director = False
                contractor_profile.save()
                director_contractor_profile.director = True
                director_contractor_profile.save()
            # Смена админа:
            if blocking_relations['admin']:
                new_admin_id = data.get('admin')
                if not new_admin_id:
                    raise drf_exceptions.ValidationError('Не назначен новый администратор организации')
                try:
                    admin_contractor_profile = ContractorProfileModel.objects.get(
                        contractor=organization,
                        user_id=new_admin_id,
                    )
                except (ValidationError, ObjectDoesNotExist,):
                    raise drf_exceptions.ValidationError('Новый администратор не является участником организации')
                from contractor_permissions.models import AccessGroupMemberThroughModel, AccessGroupModel
                from contractor_permissions.notifications import notify_about_add_member
                admin_access_group = AccessGroupModel.objects.get(code='admin')
                AccessGroupMemberThroughModel.objects.create(
                    access_group=admin_access_group,
                    member=admin_contractor_profile,
                )
                transaction.on_commit(
                    partial(
                        notify_about_add_member, str(new_admin_id), str(admin_access_group.pk), str(organization.pk)
                    )
                )
            # Руководитель (основатель) проекта:
            if blocking_relations['projects']:
                founder_projects = data.get('projects')
                if not founder_projects:
                    raise drf_exceptions.ValidationError('Не назначены основатели проекта')
                try:
                    projects_dict = {_['project']: _['founder'] for _ in founder_projects}
                except (TypeError, KeyError):
                    raise drf_exceptions.ValidationError('Некорректный список основателей проекта')
                admin_membership_role = WorkgroupMembershipRole.objects.get(code='FOUNDER')
                membership_status = WorkgroupMembershipStatus.objects.get(code='APPROVED')
                for each in blocking_relations['projects']:
                    new_founder_user_id = projects_dict.get(str(each.pk))
                    if not new_founder_user_id:
                        raise drf_exceptions.ValidationError(f'Не назначен новый осонователь проекта {each.name}.')

                    old_founder = WorkgroupMembersModel.objects.filter(
                        member=profile,
                        work_group=each,
                        membership_role__code='FOUNDER',
                    ).first()
                    if old_founder:
                        old_founder.delete()
                    new_founder_user_id = projects_dict[str(each.pk)]
                    try:
                        new_founder = WorkgroupMembersModel.objects.get(
                            member_id=new_founder_user_id,
                            work_group=each,
                        )
                    except ObjectDoesNotExist:
                        new_founder = WorkgroupMembersModel.objects.create(
                            member_id=new_founder_user_id,
                            work_group=each,
                            membership_request_status=membership_status,
                            membership_role=admin_membership_role,
                            member_visible=True,
                        )
                    else:
                        new_founder.membership_role = admin_membership_role
                        new_founder.membership_request_status=membership_status
                        new_founder.is_active = True
                        new_founder.save()
            # Руководитель (основатель) команды:
            if blocking_relations['workgroups']:
                founder_workgroups = data.get('workgroups')
                if not founder_workgroups:
                    raise drf_exceptions.ValidationError('Не назначены основатели команды')
                try:
                    workgroups_dict = {_['workgroup']: _['founder'] for _ in founder_workgroups}
                except (TypeError, KeyError):
                    raise drf_exceptions.ValidationError('Некорректный список основателей проекта')
                admin_membership_role = WorkgroupMembershipRole.objects.get(code='FOUNDER')
                for each in blocking_relations['workgroups']:
                    new_founder_user_id = workgroups_dict.get(str(each.pk))
                    if not new_founder_user_id:
                        raise drf_exceptions.ValidationError(f'Не назначен новый осонователь команды {each.name}.')
                    old_founder = WorkgroupMembersModel.objects.filter(
                        member=profile,
                        work_group=each,
                        membership_role__code='FOUNDER',
                    ).first()
                    if old_founder:
                        old_founder.delete()
                    new_founder_user_id = workgroups_dict[str(each.pk)]
                    try:
                        new_founder = WorkgroupMembersModel.objects.get(
                            member_id=new_founder_user_id,
                            work_group=each,
                        )
                    except ObjectDoesNotExist:
                        new_founder = WorkgroupMembersModel.objects.create(
                            member_id=new_founder_user_id,
                            work_group=each,
                            membership_request_status=membership_status,
                            membership_role=admin_membership_role,
                            member_visible=True,
                        )
                    else:
                        new_founder.membership_role = admin_membership_role
                        new_founder.membership_request_status = membership_status
                        new_founder.is_active = True
                        new_founder.save()

            # Модератор чата проекта:
            chats = blocking_relations['chats']
            from bpms.chat.models import MemberModel
            if chats:
                chat_list = data.get('chats')
                if not chat_list:
                    raise drf_exceptions.ValidationError('Не указаны модераторы чатов')
                try:
                    chats_dict = {_['chat']: _['user'] for _ in chat_list}
                except (KeyError, TypeError):
                    raise drf_exceptions.ValidationError('Некорректный список модераторов чата')
                for each in chats:
                    new_chat_member_id = chats_dict.get(str(each.pk))
                    if not new_chat_member_id:
                        raise drf_exceptions.ValidationError(f'Не назначен новый модератор чата {each.name}')
                    try:
                        old_chat_member = MemberModel.objects.get(
                            user=profile,
                            chat=each,
                        )
                    except ObjectDoesNotExist:
                        pass
                    else:
                        old_chat_member.delete()
                        transaction.on_commit(partial(delete_chat_members, str(each.chat_uid), (str(profile.pk),)))
                    try:
                        new_chat_member = MemberModel.objects.get(
                            user_id=new_chat_member_id,
                            chat=each
                        )
                    except ObjectDoesNotExist:
                        new_chat_member = MemberModel.objects.create(
                            user_id=new_chat_member_id,
                            chat=each,
                            is_moderator=True
                        )
                        transaction.on_commit(partial(add_chat_members, each.chat_uid, (new_chat_member,)))
                    else:
                        new_chat_member.is_moderator = True
                        new_chat_member.is_active = True
                        new_chat_member.save()

            # Постановщик/ответственный задачи:

            tasks = blocking_relations['tasks']
            if tasks:
                tasks_list = data.get('tasks')
                if not tasks_list:
                    raise drf_exceptions.ValidationError('Не назначены постановщики и ответственные задач')
                tasks_dict = {_['task']: {'owner': _.get('owner'), 'operator': _.get('operator')} for _ in tasks_list}
                for each in tasks:
                    new_task_member = tasks_dict.get(str(each.pk))
                    if not new_task_member:
                        raise drf_exceptions.ValidationError(
                            f'Не назначен постановщик или ответственный в задаче {each.name}'
                        )
                    new_owner_id = new_task_member.get('owner')
                    if new_owner_id:
                        each.owner_id = new_owner_id
                    new_operator_id = new_task_member.get('operator')
                    if new_operator_id:
                        each.operator_id = new_operator_id
                    try:
                        each.save()
                    except (ValidationError, ObjectDoesNotExist, IntegrityError):
                        raise drf_exceptions.ValidationError(f'Некорректные данные для задачи {each.name}')
            # Ответственный в обращениях:
            tickets = blocking_relations['tickets']
            if tickets:
                ticket_list = data.get('tickets')
                if not ticket_list:
                    raise drf_exceptions.ValidationError('Не назначены ответственные в обращениях')
                try:
                    tickets_dict = {_['ticket']: _['specialist'] for _ in ticket_list}
                except (KeyError, TypeError):
                    raise drf_exceptions.ValidationError('Некорректный список ответственных обращения')
                for each in tickets:
                    ticket = tickets_dict.get(str(each.pk))
                    if not ticket:
                        raise drf_exceptions.ValidationError(f"Не назначен ответственный в обращении {ticket.name}")
                    each.specialist = ticket.get('specialist')
                    try:
                        each.save()
                    except (ValidationError, IntegrityError):
                        raise drf_exceptions.ValidationError(f"Некорректный ответственный в обращени {ticket.name}")
            # Удаляем неблокирующие связи:
            non_blocking_relations = utils.get_non_blocking_relations(contractor_profile)
            # Участник проектов:
            projects = non_blocking_relations['projects']
            for each in projects:
                delete_member = WorkgroupMembersModel.objects.filter(
                    work_group=each,
                    member=profile,
                ).first()
                if delete_member:
                    delete_member.delete()
                    transaction.on_commit(partial(delete_workgroup_chat_members, each, (str(profile.pk),)))

            # Участник команды:
            workgroups = non_blocking_relations['workgroups']
            for each in workgroups:
                delete_member = WorkgroupMembersModel.objects.filter(
                    workg_group=each,
                    member=profile,
                ).first()
                if delete_member:
                    delete_member.delete()
            # Наблюдатель/соисполнитель задачи:
            tasks = non_blocking_relations['tasks']
            for each in tasks:
                cooperator = TaskCooperator.objects.filter(task=each, user=profile).first()
                if cooperator:
                    cooperator.delete()
                visor = TaskVisor.objects.filter(task=each, user=profile).first()
                if visor:
                    visor.delete()

            # Наблюдатель в обращениях:
            tickets = non_blocking_relations['tickets']
            for each in tickets:
                delete_visor = HelpDeskTicketVisorsModel.objects.filter(
                    ticket=each,
                    user=profile,
                ).first()
                if delete_visor:
                    delete_visor.delete()

            # Удаляем сотрудника:
            contractor_profile.delete()
        async_task(notifications.notify_about_delete_member, profile_id, organization)
        cache_key = f'tariff_section_codes_{str(profile_id)}'
        cache.delete(cache_key)
        return Response('ok')
