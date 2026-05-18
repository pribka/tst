from dal import autocomplete

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import BadRequest
from django.db.models import (Case, CharField, Count, Exists, Prefetch, Q, Sum,
                              Value, When, F)
from django.db import transaction
from django.http import HttpResponse, JsonResponse, FileResponse

from drf_haystack.viewsets import HaystackGenericAPIView
from haystack.query import RelatedSearchQuerySet, SearchQuerySet
from rest_framework import exceptions as drf_exceptions
from rest_framework import mixins, status, viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer

from bkz3.settings import DEFAULT_PRICE_TYPE_CODE
from app_info.models import AppInfo
from common.catalogs.models import (ContractorModel, DeliveryPointModel,
                                    OfferModel, UserURLsModel)
from common.paginators import CustomPagination
from common.views import BaseCatalogViewSet, BaseModelViewSet, action
from common.utils import get_filter_queryset, get_search_result

from integration_1c.utils import send_update_goods_price_to_1c
from users.models import ProfileModel
from users.serializers import AppUserShortSerializer

from contractor_permissions.models import (ContractorPermissionRoleModel,
                                           ContractorPermissionRoleProfileModel)

from . import models, permissions, serializers
from .utils import get_contractors_filtered_list, set_uids_for_uploaded_contractors, handle_upload_contractors, \
    create_contractors_from_dict, get_contractor_report_file, set_balances, block_contractor_users, unblock_contractor_users


# from common.catalogs.serializers import (AppWarehouseSerializer,
#                                          OfferModelSerializer,
#                                          MyDeliveryPointSerializer,
#                                          MyDeliveryPointSerializerPost)


class NomenclatureViewSet(BaseCatalogViewSet):
    model = models.NomenclatureModel

    def update(self, request, *args, **kwargs):
        return Response(status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response(status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        return Response(status.HTTP_405_METHOD_NOT_ALLOWED)


class PriceTypeModelViewSet(BaseCatalogViewSet):
    model = models.PriceTypeModel


class WarehouseModelViewSet(BaseCatalogViewSet):
    model = models.WarehouseModel


class GoodsCategoryModelViewSet(BaseCatalogViewSet):
    model = models.GoodsCategoryModel
    serializer_class = serializers.GoodsCategoryListSerializer
    queryset = models.GoodsCategoryModel.objects.filter(is_active=True)
    pagination_class = None

    def get_queryset(self):
        qs = self.queryset

        parent = self.request.query_params.get('parent', None)
        qs = qs.filter(parent=parent)
        return qs.distinct()

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        resp_data = resp.data
        category_with_goods_list = list()
        for category in resp_data:
            if category['goods_count'] > 0:
                category_with_goods_list.append(category)
        resp.data = category_with_goods_list
        return resp


class GoodCategoryTreeParentStructure(APIView):
    def get(self, request, *args, **kwargs):
        category_id = self.kwargs.get('pk')
        category = models.GoodsCategoryModel.objects.get(pk=category_id,
                                                         is_active=True)
        parents = category.get_ancestors(ascending=False, include_self=True)
        root = category.get_root()
        category_siblings = category.get_siblings(include_self=False)

        do_not_get_child_list = (parents | category_siblings).exclude(id=category.id).distinct()
        context = {"accepted_nodes": parents, "do_not_get_child_list": do_not_get_child_list, "request": request}
        root_data = serializers.GoodsCategoryRootSerializer(root, context=context).data
        list_with_only_goods = list()
        if root_data['children'] is None:
            root_data['children'] = []
        for ready_category in root_data['children']:
            if ready_category['goods_count'] > 0:
                list_with_only_goods.append(ready_category)
        root_data['children'] = list_with_only_goods
        # TODO Возможно есть решение покрасивее
        return Response(data=[root_data])


class GoodsModelViewSet(BaseCatalogViewSet):
    model = models.GoodsModel

    def get_queryset(self):
        category = self.request.query_params.get('category', None)
        qs = self.model.get_queryset(
            price_type_code=DEFAULT_PRICE_TYPE_CODE)  # TODO переопределил как система прав не используется
        if category:
            category_obj = models.GoodsCategoryModel.objects.get(pk=category)
            descendants = category_obj.get_descendants(include_self=True)
            qs = qs.filter(category__in=descendants)

        return qs

    @action(methods=('get',), detail=True, url_path='availability')
    def get_remnants(self, request, *args, **kwargs):
        try:
            from bkz3.settings import ONLY_DEFAULT_WAREHOUSE_IN_LIST
            only_default_warehouse_in_list = ONLY_DEFAULT_WAREHOUSE_IN_LIST
        except:
            only_default_warehouse_in_list = False
        goods = self.get_object()
        my = request.query_params.get('my', '')

        if not request.user.profile.warehouse_select_is_available or only_default_warehouse_in_list:
            qs = goods.remnants.select_related('warehouse__manager__user').filter(
                (Q(is_active=True) & Q(warehouse__default_warehouse=True)))
        else:
            qs = goods.remnants.select_related('warehouse__manager__user').filter(
                (Q(is_active=True) & Q(quantity__gt=0)) | (Q(is_active=True) & Q(warehouse__default_warehouse=True)))

        if my == 'true':
            qs = self.filter_my_warehouses(request, qs)
        qs = qs.order_by('warehouse__default_warehouse', 'warehouse__sort', 'warehouse__name')
        page = self.paginate_queryset(qs)
        data = serializers.GoodsAvailabilitySerializer(page, many=True).data
        return self.get_paginated_response(data)

    @action(methods=('get',), detail=True, url_path='available_count')
    def get_available_count(self, request, *args, **kwargs):
        goods = self.get_object()
        my = request.query_params.get('my', '')
        qs = goods.remnants.filter(is_active=True,)
        if my == 'true':
            qs = self.filter_my_warehouses(request, qs)
        available_count = qs.aggregate(Sum('quantity'))['quantity__sum']
        if available_count is None:
            available_count = 0
        return Response({'count': available_count})

    def filter_my_warehouses(self, request, qs):
        user = request.user.profile
        contractor = user.contractors.first()
        if contractor:
            my_warehouses = contractor.warehouses.all()
        else:
            my_warehouses = []
        return qs.filter(warehouse__in=my_warehouses)

    @action(methods=('get',), detail=True, url_path='by_category')
    def get_goods_by_category(self, request, *args, **kwargs):
        goods = self.get_object()
        category_list = goods.category.all()
        qs = self.model.get_queryset().filter(category__in=category_list).exclude(
            id=goods.id)  # TODO переопределил как система прав не используется
        serialized_data = serializers.GoodsModelListSerializer(qs, many=True).data
        return Response(serialized_data, status=200)

    @action(methods=('put',), detail=True, url_path='update_price')
    def update_price(self, request, *args, **kwargs):
        user = request.user.profile
        if not user.can_edit_goods_price:
            raise drf_exceptions.PermissionDenied()
        instance = self.get_object()
        serializer = serializers.GoodsModelUpdatePriceSerializer(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)
        # TODO пока стоит заглушка. Необходимо изменять цену на бэке в integration_1c от запроса самой 1С
        data, status = send_update_goods_price_to_1c(serializer.validated_data)
        if status == 200:
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(data)


class GoodsModelSearchView(HaystackGenericAPIView):
    index_models = (models.GoodsModel,)
    serializer_class = serializers.GoodsModelSearchSerializer
    pagination_class = CustomPagination
    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request, *args, **kwargs):
        text = request.query_params.get('text')
        if not text:
            search_queryset = SearchQuerySet().none()
        else:
            search_queryset = RelatedSearchQuerySet().filter(
                text=text,
            ).models(models.GoodsModel).load_all()
        ordering = request.query_params.get('ordering', '').split(',')
        if ordering:
            search_queryset = search_queryset.order_by(*ordering)
        page = self.paginate_queryset(list(search_queryset))
        s_data = self.serializer_class(page, many=True, context={'request': request}).data
        return self.get_paginated_response(s_data)


class DeliveryAddressesViewSet(BaseCatalogViewSet):
    model = models.DeliveryAddress


class ContractModelViewSet(BaseCatalogViewSet):
    model = models.ContractModel

    @action(methods=('get',), detail=False, url_path='payment')
    def get_payment(self, request, *args, **kwargs):
        contract_code = request.query_params.get('code')
        if contract_code:
            try:
                contract = models.ContractModel.objects.prefetch_related(
                    'payment__stages__payment_option'
                ).get(code=contract_code)
            except models.ContractModel.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            contract_id = request.query_params.get('id')
            if contract_id:
                try:
                    contract = models.ContractModel.objects.prefetch_related(
                        'payment__stages__payment_option'
                    ).get(pk=contract_id)
                except models.ContractModel.DoesNotExist:
                    return Response(status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        user = request.user.profile
        if not user.contractors.filter(contracts__contract=contract).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        payment = contract.payment
        data = serializers.ContractPaymentSerializer(payment).data
        return Response(data)


class ContractorMemberModelViewSet(BaseCatalogViewSet):
    model = models.ContractorMemberModel

    @action(methods=('get',), detail=False, url_path='my')
    def get_my_contractor_members(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user.profile
        queryset = queryset.filter(contractor_id__in=user.my_organizations).distinct().order_by('name')
        queryset = get_filter_queryset(request, self.model, queryset)
        page = self.paginate_queryset(queryset)
        serializer = serializers.ContractorMemberModelSerializer(page, context={'request': request}, many=True)
        s_data = serializer.data
        return self.get_paginated_response(s_data)


class ContractorModelViewSet(BaseCatalogViewSet):
    model = models.ContractorModel

    def get_queryset(self):
        return self.model.get_queryset(request=self.request)

    def annotate_contractors_queryset(self, qs):
        from django.db.models import OuterRef, Subquery

        from bpms.chat.models import ChatModel
        from bpms.tasks.models import TaskModel
        from crm.models import GoodsOrderModel
        orders = GoodsOrderModel.objects.filter(
            is_active=True,
            contractor=OuterRef('pk')
        ).order_by('-created_at')[:1]
        contractor_members = models.ContractorMemberModel.objects.filter(
            is_active=True,
            contractor=OuterRef('pk')
        ).order_by('-created_at')[:1]
        delivery_points = DeliveryPointModel.objects.filter(
            is_active=True,
            contractors=OuterRef('pk')
        ).order_by('-created_at')[:1]
        qs = qs.annotate(
            delivery_address=Subquery(delivery_points.values('name')),
            inn=Subquery(contractor_members.values('inn')),
            total_orders=Count(
                'orders',
                filter=Q(
                    orders__is_active=True,
                    orders__execute_status__code='completed'
                ),
                distinct=True
            ),
            orders_in_progress=Count(
                'orders',
                filter=Q(
                    orders__is_active=True,
                    orders__execute_status__code__in=(
                        'default',
                        'processed',
                        'partially_canceled'
                    )
                ),
                distinct=True
            ),
            last_order_date=Subquery(orders.values('created_at')),
            status=Case(
                When(is_archived=True, then=Value('Архивный')),
                When(Q(Exists(GoodsOrderModel.objects.filter(
                        is_active=True,
                        contractor=OuterRef('pk')
                        ))) |
                     Q(Exists(TaskModel.objects.filter(
                            is_active=True,
                            contractor=OuterRef('pk')
                        ))) |
                     Q(Exists(ChatModel.objects.filter(
                            is_active=True,
                            dealer=OuterRef('pk'))
                        )), then=Value('Текущий')),
                default=Value('Новый'),
                output_field=CharField(),
            )
        )
        return qs

    def create(self, request, *args, **kwargs):
        user = request.user.profile
        if not user.has_full_access_to_order_editing:
            raise drf_exceptions.PermissionDenied()

        serializer = serializers.ContractorModelCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        contractor = self.annotate_contractors_queryset(
            self.model.objects.filter(id=obj.id)
        )[0]
        return Response(
            serializers.ContractorsDetailedListSerializer(
                contractor
            ).data
        )

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        contractor = self.annotate_contractors_queryset(
            self.model.objects.filter(id=resp.data['id'])
        )[0]
        resp.data = serializers.ContractorsDetailedListSerializer(
                contractor
            ).data
        return resp

    @action(methods=('get',), detail=False, url_path='form_info')
    def get_form_info(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(
                is_active=True,
                code='client_form_info'
            ).metadata
        except AppInfo.DoesNotExist:
            data = dict()
        return Response(data)

    @action(methods=('get',), detail=False, url_path='create_form_info', permission_classes=(IsAuthenticated,))
    def get_create_form_info(self, request, *args, **kwargs):
        user = request.user.profile
        data = dict()
        default_data = {
            'ru': {
                "tax_ID_label": "БИН/ИНН"
            },
            'kk': {
                "tax_ID_label": "БСН/ЖСН"
            }
        }
        try:
            data = AppInfo.objects.get(
                is_active=True,
                code='create_contractor_form_info'
            ).metadata
        except AppInfo.DoesNotExist:
            data = default_data.get(user.language, {
                "tax_ID_label": "БИН/ИНН"
            })
        return Response(data)

    @action(methods=('get',), detail=True, url_path='action_info', permission_classes=(IsAuthenticated,))
    def action_info(self, request, *args, **kwargs):
        # TODO - прописать логику !!!!!!!!!!!!!!!
        resp = {
            'actions': {
                'edit': {
                    'availability': True
                },
                'set_archive': {
                    'availability': True
                }

            }
        }
        return Response(resp)

    @action(methods=('get',), detail=True, url_path='employees')
    def get_employees(self, request, *args, **kwargs):
        heads = request.query_params.get('heads', False)
        try:
            contractor = models.ContractorModel.objects.get(is_active=True, pk=kwargs.get('pk'))
        except models.ContractorModel.DoesNotExist:
            raise drf_exceptions.NotFound('Организация не найдена')
        if heads:
            director = ProfileModel.objects.filter(
                is_active=True,
                contractor_profile__contractor=contractor,
                contractor_profile__director=True,
            )

            admin_roles = ContractorPermissionRoleModel.objects.filter(
                is_active=True,
                contractor_permissions__permission_type_id='admin',
                contractor=contractor,
            ).values_list('pk', flat=True)
            admin_ids = set(ContractorPermissionRoleProfileModel.objects.filter(
                contractor_permission_role_id__in=admin_roles,
            ).values_list('contractor_profile__user', flat=True))
            admins = ProfileModel.objects.filter(
                is_active=True,
                id__in=admin_ids
            ).order_by('user__last_name', 'user__first_name', 'user__middle_name')

            ids = set()
            employees = list()

            for item in director:
                ids.add(item.id)
                employees.append(item)

            for item in admins:
                if item.id not in ids:
                    ids.add(item.id)
                    employees.append(item)
        else:
            employees = ProfileModel.objects.filter(
                is_active=True,
                contractor_profile__contractor=contractor
            )
        return Response(AppUserShortSerializer(employees, many=True).data)

    @action(methods=('get',), detail=False, url_path='get_by_id', permission_classes=(IsAuthenticated,))
    def get_by_id(self, request, *args, **kwargs):
        contractor_id = request.query_params.get('id')
        user = request.user.profile
        exclude_contractors = user.contractor_profile.filter(is_active=True, director=True
                                                             ).values_list('contractor', flat=True)
        if contractor_id:
            queryset = models.ContractorModel.objects.filter(
                is_active=True, pk=contractor_id).exclude(pk__in=exclude_contractors)
        else:
            queryset = models.ContractorModel.objects.none()
        paginator = CustomPagination()
        page = paginator.paginate_queryset(queryset, request, self)
        s_data = serializers.ContractorModelByIdSerializer(page, context={"request": request}, many=True).data
        return paginator.get_paginated_response(s_data)

    @action(methods=('get',), detail=False, url_path='detailed_list',)
    def get_contractors_detailed_list(self, request, *args, **kwargs):
        self_queryset = self.get_queryset().filter(is_carrier=False).order_by('name')
        annotate_self_queryset = self.annotate_contractors_queryset(
                self_queryset
            )

        qs = self.filter_queryset(
            annotate_self_queryset
        )
        page = self.paginate_queryset(qs)
        serialized_data = serializers.ContractorsDetailedListSerializer(
            page,
            many=True
        ).data
        return self.get_paginated_response(serialized_data)

    @action(methods=('get',), detail=False, url_path='to_add',)
    def get_contractors_to_add(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')

        if not search:
            return Response([])

        lookup = Q()
        lookup |= Q(name__icontains=search)
        lookup |= Q(full_name__icontains=search)
        lookup |= Q(contractor_members__inn__icontains=search)
        lookup = Q(is_active=True) & lookup

        queryset = self.model.objects.filter(
            lookup
        ).distinct().order_by('name')
        serialized_data = serializers.ContractorsToAddSerializer(
            queryset,
            many=True
        ).data
        return Response(serialized_data)

    @action(methods=('get',), detail=False, url_path='delivery_points',)
    def get_delivery_points(self, request, *args, **kwargs):
        query_params = request.query_params
        lat_gte = query_params.get('lat__gte', 0)
        lat_lte = query_params.get('lat__lte', 0)
        lon_gte = query_params.get('lon__gte', 0)
        lon_lte = query_params.get('lon__lte', 0)
        qs = models.DeliveryPointModel.objects.prefetch_related(
            Prefetch(
                lookup='contractors',
                queryset=models.ContractorModel.objects.filter(is_active=True, is_carrier=False,)
            )
        ).filter(
            is_active=True,
            lat__gte=lat_gte,
            lat__lte=lat_lte,
            lon__gte=lon_gte,
            lon__lte=lon_lte,
            contractors__isnull=False,
            contractors__is_carrier=False,
            contractors__is_active=True,
        ).distinct().order_by('-created_at')
        data = serializers.DeliveryPointWithContractorsSerializer(qs, many=True, context={'request': request}).data
        return Response(data)


class PotentialContractorModelViewSet(BaseCatalogViewSet):
    model = models.PotentialContractorModel

    def get_queryset(self):
        return self.model.objects.filter(
                is_active=True,
            ).prefetch_related(
                'my_tasks',
                'my_tasks__event_calendars',
                'my_tasks__event_calendars__events',
            )

    def annotate_leads_queryset(self, qs):
        from django.db.models import OuterRef
        from bpms.tasks.models import TaskModel
        return qs.annotate(
                status=Case(
                    When(contractor__isnull=False, then=Value('Создан клиент')),
                    When(is_archived=True, then=Value('Архивный')),
                    When(Exists(TaskModel.objects.filter(
                        is_active=True,
                        potential_contractor=OuterRef('pk')
                    )), then=Value('Текущий')),
                    default=Value('Новый'),
                    output_field=CharField(),
                )
            )

    def create(self, request, *args, **kwargs):
        serializer = serializers.PotentialContractorModelCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        lead = self.annotate_leads_queryset(
            self.model.objects.filter(id=obj.id)
        )[0]
        return Response(
            serializers.PotentialContractorModelShortSerializer(
                lead
            ).data
        )

    def update(self, request, *args, **kwargs):
        resp = super().update(request, *args, **kwargs)
        lead = self.annotate_leads_queryset(
            self.model.objects.filter(id=resp.data['id'])
        )[0]
        resp.data = serializers.PotentialContractorModelShortSerializer(
                lead
            ).data
        return resp

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(
            self.annotate_leads_queryset(
                self.get_queryset().order_by('name')
            )
        )
        page = self.paginate_queryset(qs)
        serialized_data = serializers.PotentialContractorModelShortSerializer(
            page,
            many=True
        ).data
        return self.get_paginated_response(serialized_data)

    @action(methods=('get',), detail=False, url_path='form_info')
    def get_form_info(self, request, *args, **kwargs):
        try:
            data = AppInfo.objects.get(
                is_active=True,
                code='lead_form_info'
            ).metadata
        except AppInfo.DoesNotExist:
            data = dict()
        return Response(data)

    @action(methods=('get',), detail=True, url_path='action_info', permission_classes=(IsAuthenticated,))
    def action_info(self, request, *args, **kwargs):
        resp = {
            'actions': {
                'edit': {
                    'availability': True
                },
                'set_archive': {
                    'availability': True
                },
                'convert_to_contractor': {
                    'availability': True
                }

            }
        }
        lead = self.get_object()
        if lead.is_archived:
            resp['actions'].pop('set_archive')
            resp['actions'].pop('convert_to_contractor')
        elif lead.contractor:
            resp['actions'].pop('convert_to_contractor')
        return Response(resp)


class GoodsRemnantModelViewSet(BaseCatalogViewSet):
    model = models.GoodsRemnantModel


class GoodsPriceModelViewSet(BaseCatalogViewSet):
    model = models.GoodsPriceModel


class PaymentFormModelViewSet(BaseCatalogViewSet):
    model = models.PaymentFormModel


class MyDeliveryPointsViewSet(mixins.CreateModelMixin,
                              mixins.DestroyModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    '''
    ViewSet для компонента "MyDeliveryPoints"
    '''
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MyDeliveryPointSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.MyDeliveryPointSerializerPost
        return serializers.MyDeliveryPointSerializer

    def get_queryset(self):
        # current_profile = get_current_authenticated_profile()
        query_contractor = self.request.query_params.get('contractor')
        # Берем точки доставки контрагентов пользователя
        if self.request.user.profile.has_full_access_to_order_editing:
            queryset = DeliveryPointModel.objects.filter(
                is_active=True,
                contractors__isnull=False).order_by('-created_at')
        else:
            queryset = DeliveryPointModel.objects.filter(
                contractors__profiles__user=self.request.user,
                is_active=True).order_by('-created_at')

        if query_contractor is not None:
            # Пользователь у которого has_full_access_to_order_editing = True
            # имеет доступ к точкам любого контрагента
            if not self.request.user.profile.has_full_access_to_order_editing:
                # Дополнительная проверка что контрагент из запроса связан
                # с текущим пользователем. Если query_params содержит id
                # контрагента, то полученый ранее queryset фильтруется
                # по этому id. Если id контрагента не связано с текщим
                # пользователем резульатом фильтрации будет пустой список.
                if not ContractorModel.objects.filter(
                    is_active=True,
                    pk=query_contractor,
                    profiles__user=self.request.user).exists():
                    raise BadRequest('Invalid request.')
            queryset = queryset.filter(
                contractors=query_contractor).order_by('-created_at')
        return queryset.distinct()

    def perform_destroy(self, instance):
        instance.is_active=False
        instance.save()


class OfferViewSet(APIView):
    '''
    Представление для компонента "Оферта"
    '''
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''Возвращает первую оферту'''
        queryset = OfferModel.objects.filter(is_active=True).first()
        serializer = serializers.OfferModelSerializer(queryset)
        return Response(serializer.data)


class URLsWidgetViewSet(APIView):
    '''
    Представление для компонента "Ссылки"
    '''

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''Возвращает все объекты модели UserURLsModel'''
        queryset = UserURLsModel.objects.filter(is_active=True)
        serializer = serializers.UserURLsModelSerializer(queryset, many=True)
        return Response(serializer.data)


class RegisterHelpViewSet(APIView):
    '''
    Представление для компонента вывода текста помощи при регистрации
    '''
    permission_classes = (AllowAny,)

    def get(self, request):
        '''Возвращает текст помощи при регистрации'''
        queryset = models.RegisterHelpModel.objects.filter(is_active=True).first()
        serializer = serializers.RegisterHelpModelSerializer(queryset)
        return Response(serializer.data)


class DeliveryPurposeViewSet(BaseModelViewSet):
    model = models.DeliveryPurposeModel

    def create(self, request, *args, **kwargs):
        user = request.user.profile
        if not user.can_edit_goods_price:
            raise drf_exceptions.PermissionDenied()
        return super().create(request, *args, **kwargs)


class ContractorRelationTypesModelViewSet(BaseCatalogViewSet):
    model = models.ContractorRelationTypeModel

    def get_queryset(self):
        PROJECT_ADD_RELATIONS = set([
            'affiliate',
            'contractor',
            'dealer',
            'partner',
            'vendor'
        ])
        qs = super().get_queryset()
        if self.request.query_params.get('projectAdd', False):
            return qs.filter(code__in=PROJECT_ADD_RELATIONS)
        else:
            return qs


class ContractorListView(generics.ListAPIView):
    serializer_class = serializers.ContractorModelListSerializer
    pagination_class = CustomPagination
    queryset = ContractorModel.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        qs = self.queryset

        search_string = self.request.query_params.get('search', None)
        if search_string is not None:
            qs = qs.filter(name__icontains=search_string)
            return qs.distinct()
        else:
            return qs


@csrf_exempt
def upload_contractors(request):
    if request.user.is_anonymous or not request.user.is_superuser:
        return HttpResponse('not_ok')
    if not (request.method == 'POST' and request.FILES):
        return HttpResponse('not_ok')
    file = request.FILES.getlist('upload')
    if not file:
        raise drf_exceptions.ValidationError('File not found.')
    set_uid = request.POST.get('set_uid', 'false')
    if set_uid == 'true':
        stream = set_uids_for_uploaded_contractors(file[0])
        return FileResponse(stream, as_attachment=True)
    else:
        result = handle_upload_contractors(file[0])
        return JsonResponse(result)


@csrf_exempt
def kijlr3awx8_set_balances(request):
    if request.user.is_anonymous or not request.user.is_superuser:
        return HttpResponse('not_ok')
    if not (request.method == 'POST' and request.FILES):
        return HttpResponse('not_ok')
    file = request.FILES.getlist('upload')[0]
    if not file:
        raise drf_exceptions.ValidationError('File not found')
    result = set_balances(file)
    return JsonResponse(result)


class ContractorsReportFileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        root_id = request.query_params.get('root')
        if not root_id:
            raise drf_exceptions.ValidationError({'message': 'root не указан'})
        try:
            root = models.ContractorModel.objects.get(is_active=True, pk=root_id)
        except models.ContractorModel.DoesNotExist:
            raise drf_exceptions.ValidationError({'message': 'root не найден'})
        stream = get_contractor_report_file(root)
        return FileResponse(
            stream, filename=f'Выгрузка организаций для {root.member_inn}.xlsx', as_attachment=True
        )


class BlockContractorUsersView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        root_id = request.data.get('root')
        if not root_id:
            raise drf_exceptions.ValidationError({'message': 'root required'})
        try:
            root = models.ContractorModel.objects.get(is_active=True, pk=root_id)
        except models.ContractorModel.DoesNotExist:
            raise drf_exceptions.ValidationError({'message': 'root не найден'})
        block_contractor_users(root)
        return Response('ok')


class UnblockContractorUsersView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            raise drf_exceptions.PermissionDenied()
        root_id = request.data.get('root')
        if not root_id:
            raise drf_exceptions.ValidationError({'message': 'root required'})
        try:
            root = models.ContractorModel.objects.get(is_active=True, pk=root_id)
        except models.ContractorModel.DoesNotExist:
            raise drf_exceptions.ValidationError({'message': 'root не найден'})
        unblock_contractor_users(root)
        return Response('ok')


class CreateContractorsFromDict(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response(status.HTTP_403_FORBIDDEN)
        data = request.data
        with transaction.atomic():
            create_contractors_from_dict(data)
        return Response('ok')


class ContractorListByIIN(generics.ListAPIView):
    serializer_class = serializers.ContractorModelByINNSerializer
    authentication_classes = ()
    permission_classes = ()
    queryset = models.ContractorModel.objects.filter(is_active=True)

    def get_queryset(self):
        qs = self.queryset
        inn = self.request.query_params.get('text')
        if not inn:
            return qs.none()
        if len(inn) < 5:
            return qs.none()
        qs = qs.filter(contractor_members__inn=inn)
        return qs


class GetContractorFromStatGovView(APIView):
    def get(self, request, *args, **kwargs):
        iin = request.query_params.get('bin')
        if not iin:
            return Response({
                "success": False,
                "obj": None,
                "description": None
            })
        import requests
        r = requests
        resp = r.get(url='https://stat.gov.kz/api/juridical', params={"bin": iin, "lang": "ru"})
        return Response(resp.json())


class ContractorProfileRequestModel(BaseModelViewSet):
    model = models.ContractorProfileRequestModel
    permission_classes = (IsAuthenticated, permissions.ContractorProfileRequestPermission,)

    def create(self, request, *args, **kwargs):
        raise drf_exceptions.PermissionDenied()


class LocationAdminAreaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get_serializer_class(self):
        action = self.action
        if action == 'retrieve':
            return serializers.LocationAdminAreaDetailSerializer
        else:
            return serializers.LocationAdminAreaListSerializer



    def get_queryset(self):
        if self.action == 'list':
            query_params = self.request.query_params
            parent = None
            parent_id = query_params.get('parent')
            if parent_id:
                try:
                    parent = models.LocationAdminAreaModel.objects.get(pk=parent_id)
                except (models.LocationAdminAreaModel.DoesNotExist, ValidationError):
                    raise drf_exceptions.NotFound('Область не найдена')
            if parent:
                qs = models.LocationAdminAreaModel.objects.filter(is_active=True, parent=parent).order_by('name_ru')
            else:
                qs = models.LocationAdminAreaModel.objects.filter(is_active=True, parent__isnull=True).order_by(
                    'name_ru')
        else:
            qs = models.LocationAdminAreaModel.objects.filter(is_active=True).order_by('name_ru')
        return qs


@method_decorator(login_required, name='dispatch')
class NomenclatureAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return models.NomenclatureModel.objects.none()
        request = self.request
        qs = models.NomenclatureModel.get_queryset(request)
        if self.q:
            # Фильтруем результаты по введенному тексту self.q
            # Ищем совпадения в поле 'name' (или других полях)
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(article_number__icontains=self.q) |
                Q(name_short__icontains=self.q)
            )

        return qs.order_by('name', 'article_number',)


class CostItemViewSet(BaseCatalogViewSet):
    model = models.CostItemModel
    permission_classes = (IsAuthenticated,)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions['edit'] = {'availability': True}
            actions['delete'] = {'availability': True}
        return Response({'actions': actions})

    # @action(methods=('get', ), detail=False, url_path='action_info_from_contractor',)
    # def get_action_info_from_contractor(self, request, *args, **kwargs):
    #     actions = dict()
    #     contractor_id = request.query_params.get('contractor')
    #     if not contractor_id:
    #         return Response({'actions': actions})
    #     user = request.user.profile
    #     if not utils.check_ticket_category_create_permission(user, uuid.UUID(contractor_id)):
    #         return Response({'actions': actions})
    #     actions = {
    #         'create': {'availability': True},
    #         'edit': {'availability': True},
    #         'delete': {'availability': True},
    #     }
    #     return Response({'actions': actions})

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        search = request.query_params.get('search')
        if search:
            search_result = get_search_result(self.model, search)
            search_result_ids = [item['id'] for item in search_result]
            queryset = queryset.filter(pk__in=list(search_result_ids))
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response(status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_update(self, serializer):
        return Response(status.HTTP_405_METHOD_NOT_ALLOWED)


class WorkDirectionViewSet(BaseCatalogViewSet):
    model = models.WorkDirectionModel
    permission_classes = (IsAuthenticated,)

    @action(methods=('get',), detail=True, url_path='action_info')
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions['edit'] = {'availability': True}
            actions['delete'] = {'availability': True}
        return Response({'actions': actions})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        contractor_id = request.query_params.get('contractor')
        search = request.query_params.get('search')
        if search:
            search_result = get_search_result(self.model, search)
            search_result_ids = [item['id'] for item in search_result]
            queryset = queryset.filter(pk__in=list(search_result_ids))
        from users.utils import get_tree_departments_related_organizations
        if contractor_id:
            contractors_id = get_tree_departments_related_organizations((contractor_id,))
            queryset = queryset.filter(Q(contractor__isnull=True) | Q(contractor_id__in=contractors_id))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
