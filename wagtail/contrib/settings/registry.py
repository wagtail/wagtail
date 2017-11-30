from django.apps import apps
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.text import capfirst

from wagtail.admin.menu import MenuItem
from wagtail.core import hooks

from .permissions import user_can_edit_setting_type


class SettingMenuItem(MenuItem):
    def __init__(self, model, icon='cog', classnames='', **kwargs):

        icon_classes = 'icon icon-' + icon
        if classnames:
            classnames += ' ' + icon_classes
        else:
            classnames = icon_classes

        self.model = model
        super().__init__(
            label=capfirst(model._meta.verbose_name),
            url=reverse('wagtailsettings:edit', args=[
                model._meta.app_label, model._meta.model_name]),
            classnames=classnames,
            **kwargs)

    def is_shown(self, request):
        return user_can_edit_setting_type(request.user, self.model)


class Registry(list):

    def register(self, model, **kwargs):
        """
        Register a model as a setting, adding it to the wagtail admin menu
        """

        # Don't bother registering this if it is already registered
        if model in self:
            return model
        self.append(model)

        # Register a new menu item in the settings menu
        @hooks.register('register_settings_menu_item')
        def menu_hook():
            return SettingMenuItem(model, **kwargs)

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
