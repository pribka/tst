import json
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django_q.tasks import async_task

from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers, status
from rest_framework import exceptions as drf_exceptions


from bpms.bpms_common import serializers as bpms_serializers
from bpms.event_calendar.serializers import EventCalendarModelListSerializer
from common import serializers as common_serializers
from common.current_profile.middleware import get_current_authenticated_profile
from common.utils import get_serialized_attachments, get_logo_url
from common.fields import RoundingDecimalField
from common.catalogs.utils import get_admin_area_for_point

from contractor_permissions.models import AccessGroupModel

from crm.models import ShoppingCartModel, GoodsOrderModel
from integration_1c.utils import (set_random_password_and_send_email,
                                  send_contractor_to_1c)
from users.serializers import AppUserSerializer, AppOrganizationSerializer, AppUserShortSerializer
from users.models import CustomUser, ProfileModel, ProfileTypeModel, C1RoleModel

from . import models, search_indexes
from .models import ContractorDeliveryPointModel, ContractorModel
from .utils import get_price_by_catalog_for_serializer, create_chat, get_nearest_event
from ..utils import get_filter_queryset, order_queryset_from_get_param

from bkz3.settings import DEFAULT_PRICE_CURRENCY, MEDIA_URL, BACKEND_URL, DEFAULT_PRICE_TYPE_CODE

from users.serializers import CachedAppUserSerializer


STATUS_COLOR = {
    'Новый': 'geekblue',
    'Текущий': 'purple',
    'Архивный': 'silver',
    'Создан клиент': 'green',
}


class AppWarehouseSerializer(serializers.ModelSerializer):
    manager = CachedAppUserSerializer(source='manager_id')

    class Meta:
        model = models.WarehouseModel
        fields = (
            'id',
            'name',
            'address',
            'phone',
            'manager',
            'default_warehouse',
            'manager_phone',
        )


class GoodsCategoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsCategoryModel
        fields = (
            'id',
            'name',
        )


class CategoryRootShortSerializer(serializers.ModelSerializer):
    key = serializers.UUIDField(source='id')
    title = serializers.CharField(source='name')
    children = serializers.SerializerMethodField()

    class Meta:
        model = models.GoodsCategoryModel
        fields = (
            'key',
            'title',
            'children'
        )

    def get_children(self, instance):
        accepted_nodes = self.context['accepted_nodes']
        children_list = instance.get_children().filter(id__in=accepted_nodes)
        children = CategoryRootShortSerializer(children_list,
                                               many=True,
                                               context={"accepted_nodes": accepted_nodes}).data
        return children


class GoodsCategoryRootSerializer(serializers.ModelSerializer):
    goods_count = serializers.SerializerMethodField()
    is_endpoint = serializers.SerializerMethodField()
    title = serializers.CharField(source='name')
    key = serializers.UUIDField(source='id')
    children = serializers.SerializerMethodField()

    def get_goods_count(self, instance):
        category_and_child = instance.get_descendants(include_self=True)

        qs = models.GoodsModel.get_queryset(
            price_type_code=DEFAULT_PRICE_TYPE_CODE).filter(
                category__in=category_and_child).only('id')

        filtered_qs = order_queryset_from_get_param(
                    self.context['request'],
                    models.GoodsModel,
                    get_filter_queryset(self.context['request'], models.GoodsModel, qs))

        if 'request' in self.context:
            user_id = self.context['request'].user.id
            # goods_in_search = cache.get(F'last_goods_list_{user_id}')
            goods_in_search = None
            if goods_in_search:
                qs = qs.filter(id__in=goods_in_search)
        return filtered_qs.count()

    def get_children(self, instance):
        accepted_nodes = self.context['accepted_nodes']
        do_not_get_child_list = self.context['do_not_get_child_list']
        if not self.get_goods_count(instance):
            return None
        children_qs = instance.get_children().all()
        if instance in do_not_get_child_list:
            children_qs = children_qs.filter(id__in=accepted_nodes)
        children = GoodsCategoryRootSerializer(children_qs,
                                               context={"accepted_nodes": accepted_nodes,
                                                        "do_not_get_child_list": do_not_get_child_list,
                                                        "request": self.context['request']
                                                        }, many=True).data
        ready_children = list()
        for item in children:
            if item['goods_count'] > 0:
                ready_children.append(item)

        return ready_children

    class Meta:
        model = models.GoodsCategoryModel
        fields = (
            'key',
            'title',
            'goods_count',
            'is_endpoint',
            'children',

        )

    def get_is_endpoint(self, instance):
        return instance.is_leaf_node()


class GoodsCategoryListSerializer(serializers.ModelSerializer):
    goods_count = serializers.SerializerMethodField()
    is_endpoint = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    title = serializers.CharField(source='name')
    key = serializers.UUIDField(source='id')
    top = serializers.SerializerMethodField()

    def get_goods_count(self, instance):
        category_and_child = instance.get_descendants(include_self=True).only('id')

        qs = models.GoodsModel.get_queryset(
            price_type_code=DEFAULT_PRICE_TYPE_CODE).filter(
                category__in=category_and_child).only('id')
        filtered_qs = order_queryset_from_get_param(
                    self.context['request'],
                    models.GoodsModel,
                    get_filter_queryset(self.context['request'], models.GoodsModel, qs))
        if 'request' in self.context:
            user_id = self.context['request'].user.id
            # goods_in_search = cache.get(F'last_goods_list_{user_id}')
            goods_in_search = None
            if goods_in_search:
                qs = qs.filter(id__in=goods_in_search)

        return filtered_qs.count()

    def get_top(self, instance):
        return instance.is_root_node()

    def get_is_endpoint(self, instance):
        return instance.is_leaf_node()

    def get_children(self, instance):
        # children = instance.get_children().filter(goods__isnull=False).distinct()
        children = instance.get_children().distinct()
        serialized_child = GoodsCategoryListSerializer(children, many=True, context=self.context).data
        serialized_child_with_goods = list()
        for item in serialized_child:
            if item['goods_count']:
                serialized_child_with_goods.append(item)
        return serialized_child_with_goods

    class Meta:
        model = models.GoodsCategoryModel
        fields = (
            'key',
            'title',
            'top',
            'goods_count',
            'is_endpoint',
            'children',
        )


class GoodsTypeAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsTypeModel
        fields = (
            'code',
            'name',
            'color',

        )


class MeasureUnitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MeasureUnitModel
        fields = (
            'id',
            'code',
            'name',
            'name_short',
            'name_plural',
        )


class GoodsModelForPrintSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    string_view = serializers.SerializerMethodField()

    class Meta:
        model = models.GoodsModel
        fields = (
            'id',
            'created_at',
            'article_number',
            'code',
            'name',
            'string_view',
            'image',
            'is_active',
            'goods_type',
        )

    def get_image(self, instance):
        images = list(instance.gallery.all())
        if images:
            return images[0].path
        else:
            return ''

    def get_string_view(self, instance):
        return instance.__str__()


class GoodsModelListSerializer(common_serializers.BaseCatalogListSerializer):
    price = serializers.CharField(read_only=True)
    image = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    available_count = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    in_cart = serializers.SerializerMethodField()
    goods_type = GoodsTypeAppSerializer()
    category = GoodsCategoryShortSerializer(many=True)
    price_by_catalog = serializers.SerializerMethodField()
    base_measure_unit = MeasureUnitListSerializer()
    default_price_currency = serializers.CharField(read_only=True, default=DEFAULT_PRICE_CURRENCY)

    class Meta(common_serializers.BaseCatalogListSerializer):
        model = models.GoodsModel
        fields = (
            'id',
            'created_at',
            'name',
            'article_number',
            'code',
            'string_view',
            'is_active',
            'price',
            'image',
            'is_available',
            'available_count',
            'goods_type',
            'currency',
            'in_cart',
            'category',
            'price_by_catalog',
            'base_measure_unit',
            'default_price_currency'
        )

    def get_price_by_catalog(self, instance):
        return get_price_by_catalog_for_serializer(instance)

    def get_image(self, instance):
        images = list(instance.gallery.all())
        if images:
            return images[0].path
        else:
            return ''

    def get_is_available(self, instance) -> bool:
        """Есть в наличии?"""
        return bool(getattr(instance, 'remnant_sum', False))

    def get_available_count(self, instance):
        quantity = getattr(instance, 'remnant_sum', 0)
        if quantity is None:
            quantity = 0
        return quantity

    def get_currency(self, instance) -> dict:
        return {
            'name': getattr(instance, 'currency_name', ''),
            'icon': getattr(instance, 'currency_icon', '')
        }

    def get_in_cart(self, instance) -> int:
        return bool(getattr(instance, 'in_cart', False))


class GoodsModelRetrieveSerializer(serializers.ModelSerializer):
    price = serializers.CharField(read_only=True)
    attachments = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    available_count = serializers.SerializerMethodField()
    goods_type = GoodsTypeAppSerializer()
    currency = serializers.SerializerMethodField()
    in_cart = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    price_by_catalog = serializers.SerializerMethodField()
    base_measure_unit = MeasureUnitListSerializer()

    def get_price_by_catalog(self, instance):
        return get_price_by_catalog_for_serializer(instance)

    def get_category(self, instance):
        category_list = instance.category.all()
        nodes = list()
        for category in category_list:
            parents = category.get_ancestors(ascending=False, include_self=True)
            root = category.get_root()
            serialized_data = CategoryRootShortSerializer(root, context={"accepted_nodes": parents}).data
            nodes.append(serialized_data)
        return nodes

    def get_attachments(self, instance):
        return get_serialized_attachments(instance)

    def get_is_available(self, instance) -> bool:
        return bool(getattr(instance, 'remnant_sum', False))

    def get_available_count(self, instance):
        quantity = getattr(instance, 'remnant_sum', 0)
        if quantity is None:
            quantity = 0
        return quantity

    def get_currency(self, instance) -> dict:
        return {
            'name': getattr(instance, 'currency_name', ''),
            'icon': getattr(instance, 'currency_icon', '')
        }

    def get_in_cart(self, instance):
        return getattr(instance, 'in_cart', )

    class Meta:
        model = models.GoodsModel
        fields = (
            'id',
            'code',
            'goods_type',
            'created_at',
            'category',
            'name',
            'description',
            'article_number',
            'is_active',
            'price',
            'attachments',
            'is_available',
            'available_count',
            'price_by_catalog',
            'currency',
            'in_cart',
            'base_measure_unit',
        )


class GoodsModelCUDSerializer(common_serializers.BaseCatalogCUDSerializer):
    class Meta(common_serializers.BaseCatalogCUDSerializer.Meta):
        model = models.GoodsModel
        fields = (
            'id',
            'name',
            'article_number',
        )

    def to_representation(self, instance):
        return GoodsModelRetrieveSerializer(instance).data


class GoodsModelSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = (search_indexes.GoodsModelIndex,)
        fields = (
            'content'
        )

    def to_representation(self, instance):
        obj = instance.object
        data = obj.get_serializer_class(action='list')(instance=obj, context=self.context).data
        data['type'] = obj.get_label()
        return data


class GoodsAvailabilitySerializer(serializers.ModelSerializer):
    warehouse = AppWarehouseSerializer()
    in_cart = serializers.SerializerMethodField()

    def get_in_cart(self, instance):
        user = get_current_authenticated_profile()
        goods = instance.goods

        return ShoppingCartModel.objects.filter(
            user=user,
            goods=goods,
            warehouse=instance.warehouse,
            cart_type_id='shopping_cart',
        ).exists()

    class Meta:
        model = models.GoodsRemnantModel
        fields = (
            'warehouse',
            'quantity',
            'in_cart',
        )


class ContractorModelByINNSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
        )


class ContractorModelByIdSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
            'logo',
        )

    def get_logo(self, instance):
        if instance.logo:
            return get_logo_url(instance.logo)
        else:
            return ''


class ContractorModelShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор организации.
    Кэшируется в рамках CachedBaseModelSerializer"""
    logo = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'code',
            'email',
            'full_name',
            'logo',
            'name',
            'phone'
        )

    def get_logo(self, instance):
        if instance.logo:
            return get_logo_url(instance.logo)
        else:
            return ''

class AppCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CurrencyModel
        fields = (
            'name',
            'icon',
            'code',
        )


class ContractModelListSerializer(serializers.ModelSerializer):
    currency = AppCurrencySerializer(source='price_type.currency')

    class Meta:
        model = models.ContractModel
        fields = (
            'id',
            'code',
            'name',
            'currency',
        )


class ContractorModelSerializer(serializers.ModelSerializer):
    # price_type = common_serializers.BaseCatalogListSerializer()
    profiles = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'code',
            'name',
            'profiles',
            # 'price_type',
            'is_active',
        )

    def get_profiles(self, instance):
        return ','.join(list(instance.profiles.filter(is_active=True).values_list('user__username', flat=True)))


class ContractorModelDetailSerializer(serializers.ModelSerializer):
    # inn = serializers.SerializerMethodField()
    # registered = serializers.SerializerMethodField(required=False)
    # email = serializers.SerializerMethodField(required=False)
    # first_name = serializers.SerializerMethodField(required=False)
    # last_name = serializers.SerializerMethodField(required=False)
    # contact_person_id = serializers.SerializerMethodField(required=False)
    # full_name = serializers.SerializerMethodField()
    # organization_email = serializers.SerializerMethodField()
    # kpp = serializers.SerializerMethodField()
    # ogrn = serializers.SerializerMethodField()
    # ogrnip = serializers.SerializerMethodField()
    # okpo = serializers.SerializerMethodField()
    # legal_address = serializers.SerializerMethodField()
    # postal_address = serializers.SerializerMethodField()
    # director_position = serializers.SerializerMethodField()
    # director_position_genitive = serializers.SerializerMethodField()
    # director_full_name = serializers.SerializerMethodField()
    # director_full_name_genitive = serializers.SerializerMethodField()
    # bank_name = serializers.SerializerMethodField()
    # bik = serializers.SerializerMethodField()
    # bank_account = serializers.SerializerMethodField()
    # correspondent_account = serializers.SerializerMethodField()
    # delivery_address = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
            'phone',
            'doc_prefix',
            # 'inn',
            # 'registered',
            # 'email',
            # 'first_name',
            # 'organization_email',
            # 'last_name',
            # 'contact_person_id',
            'is_archived',
            # 'full_name',
            # 'kpp',
            # 'ogrn',
            # 'ogrnip',
            # 'okpo',
            # 'legal_address',
            # 'postal_address',
            # 'director_position',
            # 'director_position_genitive',
            # 'director_full_name',
            # 'director_full_name_genitive',
            # 'bank_name',
            # 'bik',
            # 'bank_account',
            # 'correspondent_account',
            # 'delivery_address',

        )

    # def get_full_name(self, instance):
    #     try:
    #         full_name = instance.contractor_members.first().full_name
    #     except AttributeError:
    #         full_name = ''
    #     return full_name

    # def get_organization_email(self, instance):
    #     try:
    #         organization_email = instance.contractor_members.first().email
    #     except AttributeError:
    #         organization_email = ''
    #     return organization_email

    # def get_kpp(self, instance):
    #     try:
    #         kpp = instance.contractor_members.first().kpp
    #     except AttributeError:
    #         kpp = ''
    #     return kpp

    # def get_ogrn(self, instance):
    #     try:
    #         ogrn = instance.contractor_members.first().ogrn
    #     except AttributeError:
    #         ogrn = ''
    #     return ogrn

    # def get_ogrnip(self, instance):
    #     try:
    #         ogrnip = instance.contractor_members.first().ogrnip
    #     except AttributeError:
    #         ogrnip = ''
    #     return ogrnip

    # def get_okpo(self, instance):
    #     try:
    #         okpo = instance.contractor_members.first().okpo
    #     except AttributeError:
    #         okpo = ''
    #     return okpo

    # def get_legal_address(self, instance):
    #     try:
    #         legal_address = instance.contractor_members.first().legal_address
    #     except AttributeError:
    #         legal_address = ''
    #     return legal_address

    # def get_postal_address(self, instance):
    #     try:
    #         postal_address = instance.contractor_members.first().postal_address
    #     except AttributeError:
    #         postal_address = ''
    #     return postal_address

    # def get_director_position(self, instance):
    #     try:
    #         director_position = instance.contractor_members.first().director_position
    #     except AttributeError:
    #         director_position = ''
    #     return director_position

    # def get_director_position_genitive(self, instance):
    #     try:
    #         director_position_genitive = instance.contractor_members.first().director_position_genitive
    #     except AttributeError:
    #         director_position_genitive = ''
    #     return director_position_genitive

    # def get_director_full_name(self, instance):
    #     try:
    #         director_full_name = instance.contractor_members.first().director_full_name
    #     except AttributeError:
    #         director_full_name = ''
    #     return director_full_name

    # def get_director_full_name_genitive(self, instance):
    #     try:
    #         director_full_name_genitive = instance.contractor_members.first().director_full_name_genitive
    #     except AttributeError:
    #         director_full_name_genitive = ''
    #     return director_full_name_genitive

    # def get_inn(self, instance):
    #     try:
    #         inn = instance.contractor_members.first().inn
    #     except AttributeError:
    #         inn = ''
    #     return inn

    # def get_registered(self, instance):
    #     obj = instance.contractor_profile.filter(
    #         is_active=True,
    #         contractor=instance,
    #         director=True).first()
    #     try:
    #         return obj.user is not None
    #     except:
    #         return False

    # def get_email(self, instance):
    #     obj = instance.contractor_profile.filter(
    #         is_active=True,
    #         contractor=instance,
    #         director=True).first()
    #     try:
    #         email = obj.user.user.email
    #     except AttributeError:
    #         email = ''
    #     return email

    # def get_first_name(self, instance):
    #     obj = instance.contractor_profile.filter(
    #         is_active=True,
    #         contractor=instance,
    #         director=True).first()
    #     try:
    #         first_name = obj.user.user.first_name
    #     except AttributeError:
    #         first_name = ''
    #     return first_name

    # def get_bank_name(self, instance):
    #     contractor_member = instance.contractor_members.filter(
    #         is_active=True
    #     ).first()
    #     if contractor_member:
    #         bank_requisites = contractor_member.bank_requisites
    #     try:
    #         bank_name = obj.bank_name
    #     except AttributeError:
    #         bank_name = ''
    #     return bank_name
    #
    # def get_bik(self, instance):
    #     contractor_members = instance.contractor_members.filter(
    #         is_active=True
    #     ).first()
    #     obj = contractor_members.requisites.order_by(
    #             '-created_at'
    #         ).first()
    #     try:
    #         bik = obj.bik
    #     except AttributeError:
    #         bik = ''
    #     return bik
    #
    # def get_bank_account(self, instance):
    #     contractor_members = instance.contractor_members.filter(
    #         is_active=True
    #     ).first()
    #     obj = contractor_members.requisites.order_by(
    #             '-created_at'
    #         ).first()
    #     try:
    #         bank_account = obj.bank_account
    #     except AttributeError:
    #         bank_account = ''
    #     return bank_account
    #
    # def get_correspondent_account(self, instance):
    #     contractor_members = instance.contractor_members.filter(
    #         is_active=True
    #     ).first()
    #
    #     obj = contractor_members.requisites.order_by(
    #             '-created_at'
    #         ).first()
    #     try:
    #         correspondent_account = obj.correspondent_account
    #     except AttributeError:
    #         correspondent_account = ''
    #     return correspondent_account

    # def get_last_name(self, instance):
    #     obj = instance.contractor_profile.filter(
    #         is_active=True,
    #         contractor=instance,
    #         director=True).first()
    #     try:
    #         last_name = obj.user.user.last_name
    #     except AttributeError:
    #         last_name = ''
    #     return last_name

    # def get_contact_person_id(self, instance):
    #     obj = instance.contractor_profile.filter(
    #         is_active=True,
    #         contractor=instance,
    #         director=True).first()
    #     try:
    #         contact_person_id = str(obj.user.id)
    #     except AttributeError:
    #         contact_person_id = ''
    #     return contact_person_id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        contractor_member = instance.contractor_members.filter(
            is_active=True
        ).order_by('created_at').first()
        contractor_parent = instance.contractor_parent
        if contractor_parent:
            data['contractor_parent'] = ContractorModelByIdSerializer(contractor_parent).data
        else:
            data['contractor_parent'] = None
        if contractor_member:
            data['full_name'] = contractor_member.full_name
            data['organization_email'] = contractor_member.email
            data['kpp'] = contractor_member.kpp
            data['ogrn'] = contractor_member.ogrn
            data['ogrnip'] = contractor_member.ogrnip
            data['okpo'] = contractor_member.okpo
            data['legal_address'] = contractor_member.legal_address
            data['postal_address'] = contractor_member.postal_address
            data['director_position'] = contractor_member.director_position
            data['director_position_genitive'] = contractor_member.director_position_genitive
            data['director_full_name'] = contractor_member.director_full_name
            data['director_full_name_genitive'] = contractor_member.director_full_name_genitive
            data['inn'] = contractor_member.inn
            director = instance.contractor_profile.filter(is_active=True, contractor=instance, director=True).first()
            if director:
                director_user = director.user
                if director_user:
                    data['registered'] = director_user is not None
                    try:
                        data['email'] = director_user.user.email
                    except AttributeError:
                        data['email'] = ''
                    data['first_name'] = director_user.user.first_name
                    data['last_name'] = director_user.user.last_name
                    data['contact_person_id'] = str(director_user.pk)
                else:
                    data['registered'] = False
            else:
                data['registered'] = False
            bank_requisites = contractor_member.bank_requisites
            if bank_requisites:
                data['bank_name'] = bank_requisites.bank_name
                data['bik'] = bank_requisites.bik
                data['bank_account'] = bank_requisites.bank_account
                data['correspondent_account'] = bank_requisites.correspondent_account
            else:
                data['bank_name'] = ''
                data['bik'] = ''
                data['bank_account'] = ''
                data['correspondent_account'] = ''
        return data

    # def get_delivery_address(self, instance):
    #     try:
    #         delivery_address = instance.delivery_points.first().name
    #     except AttributeError:
    #         delivery_address = ''
    #     return delivery_address


class ContractorModelCreateSerializer(serializers.ModelSerializer):
    inn = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    registered = serializers.BooleanField(
        required=False,
        allow_null=False,
        default=False,
    )
    email = serializers.EmailField(
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    first_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    last_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    is_archived = serializers.BooleanField(
        required=False,
        allow_null=False,
        default=False,
    )
    is_create_chat = serializers.BooleanField(
        required=False,
        allow_null=False,
        default=False,
    )
    source_lead = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None
    )
    full_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    kpp = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrn = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrnip = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    okpo = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    legal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    postal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    organization_email = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bik = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    correspondent_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    # delivery_address = serializers.CharField(
    #     max_length=255,
    #     required=False,
    #     allow_null=False,
    #     allow_blank=True,
    #     default=''
    # )

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
            'phone',
            'inn',
            'doc_prefix',
            'registered',
            'email',
            'last_name',
            'first_name',
            'is_archived',
            'is_create_chat',
            'source_lead',
            'full_name',
            'kpp',
            'ogrn',
            'ogrnip',
            'okpo',
            'legal_address',
            'postal_address',
            'director_position',
            'director_position_genitive',
            'director_full_name',
            'director_full_name_genitive',
            'organization_email',
            'bank_name',
            'bik',
            'bank_account',
            'correspondent_account'
            # 'delivery_address',
        )

    def validate_inn(self, inn):
        if models.ContractorMemberModel.objects.filter(
                    is_active=True,
                    inn=inn
                ).exists():
            raise serializers.ValidationError(
                'Клиент с таким ИНН уже есть в базе данных.'
            )
        return inn

    def create(self, validated_data):
        try:
            from bkz3.settings import DELANS_ID
        except ImportError:
            DELANS_ID = None

        inn = validated_data.pop('inn', '')
        email = validated_data.get('email', '')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        registered = validated_data.pop('registered', '')
        is_create_chat = validated_data.pop('is_create_chat', '')
        delivery_address = validated_data.pop('delivery_address', '')
        source_lead = validated_data.pop('source_lead', '')
        phone = validated_data.get('phone', '')
        full_name = validated_data.pop('full_name', '')
        kpp = validated_data.pop('kpp', '')
        ogrn = validated_data.pop('ogrn', '')
        ogrnip = validated_data.pop('ogrnip', '')
        okpo = validated_data.pop('okpo', '')
        legal_address = validated_data.pop('legal_address', '')
        postal_address = validated_data.pop('postal_address', '')
        director_position = validated_data.pop('director_position', '')
        director_position_genitive = validated_data.pop('director_position_genitive', '')
        director_full_name = validated_data.pop('director_full_name', '')
        director_full_name_genitive = validated_data.pop('director_full_name_genitive', '')
        organization_email = validated_data.pop('organization_email', '')
        bank_name = validated_data.pop('bank_name', '')
        bank_account = validated_data.pop('bank_account', '')
        correspondent_account = validated_data.pop('correspondent_account', '')
        bik = validated_data.pop('bik', '')

        with transaction.atomic():
            instance = super().create(validated_data)
            # delivery_point = models.DeliveryPointModel.objects.create(name=delivery_address)
            # instance.contractordeliverypointmodel_set.create(contractor=instance, delivery_point=delivery_point)
            user = get_current_authenticated_profile()
            contractor_member = models.ContractorMemberModel.objects.create(
                name=instance.name,
                email=organization_email,
                inn=inn,
                contractor=instance,
                full_name=full_name,
                kpp=kpp,
                ogrn=ogrn,
                ogrnip=ogrnip,
                okpo=okpo,
                legal_address=legal_address,
                postal_address=postal_address,
                director_position=director_position,
                director_position_genitive=director_position_genitive,
                director_full_name=director_full_name,
                director_full_name_genitive=director_full_name_genitive
            )
            bank_requisites = models.BankRequisitesModel.objects.create(
                contractor_member=contractor_member,
                bank_name=bank_name,
                bank_account=bank_account,
                correspondent_account=correspondent_account,
                bik=bik,
                is_default=True
            )
            contract = models.ContractModel.objects.create(name=f"Типовое соглашение {instance.name}")
            instance.contracts.create(contractor=instance, contract=contract)
            if source_lead:
                lead = models.PotentialContractorModel.objects.get(
                    is_active=True,
                    id=source_lead
                )
                lead.contractor = instance
                lead.save(update_fields=('contractor',))
            if DELANS_ID is not None:
                delans = models.ContractorModel.objects.filter(
                    is_active=True,
                    id=DELANS_ID
                ).first()
                relation_type = models.ContractorRelationTypeModel.objects.filter(
                    is_active=True,
                    code='vendor'
                ).first()
                if delans and relation_type:
                    models.ContractorRelationModel.objects.create(
                        contractor_parent=delans,
                        contractor=instance,
                        relation_type=relation_type
                    )
            if registered:
                try:
                    # Создаем аккаунт контактного лица
                    contractor_profile_user = CustomUser.objects.create(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name
                    )
                    contractor_profile_user_profile = ProfileModel.objects.get(user=contractor_profile_user)
                    instance.contractor_profile.create(contractor=instance, user=contractor_profile_user_profile, director=True)
                    instance.contact_person = contractor_profile_user_profile
                    contractor_profile_user_profile.phone = phone
                    contractor_profile_user_profile.save()
                    # Присваиваем профилю контактного лица роли 1С со статусом "автоматически присваиваемая"
                    contractor_profile_c1_roles = C1RoleModel.objects.filter(is_active=True, is_auto_role=True)
                    contractor_profile_user_profile.c1_roles.add(*contractor_profile_c1_roles)
                    instance.save()
                except Exception as e:
                    raise serializers.ValidationError(e)
                if is_create_chat:
                    create_chat(
                        chat_author=user,
                        member=contractor_profile_user_profile,
                        is_public=False
                    )
                transaction.on_commit(lambda: async_task(set_random_password_and_send_email, contractor_profile_user))
            transaction.on_commit(
                lambda: async_task(
                    send_contractor_to_1c,
                    ContractorModelDetailSerializer(instance).data
                )
            )

        return instance

    def to_representation(self, instance):
        return ContractorModelDetailSerializer(instance).data



class ContractorModelUpdateSerializer(serializers.ModelSerializer):
    inn = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default=''
    )
    last_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    first_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    email = serializers.EmailField(
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    registered = serializers.BooleanField(
        required=False,
        allow_null=False,
        default=False,
    )
    is_archived = serializers.BooleanField(
        required=False,
        allow_null=False,
        default=False,
    )
    full_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    kpp = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrn = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    ogrnip = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    okpo = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    legal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    postal_address = serializers.CharField(
        max_length=1023,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_position_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    director_full_name_genitive = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    organization_email = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bik = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    bank_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    correspondent_account = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=False,
        allow_blank=True,
        default='',
    )
    # delivery_address = serializers.CharField(
    #     max_length=255,
    #     required=False,
    #     allow_null=False,
    #     allow_blank=True,
    #     default=''
    # )

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
            'phone',
            'inn',
            'doc_prefix',
            'registered',
            'email',
            'last_name',
            'first_name',
            'is_archived',
            'full_name',
            'kpp',
            'ogrn',
            'ogrnip',
            'okpo',
            'legal_address',
            'postal_address',
            'director_position',
            'director_position_genitive',
            'director_full_name',
            'director_full_name_genitive',
            'organization_email',
            'bank_name',
            'bik',
            'bank_account',
            'correspondent_account',
            # 'delivery_address'
        )

    def update(self, instance, validated_data):
        inn = validated_data.pop('inn', '')
        # delivery_address = validated_data.pop('delivery_address', '')
        email = validated_data.get('email', '')
        phone = validated_data.get('phone', '')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        registered = validated_data.pop('registered', '')
        delivery_address = validated_data.pop('delivery_address', '')
        full_name = validated_data.pop('full_name', '')
        kpp = validated_data.pop('kpp', '')
        ogrn = validated_data.pop('ogrn', '')
        ogrnip = validated_data.pop('ogrnip', '')
        okpo = validated_data.pop('okpo', '')
        legal_address = validated_data.pop('legal_address', '')
        postal_address = validated_data.pop('postal_address', '')
        director_position = validated_data.pop('director_position', '')
        director_position_genitive = validated_data.pop('director_position_genitive', '')
        director_full_name = validated_data.pop('director_full_name', '')
        director_full_name_genitive = validated_data.pop('director_full_name_genitive', '')
        organization_email = validated_data.pop('organization_email', '')
        bank_name = validated_data.pop('bank_name', '')
        bank_account = validated_data.pop('bank_account', '')
        correspondent_account = validated_data.pop('correspondent_account', '')
        bik = validated_data.pop('bik', '')

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            contractor_member = instance.contractor_members.first()
            if contractor_member:
                contractor_member.inn = inn
                contractor_member.email = organization_email
                contractor_member.full_name = full_name
                contractor_member.kpp = kpp
                contractor_member.ogrn = ogrn
                contractor_member.ogrnip = ogrnip
                contractor_member.okpo = okpo
                contractor_member.legal_address = legal_address
                contractor_member.postal_address = postal_address
                contractor_member.director_position = director_position
                contractor_member.director_position_genitive = director_position_genitive
                contractor_member.director_full_name = director_full_name
                contractor_member.director_full_name_genitive = director_full_name_genitive
                contractor_member.save(update_fields=('inn', 'email', 'full_name', 'kpp', 'ogrn', 'ogrnip', 'okpo', 'legal_address',
                                                      'postal_address', 'director_position', 'director_position_genitive',
                                                      'director_full_name', 'director_full_name_genitive', ))
                bank_requisites = contractor_member.requisites.first()
                if bank_requisites:
                    bank_requisites.bank_name = bank_name
                    bank_requisites.bank_account = bank_account
                    bank_requisites.correspondent_account = correspondent_account
                    bank_requisites.bik = bik
                    bank_requisites.save(update_fields=('bank_name', 'bank_account', 'correspondent_account', 'bik', ))

            if registered:
                obj = instance.contractor_profile.filter(
                    is_active=True,
                    contractor=instance,
                    director=True).first()
                if obj and obj.user is not None:
                    contractor_profile_user = obj.user.user
                    contractor_profile_user.email = email
                    contractor_profile_user.first_name = first_name
                    contractor_profile_user.last_name = last_name
                    contractor_profile_user.save(update_fields=('email', 'first_name', 'last_name'))
                else:
                    try:
                        # Создаем аккаунт контактного лица
                        contractor_profile_user = CustomUser.objects.create(
                                                    username=email,
                                                    email=email,
                                                    first_name=first_name,
                                                    last_name=last_name)
                        contractor_profile_user_profile = ProfileModel.objects.get(user=contractor_profile_user)
                        instance.contractor_profile.create(contractor=instance, user=contractor_profile_user_profile, director=True)
                        instance.contact_person = contractor_profile_user_profile
                        contractor_profile_user_profile.phone = phone
                        contractor_profile_user_profile.save()
                        # Присваиваем профилю контактного лица роли 1С со статусом "автоматически присваиваемая"
                        contractor_profile_c1_roles = C1RoleModel.objects.filter(is_active=True, is_auto_role=True)
                        contractor_profile_user_profile.c1_roles.add(*contractor_profile_c1_roles)
                        instance.save()
                    except IntegrityError:
                        raise serializers.ValidationError(f'Пользователь с email {email} уже существует')
                    except Exception as e:
                        raise serializers.ValidationError(e)
                    transaction.on_commit(lambda: async_task(set_random_password_and_send_email, contractor_profile_user))
            transaction.on_commit(
                lambda: async_task(
                    send_contractor_to_1c,
                    ContractorModelDetailSerializer(instance).data
                )
            )
            # delivery_point = instance.delivery_points.first()
            # if delivery_point:
            #     delivery_point.name = delivery_address
            #     delivery_point.save(update_fields=('name',))
            # else:
            #     delivery_point = models.DeliveryPointModel.objects.create(name=delivery_address)
            #     instance.contractordeliverypointmodel_set.create(contractor=instance, delivery_point=delivery_point)
        return instance

    def to_representation(self, instance):
        return ContractorModelDetailSerializer(instance).data


class PotentialContractorModelShortSerializer(serializers.ModelSerializer):
    # price_type = common_serializers.BaseCatalogListSerializer()
    # profiles = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    nearest_event = serializers.SerializerMethodField()

    class Meta:
        model = models.PotentialContractorModel
        fields = (
            'id',
            'code',
            'name',
            'company_name',
            'business_region_name',
            'phone',
            'email',
            'is_archived',
            'status',
            'nearest_event',
            # 'profiles',
            # 'price_type',
            # 'is_active',
        )

    def get_nearest_event(self, instance):
        nearest_event = get_nearest_event(instance)
        if nearest_event:
            return EventCalendarModelListSerializer(nearest_event).data
        return None

    def get_status(self, instance):
        try:
            return instance.status
        except AttributeError:
            return "undifined"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        color = STATUS_COLOR.get(data['status'], 'default')
        status = {
            'value': data['status'],
            'color': color
        }
        data['status'] = status
        return data


class PotentialContractorModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PotentialContractorModel
        fields = (
            'name',
            'company_name',
            'business_region_name',
            'phone',
            'email',
            'is_archived',
        )


class PotentialContractorModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PotentialContractorModel
        fields = (
            'id',
            'name',
            'company_name',
            'business_region_name',
            'phone',
            'email',
            'is_archived',
        )


class InterestPotentialContractorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PotentialContractorModel
        fields = (
            'id',
            'name',
            'company_name',
            'business_region_name',
            'phone',
            'email',
        )


class AppDeliveryAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeliveryAddress
        fields = (
            'id',
            'code',
            'address',
        )


class DeliveryAddressModelSerializer(serializers.ModelSerializer):
    contractor = common_serializers.BaseCatalogListSerializer()

    class Meta:
        model = models.DeliveryAddress
        fields = (
            'id',
            'code',
            'is_active',
            'address',
            'contractor',
        )


class RequisitesModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BankRequisitesModel
        fields = (
            'id',
            'contractor_member',
            'bank_name',
            'bank_account',
            'correspondent_account',
            'bik',
            'is_default',
        )

    # def validate(self, data):
    #     correspondent_account = data.get('correspondent_account', None)
    #     bik = data.get('bik', None)
    #     if correspondent_account and bik:
    #         if correspondent_account[-3:] != bik[-3:]:
    #             raise serializers.ValidationError(
    #                 'Последние три цифры номера корреспондентского счета '
    #                 'должны совпадать с последними тремя цифрами БИК.'
    #             )
    #     return data


class GoodsRemnantModelListSerializer(serializers.ModelSerializer):
    goods = common_serializers.BaseCatalogListSerializer()
    warehouse = common_serializers.BaseCatalogListSerializer()

    class Meta:
        model = models.GoodsRemnantModel
        fields = (
            'id',
            'goods',
            'warehouse',
            'quantity',
            'is_active',
            'created_at',
        )


class GoodsPriceModelListSerializer(serializers.ModelSerializer):
    goods = common_serializers.BaseCatalogListSerializer()
    price_type = common_serializers.BaseCatalogListSerializer()

    class Meta:
        model = models.GoodsPriceModel
        fields = (
            'id',
            'goods',
            'price_type',
            'price',
            'is_active',
            'created_at',
        )


class GoodsModelUpdatePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GoodsModel
        fields = (
            'id',
            'price_by_catalog',
        )


class PaymentStageSerializer(serializers.ModelSerializer):
    payment_option = common_serializers.BaseCatalogRetrieveSerializer()

    class Meta:
        model = models.PaymentStageModel
        fields = (
            'id',
            'sort',
            'payment_option',
            'duration',
            'payment_percent',
        )


class ContractPaymentSerializer(serializers.ModelSerializer):
    payment_form = common_serializers.BaseCatalogRetrieveSerializer()
    stages = PaymentStageSerializer(many=True)

    class Meta:
        model = models.TypeOrderPaymentModel
        fields = (
            'id',
            'payment_form',
            'stages',
        )


class DeliveryPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeliveryPointModel
        fields = [
            'id',
            'lat',
            'lon',
            'name',
            'address',
        ]


class DeliveryPurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeliveryPurposeModel
        fields = [
            'id',
            'purpose',
        ]


class ContractorsToAddSerializer(serializers.ModelSerializer):
    director = AppUserShortSerializer()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'director',
            'full_name',
            'name',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        member = instance.contractor_members.filter(
            is_active=True
        ).order_by(
            '-created_at'
        ).first()
        data['inn'] = member.inn if member else ''
        data['legal_address'] = member.legal_address if member else ''
        return data


class ContractorsDetailedListSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для виджета "Клинты" на рабочем столе
    """
    last_order_date = serializers.SerializerMethodField()
    inn = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    orders_in_progress = serializers.SerializerMethodField()
    delivery_address = serializers.SerializerMethodField()
    delivery_point = serializers.SerializerMethodField()
    contact_person = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    nearest_event = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
            'inn',
            'phone',
            'email',
            'delivery_address',
            'delivery_point',
            'last_order_date',
            'total_orders',
            'orders_in_progress',
            'contact_person',
            'is_archived',
            'status',
            'nearest_event',
            'member_inn',
        )

    def get_nearest_event(self, instance):
        nearest_event = get_nearest_event(instance)
        if nearest_event:
            return EventCalendarModelListSerializer(nearest_event).data
        return None

    def get_last_order_date(self, instance):
        try:
            result = instance.last_order_date
        except AttributeError:
            obj = GoodsOrderModel.objects.filter(
                is_active=True,
                contractor=instance
            ).order_by('-created_at').first()
            if obj is not None:
                return obj.created_at.strftime('%d.%m.%Y')
            else:
                return ''
        if result:
            return result.strftime('%d.%m.%Y')
        else:
            return ''

    def get_contact_person(self, instance):
        if instance.contact_person is not None:
            return bpms_serializers.AppUserSerializer(
                instance.contact_person
            ).data
        else:
            return ''

    def get_total_orders(self, instance):
        try:
            return instance.total_orders
        except AttributeError:
            return GoodsOrderModel.objects.filter(
                is_active=True,
                contractor=instance,
                execute_status__code='completed'
            ).count()

    def get_status(self, instance):
        try:
            return instance.status
        except AttributeError:
            return "undifined"

    def get_orders_in_progress(self, instance):
        try:
            return instance.orders_in_progress
        except AttributeError:
            return instance.orders.filter(
                execute_status__code__in=('default', 'processed', 'partially_canceled'),
                is_active=True,
            ).count()

    def get_delivery_address(self, instance):
        try:
            return instance.delivery_address
        except:
            return instance.last_delivery_address

    def get_delivery_point(self, instance):
        return instance.last_delivery_point

    def get_inn(self, instance):
        return instance.inn

    def to_representation(self, instance):
        data = super().to_representation(instance)
        color = STATUS_COLOR.get(data['status'], 'default')
        status = {
            'value': data['status'],
            'color': color
        }
        data['status'] = status
        return data


class DeliveryPointWithContractorsSerializer(serializers.ModelSerializer):
    contractors = ContractorsDetailedListSerializer(many=True)

    class Meta:
        model = models.DeliveryPointModel
        fields = (
            'id',
            'lat',
            'lon',
            'name',
            'address',
            'contractors',
        )


class DeliveryPointWithWarehousesSerializer(serializers.ModelSerializer):
    warehouses = AppWarehouseSerializer(many=True)

    class Meta:
        model = models.DeliveryPointModel
        fields = (
            'id',
            'lat',
            'lon',
            'name',
            'address',
            'warehouses',
        )


class MyDeliveryPointSerializer(serializers.ModelSerializer):
    '''
    Сериалайзер для получения списка объектов модели DeliveryPointModel, компонент "Мои точки доставки"
    '''

    class Meta:
        model = models.DeliveryPointModel
        fields = [
            'id',
            'name',
            'lat',
            'lon',
            'address',
        ]


class MyDeliveryPointSerializerPost(serializers.ModelSerializer):
    '''
    Сериалайзер для создания новых объектов модели DeliveryPointModel, компонент "Мои точки доставки"
    '''
    contractor = serializers.PrimaryKeyRelatedField(
        queryset=ContractorModel.objects.filter(is_active=True))

    class Meta:
        model = models.DeliveryPointModel
        fields = [
            'id',
            'lat',
            'lon',
            'address',
            'name',
            'contractor',
        ]

    def create(self, validated_data):
        contractor = validated_data.pop('contractor')
        with transaction.atomic():
            delivery_point = models.DeliveryPointModel.objects.create(
                **validated_data)
            ContractorDeliveryPointModel.objects.create(
                contractor=contractor,
                delivery_point=delivery_point)
        return delivery_point

    def to_representation(self, instance):
        return MyDeliveryPointSerializer(instance).data

    def validate_contractor(self, contractor):
        current_user = get_current_authenticated_profile()
        if current_user.has_full_access_to_order_editing != True:
            if not contractor.profiles.filter(is_active=True,
                                              pk=current_user.pk).exists():
                raise serializers.ValidationError('Invalid contractor')
        return contractor


class PaymentFormListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PaymentFormModel
        fields = (
            'id',
            'code',
            'name',
            'required', 'is_cash',
        )

class OfferModelSerializer(serializers.ModelSerializer):
    '''
    Сериалайзер для модели OfferModel, компонент "Оферта"
    '''
    class Meta:
        model = models.OfferModel
        fields = [
            'offer_text',
        ]


class UserURLsModelSerializer(serializers.ModelSerializer):
    '''
    Сериалайзер для модели UserURLsModel, компонент "Ссылки"
    '''
    image = serializers.SerializerMethodField()

    def get_image(self, instance):
        return f"{BACKEND_URL}{MEDIA_URL}{instance.favicon}"
    class Meta:
        model = models.UserURLsModel
        fields = [
            'id',
            'name',
            'url',
            'image',
            'method',
            'params'
        ]

class RegisterHelpModelSerializer(serializers.ModelSerializer):
    '''
    Сериалайзер для модели RegisterHelpModel
    '''
    class Meta:
        model = models.RegisterHelpModel
        fields = [
            'help_text',
            'name',
        ]


class ContractorRelationTypeModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContractorRelationTypeModel
        fields = (
            'id',
            'name',
            'name_parent',
            'code',
        )


class ContractorModelWithDirectorSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    director = serializers.SerializerMethodField()
    has_descendants = serializers.SerializerMethodField()

    class Meta:
        model = ContractorModel
        fields = (
            'id',
            'name',
            'logo',
            'director',
            'has_descendants'
        )

    def get_logo(self, instance):
        if instance.logo:
            return get_logo_url(instance.logo)
        else:
            return ''

    def get_director(self, instance):
        try:
            director = instance.contractor_director[0]
        except AttributeError:
            director = instance.contractor_profile.filter(director=True).first()
        except IndexError:
            return None
        if director:
            return AppUserSerializer(director.user).data
        else:
            return None

    def get_has_descendants(self, instance):
        return instance.contractor_relations_parent.filter(is_active=True).exists()


class MyContractorsListSerializer(serializers.ModelSerializer):
    contractor = serializers.SerializerMethodField()
    relation_type = ContractorRelationTypeModelListSerializer()
    is_parent = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorRelationModel
        fields = (
            'id',
            'contractor',
            'relation_type',
            'is_parent',
        )

    def get_is_parent(self, instance):
        if instance.contractor_id == self.context.get('instance_id'):
            return True
        return False

    def get_contractor(self, instance):
        if self.get_is_parent(instance):
            contractor = instance.contractor_parent
        else:
            contractor = instance.contractor
        return ContractorModelShortSerializer(contractor).data


class ContractorRelationModelListSerializer(serializers.ModelSerializer):
    contractor = AppOrganizationSerializer()
    contractor_parent = ContractorModelByIdSerializer()
    relation_type = ContractorRelationTypeModelListSerializer()

    class Meta:
        model = models.ContractorRelationModel
        fields = (
            'id',
            'contractor',
            'contractor_parent',
            'relation_type',
        )


class ContractorProfileNotifySerializer(serializers.ModelSerializer):
    user = AppUserSerializer()
    contractor = ContractorModelByIdSerializer()

    class Meta:
        model = models.ContractorProfileModel
        fields = (
            "id",
            "contractor",
            "user",
            "director",
        )


class ContractorModelListSerializer(serializers.ModelSerializer):
    phone = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorModel
        fields = (
            'id',
            'name',
            'phone',
            'email',
        )

    def get_phone(self, instance):
        if instance.contact_person is not None:
            return instance.contact_person.phone
        else:
            return ''

    def get_email(self, instance):
        if instance.contact_person is not None:
            return instance.contact_person.user.email
        else:
            return ''


class ContractorMemberModelSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorMemberModel
        fields = (
            'id',
            'name',
            'logo',
        )

    def get_logo(self, instance):
        logo = getattr(instance.contractor, 'logo')
        if logo:
            return get_logo_url(logo)
        else:
            return ''


# Отделы

class ContractorDepartmentDetailSerializer(serializers.ModelSerializer):
    director = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    contractor = AppOrganizationSerializer()

    class Meta:
        model = models.ContractorDepartmentModel
        fields = (
            'id',
            'name',
            'name_ru',
            'name_kk',
            'full_name',
            'full_name_ru',
            'full_name_kk',
            'phone',
            'email',
            'director',
            'members_count',
            'contractor',
        )

    def get_director(self, instance):
        director = instance.department_profiles.filter(director=True).first()
        if director:
            return AppUserSerializer(director.contractor_profile.user).data
        else:
            return None

    def get_members_count(self, instance):
        try:
            members_count = instance.annotate_members_count
        except AttributeError:
            members_count = instance.contractor_profiles.all().count()
        return members_count


class ContractorDepartmentListSerializer(serializers.ModelSerializer):
    director = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = models.ContractorDepartmentModel
        fields = (
            'id',
            'name',
            'name_ru',
            'name_kk',
            'full_name',
            'full_name_ru',
            'full_name_kk',
            'phone',
            'email',
            'director',
            'members_count',
        )

    def get_director(self, instance):
        director = instance.department_profiles.filter(director=True).first()
        if director:
            return AppUserSerializer(director.contractor_profile.user).data
        else:
            return None

    def get_members_count(self, instance):
        try:
            members_count = instance.annotate_members_count
        except AttributeError:
            members_count = instance.contractor_profiles.all().count()
        return members_count


class ContractorDepartmentCreateSerializer(serializers.ModelSerializer):
    director = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=ProfileModel.objects.filter(is_active=True, temporary_blocked=False)
    )

    class Meta:
        model = models.ContractorDepartmentModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'full_name_ru',
            'full_name_kk',
            'phone',
            'email',
            'director',
        )

    # def validate_director(self, attr):
    #     director = attr
    #     if director:
    #         contractor = self.context.get('contractor')
    #         if not contractor.profiles.filter(is_active=True, pk=director.pk).exists():
    #             raise drf_exceptions.ValidationError({'message': 'Руководитель не является участником организации.'})
    #     return attr

    def create(self, validated_data):
        director = validated_data.pop('director', None)
        with transaction.atomic():
            contractor = self.context.get('contractor')
            validated_data['contractor'] = self.context.get('contractor')
            instance = super().create(validated_data)
            if director:
                contractor_profile, created = contractor.contractor_profile.get_or_create(user=director)
                instance.department_profiles.create(contractor_profile=contractor_profile, director=True)
        return instance

    def to_representation(self, instance):
        return ContractorDepartmentListSerializer(instance).data


class ContractorDepartmentUpdateSerializer(serializers.ModelSerializer):
    director = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=ProfileModel.objects.filter(is_active=True)
    )
    contractor = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=ContractorModel.objects.filter(is_active=True)
    )

    class Meta:
        model = models.ContractorDepartmentModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'full_name_ru',
            'full_name_kk',
            'phone',
            'email',
            'director',
            'contractor',
        )

    def update(self, instance, validated_data):
        director = validated_data.pop('director', None)
        contractor = validated_data.pop('contractor', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if director:
                instance.department_profiles.filter(director=True).update(director=False)
                contractor_profile, created = instance.contractor.contractor_profile.get_or_create(user=director)
                department_profile, created = instance.department_profiles.get_or_create(
                    contractor_profile=contractor_profile)
                department_profile.director = True
                department_profile.save(update_fields=('director',))
            if contractor:
                instance.contractor = contractor
                department_profiles = instance.department_profiles.filter(is_active=True)
                for each in department_profiles:
                    user = each.contractor_profile.user
                    contractor_profile, created = contractor.contractor_profile.get_or_create(user=user)
                    each.contractor_profile = contractor_profile
                    each.save(update_fields=('contractor_profile',))
        return instance

    def to_representation(self, instance):
        return ContractorDepartmentListSerializer(instance).data


class ContractorDepartmentShortListSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для модели отдела. Когда нужно только название"""

    class Meta:
        model = models.ContractorDepartmentModel
        fields = (
            'id',
            'name',
        )


class ContractorProfileRequestModelNotify(serializers.ModelSerializer):
    user = AppUserSerializer()
    organization = ContractorModelByIdSerializer()

    class Meta:
        model = models.ContractorProfileRequestModel
        fields = (
            'id',
            'user',
            'organization',
        )


class ContractorProfileRequestListSerializer(serializers.ModelSerializer):
    user = AppUserSerializer()
    organization = AppOrganizationSerializer()
    access_groups = common_serializers.BaseCatalogRetrieveSerializer(many=True)

    class Meta:
        model = models.ContractorProfileRequestModel
        fields = (
            'id',
            'user',
            'organization',
            'access_groups',
            'created_at',
            'updated_at',
            'is_approved',
            'is_touched',
        )


class ContractorProfileRequestUpdateSerializer(serializers.ModelSerializer):
    access_groups = serializers.PrimaryKeyRelatedField(
        queryset=AccessGroupModel.objects.filter(is_active=True),
        required=False,
        allow_empty=True,
        many=True
    )

    class Meta:
        model = models.ContractorProfileRequestModel
        fields = (
            'id',
            'is_approved',
            'access_groups',
        )

    def validate(self, attrs):
        instance = self.instance
        if instance.is_touched:
            raise drf_exceptions.ValidationError({"message": "Заявка уже была рассмотрена"})
        access_groups = attrs.get('access_groups')
        if access_groups:
            organization = instance.organization
            if organization:
                from contractor_permissions.utils import get_available_access_groups
                available_access_groups = get_available_access_groups(organization)
                for access_group in access_groups:
                    if not available_access_groups.filter(pk=access_group.pk).exists():
                        raise drf_exceptions.ValidationError(
                            f'Группа доступа {access_group.name} не доступна для организации {organization.name}'
                        )
        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if instance.is_approved:
                access_groups = list(instance.access_groups.all())
                if access_groups:
                    contractor_profile = models.ContractorProfileModel.objects.get(
                        user=instance.user, contractor=instance.organization
                    )
                    for each in access_groups:
                        each.members.add(contractor_profile)
        return instance

    def to_representation(self, instance):
        return ContractorProfileRequestListSerializer(instance).data


class LocationPointSerializer(serializers.ModelSerializer):
    lat = RoundingDecimalField(max_digits=9, decimal_places=6)
    lon = RoundingDecimalField(max_digits=9, decimal_places=6)

    class Meta:
        model = models.LocationPointModel
        fields = [
            'id',
            'lat',
            'lon',
            'name',
            'address',
        ]


class LocationPointCreateSerializer(serializers.ModelSerializer):
    lat = RoundingDecimalField(max_digits=9, decimal_places=6)
    lon = RoundingDecimalField(max_digits=9, decimal_places=6)

    class Meta:
        model = models.LocationPointModel
        fields = [
            'id',
            'lat',
            'lon',
            'name',
            'address',
            'related_object',
        ]

    def create(self, validated_data):
        admin_area = get_admin_area_for_point((validated_data.get('lon'), validated_data.get('lat')),)
        instance = self.Meta.model.objects.create(admin_area=admin_area, **validated_data)
        return instance


class LocationAdminAreaListSerializer(serializers.ModelSerializer):
    geometry = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.LocationAdminAreaModel
        fields = (
            'id',
            'name',
            'osm_id',
            'show_stats',
            'geometry'
        )

    def get_name(self, obj):
        request = self.context.get('request')
        if request:
            lang = request.LANGUAGE_CODE
            if lang == 'kk':
                return obj.name_kk
            elif lang == 'en':
                return obj.name_en
        return obj.name_ru  # по умолчанию русский

    def get_geometry(self, instance):
        return json.loads(instance.geom.json)


class LocationAdminAreaShortSerializer(serializers.ModelSerializer):
    """Области без геометрии"""
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.LocationAdminAreaModel
        fields = (
            'id',
            'name',
            'osm_id',
            'show_stats',
        )

    def get_name(self, obj):
        request = self.context.get('request')
        if request:
            lang = request.LANGUAGE_CODE
            if lang == 'kk':
                return obj.name_kk
            elif lang == 'en':
                return obj.name_en
        return obj.name_ru  # по умолчанию русский


class LocationAdminAreaDetailSerializer(serializers.ModelSerializer):
    geometry = serializers.SerializerMethodField()
    children = LocationAdminAreaListSerializer(many=True)
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.LocationAdminAreaModel
        fields = (
            'id',
            'name',
            'osm_id',
            'show_stats',
            'geometry',
            'children',
        )

    def get_name(self, obj):
        request = self.context.get('request')
        if request:
            lang = request.LANGUAGE_CODE
            if lang == 'kk':
                return obj.name_kk
            elif lang == 'en':
                return obj.name_en
        return obj.name_ru  # по умолчанию русский

    def get_geometry(self, instance):
        return json.loads(instance.geom.json)


# Номенклатура
class AppNomenclatureSerializer(serializers.ModelSerializer):
    base_measure_unit = MeasureUnitListSerializer()
    goods_type = GoodsTypeAppSerializer()

    class Meta:
        model = models.NomenclatureModel
        fields = (
            'id',
            'article_number',
            'name',
            'name_short',
            'base_measure_unit',
            'goods_type',
            'price_by_catalog',
        )


class CostItemModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CostItemModel
        fields = (
            'id',
            'name',
            'code',
            'contractor'
        )


class LegalEntityCreateFrom1CSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LegalEntityModel
        fields = (
            'id',
            'external_id',
            'inn',
            'name',
            'contractor',
        )


#WorkDirection:
class WorkDirectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkDirectionModel
        fields = (
            'id',
            'name',
            'contractor',
        )

    def validate(self, attrs):
        contractor = attrs.get('contractor')
        if not contractor:
            raise drf_exceptions.ValidationError('Contractor required.')
        request = self.context.get('request')
        if not request:
            raise drf_exceptions.ValidationError('Request required')
        user = request.user.profile
        from contractor_permissions.utils import check_contractor_permission
        check_contractor_permission(user.pk, contractor.pk, 'admin', None)
        return attrs


class WorkDirectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkDirectionModel
        fields = (
            'id',
            'name',
            'is_archive',
        )


class WorkDirectionDetailSerializer(serializers.ModelSerializer):
    contractor = ContractorModelShortSerializer()

    class Meta:
        model = models.WorkDirectionModel
        fields = (
            'id',
            'name',
            'is_archive',
            'contractor',
        )


class WorkDirectionListSerializer(serializers.ModelSerializer):
    contractor = ContractorModelShortSerializer()

    class Meta:
        model = models.WorkDirectionModel
        fields = (
            'id',
            'name',
            'is_archive',
            'contractor',
        )