from django.apps import apps
from django.core.urlresolvers import reverse
from django.utils.text import capfirst

from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks


class Registry(list):

    def register(self, model, icon='cog', **kwargs):
        """
        Register a model as a setting, adding it to the wagtail admin menu
        """

        # Don't bother registering this if it is already registered
        if model in self:
            return model
        self.append(model)

        icon_classes = 'icon icon-' + icon
        if 'classnames' in kwargs:
            kwargs['classnames'] += ' ' + icon_classes
        else:
            kwargs['classnames'] = icon_classes

        # Register a new menu item in the settings menu
        @hooks.register('register_settings_menu_item')
        def hook():
            return MenuItem(
                capfirst(model._meta.verbose_name),
                reverse('wagtailsettings_edit', args=[
                    model._meta.app_label, model._meta.model_name]),
                **kwargs)

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
