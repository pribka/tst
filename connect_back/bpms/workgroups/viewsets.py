import uuid
from json.decoder import JSONDecodeError

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_save
from django.db.models import Prefetch, Sum
from django.db import IntegrityError
from django.utils import timezone
from django_q.tasks import async_task
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext as _

from rest_framework import exceptions, generics, status
# from django.db.models import Count, Q
from rest_framework import exceptions as drf_exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from app_info.models import AppInfo
from bkz3.settings import (
    FILTER_BY_ORGANIZATIONS,
    GET_PROJECTS_AND_GROUPS_FROM_OTHER_BASE,
)
from bpms.favorites import models as f_models
from bpms.news.permissions import UpdateNewsPermission
from bpms.news.serializers import NewsUpdateSerializer
from bpms.tasks.models import TaskSprintModel, TaskModel, TaskExecutionTimeModel, TaskBudgetModel, TaskStatusModel
from bpms.tasks.serializers import TaskSprintListSerializer, StageMilestoneAboutSerializer
from bpms.tasks.utils import get_tasks_status_count

from bpms.bpms_common.serializers import AppUserSerializer
from common.views import BaseModelViewSet
from common.models import BaseModel, Events, File
from common.paginators import CustomPagination, NoTablePagination
from common.catalogs import serializers as catalog_serializers
from common.serializers import CachedBaseModelSerializer
from contractor_permissions.utils import check_contractor_permission
from users.models import ProfileModel, InviteModel
from users.serializers import InviteModelCreateSerializer, CachedAppUserSerializer, CachedAppUserPreviewSerializer
from users.utils import get_tree_departments_related_organizations, get_invite_url, check_update_organization_permission

from ..bpms_common.models import NewsModel
from ..bpms_common.serializers import EventSerializer, NewsLiteSerializer
from . import models, notifications, permissions, serializers, utils


class WorkGroupViewSet(BaseModelViewSet):
    model = models.WorkgroupModel
    pagination_class = NoTablePagination

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        data['tabs'] = [
            {
                'name': 'about',
                'menuName': "project" if instance.is_project else "group",
                'icon': "retweet",
                'onlyMobile': True
            },
            {
                'name': 'news',
                'menuName': "news",
                'icon': 'read'
            },
            {
                'name': 'tasks_sub',
                'menuName': "task",
                'mainPage': 'tasks',
                'icon': "profile",
                'onlyDesktop': True,
                'child': [
                    {
                        'name': 'tasks',
                        'menuName': "table"
                    },
                    {
                        'name': 'kanban',
                        'menuName': "kanban"
                    }
                ]
            },
            {
                'name': 'tasks',
                'menuName': "task",
                'onlyMobile': True
            },
            {
                'name': 'calendar',
                'menuName': "calendar",
                'icon': "profile"
            },
            {
                'name': 'sprint',
                'menuName': "sprints",
                'icon': "retweet"
            },
            {
                'name': 'analytics',
                'menuName': "analytics",
                'icon': "profile"
            },
            {
                'name': 'group_files',
                'menuName': "group_files",
                'icon': "files"
            }
        ]
        if instance.is_project:
            workgroup_code = 'project'
        else:
            workgroup_code = 'workgroup'
        try:
            data['tabs'] = AppInfo.objects.get(is_active=True, code=f'{workgroup_code}_tabs').metadata
        except AppInfo.DoesNotExist:
            pass
        except JSONDecodeError:
            pass
        if instance.with_chat:
            data['tabs'].append(
                {
                    "name": "chat_files",
                    "menuName": "chat_files",
                    "icon": "files",
                    "title": "Файлы чата"
                }
            )
        role_1c = request.user.profile.c1_roles.filter(is_active=True).first()
        if role_1c:
            try:
                data['tabs'] = AppInfo.objects.get(is_active=True, code=f'{workgroup_code}_tabs__1c_role__{role_1c.pk}')
            except AppInfo.DoesNotExist:
                pass
        return Response(data)

    def list(self, request, *args, **kwargs):
        queryset = utils.get_workgroup_queryset(request)
        helpdesk_only = request.query_params.get('is_helpdesk')
        if helpdesk_only == 'true':
            queryset = queryset.filter(workgroup_type__code='helpdesk')
        
        approved_status = models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        founder_role = models.WorkgroupMembershipRole.objects.get(code="FOUNDER")
        
        approved_members_prefetch = Prefetch(
            'workgroupmembersmodel_set',
            queryset=models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                membership_request_status=approved_status
            ).select_related(
                'member__user',
                'member__avatar',
                'member__current_contractor',
                'membership_role',
                'membership_request_status'
            ),
            to_attr='approved_members'
        )
        
        founder_prefetch = Prefetch(
            'workgroupmembersmodel_set',
            queryset=models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                membership_request_status=approved_status,
                membership_role=founder_role
            ).select_related(
                'member__user',
                'member__avatar',
                'member__current_contractor',
                'membership_role',
                'membership_request_status'
            ),
            to_attr='founder_member'
        )
        
        queryset = queryset.select_related(
            'workgroup_logo',
            'organization'
        ).prefetch_related(
            approved_members_prefetch,
            founder_prefetch,
        )
        
        page = self.paginate_queryset(queryset)
        # profile, _ = f_models.FavoritesModel.objects.get_or_create(
        #     profile=request.user.profile
        # )
        serializer = serializers.WorkgroupListSerializer(
            page, many=True,
            context={
                'request': request,
                # 'favorites': profile.favorites,
                'approved_status': approved_status
            }
        )
        paginated_response = self.get_paginated_response(serializer.data)
        return Response(paginated_response.data, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):

        if GET_PROJECTS_AND_GROUPS_FROM_OTHER_BASE:
            return Response('Группы и проекты создаются во внешней информационной системе',
                            status=status.HTTP_400_BAD_REQUEST)
        user = request.user.profile
        if FILTER_BY_ORGANIZATIONS:
            contractor_id = request.data.get('organization')
            im_director = user.contractor_profile.filter(director=True, contractor_id=contractor_id).exists()
            try:
                check_contractor_permission(user.pk, contractor_id, 'create_workgroup', None)
            except exceptions.PermissionDenied:
                contractor_permission = False
            else:
                contractor_permission = True

            if not (im_director or user.can_create_workgroups or contractor_permission):
                raise exceptions.PermissionDenied({"message": "Вы не можете создавать команды и проекты."})
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            members = request.data.get('members')
            if members and not isinstance(members, dict):
                raise drf_exceptions.ValidationError({"members": "Ожидается словарь"})
            if members:
                profiles = members.get('profile_id')
                if profiles:
                    profiles = set(profiles)
                    profiles.discard(str(user.pk))
                    utils.set_workgroup_members(instance, profiles)
            # создание проекта по шаблону
            use_template = request.data.pop('use_template', False)
            template = request.data.pop('template', None)
            if use_template:
                if template is None:
                    raise drf_exceptions.ValidationError('There is no template.')
                try:
                    template = models.ProjectTemplateModel.objects.get(id=template)
                except models.ProjectTemplateModel.DoesNotExist:
                    raise drf_exceptions.ValidationError('Template not found.')

                utils.create_project_from_template(instance, template)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_418_IM_A_TEAPOT)

    @action(methods=["post", ], detail=True, url_name="approve_invite", url_path="approve_invite")
    def approve_invite(self, request, pk=None):
        project = self.get_object()
        organization_member_id = request.data.get('organization_member_id', None)
        status_code = request.data.get('status', None)
        if not status_code:
            raise drf_exceptions.ValidationError(
                'Статус организации-участника не передан'
            )
        
        try:
            member_organization_status = models.WorkgroupMemberOrganizationStatusModel.objects.get(
                code=status_code, 
                is_active=True
                )
        except models.WorkgroupMemberOrganizationStatusModel.DoesNotExist:
            raise drf_exceptions.ValidationError(
                'Статус организации-участника не найден'
            )
        
        if not organization_member_id:
            raise drf_exceptions.ValidationError(
                'Организация-участник не указана'
            )
        
        try:
            organization_member = models.WorkgroupMemberOrganizationModel.objects.get(
                    pk=organization_member_id,
                    work_group=project, 
                    is_active=True
                    )
        except models.WorkgroupMemberOrganizationModel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            organization_member.status = member_organization_status
            organization_member.save(update_fields=('status_id',))
            
            if status_code == 'added':
                coordinator = models.WorkgroupMembersModel.objects.filter(
                    is_active=True, 
                    work_group=project, 
                    membership_role__code='ORG-COORDINATOR',
                    member_organization=organization_member
                    ).first()
                if coordinator:
                    membership_request_status = models.WorkgroupMembershipStatus.objects.get(code='APPROVED')
                    coordinator.membership_request_status = membership_request_status
                    coordinator.save(update_fields=('membership_request_status',))

        return Response(                
            data=serializers.MemberOrganizationsSerializer(organization_member).data,
            status=status.HTTP_200_OK
        )

    @action(methods=["get", ], detail=True, url_name="my_role", url_path="my_role")
    def get_my_role(self, request, pk=None):
        work_group = self.get_object()
        queryset = models.WorkgroupMembersModel.objects.filter(
            is_active=True,
            member=request.user.profile,
            work_group=work_group,
            membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        )
        if queryset.exists():
            return Response(
                data=serializers.WorkgroupMembershipSerializer(queryset, many=True).data,
                status=status.HTTP_200_OK
            )
        else:
            profile = request.user.profile
            if profile.is_support:
                data = [
                    {
                        "id": "042798bc-6c45-11ef-944f-4216f3de51df",
                        "membership_role": {"name": "Участник", "code": "MEMBER"},
                        "membership_request_status": {"name": "Одобрено", "code": "APPROVED"},
                        "member_visible": False,
                        "member": AppUserSerializer(profile).data,
                    }
                ]
                return Response(data=data)
            else:
                return Response(
                    data=[{"membership_role": "not_member_of_the_workgroup"}], status=status.HTTP_200_OK
                )

    @action(methods=["post", ], detail=True, url_name="join_workgroups", url_path="join_workgroups")
    def join_workgroups(self, request, pk=None):
        """Самодобавление в рабочую группу."""
        workgroup: models.WorkgroupModel = self.get_object()
        member_visibility = request.data.get("member_visible")
        user = request.user.profile
        member, created = models.WorkgroupMembersModel.objects.update_or_create(
            member=user,
            work_group=workgroup,
            defaults={"membership_role": models.WorkgroupMembershipRole.objects.get(code="MEMBER"),
                      "membership_request_status": models.WorkgroupMembershipStatus.objects.get(code="APPROVED"),
                      # "member_visible": member_visibility, TODO отключил этот атрибут до выяснения его необходимости.
                      "is_active": True,
                      },
        )
        async_task(notifications.notify_about_new_workgroup_member, workgroup, user, user)
        async_task(utils.create_workgroup_chat_members, str(workgroup.pk), (str(user.pk),))
        serializer = serializers.WorkgroupMembershipSerializer(member).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["delete", ], detail=True,
            url_name="delete_workgroups_member", url_path="delete_workgroups_member",
            permission_classes=(permissions.WorkgroupModerator,),
            )
    def delete_workgroups_member(self, request, pk=None):
        #  удаление участника студ клуба
        membership_id = request.data.get("membership_id")
        membership = models.WorkgroupMembersModel.objects.get(pk=membership_id, is_active=True)
        membership.is_active = False
        membership.save()
        workgroups = self.get_object()
        members = models.WorkgroupMembersModel.objects.filter(work_group=workgroups, is_active=True)
        async_task(utils.delete_workgroup_chat_members, workgroups, (membership.member_id,))
        serializer = serializers.WorkgroupMembershipSerializer(members, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=True,
            url_name="get_workgroups_members", url_path="get_workgroups_members")
    def get_workgroups_members(self, request, pk=None):
        workgroups = self.get_object()
        members = models.WorkgroupMembersModel.objects.filter(
            is_active=True,
            work_group=workgroups,
            membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        ).order_by('member__user__last_name', 'member__user__first_name')
        paginator = CustomPagination()
        page = paginator.paginate_queryset(members, request, self)
        serializer = serializers.WorkgroupMembershipSerializer(page, many=True, context={"request": request})
        response = paginator.get_paginated_response(serializer.data)
        return response

    @action(methods=["get", ], detail=True,
            url_name="get_workgroups_members_short", url_path="get_workgroups_members_short")
    def get_workgroups_members_short(self, request, pk=None):
        workgroups = self.get_object()
        members = models.WorkgroupMembersModel.objects.filter(
            is_active=True,
            work_group=workgroups,
            membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        )
        qs = ProfileModel.objects.filter(
            pk__in=members.values_list('member_id', flat=True),
            is_active=True,
            temporary_blocked=False
        ).order_by("user__last_name", "user__first_name", "user__middle_name").values_list('pk', flat=True)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, self)
        page_ids = list(page)
        data = CachedAppUserPreviewSerializer(page_ids, many=True).data
        return paginator.get_paginated_response(data)

    @action(methods=["delete"], detail=True,
            url_name="leave_workgroups", url_path="leave_workgroups")
    def leave_workgroups(self, request, pk=None):
        workgroups = self.get_object()
        user = request.user.profile
        try:
            member = models.WorkgroupMembersModel.objects.get(member=user, work_group=workgroups,
                                                              is_active=True)
        except models.WorkgroupMembersModel.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        member.is_active = False
        member.save()
        async_task(notifications.notify_about_remove_from_workgroup_member, workgroups, user)
        async_task(utils.delete_workgroup_chat_members, workgroups, (user.pk,))
        members = models.WorkgroupMembersModel.objects.filter(work_group=workgroups, is_active=True)
        serializer = serializers.WorkgroupMembershipSerializer(members, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["put", ], detail=True,
            url_path="change_member_role", url_name="change_member_role",
            permission_classes=(permissions.WorkgroupModerator,)
            )
    def change_member_role(self, request, pk=None):
        member_id = request.data.get("membership_id")
        unset = request.data.get("unset", False)
        try:
            member: models.WorkgroupMembersModel = models.WorkgroupMembersModel.objects.get(pk=member_id)
            role_code = 'MEMBER' if unset else 'MODERATOR'
            member.membership_role = models.WorkgroupMembershipRole.objects.get(code=role_code)
            member.save()
        except:
            return Response(data="wrong id", status=status.HTTP_400_BAD_REQUEST)
        workgroup = member.work_group
        if workgroup.with_chat and workgroup.linked_chat:
            chat = workgroup.linked_chat
            chat_member = chat.members.filter(user=member.member, is_active=True).first()
            if chat_member:
                is_moderator = not unset
                if not chat_member.is_moderator == is_moderator:
                    chat_member.is_moderator = is_moderator
                    chat_member.save()
                    utils.send_socketio_about_update_chat_member(chat, ((chat_member.user.pk, is_moderator,),))
        return Response(data=serializers.WorkgroupMembershipSerializer(member).data, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='assign_founder', permission_classes=(IsAuthenticated,))
    def assign_founder(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_assign_founder_permission(request):
            raise drf_exceptions.PermissionDenied()
        member_id = request.data.get('membership_id')
        try:
            member = models.WorkgroupMembersModel.objects.get(pk=member_id, work_group=instance)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Участник не найден')
        role_moderator = models.WorkgroupMembershipRole.objects.get(code='MODERATOR')
        role_founder = models.WorkgroupMembershipRole.objects.get(code='FOUNDER')
        old_founders = list(
            models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                membership_role__code='FOUNDER',
                membership_request_status__code='APPROVED',
                work_group=instance,
            )
        )
        with transaction.atomic():
            for each in old_founders:
                each.membership_role = role_moderator
                each.save()
            member.membership_role = role_founder
            member.save()
            if instance.with_chat and instance.linked_chat:
                chat = instance.linked_chat
                chat_author = chat.chat_author
                if not chat_author == member.member:
                    if not chat.members.filter(user=member.member, is_active=True).exists():
                        utils.create_workgroup_chat_members(instance.pk, (member.member.pk,))
                    chat.chat_author = member.member
                    chat.save()
                    chat_author_member = chat.members.filter(user=chat_author).first()
                    chat_author_member.is_moderator = True
                    chat_author_member.save()
        utils.send_socketio_about_new_chat_author(chat)
        utils.send_socketio_about_update_chat_member(chat, ((chat_author.pk, True),))
        return Response(data=serializers.WorkgroupMembershipSerializer(member).data, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='default_visors',)
    def get_default_visors(self, request, *args, **kwargs):
        workgroup = self.get_object()
        members = models.WorkgroupMembersModel.objects.filter(
            is_active=True,
            work_group=workgroup,
            default_visor=True,
            membership_request_status__code="APPROVED"
        ).values_list('member', flat=True)
        serializer = CachedAppUserSerializer(members, many=True)
        return Response(serializer.data)

    @action(
        methods=['put', ],
        detail=True,
        url_path='set_default_visor',
        permission_classes=(permissions.WorkgroupModerator,)
    )
    def change_default_visor(self, request, pk=None):
        member_id = request.data.get("member")
        try:
            member = models.WorkgroupMembersModel.objects.get(pk=member_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError('Участник не найден')
        serializer = serializers.WorkgroupMembershipUpdateDefaultVisorSerializer(
            instance=member,
            data=request.data,
            context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        s_data = serializers.WorkgroupMembershipSerializer(member).data
        return Response(s_data)

    @action(methods=["put", ], detail=True,
            url_name="upload_gallery_files", url_path="upload_gallery_files"
            )
    def upload_gallery_files(self, request, pk=None):
        workgroups: models.WorkgroupModel = self.get_object()
        files = File.objects.filter(pk__in=request.data.get("files"))
        gallery_files = [workgroups.gallery_files.add(file) for file in files]
        serializer = serializers.WorkgroupGallerySerializer(workgroups).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["delete", ], detail=True,
            url_path="delete_gallery_files", url_name="delete_gallery_files",
            )
    def delete_gallery_files(self, request, pk=None):
        workgroups: models.WorkgroupModel = self.get_object()
        files = File.objects.filter(pk__in=request.data.get("files"))
        gallery_files = [workgroups.gallery_files.remove(file) for file in files]
        serializer = serializers.WorkgroupGallerySerializer(workgroups).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=True,
            url_name="get_gallery_files", url_path="get_gallery_files")
    def get_gallery_files(self, request, pk=None):
        workgroups: models.WorkgroupModel = self.get_object()
        if not workgroups.public_or_private or models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                member=request.user.profile,
                work_group=workgroups,
                membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        ).exists():
            return Response(
                data=serializers.WorkgroupGallerySerializer(workgroups).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                data="not a workgroup member",
                status=status.HTTP_403_FORBIDDEN
            )

    @action(methods=["put", ], detail=True,
            url_name="upload_attachments", url_path="upload_attachments"
            )
    def upload_attachments(self, request, pk=None):
        workgroups: models.WorkgroupModel = self.get_object()
        files = File.objects.filter(pk__in=request.data.get("files"))
        attachments = [workgroups.attachments.add(file) for file in files]
        serializer = serializers.WorkgroupAttachmentsSerializer(workgroups).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["delete", ], detail=True,
            url_path="delete_attachments", url_name="delete_attachments",
            )
    def delete_attachments(self, request, pk=None):
        workgroups: models.WorkgroupModel = self.get_object()
        files = File.objects.filter(pk__in=request.data.get("files"))
        attachments = [workgroups.attachments.remove(file) for file in files]
        serializer = serializers.WorkgroupAttachmentsSerializer(workgroups).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    @action(methods=["get", ], detail=True,
            url_name="get_attachments", url_path="get_attachments")
    def get_attachments(self, request, pk=None):
        workgroups: models.WorkgroupModel = self.get_object()
        if not workgroups.public_or_private or models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                member=request.user.profile,
                work_group=workgroups,
                membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        ).exists():
            return Response(
                data=serializers.WorkgroupAttachmentsSerializer(workgroups).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                data="not a workgroup member",
                status=status.HTTP_403_FORBIDDEN)

    @action(methods=["post", ], detail=True, url_name="send_invitations", url_path="send_invitations")
    def send_invitations(self, request, pk=None):
        # Уведомление приглашение профилям на вступление в студ клуб
        workgroup = self.get_object()
        profiles = request.data.get("profile_id")  # Массивом уиды профилей
        with transaction.atomic():
            members = utils.set_workgroup_members(workgroup, set(profiles))
        serialized_data = serializers.WorkgroupMembershipSerializer(members, many=True).data
        return Response(data=serialized_data, status=status.HTTP_200_OK)

    @action(methods=["patch", ], detail=True, url_name="add_chat", url_path="add_chat")
    def add_chat(self, request, pk=None):
        """Добавление чата"""
        project = self.get_object()
        if not project.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if project.is_finished:
            raise drf_exceptions.ValidationError(_('Проект завершён'))
        project.linked_chat_id = request.data['chat_uid']
        project.with_chat = True
        project.save()
        return Response(data={"linked_chat": request.data['chat_uid']}, status=status.HTTP_200_OK)

    @action(methods=["patch", ], detail=True, url_name="add_new_chat", url_path="add_new_chat")
    def add_new_chat(self, request, pk=None):
        """Добавление чата"""
        project = self.get_object()
        if not project.get_update_permission(request):
            raise drf_exceptions.PermissionDenied()
        if project.is_finished:
            raise drf_exceptions.ValidationError(_('Проект завершён'))
        project.with_chat = request.data['with_chat']
        project.save()
        return Response(data={"chat_uid": project.linked_chat.chat_uid}, status=status.HTTP_200_OK)

    @action(methods=["patch", ], detail=True, url_name="add_finished_date", url_path="add_finished_date")
    def add_finished_date(self, request, pk=None):
        """Добавление к проекту даты завершения"""
        project = self.get_object()
        is_finished = bool(request.data.get('finished_date'))
        project.is_finished = is_finished
        project.save()
        if is_finished:
            text = f'Проект "{project.name}" завершён.'
        else:
            text = f'Проект "{project.name}" возобновлён.'
        async_task(utils.send_message_chat_project, str(project.pk), text)
        return Response(data={"finished_date": request.data['finished_date']}, status=status.HTTP_200_OK)

    @action(methods=('post',), detail=True, url_path='delete', permission_classes=(IsAuthenticated,))
    def delete_workgroup(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.get_update_permission(request):
            raise exceptions.ValidationError(
                'Недостаточно прав для выполнения данного действия.'
            )
        with transaction.atomic():
            invest_projects = instance.invest_projects_info.all()
            instance.is_active = False
            instance.save(update_fields=('is_active',))
            for each in invest_projects:
                each.project = None
                each.save(update_fields=('project',))
        if instance.is_project:
            text = f'Проект "{instance.name}" удалён.'
        else:
            text = f'Команда "{instance.name}" удалена.'
        async_task(utils.send_message_chat_project, str(instance.pk), text)
        return Response(status=status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='action_info', permission_classes=(IsAuthenticated,))
    def get_action_info(self, request, *args, **kwargs):
        instance = self.get_object()
        actions = dict()
        if instance.get_update_permission(request):
            actions = {
                "add_news": {
                    "availability": True
                },
                "add_event": {
                    "availability": True
                },
                "edit": {
                    "availability": True
                },
                "create_file": {
                    "availability": True
                },
                "add_member": {
                    "availability": True
                },
                "add_sprint": {
                    "availability": True
                },
                "delete": {
                    "availability": True
                },
                "create_task": {
                    "availability": True
                },
                "set_default_visors": {
                    "availability": True
                }
            }
            if instance.is_finished:
                if instance.with_chat and instance.linked_chat:
                    actions['open_chat'] = {'availability': True}
            else:
                if not instance.with_chat or not instance.linked_chat:
                    actions['create_chat'] = {"availability": True}
                else:
                    actions['open_chat'] = {"availability": True}
            if instance.is_project:
                actions['project_finish'] = {"availability": True}
        elif instance.get_detail_permission(request):
            actions["create_task"] = {"availability": True}
            actions["add_event"] = {"availability": True}
            actions["create_file"] = {"availability": True}
            if instance.with_chat and instance.linked_chat:
                actions["open_chat"] = {"availability": True}
        if instance.get_assign_founder_permission(request):
            actions['assign_founder'] = {'availability': True}
        data = {"actions": actions}
        return Response(data)

    @action(methods=('get',), detail=False, url_path='table_info')
    def get_table_info(self, request, *args, **kwargs):
        # workgroup_type принимает значение 'group' или 'project':
        workgroup_type = request.query_params.get('type', 'group')
        if workgroup_type == 'project':
            columns = [
                {
                    "dataIndex": 'name',
                    "title": 'Название',
                    "key": 'name',
                    "width": 360,
                    "sorter": True,
                    "fixed": True,
                    "scopedSlots": {"customRender": 'name'}
                },
                {
                    "dataIndex": 'date_start_plan',
                    "title": 'Дата начала',
                    "key": 'date_start_plan',
                    "sorter": True,
                    "width": 240,
                    "scopedSlots": {"customRender": 'date_start_plan'}
                },
                {
                    "dataIndex": 'dead_line',
                    "title": 'Крайний срок',
                    "key": 'dead_line',
                    "sorter": True,
                    "width": 180,
                    "scopedSlots": {"customRender": 'dead_line'}
                },
                {
                    "dataIndex": 'founder',
                    "title": 'Участники',
                    "key": 'founder',
                    "width": 200,
                    "scopedSlots": {"customRender": 'founder'}
                },
                {
                    "dataIndex": 'tasks',
                    "title": 'Эффективность',
                    "key": 'tasks',
                    "width": 250,
                    "scopedSlots": {"customRender": 'tasks'}
                },
                {
                    "dataIndex": 'finished',
                    "title": 'Статус',
                    "key": 'finished',
                    "width": 110,
                    "scopedSlots": {"customRender": 'finished'}
                },
                {
                    "dataIndex": 'public_or_private',
                    "title": 'Тип приватности',
                    "key": 'public_or_private',
                    "sorter": True,
                    "width": 150,
                    "scopedSlots": {"customRender": 'public_or_private'}
                }
            ]
        else:
            columns = [
                {
                    "dataIndex": 'name',
                    "title": 'Название',
                    "key": 'name',
                    "width": 360,
                    "fixed": True,
                    "sorter": True,
                    "scopedSlots": {"customRender": 'name'}
                },
                # {
                #     "dataIndex": 'created_at',
                #     "title": 'Дата основания',
                #     "key": 'created_at',
                #     "sorter": True,
                #     "width": 240,
                #     "scopedSlots": {"customRender": 'dead_line'}
                # },
                # {
                #     "dataIndex": 'add_file_at',
                #     "title": 'Дата добавления файла',
                #     "key": 'add_file_at',
                #     "sorter": True,
                #     "width": 240,
                #     "scopedSlots": {"customRender": 'dead_line'}
                # },
                {
                    "dataIndex": 'updated_at',
                    "title": 'Дата обновления',
                    "key": 'updated_at',
                    "sorter": True,
                    "width": 240,
                    "scopedSlots": {"customRender": 'dead_line'}
                },
                {
                    "dataIndex": 'founder',
                    "title": 'Участники',
                    "key": 'founder',
                    "width": 200,
                    "scopedSlots": {"customRender": 'founder'}
                },
                {
                    "dataIndex": 'tasks',
                    "title": 'Всего задач',
                    "key": 'tasks',
                    "width": 150,
                    "scopedSlots": {"customRender": 'tasks_stat'}
                },
                {
                    "dataIndex": 'public_or_private',
                    "title": 'Тип приватности',
                    "key": 'public_or_private',
                    "sorter": True,
                    "width": 150,
                    "scopedSlots": {"customRender": 'public_or_private'}
                }
            ]
        data = {"columns": columns}
        try:
            data = AppInfo.objects.get(is_active=True, code=f"workgroups_{workgroup_type}_table_info").metadata
        except AppInfo.DoesNotExist:
            pass
        return Response(data)

    @action(methods=('get',), detail=False, url_path='points')
    def get_points(self, request, *args, **kwargs):
        """Фильтрация списка проектов по геолокации на карте.
        Сначала получает queryset аналогично def list, затем фильтрует его по переданным координатам"""
        queryset = utils.get_workgroup_queryset(request)

        query_params = request.query_params
        lat_gte = query_params.get('lat__gte', 0)
        lat_lte = query_params.get('lat__lte', 0)
        lon_gte = query_params.get('lon__gte', 0)
        lon_lte = query_params.get('lon__lte', 0)
        queryset = queryset.filter(
            is_active=True,
            location_points__lat__gte=lat_gte,
            location_points__lat__lte=lat_lte,
            location_points__lon__gte=lon_gte,
            location_points__lon__lte=lon_lte,
        ).distinct()

        page = self.paginate_queryset(queryset)
        # profile, _ = f_models.FavoritesModel.objects.get_or_create(
        #     profile=request.user.profile
        # )
        serializer = serializers.WorkgroupListSerializer(
            page, many=True,
            context={
                'request': request,
                # 'favorites': profile.favorites
            }
        )
        paginated_response = self.get_paginated_response(serializer.data)
        return Response(paginated_response.data, status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='gantt_chart')
    def get_gantt_chart(self, request, *args, **kwargs):
        """Вывод проектов в формате для диаграммы Ганта https://docs.dhtmlx.com/
        Получает queryset аналогично def list."""
        queryset = utils.get_workgroup_queryset(request)
        queryset = queryset.filter(
            date_start_plan__isnull=False,
            dead_line__isnull=False,
            )
        page = self.paginate_queryset(queryset)
        serializer = serializers.WorkgroupGanttChartSerializer(page, many=True, context={'request': request})
        paginated_response = self.get_paginated_response(serializer.data)
        return Response(paginated_response.data, status.HTTP_200_OK)

    @action(methods=('get',), detail=False, url_path='list_short')
    def list_short(self, request, *args, **kwargs):
        """Список команд и проектов для селекта с логотипом, используя кэшированный WorkgroupNameLogoSerializer"""
        queryset = utils.get_workgroup_queryset(request)
        qs = queryset.values_list('pk', flat=True)
        page = self.paginate_queryset(qs)
        page_ids = list(page)
        
        data = CachedBaseModelSerializer(
            page_ids,
            many=True,
            serializer_class=serializers.WorkgroupNameLogoSerializer,
            context={'request': request}
        ).data
        paginated_response = self.get_paginated_response(data)
        return Response(paginated_response.data, status.HTTP_200_OK)

    @action(methods=('get',), detail=True, url_path='about/task_count')
    def get_about_task_count(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = TaskModel.objects.filter(is_active=True, project=instance, task_type='task')
        count = queryset.count()
        status_count_data = get_tasks_status_count(queryset)
        data = {
            'count': count,
            'status_count': status_count_data
        }
        tasks_id = queryset.values_list('pk', flat=True)
        time_fact = TaskExecutionTimeModel.objects.filter(
            is_active=True,
            task__in=tasks_id,
        ).aggregate(hours_sum=Sum('hours'))['hours_sum']
        if time_fact is None:
            time_fact = 0
        time_plan = queryset.aggregate(time_plan=Sum('execution_time_plan'))['time_plan']
        if time_plan is None:
            time_plan = 0
        time_difference = time_fact - time_plan
        data['time'] = [
            {
                'label': 'Плановые общие трудозатраты',
                'value': time_plan,
            },
            {
                'label': 'Фактические трудозатраты',
                'value': time_fact,
            },
            {
                'label': 'Отклонение',
                'value': time_difference,
            },
        ]

        task_statuses_qs = TaskStatusModel.objects.filter(
            is_active=True,
            task_status_type__task_type__code='task',
        ).values_list('code', 'name')
        task_statuses = dict(task_statuses_qs)
        task_statuses['overdue'] = 'Просрочена'
        data['labels'] = task_statuses
        return Response(data)

    @action(methods=('get',), detail=True, url_path='about/stages')
    def get_about_stages(self, request, *args, **kwargs):
        instance = self.get_object()
        stages_qs = TaskModel.objects.filter(
            is_active=True,
            project=instance,
            task_type='stage'
        ).order_by('date_start_plan')
        count = stages_qs.count()
        status_list = []
        status_data = {
            'stage_planned': 0,
            'stage_open': 0,
            'stage_completed': 0,
            'stage_overdue': 0,
        }
        for each in stages_qs:
            stage_status = each.stage_status
            if stage_status not in status_list:
                status_list.append(stage_status)
                status_data[stage_status] = 1
            else:
                status_data[stage_status] += 1
        stage_statuses_qs = TaskStatusModel.objects.filter(
            is_active=True,
            task_status_type__task_type__code='stage'
        ).distinct().values_list('code', 'name')
        stage_statuses = dict(stage_statuses_qs)
        data = {
            'count': count,
            'labels': stage_statuses,
            'status_count': status_data,
            'stages': StageMilestoneAboutSerializer(stages_qs, many=True).data
        }
        return Response(data)

    @action(methods=('get',), detail=True, url_path='about/milestones')
    def get_about_milestone_count(self, request, *args, **kwargs):
        instance = self.get_object()
        milestone_qs = TaskModel.objects.filter(
            is_active=True,
            project=instance,
            task_type='milestone',
        )
        count = milestone_qs.count()
        status_list = []
        status_data = {
            'milestone_planned': 0,
            'milestone_passed': 0,
            'milestone_overdue': 0,
        }
        for each in milestone_qs:
            milestone_status = each.milestone_status
            if milestone_status not in status_list:
                status_list.append(milestone_status)
                status_data[milestone_status] = 1
            else:
                status_data[milestone_status] += 1
        milestone_statuses_qs = TaskStatusModel.objects.filter(
            is_active=True,
            task_status_type__task_type__code='milestone',
        ).distinct().values_list('code', 'name')
        milestone_statuses = dict(milestone_statuses_qs)
        data = {
            'count': count,
            'labels': milestone_statuses,
            'status_count': status_data,
            'milestones': StageMilestoneAboutSerializer(milestone_qs, many=True).data
        }
        return Response(data)

    @action(methods=('get',), detail=True, url_path='about/funds')
    def get_about_amount(self, request, *args, **kwargs):
        instance = self.get_object()
        task_qs = TaskModel.objects.filter(
            is_active=True,
            project=instance,
            task_type='task'
        )
        amount_plan_sum = task_qs.aggregate(amount_plan_sum=Sum('funds'))['amount_plan_sum']
        if amount_plan_sum is None:
            amount_plan_sum = 0
        tasks_id = task_qs.values_list('pk', flat=True)
        amount_fact_sum = TaskBudgetModel.objects.filter(
            task__in=tasks_id,
            is_active=True
        ).aggregate(amount_fact_sum=Sum('amount'))['amount_fact_sum']
        if amount_fact_sum is None:
            amount_fact_sum = 0
        data = {
            'funds': [
                {
                    'label': 'Плановая стоимость',
                    'value': amount_plan_sum,
                },
                {
                    'label': 'Фактическая стоимость',
                    'value': amount_fact_sum,
                },
                {
                    'label': 'Отклонение',
                    'value': amount_fact_sum - amount_plan_sum,
                }
            ]
        }
        return Response(data)

    @action(methods=('get',), detail=True, url_path='about/progress')
    def get_about_progress(self, request, *args, **kwargs):
        instance = self.get_object()
        progress = instance.progress
        progress = progress * 100
        progress_plan = 100
        data = {
            'progress': [
                {
                    'label': 'Запланированный прогресс',
                    'value': progress_plan
                },
                {
                    'label': 'Актуальный прогресс',
                    'value': progress,
                },
                {
                    'label': 'Отставание',
                    'value': progress - progress_plan
                }
            ]
        }
        return Response(data)

    @action(methods=('post', 'put'), detail=True, url_path='add/organization')
    def add_organization(self, request, *args, **kwargs):
        MANAGER_ROLES = set(['FOUNDER', 'MODERATOR'])
        member_organization = None
        project = self.get_object()
        employees = request.data.get('employees', [])

        if not employees or not isinstance(employees, list):
            raise drf_exceptions.ValidationError(
                'Список сотрудников пуст или некорректен'
            )

        if request.method == 'POST':
            has_org_coordinator = any(item['role'] == 'ORG-COORDINATOR' for item in employees)
            if not has_org_coordinator:
                raise drf_exceptions.ValidationError(
                    'Не указан координатор организации'
                )
            serializer = serializers.WorkgroupMemberOrganizationModelCreateSerializer(
                data={
                    'organization': request.data.get('organization', None),
                    'role': request.data.get('role', None),
                    'work_group': project,
                    'status': 'invited'
                }
            )
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                member_organization = serializer.save()
                membership_request_status = models.WorkgroupMembershipStatus.objects.get(code='AWAITS_VERIFICATION')
                for item in employees:
                    membership_role = models.WorkgroupMembershipRole.objects.get(
                        is_active=True,
                        code=item['role']
                    )
                    member, created = models.WorkgroupMembersModel.objects.get_or_create(
                        is_active=True,
                        member_id=item['employee'],
                        work_group=project,
                        defaults={
                            'membership_role': membership_role,
                            'membership_request_status': membership_request_status,
                            'member_visible': True,
                            'member_organization': member_organization
                        }
                    )
                    if not created and member.membership_role.code == 'ORG-COORDINATOR' and member.member_organization:
                        raise drf_exceptions.ValidationError(
                            f'Пользователь {member.member} уже является '
                            'координатором одной из организаций-участников.'
                        )
                    if not created and member.membership_role.code not in MANAGER_ROLES:
                        # Такой участник уже есть в проекте - меняем его роль
                        member.membership_role = membership_role
                        member.save(update_fields=('membership_role',))
                    
                    async_task(notifications.notify_about_invite_workgroup_organization_member, 
                                str(project.id),
                                str(member_organization.id),
                                str(member.member.id)
                                )

                        # send notification

        elif request.method == 'PUT':
            member_organization = models.WorkgroupMemberOrganizationModel.objects.filter(
                is_active=True,
                work_group=project,
                organization=request.data.get('organization', None)
            ).first()
            if not member_organization:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if not member_organization.get_update_permission(request):
                raise drf_exceptions.ValidationError(
                    'Недостаточно прав для редактирования организации-участника'
                )
            with transaction.atomic():
                models.WorkgroupMembersModel.objects.filter(
                    is_active=True,
                    work_group=project,
                    member_organization=member_organization
                ).update(is_active=False)
                membership_request_status = models.WorkgroupMembershipStatus.objects.get(code='APPROVED')
                for item in employees:
                    membership_role = models.WorkgroupMembershipRole.objects.get(
                        is_active=True,
                        code=item['role']
                    )
                    member, created = models.WorkgroupMembersModel.objects.get_or_create(
                        is_active=True,
                        member_id=item['employee'],
                        work_group=project,
                        defaults={
                            'membership_role': membership_role,
                            'membership_request_status': membership_request_status,
                            'member_visible': True,
                            'member_organization': member_organization
                        }
                    )
                    if not created:
                        if member.membership_role.code in MANAGER_ROLES:
                            continue
                        if (member.membership_role.code == 'ORG-COORDINATOR' and member.member_organization):
                            raise drf_exceptions.ValidationError(
                                f'Пользователь {member.member} уже является '
                                'координатором одной из организаций-участников'
                            )
                        member.membership_role = membership_role
                        member.save(update_fields=('membership_role',))
        return Response(
            serializers.MemberOrganizationsSerializer(
                member_organization,
                context={
                    'request': request
                },
            ).data
        )

    @action(methods=("get", "post"), detail=True, url_path="invite",
            permission_classes=(permissions.WorkgroupModerator,),)
    def get_post_invite_link(self, request, *args, **kwargs):
        """Создание приглашения в команду"""
        workgroup = self.get_object()
        user = request.user.profile
        
        if request.method == 'POST':
            data = request.data.copy()
            data['workgroup'] = workgroup.pk
            serializer = InviteModelCreateSerializer(
                data=data, 
                context={"request": request, "contractor": workgroup.organization}
            )
            serializer.is_valid(raise_exception=True)
            invite = serializer.save()
        else:
            invite, created = InviteModel.objects.get_or_create(
                is_active=True, 
                contractor=workgroup.organization,
                workgroup=workgroup,
                is_create_new_contractor=True,
            )
        return Response(
            {
                "invite": get_invite_url(invite.token),
                "deactivate_at": invite.deactivate_at,
                "workgroup": invite.workgroup_id,
                "is_create_new_contractor": invite.is_create_new_contractor
            }
        )


    @action(methods=('post',), detail=True, url_path='remove/organization')
    def remove_organization(self, request, *args, **kwargs):
        project = self.get_object()
        member_organization = models.WorkgroupMemberOrganizationModel.objects.filter(
            is_active=True,
            work_group=project,
            organization=request.data.get('organization', None)
        ).first()
        if not member_organization:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not member_organization.get_update_permission(request):
            raise drf_exceptions.ValidationError(
                'Недостаточно прав для удаления организации'
            )
        with transaction.atomic():
            member_organization.is_active = False
            member_organization.deleted_at = timezone.now()
            member_organization.save(update_fields=('is_active', 'deleted_at'))
            models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                work_group=project,
                member_organization=member_organization
            ).update(is_active=False, deleted_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('get',), detail=True, url_path='member_organizations')
    def get_member_organizations(self, request, *args, **kwargs):

        project = self.get_object()
        qs = models.WorkgroupMemberOrganizationModel.objects.filter(
            is_active=True,
            work_group=project
        )

        return Response(serializers.MemberOrganizationsSerializer(
            qs,
            context={
                'request': request
            },
            many=True
        ).data)


class WorkGroupTypesViewSet(ModelViewSet):
    queryset = models.WorkgroupTypes.objects.filter(is_active=True)
    serializer_class = serializers.WorkgroupTypesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.workgroup_set.filter(is_active=True).exists():
            return Response(data=({"error": "there are already work group with this type"}),
                            status=status.HTTP_400_BAD_REQUEST)
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkGroupStatusViewSet(ModelViewSet):
    queryset = models.WorkgroupStatus.objects.filter(is_active=True)
    serializer_class = serializers.WorkgroupStatusSerializer


class WorkGroupMembershipStatusViewSet(ModelViewSet):
    queryset = models.WorkgroupMembershipStatus.objects.filter(is_active=True)
    serializer_class = serializers.WorkgroupMembershipStatusSerializer


class WorkGroupMembershipRoleViewSet(ModelViewSet):
    queryset = models.WorkgroupMembershipRole.objects.filter(is_active=True)
    serializer_class = serializers.WorkgroupMembershipRoleSerializer


class WorkGroupNewsViewSet(ModelViewSet):
    queryset = NewsModel.objects.filter(is_active=True, is_independent=False)
    serializer_class = NewsLiteSerializer
    pagination_class = CustomPagination
    permission_classes = (permissions.WorkgroupNewsPermissions,)

    def create(self, request, *args, **kwargs) -> Response:
        news = super(WorkGroupNewsViewSet, self).create(request, *args, **kwargs)
        news_recorded: NewsModel = news.data.serializer.instance
        news_recorded.author = request.user.profile
        news_recorded.ct = ContentType.objects.get(app_label="bpms_common", model="newsmodel")
        workgroup = models.WorkgroupModel.objects.get(id=request.data.get("workgroups"))
        news_recorded.work_groups.add(workgroup)

        attachments = request.data.get('attachments', [])
        with transaction.atomic():
            news_recorded.save()
            if attachments:
                news_recorded.attachments.set(attachments)
        data = self.serializer_class(news_recorded).data
        async_task(notifications.notify_about_workgroup_news, news_recorded, news_recorded.author, workgroup)
        return Response(data=data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs) -> Response:
        queryset = self.queryset.filter(
            is_active=True,
            work_groups=request.query_params.get("workgroups")
        ).order_by('-created_at')
        paginated_queryset = self.paginate_queryset(queryset)
        data = self.serializer_class(paginated_queryset, many=True).data
        return Response(data=self.get_paginated_response(data).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        if instance.author == request.user.profile:
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({
                "message_ru": "Вы не автор новости",
                "message_kk": "Сіз бұл жаңалықтың авторы емессіз",
                "message_en": "You aren't author news"
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateWorkGroupNewsView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, UpdateNewsPermission)
    serializer_class = NewsUpdateSerializer
    queryset = NewsModel.objects.filter(is_independent=False)


class WorkGroupSprintListView(generics.ListAPIView):
    queryset = TaskSprintModel.objects.filter(is_active=True)
    serializer_class = TaskSprintListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        work_group_id = self.request.query_params.get('work_group', None)
        qs = TaskSprintModel.objects.none()
        if work_group_id:
            work_group = models.WorkgroupModel.objects.get(pk=work_group_id)
            wg_tasks = work_group.workgroup_tasks.filter(is_active=True)
            project_tasks = work_group.project_tasks.filter(is_active=True)
            all_tasks = wg_tasks | project_tasks
            sprint_id_list = all_tasks.filter(sprint__isnull=False).values_list('sprint', flat=True).distinct()
            qs = self.queryset.filter(id__in=sprint_id_list)
        return qs


class WorkGroupEventsViewSet(ModelViewSet):
    queryset = Events.objects.filter(is_active=True)
    pagination_class = CustomPagination
    serializer_class = EventSerializer
    permission_classes = (permissions.WorkgroupNewsPermissions,)

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        workgroups = models.WorkgroupModel.objects.get(pk=request.data.get("workgroups"))
        if serializer.is_valid():
            self.perform_create(serializer)
            workgroups_members = models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                work_group=workgroups,
                membership_request_status=models.WorkgroupMembershipStatus.objects.get(
                    code="APPROVED"
                )
            )
            # if serializer.instance.participants is None:
            #     participants = Participants.objects.create()
            #     participants.participant_profiles.set([i.member.profile for i in workgroups_members])
            #     serializer.instance.participants = participants
            # else:
            #     serializer.instance.participant_profiles.set([i.member.profile for i in workgroups_members])
            serializer.instance.ct = ContentType.objects.get(app_label="workgroups", model="workgroupmodel")
            serializer.instance.workgroup = workgroups
            serializer.instance.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs) -> Response:
        workgroups = models.WorkgroupModel.objects.get(pk=request.query_params.get("workgroups"))
        events_to_show = timezone.now()
        events_to_show_by_2_weeks = timezone.now() + timezone.timedelta(days=14)
        queryset = self.queryset.filter(
            is_active=True,
            event_start__date__gte=events_to_show,
            event_start__date__lte=events_to_show_by_2_weeks,
            workgroup=workgroups
        ).order_by("event_start")
        serializer = self.serializer_class(queryset, many=True).data
        return Response(data=serializer, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetProjectsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        obj = BaseModel.objects.super_get(pk=self.kwargs.get('pk'))
        if obj is None:
            raise exceptions.NotFound()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        request_user_organizations = request.user.profile.my_organizations
        permitted_organizations = get_tree_departments_related_organizations(request_user_organizations)
        instance = self.get_object()
        instance_model_name = instance.__class__.__name__
        models_list = [
            'ProfileModel',
            'ContractorModel',
            'ContractorDepartmentModel'
        ]
        if instance_model_name not in models_list:
            raise exceptions.NotFound()

        if instance_model_name == 'ProfileModel':  # Сотрудник
            if not permitted_organizations & set(instance.my_organizations):
                raise exceptions.ValidationError('Access is denied.')
            user_workgroups_ids = models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                member=instance,
                membership_request_status__code='APPROVED'
            ).values_list(
                'work_group_id',
                flat=True
            ).distinct(
                'work_group_id'
            )
            qs = models.WorkgroupModel.objects.filter(
                is_active=True,
                is_project=True,
                pk__in=user_workgroups_ids,
                organization__in=permitted_organizations
            ).order_by('is_finished', '-created_at')
            data = serializers.WorkgroupNotifySerializer(qs, many=True).data
            return Response(data)
        if instance_model_name == 'ContractorModel':  # Организация
            if instance.id not in permitted_organizations:
                raise exceptions.ValidationError('Access is denied.')
            qs = models.WorkgroupModel.objects.filter(
                is_active=True,
                is_project=True,
                organization=instance
            ).order_by('is_finished', '-created_at')
            data = serializers.WorkgroupNotifySerializer(qs, many=True).data
            return Response(data)
        if instance_model_name == 'ContractorDepartmentModel':  # Отдел
            # TODO Дописать логику для отделов, когда появится возможность указывать их в задаче
            return Response([])


    def create(self, request, *args, **kwargs):
        data = request.data
        name = data.get('name', '')
        is_public = data.get('is_public', None)
        template, _ = self.model.objects.get_or_create(name=name)
        if is_public is not None:
            template.is_public = is_public
        serializer = self.get_serializer(template, data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return super().perform_create(serializer)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except self.model.DoesNotExist:
            raise drf_exceptions.NotFound('Instance not found.')
        if instance.author != request.user.profile:
            raise drf_exceptions.PermissionDenied('Only author.')
        serializer = serializers.WorkgroupTemplateDetailSerializer(
            instance, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except self.model.DoesNotExist:
            raise drf_exceptions.NotFound('Instance not found.')
        if instance.author != request.user.profile:
            raise drf_exceptions.PermissionDenied('Only author.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()

    @action(('get', 'post', 'put', 'delete'), True, 'tasks')
    def tasks(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except self.model.DoesNotExist:
            raise drf_exceptions.NotFound('Instance not found.')
        data = request.data
        task_type = request.query_params.get('type', None)
        id = data.pop('id', None)
        serializer = serializers.TaskTemplateSerializer
        if request.method == 'POST':
            task_type = task_type if task_type is not None else 'task'
            if instance.author != request.user.profile:
                raise drf_exceptions.PermissionDenied('Only author.')
            data['template'] = instance
            data['task_type'] = task_type
            serializer = serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status.HTTP_201_CREATED)
        elif request.method == 'PUT':
            if instance.author != request.user.profile:
                raise drf_exceptions.PermissionDenied('Only author.')
            try:
                task = models.TaskTemplateModel.objects.get(id=uuid.UUID(id))
            except:  # noqa: E722
                raise drf_exceptions.ValidationError('Instance not found.')
            serializer = serializer(task, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if instance.author != request.user.profile:
                raise drf_exceptions.PermissionDenied('Only author.')
            try:
                task = models.TaskTemplateModel.objects.get(id=uuid.UUID(id))
            except:  # noqa: E722
                raise drf_exceptions.ValidationError('Instance not found.')
            task.delete()
            return Response(
                {'detail': 'Task is deleted.'}, status.HTTP_200_OK
            )
        else:
            if task_type is not None:
                tasks = models.TaskTemplateModel.objects.filter(
                    template=instance, task_type=task_type
                )
            else:
                tasks = models.TaskTemplateModel.objects.filter(
                    template=instance
                )
            serializer = serializer(tasks, many=True)
        return Response(serializer.data, status.HTTP_200_OK)


class ProjectTemplateViewSet(BaseModelViewSet):
    model = models.ProjectTemplateModel
    permission_classes = (IsAuthenticated, permissions.ProjectTemplatePermission)
    pagination_class = CustomPagination

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=('is_active',))
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['get', ], detail=False, url_path='available_temlates', url_name='available_temlates')
    def get_available_temlates(self, request):
        """Список шаблонов, по которым могут создаваться проекты."""
        queryset = self.get_queryset()
        queryset = queryset.filter(is_draft=False)
        serializer = serializers.ProjectTemplateListSerializer(queryset, many=True).data
        return Response(data=serializer, status=status.HTTP_200_OK)


class TaskTemplateViewSet(ModelViewSet):
    model = models.TaskTemplateModel
    queryset = models.TaskTemplateModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated, permissions.TaskTemplatePermission,)
    pagination_class = CustomPagination

    def get_serializer_class(self, *args, **kwargs):
        return self.model.get_serializer_class(action=self.action)

    def list(self, request, *args, **kwargs):
        template_id = request.query_params.get('template')
        queryset = self.queryset.filter(template=template_id, level=0).order_by('order')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
    @action(methods=['put', ], detail=True, url_name='up', url_path='up')
    def put_up(self, request, pk=None):
        """УМЕНЬШАЕТ порядковый номер задачи на единицу. Т.е. помещает его ВЫШЕ по списку."""
        task = self.get_object()
        # подзадачи перемещаем относительно "сестер"
        if task.parent:
            previous_task = task.get_siblings(include_self=False).filter(order__lt=task.order).order_by('order').last()
            if previous_task:
                utils.swap_task_order(task, previous_task)
        # корневые задачи перемещаем относительно корневых задач шаблона
        else:
            previous_task = task.template.tasks.filter(level=0, order__lt=task.order).order_by('order').last()
            if previous_task:
                utils.swap_task_order(task, previous_task)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['put', ], detail=True, url_name='down', url_path='down')
    def put_down(self, request, pk=None):
        """УВЕЛИЧИВАЕТ порядковый номер задачи на единицу. Т.е. помещает его НИЖЕ по списку."""
        task = self.get_object()
        # подзадачи перемещаем относительно "сестер"
        if task.parent:
            next_task = task.get_siblings(include_self=False).filter(order__gt=task.order).order_by('order').first()
            if next_task:
                utils.swap_task_order(task, next_task)
        # корневые задачи перемещаем относительно корневых задач шаблона
        else:
            next_task = task.template.tasks.filter(level=0, order__gt=task.order).order_by('order').first()
            if next_task:
                utils.swap_task_order(task, next_task)
        return Response(status=status.HTTP_200_OK)

