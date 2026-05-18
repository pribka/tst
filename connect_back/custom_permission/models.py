from django.db import models
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT

# Create your models here.


class RoleModel(models.Model):
    name = models.CharField(default='',
                            verbose_name='Наименование',
                            max_length=255,
                            blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Роли'
        verbose_name = 'Роль'


class AccessTemplateModel(models.Model):
    CHOICES = (
        ('organization', 'organization'),
        ('author', 'author'),
    )

    name = models.CharField(default='',
                            verbose_name='Наименование',
                            max_length=255,
                            blank=False)
    target_field = models.CharField(default='',
                                    max_length=100,
                                    choices=CHOICES,
                                    verbose_name='Поле отбора', )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Шаблоны ограничения доступа'
        verbose_name = 'Шаблон ограничения доступа'


class RoleAccessModel(models.Model):
    role = models.ForeignKey(RoleModel,
                             related_name='access',
                             on_delete=CUSTOM_CASCADE, verbose_name='Роль')
    ct = models.ForeignKey(ContentType, verbose_name='Таблица',
                           on_delete=CUSTOM_CASCADE)
    # Разновидности прав
    read = models.BooleanField(default=False,
                               verbose_name='Право "Чтение"')
    read_template = models.ManyToManyField(AccessTemplateModel,
                                           related_name='in_read',
                                           blank=True, verbose_name='Шаблон доступа "Чтение"'
                                           )
    view = models.BooleanField(default=False,
                               verbose_name='Право "Просмотр"')
    view_template = models.ManyToManyField(AccessTemplateModel,
                                           related_name='in_view',
                                           blank=True, verbose_name='Шаблон доступа "Просмотр"'
                                           )
    create = models.BooleanField(default=False,
                                 verbose_name='Право "Создание"')
    create_template = models.ManyToManyField(AccessTemplateModel,
                                             related_name='in_create',
                                             blank=True, verbose_name='Шаблон доступа "Создание"'
                                             )
    update = models.BooleanField(default=False,
                                 verbose_name='Право "Обновление"')
    update_template = models.ManyToManyField(AccessTemplateModel,
                                             related_name='in_update',
                                             blank=True,
                                             verbose_name='Шаблон доступа "Обновление"'
                                             )
    delete = models.BooleanField(default=False,
                                 verbose_name='Право "Удаление"')
    delete_template = models.ManyToManyField(AccessTemplateModel,
                                             related_name='in_delete',
                                             blank=True,
                                             verbose_name='Шаблон доступа "Удаление"'
                                             )

    def __str__(self):
        return self.role.name + ' ' + self.ct.name

    class Meta:
        unique_together = ['role', 'ct']
        verbose_name_plural = 'Доступ к объектам'
        verbose_name = 'Доступ к объекту'


class AccessProfileModel(models.Model):
    name = models.CharField(default='', max_length=255, blank=False,
                            verbose_name='Наименование')
    roles = models.ManyToManyField(RoleModel, blank=True,
                                   verbose_name='Роли')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Профили доступа'
        verbose_name = 'Профиль доступа'


class UserAccessProfileModel(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=CUSTOM_CASCADE, related_name='access_profiles',
                                verbose_name='Пользователь')

    access_profile = models.ManyToManyField(AccessProfileModel,
                                            verbose_name='Профили доступа')

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name_plural = 'Права пользователей'
        verbose_name = 'Права пользователя'


class SessionParameterModel(models.Model):
    user = models.OneToOneField(CustomUser,
                                on_delete=CUSTOM_CASCADE,
                                related_name='session_parameters',
                                verbose_name='Пользователь')

    organization = models.ManyToManyField('common.Organization',
                                          verbose_name='Организации',
                                          blank=True)
    author = models.ManyToManyField('users.ProfileModel',
                                    verbose_name='Профили',
                                    blank=True)

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name_plural = 'Параметры сессий'
        verbose_name = 'Параметр сессии'
