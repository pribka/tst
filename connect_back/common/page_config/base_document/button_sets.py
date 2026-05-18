from django.utils.translation import gettext_lazy as _

from common.page_config.common import ModelSetConfig
from common.page_config.buttons import DropdownActionsButton
from common.page_config.base_model.buttons import ModelButton, ModelButtonSaveAndClose, DropdownButton, \
    StatusMarkButton, CopyModelButton, AddButton, DeleteButton, CopyButton, SelectAllButton
from common.page_config.base_model.button_sets import BaseModelContextMenuButtonSet
from .buttons import UnpostDocumentButton, PostDocumentButton


class BaseDocumentButtonSet(ModelSetConfig):
    instances = ('save_and_post_and_close', 'save', 'save_and_post', 'more')
    save_and_post_and_close = ModelButton(
        action='save_and_post_and_close', title=_("Post and close"), obj_type="primary"
    )
    save = DropdownActionsButton(
        action='save',
        title=_('Save'),
        children=ModelSetConfig(
            save_and_close=ModelButtonSaveAndClose(), instances=('save_and_close',)
        )
    )
    save_and_post = ModelButton(action='save_and_post', title=_("Post"))
    more = DropdownButton(
        title=_("More"),
        action='more',
        children=ModelSetConfig(
            status_mark=StatusMarkButton(),
            unpost_document=UnpostDocumentButton(),
            copy_document=CopyModelButton(),
            instances=('status_mark', 'unpost_document', 'copy_document')
        )
    )


class TabularPartButtonSet(ModelSetConfig):
    instances = ('add',)
    add = AddButton()


class TabularPartContextMenuButtonSet(ModelSetConfig):
    instances = ('add', 'delete', 'copy', 'select_all')
    add = AddButton()
    delete = DeleteButton()
    copy = CopyButton()
    select_all = SelectAllButton()


class BaseDocumentContextMenuButtonSet(BaseModelContextMenuButtonSet):
    post = PostDocumentButton()
    unpost = UnpostDocumentButton()
    instances = ('add', 'edit', 'status_mark', 'copy', 'post', 'unpost')
