from django import forms
from django.contrib import admin

from common.admin import FileBaseModelInline  # noqa: F401

from . import models


class MyModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MyModelForm, self).__init__(*args, **kwargs)
        self.member = kwargs.pop('member', None)
        self.fields['member'].required = True
        self.fields['membership_request_status'].required = True
        self.fields['membership_role'].required = True

    def clean(self):
        status = self.cleaned_data.get('membership_request_status', None)
        role = self.cleaned_data.get('membership_role', None)
        if not status:
            forms.ValidationError('Не указан статус.')
        if not role:
            forms.ValidationError('Не указана роль.')
        # if status != models.WorkgroupMembershipStatus.objects.get(code="APPROVED"):
        #     raise forms.ValidationError('Approved')
        # if role != models.WorkgroupMembershipRole.objects.get(code="FOUNDER"):
        #     raise forms.ValidationError('Founder')
        return super().clean()


class WorkgroupMembersInline(admin.StackedInline):
    model = models.WorkgroupMembersModel
    fk_name = 'work_group'
    form = MyModelForm
    fields = ('is_active', 'member', 'membership_request_status', 'membership_role')
    autocomplete_fields = ('member',)
    extra = 0
    #
    # def get_queryset(self, request):
    #     return models.WorkgroupMembersModel.objects.filter(is_active=True,
    #                                                        membership_role=models.WorkgroupMembershipRole.objects.get(
    #                                                            code="FOUNDER"),
    #                                                        membership_request_status=models.WorkgroupMembershipStatus.
    #                                                        objects.get(code="APPROVED"))


class WorkDirectionInline(admin.TabularInline):
    model = models.WorkgroupWorkDirectionModel
    fields = (
        'work_direction',
    )
    ordering = ('work_direction__name',)
    extra = 0
    autocomplete_fields = ('work_direction',)
    fk_name = 'work_group'


@admin.register(models.WorkgroupModel)
class WorkgroupAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "workgroup_type",
        "public_or_private",
        "created_at",
        "is_finished",
        "organization",
        "external_id",
    ]
    autocomplete_fields = [
        "gallery_files",
        "social_links",
        "workgroup_type",
        "workgroup_logo",
        "organization",
        "counterparty",
        "program",
        "costing_object",
        "location",
        "linked_chat",
        ]
    search_fields = ["name", ]
    ordering = ('-created_at', )
    inlines = (
        #FileBaseModelInline,
        WorkgroupMembersInline,
        WorkDirectionInline,
        )


@admin.register(models.WorkgroupStatus)
class WorkgroupStatusAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name"
    ]


@admin.register(models.WorkgroupTypes)
class WorkgroupTypesAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
    ]
    search_fields = ["name", ]


@admin.register(models.WorkgroupMembersModel)
class WorkgroupMembers(admin.ModelAdmin):
    autocomplete_fields = [
        "member", "work_group",
    ]
    list_display = [
        "get_member_full_name",
        "get_workgroup",
        "membership_role",
        "membership_request_status",
    ]
    search_fields = [
        "member__full_name",
        "work_group__name",
    ]
    list_filter = [
        "work_group__name",
        "membership_role__name",
        "membership_request_status__name",
    ]

    def get_member_full_name(self, obj: models.WorkgroupMembersModel):
        return obj.member.full_name

    def get_workgroup(self, obj: models.WorkgroupMembersModel):
        return obj.work_group.name


@admin.register(models.WorkgroupMembershipRole)
class WorkgroupMembershipRoleAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
    ]


@admin.register(models.WorkgroupMembershipStatus)
class WorkgroupMembershipStatusAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
    ]


@admin.register(models.ProjectTemplateModel)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_public',
    )
    autocomplete_fields = ['organization',]
    search_fields = ['name', 'organization__id',]
    ordering = ('-created_at', )


@admin.register(models.TaskTemplateModel)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'template',
        'name',
        'duration',
        'task_type',
    )
    autocomplete_fields = ['template',]
    search_fields = ['name', 'template__id',]
    ordering = ('-created_at', )


@admin.register(models.WorkgroupMemberOrganizationModel)
class WorkgroupMemberOrganizationModelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'work_group',
        'organization',
        'role'
    )
    autocomplete_fields = (
        'work_group',
        'organization',
        'role'
    )
