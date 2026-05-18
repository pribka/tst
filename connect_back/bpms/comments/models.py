from bs4 import BeautifulSoup

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT
from bkz3.settings import FRONTEND_URL

from common import models as common_models


class CommentModel(common_models.BaseModel):
    parent = models.ForeignKey(to='self', on_delete=CUSTOM_CASCADE, null=True, blank=True, related_name='children')
    text = models.TextField(null=False, default='', blank=True)
    related_object = models.ForeignKey('common.BaseModel', null=True, on_delete=CUSTOM_PROTECT, related_name='comments')
    readers = models.ManyToManyField('users.ProfileModel',
                                     verbose_name=_('Читатели'),
                                     blank=True)
    is_personal = models.BooleanField(default=False,
                                      verbose_name=_('Персональный'))
    is_system = models.BooleanField(default=False,
                                    verbose_name='Системный комментарий')
    is_updated = models.BooleanField(default=False, verbose_name=_('Изменен'))

    class Meta:
        verbose_name = _('Комментарий')
        verbose_name_plural = _('Комментарии')

    def get_children(self, children=None):
        if children is None:
            children = list(CommentModel.objects.filter(parent=self).values_list('pk', flat=True))
            return self.get_children(children)
        else:
            new_children = list(CommentModel.objects.filter(parent__in=children).values_list('pk', flat=True))
            if new_children:
                children = children + new_children
                return self.get_children(children)
            else:
                return children

    @classmethod
    def get_serializer_class(cls, action=None):
        from .serializers import CommentListSerializer, CommentCreateSerializer, CommentNotifySerializer
        if action == 'create':
            return CommentCreateSerializer
        elif action == 'notify':
            return CommentNotifySerializer
        return CommentListSerializer

    def get_detail_permission(self, request) -> bool:
        try:
            related_object = common_models.BaseModel.objects.super_get(pk=self.related_object_id)
        except common_models.BaseModel.DoesNotExist:
            return False
        return related_object.get_detail_permission(request)

    @property
    def text_clear(self) -> str:
        return BeautifulSoup(self.text, 'lxml').get_text(separator=" ", strip=True)
