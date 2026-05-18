import uuid
import shutil
import datetime
import pytz

from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction, IntegrityError
from django.db.models import Count, Q

from drf_recaptcha.fields import ReCaptchaV3Field, ReCaptchaV2Field
from django_q.tasks import async_task
from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer
from django.contrib.auth import password_validation
from rest_framework.exceptions import ValidationError


from common.utils import get_my_access_groups, get_tariff_section_codes, get_available_section_codes
from contractor_permissions.models import AccessGroupMemberThroughModel, AccessGroupModel
from contractor_permissions.utils import get_tariffs_id_by_contractors

from billing.models import ContractorTariffModel


try:
    from bkz3.settings import DOWNLOADER_PATH
except ImportError:
    DOWNLOADER_PATH = None
from bkz3.settings import INVITE_REGISTER_ONLY

from bkz3.settings import MEDIA_URL, BACKEND_URL, AVATAR_ROOT, SUPPORT_EMAIL

from common.models import File, ObjectViewerRelationModel
from common.catalogs.models import (
    ContractorModel,
    ContractorProfileModel,
    ContractorMemberModel,
    ContractorRelationModel,
    BankRequisitesModel
)
from common.utils import get_logo_url
from common.current_profile.middleware import get_current_authenticated_profile

from bpms.event_calendar.models import EventCalendarModel
from bpms.personal_planes.models import PersonalPlaneModel

from . import models, utils, notifications
from .search_indexes import ProfileIndex



class AppOrganizationSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    director = serializers.SerializerMethodField()
    has_descendants = serializers.SerializerMethodField()
    structural_division_count = serializers.SerializerMethodField()
    department_count = serializers.SerializerMethodField()
    # task_count = serializers.SerializerMethodField()
    # project_count = serializers.SerializerMethodField()

    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name',
            'name_ru',
            'name_kk',
            'full_name',
            'full_name_ru',
            'full_name_kk',
            'phone',
            'email',
            'doc_prefix',
            'logo',
            'members_count',
            'director',
            'has_descendants',
            'structural_division_count',
            'department_count',
            # 'task_count',
            # 'project_count',
        )

    def get_members_count(self, instance):
        try:
            result = instance.annotate_members_count
        except AttributeError:
            result = instance.profiles.filter(is_active=True, temporary_blocked=False).count()
        return result

    def get_structural_division_count(self, instance):
        try:
            result = instance.annotate_structural_division_count
        except AttributeError:
            result = instance.contractor_relations_parent.filter(is_active=True, relation_type='structural_division').count()
        return result

    def get_department_count(self, instance):
        try:
            result = instance.annotate_department_count
        except AttributeError:
            result = instance.departments.filter(is_active=True).count()
        return result

    # def get_task_count(self, instance):
    #     try:
    #         result = instance.annotate_task_count
    #     except AttributeError:
    #         result = instance.tasks.filter(
    #             is_active=True,
    #             status__task_status_type__is_complete=False
    #         ).distinct().count()
    #     return result
    #
    # def get_project_count(self, instance):
    #     try:
    #         result = instance.annotate_project_count
    #     except AttributeError:
    #         result = instance.workgroups.filter(is_active=True, is_project=True, is_finished=False).distinct().count()
    #     return result

    def get_logo(self, instance):
        if instance.logo:
            return get_logo_url(instance.logo)
        else:
            return ''

    def get_director(self, instance):

        # director_id = cache.get('ContractorDirectorId' + str(instance.id), None)
        # if director_id:
        #     return CachedAppUserSerializer(director_id).data
        try:
            director = instance.contractor_director[0]
        except AttributeError:
            director = instance.contractor_profile.filter(director=True).first()
        except IndexError:
            return None
        if director:
            # cache.set('ContractorDirectorId' + str(instance.id), director.user.id)
            return AppUserSerializer(director.user).data
        else:
            return None

    def get_has_descendants(self, instance):
        try:
            has_descendants = instance.annotate_has_descendants
        except AttributeError:
            has_descendants = instance.contractor_relations_parent.filter(is_active=True).exists()
        return has_descendants

    def to_representation(self, instance):
        data = super().to_representation(instance)
        contractor_members = list(filter(lambda x: x.is_active, list(instance.contractor_members.all())))
        if contractor_members:
            contractor_member = contractor_members[0]
            data['inn'] = contractor_member.inn
        else:
            data['inn'] = ''
        if hasattr(instance, 'is_my'):
            data['is_my'] = instance.is_my
        else:
            current_user = self.get_current_user()
            if current_user:
                data['is_my'] = instance.pk in current_user.my_organizations
        if hasattr(instance, 'is_current'):
            data['is_current'] = instance.is_current
        else:
            current_user = self.get_current_user()
            if current_user:
                data['is_current'] = current_user.current_contractor == instance
        return data

    def get_current_user(self):
        current_user = self.context.get('current_user')
        if not current_user:
            current_user = get_current_authenticated_profile()
            self.context['current_user'] = current_user
        return current_user


class ContractorRelationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorRelationModel
        fields = (
            'id',
            'contractor_parent',
            'relation_type',
        )

    def update(self, instance, validated_data):
        contractor = self.context.get('contractor')
        validated_data['contractor'] = contractor
        instance = super().update(instance, validated_data)
        return instance


class MyOrganizationDetailSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    director = serializers.SerializerMethodField()
    has_descendants = serializers.SerializerMethodField()
    structural_division_count = serializers.SerializerMethodField()
    department_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name',
            'full_name',
            'phone',
            'email',
            'doc_prefix',
            'logo',
            'members_count',
            'director',
            'has_descendants',
            'structural_division_count',
            'department_count',
            'task_count',
            'project_count',
            'metadata',
        )

    def get_members_count(self, instance):
        try:
            result = instance.annotate_members_count
        except AttributeError:
            result = instance.profiles.filter(is_active=True, temporary_blocked=False).count()
        return result

    def get_structural_division_count(self, instance):
        try:
            result = instance.annotate_structural_division_count
        except AttributeError:
            result = instance.contractor_relations_parent.filter(is_active=True,
                                                                 relation_type='structural_division').count()
        return result

    def get_department_count(self, instance):
        try:
            result = instance.annotate_department_count
        except AttributeError:
            result = instance.departments.filter(is_active=True).count()
        return result

    def get_task_count(self, instance):
        try:
            result = instance.annotate_task_count
        except AttributeError:
            result = instance.tasks.filter(
                is_active=True,
                status__task_status_type__is_complete=False
            ).distinct().count()
        return result

    def get_project_count(self, instance):
        try:
            result = instance.annotate_project_count
        except AttributeError:
            result = instance.workgroups.filter(is_active=True, is_project=True, is_finished=False).distinct().count()
        return result

    def get_logo(self, instance):
        if instance.logo:
            return get_logo_url(instance.logo)
        else:
            return ''

    def get_director(self, instance):

        try:
            director = instance.contractor_director[0]
        except AttributeError:
            director = instance.contractor_profile.filter(director=True).first()
        except IndexError:
            return None
        if director:
            return AppUserSerializer(director.user).data
        else:
            return None

    def get_has_descendants(self, instance):
        try:
            has_descendants = instance.annotate_has_descendants
        except AttributeError:
            has_descendants = instance.contractor_relations_parent.filter(is_active=True).exists()
        return has_descendants

    def get_current_user(self):
        current_user = self.context.get('current_user')
        if not current_user:
            current_user = get_current_authenticated_profile()
            self.context['current_user'] = current_user
        return current_user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        contractor_members = list(filter(lambda x: x.is_active, list(instance.contractor_members.all())))
        if contractor_members:
            contractor_member = contractor_members[0]
            data['full_name'] = contractor_member.full_name
            data['organization_email'] = contractor_member.email
            data['kpp'] = contractor_member.kpp
            data['ogrn'] = contractor_member.ogrn
            data['ogrnip'] = contractor_member.ogrnip
            data['okpo'] = contractor_member.okpo
            data['legal_address'] = contractor_member.legal_address
            data['postal_address'] = contractor_member.postal_address
            data['director_position'] = contractor_member.director_position
            data['director_position_genitive'] = contractor_member.director_position_genitive
            data['director_full_name'] = contractor_member.director_full_name
            data['director_full_name_genitive'] = contractor_member.director_full_name_genitive
            data['inn'] = contractor_member.inn
        else:
            contractor_member = None
            data['full_name'] = ''
            data['organization_email'] = ''
            data['kpp'] = ''
            data['ogrn'] = ''
            data['ogrnip'] = ''
            data['okpo'] = ''
            data['legal_address'] = ''
            data['postal_address'] = ''
            data['director_position'] = ''
            data['director_position_genitive'] = ''
            data['director_full_name'] = ''
            data['director_full_name_genitive'] = ''
            data['inn'] = ''
        if contractor_member and contractor_member.bank_requisites:
            bank_requisites = contractor_member.bank_requisites
            data['bank_name'] = bank_requisites.bank_name
            data['bik'] = bank_requisites.bik
            data['bank_account'] = bank_requisites.bank_account
            data['correspondent_account'] = bank_requisites.correspondent_account
        else:
            data['bank_name'] = ''
            data['bik'] = ''
            data['bank_account'] = ''
            data['correspondent_account'] = ''
        contractor_parent = instance.contractor_parent
        if contractor_parent:
            from common.catalogs.serializers import ContractorModelByIdSerializer
            data['contractor_parent'] = ContractorModelByIdSerializer(contractor_parent).data
        else:
            data['contractor_parent'] = None
        if hasattr(instance, 'is_my'):
            data['is_my'] = instance.is_my
        else:
            current_user = self.get_current_user()
            if current_user:
                data['is_my'] = instance.pk in current_user.my_organizations
        if hasattr(instance, 'is_current'):
            data['is_current'] = instance.is_current
        else:
            current_user = self.get_current_user()
            if current_user:
                data['is_current'] = current_user.current_contractor == instance
        return data


class MyOrganizationCreateSerializer(serializers.ModelSerializer):
    inn = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    email = serializers.EmailField(
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    kpp = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrn = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrnip = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    okpo = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    legal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    postal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bik = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    correspondent_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    logo = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.filter(is_active=True), required=False, allow_null=True)
    contractor_parent = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True,), allow_null=True, required=False
    )
    director = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.ProfileModel.objects.filter(is_active=True, temporary_blocked=False)
    )

    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'phone',
            'inn',
            'doc_prefix',
            'email',
            'full_name_ru',
            'full_name_kk',
            'kpp',
            'ogrn',
            'ogrnip',
            'okpo',
            'legal_address',
            'postal_address',
            'director_position',
            'director_position_genitive',
            'director_full_name',
            'director_full_name_genitive',
            'bank_name',
            'bik',
            'bank_account',
            'correspondent_account',
            'logo',
            'contractor_parent',
            'director',
            'doc_prefix',
            'metadata',
        )

    def validate_logo(self, data):
        return utils.validate_logo(self, data)

    def validate_name_ru(self, data):
        name_ru = self.initial_data.get('name_ru', None)
        if not name_ru:
            raise ValidationError({'name_ru': 'Обязательное поле.'})
        return data

    def create(self, validated_data):

        inn = validated_data.pop('inn', '')
        if not validated_data.get('full_name_ru') and validated_data.get('name_ru', None):
            validated_data['full_name_ru'] = validated_data.get('name_ru', '')
        logo_instance = validated_data.pop('logo', None)
        logo = utils.get_logo_path(logo_instance)
        user = self.context.get('request').user.profile
        contractor_parent = validated_data.pop('contractor_parent', None)
        director = validated_data.pop('director', None)
        kpp = validated_data.pop('kpp', '')
        ogrn = validated_data.pop('ogrn', '')
        ogrnip = validated_data.pop('ogrnip', '')
        okpo = validated_data.pop('okpo', '')
        legal_address = validated_data.pop('legal_address', '')
        postal_address = validated_data.pop('postal_address', '')
        director_position = validated_data.pop('director_position', '')
        director_position_genitive = validated_data.pop('director_position_genitive', '')
        director_full_name = validated_data.pop('director_full_name', '')
        director_full_name_genitive = validated_data.pop('director_full_name_genitive', '')
        bank_name = validated_data.pop('bank_name', '')
        bank_account = validated_data.pop('bank_account', '')
        correspondent_account = validated_data.pop('correspondent_account', '')
        bik = validated_data.pop('bik', '')

        with transaction.atomic():
            instance = ContractorModel.objects.create(
                logo=logo,
                **validated_data,
            )

            contractor_member = ContractorMemberModel.objects.create(
                name_ru=instance.name_ru,
                name_kk=instance.name_kk,
                email=instance.email,
                inn=inn,
                contractor=instance,
                full_name_ru=instance.full_name_ru,
                full_name_kk=instance.full_name_kk,
                kpp=kpp,
                ogrn=ogrn,
                ogrnip=ogrnip,
                okpo=okpo,
                legal_address=legal_address,
                postal_address=postal_address,
                director_position=director_position,
                director_position_genitive=director_position_genitive,
                director_full_name=director_full_name,
                director_full_name_genitive=director_full_name_genitive
            )
            bank_requisites = BankRequisitesModel.objects.create(
                contractor_member=contractor_member,
                bank_name=bank_name,
                bank_account=bank_account,
                correspondent_account=correspondent_account,
                bik=bik,
                is_default=True
            )
            if director and contractor_parent:
                director_profile = ContractorProfileModel.objects.create(
                    user=director,
                    contractor=instance,
                    director=True,
                )
            else:
                director_profile = ContractorProfileModel.objects.create(
                    user=user,
                    contractor=instance,
                    director=True,
                )
            if director_profile.user == user:
                user.current_contractor = instance
                user.save(update_fields=('current_contractor',))
            if contractor_parent:
                relation = ContractorRelationModel.objects.create(
                    contractor_parent=contractor_parent,
                    contractor=instance,
                    relation_type_id='structural_division',
                )
            else:
                relation = None
            self.context['relation'] = relation
            if logo_instance:
                logo_instance.copy_to_avatar_path()
        return instance

    def to_representation(self, instance):
        return AppOrganizationSerializer(instance, context=self.context).data


class MyOrganizationUpdateSerializer(serializers.ModelSerializer):
    inn = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.ProfileModel.objects.filter(is_active=True, temporary_blocked=False)
    )
    contractor_parent = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True,), allow_null=True, required=False
    )

    email = serializers.EmailField(
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    kpp = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrn = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrnip = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    okpo = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    legal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    postal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bik = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    correspondent_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )

    class Meta:
        model = ContractorModel
        fields = (
            'inn',
            'name_ru',
            'name_kk',
            'director',
            'contractor_parent',
            'email',
            'full_name_ru',
            'full_name_kk',
            'kpp',
            'ogrn',
            'ogrnip',
            'okpo',
            'legal_address',
            'postal_address',
            'director_position',
            'director_position_genitive',
            'director_full_name',
            'director_full_name_genitive',
            'bank_name',
            'bik',
            'bank_account',
            'correspondent_account',
            'phone',
            'doc_prefix',
            'metadata',
        )

    def validate_name_ru(self, data):
        name_ru = self.initial_data.get('name_ru', None)
        if not name_ru:
            raise ValidationError({'name_ru': 'Обязательное поле.'})
        return data

    def update(self, instance, validated_data):
        inn = validated_data.pop('inn', '')

        director = validated_data.pop('director', None)
        contractor_parent = validated_data.pop('contractor_parent', None)
        kpp = validated_data.pop('kpp', '')
        ogrn = validated_data.pop('ogrn', '')
        ogrnip = validated_data.pop('ogrnip', '')
        okpo = validated_data.pop('okpo', '')
        legal_address = validated_data.pop('legal_address', '')
        postal_address = validated_data.pop('postal_address', '')
        director_position = validated_data.pop('director_position', '')
        director_position_genitive = validated_data.pop('director_position_genitive', '')
        director_full_name = validated_data.pop('director_full_name', '')
        director_full_name_genitive = validated_data.pop('director_full_name_genitive', '')
        bank_name = validated_data.pop('bank_name', '')
        bank_account = validated_data.pop('bank_account', '')
        correspondent_account = validated_data.pop('correspondent_account', '')
        bik = validated_data.pop('bik', '')

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if inn is not None:
                contractor_member = ContractorMemberModel.objects.filter(is_active=True, contractor=instance).first()
                if not contractor_member:
                    contractor_member = ContractorMemberModel.objects.create(
                        contractor=instance,
                        name_ru=instance.name_ru,
                        inn=inn,
                    )
                else:
                    contractor_member.inn = inn
                    contractor_member.save(update_fields=('inn',),)
            
            contractor_member.name_ru = instance.name_ru
            contractor_member.name_kk = instance.name_kk
            contractor_member.inn = inn
            contractor_member.email = instance.email
            contractor_member.full_name_ru = instance.full_name_ru
            contractor_member.full_name_kk = instance.full_name_kk
            contractor_member.kpp = kpp
            contractor_member.ogrn = ogrn
            contractor_member.ogrnip = ogrnip
            contractor_member.okpo = okpo
            contractor_member.legal_address = legal_address
            contractor_member.postal_address = postal_address
            contractor_member.director_position = director_position
            contractor_member.director_position_genitive = director_position_genitive
            contractor_member.director_full_name = director_full_name
            contractor_member.director_full_name_genitive = director_full_name_genitive
            contractor_member.save(
                update_fields=('name_ru', 'name_kk', 'inn', 'email', 'full_name_ru', 'full_name_kk',
                               'kpp', 'ogrn', 'ogrnip', 'okpo', 'legal_address',
                               'postal_address', 'director_position', 'director_position_genitive',
                               'director_full_name', 'director_full_name_genitive',))

            if director:
                ContractorProfileModel.objects.filter(contractor=instance, director=True).update(director=False)
                contractor_profile, created = ContractorProfileModel.objects.get_or_create(
                    user=director, contractor=instance
                )
                contractor_profile.director = True
                contractor_profile.save(update_fields=('director',))
            if contractor_parent:
                ContractorRelationModel.objects.filter(
                    contractor=instance, relation_type='structural_division',
                ).delete()
                try:
                    ContractorRelationModel.objects.create(
                        contractor_parent=contractor_parent,
                        contractor=instance,
                        relation_type_id='structural_division',
                    )
                except IntegrityError:
                    pass

            bank_requisites = contractor_member.requisites.first()
            if not bank_requisites:
                bank_requisites = BankRequisitesModel.objects.create(
                    contractor_member=contractor_member,
                    bank_name=bank_name,
                    bank_account=bank_account,
                    correspondent_account=correspondent_account,
                    bik=bik,
                    is_default=True
                )
            else:
                bank_requisites.bank_name = bank_name
                bank_requisites.bank_account = bank_account
                bank_requisites.correspondent_account = correspondent_account
                bank_requisites.bik = bik
                bank_requisites.save(update_fields=('bank_name', 'bank_account', 'correspondent_account', 'bik',))

        return instance

    def to_representation(self, instance):
        return AppOrganizationSerializer(instance, context=self.context).data


class MyOrganizationUpdateLogoSerializer(serializers.ModelSerializer):
    logo = serializers.PrimaryKeyRelatedField(queryset=File.objects.filter(is_active=True))

    class Meta:
        model = ContractorModel
        fields = (
            "id",
            "logo",
        )

    def validate_logo(self, data):
        return utils.validate_logo(self, data)

    def update(self, instance, validated_data):
        logo_instance = validated_data.get('logo', '')
        logo = utils.get_logo_path(logo_instance)
        instance.logo = logo
        instance.save(update_fields=('logo',),)
        if logo:
            logo_instance.copy_to_avatar_path()
        return instance


class SetAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileModel
        fields = (
            'avatar',
        )

    def validate(self, data):
        avatar = data['avatar']
        if avatar:
            if not avatar.is_image:
                raise ValidationError('Загружен неверный файл.')
            if avatar.author and not avatar.author == self.instance:
                raise ValidationError('Загружен неверный файл.')
        return data


class SetHeaderImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileModel
        fields = (
            'header_image',
        )

    def validate(self, data):
        header_image = data['header_image']
        if header_image:
            if not header_image.is_image:
                raise ValidationError('Загружен неверный файл.')
            if header_image.author and not header_image.author == self.instance:
                raise ValidationError('Загружен неверный файл.')
        return data


class ChangePasswordSerializer(serializers.ModelSerializer):
    oldPassword = serializers.CharField()
    passwordConfirm = serializers.CharField()

    class Meta:
        model = models.CustomUser
        fields = (
            "id",
            "oldPassword",
            "password",
            "passwordConfirm",
        )

    def validate(self, data):
        user = self.context.get("request").user

        if not user.check_password(data["oldPassword"]):
            raise ValidationError('Неправильно указан текущий пароль!')

        if data["password"] != data["passwordConfirm"]:
            raise ValidationError('Неправильно указано подтверждение нового пароля!')

        password_validation.validate_password(data["password"])
        return data

    def create(self, validated_data):
        user = self.context.get("request").user
        user.set_password(validated_data["password"])
        user.save()
        return user


class SetNewPasswordSerializer(serializers.ModelSerializer):
    passwordConfirm = serializers.CharField()

    class Meta:
        model = models.CustomUser
        fields = (
            'password',
            'passwordConfirm'
        )

    def validate(self, data):
        user = self.context.get("request").user
        if not user.password_generated:
            raise ValidationError('Вы уже изменили пароль')
        if data["password"] != data["passwordConfirm"]:
            raise ValidationError('Неправильно указано подтверждение нового пароля!')

        password_validation.validate_password(data["password"])
        return data

    def create(self, validated_data):
        user = self.context.get("request").user
        user.set_password(validated_data["password"])
        user.password_generated = False
        user.save()
        return user


class SendConfirmCodeSerializer(serializers.Serializer):
    target = serializers.CharField(max_length=20, required=True, allow_null=False, allow_blank=False)
    login = serializers.CharField(max_length=127, required=True, allow_null=False, allow_blank=False)
    invite_token = serializers.CharField(max_length=36, required=False, allow_null=True, allow_blank=True)
    captcha = ReCaptchaV3Field(action="send_confirm_code")
    join_organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True), required=False, allow_null=True
    )

    def validate_login(self, attr):
        return attr.strip().lower()

    def validate(self, attrs):
        attrs.pop('captcha', None)
        login_name = attrs.get('login', '')
        target = attrs.get('target', 'email')
        target_name = utils.get_target_name(target)
        invite_token = attrs.get('invite_token')
        join_organization = attrs.get('join_organization', None)
        if invite_token:
            utils.check_invite_token(invite_token)
        else:
            if INVITE_REGISTER_ONLY and not join_organization:
                raise ValidationError({"message": "Регистрация доступна только по ссылке-приглашению."})
        if not login_name:
            raise ValidationError({"message": f"Некорректный {target_name}."})
        if utils.check_login_exist(login_name):
            raise ValidationError({"message": f"Такой {target_name} уже существует."})
        return attrs


class ForgetPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)
    captcha = ReCaptchaV3Field(action="forgot_password")

    class Meta:
        model = models.ResetPasswordModel
        fields = (
            'id',
            'email',
            'phone',
            'captcha',
        )

    def validate(self, data):
        data.pop('captcha', None)
        email = data.get('email', '')
        if email:
            if not models.CustomUser.objects.filter(email=email,
                                                    is_active=True).exists():
                raise ValidationError('Пользователь не найден!')
        phone = data.get('phone', '')
        if phone:
            if not models.CustomUser.objects.filter(profile__phone=phone, is_active=True).exists():
                raise ValidationError('Пользователь не найден!')
        if not email and not phone:
            raise ValidationError('Пользователь не найден!')
        return data

    def create(self, validated_data):
        email = validated_data.pop('email', '')
        phone = validated_data.pop('phone', '')
        if email:
            user = models.CustomUser.objects.get(email=email,
                                                 is_active=True)
        elif phone:
            user = models.CustomUser.objects.get(profile__phone=phone, is_active=True)
            utils.send_sms_forgot_password(phone)
        else:
            raise ValidationError('Пользователь не найден!')
        instance = models.ResetPasswordModel.objects.create(
            user=user
        )
        if email:
            utils.send_email_forgot_password(instance, user)
        return instance


class ResetPasswordSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)
    password = serializers.CharField()
    password2 = serializers.CharField()

    class Meta:
        model = models.ResetPasswordModel
        fields = (
            'uuid',
            'password',
            'password2',
        )

    def to_representation(self, instance):
        result = {"status": "not found"}
        if self.instance:
            result = {"status": "ok"}
        return result

    def validate(self, data):
        if data['password'] != data['password2']:
            raise ValidationError('Пароли не совпадают!')

        password_validation.validate_password(data['password'])

        return data

    def update(self, reset, validated_data):
        user = reset.user
        user.set_password(self.validated_data['password'])
        user.save()
        reset.changed = True
        reset.save()
        return reset


class LoginCustomUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(required=True)
    captcha = ReCaptchaV3Field(action="login")

    def validate(self, attrs):
        attrs.pop('captcha', None)
        email = attrs.get('email', '')
        phone = attrs.get('phone', '')
        if not email and not phone:
            raise ValidationError("Логин не указан.")
        return attrs


class LoginCustomUserSerializerNoCaptcha(serializers.Serializer):
    """Тот же логин, без проверки reCAPTCHA (для login2)."""
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('email', '')
        phone = attrs.get('phone', '')
        if not email and not phone:
            raise ValidationError("Логин не указан.")
        return attrs


class ProfileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
        )


class ProfileFilterSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        return ""

    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'full_name',
            'avatar',
            'is_support',
        )


class AvatarSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = (
            'id',
            'name',
            'content_type',
            'extension',
            'path',
            'size',
            'is_image'
        )

    def get_content_type(self, instance):
        return getattr(instance, 'mime_type_id', '')

    def get_path(self, instance):
        return instance.avatar_url


class CustomUserDetailSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    middle_name = serializers.SerializerMethodField()
    avatar = AvatarSerializer()
    header_image = AvatarSerializer()
    default_chat = serializers.SerializerMethodField()
    password_generated = serializers.SerializerMethodField()
    contractor_list = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    current_contractor = serializers.SerializerMethodField()
    chat_ai_tooltip = serializers.SerializerMethodField()

    def get_current_contractor(self, instance):
        if current_contractor := instance.current_contractor:
            from common.catalogs.serializers import ContractorModelByIdSerializer
            return ContractorModelByIdSerializer(current_contractor).data
        else:
            return None

    def get_contractor_list(self, instance):
        return instance.contractormodel_set.all().values_list('id', flat=True)

    def get_default_chat(self, instance):
        default_chat = None
        if instance.default_chat:
            default_chat = instance.default_chat.chat_uid

        return default_chat

    def get_password_generated(self, instance):
        return getattr(instance.user, 'password_generated', False)

    def get_username(self, instance):
        return getattr(instance.user, 'username', 'N/A')

    def get_email(self, instance):
        return getattr(instance.user, 'email', 'N/A')

    def get_first_name(self, instance):
        return getattr(instance.user, 'first_name', 'N/A')

    def get_last_name(self, instance):
        return getattr(instance.user, 'last_name', 'N/A')

    def get_middle_name(self, instance):
        return getattr(instance.user, 'middle_name', 'N/A')

    def get_is_staff(self, instance):
        return instance.user.is_staff

    def get_chat_ai_tooltip(self, instance):
        chat_ai_tooltip = instance.chat_ai_tooltip if isinstance(instance.chat_ai_tooltip, dict) else {}
        return {
            'task': bool(chat_ai_tooltip.get('task', False)),
            'event': bool(chat_ai_tooltip.get('event', False)),
            'meeting': bool(chat_ai_tooltip.get('meeting', False)),
            'reports': bool(chat_ai_tooltip.get('reports', False)),
            'notification': bool(chat_ai_tooltip.get('notification', False)),
        }

    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'username',
            'default_chat',
            'support_chat',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'password_generated',
            'contractor_list',
            'avatar',
            # Роли 1С:
            'has_full_access_to_order_tp',
            'has_full_access_to_order_editing',
            'me_logistic_manager_only',
            'can_create_logistic_task',
            'can_set_pay_sum',
            'can_edit_goods_price',
            'is_driver',
            'is_storekeeper',
            'has_full_access_to_order_list',
            'send_geodata',
            'strict_work_schedule',
            'can_create_workgroups',
            'warehouse_select_is_available', 'job_title', 'contact_phone', 'birthday',
            'is_make_events_in_task_automatically',
            'write_me_about_events_in_my_chat',
            'telegram_connect_token',
            'is_support',
            'is_staff',
            'about_me',
            'color',
            'header_image',
            'language',
            'timezone',
            'timezone_auto_detect',
            'current_contractor',
            'has_onboarding_tasks',
            'has_demo_data',
            'use_ai_bot',
            'chat_ai_tooltip',
            'hide_read_notifications',
            'group_notifications',
            'send_to_tg_always',
        )
    def to_representation(self, instance):
        data = super().to_representation(instance)
        my_access_groups = get_my_access_groups(instance)
        data['has_access_group'] = my_access_groups.exists()

        my_access_groups_without_tariffs = get_my_access_groups(instance, contractor_id=None, apply_tariffs=False)
        data['has_admin_access_group'] = my_access_groups_without_tariffs.filter(code='admin').exists()

        data['tariff_section_codes'] = get_available_section_codes(instance) # до 25.03.2026 было get_tariff_section_codes

        tariffs = get_tariffs_id_by_contractors(instance.my_organizations)
        data['has_tariffs'] = bool(tariffs)
        return data


class ChatAiTooltipUpdateSerializer(serializers.Serializer):
    task = serializers.BooleanField(required=False)
    event = serializers.BooleanField(required=False)
    meeting = serializers.BooleanField(required=False)
    reports = serializers.BooleanField(required=False)
    notification = serializers.BooleanField(required=False)


class CachedAppUserSerializer(serializers.Serializer):

    def to_representation(self, instance):
        if isinstance(instance, models.ProfileModel):
            instance_pk = instance.pk
        else:
            instance_pk = instance
        data = cache.get('CachedAppUserSerializer_' + str(instance_pk))
        if not data:
            if isinstance(instance, models.ProfileModel):
                obj = instance
            else:
                obj = models.ProfileModel.objects.get(pk=instance_pk)
            data = AppUserSerializer(instance=obj).data
            cache.set('CachedAppUserSerializer_' + str(instance_pk), data, timeout=None)
        
        # Добавляем вычисление short_name, если оно пустое
        if not data.get('short_name'):
            data['short_name'] = f'{data["last_name"]} {data["first_name"]}'.strip()
            cache.set('CachedAppUserSerializer_' + str(instance_pk), data, timeout=None)
        
        return data


class CachedAppUserPreviewSerializer(serializers.Serializer):

    def to_representation(self, instance):
        if isinstance(instance, models.ProfileModel):
            instance_pk = instance.pk
        else:
            instance_pk = instance
        data = cache.get('CachedAppUserPreviewSerializer_' + str(instance_pk))
        if not data:
            if isinstance(instance, models.ProfileModel):
                obj = instance
            else:
                obj = models.ProfileModel.objects.get(pk=instance_pk)
            data = AppUserPreviewSerializer(instance=obj).data
            cache.set('CachedAppUserPreviewSerializer_' + str(instance_pk), data, timeout=int(datetime.timedelta(days=1).total_seconds()))

        return data


class CachedUserPreviewSerializer(CachedAppUserPreviewSerializer):
    """Backward-compatible alias with explicit ProfileModel preview semantics."""


class AppUserPreviewSerializer(serializers.ModelSerializer):
    """ 
    Неполный сериализатор для превью пользователя.
    Для списков с основной информацией без избыточных данных.
    """
    avatar = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'avatar',
            'username',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'job_title',
            'is_support',
            'last_activity',
        )

    def get_avatar(self, instance):
        return {"path": instance.avatar.avatar_url} if instance.avatar else None

    def get_username(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # return getattr(instance.user, 'username', 'N/A')
        return _("Скрыто")

    def get_email(self, instance):
        return getattr(instance.user, 'email', 'N/A')

    def get_job_title(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # return getattr(instance, 'job_title', '')
        return _("Должность скрыта")


class AppUserShortSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'full_name',
            'short_name',
            'avatar',
            'is_support',
        )

    def get_avatar(self, instance):
        return {"path": instance.avatar.avatar_url} if instance.avatar else None


class AppUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    middle_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar = AvatarSerializer()
    organization_id = serializers.SerializerMethodField()
    current_contractor = serializers.SerializerMethodField()
    # organizations = serializers.SerializerMethodField()

    def get_username(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # return getattr(instance.user, 'username', 'N/A')
        return _("Скрыто")

    def get_email(self, instance):
        return getattr(instance.user, 'email', 'N/A')

    def get_phone(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # return getattr(instance, 'phone', '')
        return _("Скрыто")

    def get_job_title(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # return getattr(instance, 'job_title', '')
        return _("Должность скрыта")

    def get_birthday(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # return getattr(instance, 'birthday', None)
        return _("Скрыто")

    def get_first_name(self, instance):
        return getattr(instance.user, 'first_name', 'N/A')

    def get_last_name(self, instance):
        return getattr(instance.user, 'last_name', 'N/A')

    def get_middle_name(self, instance):
        return getattr(instance.user, 'middle_name', 'N/A')

    def get_full_name(self, instance):
        return instance.full_name

    def get_current_contractor(self, instance):
        # TODO: Заглушка - убрать для показа реальных данных
        # if instance.current_contractor_id:
        #     from common.serializers import CachedBaseModelSerializer
        #     from common.catalogs.serializers import ContractorModelShortSerializer
        #     return CachedBaseModelSerializer(
        #         instance.current_contractor_id,
        #         serializer_class=ContractorModelShortSerializer
        #     ).data
        # return None
        return _("Скрыто")

    def get_organization_id(self, instance):
        return None

    # def get_organizations(self, instance):
    #     my_organizations = instance.my_organizations
    #     if my_organizations:
    #         from common.catalogs.serializers import ContractorModelByINNSerializer
    #         contractors = ContractorModel.objects.filter(pk__in=my_organizations)
    #         return ContractorModelByINNSerializer(contractors, many=True).data
    #     else:
    #         return None

    def to_representation(self, instance):
        # TODO удалить, поскольку изменили CachedAppUserSerializer 26.06.2025
        if not isinstance(instance, models.ProfileModel):
            instance = models.ProfileModel.objects.get(pk=instance)

        data = super().to_representation(instance)

        data['online'] = instance.is_online
        tasks_in_work = getattr(self.context.get('view'), 'tasks_in_work', False)
        if tasks_in_work:
            data['tasks_in_work'] = instance.operator_tasks.filter(is_active=True,
                                                                   status__task_status_type__is_complete=False).values_list('pk',
                                                                         flat=True).distinct().count()

        return data

    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'short_name',
            'avatar',
            # 'avatar_path',
            'organization_id',
            # 'organizations',
            'last_activity',
            'temporary_blocked',
            'is_active',
            'company', 'birthday', 'phone',
            'job_title',
            'is_support',
            'current_contractor',
            'color',
        )


class AppUserDetailSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    middle_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar = AvatarSerializer()
    header_image = AvatarSerializer()
    organization_id = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='user.date_joined')

    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'avatar',
            'username',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'avatar',
            'header_image',
            'organization_id',
            'last_activity',
            'temporary_blocked',
            'is_active',
            'company', 'birthday', 'phone',
            'job_title',
            'is_support',
            'color',
            'about_me',
            'date_joined',
        )

    def get_username(self, instance):
        return getattr(instance.user, 'username', 'N/A')

    def get_email(self, instance):
        return getattr(instance.user, 'email', 'N/A')

    def get_first_name(self, instance):
        return getattr(instance.user, 'first_name', 'N/A')

    def get_last_name(self, instance):
        return getattr(instance.user, 'last_name', 'N/A')

    def get_middle_name(self, instance):
        return getattr(instance.user, 'middle_name', 'N/A')

    def get_full_name(self, instance):
        return instance.full_name

    def get_organization_id(self, instance):
        return None

    def to_representation(self, instance):

        if not isinstance(instance, models.ProfileModel):
            instance = models.ProfileModel.objects.get(pk=instance)

        data = super().to_representation(instance)

        data['online'] = instance.is_online
        tasks_in_work = getattr(self.context.get('view'), 'tasks_in_work', False)
        if tasks_in_work:
            data['tasks_in_work'] = instance.operator_tasks.filter(is_active=True,
                                                                   status__task_status_type__is_complete=False).values_list(
                'pk',
                flat=True).distinct().count()

        return data


class AccessGroupShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessGroupModel
        fields = (
            'id',
            'name',
            'description',
            'is_predefined',
        )


class MyOrganizationUserSerializer(AppUserSerializer):
    class Meta:
        model = ContractorProfileModel
        fields = (
            'user',
        )

    def to_representation(self, instance):
        serializer = CachedAppUserSerializer(str(instance.user_id))
        data = serializer.data
        org_admins = self.context.get('admins', [])
        if instance.user_id in org_admins:
            data['is_org_admin'] = True
        else:
            data['is_org_admin'] = False
        from common.catalogs.models import ContractorDepartmentProfileModel
        contractor = self.context.get('contractor')
        if contractor:
            data['departments'] = list(ContractorDepartmentProfileModel.objects.filter(
                contractor_profile__user=instance.user_id,
                department__is_active=True,
                department__contractor=contractor,
            ).order_by('department__name').values_list('department__name', flat=True))
        access_groups_id = AccessGroupMemberThroughModel.objects.filter(
            member=instance,
            member__contractor=contractor,
        ).values_list('access_group', flat=True)
        access_groups = AccessGroupModel.objects.filter(pk__in=access_groups_id, is_active=True)
        data['access_groups'] = AccessGroupShortSerializer(access_groups, many=True).data
        data['default_ticket_visor'] = instance.default_ticket_visor
        return data


class AppObjectViewerSerializer(serializers.ModelSerializer):
    profile = CachedAppUserSerializer(read_only=True, source='profile_id')

    class Meta:
        model = ObjectViewerRelationModel
        fields = [
            'profile',
            'created_at'
        ]


class AppCustomUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    middle_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    organization_id = serializers.SerializerMethodField()

    def get_username(self, instance):
        return getattr(instance, 'username', 'N/A')

    def get_email(self, instance):
        return getattr(instance, 'email', 'N/A')

    def get_first_name(self, instance):
        return getattr(instance, 'first_name', 'N/A')

    def get_last_name(self, instance):
        return getattr(instance, 'last_name', 'N/A')

    def get_middle_name(self, instance):
        return getattr(instance, 'middle_name', 'N/A')

    def get_id(self, instance):
        return getattr(instance.profile, 'id', 'N/A')

    def get_full_name(self, instance):
        return instance.full_name

    def get_avatar(self, instance):
        return None

    def get_organization_id(self, instance):
        return None

    class Meta:
        model = models.CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'avatar',
            'organization_id',
        )


class CustomUserSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = (ProfileIndex,)
        fields = (
            'profile_id',
        )

    def to_representation(self, instance):
        data = AppUserSerializer(instance.object).data
        return data


class ValidatePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, allow_null=False)
    password_confirm = serializers.CharField(required=True, allow_null=False)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"message": "Пароли не совпадают."})
        password_confirm = data['password_confirm']
        password_validation.validate_password(password_confirm)
        return data


class RegisterUserSerializer(serializers.Serializer):
    password = serializers.CharField()
    password_confirm = serializers.CharField()
    login = serializers.CharField()
    target = serializers.CharField(default='email')
    confirm_token = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    invite_token = serializers.CharField(required=False, max_length=36)
    join_organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True), required=False, allow_null=True
    )

    first_name = serializers.CharField(default='', allow_null=False, required=False)
    last_name = serializers.CharField(default='', allow_null=False, required=False)
    middle_name = serializers.CharField(default='', allow_null=False, required=False)

    class Meta:
        model = models.CustomUser
        fields = (
            'password',
            'password_confirm',
            'login',
            'target',
            'confirm_token',
            'invite_token',
            'join_organization',

            'first_name',
            'last_name',
            'middle_name',
        )

    def validate(self, data):
        join_organization = data.get('join_organization', None)
        invite_token = data.get('invite_token')
        if INVITE_REGISTER_ONLY and not (join_organization or invite_token):
            raise serializers.ValidationError({"message": "Укажите организацию."})
        invite_token = data.get('invite_token')
        if invite_token:
            utils.check_invite_token(invite_token)
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"message": "Пароли не совпадают."})
        password_confirm = data['password_confirm']
        password_validation.validate_password(password_confirm)
        target = data.get('target', 'email')
        target_name = utils.get_target_name(target)
        login_name = data.get('login').lower().strip()
        if not login_name:
            raise ValidationError({"message": f"Некорректный {target_name}."})
        if target == 'email':
            serializers.EmailField().run_validation(login_name)
        if utils.check_login_exist(login_name):
            raise ValidationError({"message": f"Такой {target_name} уже существует."})
        confirm_token = data.get('confirm_token', '')
        if not confirm_token or not utils.check_confirm_token(login_name, target, confirm_token):
            raise ValidationError({"message": f"Код подтверждения устарел. Подтвердите {target_name} еще раз."})
        return data

    def create(self, validated_data):
        join_organization = validated_data.pop('join_organization', None)
        login_name = validated_data.get('login', '').lower().strip()
        invite_token = validated_data.get('invite_token')
        target = validated_data.get('target', 'email')
        username = f"user_{str(uuid.uuid4())}"
        generated_sequence = utils.generate_user_name()
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        middle_name = validated_data.get('middle_name')
        if not (first_name or last_name or middle_name):
            first_name = f"User_{generated_sequence}"
        if target == 'email':
            user = models.CustomUser(username=username, email=login_name)
        else:
            user = models.CustomUser(username=username)
        user.set_password(validated_data['password'])
        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = middle_name
        with transaction.atomic():
            user.save(
                profile_kwargs={
                    "phone": login_name if target == 'phone' else '',
                    "temporary_blocked": True if join_organization else False,
                }
            )
            profile = user.profile
            is_create_new_contractor = utils.get_is_create_new_contractor_from_token(invite_token)
            if invite_token and not is_create_new_contractor:
                contractor = utils.get_organization_from_invite_token(invite_token)
                if not contractor:
                    contact_person = utils.get_contact_person_from_invite_token(invite_token)
                    if not contact_person:
                        raise ValidationError({"message": "Приглашение аннулировано."})
                    else:
                        contact_person.user = profile
                        customer_card = contact_person.customer_card
                        contractor = customer_card.customer
                        from billing.models import ContractorTariffModel, TariffModel
                        from contractor_permissions.models import AccessGroupMemberThroughModel, AccessGroupModel
                        default_tariff = TariffModel.objects.get(code='help_desk_client')
                        if not contractor:
                            contractor = ContractorModel()
                            contractor.name = customer_card.name
                            contractor.full_name = customer_card.name
                            contractor.save()

                            contractor_member = ContractorMemberModel()
                            contractor_member.contractor = contractor
                            contractor_member.name = contractor.name
                            contractor_member.inn = customer_card.inn
                            contractor_member.save()

                            contractor_profile = ContractorProfileModel()
                            contractor_profile.contractor = contractor
                            contractor_profile.user = user
                            contractor_profile.director = True
                            contractor_profile.save()

                            contractor_tariff = ContractorTariffModel()
                            contractor_tariff.contractor = contractor
                            contractor_tariff.tariff = default_tariff
                            contractor_tariff.date_start = timezone.now()
                            contractor_tariff.date_end = contractor_tariff.date_start + datetime.timedelta(weeks=5000)
                            contractor_tariff.save()

                            admin_access_group_member = AccessGroupMemberThroughModel()
                            admin_access_group_member.member = contractor_profile
                            admin_access_group = AccessGroupModel.objects.get(code='admin')
                            admin_access_group_member.access_group = admin_access_group
                            admin_access_group_member.save()
                            client_access_group_member = AccessGroupMemberThroughModel()
                            client_access_group_member.member = contractor_profile
                            client_access_group = AccessGroupModel.objects.get(code='help_desk_client')
                            client_access_group_member.access_group = client_access_group
                            client_access_group_member.save()
                        else:
                            from contractor_permissions.utils import get_tariffs_id_by_contractors
                            if not str(default_tariff.pk) in get_tariffs_id_by_contractors((contractor.pk,)):
                                contractor_tariff = ContractorTariffModel()
                                contractor_tariff.contractor = contractor
                                contractor_tariff.tariff = default_tariff
                                contractor_tariff.date_start = timezone.now()
                                contractor_tariff.date_end = contractor_tariff.date_start + datetime.timedelta(
                                    weeks=5000)
                                contractor_tariff.save()
                            contractor_profile = ContractorProfileModel()
                            contractor_profile.contractor = contractor
                            contractor_profile.user = user
                            contractor_profile.save()

                            client_access_group_member = AccessGroupMemberThroughModel()
                            client_access_group_member.member = contractor_profile
                            client_access_group = AccessGroupModel.objects.get(code='help_desk_client')
                            client_access_group_member.access_group = client_access_group
                            client_access_group_member.save()

                else:
                    contractor_profile = ContractorProfileModel.objects.create(contractor=contractor, user=user.profile)
                    transaction.on_commit(
                        lambda: async_task(notifications.send_notify_about_new_member, str(contractor_profile.pk))
                    )
            else:
                if join_organization:
                    from common.catalogs.models import ContractorProfileRequestModel
                    contractor_request = ContractorProfileRequestModel()
                    contractor_request.user = user.profile
                    contractor_request.organization = join_organization
                    # contractor_request.is_active = False
                    contractor_request.save()
                else:
                    contractor = ContractorModel()
                    contractor.name = f"Company_{generated_sequence}"
                    contractor.full_name = contractor.name
                    contractor.save()

                    contractor_profile = ContractorProfileModel()
                    contractor_profile.contractor = contractor
                    contractor_profile.user = user.profile
                    contractor_profile.director = True
                    contractor_profile.save()

                    contractor_member = ContractorMemberModel()
                    contractor_member.contractor = contractor
                    contractor_member.name = contractor.name
                    contractor_member.inn = validated_data.get('contractor_bin', '')
                    contractor_member.save()
            utils.delete_confirm_token(login_name, target)
            utils.accept_invite(invite_token, user.profile)
        return user


class UserIntroSerializer(serializers.Serializer):
    contractor_name = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=False, default="")
    contractor_bin = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=False, default="")
    contractor_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=False, default="")

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        user = self.context.get('user')
        with transaction.atomic():

            user.first_name = validated_data.get('first_name', '')
            user.last_name = validated_data.get('last_name', '')
            user.middle_name = validated_data.get('middle_name', '')
            user.save(update_fields=('first_name', 'last_name', 'middle_name',),)

            contractor_profile = user.profile.contractor_profile.filter(director=True).first()
            if contractor_profile:
                contractor = contractor_profile.contractor
                contractor_name = validated_data.get('contractor_name', '')
                if not contractor_name:
                    raise ValidationError({"message": "Не указано наименование организации."})
                contractor.name = validated_data.get('contractor_name', '')
                contractor.phone = validated_data.get('contractor_phone', '')
                contractor.save()

                contractor_member = ContractorMemberModel.objects.filter(contractor=contractor).first()
                if contractor_member:
                    contractor_member.name = contractor.name
                    contractor_member.inn = validated_data.get('contractor_bin', '')
                    contractor_member.save(update_fields=('name', 'inn',))
        async_task(utils.index_contractor_profile_requests, user.profile.pk)

    def to_representation(self, instance):
        return


class RegisterUserB2GSerializer(serializers.Serializer):
    password = serializers.CharField()
    password_confirm = serializers.CharField()
    login = serializers.CharField()
    target = serializers.CharField(default='email')
    confirm_token = serializers.CharField(required=True, allow_null=False, allow_blank=False)
    invite_token = serializers.CharField(required=False, max_length=36)

    first_name = serializers.CharField(default='', allow_null=False, required=False)
    last_name = serializers.CharField(default='', allow_null=False, required=False)
    middle_name = serializers.CharField(default='', allow_null=False, required=False)

    class Meta:
        model = models.CustomUser
        fields = (
            'password',
            'password_confirm',
            'login',
            'target',
            'confirm_token',
            'invite_token',

            'first_name',
            'last_name',
            'middle_name',
        )

    def validate(self, data):
        join_organization = data.get('join_organization', None)
        invite_token = data.get('invite_token')
        if INVITE_REGISTER_ONLY and not (join_organization or invite_token):
            raise serializers.ValidationError({"message": "Укажите организацию."})
        invite_token = data.get('invite_token')
        if invite_token:
            utils.check_invite_token(invite_token)
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"message": "Пароли не совпадают."})
        password_confirm = data['password_confirm']
        password_validation.validate_password(password_confirm)
        target = data.get('target', 'email')
        target_name = utils.get_target_name(target)
        login_name = data.get('login').lower().strip()
        if not login_name:
            raise ValidationError({"message": f"Некорректный {target_name}."})
        if target == 'email':
            serializers.EmailField().run_validation(login_name)
        if utils.check_login_exist(login_name):
            raise ValidationError({"message": f"Такой {target_name} уже существует."})
        confirm_token = data.get('confirm_token', '')
        if not confirm_token or not utils.check_confirm_token(login_name, target, confirm_token):
            raise ValidationError({"message": f"Код подтверждения устарел. Подтвердите {target_name} еще раз."})
        return data

    def create(self, validated_data):
        join_organization = validated_data.pop('join_organization', None)
        login_name = validated_data.get('login', '').lower().strip()
        invite_token = validated_data.get('invite_token')
        target = validated_data.get('target', 'email')
        username = f"user_{str(uuid.uuid4())}"
        generated_sequence = utils.generate_user_name()
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        middle_name = validated_data.get('middle_name')
        if not (first_name or last_name or middle_name):
            first_name = f"User_{generated_sequence}"
        if target == 'email':
            user = models.CustomUser(username=username, email=login_name)
        else:
            user = models.CustomUser(username=username)
        user.set_password(validated_data['password'])
        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = middle_name
        with transaction.atomic():
            user.save(
                profile_kwargs={
                    "phone": login_name if target == 'phone' else '',
                    "temporary_blocked": True if join_organization else False,
                }
            )
            profile = user.profile
            if invite_token:

                is_create_new_contractor = utils.get_is_create_new_contractor_from_token(invite_token)
                if is_create_new_contractor:
                    contractor = utils.create_demo_contractor(profile)
                else:
                    contractor = utils.get_organization_from_invite_token(invite_token)
                    if not contractor:
                        contact_person = utils.get_contact_person_from_invite_token(invite_token)
                        if not contact_person:
                            raise ValidationError({"message": "Приглашение аннулировано."})
                        contact_person.user = profile
                        contact_person.unknown = False
                        contact_person.save(update_fields=('user', 'unknown'))
                        customer_card = contact_person.customer_card
                        contractor = customer_card.customer
                        from billing.models import ContractorTariffModel, TariffModel
                        default_tariff = TariffModel.objects.get(code='help_desk_client')
                        if not contractor:
                            contractor = utils.create_customer_card_contractor(customer_card, profile)
                            utils.create_contractor_profile(contractor, profile, 'help_desk_client')
                        else:
                            from contractor_permissions.utils import get_tariffs_id_by_contractors
                            if not str(default_tariff.pk) in get_tariffs_id_by_contractors((contractor.pk,)):
                                contractor_tariff = ContractorTariffModel()
                                contractor_tariff.contractor = contractor
                                contractor_tariff.tariff = default_tariff
                                contractor_tariff.date_start = timezone.now()
                                contractor_tariff.date_end = contractor_tariff.date_start + datetime.timedelta(days=default_tariff.duration)
                                contractor_tariff.save()
                            if customer_card.client_guest:
                                contractor_profile = utils.create_contractor_profile(contractor, profile, 'help_desk_client_guest')
                            else:
                                contractor_profile = utils.create_contractor_profile(contractor, profile, 'help_desk_client')
                    else:
                        contractor_profile = utils.create_contractor_profile(contractor, profile, 'contractor_guest')
                        transaction.on_commit(
                            lambda: async_task(notifications.send_notify_about_new_member, str(contractor_profile.pk))
                        )
                        transaction.on_commit(
                            lambda: async_task(notifications.send_notify_about_welcome, str(profile.pk))
                        )
            else:
                utils.create_entry_info_for_user(user.profile)
            utils.delete_confirm_token(login_name, target)
            utils.accept_invite(invite_token, user.profile)
        return user


class EntryInfoModelDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EntryInfoModel
        fields = (
            'id',
            'data',
            'complete',
        )


class EntryInfoModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EntryInfoModel
        fields = (
            'id',
            'data',
            'complete',
        )

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if instance.complete:
                serializer = UserIntroDataSaveSerializer(
                    data=instance.data,
                    context={
                        'user': instance.user,
                    }
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                contractor = serializer.context.get('contractor')
                if contractor:
                    instance.contractor = contractor
                    instance.save(update_fields=('contractor',))
        async_task(utils.index_contractor_profile_requests, str(instance.user.pk))
        return instance


class UserIntroDataSaveSerializer(serializers.ModelSerializer):
    contractor_name = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=False,
                                            default="")
    contractor_bin = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=False,
                                           default="")
    join_organization = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True), required=False, allow_null=True
    )
    invite_token = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=36)
    invite_emails = serializers.ListField(required=False, allow_null=True, allow_empty=True,)
    demo_data = serializers.BooleanField(required=False, default=False)
    need_meeting = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = models.EntryInfoModel
        fields = (
            'id',
            'contractor_name',
            'contractor_bin',
            'join_organization',
            'invite_token',
            'invite_emails',
            'demo_data',
            'need_meeting',
        )

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        join_organization = validated_data.get('join_organization', None)
        contractor_name = validated_data.get('contractor_name', None)
        user = self.context.get('user')

        with transaction.atomic():
            if join_organization:
                from common.catalogs.models import ContractorProfileRequestModel
                contractor_request = ContractorProfileRequestModel()
                contractor_request.user = user
                contractor_request.organization = join_organization
                contractor_request.save()
                transaction.on_commit(lambda: async_task(utils.initial_contractor_request, str(contractor_request.pk)))
            else:
                contractor = utils.create_demo_contractor(user, contractor_name)
                self.context['contractor'] = contractor

                # # Прописываем организацию в инвайт, если он есть # TODO ЗАЧЕМ МЫ ЭТО ДЕЛАЕМ?????
                # invite_token = validated_data.get('invite_token')
                # if invite_token:
                #     try:
                #         invite = models.InviteModel.objects.get(token=invite_token)
                #     except models.InviteModel.DoesNotExist:
                #         pass
                #     else:
                #         invite.contractor = contractor
                #         invite.save(update_fields=('contractor',))

                # Приглашаем новых пользователей, если указаны email
                invite_emails = validated_data.get('invite_emails')
                if invite_emails:
                    invite_emails = set(invite_emails)
                    invite_emails.discard('')
                    invite_emails.discard(None)
                    for invite_email in invite_emails:
                        invite_email = invite_email.replace(' ', '')
                        if invite_email:
                            invite_email_serializer = EmailInviteModelCreateSerializer(
                                data={'email': invite_email},
                                context={'contractor': contractor}
                            )
                            invite_email_serializer.is_valid(raise_exception=True)
                            invite_email_serializer.save()
                
                # Создаем демо-данные, если пользователь их запросил.
                demo_data = validated_data.get('demo_data', None)
                if demo_data:
                    from demo.utils import create_demo_data
                    create_demo_data(user.pk)

                # Посылаем запрос на демонстрацию, если пользователь ее запросил
                need_meeting = validated_data.get('need_meeting', False)
                if need_meeting:
                    leave_request_instance = models.LeaveRequestModel.objects.create(
                        request_type_id='request_demonstration',
                        email=user.user.email,
                        name=user.full_name,
                    )
                    from .utils import send_leave_request_email
                    transaction.on_commit(lambda: async_task(send_leave_request_email, str(leave_request_instance.pk)))

    def to_representation(self, instance):
        return


class CustomUserUpdateSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(allow_null=True, allow_blank=True)
    contact_phone = serializers.CharField(allow_null=True, allow_blank=True)
    birthday = serializers.DateField(allow_null=True)
    is_make_events_in_task_automatically = serializers.BooleanField(allow_null=True)
    hide_read_notifications = serializers.BooleanField(allow_null=True)
    group_notifications = serializers.BooleanField(allow_null=True)
    send_to_tg_always = serializers.BooleanField(allow_null=True)
    about_me = serializers.CharField(allow_null=True, allow_blank=True)
    color = serializers.CharField(allow_null=True, allow_blank=True)
    language = serializers.CharField(allow_null=True, allow_blank=True)
    timezone = serializers.CharField(required=False)
    timezone_auto_detect = serializers.BooleanField(required=False)

    class Meta:
        model = models.CustomUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "middle_name",
            'is_make_events_in_task_automatically',
            'hide_read_notifications',
            'group_notifications',
            'send_to_tg_always',
            'job_title',
            'birthday',
            'contact_phone',
            'about_me',
            'color',
            'language',
            'timezone',
            'timezone_auto_detect',
        )

    def validate_timezone(self, value):
        if value in (None, ''):
            return value
        if value not in pytz.common_timezones:
            raise ValidationError('Некорректный часовой пояс. Используйте IANA timezone, например Europe/Moscow.')
        return value

    def update(self, instance, validated_data):
        profile = instance.profile
        profile_field_names = {
            field.name
            for field in profile._meta.get_fields()
            if getattr(field, 'concrete', False) and not getattr(field, 'many_to_many', False)
        }
        user_updates = {}
        profile_update_fields = []

        for field_name, field_value in validated_data.items():
            if field_name in profile_field_names:
                setattr(profile, field_name, field_value)
                profile_update_fields.append(field_name)
            else:
                user_updates[field_name] = field_value

        if user_updates:
            instance = super().update(instance, user_updates)
        if profile_update_fields:
            profile.save(update_fields=profile_update_fields)

        return instance

    def to_representation(self, instance):
        return AppUserSerializer(instance).data


class InviteModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InviteModel
        fields = (
            "id",
            "deactivate_at",
            "workgroup",
            "is_create_new_contractor",
        )

    def create(self, validated_data):
        contractor = self.context.get('contractor')
        instance = models.InviteModel.objects.create(contractor=contractor, **validated_data)
        return instance


class EmailInviteModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmailInviteModel
        fields = (
            "id",
            "email",
            "workgroup",
            "is_create_new_contractor",
        )

    def create(self, validated_data):
        contractor = self.context.get('contractor')
        instance = models.EmailInviteModel.objects.create(contractor=contractor, **validated_data)
        transaction.on_commit(lambda: async_task(utils.send_email_invite, instance))
        return instance


class EmailInviteListSerializer(serializers.ModelSerializer):
    accepted_user = AppUserSerializer()
    workgroup = serializers.SerializerMethodField()

    class Meta:
        model = models.EmailInviteModel
        fields = (
            "id",
            "accepted_user",
            "created_at",
            "email",
            "is_accepted",
            "is_sent",
            "workgroup",
            "is_create_new_contractor",
        )

    def get_workgroup(self, instance):
        workgroup = instance.workgroup
        if workgroup:
            return {"id": instance.workgroup_id, "name": workgroup.name}
        return None


class InviteInfoSerializer(serializers.Serializer):
    from bpms.workgroups.serializers import WorkgroupNameLogoSerializer
    id = serializers.CharField()
    token = serializers.CharField()
    created_at = serializers.DateTimeField()
    is_create_new_contractor = serializers.BooleanField()
    author = CachedAppUserPreviewSerializer(read_only=True, source='author_id')
    contractor = AppOrganizationSerializer()
    workgroup = WorkgroupNameLogoSerializer()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.contractor:
            data['name'] = instance.contractor.name
            data['full_name'] = instance.contractor.full_name
            data['support_email'] = SUPPORT_EMAIL
        return data


class EmailNotifiProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    def get_email(self, instance):
        return instance.user.email

    class Meta:
        model = models.ProfileModel
        fields = (
            'full_name',
            'email',
            'phone'
        )


class TokenContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name',
            'full_name',
        )


class UserActivitiesSerializer(CachedAppUserSerializer):
    class Meta:
        model = models.ProfileModel
        fields = (
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'avatar',
            'is_support',
        )

    def to_representation(self, instance):
        from bpms.personal_planes.serializers import PlanForUserSerializer
        data = super().to_representation(instance)
        # Фильтруем только нужные поля
        data = {k: v for k, v in data.items() if k in self.Meta.fields}

        query_params = self.context.get('request').query_params
        plane_datetime_gte = query_params.get('start')
        plane_datetime_lte = query_params.get('end')
        plane_date_gte = plane_datetime_gte[:10]
        plane_date_lte = plane_datetime_lte[:10]
        if not plane_date_gte or not plane_date_lte:
            return data
        # Дейлики
        if instance.pk in self.context.get('plans_users'):
            try:
                plans = PersonalPlaneModel.objects.filter(
                    author=instance,
                    plane_date__gte=plane_date_gte,
                    plane_date__lte=plane_date_lte
                ).annotate(
                    count=Count('plane_items')
                ).order_by('plane_date')
            except ValidationError:
                data['plans'] = []
            else:
                data['plans'] = PlanForUserSerializer(plans, many=True, ).data
        else:
            data['plans'] = []
        # События
        if instance.pk in self.context.get('events_users'):
            plane_datetime_gte = serializers.DateTimeField().to_internal_value(plane_datetime_gte)
            plane_datetime_lte = serializers.DateTimeField().to_internal_value(plane_datetime_lte)
            gte = plane_datetime_gte
            plane_date_gte = serializers.DateField().to_internal_value(plane_date_gte)
            day_list = []
            event_calendar_qs = EventCalendarModel.objects.filter(
                is_active=True,
                calendar__is_active=True,
                members=instance,
            )
            for each in range(0, (plane_datetime_lte - plane_datetime_gte).days + 1):
                lt = gte + datetime.timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
                event_count = event_calendar_qs.filter(
                    Q(start_at__gte=gte) | Q(end_at__gte=gte),
                    Q(start_at__lte=lt) | Q(end_at__lte=lt),
                ).count()
                day_list.append({'start': gte, 'end': lt, 'count': event_count, 'date': plane_date_gte.strftime("%Y-%m-%d")})
                gte += datetime.timedelta(days=1)
                plane_date_gte += datetime.timedelta(days=1)
            data['events'] = day_list
        else:
            data['events'] = []
        return data



class LeaveRequestSerializer(serializers.ModelSerializer):
    """Сериализатор функции 'Запросить демонстрацию' на сайте."""

    class Meta:
        model = models.LeaveRequestModel
        fields = (
            'id',
            'created_at',
            'name',
            'phone',
            'email',
            'privacy_policy_consent',
            'marketing_consent',
            'request_type',
            'data',
        )

    def create(self, validated_data):
        request = self.context.get('request')
        
        with transaction.atomic():
            instance = super().create(validated_data)
            transaction.on_commit(lambda: async_task(utils.send_leave_request_email, str(instance.pk)))
        return instance


class NewUserContractorSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'code',
            'name',
            'phone',
            'logo',
            'email',

        )

    def get_logo(self, instance):
        if instance.logo:
            return get_logo_url(instance.logo)
        else:
            return ''


class NewUserInfoListSerializer(serializers.ModelSerializer):
    user = CachedAppUserPreviewSerializer(source='user_id')
    contractor = NewUserContractorSerializer()
    support_chat = serializers.SerializerMethodField()

    class Meta:
        model = models.NewUserInfoModel
        fields = (
            'id',
            'user',
            'contractor',
            'created_at',
            'is_chat_welcome_sent',
            'support_chat',
        )

    def get_support_chat(self, obj):
        return obj.user.support_chat

    def to_representation(self, instance):
        data = super().to_representation(instance)
        contractor = instance.contractor
        if contractor:
            now = self.context.get('now')
            if not now:
                now = timezone.now()
                self.context['now'] = now
            org_tariffs = set(contractor.contractor_tariffs.filter(
                date_start__lte=now,
                date_end__gte=now,
                is_active=True,
                tariff__is_active=True
            ).values_list('tariff__name', flat=True))
            data['tariffs'] = list(org_tariffs)
        else:
            data['tariffs'] = []
        return data


class NewUserInfoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NewUserInfoModel
        fields = ('is_chat_welcome_sent',)


class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    captcha = ReCaptchaV3Field(action="check_email")

    def validate(self, data):
        data.pop('captcha', None)
        email = data.get('email').lower().strip()
        is_user_exists = models.CustomUser.objects.filter(
            is_active=True,
            email=email
        ).exists()
        return {'is_user_exists': is_user_exists}
