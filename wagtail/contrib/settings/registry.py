from warnings import warn

from django.apps import apps
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.text import capfirst

from wagtail import hooks
from wagtail.admin.admin_url_finder import (
    ModelAdminURLFinder,
    register_admin_url_finder,
)
from wagtail.admin.menu import MenuItem
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.utils.deprecation import RemovedInWagtail70Warning

from .permissions import user_can_edit_setting_type


class SettingMenuItem(MenuItem):
    def __init__(self, model, icon="cog", classname="", classnames="", **kwargs):
        if classnames:
            warn(
                "The `classnames` kwarg for SettingMenuItem is deprecated - use `classname` instead.",
                category=RemovedInWagtail70Warning,
            )
        classname = classname or classnames

        self.model = model
        super().__init__(
            label=capfirst(model._meta.verbose_name),
            url=reverse(
                "wagtailsettings:edit",
                args=[model._meta.app_label, model._meta.model_name],
            ),
            classname=classname,
            icon_name=icon,
            **kwargs,
        )

    def is_shown(self, request):
        return user_can_edit_setting_type(request.user, self.model)


class SiteSettingAdminURLFinder(ModelAdminURLFinder):
    def construct_edit_url(self, instance):
        return reverse(
            "wagtailsettings:edit",
            args=[
                self.model._meta.app_label,
                self.model._meta.model_name,
                instance.site_id,
            ],
        )


class GenericSettingAdminURLFinder(ModelAdminURLFinder):
    def construct_edit_url(self, instance):
        return reverse(
            "wagtailsettings:edit",
            args=[
                self.model._meta.app_label,
                self.model._meta.model_name,
                instance.id,
            ],
        )


class Registry(list):
    def __init__(self):
        self._model_icons = {}

    def register(self, model, icon="cog", **kwargs):
        from .models import BaseGenericSetting, BaseSiteSetting

        """
        Register a model as a setting, adding it to the wagtail admin menu
        """
        if icon:
            self._model_icons[model] = icon

        # Don't bother registering this if it is already registered
        if model in self:
            return model
        self.append(model)

        # Register a new menu item in the settings menu
        @hooks.register("register_settings_menu_item")
        def menu_hook():
            return SettingMenuItem(model, icon=self._model_icons.get(model), **kwargs)

        @hooks.register("register_permissions")
        def permissions_hook():
            return Permission.objects.filter(
                content_type__app_label=model._meta.app_label,
                codename=f"change_{model._meta.model_name}",
            )

        # Register an admin URL finder
        permission_policy = ModelPermissionPolicy(model)

        if issubclass(model, BaseSiteSetting):
            finder_class = type(
                "_SiteSettingAdminURLFinder",
                (SiteSettingAdminURLFinder,),
                {"model": model, "permission_policy": permission_policy},
            )
        elif issubclass(model, BaseGenericSetting):
            finder_class = type(
                "_GenericSettingAdminURLFinder",
                (GenericSettingAdminURLFinder,),
                {"model": model, "permission_policy": permission_policy},
            )
        else:
            raise NotImplementedError

        register_admin_url_finder(model, finder_class)

        return model

    def register_decorator(self, model=None, icon="cog", **kwargs):
        """
        Register a model as a setting in the Wagtail admin
        """
        if model is None:
            return lambda model: self.register(model, icon=icon, **kwargs)
        return self.register(model, icon=icon, **kwargs)

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
        else:
            if Model not in registry:
                return None
            return Model


registry = Registry()
register_setting = registry.register_decorator
