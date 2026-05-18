import json
import uuid

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.apps import apps

from common.models import BaseCatalog, BaseModel, BaseAbstractCatalog, BaseAbstractModel
from common import fields as common_fields

from bkz3.settings import BACKEND_URL, CUSTOM_CASCADE, CUSTOM_PROTECT


class Object1C(BaseAbstractModel):

    name = models.CharField(
        max_length=255,
        null=True,
        blank=False,
        default='',
        verbose_name='Название'
    )

    name_object_1c = models.CharField(
        max_length=255,
        null=True,
        verbose_name='Имя объекта в 1С',
    )
    model = models.CharField(
        verbose_name='Модель Джанго',
        default='',
        max_length=100,
    )
    is_related = models.BooleanField(
        default=False,
        verbose_name='Это связанная модель',
    )
    model_ct = models.ForeignKey(
        ContentType,
        verbose_name='Модель для загрузки из 1С',
        on_delete=CUSTOM_PROTECT,
        null=True,
        blank=True,
    )
    lookup_field = common_fields.CustomCharField(
        max_length=100,
        default='external_id',
        verbose_name='Поле поиска/обновления',
    )
    organization_field = common_fields.CustomCharField(
        max_length=100,
        default='',
        blank=True,
        verbose_name='Поле организации',
        help_text='Записывается автоматически из токена'
    )
    create_if_missing = common_fields.CustomBooleanField(
        default=True,
        verbose_name='Создавать запись, если не найдена',
    )

    update_if_exist = common_fields.CustomBooleanField(
        default=True,
        verbose_name='Изменять запись, если существует'
    )

    organization = common_fields.CustomForeignKey(
        to='catalogs.ContractorModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Корневая организация',
        related_name='objects_1c'
    )

    class Meta:
        verbose_name = 'Объект интеграции с 1с'
        verbose_name_plural = 'Объекты интеграции с 1с'

    def save(self, *args, **kwargs):
        if self.model:
            try:
                app_label, model_name = self.model.split('.', 1)
                model_cls = apps.get_model(app_label, model_name)
            except (LookupError, ValueError) as exc:
                raise ValidationError({'model': f'Не удалось найти модель "{self.model}".'}) from exc
            self.model_ct = ContentType.objects.get_for_model(model_cls)
        elif self.model_ct_id:
            model_cls = self.model_ct.model_class()
            if model_cls is not None:
                self.model = f'{model_cls._meta.app_label}.{model_cls.__name__}'

        super().save(*args, **kwargs)


class Object1CField(BaseAbstractModel):
    name = models.CharField(
        max_length=255,
        null=True,
        blank=False,
        default='',
        verbose_name='Название'
    )
    object_1c = models.ForeignKey(
        'integration_1c.Object1C',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Объект интеграции',
        related_name='fields',
    )
    field_1c = models.CharField(
        verbose_name='Поле 1С',
        default='',
        max_length=100,
    )
    field_django = models.CharField(
        verbose_name='Поле Django',
        default='',
        max_length=100,
    )
    field_search = models.CharField(
        max_length=100,
        null=False,
        default='',
        blank=True,
        verbose_name='Поле поиска',
        help_text='Для внешрих ключей',
    )
    main_field = models.BooleanField(
        default=False,
        verbose_name='Ведущее поле',
    )
    is_binary_data = models.BooleanField(
        default=False,
        verbose_name='Двоичные данные',
    )

    class Meta:
        verbose_name = 'Поле'
        verbose_name_plural = 'Поля'
        unique_together = (('object_1c', 'field_1c',),)

    def __str__(self):
        return f'{self.field_1c} -> {self.field_django}'


class WriteLog(BaseAbstractModel):
    source = models.ForeignKey(
        'catalogs.Contractor1CAccessTokenModel',
        null=True,
        blank=True,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Источник',
        related_name='write_logs',
    )
    action = models.CharField(
        max_length=31,
        null=False,
        default='write',
        blank=False,
        verbose_name='Запрос',
        choices=(
            ('write', 'Запись',),
            ('set_is_active', 'Пометка на удаление'),
        )
    )
    payload = models.JSONField(
        null=False,
        blank=True,
        default=dict,
        verbose_name='Пэйлоад',
    )
    ret = models.JSONField(
        null=False,
        blank=True,
        default=dict,
        verbose_name='Ответ'
    )

    class Meta:
        verbose_name = 'Лог записи из 1С'
        verbose_name_plural = 'Логи записи из 1С'
        ordering = ('-created_at',)


class Mapping1C(BaseAbstractModel):
    name_object_1c = models.CharField(
        max_length=255,
        verbose_name='Имя объекта в 1С',
    )
    model = models.CharField(
        verbose_name='Модель Джанго',
        max_length=255,
    )

    class Meta:
        verbose_name = 'Связь модели с 1С'
        verbose_name_plural = 'Связи моделей с 1С'

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        # Убедись, что поле is_active действительно есть
        if self.is_active:
            exists = Mapping1C.objects.filter(
                model=self.model,
                name_object_1c=self.name_object_1c,
                is_active=True
            ).exclude(pk=self.pk).exists()
            if exists:
                raise ValidationError(
                    f'Связь модели "{self.model}" и объекта 1С "{self.name_object_1c}" уже существует среди активных записей.'
                )
        super().save(*args, **kwargs)


class ModelToIntegrationModel(BaseCatalog):
    """Список моделей для обмена данными"""
    model_ct = models.ForeignKey(ContentType,
                                 verbose_name='Модель доступная для интеграции',
                                 on_delete=CUSTOM_PROTECT)

    class Meta:
        verbose_name = 'Модель для обмена'
        verbose_name_plural = 'Модели для обмена'


class Profile1CDocumentsModel(BaseCatalog):
    profile = models.ForeignKey('users.ProfileModel',
                                on_delete=CUSTOM_PROTECT,
                                null=True,
                                blank=True,
                                verbose_name='Профиль',
                                related_name='documents_1c')
    code = models.CharField(
        verbose_name='Код для параметра',
        null=False,
        default=uuid.uuid1,
        max_length=100,
        blank=True,    )
    contractor_is_required = common_fields.CustomBooleanField(default=False,
                                                              blank=False,
                                                              verbose_name='Клиент')
    member_is_required = common_fields.CustomBooleanField(default=False,
                                                          blank=False,
                                                          verbose_name='Контрагент')
    contract_is_required = common_fields.CustomBooleanField(default=False,
                                                            blank=False,
                                                            verbose_name='Соглашение')
    start_date_is_required = common_fields.CustomBooleanField(default=False,
                                                              blank=False,
                                                              verbose_name='Дата начала')
    end_date_is_required = common_fields.CustomBooleanField(default=False,
                                                            blank=False,
                                                            verbose_name='Дата окончания')

    class Meta:
        verbose_name = 'Мои документы из 1С'
        verbose_name_plural = 'Мои документы из 1С'
        unique_together = ('code', 'profile')

# from django.contrib.contenttypes.models import ContentType
#
#
# class Profile1CDocumentsParametersModel(BaseModel):
#     owner = models.ForeignKey(Profile1CDocumentsModel, on_delete=CUSTOM_CASCADE, verbose_name='Владелец')
#     name = models.CharField(default='', blank=False, verbose_name='Имя параметра',max_length=255
#                             )
#
#     value_type = models.ForeignKey(ContentType, on_delete=CUSTOM_CASCADE, verbose_name='Тип значения')
#     required = models.BooleanField(default=False, verbose_name='Обязательный')
