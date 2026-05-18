from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import Q

from contractor_permissions.utils import check_contractor_permission

from rest_framework import exceptions as drf_exceptions

from common.models import BaseModel

from . import models


def get_section_qs(request):
    queryset = models.WikiSectionModel.objects.filter(is_active=True)
    contractor_id = request.query_params.get('contractor')
    user = request.user.profile
    if contractor_id:
        try:
            check_contractor_permission(user.pk, contractor_id, 'contractor_wiki_admin', None)
        except drf_exceptions.PermissionDenied:
            queryset = queryset.filter(
                Q(
                    wiki_access__contractor_profile__user=user,
                    wiki_access__contractor_profile__contractor_id=contractor_id,
                    public=False,
                ) |
                Q(
                    public=True,
                ),
                contractor_id=contractor_id,

            )
        else:
            queryset = queryset.filter(
                contractor_id=contractor_id,
            )
    else:
        related_object_id = request.query_params.get('related_object')
        if related_object_id:
            try:
                original_object = BaseModel.objects.super_get(related_object_id)
            except (ValidationError, ObjectDoesNotExist):
                queryset = queryset.none()
            else:
                if original_object.get_detail_permission(request):
                    queryset = queryset.filter(related_object_id=related_object_id)
                else:
                    queryset = queryset.none()
        else:
            queryset = queryset.filter(related_object__isnull=True, contractor__isnull=True)
    return queryset


def get_chapter_qs(request):
    queryset = models.WikiChapterModel.objects.filter(is_active=True).order_by('sort')
    contractor_id = request.query_params.get('contractor')
    user = request.user.profile
    if contractor_id:
        try:
            check_contractor_permission(user.pk, contractor_id, 'contractor_wiki_admin', None)
        except drf_exceptions.PermissionDenied:
            queryset = queryset.filter(
                Q(
                    section__wiki_access__contractor_profile__user=user,
                    section__wiki_access__contractor_profile__contractor_id=contractor_id
                ) |
                Q(section__public=True),
                section__contractor_id=contractor_id,
            )
        else:
            queryset = queryset.filter(
                section__contractor_id=contractor_id,
            )
    else:
        related_object_id = request.query_params.get('related_object')
        if related_object_id:
            try:
                related_object = BaseModel.objects.super_get(related_object_id)
            except (ValidationError, ObjectDoesNotExist,):
                return queryset.none()
            if related_object.get_detail_permission(request):
                queryset = queryset.filter(related_object_id=related_object_id)
            else:
                return queryset.none()
        else:
            queryset = queryset.filter(related_object__isnull=True, section__contractor__isnull=True)
    return queryset


def get_page_qs(request):
    queryset = models.WikiPageModel.objects.filter(is_active=True).order_by('sort')
    contractor_id = request.query_params.get('contractor')
    user = request.user.profile
    if contractor_id:
        try:
            check_contractor_permission(user.pk, contractor_id, 'contractor_wiki_admin', None)
        except drf_exceptions.PermissionDenied:
            queryset = queryset.filter(
                Q(
                    chapter__section__wiki_access__contractor_profile__user=user,
                    chapter__section__wiki_access__contractor_profile__contractor_id=contractor_id
                ) |
                Q(chapter__section__public=True),
                chapter__section__contractor_id=contractor_id,
            )
        else:
            queryset = queryset.filter(
                chapter__section__contractor_id=contractor_id,
            )
    else:
        related_object_id = request.query_params.get('related_object')
        if related_object_id:
            try:
                related_object = BaseModel.objects.super_get(related_object_id)
            except (ValidationError, ObjectDoesNotExist,):
                return queryset.none()
            if related_object.get_detail_permission(request):
                queryset = queryset.filter(related_object_id=related_object_id)
            else:
                return queryset.none()
        else:
            queryset = queryset.filter(related_object__isnull=True, chapter__section__contractor__isnull=True)
    return queryset
