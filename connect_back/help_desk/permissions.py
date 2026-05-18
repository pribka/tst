from rest_framework.permissions import BasePermission
from . import models


class CustomerCartModelPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, models.CustomerCardModel):
            if view.action in (
                    'update',
                    'partial_update',
                    'add_specialist',
                    'update_specialist',
                    'remove_specialist',
                    'add_contact_person',
                    'update_contact_person',
                    'remove_contact_person',
            ):
                return obj.get_update_permission(request)
            else:
                return obj.get_detail_permission(request)
        else:
            return True


class CustomerCardAdminPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, models.CustomerCardAdminModel):
            if view.action in (
                    'update',
                    'partial_update',
                    'delete_admin',
            ):
                return obj.get_update_permission(request)
            else:
                return obj.get_detail_permission(request)
        else:
            return True


class ContactPersonPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in (
            'update',
            'partial_update',

        ):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class HelpDeskTicketCategoryPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class ContactPersonPostPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)


class HelpDeskCostPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update'):
            return obj.get_update_permission(request)
        else:
            return obj.get_detail_permission(request)