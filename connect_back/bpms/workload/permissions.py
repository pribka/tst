from rest_framework import status

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions as drf_exceptions
from rest_framework.permissions import BasePermission

from bpms.workgroups import models as wg_models
from users import models as u_models


class WorkSchedulePermission(BasePermission):

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True

        elif request.method == 'PUT':
            try:
                profile_id = view.kwargs.get('profile')
                profile = u_models.ProfileModel.objects.get(id=profile_id)
            except ObjectDoesNotExist:
                return False

            if request.user.profile == profile:
                return True
            elif wg_models.WorkgroupMembersModel.objects.filter(
                member=request.user.profile,
                membership_role__code__in=('MODERATOR', 'FOUNDER')
            ).exists():
                return True
            else:
                return False

        else:
            return drf_exceptions.MethodNotAllowed(
                method='POST', code=status.HTTP_405_METHOD_NOT_ALLOWED
            )
