from common.page_config.common import ModelSetConfig

from .buttons import ModelButtonSave, ModelButtonSaveAndClose, AddButton, EditButton, StatusMarkButton, CopyButton


class BaseCatalogButtonSet(ModelSetConfig):
    model = None
    save = ModelButtonSave(model=model)
    save_and_close = ModelButtonSaveAndClose(model=model)
    instances = ('save', 'save_and_close')


class BaseModelTableButtonSet(ModelSetConfig):
    instances = ('add',)
    add = AddButton(obj_type="primary")


class BaseModelContextMenuButtonSet(ModelSetConfig):
    add = AddButton()
    edit = EditButton()
    status_mark = StatusMarkButton()
    copy = CopyButton()
    instances = ('add', 'edit', 'status_mark', 'copy')
