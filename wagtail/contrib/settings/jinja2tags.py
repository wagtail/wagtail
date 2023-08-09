from weakref import WeakKeyDictionary

import jinja2
from django.utils.encoding import force_str
from jinja2.ext import Extension

from wagtail.contrib.settings.models import BaseGenericSetting, BaseSiteSetting
from wagtail.contrib.settings.registry import registry
from wagtail.models import Site

# Settings are cached per template context, to prevent excessive database
# lookups. The cached settings are disposed of once the template context is no
# longer used.
settings_cache = WeakKeyDictionary()


class SettingContextCache(dict):
    """
    Settings cache for a template Context
    """

    def __missing__(self, key):
        out = self[key] = Setting(key)
        return out


class Setting(dict):
    def __init__(self, site):
        super().__init__()
        self.site = site

    def __getitem__(self, key):
        # Normalise all keys to lowercase
        return super().__getitem__(force_str(key).lower())

    def __missing__(self, key):
        """
        Get the settings instance and store it for later
        """
        try:
            app_label, model_name = key.split(".", 1)
        except ValueError:
            raise KeyError(f"Invalid model name: `{key}`")

        Model = registry.get_by_natural_key(app_label, model_name)
        if Model is None:
            raise RuntimeError(f"Could not find model matching `{key}`.")

        if issubclass(Model, BaseGenericSetting):
            out = self[key] = Model.load(request_or_site=self.site)
        elif issubclass(Model, BaseSiteSetting):
            if self.site is None or not isinstance(self.site, Site):
                raise RuntimeError(
                    "Site-specific settings cannot be identified because "
                    "`self.site` is not a Site."
                )
            out = self[key] = Model.for_site(self.site)
        else:
            raise NotImplementedError

        return out


@jinja2.pass_context
def get_setting(context, model_string, use_default_site=False):
    cache_key = None
    if use_default_site:
        cache_key = Site.objects.get(is_default_site=True)
    elif "request" in context:
        cache_key = Site.find_for_request(context["request"])

    # Sadly, WeakKeyDictionary can not implement __missing__, so we have to do
    # this one manually
    try:
        context_cache = settings_cache[context]
    except KeyError:
        context_cache = settings_cache[context] = SettingContextCache()
    # These ones all implement __missing__ in a useful way though
    return context_cache[cache_key][model_string]


class SettingsExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        self.environment.globals.update(
            {
                "settings": get_setting,
            }
        )


settings = SettingsExtension
