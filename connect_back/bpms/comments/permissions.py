from rest_framework.permissions import BasePermission


class CommentAuthorPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.profile == obj.author
