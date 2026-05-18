from typing import Any
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_PROTECT
from common import fields as common_fields
from common.models import BaseAbstractCatalog, BaseCatalog, BaseModel


class BudgetFunctionalGroupModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        unique=True,
        null=False,
        max_length=10,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name='Наименование',
        max_length=1023,
        null=False,
        default='',
        blank=True
    )

    class Meta:
        verbose_name = 'Функциональная группа'
        verbose_name_plural = 'Функциональные группы'

    def __str__(self):
        return f'Функциональная группа. Код: {self.code}'


class BudgetFunctionalSubgroupModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        unique=False,
        null=False,
        max_length=10,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name='Наименование',
        max_length=1023,
        null=False,
        default='',
        blank=True
    )
    functional_group = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetFunctionalGroupModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Функциональная группа',
        related_name='functional_subgroups',
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = 'Функциональная подгруппа'
        verbose_name_plural = 'Функциональные подгруппы'
        unique_together = ('code', 'functional_group',)

    def __str__(self):
        return f'Функциональная подгруппа. Код: {self.functional_group.code} {self.code}'


class BudgetProgramAdministratorModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        unique=False,
        null=False,
        max_length=10,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name='Наименование',
        max_length=1023,
        null=False,
        default='',
        blank=True
    )
    functional_subgroup = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetFunctionalSubgroupModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Функциональная подгруппа',
        related_name='budget_program_administrators',
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = 'Администратор бюджетных программ'
        verbose_name_plural = 'Администраторы бюджетных программ'
        unique_together = ('code', 'functional_subgroup',)

    def __str__(self):
        return f'{self.functional_subgroup.functional_group.code} {self.functional_subgroup.code} {self.code} {self.name}'

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        qs = cls.get_select_queryset(request)
        if text:
            qs = qs.filter(name__icontains=text)
        return qs

    @property
    def f_group(self):
        return self.functional_subgroup.functional_group


class BudgetProgramModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        unique=False,
        null=False,
        max_length=10,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name='Наименование',
        max_length=1023,
        null=False,
        default='',
        blank=True
    )
    budget_program_administrator = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramAdministratorModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Администратор бюджетных программ',
        related_name='programs',
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = 'Программа'
        verbose_name_plural = 'Программы'
        unique_together = ('code', 'budget_program_administrator',)

    def __str__(self):
        return f'Программа. Код: {self.budget_program_administrator.functional_subgroup.functional_group.code} {self.budget_program_administrator.functional_subgroup.code} {self.budget_program_administrator.code} {self.code}'


class BudgetSubprogramModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        unique=False,
        null=False,
        max_length=10,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name='Наименование',
        max_length=1023,
        null=False,
        default='',
        blank=True
    )
    program = common_fields.CustomForeignKey(
        to='accounting_catalogs.BudgetProgramModel',
        on_delete=CUSTOM_CASCADE,
        verbose_name='Программа',
        related_name='subprograms',
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = 'Подпрограмма'
        verbose_name_plural = 'Подпрограммы'
        unique_together = ('code', 'program',)

    def __str__(self):
        return f'Подпрограмма. Код: {self.program.budget_program_administrator.functional_subgroup.functional_group.code} {self.program.budget_program_administrator.functional_subgroup.code} {self.program.budget_program_administrator.code} {self.program.code} {self.code}'


class KATOCodesModel(BaseModel):
    code = common_fields.CustomCharField(
        verbose_name='Код',
        null=False,
        max_length=9,
        blank=True,
        unique=True
    )
    ab = common_fields.CustomCharField(
        verbose_name='ab',
        unique=False,
        default='',
        max_length=9,
        blank=True
    )
    cd = common_fields.CustomCharField(
        verbose_name='cd',
        unique=False,
        default='',
        max_length=9,
        blank=True
    )
    ef = common_fields.CustomCharField(
        verbose_name='ef',
        unique=False,
        default='',
        max_length=9,
        blank=True
    )
    hij = common_fields.CustomCharField(
        verbose_name='hij',
        unique=False,
        default='',
        max_length=9,
        blank=True
    )
    k = common_fields.CustomCharField(
        verbose_name='k',
        unique=False,
        default='',
        max_length=9,
        blank=True
    )
    name = common_fields.CustomCharField(
        verbose_name=_('Название'),
        unique=False,
        default='',
        max_length=127,
        blank=True
    )
    nn = common_fields.CustomCharField(
        verbose_name='nn',
        unique=False,
        default='',
        max_length=9,
        blank=True
    )

    class Meta:
        verbose_name = 'Код КАТО'
        verbose_name_plural = 'Коды КАТО'

    def save(self, *args, **kwargs):
        if self.id:
            cache.delete(f"CachedKATOCodesModelSerializer_{str(self.id)}_ru")
            cache.delete(f"CachedKATOCodesModelSerializer_{str(self.id)}_kk")
        return super().save(*args, **kwargs)

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('code')

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.get_queryset(request).filter(
            models.Q(name__icontains=text) |
            models.Q(code__icontains=text),
            is_active=True,
        ).distinct()

    @property
    def level(self) -> str:
        if self.cd == '00':
            return 'region'
        elif self.ef == '00':
            return 'district'
        elif self.hij == '000':
            return 'akimat'
        elif self.hij.endswith('00'):
            return 'settlement'
        else:
            return 'village'

    @property
    def full_name(self) -> str:
        level = self.level
        location_full_name = f'{self.name}'
        if level == 'region':
            pass
        elif level == 'district':
            region = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    code__endswith='0000000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            if region:
                location_full_name = f'{region.name}, {self.name}'
        elif level == 'akimat':
            region = None
            district = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    code__endswith='0000000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            try:
                district = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    cd=self.cd,
                    code__endswith='00000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            if region and district:
                location_full_name = f'{region.name}, {district.name}, {self.name}'
        elif level == 'settlement':
            region = None
            district = None
            akimat = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    code__endswith='0000000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            try:
                district = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    cd=self.cd,
                    code__endswith='00000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            try:
                akimat = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    cd=self.cd,
                    ef=self.ef,
                    code__endswith='000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            if region and district and akimat:
                location_full_name = f'{region.name}, {district.name}, {akimat.name}, {self.name}'
        elif level == 'village':
            region = None
            district = None
            akimat = None
            settlement = None
            try:
                region = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    code__endswith='0000000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            try:
                district = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    cd=self.cd,
                    code__endswith='00000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            try:
                akimat = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    cd=self.cd,
                    ef=self.ef,
                    code__endswith='000'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            try:
                settlement = KATOCodesModel.objects.get(
                    is_active=True,
                    ab=self.ab,
                    cd=self.cd,
                    ef=self.ef,
                    hij__startswith=self.hij[0],
                    code__endswith='00'
                )
            except KATOCodesModel.DoesNotExist:
                pass
            if region and district and akimat and settlement:
                location_full_name = (
                    f'{region.name}, {district.name}, {akimat.name}, {settlement.name}, {self.name}')

        return location_full_name

    def __str__(self):
        return f'{self.code} - {self.name}'
