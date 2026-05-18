from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.apps import apps

from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions

from common.models import BaseModel

from users.models import ProfileModel
from users.serializers import AppUserSerializer, AppUserShortSerializer
from users.utils import check_update_organization_permission

from . import models, utils


class ContractorPermissionModelCreateSerializer(serializers.ModelSerializer):
    aux_conditions = serializers.PrimaryKeyRelatedField(
        queryset=BaseModel.objects.filter(is_active=True),
        allow_null=True,
        required=False,
        many=True
    )

    class Meta:
        model = models.ContractorPermissionModel
        fields = (
            'id',
            'permission_type',
            'aux_conditions',
        )

    def validate(self, attrs):
        permission_type = attrs.get('permission_type')
        target_model = permission_type.aux_condition_model
        aux_conditions = attrs.get('aux_conditions')
        if aux_conditions:
            for each in aux_conditions:
                label = BaseModel.objects.super_get(each.pk).get_label()
                if not label == target_model:
                    raise drf_exceptions.ValidationError({"message": "Некорректное дополнительное условие."})
        return attrs

    def create(self, validated_data):
        contractor_permission_role = self.context.get('contractor_permission_role')
        aux_conditions = validated_data.pop('aux_conditions', None)
        with transaction.atomic():
            instance = models.ContractorPermissionModel.objects.create(
                contractor_permission_role=contractor_permission_role,
                **validated_data
            )
            if aux_conditions:
                for each in aux_conditions:
                    models.ContractorPermissionAuxConditionModel.objects.create(
                        contractor_permission=instance,
                        aux_condition=each,
                    )
        return instance


class ContractorPermissionModelUpdateSerializer(serializers.ModelSerializer):
    aux_conditions = serializers.PrimaryKeyRelatedField(
        queryset=BaseModel.objects.filter(is_active=True),
        allow_null=True,
        required=False,
        many=True
    )

    class Meta:
        model = models.ContractorPermissionModel
        fields = (
            'id',
            'permission_type',
            'aux_conditions',
        )

    def validate(self, attrs):
        permission_type = attrs.get('permission_type')
        target_model = permission_type.aux_condition_model
        aux_conditions = attrs.get('aux_conditions')
        if aux_conditions:
            for each in aux_conditions:
                label = BaseModel.objects.super_get(each.pk).get_label()
                if not label == target_model:
                    raise drf_exceptions.ValidationError({"message": "Некорректное дополнительное условие."})
        return attrs

    def update(self, instance, validated_data):
        aux_conditions = validated_data.pop('aux_conditions', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if aux_conditions is not None:
                for each in aux_conditions:
                    models.ContractorPermissionAuxConditionModel.objects.get_or_create(
                        contractor_permission=instance,
                        aux_condition=each,
                    )
                delete_aux_conditions = models.ContractorPermissionAuxConditionModel.objects.filter(
                    contractor_permission=instance,
                ).exclude(aux_condition__in=aux_conditions)
                for delete_aux_condition in delete_aux_conditions:
                    delete_aux_condition.delete()
        return instance


class ContractorPermissionRoleModelListSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    permission_types = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorPermissionRoleModel
        fields = (
            'id',
            'name',
            'users',
            'permission_types',
            'created_at',
            'updated_at',
        )

    def get_users(self, instance):
        return AppUserShortSerializer([each.user for each in instance.contractor_profiles.all()], many=True).data

    def get_permission_types(self, instance):
        return [each.permission_type.name for each in instance.contractor_permissions.all()]


class ContractorPermissionTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContractorPermissionTypeModel
        fields = (
            'id',
            'name',
            'aux_condition_model',
            'code',
        )


class AuxConditionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class ContractorPermissionListSerializer(serializers.ModelSerializer):
    permission_type = ContractorPermissionTypeListSerializer()
    aux_conditions = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorPermissionModel
        fields = (
            'id',
            'permission_type',
            'aux_conditions',
            'created_at',
            'updated_at',
        )

    def get_aux_conditions(self, instance):
        model_label = instance.permission_type.aux_condition_model
        if not model_label:
            return []
        app_label, model_name = model_label.split('.')
        model = apps.get_model(app_label, model_name)
        qs = model.objects.filter(is_active=True, pk__in=instance.aux_conditions.all().values_list('pk', flat=True))
        data = AuxConditionSerializer(qs, many=True).data
        return data


class ContractorPermissionRoleModelDetailSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    contractor_permissions = ContractorPermissionListSerializer(many=True)

    class Meta:
        model = models.ContractorPermissionRoleModel
        fields = (
            'id',
            'name',
            'created_at',
            'updated_at',
            'users',
            'contractor_permissions',
        )

    def get_users(self, instance):
        users_id = instance.contractor_profiles.all().values_list('user', flat=True)
        users = ProfileModel.objects.filter(is_active=True, pk__in=users_id)
        return AppUserSerializer(users, many=True).data


class ContractorPermissionRoleModelCreateSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True, temporary_blocked=False,),
        allow_null=True,
        required=False,
        many=True
    )
    contractor_permissions = ContractorPermissionModelCreateSerializer(many=True)

    class Meta:
        model = models.ContractorPermissionRoleModel
        fields = (
            'id',
            'name',
            'contractor',
            'users',
            'contractor_permissions',
        )

    def validate_contractor(self, attr):
        user = self.context.get('request').user.profile
        check_update_organization_permission(attr.pk, user)
        return attr

    def create(self, validated_data):
        users = validated_data.pop('users', None)
        contractor_permissions = validated_data.pop('contractor_permissions', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            if users:
                contractor = validated_data.get('contractor')
                for each in users:
                    try:
                        contractor_profile = contractor.contractor_profile.get(user=each)
                    except ObjectDoesNotExist:
                        raise drf_exceptions.ValidationError(
                            {"message": f"Пользователь {each.full_name} не является участником организации."}
                        )
                    models.ContractorPermissionRoleProfileModel.objects.create(
                        contractor_permission_role=instance,
                        contractor_profile=contractor_profile
                    )
            if contractor_permissions:
                for each in contractor_permissions:
                    try:
                        contractor_permission = models.ContractorPermissionModel.objects.create(
                            contractor_permission_role=instance,
                            permission_type=each.get('permission_type')
                        )
                    except IntegrityError:
                        raise drf_exceptions.ValidationError({"message": "Повторяющиеся типы прав."})
                    aux_conditions = each.get('aux_conditions')
                    if aux_conditions:
                        for aux_condition in aux_conditions:
                            models.ContractorPermissionAuxConditionModel.objects.create(
                                contractor_permission=contractor_permission,
                                aux_condition=aux_condition,
                            )
        return instance

    def to_representation(self, instance):
        return ContractorPermissionRoleModelDetailSerializer(instance).data


class ContractorPermissionRoleModelUpdateSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True, temporary_blocked=False, ),
        allow_null=True,
        required=False,
        many=True
    )

    class Meta:
        model = models.ContractorPermissionRoleModel
        fields = (
            'id',
            'name',
            'users',
        )

    def update(self, instance, validated_data):
        users = validated_data.pop('users', None)
        contractor_permissions = self.initial_data.get('contractor_permissions', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if users is not None:
                contractor = instance.contractor
                for each in users:
                    try:
                        contractor_profile = contractor.contractor_profile.get(user=each)
                    except ObjectDoesNotExist:
                        raise drf_exceptions.ValidationError(
                            {"message": f"Пользователь {each.full_name} не является участником организации."}
                        )
                    models.ContractorPermissionRoleProfileModel.objects.get_or_create(
                        contractor_permission_role=instance,
                        contractor_profile=contractor_profile
                    )
                delete_role_profiles = instance.role_contractor_profiles.all().exclude(
                    contractor_profile__user__in=users
                )
                for delete_role_profile in delete_role_profiles:
                    delete_role_profile.delete()
            if contractor_permissions is not None:
                delete_list = contractor_permissions.get('delete')
                if isinstance(delete_list, list):
                    for each in instance.contractor_permissions.filter(pk__in=delete_list):
                        each.delete()
                create_list = contractor_permissions.get('add')
                if isinstance(create_list, list):
                    for each in create_list:
                        serializer = ContractorPermissionModelCreateSerializer(
                            data=each, context={'contractor_permission_role': instance}
                        )
                        serializer.is_valid(raise_exception=True)
                        try:
                            serializer.save()
                        except IntegrityError:
                            raise drf_exceptions.ValidationError({"message": "Одинаковые виды разрешений."})
                edit_list = contractor_permissions.get('edit')
                if isinstance(edit_list, list):
                    for each in edit_list:
                        try:
                            each_instance = instance.contractor_permissions.get(pk=each.get('id'))
                        except (ObjectDoesNotExist, ValidationError):
                            raise drf_exceptions.ValidationError({"message": "Разрешение не найдено."})
                        serializer = ContractorPermissionModelUpdateSerializer(
                            data=each,
                            instance=each_instance,
                            partial=True
                        )
                        serializer.is_valid(raise_exception=True)
                        try:
                            serializer.save()
                        except IntegrityError:
                            raise drf_exceptions.ValidationError({"message": "Одинаковые виды разрешений."})
        return instance

    def to_representation(self, instance):
        return ContractorPermissionRoleModelDetailSerializer(instance).data


class AccessGroupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccessGroupModel
        fields = (
            'id',
            'name',
            'description',
            'is_predefined',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        contractor_id = self.context.get('request').query_params.get('contractor')
        if contractor_id:
            members = instance.members.filter(contractor_id=contractor_id).order_by(
                'user__user__last_name',
                'user__user__first_name',
                'user__user__middle_name',
            )
            members_count = members.count()
            profiles = [_.user for _ in members[:3]]
            data['members'] = AppUserShortSerializer(profiles, many=True).data
            data['members_count'] = members_count
        return data


class AccessGroupNotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccessGroupModel
        fields = (
            'id',
            'name',
        )


class AppSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AppSectionModel
        fields = (
            'code',
            'name',
            'is_main',
        )


class AppSectionRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AppSectionRoleModel
        fields = (
            'code',
            'name',
        )


class AppSectionRoleThroughSerializer(serializers.ModelSerializer):
    app_section = AppSectionSerializer()
    role = AppSectionRoleSerializer()

    class Meta:
        model = models.AppSectionRoleThroughModel
        fields = (
            'app_section',
            'role',
        )


class AccessGroupDetailSerializer(serializers.ModelSerializer):
    app_section_roles = serializers.SerializerMethodField()

    class Meta:
        model = models.AccessGroupModel
        fields = (
            'id',
            'name',
            'description',
            'is_predefined',
            'app_section_roles',
            'contractor'
        )

    def get_app_section_roles(self, instance):
        if not instance.is_predefined:
            contractor = instance.contractor
            available_sections = utils.get_available_sections(contractor).order_by(
                '-is_main',
                'sort',
                'name',
            ).values_list('code', flat=True)
            data = []
            for each in available_sections:
                app_section_role = instance.app_section_roles.filter(app_section_id=each).first()
                if not app_section_role:
                    app_section_role = models.AppSectionRoleThroughModel.objects.get(app_section=each, role_id='banned')
                data.append(AppSectionRoleThroughSerializer(app_section_role).data)
        else:
            app_section_roles = instance.app_section_roles.all().order_by(
                '-app_section__is_main',
                'app_section__sort',
                'app_section__name',
            )
            data = AppSectionRoleThroughSerializer(app_section_roles, many=True).data
        return data


class AccessGroupCreateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True),
        required=False,
        allow_empty=True,
        many=True
    )

    class Meta:
        model = models.AccessGroupModel
        fields = (
            'id',
            'name',
            'contractor',
            'members',
            'description',
        )

    def validate(self, data):
        utils.validate_access_group_members(data)
        return data

    def create(self, validated_data):
        with transaction.atomic():
            members = validated_data.pop('members', None)
            instance = super().create(validated_data)
            app_section_roles_data = self.initial_data.get('app_section_roles')
            app_section_roles = []
            for each in app_section_roles_data:
                app_section = each.get('app_section')
                role = each.get('role')
                try:
                    app_section_role = models.AppSectionRoleThroughModel.objects.get(
                        app_section_id=app_section,
                        role_id=role
                    )
                except ObjectDoesNotExist:
                    raise drf_exceptions.ValidationError(f'pare app_section {app_section} role {role} does not exist')
                app_section_roles.append(app_section_role)
            available_sections = utils.get_available_sections(instance.contractor)
            app_sections = [_.app_section_id for _ in app_section_roles]
            for each in available_sections:
                if each.code not in app_sections:
                    app_section_roles.append(
                        models.AppSectionRoleThroughModel.objects.get(app_section=each, role_id='banned')
                    )
            instance.app_section_roles.set(app_section_roles)

            if members:
                contractor = instance.contractor
                contractor_profiles = []
                for each in members:
                    contractor_profile = contractor.contractor_profile.get(user=each)
                    contractor_profiles.append(contractor_profile)
                instance.members.set(contractor_profiles)
        return instance

    def to_representation(self, instance):
        return AccessGroupDetailSerializer(instance).data


class AccessGroupUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AccessGroupModel
        fields = (
            'id',
            'name',
            'description',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            app_section_roles_data = self.initial_data.get('app_section_roles')
            app_section_roles = []
            if app_section_roles_data is not None:
                for each in app_section_roles_data:
                    app_section = each.get('app_section')
                    role = each.get('role')
                    try:
                        app_section_role = models.AppSectionRoleThroughModel.objects.get(
                            app_section_id=app_section,
                            role_id=role
                        )
                    except ObjectDoesNotExist:
                        raise drf_exceptions.ValidationError(f'pare app_section {app_section} role {role} does not exist')
                    app_section_roles.append(app_section_role)
                available_sections = utils.get_available_sections(instance.contractor)
                app_sections = [_.app_section_id for _ in app_section_roles]
                for each in available_sections:
                    if each.code not in app_sections:
                        app_section_roles.append(
                            models.AppSectionRoleThroughModel.objects.get(app_section=each, role_id='banned')
                        )
                instance.app_section_roles.set(app_section_roles)
        return instance


class AppSectionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AppSectionModel
        fields = (
            'id',
            'name',
            'code',
            'is_main',
        )


class AccessGroupMemberThroughModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccessGroupMemberThroughModel
        fields = (
            'member',
            'access_group',
        )

