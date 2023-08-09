from wagtail.contrib.settings.models import BaseGenericSetting, BaseSiteSetting
from wagtail.models import Site

from .registry import registry


class SettingProxy(dict):
    """
    Get a SettingModuleProxy for an app using proxy['app_label']
    """

    def __init__(self, request_or_site):
        self.request_or_site = request_or_site

    def __missing__(self, app_label):
        self[app_label] = value = SettingModuleProxy(self.request_or_site, app_label)
        return value


class SettingModuleProxy(dict):
    """
    Get a specific setting instance using proxy['modelname']
    """

    def __init__(self, request_or_site, app_label):
        self.app_label = app_label
        self.request_or_site = request_or_site

    def __getitem__(self, model_name):
        """Get a setting instance for a model"""
        # Model names are treated as case-insensitive
        return super().__getitem__(model_name.lower())

    def __missing__(self, model_name):
        """Get and cache settings that have not been looked up yet"""
        self[model_name] = value = self.get_setting(model_name)
        return value

    def __str__(self):
        return f"SettingModuleProxy({self.app_label})"

    def get_setting(self, model_name):
        """
        Get a setting instance
        """
        Model = registry.get_by_natural_key(self.app_label, model_name)
        if Model is None:
            raise RuntimeError(
                f"Could not find model matching `{self.app_label}.{model_name}`."
            )

        if issubclass(Model, BaseGenericSetting):
            return Model.load(request_or_site=self.request_or_site)
        elif issubclass(Model, BaseSiteSetting):
            if self.request_or_site is not None:
                if isinstance(self.request_or_site, Site):
                    return Model.for_site(self.request_or_site)

                # Utilises cached value on request if set
                return Model.for_request(self.request_or_site)

            raise RuntimeError(
                "Site-specific settings cannot be identified because "
                "`request` is not available in the context and "
                "`use_default_site` is False."
            )

        raise NotImplementedError(
            "Setting models should inherit from either `BaseGenericSetting` "
            "or `BaseSiteSetting`."
        )


def settings(request):
    return {"settings": SettingProxy(request_or_site=request)}
