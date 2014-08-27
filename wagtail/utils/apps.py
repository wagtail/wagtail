try:
    from importlib import import_module
except ImportError:
    # for Python 2.6, fall back on django.utils.importlib (deprecated as of Django 1.7)
    from django.utils.importlib import import_module

import django
from django.conf import settings
from django.utils.module_loading import module_has_submodule


def get_app_modules():
    """
    Generator function that yields a module object for each installed app
    yields tuples of (app_name, module)
    """
    if django.VERSION < (1, 7):
        # Django 1.6
        for app in settings.INSTALLED_APPS:
            yield app, import_module(app)
    else:
        # Django 1.7+
        from django.apps import apps
        for app in apps.get_app_configs():
            yield app.name, app.module


def get_app_submodules(submodule_name):
    """
    Searches each app module for the specified submodule
    yields tuples of (app_name, module)
    """
    for name, module in get_app_modules():
        if module_has_submodule(module, submodule_name):
            yield name, import_module('%s.%s' % (name, submodule_name))
