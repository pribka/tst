from django.utils.translation import gettext_lazy as _

from common.page_config.buttons import Button


class PostDocumentButton(Button):
    action = 'post_document'
    title = _('Post')


class UnpostDocumentButton(Button):
    action = 'unpost_document'
    title = _('Unpost')
