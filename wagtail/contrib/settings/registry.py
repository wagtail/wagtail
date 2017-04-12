from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from wagtail.contrib.modeladmin.options import modeladmin_register
from wagtail.contrib.settings.options import SettingAdmin
from wagtail.wagtailcore import hooks

from .menu import SettingMenuItem
from .permissions import user_can_edit_setting_type


class Registry(list):

    def register(self, model, add_to_menu=True, **kwargs):
        """
        Register a model as a setting, adding it to the wagtail admin menu
        """

        # Don't bother registering this if it is already registered
        if model in self:
            return model
        self.append(model)

        # Register a new menu item in the settings menu
        if add_to_menu:
            admin_kwargs = {'menu_' + key: value for key, value in kwargs.items()}
            modeladmin_register(SettingAdmin.for_setting(model, **admin_kwargs))

        elif kwargs:
            raise TypeError('Menu keyword arguments supplied when `add_to_menu` is False')

        @hooks.register('register_permissions')
        def permissions_hook():
            return Permission.objects.filter(
                content_type__app_label=model._meta.app_label,
                codename='change_{}'.format(model._meta.model_name))

        return model

    def register_decorator(self, model=None, **kwargs):
        """
        Register a model as a setting in the Wagtail admin
        """
        if model is None:
            return lambda model: self.register(model, **kwargs)
        return self.register(model, **kwargs)

    def get_by_natural_key(self, app_label, model_name):
        """
        Get a setting model using its app_label and model_name.

        If the app_label.model_name combination is not a valid model, or the
        model is not registered as a setting, returns None.
        """
        try:
            Model = apps.get_model(app_label, model_name)
        except LookupError:
            return None
        if Model not in registry:
            return None
        return Model


registry = Registry()
register_setting = registry.register_decorator
