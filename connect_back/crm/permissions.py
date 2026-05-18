from rest_framework.permissions import BasePermission


class ContractGetFilePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user.profile
        return not obj.is_individual or obj.contractors.filter(contractor__contractor_profile__user=user).exists()


class OrderDetailPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.get_detail_permission(request)


class DeliveryPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        delivery_point = obj.task_delivery_point
        user = request.user.profile
        if user == obj.user:
            return True
        if delivery_point:
            task = delivery_point.task
            if task:
                operator = task.operator
                if operator == user:
                    return True
                owner = task.owner
                if owner and owner == user:
                    return True
        return False
