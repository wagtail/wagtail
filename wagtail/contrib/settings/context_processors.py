from django.utils.functional import SimpleLazyObject

from wagtail.core.models import Site

from .registry import registry


class SettingsProxy(dict):
    """
    Get a SettingModuleProxy for an app using proxy['app_label']
    """
    def __init__(self, site):
        self.site = site

    def __missing__(self, app_label):
        self[app_label] = value = SettingModuleProxy(self.site, app_label)
        return value

    def __str__(self):
        return 'SettingsProxy'


class SettingModuleProxy(dict):
    """
    Get a setting instance using proxy['modelname']
    """
    def __init__(self, site, app_label):
        self.site = site
        self.app_label = app_label

    def __getitem__(self, model_name):
        """ Get a setting instance for a model """
        # Model names are treated as case-insensitive
        return super().__getitem__(model_name.lower())

    def __missing__(self, model_name):
        """ Get and cache settings that have not been looked up yet """
        self[model_name] = value = self.get_setting(model_name)
        return value

    def get_setting(self, model_name):
        """
        Get a setting instance
        """
        Model = registry.get_by_natural_key(self.app_label, model_name)
        if Model is None:
            return None

        return Model.for_site(self.site)

    def __str__(self):
        return 'SettingsModuleProxy({0})'.format(self.app_label)


def settings(request):
    def _inner(request):
        site = Site.find_for_request(request)
        if site is None:
            # find_for_request() can't determine the site
            # old SiteMiddleware case
            # Unittest or email templates might also mock request
            # objects that don't have a request.site.
            return {}
        else:
            return SettingsProxy(site)

    return {'settings': SimpleLazyObject(lambda: _inner(request))}
