from django.db import models
from django.db.models import Q

from bkz3.settings import CUSTOM_PROTECT, CUSTOM_CASCADE

from common import fields as common_fields
from common.models import BaseModel, BaseCatalog, BaseAbstractCatalog


class ContractorDocTypeModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Типы документа'


class ContractorDocTemplateModel(BaseCatalog, BaseAbstractCatalog):
    doc_type = common_fields.CustomForeignKey(
        to='contractor_docs.ContractorDocTypeModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Тип документа',
    )
    description = common_fields.CustomCharField(
        max_length=511,
        null=False,
        blank=True,
        default='',
        verbose_name='Описание'
    )
    content = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Контент',
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorDocTemplateModelSerializer
        return ContractorDocTemplateModelSerializer

    class Meta:
        verbose_name = 'Шаблон документа клиента'
        verbose_name_plural = 'Шаблоны документов клиента'


class ContractorDocDeliveryStatusModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Статус отправки документа'
        verbose_name_plural = 'Статусы отправки документа'

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='',
        verbose_name='Цвет',
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort', 'name', 'created_at',)


class ContractorDocApprovalStatusModel(BaseCatalog, BaseAbstractCatalog):
    class Meta:
        verbose_name = 'Статус подписания документа'
        verbose_name_plural = 'Статусы подписания документа'

    color = common_fields.CustomCharField(
        max_length=31,
        null=False,
        blank=True,
        default='',
        verbose_name='Цвет',
    )

    @classmethod
    def is_enum(cls):
        return True

    @classmethod
    def get_queryset(cls, request=None):
        return cls.objects.filter(is_active=True).order_by('sort', 'name', 'created_at', )


class ContractorDocModel(BaseCatalog, BaseAbstractCatalog):
    doc_file = common_fields.CustomForeignKey(
        to='common.File',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Файл',
        null=True,
        blank=True,
    )
    members = models.ManyToManyField(
        'users.ProfileModel',
        through='contractor_docs.ContractorDocMemberModel',
        verbose_name='Соисполнители',
        through_fields=('contractor_doc', 'user')
    )
    template = common_fields.CustomForeignKey(
        to='contractor_docs.ContractorDocTemplateModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Шаблон',
    )
    contractor = common_fields.CustomForeignKey(
        to='catalogs.ContractorMemberModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Организация',
        related_name='organization_docs'
    )
    customer = common_fields.CustomForeignKey(
        to='catalogs.ContractorMemberModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_PROTECT,
        verbose_name='Клиент',
        related_name='contractor_docs'
    )
    delivery_status = common_fields.CustomForeignKey(
        to='contractor_docs.ContractorDocDeliveryStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='not_delivered',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Статус отправки',
    )
    approval_status = common_fields.CustomForeignKey(
        to='contractor_docs.ContractorDocApprovalStatusModel',
        to_field='code',
        null=False,
        blank=False,
        default='new',
        on_delete=CUSTOM_PROTECT,
        verbose_name='Статус',
    )
    content = models.TextField(
        null=False,
        blank=True,
        default='',
        verbose_name='Контент',
    )
    locked = common_fields.CustomBooleanField(
        default=False,
        verbose_name='Заблокирован'
    )

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import ContractorDocModelCreateSerializer, ContractorDocModelDetailSerializer, \
            ContractorDocModelListSerializer, ContractorDocModelUpdateSerializer, ContractorDocContentSerializer
        if not action:
            return ContractorDocModelListSerializer
        if action == 'list':
            return ContractorDocModelListSerializer
        elif action == 'retrieve':
            return ContractorDocModelDetailSerializer
        elif action in ('update', 'partial_update'):
            return ContractorDocModelUpdateSerializer
        elif action == 'create':
            return ContractorDocModelCreateSerializer
        elif action == 'get_content':
            return ContractorDocContentSerializer
        else:
            return ContractorDocModelListSerializer

    def get_update_permission(self, request) -> bool:
        if self.locked:
            return False
        return request.user.profile == self.author

    def get_detail_permission(self, request=None):
        if not request:
            return False
        user = request.user.profile
        if user == self.author:
            return True
        if user in list(self.members.all()):
            return True
        return False

    @classmethod
    def get_queryset(cls, request=None):
        if not request:
            return cls.objects.none()
        user = request.user.profile
        queryset = cls.objects.filter(Q(author=user) | Q(members=user), is_active=True).distinct()
        return queryset

    @classmethod
    def get_table_columns(cls):
        return 'name', 'template', 'contractor', 'customer', 'delivery_status', 'approval_status',

    class Meta:
        verbose_name = 'Документ клиента'
        verbose_name_plural = 'Документы клиентов'


class ContractorDocMemberModel(BaseModel):
    user = common_fields.CustomForeignKey(
        to='users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Пользователь',
        related_name='contractor_doc_members'
    )
    contractor_doc = common_fields.CustomForeignKey(
        to='contractor_docs.ContractorDocModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        verbose_name='Документ',
        related_name='contractor_doc_members',
    )

    class Meta:
        verbose_name = 'Соисполнитель документа'
        verbose_name_plural = 'Участники события'
        unique_together = (('user', 'contractor_doc',),)

