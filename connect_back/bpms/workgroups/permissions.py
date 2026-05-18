from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db.models import Q

from contractor_permissions.utils import check_contractor_permission, contractors_where_user_has_permission
from . import models


class WorkGroup(BasePermission):
    def has_permission(self, request, view) -> bool:
        return view.action in [
            "list", "create", "retrieve", "update", "destroy", "join_workgroups",
            "get_my_role", "get_workgroups_members", "leave_workgroups", "get_gallery_files", "send_invitations",
        ]


class WorkgroupModerator(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user.profile
        if user.can_create_workgroups:
            return True
        try:
            workgroups = models.WorkgroupModel.objects.get(pk=view.kwargs.get("pk"))
        except models.WorkgroupModel.DoesNotExist:
            return False
        return models.WorkgroupMembersModel.objects.filter(
            Q(
                member=user,
                work_group=workgroups,
                membership_role=models.WorkgroupMembershipRole.objects.get(code="MODERATOR")
            ) |
            Q(
                member=user,
                work_group=workgroups,
                membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER")
            )
        ).exists()


class WorkgroupNewsPermissions(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user.profile
        if user.can_create_workgroups:
            return True
        if view.action in ["create", "update", "destroy"]:
            try:
                workgroups: models.WorkgroupModel = models.WorkgroupModel.objects.get(
                    pk=request.data.get("workgroups")
                )
            except:
                raise ValidationError("no such workgroup")
            return models.WorkgroupMembersModel.objects.filter(
                Q(
                    member=user,
                    work_group=workgroups,
                    membership_role=models.WorkgroupMembershipRole.objects.get(code="MODERATOR")
                ) |
                Q(
                    member=user,
                    work_group=workgroups,
                    membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER")
                )
            ).exists()

        elif view.action in ["list", "retrieve"]:
            try:
                workgroups: models.WorkgroupModel = models.WorkgroupModel.objects.get(
                    pk=request.query_params.get("workgroups")
                )
            except:
                raise ValidationError("no such workgroup")
            return workgroups.get_detail_permission(request)
            # return not workgroups.public_or_private or models.WorkgroupMembersModel.objects.filter(
            #     member=user,
            #     work_group=workgroups,
            #     membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
            # ).exists()


class ProjectTemplatePermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        # Создавать публичные шаблоны может только суперпользователь
        # Создавать шаблоны в организации может только участник ЭТОЙ организации с правами или ее директор
        user = request.user.profile
        if view.action=='create':
            is_public = request.data.get('is_public', False)
            if is_public:
                return request.user.is_superuser
            else:
                contractor_id = request.data.get('organization')
                im_director = user.contractor_profile.filter(
                    director=True,
                    contractor_id=contractor_id
                    ).exists()
                try:
                    check_contractor_permission(user.pk, contractor_id, 'create_workgroup', None)
                except PermissionDenied:
                    contractor_permission = False
                else:
                    contractor_permission = True
                
                if im_director or contractor_permission:
                    return True
                else:
                    return False
        # Просматривать список шаблонов могут только пользователи с правами создавать проекты и директора организаций
        elif view.action=='list':
            im_director = user.contractor_profile.filter(
                director=True,
                ).exists()
            if contractors_where_user_has_permission(user.pk, 'create_workgroup', None):
                contractor_permission = True
            else:
                contractor_permission = False
            if im_director or contractor_permission:
                return True
            else:
                return False
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update', 'destroy'):
            return obj.get_update_permission(request)
        return obj.get_detail_permission(request)
    

class TaskTemplatePermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        if view.action=='create':
            try:
                template = models.ProjectTemplateModel.objects.get(
                    pk=request.data.get('template')
                )
            except models.ProjectTemplateModel.DoesNotExist:
                raise ValidationError('no such template')
            return template.get_update_permission(request)
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update', 'destroy'):
            return obj.template.get_update_permission(request)
        return obj.template.get_detail_permission(request)