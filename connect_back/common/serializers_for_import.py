from rest_framework import serializers
from users.models import ProfileModel, CustomUser
from .models import Organization
from bpms.bpms_common.models import WorkTimeLineModel, Position
from django.db import IntegrityError


class WorkTimeLineCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    class Meta:
        model = WorkTimeLineModel
        fields = (
            'id',
            'profile',
            'organization',
            'positions',
            'date_begin',
            'date_end',
            'current',
            'checked',
            'fired',
        )

    def create(self, validated_data):
        pos_data = self.initial_data.get('position')
        pos_id = pos_data.get('id')
        pos_name = pos_data.get('name')
        pos_obj, created = Position.objects.get_or_create(id=pos_id, defaults={'name': pos_name, "uid": pos_id})
        validated_data['positions'] = pos_obj
        return super().create(validated_data)

    def update(self, instance, validated_data):
        pos_data = self.initial_data.get('position')
        pos_id = pos_data.get('id')
        pos_name = pos_data.get('name')
        pos_obj, created = Position.objects.get_or_create(id=pos_id, defaults={'name': pos_name, "uid": pos_id})
        validated_data['positions'] = pos_obj
        return super().update(instance, validated_data)


class ImportProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()

    class Meta:
        model = ProfileModel
        fields = (
            'id',
            'user',
            'temp_organization',
            'avatar_path',
            # 'uid1c',
            # 'first_name',
            # 'last_name',
            # 'middle_name',
            # 'organization',
            # 'organization_uid',
            # 'position',
            # 'role',
            # 'phone',
            # 'bin',
            # 'iin',
            # 'avatar',
        )


class ImportCreatedProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = (
            'id',
            'user',
            'temp_organization',
            'avatar_path',
            # 'uid1c',
            # 'first_name',
            # 'last_name',
            # 'middle_name',
            # 'organization',
            # 'organization_uid',
            # 'position',
            # 'role',
            # 'phone',
            # 'bin',
            # 'iin',
            # 'avatar',
        )


class ImportCreatedUserSerializer(serializers.ModelSerializer):
    is_loading = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'is_loading', 'gos24_id'
        )



class ImportUserSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField()
    is_loading = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            #'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'is_loading',
            'gos24_id'
        )


class ImportCreatedOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            'id',
            'name',
            # 'bin',
            # 'parent',
        )


class ImportOrganizationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()

    class Meta:
        model = Organization
        fields = (
            'id',
            'name',
            # 'bin',
            # 'parent',
        )


def load_users(users):
    for user in users:
        user['gos24_id'] = user['id']
        user_in_db = CustomUser.objects.filter(gos24_id=user['id'])
        if user_in_db.exists():
            serialized_user = ImportCreatedUserSerializer(instance=user_in_db.last(), data=user)
            # print('update_user' + user['first_name'] + ' ' + user['last_name'])
        else:
            serialized_user = ImportUserSerializer(data=user)
            # print('new_user' + user['first_name'] + ' ' + user['last_name'])
        if serialized_user.is_valid():
            serialized_user.save()
            # print('user_saved')


def load_organizations(organizations):
    for organization in organizations:
        org_in_db = Organization.objects.filter(id=organization['id'])
        if org_in_db.exists():
            serialized_organization = ImportCreatedOrganizationSerializer(instance=org_in_db.last(), data=organization)
            # print('organization_updated :' + organization['name'])
        else:
            serialized_organization = ImportOrganizationSerializer(data=organization)
            # print('organization_created :' + organization['name'])
        if serialized_organization.is_valid():
            serialized_organization.save()
            # print('organization_saved')


def load_profiles(profiles):
    for profile in profiles:
        # profile['avatar_path'] = profile['avatar']
        pf_in_db = ProfileModel.objects.filter(id=profile['id'])
        if pf_in_db.exists():
            serialized_profile = ImportCreatedProfileSerializer(instance=pf_in_db.last(), data=profile)
            # print('profile_updated :' + str(profile['user']))
        else:
            serialized_profile = ImportProfileSerializer(data=profile)
            # print('profile_created :' + str(profile['user']))
        if serialized_profile.is_valid():
            serialized_profile.save()
            # print('profile_saved')


def load_wtl(wtl_list):
    for wtl in wtl_list:
        wtl_in_db = WorkTimeLineModel.objects.filter(id=wtl['id'])
        if wtl_in_db.exists():
            serialized_wtl = WorkTimeLineCreateUpdateSerializer(instance=wtl_in_db.last(), data=wtl)
        else:
            serialized_wtl = WorkTimeLineCreateUpdateSerializer(data=wtl)

        if serialized_wtl.is_valid():
            serialized_wtl.save()
        else:
            print(serialized_wtl.errors)
