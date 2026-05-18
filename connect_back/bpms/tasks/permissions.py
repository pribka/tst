import json
import hashlib

from rest_framework.permissions import BasePermission

from . import models
from .utils import filter_by_permissions, get_tasks_for_sprint_qs
from bkz3.settings import DID_SALT


class DetailTaskPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if filter_by_permissions(models.TaskModel.objects.filter(is_active=True, pk=obj.pk), request.user.profile
                                 ).exists():
            return True
        else:
            return False


class IsBySecretAuthenticated(BasePermission):
    def has_permission(self, request, view):
        copy_data = request.data.copy()

        secret = copy_data.pop('secret', '')

        if secret:
            return hashlib.md5((json.dumps(copy_data) + DID_SALT).encode('utf-8')).hexdigest() == secret
        else:
            return False

    def has_object_permission(self, request, view, obj):
        copy_data = request.data.copy()

        secret = copy_data.pop('secret', '')

        if secret:
            obj_success = True
            if obj and str(obj.pk) != str(copy_data.get('task_id', '')):
                obj_success = False
            return hashlib.md5((json.dumps(copy_data) + DID_SALT).encode('utf-8')).hexdigest() == secret and obj_success
        else:
            return False


class UpdateTaskStatusPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        status = request.data.get('status')
        im_project_moderator = False
        im_group_moderator = False
        im_sprint_author = False
        im_dealer = False
        im_interest_visor = False
        task_type_id = obj.task_type_id

        # Если статус не изменился — разрешаем (меняется только порядок)
        if status == str(obj.status_id):
            return True
        if task_type_id == 'task':
            return status in obj.get_available_statuses(user.pk)
        if obj.project:
            task_project = obj.project
            im_project_moderator = task_project.workgroupmembersmodel_set.filter(
                is_active=True,
                membership_request_status__code='APPROVED',
                membership_role__code__in=('FOUNDER', 'MODERATOR'),
                member=user,
            ).exists()
        if obj.workgroup:
            task_group = obj.workgroup
            im_group_moderator = task_group.workgroupmembersmodel_set.filter(
                is_active=True,
                membership_request_status__code='APPROVED',
                membership_role__code__in=('FOUNDER', 'MODERATOR'),
                member=user,
            ).exists()
        if obj.sprint:
            task_sprint = obj.sprint
            if not task_sprint.status == 'completed' and task_sprint.author == user:
                im_sprint_author = True
        if obj.contractor:
            im_dealer = user in obj.contractor.profiles.all()
        
        if obj.task_type.code == 'interest' and obj.visors:
            im_interest_visor = user in obj.visors.all()

        if obj.owner == user or im_group_moderator or im_project_moderator or im_sprint_author or im_dealer or im_interest_visor or task_type_id == 'logistic':
            return True
        elif obj.operator == user and status in ['new', 'in_work', 'on_pause', 'on_check', 'on_rework']:
            return True
        else:
            return False


class UpdateCooperatorTaskStatusPermission(BasePermission):
    """Разрешение на изменение статуса задачи соисполнителя."""
    def has_object_permission(self, request, view, obj):
        obj = obj.task
        user = request.user.profile
        status = request.data.get('status')
        task_type_id = obj.task_type_id
        if task_type_id == 'task':
            return status in obj.get_available_coop_statuses(user.pk)



        # im_project_author = False
        # im_group_author = False
        # im_sprint_author = False
        # im_dealer = False
        # im_interest_visor = False
        # im_cooperator = False
        # task_type_id = obj.task_type_id
        # if obj.project:
        #     task_project = obj.project
        #     im_project_author = task_project.author == user
        # if obj.workgroup:
        #     task_group = obj.workgroup
        #     im_group_author = task_group.author == user
        # if obj.sprint:
        #     task_sprint = obj.sprint
        #     if not task_sprint.status == 'completed' and task_sprint.author == user:
        #         im_sprint_author = True
        # if obj.contractor:
        #     im_dealer = user in obj.contractor.profiles.all()
        #
        # if obj.task_type.code == 'interest' and obj.visors:
        #     im_interest_visor = user in obj.visors.all()
        #
        # if obj.cooperators:
        #     im_cooperator = user in obj.cooperators.all()
        #
        # if (obj.operator == user or obj.owner == user
        #     or im_group_author or im_project_author or im_sprint_author or im_dealer or im_interest_visor
        #     or task_type_id == 'logistic'):
        #     return True
        # elif im_cooperator and status in ['new', 'in_work', 'on_pause', 'on_check', 'on_rework']:
        #     return True
        # else:
        #     return False


class UpdateTaskSprintStatusPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if obj.author == user:
            return True
        projects = obj.projects.all()
        for project in projects:
            if project.get_update_permission(request):
                return True


class UpdateTaskPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_update_permission(request)


class TakeAuctionTaskPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        task_type = obj.task_type.code
        if task_type in ['task', 'logistic', ] and obj.is_auction:
            return True
        if task_type == 'interest' and request.user.profile.is_auctioneer and obj.is_auction:
            return True
        return False


class UpdateSprintPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user == obj.author:
            return True
        projects = obj.projects.all()
        for project in projects:
            if project and project.get_update_permission(request):
                return True


class DetailSprintPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.get_detail_permission(request):
            return True
        return False


class SetSprintPermission(BasePermission):
    # Здесь obj это задача
    def has_object_permission(self, request, view, obj):
        project = obj.project
        if project:
            return obj.project.get_update_permission(request)
        else:
            return False


class UpdateOwnerTaskPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user == obj.owner:
            return True
        else:
            return False


class UpdateOperatorPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user in (obj.owner, obj.operator):
            return True
        else:
            return False


class DeleteTaskPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user == obj.owner and obj.get_children().filter(is_active=True).count() == 0:
            return True
        else:
            return False


class TaskExecutionTimeModelPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        else:
            return obj.task.get_detail_permission(request)


class TaskBudgetModelPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user == obj.task.owner or user == obj.task.operator:
            return True


class TaskInterestNeedPermission(BasePermission):

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update', 'destroy'):
            return obj.task.get_update_permission(request)
        return obj.task.get_detail_permission(request)


class TaskDifficultyPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        if user == obj.task.owner:
            return True


class LogistPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user.profile
        # TODO добавить еще logist_manager заказа в разрешения
        return user.can_create_logistic_task


class SprintExpectedResultUpdatePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.get_update_permission(request):
            return True
        else:
            return False
