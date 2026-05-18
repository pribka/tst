from rest_framework.permissions import BasePermission
from rest_framework import exceptions as drf_exceptions

from contractor_permissions.utils import check_contractor_permission, contractors_where_user_has_permission
from .models import ObjectivesModel, KeyResultsModel


class MissionModelPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            user_id = request.user.profile.pk
            organization_id = request.data.get('organization', '')
            try:
                check_contractor_permission(user_id, organization_id, 'create_okr', None)
            except drf_exceptions.PermissionDenied:
                return False
            else:
                return True
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class ObjectivesModelPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            user_id = request.user.profile.pk
            if request.data:
                organization_id = request.data.get('organization', '')
                try:
                    check_contractor_permission(user_id, organization_id, 'create_okr', None)
                    return True
                except drf_exceptions.PermissionDenied:
                    return False
            else:
                create_okr_contractors = contractors_where_user_has_permission(user_id, 'create_okr', None)
                return create_okr_contractors is not None
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class KeyResultsModelPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            objective_id = request.data.get('objective', '')
            try:
                objective = ObjectivesModel.objects.get(pk=objective_id)
            except ObjectivesModel.DoesNotExist:
                return False
            return objective.get_update_key_results_permission(request)
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)
        

class InitiativesModelPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            key_result_id = request.data.get('key_result', '')
            try:
                key_result = KeyResultsModel.objects.get(pk=key_result_id)
            except KeyResultsModel.DoesNotExist:
                return False
            return key_result.get_update_initiatives_permission(request)
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update', 'set_complete'):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)
        

class KeyResultMetricsModelPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            user_id = request.user.profile.pk
            contractor_id = request.data.get('contractor', '')
            try:
                check_contractor_permission(user_id, contractor_id, ('create_okr', 'operator_okr'), None)
            except drf_exceptions.PermissionDenied:
                return False
            else:
                return True
        else:
            return True

    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update',):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)