from django.utils.translation import gettext_lazy as _

from common.page_config.buttons import Button, ModelButton, DropdownButton, ModelFormButton


class StatusMarkButton(Button):
    action = 'status_mark'
    title = _("Mark for deletion") + '/' + _("Unmark")


class CopyModelButton(ModelButton):
    action = 'copy'
    title = _('Copy')


class ModelButtonSave(ModelButton):
    action = 'save'
    icon = 'save'
    title = _('Save')
    obj_type = 'primary'


class ModelButtonSaveAndClose(ModelButton):
    action = 'save_and_close'
    title = _('Save and close')


class PrintDropdownButton(DropdownButton):
    title = _('Print')
    obj_type = 'dashed'


class AddButton(ModelFormButton):
    title = _("Add")
    action = "create"
    icon = "plus"


class CopyButton(ModelFormButton):
    title = _("Copy")
    action = "copy"


class EditButton(ModelFormButton):
    title = _("Edit")
    action = "update"


class DeleteButton(Button):
    title = _("Delete")
    action = "delete"


class SelectAllButton(Button):
    title = _("Select all")
    action = "select_all"
