import uuid

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from mptt.models import MPTTModel, TreeForeignKey

from rest_framework import exceptions as drf_exceptions

from bpms.bpms_common.utils import get_actual_staff_records
from common.models import BaseModel, BaseAbstractCatalog, BaseAbstractModel, Organization, Individual, BaseCatalog
from users.models import CustomUser, ProfileModel
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT
from common import fields as common_fields

class SocialWebType(BaseCatalog):
    class Meta:
        verbose_name = "Тип социальной сети"
        verbose_name_plural = "Типы социальных сетей"


class SocialURLs(BaseModel):
    social_link = models.URLField(
        default="",
        blank=True,
        null=True,
        verbose_name="Ссылка на социальную сеть",
    )
    social_web_type = models.ForeignKey(
        SocialWebType,
        blank=True,
        null=True,
        verbose_name="Тип социальной сети",
        on_delete=CUSTOM_DO_NOTHING
    )

    class Meta:
        verbose_name = "Ссылка на социальную сеть"
        verbose_name_plural = "Ссылки на социальные сети"


class Unit(BaseCatalog):
    """Подразделение"""

    uid = models.CharField(
        max_length=36,
        unique=True,
        verbose_name='UID 1С',
        default=uuid.uuid4

    )

    code = models.CharField(
        max_length=15,
        default='',
        verbose_name='Код'
    )

    unit_organization = models.ForeignKey(
        Organization,
        null=True,
        on_delete=CUSTOM_SET_NULL,
        related_name='units',
        verbose_name='Организация',
    )

    def get_persons(self):
        org_recs = get_actual_staff_records(self.unit_organization, None)
        actual_history = StaffHistory.objects.select_related('person', 'person__profile').filter(pk__in=org_recs,
                                                                                                 unit=self,
                                                                                                 type_record__lte=2).values_list(
            'person__id', flat=True)

        persons = Individual.objects.select_related('profile__avatar').filter(pk__in=actual_history)

        return persons

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'


class NewsCategoryModel(BaseCatalog, BaseAbstractCatalog):

    class Meta:
        verbose_name = 'Категория новости'
        verbose_name_plural = 'Категории новости'
        ordering = ('sort', 'name',)


class NewsModel(BaseModel, MPTTModel):
    category = models.ForeignKey(
        'bpms_common.NewsCategoryModel',
        to_field='code',
        null=False,
        blank=True,
        default='new',
        on_delete=CUSTOM_PROTECT,
    )
    parent = TreeForeignKey('self',
                            on_delete=CUSTOM_PROTECT,
                            null=True,
                            blank=True,
                            related_name='children')
    level = models.IntegerField(default=0)
    lft = models.IntegerField(default=0)
    rght = models.IntegerField(default=0)
    tree_id = models.IntegerField(default=0)
    title = models.CharField(max_length=1000, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Контент")
    author_news = models.ForeignKey(
        ProfileModel,
        on_delete=CUSTOM_PROTECT,
        related_name="news",
        verbose_name="Автор новости",
        blank=True,
        null=True,
    )
    is_important = models.BooleanField(default=False, verbose_name="Важная новость?")
    is_banner = models.BooleanField(default=False, verbose_name="Выводить на баннере")
    addressees = models.ManyToManyField(
        ProfileModel, blank=True, verbose_name="Адресаты"
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
        blank=True,
        null=True,
    )

    organization = models.ManyToManyField(
        'common.Organization', blank=True, verbose_name="Организации"
    )
    unit = models.ManyToManyField(
        Unit, blank=True, verbose_name="Подразделения"
    )
    work_groups = models.ManyToManyField(
        "workgroups.WorkgroupModel", blank=True, verbose_name="Рабочие группы"
    )
    image = models.ForeignKey(
        'common.File',
        on_delete=CUSTOM_SET_NULL,
        blank=True,
        null=True,
        verbose_name="Изображение новости",
        related_name="front_images",
    )
    sprint = models.ForeignKey('tasks.TaskSprintModel',
                               verbose_name='Отчет по спринту (релиз)',
                               null=True,
                               blank=True,
                               on_delete=CUSTOM_PROTECT)
    is_independent = models.BooleanField(default=False,
                                         verbose_name='Независимая?')
    related_object = common_fields.CustomForeignKey(
        'common.BaseModel',
        null=True, blank=True,
        on_delete=CUSTOM_CASCADE,
        related_name='object_news'
    )

    def get_detail_permission(self, request) -> bool:
        from bpms.workgroups.models import WorkgroupMembershipStatus, WorkgroupMembersModel
        if self.is_independent:
            return True
        work_groups = self.work_groups.filter(is_active=True)
        if work_groups.filter(public_or_private=False).exists():
            return True
        work_groups = work_groups.filter(
            workgroupmembersmodel__member=request.user.profile,
        ).values_list('pk', flat=True)

        return WorkgroupMembersModel.objects.filter(
            is_active=True,
            work_group_id__in=work_groups,
            member=request.user.profile,
            membership_request_status=WorkgroupMembershipStatus.objects.get(code="APPROVED")
        ).exists()

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

    def __str__(self):
        return self.title

    def set_is_active(self, value: bool, request):
        user = request.user.profile
        if self.author == user or user.is_support or request.user.is_staff:
            if value is not self.is_active:
                if value is False and self.is_active is True:
                    self.deleted_at = timezone.now()
                elif value is True and self.is_active is False:
                    self.deleted_at = None
                try:
                    self.is_active = value
                except ValidationError:
                    raise drf_exceptions.ValidationError()
            else:
                pass
        else:
            raise drf_exceptions.PermissionDenied()


class Position(BaseModel):
    """Модель данных - Должности"""

    uid = models.CharField(
        max_length=36,
        unique=True,
        verbose_name='UID 1С'
    )

    code = models.CharField(
        max_length=15,
        verbose_name='Код'
    )

    name = models.CharField(
        max_length=150,
        default='',
        verbose_name='Наименование'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'


class StaffHistory(BaseModel):
    """Кадровая история"""

    document = models.CharField(
        max_length=36,
        default='',
        verbose_name='Документ регистратор (uid 1С)',
    )

    person = models.ForeignKey(
        Individual,
        null=True,
        on_delete=CUSTOM_SET_NULL,
        # related_name='persons',
        verbose_name='Физическое лицо',
    )  # Берем

    staff = models.CharField(
        max_length=36,
        default='',
        verbose_name='Сотрудник (uid 1С)',
    )  # Берем

    date_registration = models.DateField(
        verbose_name='Дата регистрации'
    )

    type_record = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Тип перемещения',
        help_text='0 - не заполнено, '
                  '1 - прием на работу, '
                  '2 - кадровое перемещение, '
                  '3 - увольнение',
    )

    rate = models.DecimalField(
        default=0,
        max_digits=4,
        decimal_places=2,
        verbose_name='Количество ставок',
    )

    organization = models.ForeignKey(
        Organization,
        null=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name='Организация',
    )

    unit = models.ForeignKey(
        Unit,
        null=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name='Подразделение',
    )

    staff_position = models.ForeignKey(
        Position,
        null=True,
        on_delete=CUSTOM_SET_NULL,
        verbose_name='Должность',
    )

    type_staff_rate = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Тип ставки',
        help_text='0 - не заполнено, '
                  '1 - основное место, '
                  '2 - внутреннее совместительство, '
                  '3 - внешнее совместительство',
    )

    class Meta:
        verbose_name = 'Кадровая история'
        verbose_name_plural = 'Кадровая история'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete_pattern(r'unit__persons__*')


class ProgramModel(BaseCatalog):
    class Meta:
        verbose_name = 'Программа'
        verbose_name_plural = 'Программы'

    def __str__(self):
        return self.name


class CostingObjectModel(BaseCatalog):
    class Meta:
        verbose_name = 'Объект калькуляции'
        verbose_name_plural = 'Объекты калькуляции'

    def __str__(self):
        return self.name


class CounterpartyModel(BaseCatalog):
    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return self.name


class WorkTimeLineModel(BaseModel):
    class Meta:
        verbose_name = 'Место работы'
        verbose_name_plural = 'Места работы'

    profile = models.ForeignKey('users.ProfileModel',
                                on_delete=CUSTOM_CASCADE,
                                verbose_name='Профиль',
                                related_name='wtl')
    organization = models.ForeignKey('common.Organization',
                                     on_delete=CUSTOM_PROTECT,
                                     verbose_name='Организация',
                                     related_name='wtl')
    positions = models.ForeignKey(Position,
                                  verbose_name='Должность',
                                  null=True,
                                  blank=True,
                                  on_delete=models.CASCADE)
    date_begin = models.DateField(verbose_name='Дата начала')
    date_end = models.DateField(verbose_name='Дата окончание',
                                null=True,
                                blank=True)
    current = models.BooleanField(default=False,
                                  verbose_name='Текущее место работы')
    checked = models.BooleanField(default=False,
                                  verbose_name='Подтверждено')
    fired = models.BooleanField(default=False,
                                verbose_name='Уволен')
