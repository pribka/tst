import json
import os
import uuid
import operator
from urllib.parse import urlparse
from datetime import timedelta
from functools import reduce
from django_q.tasks import async_task
import copy
import redis

from django.apps import apps
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, ObjectDoesNotExist, Value, Count, Case, When, Value, IntegerField
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.core.exceptions import FieldError, ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.conf import settings

from rest_framework import viewsets
from rest_framework import status
from rest_framework import exceptions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework_simplejwt.authentication import JWTAuthentication

from app_info.models import AppInfo, CustomRoutesModel

from contractor_permissions.utils import contractors_where_user_has_permission

from . import models
from . import serializers
from . import utils as common_utils
from . import paginators
from . import auth_classes
from . import utils
from . import front_routes
from . import defaults
from .redis import socketio_redis
from .serializers_for_import import load_users, load_organizations, load_profiles, load_wtl
from .table_settings import DEFAULT_TABLE_SETTINGS

from bkz3.settings import DOCUMENT_LOCK_TIMEOUT, IMPORT_DATA_TOKEN, GLOBAL_FRONT_SETTINGS, \
    MOBILE_GLOBAL_FRONT_SETTINGS, ZIPFILES_EXPIRE, MOBILE_APP_GLOBAL_FRONT_SETTINGS, MOBILE_APP_PRIVATE_OFFICE, \
    FRONT_CATEGORIES, MOBILE_FRONT_CATEGORIES, FILTER_BY_ORGANIZATIONS

try:
    from bkz3.settings import PRIVATE_OFFICE
except ImportError:
    PRIVATE_OFFICE = ({
                          'name': 'Персональная информация',
                          'path': 'personal',
                          'icon': 'idcard',
                          'widget': 'Personal'
                      },
                      {
                          'name': 'Сменить пароль',
                          'path': 'change-password',
                          'icon': 'lock',
                          'widget': 'Password'
                      },
                      {
                          "name": "Интерфейс",
                          "path": "interface",
                          "icon": "layout",
                          "widget": "Interface"
                      },)
try:
    from bkz3.settings import MOBILE_PRIVATE_OFFICE
except ImportError:
    MOBILE_PRIVATE_OFFICE = (
        {
            "name": "Персональная информация",
            "path": "personal",
            "icon": "fi-rr-id-badge",
            "widget": "Personal"
        },
        {
            "name": "Сменить пароль",
            "path": "change-password",
            "icon": "fi-rr-lock",
            "widget": "Password"
        },
    )
from users.serializers import AppUserSerializer, CachedAppUserPreviewSerializer
from users.models import ProfileModel
from custom_permission.utils import check_custom_permission


def get_meeting_server_base_url():
    from bpms.meetings.models import MeetingServerModel, _get_default_server

    default_server_code = _get_default_server()
    meeting_server = MeetingServerModel.objects.get(code=default_server_code)
    parsed_url = urlparse(meeting_server.url)
    if parsed_url.scheme and parsed_url.netloc:
        return f'{parsed_url.scheme}://{parsed_url.netloc}'
    return meeting_server.url.rstrip('/')


class AppInfoViewSet(viewsets.ViewSet, paginators.CustomFilterPagination):

    @action(methods=('get',), detail=False, url_path='timer', permission_classes=(IsAuthenticated,))
    def get_timer(self, request, *args, **kwargs):
        # from help_desk.models import HelpDeskWorkLogModel
        from help_desk.serializers import HelpDeskTicketShortSerializer
        from help_desk.utils import get_work_log_duration as ticket_duration
        # from bpms.tasks.models import TaskExecutionTimeModel
        from bpms.tasks.serializers import ShortTaskSerializer
        from bpms.tasks.utils import get_work_log_duration as task_duration
        user = request.user.profile
        try:
            current_work = user.current_work.original_object
        except AttributeError:
            data = dict()
        else:
            label = current_work.get_label()
            if label == 'help_desk.HelpDeskTicketModel':
                duration, is_current, incomplete_duration = ticket_duration(user, current_work)
                data = {
                    "ticket": HelpDeskTicketShortSerializer(
                        current_work,
                        context={'request': request, 'view': self}
                    ).data,
                    "duration": duration,
                    "is_current": is_current,
                    "incomplete_duration": incomplete_duration
                }
            elif label == 'tasks.TaskModel':
                duration, is_current, incomplete_duration = task_duration(user, current_work)
                data = {
                    "task": ShortTaskSerializer(
                        current_work,
                        context={'request': request, 'view': self}
                    ).data,
                    "duration": duration,
                    "is_current": is_current,
                    "incomplete_duration": incomplete_duration
                }
            else:
                data = dict()
        return Response(data)

    @action(methods=("get",), detail=False, url_path='entry', permission_classes=(), authentication_classes=())
    def get_entry(self, request, *args, **kwargs):
        try:
            entry_data = AppInfo.objects.get(code='entry', is_active=True).metadata
        except AppInfo.DoesNotExist:
            entry_data = {
                "register": False,
                "registerType": None,
                "forgotPassword": True,
                "privacy": None,
                "agreement": None
            }
        return Response(entry_data)

    @action(methods=["get", ], detail=False, url_path='check_front_cache', permission_classes=(), )
    def check_front_cache(self, request, *args, **kwargs):
        ver = request.query_params.get('ver', '')
        if ver == 'mobile_app':
            uid = cache.get_or_set('mobile_app_front_cache_uid', str(uuid.uuid4()))
        else:
            uid = cache.get_or_set('front_cache_uid', str(uuid.uuid4()))
        return Response({'uid': uid}, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=False, url_path='update_front_cache')
    def update_cache(self, request, *args, **kwargs):
        user = request.user
        if not user.is_anonymous and user.is_superuser:
            uid = str(uuid.uuid4())
            if request.query_params.get('ver', '') == 'mobile_app':
                cache.set('mobile_app_front_cache_uid', uid)
            else:
                cache.set('front_cache_uid', uid)
            return Response({'uid': uid}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @action(methods=["get", ], detail=False, url_path='routes', permission_classes=(IsAuthenticated,))
    def get_routes(self, request, *args, **kwargs):
        ver = request.query_params.get('ver', '')
        if ver == 'mobile':
            user = request.user.profile
            user_role = user.c1_roles.first()
            try:
                front_categories = AppInfo.objects.get(code="mobile_front_categories").metadata
            except AppInfo.DoesNotExist:
                front_categories = MOBILE_FRONT_CATEGORIES
            if user_role:
                try:
                    front_categories = AppInfo.objects.get(code=f"mobile_front_categories__1c_role__{user_role.pk}").metadata
                except AppInfo.DoesNotExist:
                    pass
            common_list = front_routes.MobileRoutes().get_dict()
            result_routes = []
            common_dict = dict()
            for each in common_list:
                try:
                    common_dict[each['name']] = each
                except KeyError:
                    continue
            for key, value in front_categories.items():
                try:
                    curr_dict = common_dict[key]
                except KeyError:
                    continue
                try:
                    curr_dict['meta']['showFooterMenu'] = value.get('show_footer_menu', False)
                except KeyError:
                    pass
                result_routes.append(curr_dict)
            return Response(result_routes)

        if ver == 'mobile_app':
            try:
                metadata = AppInfo.objects.get(code='mobile_app_front_routes', is_active=True).metadata
            except AppInfo.DoesNotExist:
                return Response(front_routes.MobileAppRoutes().get_dict(), status=status.HTTP_200_OK)
            return Response(metadata)
        if ver == 'alt':
            data = utils.get_alt_routes(request)
            return Response(data)
        common_dict = front_routes.Routes().get_dict()
        user = request.user.profile
        try:
            personal_dicts = models.InterfaceModel.objects.filter(role=user.c1_roles.first())
        except:
            personal_dicts = []
        if len(personal_dicts) > 0:
            personal_dict = personal_dicts[0].interface
        else:
            try:
                personal_dict = AppInfo.objects.get(is_active=True, code='front_categories').metadata
            except AppInfo.DoesNotExist:
                personal_dict = FRONT_CATEGORIES
        crm_items = personal_dict.get('crm', ())
        if isinstance(crm_items, str):
            crm_items = [crm_items]
        elif not isinstance(crm_items, (list, tuple)):
            try:
                crm_items = list(crm_items)
            except TypeError:
                crm_items = []
        if 'deals' not in crm_items:
            crm_items = list(crm_items) + ['deals']
        personal_dict['crm'] = tuple(crm_items)
        deleting_cats = []
        for category in common_dict:
            # if category['name'] in ('test_page', 'staff'):
            #     continue
            if not category['name'] in personal_dict:
                deleting_cats.append(category)
                continue

            deleting_subcats = []
            if category.get('children', None):
                for subsystem in category['children']:
                    if not subsystem['name'] in personal_dict[category['name']]: #  TODO пока test_page и edition не доступны.
                        deleting_subcats.append(subsystem)
                for subcat in deleting_subcats:
                    category['children'].remove(subcat)

        for item in deleting_cats:
            common_dict.remove(item)

        return Response(common_dict, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=False, url_path='routes/custom')
    def customize_routes(self, request, *args, **kwargs):
        data = request.data
        if not data:
            return Response()
        user = request.user.profile
        custom_route = CustomRoutesModel.objects.filter(is_active=True, author=user).order_by('-created_at').first()
        if not custom_route:
            custom_route = CustomRoutesModel()
        custom_route.metadata = data
        custom_route.save()
        resp_data = utils.get_alt_routes(request)
        return Response(resp_data)

    @action(methods=('get',), detail=False, url_path='routes/meta')
    def get_routes_meta(self, request, *args, **kwargs):
        name = request.query_params.get('name', '')
        user = request.user.profile
        if name == 'deals':
            allowed_contractors = contractors_where_user_has_permission(user.pk, ('admin', 'create_workgroup',), None)
            if allowed_contractors:
                data = {'pageActions': {'add': True}}
            else:
                data = dict()
            return Response(data)
        if utils.use_access_groups(user.pk):
            access_groups = utils.get_my_access_groups(user)
            from contractor_permissions.models import AccessGroupAppSectionRoleThrough
            lookup = {
                'access_group__in': access_groups,
                f'app_section_role__routes_meta__{name}__isnull': False,
            }
            app_section_role = AccessGroupAppSectionRoleThrough.objects.filter(
                **lookup,
            ).order_by('app_section_role__role__access_level').first()
            if app_section_role:
                data = app_section_role.app_section_role.routes_meta.get(name)
                return Response(data)
            else:
                return Response({})
        try:
            metadata = AppInfo.objects.get(is_active=True, code='routes_meta').metadata
        except AppInfo.DoesNotExist:
            metadata = defaults.DEFAULT_ROUTES_META
        data = copy.deepcopy(metadata.get(name, dict()))
        if not data and name in defaults.DEFAULT_ROUTES_META:
            data = copy.deepcopy(defaults.DEFAULT_ROUTES_META.get(name, dict()))
        if name in ('groups', 'projects'):
            data['pageActions']['add'] = True
            if FILTER_BY_ORGANIZATIONS:
                # im_director = user.contractor_profile.filter(director=True).exists()
                from contractor_permissions.models import ContractorPermissionModel
                contractor_permission = ContractorPermissionModel.objects.filter(
                    permission_type_id='create_workgroup',
                    contractor_permission_role__contractor_profiles__user=user.pk,
                    contractor_permission_role__is_active=True,
                ).exists()
                if not contractor_permission:
                    try:
                        data['pageActions']['add'] = False
                    except KeyError:
                        pass
            else:
                if not user.can_create_workgroups:
                    try:
                        data['pageActions']['add'] = False
                    except KeyError:
                        pass
        if name == 'orders' and not user.has_full_access_to_order_editing:
            try:
                data['pageActions']['add'] = False
            except KeyError:
                pass
        if name == 'sports-facilities' and not contractors_where_user_has_permission(user.pk, 'create_sport_facility', None):
            data['pageActions']['add'] = False
        if name == 'projects-sprints':
            is_project_moderator = user.workgroupmembersmodel_set.filter(
                is_active=True,
                work_group__is_active=True,
                work_group__is_project=True,
                membership_request_status__code='APPROVED',
                membership_role__code__in=('FOUNDER', 'MODERATOR',),
            ).exists()
            if is_project_moderator:
                try:
                    data['pageActions']['add'] = True
                except KeyError:
                    data['pageActions'] = {
                        'add': True,
                        'addTemplate': True,
                        'help': True,
                    }

        return Response(data)

    @action(methods=['get', ], detail=False, url_path='form_info')
    def get_form_info(self, request, *arts, **kwargs):
        form_name = request.query_params.get('form')
        if form_name:
            data = cache.get(f'form_info:{form_name}')
        else:
            data = dict()
        return Response(data, status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, url_path='form_fields_info')
    def get_form_fields_info(self, request, *arts, **kwargs):
        form_name = request.query_params.get('form')
        if form_name:

            rec = AppInfo.objects.filter(code=f'form_fields_info_{form_name}').first()

            if rec:
                return Response(rec.metadata, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
            #data = cache.get(f'form_fields_info:{form_name}')
        else:
            data = dict()
        return Response(data, status.HTTP_200_OK)

    @action(methods=["get", ], detail=False, url_path='table_info')
    def get_table_info(self, request, *args, **kwargs):
        model = utils.get_model(request)
        if not model:
            return Response(status=status.HTTP_404_NOT_FOUND)
        data = model.get_table_structure()
        # if 'alt' in request.query_params:
        #     data = model.get_alt_table_structure()
        return Response(
            data,
            status=status.HTTP_200_OK,
        )

    @action(methods=['get', ], detail=False, url_path='filter_info')
    def get_filter_info(self, request, *args, **kwargs):
        """Получить информацию о фильтрах таблицы"""
        model = utils.get_model(request)
        if not model:
            return Response(status=status.HTTP_404_NOT_FOUND)
        filter_class = model.get_filterset_class()
        filter_info = []
        for key, value in filter_class.base_filters.items():
            try:
                # filter_info.append(value.get_widget())
                # splited = model.split('.')
                # model_label = apps.get_model(splited[0], splited[1])()
                # filter_info.append(model_label.fields_to_dict())
                print('Filter Info: ', filter_info)
            except:
                pass
        return Response(filter_info, status=status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, url_path='select_list')
    def get_select_list(self, request, *args, **kwargs):
        """Получить список для селекта"""
        model = utils.get_model(request)
        if not model:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # try: TODO убрал механику вывода селекта как в 1С.
        #     is_enum = model.is_enum()
        # except AttributeError:
        #     is_enum = False
        # default_value = request.query_params.get('default_value')
        # try:
        #     default_pk = str(model.objects.get(code=default_value).pk)
        # except (ObjectDoesNotExist, FieldError):
        #     default_pk = None
        # if is_enum:
        queryset = model.get_select_queryset(request)
        if 'filters' in list(request.query_params.keys()):
            filters_dict = json.loads(request.query_params.get('filters'))
            queryset = utils.filter_queryset_from_get_param(filters_dict, queryset=queryset)
        s_data = serializers.SelectListSerializer(queryset, many=True).data
        # else:
        #     cache_key = self.picked_records_key
        #     cached_data = cache.get(cache_key, [])
        #     if default_pk and default_pk not in cached_data:
        #         cached_data.append(default_pk)
        #     queryset = model.get_select_queryset().filter(pk__in=cached_data)[:20]
        #     data = []
        #     for each in queryset:
        #         obj_id = str(each.id)
        #         if obj_id in cached_data:
        #             data.insert(cached_data.index(obj_id), each)
        #     s_data = serializers.SelectListSerializer(data, many=True).data
        #     new_cache_data = [str(i.get('id')) for i in s_data]
        #     cache.set(cache_key, new_cache_data, timeout=None)
        return Response({"selectList": s_data}, status=status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, url_path='filtered_select_list')
    def get_filtered_select_list(self, request, *args, **kwargs):
        """Получить список для селекта, отфильтрованных по значению из гет-параметра text."""
        text = request.query_params.get('text')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        first = request.query_params.get('first')
        if search:
            text = search
        model = utils.get_model(request)
        if 'filters' in list(request.query_params.keys()):
            filters_dict = json.loads(request.query_params.get('filters'))
        else:
            filters_dict = dict()
        if text is None:
            # Получаем уже выбранные объекты в селекте:
            page_name = request.query_params.get('page_name')
            field = request.query_params.get('field')
            selected_qs = None
            if page_name and field:
                # Здесь не надо фильтровать FiltersStore по model!!!
                # Потому что фильтр сохранен для одной модели (например, TaskModel),
                # а мы пытаемся внутри него найти значения для другой модели (например, WorkgroupModel)
                # (в запросе filtered_select_list будет другая model, чем та, для которой сохранен фильтр).
                try:
                    user_filter = models.FiltersStore.objects.get(
                        author=request.user.profile,
                        page_name=page_name,
                        is_active=True,
                    )
                except models.FiltersStore.DoesNotExist:
                    user_filter = None
                if user_filter:
                    selected_objects = user_filter.filters.get(
                        'values', dict()).get(field, dict()).get('values', dict()).get('value')
                    if selected_objects:
                        try:
                            selected_qs = model.get_select_queryset(request).filter(
                                pk__in=selected_objects).annotate(priority=Value(0))
                        except ValidationError:
                            selected_qs = model.get_select_queryset(request).filter(
                                code__in=selected_objects).annotate(priority=Value(0))
            queryset = model.get_select_queryset(request)
            if filters_dict:
                queryset = utils.filter_queryset_from_get_param(filters_dict, queryset)
            if selected_qs:
                # Объединяем запросы, если есть выбранные объекты:
                try:
                    queryset = selected_qs.union(
                        queryset.exclude(pk__in=selected_qs).annotate(priority=Value(1))
                    ).order_by(
                        *['priority'],
                        *model.get_order_param()
                    )
                except ValidationError:
                    queryset = selected_qs.union(
                        queryset.exclude(code__in=selected_qs).annotate(priority=Value(1))
                    ).order_by(*['priority'], *model.get_order_param())
            if first:
                first_uuid = uuid.UUID(first)
                queryset = queryset.annotate(
                    custom_order=Case(
                        When(id=first_uuid, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                ).order_by('custom_order')

            if ordering and ordering != '':
                queryset = queryset.order_by(*ordering.split(','))

            page = self.paginate_queryset(queryset, request, view=self)
            if page is not None:
                s_data = serializers.SelectListSerializer(page, many=True).data
                return self.get_paginated_response(s_data)
            else:
                return Response({"filteredSelectList": []}, status=status.HTTP_200_OK)
        if not isinstance(text, str) or len(text) <= 2:
            return Response({"filteredSelectList": []}, status=status.HTTP_200_OK)
        if not model:
            return Response({"filteredSelectList": []}, status=status.HTTP_200_OK)
        filtered_select_queryset = model.get_filtered_select_queryset(text, request)
        if filters_dict:
            filtered_select_queryset = utils.filter_queryset_from_get_param(filters_dict, filtered_select_queryset)

        if ordering and ordering != '':
            filtered_select_queryset = filtered_select_queryset.order_by(*ordering.split(','))

        filtered_select_queryset = filtered_select_queryset[:20]
        s_data = serializers.SelectListSerializer(filtered_select_queryset, many=True).data
        return Response({"filteredSelectList": s_data}, status=status.HTTP_200_OK)

    def get_model(self, request):
        model_app_label = request.query_params.get('model', None)
        if not model_app_label:
            return None
        app_name, model_name = model_app_label.split('.')
        try:
            model = apps.get_model(app_name, model_name)
        except LookupError:
            return None
        return model

    @action(methods=['get', ], detail=False, url_path='global', permission_classes=(IsAuthenticated,))
    def get_global(self, request, *args, **kwargs):
        ver = request.query_params.get('ver', '')
        if ver == 'mobile':
            default_settings = MOBILE_GLOBAL_FRONT_SETTINGS
            code = 'mobile_global_front_settings'
        elif ver == 'mobile_app':
            default_settings = MOBILE_APP_GLOBAL_FRONT_SETTINGS
            code = 'mobile_app_global_front_settings'
        else:
            default_settings = GLOBAL_FRONT_SETTINGS
            code = 'global_front_settings'
        data = copy.copy(default_settings)
        try:
            custom_data = AppInfo.objects.get(
                is_active=True,
                code=code,
            ).metadata
        except AppInfo.DoesNotExist:
            custom_data = dict()
        for key, value in custom_data.items():
            data[key] = value

        data['meeting_settings'] = {
            'server': get_meeting_server_base_url(),
        }

        user = request.user.profile
        role_1c = user.c1_roles.filter(is_active=True).first() # TODO только одна роль должна быть! Иначе будет непредсказуемый результат.
        if role_1c:
            try:
                role_custom_data = AppInfo.objects.get(
                    is_active=True,
                    code=f"{code}__1c_role__{role_1c.pk}"
                ).metadata
            except AppInfo.DoesNotExist:
                return Response(data, status=status.HTTP_200_OK)
            for key, value in role_custom_data.items():
                data[key] = value

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='private_office')
    def get_private_office(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user = request.user.profile
        ver = request.query_params.get('ver', '')
        try:
            result = AppInfo.objects.get(is_active=True, code=f"{ver}_private_office").metadata
        except AppInfo.DoesNotExist:
            if ver == 'mobile_app':
                return Response(MOBILE_APP_PRIVATE_OFFICE, status=status.HTTP_200_OK)
            if ver == 'mobile':
                result = MOBILE_PRIVATE_OFFICE
            else:
                result = PRIVATE_OFFICE
        if user.default_chat:
            result += ({
                           "name": "Чат дилера",
                           "path": "chat",
                           "icon": "message",
                           "widget": "DealerChat",
                       },)
        return Response(result)

    @action(methods=['get', ], detail=False, url_path='pick_record')
    def pick_record(self, request, *args, **kwargs):
        """Добавляет выбранную запись таблицы в список"""
        model = utils.get_model(request)
        if not model:
            return Response(status=status.HTTP_404_NOT_FOUND)
        record_id = request.query_params.get('id')
        if not record_id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        cache_key = self.picked_records_key
        cache_data = cache.get(cache_key, [])
        try:
            cache_data.remove(record_id)
        except ValueError:
            pass
        cache_data.insert(0, record_id)
        cache.set(cache_key, cache_data, timeout=None)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, url_path='custom_style')
    def custom_style(self, request, *args, **kwargs):
        """Проба пера кастомных стилей"""

        theme = models.CustomThemeModel.objects.first()
        css_data = ''

        if theme is not None:
            css_data = theme.css_text

        return HttpResponse(css_data, content_type="text/css")

    @action(methods=['get', ], detail=False, url_path='custom_js')
    def custom_js(self, request, *args, **kwargs):
        """Проба пера кастомных JS"""
        if request.user.is_authenticated:
            return HttpResponse('', content_type="application/javascript")
            # TODO в идеале, будем подгонять кастомный JS. Пока, по задаче, сделаем так
        theme = models.CustomJSModel.objects.first()
        js_data = ''

        if theme is not None:
            js_data = theme.js_text

        return HttpResponse(js_data, content_type="application/javascript")

    @property
    def picked_records_key(self):
        return f"picked_records__user_{self.request.user.id}__model_{self.request.query_params.get('model')}"

    @action(methods=['post'], detail=False, url_path='chosen_filters')
    def post_chosen_filters(self, request, *args, **kwargs):
        model_app_label = request.data.get('key', None)
        if not model_app_label:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        app_name, model_name = model_app_label.split('.')
        try:
            model = apps.get_model(app_name, model_name)
        except LookupError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        page_name = request.data.get('page_name', '')
        instance, is_created = models.FiltersStore.objects.get_or_create(
            author=request.user.profile,
            model=model_app_label,
            page_name=page_name,
        )
        # data = {'values': request.data.get('fields', dict()),
        #         'filterTags': request.data.get('filterTags', list()),
        #         'search': request.data.get('search', ""),
        #         'ordering': request.data.get('ordering', list()),
        #         'others': request.data.get('others', dict())
        #         }
        # instance.filters = data
        instance.filters['values'] = request.data.get('fields', dict())
        instance.filters['filterTags'] = request.data.get('filterTags', list())
        instance.filters['search'] = request.data.get('search', "")
        instance.filters['ordering'] = request.data.get('ordering', list())
        instance.filters['others'] = request.data.get('others', dict())

        instance.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='products_list_info')
    def get_products_list_info(self, request, *args, **kwargs):

        try:
            from bkz3.local_settings import PRODUCT_LIST_INFO
        except:
            PRODUCT_LIST_INFO = [
                {
                    "type": 'ProductCard',
                    "icon": 'fi-rr-apps',
                    "title": 'Карточки',
                },
                {
                    "type": 'ProductCardList',
                    "icon": 'fi-rr-ballot',
                    "title": 'Список',
                },
                {
                    "type": 'ProductCardInfoList',
                    "icon": 'fi-rr-list',
                    "title": 'Короткий список',
                },
            ]

        result = PRODUCT_LIST_INFO

        return Response(result)

    @action(methods=('get',), detail=False, url_path='contractors_list_info')
    def get_contractors_list_info(self, request, *args, **kwargs):

        try:
            from bkz3.local_settings import CONTRACTORS_LIST_INFO
        except:
            CONTRACTORS_LIST_INFO = [
                {
                    "type": 'ContractorsViewGrid',
                    "icon": 'fi-rr-apps',
                    "title": 'Карточки',
                },
                {
                    "type": 'ContractorsViewTable',
                    "icon": 'fi-rr-list',
                    "title": 'Таблица',
                },
        ]

        result = CONTRACTORS_LIST_INFO

        return Response(result)

    @action(methods=['get'], detail=False, url_path='active_filters')
    def get_active_filters(self, request, *args, **kwargs):
        model = utils.get_model(request)
        if model is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            active_filters = models.FiltersStore.objects.get(author=request.user.profile,
                                                             model=request.query_params.get('model'),
                                                             page_name=request.query_params.get('page_name', '')
                                                             )
        except models.FiltersStore.DoesNotExist:
            return Response({
                "include": model.get_filter_fields(request=request),
                "exclude": model.get_filter_fields(exclude=True, request=request),
                "activeFilters": dict(),
                "filterTags": list(),
                "searchInput": model.search_input(),
                "search": "",
                "ordering": list(),
                "others": dict(),
            }, status=status.HTTP_200_OK)
        values = active_filters.filters
        if values is None:
            values = dict()
        data = {
            "include": model.get_filter_fields(request=request),
            "exclude": model.get_filter_fields(exclude=True, request=request),
            "activeFilters": values.get('values', dict()),
            "filterTags": values.get('filterTags', list()),
            "search": values.get('search', ''),
            "searchInput": model.search_input(),
            "ordering": values.get('ordering', list()),
            "others": values.get('others', dict()),
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post', 'delete'], detail=False, url_path='recently_selected_users')
    def recently_selected_users(self, request, *args, **kwargs):
        """GET: список ранее выбранных пользователей. POST: добавить profile_id в начало списка (макс. 30). DELETE: удалить запись автора."""
        if request.method == 'GET':
            return self._get_recently_selected_users(request)
        if request.method == 'DELETE':
            return self._delete_recently_selected_users(request)
        return self._post_recently_selected_users(request)

    def _get_recently_selected_users(self, request):
        """Возвращает пользователей в том же порядке, что в БД: первый в списке profile_ids — первым в ответе."""
        try:
            store = models.RecentlySelectedUsersModel.objects.get(author=request.user.profile)
            profile_ids = store.profile_ids or []
        except models.RecentlySelectedUsersModel.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        data = []
        for pid in profile_ids:
            try:
                data.append(CachedAppUserPreviewSerializer(instance=pid).data)
            except ProfileModel.DoesNotExist:
                pass
        return Response(data, status=status.HTTP_200_OK)

    def _delete_recently_selected_users(self, request):
        """Удаляет запись RecentlySelectedUsersModel для автора (текущего пользователя)."""
        models.RecentlySelectedUsersModel.objects.filter(author=request.user.profile).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _post_recently_selected_users(self, request):
        raw_id = request.data.get('id')
        ids = [raw_id] if not isinstance(raw_id, list) else raw_id
        store, created = models.RecentlySelectedUsersModel.objects.get_or_create(
            author=request.user.profile,
            defaults={'profile_ids': []},
        )
        profile_ids = list(store.profile_ids or [])
        for pid in ids:
            try:
                profile_ids.remove(pid)
            except ValueError:
                pass
            profile_ids.insert(0, pid)
        store.profile_ids = profile_ids[:30]
        store.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='characteristic')
    def get_characteristic(self, request, *args, **kwargs):
        model = utils.get_model(request)

        characteristics, independent_fields = model.get_model_characteristics_fields()

        blocks_choices = models.PlanOfCharacteristicBlock.objects.filter(
            characteristics__in=(*characteristics, *independent_fields)
        ).distinct().order_by('sort').values_list('code', 'name')
        blocks = []
        for choice_code, choice_name in blocks_choices:
            block_characteristic = characteristics.filter(block=choice_code)
            independent_fields_blocks = independent_fields.filter(block=choice_code)
            editable_part = {
                "name": f"{choice_code}_BLOCK",
                "title": str(choice_name),
                "block_code": str(choice_code),
                "type_for_front": 'form',
                "fields": block_characteristic,
                "independent_fields": independent_fields_blocks,
                "filterInfo": ""
            }
            if block_characteristic.__len__() > 0 or independent_fields_blocks.__len__() > 0:
                blocks.append(editable_part)
        from pvh.serializers import PlanOfCharacteristicBlockSerializer
        poc_data = PlanOfCharacteristicBlockSerializer(blocks, many=True).data
        result = {
            "title": "Каталогизация",
            "type": "form",
            "pageWidget": "TableForm",
            "navWidget": "NavForm",
            "name": model._meta.label + '_parts',
            "editablePart": poc_data,
        }
        return Response(result, status=status.HTTP_200_OK)


class BaseModelActionsViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(methods=['post', ], detail=False)
    def update_is_active(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            data = [data]
        serializer = serializers.IsActiveSetSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            for each in serializer.validated_data:
                final_instance = models.BaseModel.objects.super_get(each.get('id').pk)
                final_instance.set_is_active(each.get('is_active'), request)
                final_instance.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False)
    def update_is_posted(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            data = [data]
        serializer = serializers.IsPostedSetSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            for each in serializer.validated_data:
                instance = each.get('id')
                is_posted = each.get('is_posted')
                instance.check_locking()
                final_instance = instance.get_final_instance()
                final_instance.set_is_posted(is_posted)
                final_instance.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, url_path='lock_document')
    def lock_document(self, request, *args, **kwargs):
        instance_id = request.data.get('id')
        if not instance_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        cache_key = f'locked_doc__{instance_id}'
        instance_locked = cache.get(cache_key, dict())
        user = request.user
        if not instance_locked or instance_locked.get('user', dict()).get('id', 0) == user.id:
            now = timezone.now()
            cache_data = {
                'date': now,
                'user': AppUserSerializer(user).data
            }
            cache.set(cache_key, cache_data, timeout=DOCUMENT_LOCK_TIMEOUT)
            return Response('ok', status=status.HTTP_200_OK)
        else:
            user = instance_locked.get('user')
            if user:
                user_fullname = f"{user.get('last_name', '')} {user.get('first_name', '')} {user.get('middle_name', '')}"
            else:
                user_fullname = ''
            raise exceptions.PermissionDenied(_('Document locked by user') + ' ' + user_fullname)

    @action(methods=['post', ], detail=False, url_path='unlock_document')
    def unlock_document(self, request, *args, **kwargs):
        instance_id = request.data.get('id')
        if not instance_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        cache_key = f'locked_doc__{instance_id}'
        instance_locked = cache.get(cache_key, dict())
        user = request.user
        if instance_locked.get('user', dict()).get('id', 0) == user.id:
            cache.delete_pattern(cache_key)
        return Response('ok', status=status.HTTP_200_OK)


class BaseModelViewSet(viewsets.ModelViewSet):
    model = models.BaseModel
    pagination_class = paginators.CustomPagination
    permission_classes = (IsAuthenticated,)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if self.request.query_params.get('no_pagination', 'false') == 'true':
            return None
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def filter_queryset(self, queryset):
        return utils.order_queryset_from_get_param(
            self.request, self.model, utils.get_filter_queryset(self.request, self.model, queryset)
        )

    def get_queryset(self):
        return self.model.get_queryset(self.request)

    def get_serializer_class(self, *args, **kwargs):
        return self.model.get_serializer_class(action=self.action)

    # def create(self, request, *args, **kwargs):
    #     # Проверим права
    #     check_custom_permission(self, 'create', request)
    #     return super().create(request, *args, **kwargs)
    #
    # def update(self, request, *args, **kwargs):
    #     check_custom_permission(self, 'update', request)
    #     return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_418_IM_A_TEAPOT)


class BaseCatalogViewSet(BaseModelViewSet):
    model = models.BaseCatalog

    def create(self, request, *args, **kwargs):
        if self.model.is_enum():
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if self.model.is_enum():
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class FileViewSet(BaseCatalogViewSet):
    authentication_classes = (
        auth_classes.CsrfExemptSessionAuthentication, auth_classes.BasicAuthentication, JWTAuthentication)
    pagination_class = paginators.BreadCramsCustomPaginator
    model = models.File

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'update_folder':
            return serializers.FolderUpdateSerializer
        elif self.action == 'create_folder':
            return serializers.FolderCreateSerializer

        return super().get_serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        folder_id = request.GET.get('folder', None)
        user = request.user.profile
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(id=folder_id, related_object=user, is_active=True)
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            folder = None
        files = utils.get_filter_queryset(
            request,
            self.model,
            models.File.objects.filter(
                folder=folder,
                author=user,
                is_active=True,
                is_confined=False
            )
        ).values('pk', 'ct')
        if folder:
            folders_qs = folder.get_children().filter(is_active=True)
        else:
            folders_qs = models.FolderModel.objects.filter(
                parent__isnull=True,
                related_object=user,
                is_active=True
            )
        folders_qs = utils.get_filter_queryset(request, models.FolderModel, folders_qs).values('pk', 'ct')
        breadcrumb = []
        folder_name = None
        if folder:
            breadcrumb.append({'name': 'Все файлы', 'folder_id': None})
            folder_name = folder.name
            if folder.parent:
                ancestors = folder.get_ancestors(include_self=False).order_by('level')
                for each in ancestors:
                    breadcrumb.append({'name': each.name, 'folder_id': str(each.pk)})
        total_qs = files.union(folders_qs)
        order_field_keys = utils.get_field_keys(request, models.BaseCatalog)
        if order_field_keys:
            total_qs = total_qs.order_by('-ct', *order_field_keys)
        else:
            page_name = request.query_params.get('page_name', None)
            if page_name:
                try:
                    filters_store = models.FiltersStore.objects.get(page_name=page_name, author=user)
                except models.FiltersStore.DoesNotExist:
                    filters_store = None
                if filters_store:
                    ordering_fields = filters_store.filters.get('ordering', [])
                    if ordering_fields:
                        total_qs = utils.order_queryset(models.BaseCatalog, total_qs, ordering_fields)
        if not total_qs.ordered:
            total_qs = total_qs.order_by('-ct', '-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(total_qs, request, self)
        context = {"related_object": str(user.pk)}
        serialized_data = serializers.FileAndFolderSerializer(page, many=True, context=context).data
        paginate_response = paginator.get_paginated_response(serialized_data, breadcrumb, folder_name)
        return paginate_response

    @action(
        methods=('post',),
        detail=False,
        url_path='add_folder',
    )
    def add_folder(self, request, *args, **kwargs):
        data = self.request.data.copy()
        data['related_object'] = request.user.profile.pk
        folder_serializer = serializers.FolderCreateSerializer(data=data)
        folder_serializer.is_valid(raise_exception=True)
        folder_serializer.save()
        return Response(data=folder_serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('put',),
        detail=False,
        url_path='update_folder',
    )
    def update_folder(self, request, *args, **kwargs):
        data = request.data
        user = request.user.profile
        try:
            folder = models.FolderModel.objects.get(pk=data.get('id'), related_object=user)
        except ObjectDoesNotExist:
            raise ValidationError('Folder not found.')
        serializer = serializers.FolderUpdateSerializer(instance=folder, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('post',),
        detail=False,
        url_path='remove_files',
    )
    def remove_files(self, request, *args, **kwargs):
        folders_list = request.data.get('folders', [])
        files_list = request.data.get('files', [])
        folder_id = request.data.get('folder', None)
        user = request.user.profile
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(pk=folder_id, related_object=user, is_active=True)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found.')
        else:
            folder = None
        folders = models.FolderModel.objects.filter(
            pk__in=folders_list,
            parent=folder,
            related_object=user,
            is_active=True,
        )
        with transaction.atomic():
            now = timezone.now()
            for each in folders:
                each.parent = None
                each.save()
                descendants = each.get_descendants(include_self=True).filter(is_active=True)
                included_files = models.File.objects.filter(is_active=True, folder__in=descendants, author=user)
                included_files.update(
                    is_active=False,
                    deleted_at=now
                )
                descendants.update(is_active=False, deleted_at=now)
            models.File.objects.filter(
                folder=folder,
                pk__in=files_list,
                is_active=True,
                author=user
            ).update(is_active=False, folder=None, deleted_at=now)
        return Response(data={'status': 'ok'}, status=status.HTTP_200_OK)

    @action(
        methods=('post',),
        detail=False,
        url_path='restore',
    )
    def restore(self, request, *args, **kwargs):
        data = request.data
        files_list = data.get('files', [])
        folders_list = data.get('folders', [])
        folder_id = data.get('folder', None)
        user = request.user.profile
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(pk=folder_id, related_object=user, is_active=True)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found.')
        else:
            folder = None
        folders = models.FolderModel.objects.filter(
            pk__in=folders_list,
            related_object=user,
            is_active=False,
        )
        with transaction.atomic():
            for each in folders:
                each.parent = folder
                each.save()
                descendants = each.get_descendants(include_self=True).filter(is_active=False)
                models.File.objects.filter(
                    is_active=False,
                    folder__in=descendants,
                    author=user).update(
                    is_active=True,
                    deleted_at=None,
                )
                descendants.update(is_active=True, deleted_at=None)
            models.File.objects.filter(
                pk__in=files_list,
                is_active=False,
                author=user
            ).update(is_active=True, folder=folder, deleted_at=None)
        return Response(data={'status': 'ok'}, status=status.HTTP_200_OK)

    @action(
        methods=('get',),
        detail=False,
        url_path='folders',
    )
    def get_folders(self, request, *args, **kwargs):
        folder_id = request.query_params.get('folder')
        user = request.user.profile
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(is_active=True, related_object=user, pk=folder_id)
            except ObjectDoesNotExist:
                return Response('Folder not found.')
        else:
            folder = None
        queryset = models.FolderModel.objects.filter(
            is_active=True,
            parent=folder,
            related_object=user
        ).order_by('name')
        paginator = paginators.CustomPagination()
        page = paginator.paginate_queryset(queryset, request, self)
        s_data = serializers.BaseFolderSerializer(page, many=True).data
        return paginator.get_paginated_response(s_data)

    @action(
        methods=('get',),
        detail=False,
        url_path='trash',
    )
    def get_trash(self, request, *args, **kwargs):
        folder_id = request.GET.get('folder', None)
        user = request.user.profile
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(
                    id=folder_id,
                    related_object=user,
                    is_active=False,
                    is_deleted=False,
                )
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            folder = None
        if folder:
            files = utils.get_filter_queryset(
                request,
                self.model,
                models.File.objects.filter(
                    folder=folder, author=user, is_active=False, is_deleted=False).values_list('pk', flat=True)
            )
        else:
            files = utils.get_filter_queryset(
                request,
                self.model,
                models.File.objects.filter(
                    Q(folder__isnull=True) | Q(folder__is_active=True),
                    author=user,
                    is_active=False,
                    is_deleted=False
                ).values('pk', 'ct')
            )
        if folder:
            folders_qs = folder.get_children().filter(is_active=False, is_deleted=False,)
        else:
            folders_qs = models.FolderModel.objects.filter(
                Q(parent__isnull=True) | Q(parent__is_active=True),
                related_object=user,
                is_active=False,
                is_deleted=False,
            )
        folders_ids = utils.get_filter_queryset(request, models.FolderModel, folders_qs).values('pk', 'ct')
        breadcrumb = []
        folder_name = None
        if folder:
            breadcrumb.append({'name': 'Все файлы', 'folder_id': None})
            folder_name = folder.name
            if folder.parent:
                breadcrumb.append({'name': folder.parent.name, 'folder_id': str(folder.parent_id)})
        total_qs = files.union(folders_ids)
        order_field_keys = utils.get_field_keys(request, models.BaseCatalog)
        if order_field_keys:
            total_qs = total_qs.order_by('-ct', *order_field_keys)
        else:
            page_name = request.query_params.get('page_name', None)
            if page_name:
                try:
                    filters_store = models.FiltersStore.objects.get(page_name=page_name, author=user)
                except models.FiltersStore.DoesNotExist:
                    filters_store = None
                if filters_store:
                    ordering_fields = filters_store.filters.get('ordering', [])
                    if ordering_fields:
                        total_qs = utils.order_queryset(models.BaseCatalog, total_qs, ordering_fields)
        if not total_qs.ordered:
            total_qs = total_qs.order_by('-ct', '-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(total_qs, request, self)
        context = {"related_object": str(user.pk)}
        serialized_data = serializers.FileAndFolderSerializer(page, many=True, context=context).data
        paginate_response = paginator.get_paginated_response(serialized_data, breadcrumb, folder_name)
        return paginate_response

    @action(methods=('post',), detail=False, url_path='trash/clear')
    def clear_trash(self, request, *args, **kwargs):
        user = request.user.profile
        files = models.File.objects.filter(author=user, is_active=False, is_deleted=False)
        folders = models.FolderModel.objects.filter(
                Q(parent__isnull=True) | Q(parent__is_active=True),
                related_object=user,
                is_active=False,
                is_deleted=False,
            )
        files.update(is_deleted=True)
        folders.update(is_deleted=True)

        return Response('ok')

    @action(
        methods=('post',),
        detail=False,
        url_path='delete_files',
    )
    def delete_files(self, request, *args, **kwargs):
        data = request.data
        user = request.user.profile
        folders_list = data.get('folders', [])
        files_list = data.get('files', [])
        folders = models.FolderModel.objects.filter(is_active=False, related_object=user, pk__in=folders_list)
        with transaction.atomic():
            for each in folders:
                each.parent = None
                each.save()
                descendants = each.get_descendants(include_self=True)
                models.File.objects.filter(folder__in=descendants).update(is_active=False, is_deleted=True)
                descendants.update(is_active=False, is_deleted=True)
            files = models.File.objects.filter(author=user, is_active=False, pk__in=files_list)
            files.update(is_deleted=True)
        return Response('ok')

    @action(
        methods=('post',),
        detail=False,
        url_path='move_files',
    )
    def move_files(self, request, *args, **kwargs):
        files_list = request.data.get('files', [])
        folders_list = request.data.get('folders', [])
        folder_id = request.data.get('folder', None)
        user = request.user.profile
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(pk=folder_id, related_object=user)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found.')
        else:
            folder = None
        models.File.objects.filter(
            pk__in=files_list,
            is_dynamic=False,
            author=user,
        ).update(folder=folder)
        folders = models.FolderModel.objects.filter(pk__in=folders_list, related_object=user)
        for each in folders:
            each.parent = folder
            each.save()
        return Response(data={'status': 'ok'}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='aggregate',)
    def get_aggregate(self, request, *args, **kwargs):
        folder = request.query_params.get('folder')
        user = request.user.profile
        if folder:
            try:
                folder = models.FolderModel.objects.get(pk=folder, related_object=user)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found.')
            descendants = folder.get_descendants(include_self=True)
            folders_count = descendants.count() - 1
            files_count = descendants.aggregate(files_count=Count('directly_files'))['files_count']
        else:
            folders_count = models.FolderModel.objects.filter(related_object=user).count()
            files_count = models.File.objects.filter(author=user, is_active=True).count()
        return Response({'folders': folders_count, 'files': files_count})

    @action(methods=('post',), detail=False, url_path='zip')
    def create_zip(self, request, *args, **kwargs):
        user = request.user.profile
        folder_id = request.data.get('folder')
        if folder_id:
            try:
                folder = models.FolderModel.objects.get(pk=folder_id, related_object=user)
            except ObjectDoesNotExist:
                raise ValidationError('Folder not found')
        else:
            folder = None
        files_from = utils.FilesFrom.directly_files
        already_working = cache.get(utils.get_already_working_key(user.pk, folder, files_from), False)
        if not already_working:
            async_task(utils.create_zip_file, user, folder, files_from, q_options={'timeout': ZIPFILES_EXPIRE})
        return Response({'already_working': already_working})

    @action(methods=('get',), detail=True, url_path='related_objects')
    def get_related_objects(self, request, *args, **kwargs):
        file = self.get_object()
        data = {
            "attaches": self.get_related_object_list(
                file.basemodel_set.filter(is_active=True).values_list('pk', flat=True)
            ),
            "galleries": self.get_related_object_list(
                file.gallerymodel_set.filter(is_active=True).values_list('related_object', flat=True)
            ),
            "ckeditors": self.get_related_object_list(
                file.ckeditorfilemodel_set.filter(is_active=True).values_list('related_object', flat=True)
            ),
            "workgroup_logo": self.get_related_object_list(
                file.workgroupmodel_set.filter(is_active=True).values_list('pk', flat=True)
            ),
            "workgroup_gallery": self.get_related_object_list(
                file.workgroup_gallery_files.filter(is_active=True).values_list('pk', flat=True)
            ),
        }
        return Response(data)

    def get_related_object_list(self, ids):
        data_list = []
        for each in ids:
            instance = models.BaseModel.objects.super_get(pk=each)
            serializer_class = instance.get_serializer_class(action='list')
            data = serializer_class(instance).data
            data['object_type'] = instance.get_label()
            data_list.append(data)
        return data_list


class MimeTypeViewSet(BaseCatalogViewSet):
    model = models.MimeType

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_403_FORBIDDEN)


class FileTypeViewSet(BaseCatalogViewSet):
    model = models.FileType


class OrganizationViewSet(BaseCatalogViewSet):
    model = models.Organization


class IndividualViewSet(BaseCatalogViewSet):
    model = models.Individual


class BaseDocumentViewSet(BaseModelViewSet):
    model = models.BaseDocument

    def get_serializer_class(self, *args, **kwargs):
        return self.model.get_serializer_class(action=self.action)

    def get_tabular_parts(self, request, pk=None):
        instance = self.get_object()

        tabular_parts = self.model.get_tabular_parts()
        tabular_name = self.action.replace('get_', '')
        tabular_part_model = tabular_parts.get(tabular_name)
        if not tabular_part_model:
            return Response([], status=status.HTTP_200_OK)
        tabular_part_serializer = tabular_part_model.get_serializer_class(action=self.action)
        tabular_part_filter = tabular_part_model.get_filterset_class()
        filter_qs = tabular_part_filter(  # noqa
            queryset=tabular_part_model.get_queryset(request).filter(owner=instance), request=request).qs
        field_keys = utils.get_field_keys(request, tabular_part_model)
        if field_keys:
            filter_qs = filter_qs.order_by(*field_keys)
        else:
            filter_qs = filter_qs.order_by('created_at')
        return Response(data=tabular_part_serializer(filter_qs, many=True).data, status=status.HTTP_200_OK)

    def paginate_queryset(self, queryset):
        data = super().paginate_queryset(queryset)
        keys = [f"locked_doc__{i.id}" for i in data]
        result = cache.get_many(keys)
        for each in data:
            each.locked = result.get(f"locked_doc__{each.id}", None)
        return data


class PlanOfCharacteristicViewSet(BaseCatalogViewSet):
    model = models.PlanOfCharacteristic


@csrf_exempt
def import_user_data(request):
    data = json.loads(request.body)
    if data['token'] == IMPORT_DATA_TOKEN:
        load_users(data['users'])
        load_organizations(data['organizations'])
        load_profiles(data['profiles'])
        wtls = data.get('wtl', None)
        if wtls:
            load_wtl(data['wtl'])
        return JsonResponse(data={'status': 'ok'}, status=200, safe=False)
    return JsonResponse(data={'status': 'forbidden'}, status=403, safe=False)


class GetFilePath(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        query_params = request.query_params
        file_id = query_params.get('id')
        not_found_response = Response(status=status.HTTP_404_NOT_FOUND)
        if not file_id or not isinstance(file_id, str):
            return not_found_response
        try:
            file = models.File.objects.get(pk=file_id, is_active=True)
        except ObjectDoesNotExist:
            return not_found_response
        file_path = file.upload.path
        data = {"path": file_path, "filename": f"{file.name}.{file.extension}"}
        if file.get_detail_permission(request):
            return Response(data)
        target = query_params.get('target', '')
        if target == 'chat_attachments' and utils.check_chat_attachments(request):
            return Response(data)
        obj_id = query_params.get('obj')
        if not obj_id or not isinstance(obj_id, str):
            return not_found_response
        try:
            obj = models.BaseModel.objects.super_get(obj_id)
        except ObjectDoesNotExist:
            return not_found_response
        if target == 'attachments':
            if obj.get_label() == 'chat.ChatModel':
                target_exist = obj.messages.filter(is_active=True, attachments=file_id).exists()
            else:
                target_exist = obj.attachments.filter(pk=file_id).exists()
        elif target == 'gallery':
            target_exist = obj.gallery.filter(file_id=file_id, is_active=True).exists()
        elif target == 'ckeditor':
            target_exist = obj.ckeditor_files.filter(is_active=True, file_id=file_id).exists()
        else:
            related_file = getattr(obj, target, None)
            if isinstance(related_file, models.File) and related_file.pk == file.pk:
                target_exist = True
            else:
                target_exist = False
        if not target_exist:
            return not_found_response
        if not obj.get_detail_permission(request):
            return not_found_response
        return Response(data)


class UpdateServerView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')
        try:
            from bkz3.settings import UPDATE_SERVER_PATH
        except ImportError:
            raise exceptions.ValidationError('На сервере не прописан путь к скрипту.')
        from bkz3.settings import DEBUG
        from django.http import HttpResponse
        from io import StringIO
        import subprocess
        if not DEBUG:
            raise exceptions.PermissionDenied("Дебаг отключен!")
        try:
            # Путь в явном виде.
            result = subprocess.check_output(
                ['/usr/bin/bash', UPDATE_SERVER_PATH],
            )
        except subprocess.CalledProcessError as ex:
            result = ex.__str__()
        except OSError as ex:
            result = ex.__str__()
        logs = StringIO()
        try:
            logs.write(result.decode('utf-8'))
        except AttributeError:
            logs.write(result)
        logs.seek(0)
        resp = HttpResponse(logs, content_type='application/txt')
        resp['Content-Disposition'] = 'attachment; filename="logs.txt"'
        return resp


class ClearCacheView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')
        cache.clear()
        return Response('ok')


class ClearSessionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')
        config = settings.SESSION_REDIS

        s_redis = redis.Redis(host=config.get('host'), port=config.get('port'), db=config.get('db'))
        s_redis.flushdb()
        return Response('ok')


class ClearCacheByPrefixView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')

        prefix = request.query_params.get('prefix', '').strip()
        if not prefix:
            return Response('Префикс не указан. Используйте ?prefix=название_префикса', status=status.HTTP_400_BAD_REQUEST)

        try:
            # Получаем Redis клиент для поиска ключей (аналогично ClearMessageKeysView)
            from django_redis import get_redis_connection
            cache_client = get_redis_connection("default")

            # Ищем все ключи по паттерну (аналогично socketio_redis.keys('messages*'))
            pattern = f'*{prefix}*'
            found_keys = cache_client.keys(pattern)

            # Удаляем найденные ключи напрямую через Redis клиент
            cleared_keys_count = 0
            for key in found_keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if cache_client.delete(key_str):
                    cleared_keys_count += 1

            return Response(f'Очищено ключей: {cleared_keys_count}', status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                f'Ошибка при очистке кэша: {str(e)}',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskKlassPauseView(APIView):
    """GET: выдать 10 минут паузы для task_klass.py (OLLAMA свободен). Только для pribka@mail.ru."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if getattr(request.user, 'email', None) != 'pribka@mail.ru':
            raise exceptions.PermissionDenied('Доступ запрещен!')
        pause_until = timezone.now() + timedelta(minutes=10)
        cache.set(common_utils.TASK_KLASS_PAUSE_UNTIL_KEY, pause_until.timestamp(), timeout=660)
        return Response({
            'pause_until': pause_until.isoformat(),
            'message': f'Пауза task_klass до {pause_until.isoformat()}',
        })


class RebuildHaystackIndexView(APIView):
    """Перестраивает индексы ElasticSearch, которые используются при подключении через Haystack."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')

        # Поддержка точечного обновления по конкретной модели: ?model=app_label.ModelName
        model_label = request.query_params.get('model')
        if model_label:
            call_command('update_index', model_label, remove=True)
            return Response(f'Индекс модели "{model_label}" обновлен')

        # Поддержка обновления по приложению: ?app=app_label
        app = request.query_params.get('app')
        if app:
            call_command('update_index', app, remove=True)
            return Response(f'Индексы приложения "{app}" обновлены')

        # Принудительное полное обновление: ?full=1
        full = request.query_params.get('full')
        if full:
            index_name = settings.HAYSTACK_CONNECTIONS.get('default', {}).get('INDEX_NAME')
            if not index_name:
                raise exceptions.ValidationError('HAYSTACK_CONNECTIONS["default"]["INDEX_NAME"] не найден')
            call_command('elastic', rebuild_index=index_name)
            call_command('update_index')
            return Response('Все индексы пересозданы')

        # Если параметров нет — показать простую HTML-форму с полями для модели и приложения
        html = (
            "<html><body style=\"font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif; padding:16px;\">"
            "<h3>Rebuild Haystack Index</h3>"
            # Model form
            "<form method=\"get\" action=\"\" style=\"margin-bottom:16px;\">"
            "<label for=\"model\">Модель (app_label.ModelName), например: catalogs.ContractorModel</label><br>"
            "<input id=\"model\" name=\"model\" type=\"text\" style=\"min-width:480px; padding:6px;\" placeholder=\"catalogs.ContractorModel\">"
            "<button type=\"submit\" style=\"margin-left:8px; padding:6px 12px;\">Обновить модель</button>"
            "</form>"
            # App form
            "<form method=\"get\" action=\"\" style=\"margin-bottom:16px;\">"
            "<label for=\"app\">Приложение (app_label), например: catalogs</label><br>"
            "<input id=\"app\" name=\"app\" type=\"text\" style=\"min-width:480px; padding:6px;\" placeholder=\"catalogs\">"
            "<button type=\"submit\" style=\"margin-left:8px; padding:6px 12px;\">Обновить приложение</button>"
            "</form>"
            # Full rebuild button
            "<div style=\"margin-top:8px;\">"
            "<a href=\"?full=1\" style=\"padding:6px 12px; display:inline-block;\">Пересоздать все индексы</a>"
            "</div>"
            "</body></html>"
        )
        return HttpResponse(html)


class DeleteFiltersStoreView(APIView):
    """Удаление FiltersStore по model и page_name для всех пользователей или только очистка table_settings."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')

        model = (request.query_params.get('model') or '').strip()
        page_name = (request.query_params.get('page_name') or '').strip()
        action = (request.query_params.get('action') or '').strip()

        if model and page_name:
            if action == 'clear_table_settings':
                qs = models.FiltersStore.objects.filter(model=model, page_name=page_name)
                count = 0
                for obj in qs:
                    obj.filters['table_settings'] = dict()
                    obj.save()
                    cache.delete(utils.get_cache_key_name(page_name, obj.author))
                    count += 1
                return HttpResponse(
                    f'<html><body style="font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif; padding:16px;">'
                    f'<p>Очищен ключ table_settings у записей FiltersStore: <strong>{count}</strong> '
                    f'(model={model!r}, page_name={page_name!r})</p>'
                    f'<a href="">Вернуться к форме</a></body></html>',
                    content_type='text/html; charset=utf-8',
                )
            else:
                qs = models.FiltersStore.objects.filter(model=model, page_name=page_name)
                for obj in qs:
                    cache.delete(utils.get_cache_key_name(page_name, obj.author))
                count = qs.count()
                qs.delete()
                return HttpResponse(
                    f'<html><body style="font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif; padding:16px;">'
                    f'<p>Удалено записей FiltersStore: <strong>{count}</strong> (model={model!r}, page_name={page_name!r})</p>'
                    f'<a href="">Вернуться к форме</a></body></html>',
                    content_type='text/html; charset=utf-8',
                )
        elif model:
            if action == 'clear_table_settings':
                qs = models.FiltersStore.objects.filter(model=model)
                count = 0
                for obj in qs:
                    obj.filters['table_settings'] = dict()
                    obj.save()
                    cache.delete(utils.get_cache_key_name(obj.page_name, obj.author))
                    count += 1
                return HttpResponse(
                    f'<html><body style="font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif; padding:16px;">'
                    f'<p>Очищен ключ table_settings у записей FiltersStore: <strong>{count}</strong> '
                    f'(model={model!r}, page_name=ALL)</p>'
                    f'<a href="">Вернуться к форме</a></body></html>',
                    content_type='text/html; charset=utf-8',
                )
            else:
                qs = models.FiltersStore.objects.filter(model=model)
                for obj in qs:
                    cache.delete(utils.get_cache_key_name(obj.page_name, obj.author))
                count = qs.count()
                qs.delete()
                return HttpResponse(
                    f'<html><body style="font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif; padding:16px;">'
                    f'<p>Удалено записей FiltersStore: <strong>{count}</strong> (model={model!r}, page_name=ALL)</p>'
                    f'<a href="">Вернуться к форме</a></body></html>',
                    content_type='text/html; charset=utf-8',
                )

        html = (
            "<html><body style=\"font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif; padding:16px;\">"
            "<h3>Delete FiltersStore</h3>"
            "<form method=\"get\" action=\"\" style=\"margin-bottom:16px;\">"
            "<label for=\"model\">model</label><br>"
            "<input id=\"model\" name=\"model\" type=\"text\" style=\"min-width:480px; padding:6px;\" placeholder=\"app_label.ModelName\"><br><br>"
            "<label for=\"page_name\">page_name</label><br>"
            "<input id=\"page_name\" name=\"page_name\" type=\"text\" style=\"min-width:480px; padding:6px;\" placeholder=\"page_name\"><br><br>"
            "<button type=\"submit\" name=\"action\" value=\"delete\" style=\"padding:6px 12px; margin-right:8px; background:#ba2121; color:white; border:none; cursor:pointer;\">Удалить FiltersStore полностью</button>"
            "<button type=\"submit\" name=\"action\" value=\"clear_table_settings\" style=\"padding:6px 12px; background:#417690; color:white; border:none; cursor:pointer;\">Очистить только table_settings</button>"
            "</form>"
            "</body></html>"
        )
        return HttpResponse(html)


class RebuildDSLIndexView(APIView):
    """Перестраивает индексы ElasticSearch, которые используются при подключении через elasticsearch-dsl.
    Настройки берутся из приложения search (indexes.py, documents.py)"""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied('Доступ запрещен!')

        try:
            # Гарантируем регистрацию всех Document'ов до rebuild
            import es_search.documents  # noqa: F401
            # Выполняем команду search_index --rebuild -f
            call_command('search_index', action='rebuild', force=True)
            return Response('ok')
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TableInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        profile = request.user.profile
        page_name = request.query_params.get('page_name')
        model = request.query_params.get('model')
        table_type = request.query_params.get('table_type')

        # Проверяем есть ли нужные настройки в кэше
        settings = cache.get(utils.get_cache_key_name(page_name, profile))

        if settings is not None:
            return Response(settings, status=status.HTTP_200_OK)

        # Пробуем получить сохраненные настройки из БД. Если их нет,
        # берем настройки по умолчанию для заданного page_name
        object = models.FiltersStore.objects.filter(
            author=profile,
            model=model,
            page_name=page_name
        ).first()

        if object:
            settings = object.filters.get('table_settings')
            if not utils.validate_settings(settings):
                settings = DEFAULT_TABLE_SETTINGS.get(table_type)
        else:
            settings = DEFAULT_TABLE_SETTINGS.get(table_type)

        if not settings:
            raise exceptions.ValidationError(
                'Не удалось получить настройки')

        return Response(settings, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        profile = request.user.profile
        page_name = request.data.get('page_name')
        model = request.data.get('model')
        table_type = request.data.get('table_type')

        if request.data.get('drop'):
            settings = DEFAULT_TABLE_SETTINGS.get(table_type)
            if not settings:
                raise exceptions.ValidationError(
                    'Не удалось получить настройки по умолчанию')
            object = models.FiltersStore.objects.filter(
                author=profile,
                model=model,
                page_name=page_name
            ).first()
            if object:
                object.filters['table_settings'] = dict()
                object.save()
                cache.delete(utils.get_cache_key_name(page_name, profile))
            return Response(
                    settings,
                    status=status.HTTP_200_OK
                )

        # Проверяем валидность полученных настроек
        settings = request.data.get('settings')
        if not utils.validate_settings(settings):
            raise exceptions.ValidationError('Данные не прошли проверку')

        # Создаем или перезаписываем настройки пользователя для таблицы
        object, created = models.FiltersStore.objects.get_or_create(
            author=profile,
            model=model,
            page_name=page_name,
        )
        if created:
            object.filters = {
                'table_settings': settings
            }
            object.save()
        else:
            object.filters['table_settings'] = settings
            object.save()

        cache.set(utils.get_cache_key_name(page_name, profile), settings)
        return Response(object.filters['table_settings'],
                        status=status.HTTP_200_OK)


class SetBalancesView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response('Пользователь не является администратором')

        import json

        from common.catalogs.models import ContractorModel

        from consolidation.models import (ContractorBalanceModel,
                                          ReportFormModel)

        try:
            report_form = ReportFormModel.objects.get(
                is_active=True,
                code='f2go'
            )
        except ReportFormModel.DoesNotExist:
            return ValidationError('Форма отчетности с кодом f2go не найдена')
        form_info = json.loads(report_form.form_info)
        balances = form_info.get('balance', {})
        lost_contractors = list()
        success_count = 0
        for key, value in balances.items():
            try:
                contractor = ContractorModel.objects.get(
                    is_active=True,
                    name=key
                )
            except ContractorModel.DoesNotExist:
                lost_contractors.append(key)
            else:
                balance, created = ContractorBalanceModel.objects.get_or_create(
                    contractor=contractor,
                    defaults={
                        'balance': value,
                        'year': 2023
                    }
                )
                if created:
                    success_count += 1
        if lost_contractors:
            file_name = 'lost_contractors_view.txt'
            with open(file_name, 'w', encoding='utf-8') as file:
                for org in lost_contractors:
                    file.write(org + "\n")

        return Response({
            'Всего записей найдено': len(balances),
            'Добавлено записей': success_count,
            'Не найдено клиентов': len(lost_contractors)
        })


class TestSentryApiView(APIView):

    def get(self, request, *args, **kwargs):
        raise exceptions.NotFound()
        d_b_z = 1 / 0
        return Response('ok')


class ObjectViewersList(APIView):
    def get(self, request, *args, **kwargs):
        related_object_id = request.query_params.get('related_object')
        if not related_object_id:
            return Response([])
        try:
            related_object = models.BaseModel.objects.super_get(pk=related_object_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response([])
        if not related_object.get_detail_permission(request):
            return Response([])
        object_viewers = related_object.viewers.filter(is_active=True).order_by(
            'user__last_name',
            'user__first_name',
            'user__middle_name',
        ).values_list('pk', flat=True)
        paginator = paginators.CustomPagination()
        page = paginator.paginate_queryset(object_viewers, request, self)
        data = CachedAppUserPreviewSerializer(page, many=True, context={'request': request, 'view': self}).data
        return paginator.get_paginated_response(data)

    def post(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            raise exceptions.PermissionDenied()
        data = request.data
        obj_id = data.get('obj')
        if not obj_id:
            raise exceptions.ValidationError('obj is required.')
        if isinstance(obj_id, str):
            try:
                obj = models.BaseModel.objects.get(pk=obj_id)
            except (ValidationError, ObjectDoesNotExist):
                raise exceptions.ValidationError('obj not found.')
            obj.cluts()
        elif isinstance(obj_id, list):
            obj_list = list(models.BaseModel.objects.filter(pk__in=obj_id).values_list('pk', flat=True))
            if obj_list:
                models.BaseModel.bulk_cluts(obj_list, request.user.profile.pk)
        return Response('ok')


class DesktopAppVersionView(APIView):

    def get(self, request, *args, **kwargs):
        obj = (
            models.DesktopApplicationVersionModel.objects.filter(is_active=True)
            .order_by('-created_at', '-id')
            .first()
        )
        if obj is None:
            return Response(
                {
                    'version': '',
                    'target_url': '',
                    'download_url': '',
                    'file_name': '',
                    'created_at': None,
                },
            )

        download_url = ''
        if obj.release_file:
            try:
                download_url = request.build_absolute_uri(obj.release_file.url)
            except Exception:
                download_url = ''

        return Response(
            {
                'version': obj.version,
                'target_url': obj.target_url,
                'download_url': download_url,
                'file_name': os.path.basename(obj.release_file.name)
                if obj.release_file
                else '',
                'created_at': obj.created_at,
            },
        )

