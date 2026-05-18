from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from common import models as common_models
from common import fields as common_fields

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from contractor_permissions.utils import (
    contractors_where_im_director,
    contractors_where_user_has_permission,
)
from users.utils import get_descendants_departments_related_organizations

from . import fields as day_summary_fields


class DaySummaryNoteStatusModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):
    """Справочник статусов заметки за день."""
    color = common_fields.CustomCharField(
        null=False,
        default="default",
        blank=True,
        max_length=20,
        verbose_name=_("Цвет"),
    )

    class Meta:
        verbose_name = _("Статус итога дня")
        verbose_name_plural = _("Статусы итогов дня")


class DaySummaryNoteCategoryModel(common_models.BaseCatalog, common_models.BaseAbstractCatalog):

    icon = common_fields.CustomCharField(
        null=False,
        default='',
        blank=True,
        max_length=50,
        verbose_name=_('Icon')
    )
    hex_color = common_fields.CustomCharField(
        null=False,
        default='#ffffff',
        blank=True,
        max_length=7,
        verbose_name=_('Код цвета'),
        help_text='начинается с #: #ff00ff',
    )

    class Meta:
        verbose_name = _('Категория итога дня')
        verbose_name_plural = _('Категории итогов дня')


class DaySummaryNoteModel(common_models.BaseModel):
    """
    Заметка пользователя за день.
    """
    date = common_fields.CustomDateField(
        verbose_name=_("Дата"),
    )
    content = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Текст заметки"),
    )
    status = common_fields.CustomForeignKey(
        to="day_summary.DaySummaryNoteStatusModel",
        to_field="code",
        null=True,
        blank=True,
        default="draft",
        on_delete=CUSTOM_PROTECT,
        related_name="day_summary_notes",
        verbose_name=_("Статус"),
    )
    category = common_fields.CustomForeignKey(
        to="day_summary.DaySummaryNoteCategoryModel",
        to_field="code",
        null=True,
        blank=True,
        default="note",
        on_delete=CUSTOM_PROTECT,
        related_name="day_summary_notes",
        verbose_name=_("Категория"),
    )
    visors = models.ManyToManyField(
        to='users.ProfileModel',
        through='day_summary.DaySummaryNoteVisorsModel',
        through_fields=('day_summary', 'user'),
        related_name='visor_day_summary',
        verbose_name=_('Наблюдатели'),
    )
    is_ai_summary = models.BooleanField(
        default=False,
        verbose_name=_("Итог сгенерирован ИИ"),
    )

    project_filter = day_summary_fields.DaySummaryProjectFilterField()
    workgroup_filter = day_summary_fields.DaySummaryWorkgroupFilterField()
    organization_filter = day_summary_fields.DaySummaryOrganizationFilterField()

    class Meta:
        verbose_name = _("Итог дня")
        verbose_name_plural = _("Итоги дня")
        ordering = ("-date", "-created_at")


    @classmethod
    def get_table_columns(cls):
        return ['organization_filter', 'project_filter', 'workgroup_filter', 'author',]

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import (
            DaySummaryNoteListSerializer,
            DaySummaryNoteDetailSerializer,
            DaySummaryNoteCreateSerializer,
            DaySummaryNoteUpdateSerializer,
            DaySummaryNoteListPlainSerializer,
        )
        if action == "create":
            return DaySummaryNoteCreateSerializer
        if action == "update" or action == "partial_update":
            return DaySummaryNoteUpdateSerializer
        if action == "retrieve":
            return DaySummaryNoteDetailSerializer
        if action == "list_latest":
            return DaySummaryNoteListPlainSerializer
        return DaySummaryNoteListSerializer

    @classmethod
    def get_queryset(cls, request=None):
        if not request or not request.user.is_authenticated:
            return cls.objects.none()
        profile = request.user.profile
        lookup = (
            Q(author_id=profile.pk)
            | Q(visors=profile)
        )
        allowed_org_ids = cls._user_allowed_org_ids(profile)
        if allowed_org_ids:
            lookup |= Q(
                author__current_contractor_id__in=allowed_org_ids,
                status_id="published",
            )
        return cls.objects.filter(lookup).filter(is_active=True).distinct()

    @staticmethod
    def _user_allowed_org_ids(profile):
        """Организации, по которым пользователь может видеть чужие заметки.
        Директоры — свои организации и потомки; супервайзеры — только организации, где назначены."""
        director_orgs = contractors_where_im_director(profile)
        supervisor_orgs = contractors_where_user_has_permission(
            profile.pk, 'tasks_supervisor', None
        )
        allowed = set()
        if director_orgs:
            allowed |= get_descendants_departments_related_organizations(
                set(director_orgs), include_self=True
            )
        if supervisor_orgs:
            allowed |= set(supervisor_orgs)
        return allowed

    def get_detail_permission(self, request) -> bool:
        profile = request.user.profile
        if self.author_id == profile.pk:
            return True
        if self.status_id != "published":
            return False
        author_org_id = self.author.current_contractor_id if self.author else None
        if author_org_id is None:
            return False
        return author_org_id in self._user_allowed_org_ids(request.user.profile)

    def get_update_permission(self, request) -> bool:
        return self.author_id == request.user.profile.pk

    @classmethod
    def search_input(cls):
        return True


class DaySummaryNoteVisorsModel(common_models.BaseAbstractModel):
    day_summary = common_fields.CustomForeignKey(
        to='day_summary.DaySummaryNoteModel',
        null=False,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='day_summary_visors_through',
    )
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=False,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='day_summary_visors_through',
    )

    class Meta:
        verbose_name = _('Наблюдатель итогов дня')
        verbose_name_plural = _('Наблюдатели итогов дня')
        unique_together = (('day_summary', 'user'),)