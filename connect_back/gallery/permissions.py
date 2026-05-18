from rest_framework.permissions import BasePermission


class GalleryModelUpdatePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        related_object = obj.related_object.original_object
        if view.action in ('list', 'retrieve') and related_object.get_detail_permission(request):
            return True
        if view.action in ('update', 'partial_update', 'destroy') and related_object.get_update_permission:
            return True
        return False


