import warnings

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from ...middleware import get_current_authenticated_profile
from bkz3.settings import CUSTOM_CASCADE, CUSTOM_DO_NOTHING, CUSTOM_SET_NULL, CUSTOM_PROTECT

class CurrentProfileField(models.ForeignKey):

    warning = ("You passed an argument to CurrentProfileField that will be "
               "ignored. Avoid args and following kwargs: default, null, to.")
    description = _(
        'as default value sets the current logged in user profile if available')
    defaults = dict(null=True, default=get_current_authenticated_profile,
                    to='users.profilemodel')

    def __init__(self, *args, **kwargs):
        self.on_update = kwargs.pop("on_update", False)
        self._warn_for_shadowing_args(*args, **kwargs)

        if "on_delete" not in kwargs:
            kwargs["on_delete"] = CUSTOM_CASCADE

        if self.on_update:
            kwargs["editable"] = False
            kwargs["blank"] = True

        kwargs.update(self.defaults)
        super(CurrentProfileField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CurrentProfileField, self).deconstruct()
        if self.on_update:
            kwargs['on_update'] = self.on_update
            del kwargs["editable"]
            del kwargs["blank"]

        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        if self.on_update:
            value = get_current_authenticated_profile()
            if value is not None:
                value = value.pk
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(CurrentProfileField, self).pre_save(model_instance, add)

    def _warn_for_shadowing_args(self, *args, **kwargs):
        if args:
            warnings.warn(self.warning)
        else:
            for key in set(kwargs).intersection(set(self.defaults.keys())):
                if not kwargs[key] == self.defaults[key]:
                    warnings.warn(self.warning)
                    break
