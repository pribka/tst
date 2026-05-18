from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_currentuser.middleware import get_current_authenticated_user
from common.models import BaseCatalog, BaseModel, BaseAbstractCatalog, BaseAbstractModel
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT


class WidgetCatalog(BaseCatalog):
    """ ВИДЖЕТЫ"""
    component_name = models.CharField(
        max_length=40,
        blank=True,
        null=True
    )
    icon_name = models.CharField(
        max_length=40,
        blank=True,
        null=True
    )
    column = models.PositiveIntegerField(
        verbose_name="Колонка",
        blank=True,
        null=False,
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(3)
        ],
    )

    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Виджет'
        verbose_name_plural = 'Виджеты'


class UserWidgetModel(BaseModel):
    """ПОЛЬЗОВАТЕЛЬСКИЙ ВИДЖЕТ"""
    user = models.ForeignKey(
        'users.ProfileModel',
        blank=True,
        null=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name="Пользователь"
    )
    widget = models.ForeignKey(
        WidgetCatalog,
        blank=True,
        null=True,
        on_delete=CUSTOM_CASCADE,
        verbose_name="Виджет"
    )
    column = models.PositiveIntegerField(
        verbose_name="Колонка",
        blank=True,
        null=False,
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(3)
        ],
    )
    category = models.CharField(
        verbose_name="Категория",
        max_length=100,
        blank=True,
        null=True,
    )

    def __str__(self):
        return " %s %s %s %s" % (str(self.user), str(self.widget), str(self.column), str(self.sort))

    class Meta:
        unique_together = ['user', 'widget']
        verbose_name = 'Пользовательский виджет'
        verbose_name_plural = 'Пользовательские виджеты'


class WidgetCategoryModel(BaseCatalog, BaseAbstractCatalog):
    pass


class WidgetModel(BaseCatalog, BaseAbstractCatalog):
    category = models.ForeignKey(WidgetCategoryModel, on_delete=CUSTOM_PROTECT, related_name='widgets')
    icon = models.CharField(default='fi-rr-apps-add', max_length=255)
    widget_component = models.CharField(max_length=100)
    setting_component = models.CharField(max_length=100)
    static = models.BooleanField(default=False)
    w = models.IntegerField(default=3)
    h = models.IntegerField(default=3)
    minW = models.IntegerField(default=1)
    minH = models.IntegerField(default=1)
    maxW = models.IntegerField(default=15)
    maxH = models.IntegerField(default=15)
    may_config = models.BooleanField(default=True)
    may_pin = models.BooleanField(default=True)
    may_delete = models.BooleanField(default=True)
    random_html = models.TextField(default='', blank=True)
    is_mobile = models.BooleanField(default=True)
    is_desktop = models.BooleanField(default=True)
    show_in_list = models.BooleanField(default=True, verbose_name='Показывать в списке')
    for_support = models.BooleanField(default=False, verbose_name='Для техподдержки')

    app_section_roles_through = models.ManyToManyField(
        to='contractor_permissions.AppSectionRoleThroughModel',
        through='WidgetAppSectionRoleThrough',
        related_name='widgets',
    )


class WidgetAppSectionRoleThrough(BaseAbstractModel):
    widget = models.ForeignKey(
        to='widgets.WidgetModel',
        on_delete=CUSTOM_CASCADE,
        related_name='widget_app_section_role_through',
    )
    app_section_role = models.ForeignKey(
        to='contractor_permissions.AppSectionRoleThroughModel',
        on_delete=CUSTOM_CASCADE,
        related_name='widget_app_section_role_through',
    )

    class Meta:
        verbose_name = 'Роль раздела виджета'
        verbose_name_plural = 'Роли раздела виджета'
        unique_together = (('widget', 'app_section_role',),)


class DesktopTemplateModel(BaseCatalog, BaseAbstractCatalog):
    draggable = models.BooleanField(default=True)
    resizable = models.BooleanField(default=True)
    margin_x = models.IntegerField(default=10)
    margin_y = models.IntegerField(default=10)
    vertical_compact = models.BooleanField(default=True)
    use_css_transforms = models.BooleanField(default=True)
    default = models.BooleanField(default=False)

    access_groups = models.ManyToManyField(
        'contractor_permissions.AccessGroupModel',
        through='DesktopTemplateAccessGroupThrough',
        through_fields=('desktop_template', 'access_group',)
    )


class DesktopTemplateWidgetOnDesktopModel(BaseCatalog, BaseAbstractCatalog):
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    w = models.IntegerField(default=0)
    h = models.IntegerField(default=0)
    i = models.IntegerField(default=0)
    static = models.BooleanField(default=False)
    widget = models.ForeignKey(WidgetModel, on_delete=CUSTOM_PROTECT)
    desktop = models.ForeignKey(DesktopTemplateModel, on_delete=CUSTOM_CASCADE, related_name='default_widgets')
    mobile_index = models.IntegerField(default=0)
    is_mobile = models.BooleanField(default=False)
    is_desktop = models.BooleanField(default=False)
    random_settings = models.JSONField(null=True, blank=True)


class DesktopTemplateAccessGroupThrough(BaseAbstractModel):
    desktop_template = models.ForeignKey(
        DesktopTemplateModel,
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='desktop_template_access_group_through'
    )
    access_group = models.ForeignKey(
        'contractor_permissions.AccessGroupModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='desktop_template_access_group_through',
    )

    class Meta:
        verbose_name = 'Группа доступа шаблона рабочего стола'
        verbose_name_plural = 'Группы доступа шаблона рабочего стола'
        unique_together = (('desktop_template', 'access_group', ),)


class UserDesktopModel(BaseCatalog, BaseAbstractCatalog):
    desktop_template = models.ForeignKey(DesktopTemplateModel,
                                         null=True,
                                         on_delete=CUSTOM_SET_NULL)
    # profile = models.ForeignKey('users.ProfileModel',
    #                             on_delete=CUSTOM_CASCADE)

    draggable = models.BooleanField(default=True)
    resizable = models.BooleanField(default=True)
    margin_x = models.IntegerField(default=10)
    margin_y = models.IntegerField(default=10)
    vertical_compact = models.BooleanField(default=True)
    use_css_transforms = models.BooleanField(default=True)


class UserWidgetOnDesktopModel(BaseCatalog, BaseAbstractCatalog):
    # profile = models.ForeignKey('users.ProfileModel',
    #                             on_delete=CUSTOM_CASCADE)

    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    w = models.IntegerField(default=3)
    h = models.IntegerField(default=3)
    i = models.IntegerField(default=0)
    static = models.BooleanField(default=False)
    widget = models.ForeignKey(WidgetModel, on_delete=CUSTOM_PROTECT)
    desktop = models.ForeignKey(UserDesktopModel, on_delete=CUSTOM_CASCADE, related_name='widgets')
    random_html = models.TextField(default='', blank=True)
    random_settings = models.JSONField(null=True, blank=True)
    mobile_index = models.IntegerField(default=0)
    is_mobile = models.BooleanField(default=False)
    is_desktop = models.BooleanField(default=False)

    @property
    def page_name(self):
        return str(self.id)
