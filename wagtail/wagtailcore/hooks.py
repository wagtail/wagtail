from django.conf import settings
try:
    from importlib import import_module
except ImportError:
    # for Python 2.6, fall back on django.utils.importlib (deprecated as of Django 1.7)
    from django.utils.importlib import import_module

_hooks = {}


def register(hook_name, fn=None):
    """
    Register hook for ``hook_name``. Can be used as a decorator::

        @register('hook_name')
        def my_hook(...):
            pass

    or as a function call::

        def my_hook(...):
            pass
        register('hook_name', my_hook)
    """

    # Pretend to be a decorator if fn is not supplied
    if fn is None:
        def decorator(fn):
            register(hook_name, fn)
            return fn
        return decorator

    if hook_name not in _hooks:
        _hooks[hook_name] = []
    _hooks[hook_name].append(fn)

_searched_for_hooks = False


def search_for_hooks():
    global _searched_for_hooks
    if not _searched_for_hooks:
        for app_module in settings.INSTALLED_APPS:
            try:
                import_module('%s.wagtail_hooks' % app_module)
            except ImportError:
                continue

        _searched_for_hooks = True


def get_hooks(hook_name):
    search_for_hooks()
    return _hooks.get(hook_name, [])
