from django.utils.translation import get_language_from_request

from drf_haystack.serializers import HaystackSerializer

from rest_framework import serializers, exceptions as drf_exceptions

from common.catalogs.serializers import ContractorModelShortSerializer

from contractor_permissions.utils import check_contractor_permission

from .models import WikiSectionModel, WikiChapterModel, WikiPageModel, WikiAccessModel
from . import search_indexes


class WikiChapterShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiChapterModel
        fields = (
            'id',
            'name',
            'sort',
            'code',
            'show_on_main_page',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['pages_num'] = instance.pages.filter(is_active=True).count()
        return data


class WikiSectionShortSerializer(serializers.ModelSerializer):
    # chapters = WikiChapterShortSerializer(many=True, read_only=True)

    class Meta:
        model = WikiSectionModel
        fields = (
            'id',
            'name',
            'created_at',
            'updated_at',
            'sort',
            'random_html',
            'use_in_wiki',
            'code',
        )


class WikiSectionFormSerializer(serializers.ModelSerializer):
    contractor = ContractorModelShortSerializer()

    class Meta:
        model = WikiSectionModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'random_html_ru',
            'random_html_kk',
            'created_at',
            'updated_at',
            'sort',
            'use_in_wiki',
            'code',
            'is_active',
            'related_object',
            'public',
            'contractor',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        is_retrieve = False
        try:
            is_retrieve = self.context['view'].action == 'retrieve'
        except (KeyError, AttributeError):
            pass
        qs = instance.chapters.filter(is_active=True, use_in_wiki=True).order_by('sort')
        if not is_retrieve:
            qs = qs.filter(show_on_main_page=True)
        data['chapters'] = WikiChapterShortSerializer(qs, many=True).data
        data['has_more'] = instance.chapters.filter(is_active=True, show_on_main_page=False,
                                                    use_in_wiki=True).exists()
        return data


class WikiSectionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiSectionModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'random_html_ru',
            'random_html_kk',
            'use_in_wiki',
            'code',
            'related_object',
            'public',
            'contractor',
        )

    def validate_contractor(self, contractor):
        if contractor:
            user = self.context.get('request').user.profile
            check_contractor_permission(user.pk, contractor.pk, 'contractor_wiki_admin', None)
        return contractor

    def validate_related_object(self, related_object):
        if related_object:
            original_object = related_object.original_object
            request = self.context.get('request')
            if not request.user.is_superuser:
                if not original_object.get_update_permission(request):
                    raise drf_exceptions.PermissionDenied('related_object')
        return related_object


class WikiSectionReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = WikiSectionModel
        fields = (
            'id',
            'name',
            'created_at',
            'updated_at',
            'sort',
            'random_html',
            'use_in_wiki',
            'code',
            'is_active',
            'related_object',
            'public',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        is_retrieve = False
        try:
            is_retrieve = self.context['view'].action == 'retrieve'
        except (KeyError, AttributeError):
            pass
        qs = instance.chapters.filter(is_active=True, use_in_wiki=True).order_by('sort')
        if not is_retrieve:
            qs = qs.filter(show_on_main_page=True)
        data['chapters'] = WikiChapterShortSerializer(qs, many=True).data
        data['has_more'] = instance.chapters.filter(is_active=True, show_on_main_page=False, use_in_wiki=True).exists()
        if get_language_from_request(self.context.get('request')) == 'kk':
            data['has_kk'] = bool(instance.random_html_kk)
        return data


class WikiPageShortReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPageModel
        fields = (
            'id',
            'name',
            'sort',
            'is_active',
        )


class WikiPageFormSerializer(serializers.ModelSerializer):
    chapter = WikiChapterShortSerializer(many=True)
    class Meta:
        model = WikiPageModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'random_html_ru',
            'random_html_kk',
            'use_in_wiki',
            'created_at',
            'updated_at',
            'sort',
            'code',
            'chapter',
            'is_active',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        sections = WikiSectionModel.objects.filter(chapters__pages__in=[instance],
                                                   is_active=True).order_by('sort')
        data['section'] = WikiSectionShortSerializer(sections, many=True).data

        if 'view' in self.context and self.context['view'].action == 'retrieve':
            instance.cluts()
            data['viewer_count'] = instance.viewers.count()

        return data


class WikiPageReadSerializer(serializers.ModelSerializer):
    chapter = WikiChapterShortSerializer(many=True)

    class Meta:
        model = WikiPageModel
        fields = (
            'id',
            'name',
            'random_html',
            'use_in_wiki',
            'created_at',
            'updated_at',
            'sort',
            'code',
            'chapter',
            'is_active',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        sections = WikiSectionModel.objects.filter(chapters__pages__in=[instance],
                                                   is_active=True).order_by('sort')
        data['section'] = WikiSectionShortSerializer(sections, many=True).data

        if 'view' in self.context and self.context['view'].action == 'retrieve':
            instance.cluts()
            data['viewer_count'] = instance.viewers.count()
        if get_language_from_request(self.context.get('request')) == 'kk':
            data['has_kk'] = bool(instance.random_html_kk)
        return data


class WikiPageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPageModel
        fields = (
            'id',
            'name_ru',
            'name_kk',
            'random_html_ru',
            'random_html_kk',
            'use_in_wiki',
            'sort',
            'code',
            'chapter',
            'related_object',
        )

    def validate_related_object(self, related_object):
        request = self.context.get('request')
        is_superuser = request.user.is_superuser
        if related_object:
            original_object = related_object.original_object
            if not is_superuser:
                if not original_object.get_update_permission(request):
                    raise drf_exceptions.PermissionDenied('related_object')
        else:
            if not is_superuser:
                raise drf_exceptions.PermissionDenied()
        return related_object

    def validate(self, attrs):
        related_object = attrs.get('related_object')
        chapter_related_object = attrs.get('chapter')[0].related_object
        if not related_object == chapter_related_object:
            raise drf_exceptions.ValidationError('Связанные объекты главы и страницы не совпадают')
        return attrs


class WikiPageShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPageModel
        fields = (
            'id',
            'name',
            'sort',
            'is_active',
        )


class WikiChapterWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiChapterModel
        fields = (
            'id',
            'code',
            'name_ru',
            'name_kk',
            'random_html_ru',
            'random_html_kk',
            'use_in_wiki',
            'sort',
            'section',
            'show_on_main_page',
            'related_object',
        )

    def validate_related_object(self, related_object):
        if related_object:
            original_object = related_object.original_object
            request = self.context.get('request')
            if not request.user.is_superuser:
                if not original_object.get_update_permission(request):
                    raise drf_exceptions.PermissionDenied('related_object')
        return related_object

    def validate(self, attrs):
        related_object = attrs.get('related_object')
        section_related_object = attrs.get('section')[0].related_object
        if not related_object == section_related_object:
            raise drf_exceptions.ValidationError('Связанные объекты раздела и главы не совпадают')
        return attrs


class WikiChapterFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiChapterModel
        fields = (
            'id',
            'code',
            'name_ru',
            'name_kk',
            'random_html_ru',
            'random_html_kk',
            'use_in_wiki',
            'created_at',
            'updated_at',
            'sort',
            'section',
            'is_active',
            'show_on_main_page',
            'related_object',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['pages'] = WikiPageShortSerializer(instance.pages.filter(is_active=True,
                                                                      use_in_wiki=True).order_by('sort'),
                                                many=True).data
        data['sections'] = WikiSectionShortSerializer(instance.section.filter(is_active=True,
                                                                              use_in_wiki=True).order_by('sort'),
                                                      many=True).data
        return data


class WikiChapterReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiChapterModel
        fields = (
            'id',
            'code',
            'name',
            'random_html',
            'use_in_wiki',
            'created_at',
            'updated_at',
            'sort',
            'section',
            'is_active',
            'show_on_main_page',
            'related_object',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['pages'] = WikiPageShortSerializer(instance.pages.filter(is_active=True,
                                                                      use_in_wiki=True).order_by('sort'),
                                                many=True).data
        data['sections'] = WikiSectionShortSerializer(instance.section.filter(is_active=True,
                                                                              use_in_wiki=True).order_by('sort'),
                                                      many=True).data
        if get_language_from_request(self.context.get('request')) == 'kk':
            data['has_kk'] = bool(instance.random_html_kk)
        return data


# class WikiShortSearchSerializer(HaystackSerializer):
#     class Meta:
#         index_classes = [search_indexes.WikiPageIndex,
#                          search_indexes.WikiChapterIndex,
#                          search_indexes.WikiSectionIndex]
#         fields = (
#             'content'
#         )
#
#     def to_representation(self, instance):
#         data = WikiPageShortSerializer(instance.object).data
#         data['content'] = instance.text
#         data['model'] = instance.model_name.replace('model', '').replace('wiki', '')
#         return data


class WikiShortSearchSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    sort = serializers.IntegerField()
    model = serializers.CharField()
    is_active = serializers.BooleanField()


class WikiAccessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiAccessModel
        fields = (
            'contractor_profile',
            'wiki_section',
        )
