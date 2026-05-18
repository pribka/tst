from drf_haystack.serializers import HaystackSerializer
from rest_framework import exceptions as drf_exceptions
from rest_framework import serializers
from django.db import transaction
from django.db.models import Q, Count
from datetime import timedelta

from bpms.bpms_common import serializers as bpms_serializers
from bpms.favorites import mixins as f_mixins
from bpms.tasks.models import TaskModel
from bpms.tasks.utils import get_tasks_status_count
from common.catalogs import serializers as catalog_serializers
from common.catalogs.models import ContractorModel, ContractorRelationTypeModel, WorkDirectionModel
from common.catalogs.serializers import (
    ContractorsToAddSerializer,
    ContractorRelationTypeModelListSerializer,
    AppCurrencySerializer,
    WorkDirectionListSerializer,
)
from common.models import BaseModel, FileBaseModel, FileBaseUpdateModel  # noqa: F401
from common.serializers import AppFileSerializer, CachedBaseModelSerializer
from common.utils import get_serialized_attachments
from common.fields import RoundingDecimalField
from contractor_permissions.utils import check_contractor_permission
from users.serializers import (AvatarSerializer,
                               CachedAppUserSerializer,
                               AppUserShortSerializer)
from users.models import ProfileModel

from common.accounting_catalogs.serializers import CachedKATOCodesModelSerializer
from bpms.favorites.utils import get_in_favorites
from . import models, search_indexes, utils  # noqa: F401
from bpms.tasks.utils import get_gantt_chart_task_queryset


class WorkgroupNotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupModel
        fields = (
            'id',
            'name',

        )


class WorkgroupTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupTypes
        fields = [
            "id",
            "name"
        ]


class WorkgroupStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupStatus
        fields = [
            "id",
            "name",
        ]


class WorkgroupMembershipRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupMembershipRole
        fields = [
            "id",
            "name",
            "code",
        ]


class WorkgroupMembershipStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupMembershipStatus
        fields = [
            "id",
            "name",
            "code",
        ]


class WorkgroupListSerializer(serializers.ModelSerializer):
    founder = serializers.SerializerMethodField()
    # tasks = serializers.SerializerMethodField()
    # complete_tasks = serializers.SerializerMethodField()
    # tasks_status_count = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()
    # add_file_at = serializers.SerializerMethodField()
    # updated_at = serializers.SerializerMethodField()
    finished_date = serializers.DateTimeField(input_formats=['%Y-%m-%d'], allow_null=True, required=False)
    workgroup_logo = AvatarSerializer()
    organization = CachedBaseModelSerializer(source='organization_id', serializer_class=catalog_serializers.ContractorModelShortSerializer)
    # location = CachedKATOCodesModelSerializer(source='location_id')
    # location_point = catalog_serializers.LocationPointSerializer()
    
    # def get_attachments(self, instance):
    #     return get_serialized_attachments(instance)

    def get_founder(self, obj: models.WorkgroupModel):
        # Используем предзагруженные данные из prefetch_related
        # FOUNDER может быть только один, поэтому берем первый элемент
        if hasattr(obj, 'founder_member') and obj.founder_member:
            founder = obj.founder_member[0]
            return WorkgroupMembershipSerializer(founder, context=self.context).data
        else:
            # Fallback на прямой запрос, если prefetch не был применен
            try:
                founder = models.WorkgroupMembersModel.objects.get(
                    work_group=obj,
                    is_active=True,
                    membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED"),
                    membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER")
                )
                return WorkgroupMembershipSerializer(founder, context=self.context).data
            except models.WorkgroupMembersModel.DoesNotExist:
                return None

    # def get_tasks(self, obj: models.WorkgroupModel):
    #     if not obj.is_project:
    #         return TaskModel.objects.filter(is_active=True, workgroup=obj, task_type='task').count()
    #     else:
    #         return TaskModel.objects.filter(is_active=True, project=obj, task_type='task').count()

    # def get_complete_tasks(self, obj: models.WorkgroupModel):
    #     if not obj.is_project:
    #         return TaskModel.objects.filter(is_active=True, workgroup=obj, task_type='task', status="completed").count()
    #     else:
    #         return TaskModel.objects.filter(is_active=True, project=obj, task_type='task', status="completed").count()

    # def get_tasks_status_count(self, obj: models.WorkgroupModel):
    #     if not obj.is_project:
    #         return None
    #     queryset = TaskModel.objects.filter(is_active=True, project=obj)
    #     data = get_tasks_status_count(queryset)
    #     return data

    def get_finished(self, obj: models.WorkgroupModel):
        if not obj.is_project:
            return None
        else:
            return obj.is_finished

    # def get_add_file_at(self, instance):
    #     if FileBaseModel.objects.filter(is_active=True, related_object=instance).exists():
    #         return FileBaseModel.objects.filter(
    #             is_active=True,
    #             related_object=instance).order_by('-created_at').first().created_at
    #     return ''

    # def get_updated_at(self, instance):
    #     if FileBaseUpdateModel.objects.filter(is_active=True, related_object=instance).exists():
    #         return FileBaseUpdateModel.objects.filter(
    #             is_active=True,
    #             related_object=instance).order_by('-created_at').first().updated_at
    #     return ''

    class Meta:
        model = models.WorkgroupModel
        fields = [
            'id',
            'name',
            'workgroup_logo',
            # 'social_links',
            'public_or_private',
            'created_at',
            'founder',
            # 'tasks',
            # 'complete_tasks',
            # 'tasks_status_count',
            'date_start_plan',
            'dead_line',
            'finished_date',
            # 'program',
            'finished',
            # 'add_file_at',
            # 'updated_at',
            'organization',
            # 'location_point',
            # 'location',
            'control_dates',
            'funds',
            'progress',
        ]

    def to_representation(self, instance: models.WorkgroupModel):
        request = self.context.get('request', None)
        data = super().to_representation(instance=instance)
        
        # Используем предзагруженные данные из prefetch_related вместо новых запросов
        # Проверяем, есть ли предзагруженные участники через to_attr='approved_members'
        if hasattr(instance, 'approved_members'):
            work_group_members = instance.approved_members
        else:
            # Fallback на прямой запрос, если prefetch не был применен (например, для детального просмотра)
            approved_status = models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
            work_group_members = models.WorkgroupMembersModel.objects.filter(
                is_active=True,
                work_group=instance,
                membership_request_status=approved_status
            )

        data["workgroup_members"] = WorkgroupMembershipSerializer(
            work_group_members, many=True, context=self.context
        ).data
        # if instance.counterparty:
        #     data["counterparty"] = bpms_serializers.CounterpartyModelBaseSerializer(instance.counterparty).data
        # if instance.costing_object:
        #     data["costing_object"] = bpms_serializers.CostingObjectBaseSerializer(instance.costing_object).data
        data['in_favorites'] = get_in_favorites(instance)
        return data


class WorkgroupGanttChartSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='name')
    start_date = serializers.DateTimeField(source='date_start_plan', read_only=True, format="%d-%m-%Y %H:%M")
    end_date = serializers.DateTimeField(source='dead_line', read_only=True, format="%d-%m-%Y %H:%M")
    duration = serializers.IntegerField(source='duration_minutes')
    type = serializers.SerializerMethodField()
    has_child = serializers.SerializerMethodField()
    workgroup_logo = AvatarSerializer()

    class Meta:
        model = models.WorkgroupModel
        fields = [
            'id',
            'text',
            'start_date',
            'end_date',
            'duration',
            'type',
            'has_child',
            'workgroup_logo',
            'progress',
        ]

    def get_type(self, instance):
        task_type = 'project' if instance.is_project else 'workgroup'
        return task_type

    def get_has_child(self, instance):
        # Проверяем, существуют ли задачи, которые мы можем показывать в диаграмме Ганта
        request = self.context['request']
        # Убираем page_name из get-параметров запроса.
        # Потому что фильтры должны действовать только на проекты, но не на задачи.
        request.query_params._mutable = True
        try:
            del request.query_params['page_name']
        except KeyError:
            pass
        request.query_params._mutable = False

        if instance.is_project:
            queryset = instance.project_tasks.all()
            queryset = get_gantt_chart_task_queryset(request, queryset)
            return queryset.exists()
        else:
            queryset = instance.workgroup_tasks.all()
            queryset = get_gantt_chart_task_queryset(request, queryset)
            return queryset.exists()


class WorkgroupCreateSerializer(serializers.ModelSerializer):
    founder = serializers.PrimaryKeyRelatedField(
        queryset=ProfileModel.objects.filter(is_active=True),
        allow_empty=True,
        required=False,
    )

    work_directions = serializers.PrimaryKeyRelatedField(
        queryset=WorkDirectionModel.objects.filter(is_active=True),
        allow_empty=True,
        required=False,
        many=True,
    )

    class Meta:
        model = models.WorkgroupModel
        fields = [
            'id',
            'founder',
            'name',
            'workgroup_logo',
            'description',
            'workgroup_type',
            'social_links',
            'public_or_private',
            'created_at',
            'is_project',
            'date_start_plan',
            'dead_line',
            'finished_date',
            'is_overdue',
            'linked_chat',
            'with_chat',
            'program',
            'counterparty',
            'costing_object',
            'control_dates',
            'is_helpdesk',
            'organization',
            'location_point',
            'location',
            'funds',
            'funds_currency',
            'metadata',
            'work_directions',
        ]

    def validate_organization(self, organization):
        if organization:
            user = self.context.get('request').user.profile
            try:
                check_contractor_permission(user.pk, organization.pk, 'create_workgroup', None)
            except drf_exceptions.PermissionDenied:
                contractor_permission = False
            else:
                contractor_permission = True
            if not contractor_permission:
                from users.utils import check_update_organization_permission
                check_update_organization_permission(organization.pk, user)
        return organization

    def validate(self, attrs):
        if attrs.get('use_template') and attrs.get('template') is None:
            raise serializers.ValidationError('Template is required.')
        return attrs

    def create(self, validated_data):
        founder = validated_data.pop('founder', None)
        user = self.context.get('request').user.profile
        with transaction.atomic():
            instance = super().create(validated_data)
            if founder:
                models.WorkgroupMembersModel.objects.create(
                    member=founder,
                    work_group=instance,
                    membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER"),
                    membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
                )
                if not founder == user:
                    models.WorkgroupMembersModel.objects.create(
                        member=user,
                        work_group=instance,
                        membership_role=models.WorkgroupMembershipRole.objects.get(code="MODERATOR"),
                        membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
                    )
            else:
                models.WorkgroupMembersModel.objects.create(
                    member=user,
                    work_group=instance,
                    membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER"),
                    membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
                )
            location_point_dict = self.initial_data.get('location_point')
            if location_point_dict:
                location_point_dict['related_object'] = str(instance.pk)
                location_point_serializer = catalog_serializers.LocationPointCreateSerializer(
                    data=location_point_dict,
                    context=self.context
                )
                location_point_serializer.is_valid(raise_exception=True)
                location_point_serializer.save()
        return instance
    
    def to_representation(self, instance):
        return WorkgroupDetailSerializer(instance).data


class WorkgroupUpdateSerializer(serializers.ModelSerializer):
    work_directions = serializers.PrimaryKeyRelatedField(
        queryset=WorkDirectionModel.objects.filter(is_active=True),
        allow_empty=True,
        required=False,
        many=True,
    )

    def validate_organization(self, organization):
        old_organization = self.instance.organization
        if organization and not old_organization == organization:
            user = self.context.get('request').user.profile
            try:
                check_contractor_permission(user.pk, organization.pk, 'create_workgroup', None)
            except drf_exceptions.PermissionDenied:
                contractor_permission = False
            else:
                contractor_permission = True
            if not contractor_permission:
                from users.utils import check_update_organization_permission
                check_update_organization_permission(organization.pk, user)
        return organization

    def validate(self, attrs):
        if attrs.get('use_template') and attrs.get('template') is None:
            raise serializers.ValidationError('Template is required.')
        return attrs

    class Meta:
        model = models.WorkgroupModel
        fields = [
            'id',
            'name',
            'workgroup_logo',
            'description',
            'workgroup_type',
            'social_links',
            'public_or_private',
            'created_at',
            'is_project',
            'date_start_plan',
            'dead_line',
            'finished_date',
            'is_overdue',
            'linked_chat',
            'with_chat',
            'program',
            'counterparty',
            'costing_object',
            'control_dates',
            'is_helpdesk',
            'organization',
            'location_point',
            'location',
            'funds',
            'funds_currency',
            'metadata',
            'work_directions',
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if 'location_point' in self.initial_data:
                location_point_dict = self.initial_data.get('location_point')
                old_location_point = instance.location_point
                if location_point_dict:
                    location_point_dict['related_object'] = str(instance.pk)
                    location_point_serializer = catalog_serializers.LocationPointCreateSerializer(
                        data=location_point_dict,
                        context=self.context
                    )
                    location_point_serializer.is_valid(raise_exception=True)
                    location_point_serializer.save()
                if old_location_point:
                    old_location_point.delete()
        return instance
    
    def to_representation(self, instance):
        return WorkgroupDetailSerializer(instance).data


class WorkgroupDetailSerializer(serializers.ModelSerializer):
    founder = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    complete_tasks = serializers.SerializerMethodField()
    finished = serializers.SerializerMethodField()
    add_file_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    linked_chat_id = serializers.SerializerMethodField()
    finished_date = serializers.DateTimeField(input_formats=['%Y-%m-%d'], allow_null=True, required=False)
    location = CachedKATOCodesModelSerializer(source='location_id')
    location_point = catalog_serializers.LocationPointSerializer()
    funds_currency = AppCurrencySerializer()
    work_directions = WorkDirectionListSerializer(many=True)

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def get_founder(self, obj: models.WorkgroupModel):
        founder = models.WorkgroupMembersModel.objects.get(
            work_group=obj,
            membership_role=models.WorkgroupMembershipRole.objects.get(code="FOUNDER")
        )
        return WorkgroupMembershipSerializer(founder).data

    def get_tasks(self, obj: models.WorkgroupModel):
        if not obj.is_project:
            return TaskModel.objects.filter(is_active=True, workgroup=obj, task_type='task').count()
        else:
            return TaskModel.objects.filter(is_active=True, project=obj, task_type='task').count()

    def get_complete_tasks(self, obj: models.WorkgroupModel):
        if not obj.is_project:
            return TaskModel.objects.filter(is_active=True, workgroup=obj, task_type='task', status="completed").count()
        else:
            return TaskModel.objects.filter(is_active=True, project=obj, task_type='task', status="completed").count()

    def get_finished(self, obj: models.WorkgroupModel):
        if not obj.is_project:
            return None
        else:
            return obj.is_finished

    def get_add_file_at(self, instance):
        if FileBaseModel.objects.filter(is_active=True, related_object=instance).exists():
            return FileBaseModel.objects.filter(
                is_active=True,
                related_object=instance).order_by('-created_at').first().created_at
        return ''

    def get_updated_at(self, instance):
        if FileBaseUpdateModel.objects.filter(is_active=True, related_object=instance).exists():
            return FileBaseUpdateModel.objects.filter(
                is_active=True,
                related_object=instance).order_by('-created_at').first().updated_at
        return ''

    def get_linked_chat_id(self, instance):
        if instance.linked_chat is not None:
            return instance.linked_chat.id
        return None
    
    class Meta:
        model = models.WorkgroupModel
        fields = [
            'id',
            'name',
            'workgroup_logo',
            'description',
            'workgroup_type',
            'social_links',
            'public_or_private',
            'created_at',
            'founder',
            'tasks',
            'complete_tasks',
            'is_project',
            'date_start_plan',
            'dead_line',
            'finished_date',
            'is_overdue',
            'linked_chat',
            'linked_chat_id',
            'with_chat',
            'program',
            'counterparty',
            'costing_object',
            'finished',
            'control_dates',
            'frontend_route',
            'is_helpdesk',
            'add_file_at',
            'updated_at',
            'organization',
            'location_point',
            'location',
            'funds',
            'funds_currency',
            'metadata',
            'progress',
            'work_directions',
        ]

    def to_representation(self, instance: models.WorkgroupModel):
        request = self.context.get('request', None)
        data = super(WorkgroupDetailSerializer, self).to_representation(instance=instance)
        work_group_members = models.WorkgroupMembersModel.objects.filter(
            is_active=True,
            work_group=instance,
            membership_request_status=models.WorkgroupMembershipStatus.objects.get(code="APPROVED")
        )
        data['members_count'] = work_group_members.count()
        data["workgroup_members"] = WorkgroupMembershipSerializer(
            work_group_members, many=True
        ).data
        data["news"] = bpms_serializers.NewsLiteSerializer(instance.newsmodel_set, many=True).data
        data["workgroup_type"] = WorkgroupTypesSerializer(instance.workgroup_type).data
        data["social_links"] = bpms_serializers.SocialURLsSerializer(instance.social_links, many=True).data
        if instance.program:
            data["program"] = bpms_serializers.ProgramBaseSerializer(instance.program).data
        if instance.counterparty:
            data["counterparty"] = bpms_serializers.CounterpartyModelBaseSerializer(instance.counterparty).data
        if instance.costing_object:
            data["costing_object"] = bpms_serializers.CostingObjectBaseSerializer(instance.costing_object).data
        data['workgroup_logo'] = AvatarSerializer(instance.workgroup_logo).data
        data['organization'] = catalog_serializers.ContractorModelByIdSerializer(instance.organization).data
        data['in_favorites'] = get_in_favorites(instance)
        return data


class WorkgroupGallerySerializer(serializers.ModelSerializer):
    gallery_files = AppFileSerializer(read_only=True, many=True)

    class Meta:
        model = models.WorkgroupModel
        fields = ("gallery_files",)


class WorkgroupAttachmentsSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = models.WorkgroupModel
        fields = ("attachments",)

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)


class WorkgroupMembershipSerializer(serializers.ModelSerializer):
    member = bpms_serializers.AppUserSerializer(read_only=True)
    membership_role = WorkgroupMembershipRoleSerializer(read_only=True)
    membership_request_status = WorkgroupMembershipStatusSerializer(read_only=True)

    class Meta:
        model = models.WorkgroupMembersModel
        fields = [
            "id",
            "member",
            "membership_request_status",
            "membership_role",
            "member_visible",
            "default_visor",
        ]


class WorkgroupMembershipUpdateDefaultVisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupMembersModel
        fields = (
            'id',
            'default_visor',
        )


class WorkgroupNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupModel
        fields = ["id", "name", "author", "date_start_plan", "dead_line", "finished_date", 'is_helpdesk', ]


class WorkgroupNameLogoSerializer(serializers.ModelSerializer):
    workgroup_logo = AvatarSerializer()
    # author = bpms_serializers.CachedAppUserSerializer(read_only=True, source='author_id')

    class Meta:
        model = models.WorkgroupModel
        fields = (
            'id',
            'name',
            # 'author',
            'is_project',
            'workgroup_logo',
            "date_start_plan",
            "dead_line",
            "finished_date",
            'is_helpdesk',
        )


class WorkgroupMembersSerializer(serializers.ModelSerializer):
    member = bpms_serializers.AppUserSerializer(read_only=True)
    membership_role = WorkgroupMembershipRoleSerializer(read_only=True)
    work_group = WorkgroupNameSerializer(read_only=True)

    class Meta:
        model = models.WorkgroupMembersModel
        fields = [
            "id",
            "member",
            "work_group",
            "membership_role",
        ]


# class WorkgroupSearchSerializer(HaystackSerializer):
#     class Meta:
#         index_classes = [search_indexes.WorkgroupIndex]
#         fields = (
#             'content'
#         )

#     def to_representation(self, instance):
#         data = WorkgroupDetailSerializer(instance.object).data
#         return data


class WorkgroupSearchSerializer(serializers.ModelSerializer):
    workgroup_logo = AvatarSerializer()

    class Meta:
        model = models.WorkgroupModel
        fields = (
            'id',
            'name',
            'workgroup_logo',
        )

class ProjectTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectTemplateModel
        fields = (
            'id',
            'name',
            'organization',
            'is_public',
            'is_draft',
        )

class ProjectTemplateDetailSerializer(serializers.ModelSerializer):
    author = CachedAppUserSerializer(source='author_id')

    class Meta:
        model = models.ProjectTemplateModel
        fields = (
            'id',
            'name',
            'organization',
            'is_public',
            'is_draft',
            'author',
        )

class ProjectTemplateListSerializer(serializers.ModelSerializer):
    author = CachedAppUserSerializer(source='author_id')

    class Meta:
        model = models.ProjectTemplateModel
        fields = (
            'id',
            'name',
            'organization',
            'is_public',
            'is_draft',
            'author',
        )

class TaskTemplateCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TaskTemplateModel
        fields = (
            'id',
            'template',
            'parent',
            'name',
            'result',
            'description',
            'duration',
            'task_type',
        )
    def validate(self, validated_data):
        task_type = validated_data.get('task_type')
        duration = validated_data.get('duration')
        if task_type == 'stage' and duration > timedelta(0):
            raise drf_exceptions.ValidationError('Продолжительность этапа вычисляется автоматически из продолжительности подзадач.')
        if task_type == 'milestone' and duration > timedelta(0):
            raise drf_exceptions.ValidationError('Веха - это задача без продолжительности.')
        return validated_data
    
    def validate_parent(self, data):
        if getattr(data, 'level', 0) >= 3:
            raise drf_exceptions.ValidationError('Нельзя создать подзадачу для этой задачи.')
        return data

class TaskTemplateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TaskTemplateModel
        fields = (
            'id',
            'name',
            'result',
            'description',
            'duration',
        )


class TaskTemplateListSerializer(serializers.ModelSerializer):
    """Сериализатор шаблонов задач. Рекурсивно выводит подзадачи, помещая их в поле children."""

    class Meta:
        model = models.TaskTemplateModel
        fields = (
            'id',
            'template',
            'parent',
            'name',
            'result',
            'description',
            'duration',
            'task_type',
            'order',
        )
    def to_representation(self, instance):
        data = super().to_representation(instance=instance)
        # если есть подзадачи, то выводим их во вложенном поле children
        if not instance.is_leaf_node():
            children = instance.get_children().order_by('order')
            data['children'] = TaskTemplateListSerializer(children, many=True).data
        return data


class TaskTemplateDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TaskTemplateModel
        fields = (
            'id',
            'template',
            'parent',
            'name',
            'result',
            'description',
            'duration',
            'task_type',
            'order',
        )


class WorkgroupMemberOrganizationModelCreateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=ContractorModel.objects.filter(is_active=True)
    )
    role = serializers.SlugRelatedField(
        required=True,
        slug_field='code',
        queryset=ContractorRelationTypeModel.objects.filter(is_active=True)
    )
    work_group = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.WorkgroupModel.objects.filter(is_active=True)
    )
    status = serializers.SlugRelatedField(
        required=True,
        slug_field='code',
        queryset=models.WorkgroupMemberOrganizationStatusModel.objects.filter(is_active=True)
    )
    

    class Meta:
        model = models.WorkgroupMemberOrganizationModel
        fields = (
            'organization',
            'role',
            'work_group',
            'status',
        )

    def validate(self, data):
        work_group = data['work_group']
        organization = data['organization']

        if self.Meta.model.objects.filter(
            is_active=True,
            work_group=work_group,
            organization=organization
        ).exists():
            raise serializers.ValidationError(
                f"Организация '{organization}' уже участвует в проекте '{work_group}'"
            )

        if work_group.organization == organization:
            raise serializers.ValidationError(
                f"Организацию '{organization}' нельзя добавить в проект '{work_group}' в качестве участника"
            )

        return data


class WorkgroupMemberOrganizationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkgroupMemberOrganizationStatusModel
        fields = (
            'id',
            'name',
            'color',
            'code',
        )


class MemberOrganizationsSerializer(serializers.ModelSerializer):
    organization = ContractorsToAddSerializer()
    employees = serializers.SerializerMethodField()
    role = ContractorRelationTypeModelListSerializer()
    isEditAvailable = serializers.SerializerMethodField()
    status = WorkgroupMemberOrganizationStatusSerializer()

    class Meta:
        model = models.WorkgroupMemberOrganizationModel
        fields = (
            'id',
            'employees',
            'isEditAvailable',
            'organization',
            'role',
            'status'
        )

    def get_employees(self, instance):
        employees = models.WorkgroupMembersModel.objects.filter(
            is_active=True,
            work_group=instance.work_group,
            member_organization__organization=instance.organization,
            member__contractor_profile__contractor=instance.organization
        )
        return WorkgroupMembershipSerializer(employees, many=True).data

    def get_isEditAvailable(self, instance):
        return instance.get_update_permission(self.context.get('request'))
