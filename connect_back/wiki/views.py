from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q, Value

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions as drf_exceptions

from common.paginators import CustomPagination
from common.models import BaseModel

from common.catalogs.models import ContractorProfileModel
from common.utils import get_search_bool

from bpms.bpms_common.permissions import IsSuperUserOrReadOnly

from contractor_permissions.utils import check_contractor_permission

from users.serializers import CachedAppUserPreviewSerializer

from . import models
from . import serializers
from . import utils
from . import permissions


from haystack.query import SearchQuerySet, RelatedSearchQuerySet


class WikiAccessView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        wiki_section_id = kwargs.get('pk')
        try:
            wiki_section = models.WikiSectionModel.objects.get(is_active=True, pk=wiki_section_id,)
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('Wiki section not found.')
        contractor = wiki_section.contractor
        if not contractor:
            raise drf_exceptions.ValidationError('Wiki section has not contractor')
        user = request.user.profile
        check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
        users = request.data.get('users')
        if not isinstance(users, list):
            raise drf_exceptions.ValidationError('invalid users')
        wiki_section.wiki_access.all().delete()
        if not users:
            return Response('ok')
        serializer_class = serializers.WikiAccessCreateSerializer
        with transaction.atomic():
            for each in users:
                try:
                    contractor_profile = ContractorProfileModel.objects.get(contractor=contractor, user_id=each)
                except (ValidationError, ObjectDoesNotExist):
                    raise drf_exceptions.ValidationError(f'Пользователь {user} не является сотрудником организации')
                serializer = serializer_class(
                    data={'contractor_profile': contractor_profile.pk, 'wiki_section': wiki_section.pk},
                    context={'request': request, 'view': self}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response('ok')

    def get(self, request, *args, **kwargs):
        wiki_section_id = kwargs.get('pk')
        try:
            wiki_section = models.WikiSectionModel.objects.get(is_active=True, pk=wiki_section_id, )
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('Wiki section not found.')
        contractor = wiki_section.contractor
        if not contractor:
            raise drf_exceptions.ValidationError('Wiki section has not contractor')
        user = request.user.profile
        check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
        qs = models.WikiAccessModel.objects.filter(
            wiki_section=wiki_section,
        ).order_by(
            'contractor_profile__user__user__last_name',
            'contractor_profile__user__user__first_name',
        ).values_list('contractor_profile__user', flat=True)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = CachedAppUserPreviewSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class WikiAccessAddView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        wiki_section_id = kwargs.get('pk')
        try:
            wiki_section = models.WikiSectionModel.objects.get(is_active=True, pk=wiki_section_id, )
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('Wiki section not found.')
        contractor = wiki_section.contractor
        if not contractor:
            raise drf_exceptions.ValidationError('Wiki section has not contractor')
        user = request.user.profile
        check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
        wiki_user_id = request.data.get('user')
        try:
            contractor_profile = ContractorProfileModel.objects.get(contractor=contractor, user_id=wiki_user_id)
        except (ValidationError, ObjectDoesNotExist):
            raise drf_exceptions.ValidationError(f'Пользователь {user} не является сотрудником организации')
        serializer = serializers.WikiAccessCreateSerializer(
                    data={'contractor_profile': contractor_profile.pk, 'wiki_section': wiki_section.pk},
                    context={'request': request, 'view': self}
                )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('ok')


class WikiAccessRemoveView(APIView):

    def post(self, request, *args, **kwargs):
        wiki_section_id = kwargs.get('pk')
        try:
            wiki_section = models.WikiSectionModel.objects.get(is_active=True, pk=wiki_section_id, )
        except ObjectDoesNotExist:
            raise drf_exceptions.ValidationError('Wiki section not found.')
        contractor = wiki_section.contractor
        if not contractor:
            raise drf_exceptions.ValidationError('Wiki section has not contractor')
        user = request.user.profile
        check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
        wiki_user_id = request.data.get('user')
        try:
            wiki_access = models.WikiAccessModel.objects.get(
                contractor_profile__contractor=contractor,
                contractor_profile__user_id=wiki_user_id,
                wiki_section=wiki_section,
            )
        except (ValidationError, ObjectDoesNotExist):
            return Response('ok')
        wiki_access.delete()
        return Response('ok')


class CurrentOrganizationActionInfo(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        actions = dict()
        user = request.user.profile
        current_contractor = user.get_or_set_current_contractor()
        if current_contractor:
            try:
                check_contractor_permission(user.pk, current_contractor.pk, 'contractor_wiki_admin', None)
            except drf_exceptions.PermissionDenied:
                pass
            else:
                actions = {
                    "create": {"availability": True},
                    "update": {"availability": True},
                    "delete": {"availability": True},
                }
        return Response({"actions": actions})


class WikiSectionViewSet(viewsets.ModelViewSet):
    queryset = models.WikiSectionModel.objects.filter(is_active=True)
    pagination_class = CustomPagination
    permission_classes = (permissions.SectionPermission,)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                'edit': {'availability': True},
                'delete': {'availability': True},
            }
        return Response({'actions': actions})

    @action(methods=('get',), detail=True, url_path='form',)
    def get_form(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.WikiSectionFormSerializer(instance, context={'request': request, 'view': self})
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return serializers.WikiSectionWriteSerializer
        return serializers.WikiSectionReadSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def get_object(self):
        """Сначала ищем по pk, потом по code."""
        instance_id = self.kwargs.get('pk')
        try:
            return models.WikiSectionModel.objects.get(pk=instance_id)
        except (ValidationError, ObjectDoesNotExist):
            try:
                return models.WikiSectionModel.objects.get(code=instance_id)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound()

    def list(self, request, *args, **kwargs):
        queryset = utils.get_section_qs(request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class WikiChapterViewSet(viewsets.ModelViewSet):
    queryset = models.WikiChapterModel.objects.filter(is_active=True).order_by('sort')
    pagination_class = CustomPagination
    permission_classes = (permissions.SectionPermission,)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                'edit': {'availability': True},
                'delete': {'availability': True},
            }
        return Response({'actions': actions})

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return serializers.WikiChapterWriteSerializer
        return serializers.WikiChapterReadSerializer

    @action(methods=('get',), detail=True, url_path='form', )
    def get_form(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.WikiChapterFormSerializer(instance, context={'request': request, 'view': self})
        return Response(serializer.data)

    def get_object(self):
        """Сначала ищем по pk, потом по code."""
        instance_id = self.kwargs.get('pk')
        try:
            return models.WikiChapterModel.objects.get(pk=instance_id)
        except (ValidationError, ObjectDoesNotExist):
            try:
                return models.WikiChapterModel.objects.get(code=instance_id)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = utils.get_chapter_qs(self.request)
        code = self.request.query_params.get('code')

        if code:
            queryset = queryset.filter(code=code)

        text = self.request.query_params.get('text')
        if text:
            s_queryset = RelatedSearchQuerySet().filter(text=text).models(
                models.WikiChapterModel
            ).load_all()
            if len(s_queryset) == 0:
                guess = SearchQuerySet().spelling_suggestion(text)
                if guess:
                    s_queryset = RelatedSearchQuerySet().filter(text=guess).models(
                        models.WikiChapterModel
                    ).load_all()
            queryset = queryset.filter(pk__in=s_queryset.values_list('object', flat=True))

        return queryset

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class WikiPageViewSet(viewsets.ModelViewSet):
    queryset = models.WikiPageModel.objects.filter(is_active=True).order_by('sort')

    pagination_class = CustomPagination
    permission_classes = (permissions.SectionPermission,)

    @action(methods=('get',), detail=True, url_path='action_info',)
    def get_action_info(self, request, *args, **kwargs):
        actions = dict()
        instance = self.get_object()
        if instance.get_update_permission(request):
            actions = {
                'edit': {'availability': True},
                'delete': {'availability': True},
            }
        return Response({'actions': actions})

    @action(methods=('get',), detail=True, url_path='form', )
    def get_form(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.WikiPageFormSerializer(instance, context={'request': request, 'view': self})
        return Response(serializer.data)

    def get_object(self):
        """Сначала ищем по pk, потом по code."""
        instance_id = self.kwargs.get('pk')
        try:
            return models.WikiPageModel.objects.get(pk=instance_id)
        except (ValidationError, ObjectDoesNotExist):
            try:
                return models.WikiPageModel.objects.get(code=instance_id)
            except (ValidationError, ObjectDoesNotExist):
                raise drf_exceptions.NotFound()

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request
        if self.action == 'list':
            queryset = utils.get_page_qs(self.request)
        text = self.request.query_params.get('text')
        search_true = get_search_bool()
        if text:
            search_queryset = RelatedSearchQuerySet().filter(text=text, is_active=search_true).models(
                models.WikiPageModel,
                models.WikiChapterModel,
                models.WikiSectionModel
            )

            if search_queryset.count() == 0:
                guess = SearchQuerySet().spelling_suggestion(text)
                if guess:
                    search_queryset = RelatedSearchQuerySet().filter(text=guess, is_active=search_true).models(
                        models.WikiPageModel,
                        models.WikiChapterModel,
                        models.WikiSectionModel
                    )
            if search_queryset.count() > 0:
                search_id_list = list(search_queryset.values_list('pk', flat=True))
                print("***SEARCH_ID_LIST****")
                print(search_id_list)
                section_qs = utils.get_section_qs(request).filter(
                    id__in=search_id_list
                ).annotate(
                    model=Value('wiki.WikiSectionModel')
                ).values('id', 'sort', 'name', 'is_active', 'model')
                chapter_qs = utils.get_chapter_qs(request).annotate(
                    model=Value('wiki.WikiChapterModel',)
                ).filter(
                    id__in=search_id_list
                ).values('id', 'sort', 'name', 'is_active', 'model')
                queryset = queryset.annotate(
                    model=Value('wiki.WikiPageModel')
                ).filter(
                    id__in=search_id_list
                ).values('id', 'sort', 'name', 'is_active', 'model')
                queryset = queryset.union(section_qs).union(chapter_qs)
            else:
                print('*******NO RESULT SEARCH *********')
                queryset = queryset.none()

        return queryset

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return serializers.WikiPageWriteSerializer
        text = self.request.query_params.get('text')
        if text:
            return serializers.WikiShortSearchSerializer

        return serializers.WikiPageReadSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
