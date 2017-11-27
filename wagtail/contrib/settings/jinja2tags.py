from weakref import WeakKeyDictionary

import jinja2
from django.utils.encoding import force_str
from jinja2.ext import Extension

from wagtail.contrib.settings.registry import registry
from wagtail.core.models import Site

# Settings are cached per template context, to prevent excessive database
# lookups. The cached settings are disposed of once the template context is no
# longer used.
settings_cache = WeakKeyDictionary()


class ContextCache(dict):
    """
    A cache of Sites and their Settings for a template Context
    """
    def __missing__(self, key):
        """
        Make a SiteSetting for a new Site
        """
        if not(isinstance(key, Site)):
            raise TypeError
        out = self[key] = SiteSettings(key)
        return out


class SiteSettings(dict):
    """
    A cache of Settings for a specific Site
    """
    def __init__(self, site):
        super().__init__()
        self.site = site

    def __getitem__(self, key):
        # Normalise all keys to lowercase
        return super().__getitem__(force_str(key).lower())

    def __missing__(self, key):
        """
        Get the settings instance for this site, and store it for later
        """
        try:
            app_label, model_name = key.split('.', 1)
        except ValueError:
            raise KeyError('Invalid model name: {}'.format(key))
        Model = registry.get_by_natural_key(app_label, model_name)
        if Model is None:
            raise KeyError('Unknown setting: {}'.format(key))

        out = self[key] = Model.for_site(self.site)
        return out


@jinja2.contextfunction
def get_setting(context, model_string, use_default_site=False):
    if use_default_site:
        site = Site.objects.get(is_default_site=True)
    elif 'request' in context:
        site = context['request'].site
    else:
        raise RuntimeError('No request found in context, and use_default_site '
                           'flag not set')

    # Sadly, WeakKeyDictionary can not implement __missing__, so we have to do
    # this one manually
    try:
        context_cache = settings_cache[context]
    except KeyError:
        context_cache = settings_cache[context] = ContextCache()
    # These ones all implement __missing__ in a useful way though
    return context_cache[site][model_string]


class SettingsExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        self.environment.globals.update({
            'settings': get_setting,
        })


settings = SettingsExtension
