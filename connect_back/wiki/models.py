from django.db import models
from django.utils.translation import gettext as _

from rest_framework import exceptions as drf_exceptions

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT

# Create your models here.
from common.models import BaseModel, BaseCatalog, BaseAbstractCatalog, BaseAbstractModel
from common import fields as common_fields


class WikiSectionModel(BaseCatalog, BaseAbstractCatalog):
    use_in_wiki = models.BooleanField(default=False)
    random_html = models.TextField(default='', blank=True)
    related_object = models.ForeignKey(
        'common.BaseModel',
        on_delete=models.CASCADE,
        related_name='wiki_sections',
        null=True,
        blank=True,
        verbose_name=_('Связанный объект')
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        related_name='contractor_wiki_sections',
        on_delete=CUSTOM_PROTECT,
        verbose_name=_('Организация'),
    )

    public = common_fields.CustomBooleanField(
        default=True,
        verbose_name=_('Общедоступный')
    )

    def get_detail_permission(self, request) -> bool:
        if self.related_object:
            return self.related_object.original_object.get_detail_permission(request)
        elif self.contractor:
            from contractor_permissions.utils import check_contractor_permission
            user = request.user.profile
            contractor = self.contractor
            try:
                check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
            except drf_exceptions.PermissionDenied:
                my_organizations = user.my_organizations
                if self.public:
                    return contractor.pk in my_organizations
                else:
                    return self.wiki_access.filter(
                        contractor_profile__user=user,
                        contractor_profile__contractor=contractor
                    ).exists()
            else:
                return True
        return request.user.is_authenticated

    def get_update_permission(self, request) -> bool:
        if self.related_object:
            return self.related_object.original_object.get_update_permission(request)
        elif self.contractor:
            from contractor_permissions.utils import check_contractor_permission
            user = request.user.profile
            contractor = self.contractor
            try:
                check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
            except drf_exceptions.PermissionDenied:
                return False
            else:
                return True
        return request.user.is_superuser

    def save(self, *args, **kwargs):
        if self.code == '':
            self.code = self.id
        super().save(*args, **kwargs)


class WikiAccessModel(BaseAbstractModel):
    contractor_profile = common_fields.CustomForeignKey(
        to='catalogs.ContractorProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='wiki_access',
        verbose_name=_('Сотрудник организации'),
    )

    wiki_section = common_fields.CustomForeignKey(
        to='wiki.WikiSectionModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='wiki_access',
        verbose_name=_('Раздел вики')
    )

    class Meta:
        verbose_name = _('Персональный доступ к Вики')
        verbose_name_plural = _('Персональные доступы к Вики')
        unique_together = (('contractor_profile', 'wiki_section',),)


class WikiChapterModel(BaseCatalog, BaseAbstractCatalog):
    related_object = models.ForeignKey(
        'common.BaseModel',
        on_delete=models.CASCADE,
        related_name='wiki_chapters',
        null=True,
        blank=True,
        verbose_name=_('Связанный объект')
    )
    section = models.ManyToManyField(WikiSectionModel,
                                     related_name='chapters',
                                     blank=False)
    use_in_wiki = models.BooleanField(default=False)
    random_html = models.TextField(default='', blank=True)
    show_on_main_page = models.BooleanField(default=True,
                                            verbose_name='Отображать на главной странице Wiki')

    def get_detail_permission(self, request) -> bool:
        for each in self.section.all():
            if each.get_detail_permission(request):
                return True
        return False

    def get_update_permission(self, request) -> bool:
        for each in self.section.all():
            if each.get_update_permission(request):
                return True
        return False

    def save(self, *args, **kwargs):
        if self.code == '':
            self.code = self.id
        super().save(*args, **kwargs)


class WikiPageModel(BaseCatalog, BaseAbstractCatalog):
    related_object = models.ForeignKey(
        'common.BaseModel',
        on_delete=models.CASCADE,
        related_name='wiki_pages',
        null=True,
        blank=True,
        verbose_name=_('Связанный объект')
    )
    chapter = models.ManyToManyField(WikiChapterModel,
                                     related_name='pages',
                                     blank=False)
    use_in_wiki = models.BooleanField(default=False)
    random_html = models.TextField(default='', blank=False)

    def get_detail_permission(self, request) -> bool:
        for each in self.chapter.all():
            if each.get_detail_permission(request):
                return True
        return False

    def get_update_permission(self, request) -> bool:
        for each in self.chapter.all():
            if each.get_update_permission(request):
                return True
        return False

    def save(self, *args, **kwargs):
        if self.code == '':
            self.code = self.id
        super().save(*args, **kwargs)
