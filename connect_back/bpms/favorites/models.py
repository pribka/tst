from django.db import models
from django.utils.translation import gettext_lazy as _

from bkz3.settings import CUSTOM_CASCADE

from common import models as common_models
from common.current_profile.middleware import get_current_authenticated_profile


class FavoriteModel(common_models.BaseAbstractModel):
    user = models.ForeignKey(
        'users.ProfileModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='favorites',
        verbose_name=_('Пользователь')
    )
    related_object = models.ForeignKey(
        'common.BaseModel',
        null=True,
        blank=False,
        on_delete=CUSTOM_CASCADE,
        related_name='profile_favorites',
        verbose_name=_('Связанный объект')
    )

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        unique_together = (('user', 'related_object',),)

    @classmethod
    def get_queryset(cls, request=None):
        qs = cls.objects.filter(
            user=request.user.profile,
            related_object__is_active=True
        ).order_by('-created_at',)
        return qs

    @classmethod
    def get_select_queryset(cls, request=None):
        return cls.objects.none()

    @classmethod
    def get_filtered_select_queryset(cls, text: str, request=None):
        return cls.objects.none()

    @classmethod
    def get_serializer_class(cls, action=None):
        from . import serializers
        if action == 'create':
            return serializers.FavoriteModelCreateSerializer
        else:
            return serializers.FavoriteModelListSerializer

    @staticmethod
    def annotate_favorites(queryset):
        user = get_current_authenticated_profile()
        favorites = FavoriteModel.objects.filter(user=user, related_object=models.OuterRef('pk'))
        return queryset.annotate(
            in_favorites=models.Exists(favorites)
        )

# class FavoritesModel(common_models.BaseModel):
#     """Список избранного."""
#
#     profile = models.OneToOneField(
#         'users.ProfileModel',
#         on_delete=models.CASCADE,
#         related_name='favorites',
#         blank=False,
#         null=True,
#         verbose_name=_('Профиль')
#     )
#     favorites = models.JSONField(
#         blank=False,
#         null=False,
#         default=dict,
#         verbose_name=_('Список Избранного')
#     )
#
#     class Meta:
#         verbose_name = _('избранное')
#         verbose_name_plural = _('Избранное')
#
#     def __str__(self):
#         return getattr(self.profile.user, 'full_name')

    # @classmethod
    # def get_serializer_class(cls, action=None):
    #     from . import serializers as f_serializers  # noqa: F401
    #     serializer_class = type(
    #         'serializer_class', (f_serializers.FavoritesSerializer,), {}
    #     )
    #     serializer_class.Meta.model = cls
    #     return serializer_class
