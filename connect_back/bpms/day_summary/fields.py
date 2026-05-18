from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

from common import fields as common_fields
from common import page_config

from common.catalogs import models as catalog_models
from bpms.workgroups import models as workgroup_models


class DaySummaryProjectFilterField(common_fields.FakeField):
    """Фильтр по проекту: только заметки авторов — участников указанного проекта (WorkgroupModel с is_project=True)."""
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField(filters=[
        {"name": "is_project", "value": True, "type": "defined"}
    ])
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Проект")
    name = "project_filter"
    default = None
    blank = True
    to_fields = ("id",)
    remote_field = "id"
    key = "workgroups.WorkgroupModel"
    model = "workgroups.WorkgroupModel"
    data_path = "/app_info/select_list/?model=workgroups.WorkgroupModel"

    def to_filter(self, queryset, value):
        workgroup_id = value.get("value")
        if not workgroup_id:
            return queryset
        members_subquery = workgroup_models.WorkgroupMembersModel.objects.filter(
            work_group_id=workgroup_id,
            work_group__is_project=True,
            membership_request_status__code="APPROVED",
            is_active=True,
        ).filter(member_id=OuterRef("author_id"))
        return queryset.filter(Exists(members_subquery))

    def to_exclude(self, queryset, value):
        workgroup_id = value.get("value")
        if not workgroup_id:
            return queryset
        members_subquery = workgroup_models.WorkgroupMembersModel.objects.filter(
            work_group_id=workgroup_id,
            work_group__is_project=True,
            membership_request_status__code="APPROVED",
            is_active=True,
        ).filter(member_id=OuterRef("author_id"))
        return queryset.exclude(Exists(members_subquery))


class DaySummaryWorkgroupFilterField(common_fields.FakeField):
    """Фильтр по команде: только заметки авторов — участников указанной рабочей группы."""
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Команда")
    name = "workgroup_filter"
    default = None
    blank = True
    to_fields = ("id",)
    remote_field = "id"
    key = "workgroups.WorkgroupModel"
    model = "workgroups.WorkgroupModel"
    data_path = "/app_info/select_list/?model=workgroups.WorkgroupModel"

    def to_filter(self, queryset, value):
        workgroup_id = value.get("value")
        if not workgroup_id:
            return queryset
        members_subquery = workgroup_models.WorkgroupMembersModel.objects.filter(
            work_group_id=workgroup_id,
            membership_request_status__code="APPROVED",
            is_active=True,
        ).filter(member_id=OuterRef("author_id"))
        return queryset.filter(Exists(members_subquery))

    def to_exclude(self, queryset, value):
        workgroup_id = value.get("value")
        if not workgroup_id:
            return queryset
        members_subquery = workgroup_models.WorkgroupMembersModel.objects.filter(
            work_group_id=workgroup_id,
            membership_request_status__code="APPROVED",
            is_active=True,
        ).filter(member_id=OuterRef("author_id"))
        return queryset.exclude(Exists(members_subquery))


class DaySummaryOrganizationFilterField(common_fields.FakeField):
    """Фильтр по организации: только заметки авторов — участников указанной организации (ContractorProfileModel)."""
    internal_type = "ForeignKey"
    table_info = page_config.ForeignKeyTableColumn()
    field_info = page_config.ForeignKeyFormField()
    filter_info = page_config.ForeignKeyFilterField()
    tp_info = page_config.TPForeignKeyColumn()
    filter_lookup = {"value": "__in"}
    verbose_name = _("Организация")
    name = "organization_filter"
    default = None
    blank = True
    to_fields = ("id",)
    remote_field = "id"
    key = "catalogs.ContractorModel"
    model = "catalogs.ContractorModel"
    data_path = "/app_info/select_list/?model=catalogs.ContractorModel"

    def to_filter(self, queryset, value):
        org_id = value.get("value")
        if org_id is None:
            return queryset
        member_subquery = catalog_models.ContractorProfileModel.objects.filter(
            contractor_id=org_id,
            user_id=OuterRef("author_id"),
            is_active=True,
        )
        return queryset.filter(Exists(member_subquery))

    def to_exclude(self, queryset, value):
        org_id = value.get("value")
        if org_id is None:
            return queryset
        member_subquery = catalog_models.ContractorProfileModel.objects.filter(
            contractor_id=org_id,
            user_id=OuterRef("author_id"),
            is_active=True,
        )
        return queryset.exclude(Exists(member_subquery))
